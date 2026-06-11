# controllers/prestiti.py — Controller della scheda libro e dei prestiti (T6).
# La scheda del libro e' pubblica; la richiesta di prestito (simulata, come da
# traccia) richiede il login. Il proprietario gestisce le richieste ricevute
# (accetta/rifiuta/segna restituito) dalla pagina "Prestiti": all'accettazione
# il libro diventa non disponibile, alla restituzione torna disponibile.
from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash, abort
)

from models.libro import Libro
from models.prestito import Prestito
from controllers.auth import login_richiesto

prestiti_bp = Blueprint("prestiti", __name__)


@prestiti_bp.route("/libri/<int:libro_id>")
def scheda(libro_id):
    """Scheda pubblica del libro, con proprietario e richiesta di prestito."""
    libro = Libro.trova_con_proprietario(libro_id)
    if libro is None:
        abort(404)

    # L'utente puo' chiedere il prestito se: e' autenticato, non e' il
    # proprietario, il libro e' disponibile e non ha gia' una richiesta in corso.
    utente_id = session.get("utente_id")
    richiesta_in_corso = (utente_id is not None
                          and Prestito.attivo(libro_id, utente_id))
    puo_richiedere = (utente_id is not None
                      and utente_id != libro["utente_id"]
                      and libro["disponibile"]
                      and not richiesta_in_corso)

    return render_template("libro_scheda.html", libro=libro,
                           puo_richiedere=puo_richiedere,
                           richiesta_in_corso=richiesta_in_corso)


@prestiti_bp.route("/libri/<int:libro_id>/richiedi", methods=["POST"])
@login_richiesto
def richiedi(libro_id):
    """Invia la richiesta di prestito per un libro (simulata)."""
    libro = Libro.trova_per_id(libro_id)
    if libro is None:
        abort(404)

    if libro["utente_id"] == session["utente_id"]:
        flash("Non puoi chiedere in prestito un tuo libro.", "warning")
    elif not libro["disponibile"]:
        flash("Il libro non e' al momento disponibile.", "warning")
    elif Prestito.attivo(libro_id, session["utente_id"]):
        flash("Hai gia' una richiesta in corso per questo libro.", "warning")
    else:
        Prestito.crea(libro_id, session["utente_id"])
        flash("Richiesta di prestito inviata al proprietario.", "success")

    return redirect(url_for("prestiti.scheda", libro_id=libro_id))


@prestiti_bp.route("/prestiti")
@login_richiesto
def elenco():
    """Richieste ricevute (sui propri libri) e inviate dall'utente.

    Il parametro ?apri=<id> espande il dettaglio di una richiesta inviata e
    segna come letta la relativa notifica ("Da leggere"): le altre notifiche
    restano accese finche' i singoli esiti non vengono aperti.
    """
    utente_id = session["utente_id"]
    apri = request.args.get("apri", type=int)
    if apri:
        Prestito.segna_novita_vista(apri, utente_id)
    return render_template("prestiti.html",
                           ricevuti=Prestito.ricevuti(utente_id),
                           inviati=Prestito.inviati(utente_id),
                           apri=apri)


def _prestito_ricevuto(prestito_id):
    """Restituisce il prestito se riguarda un libro dell'utente in sessione,
    altrimenti interrompe con 404/403 (solo il proprietario decide)."""
    prestito = Prestito.trova_per_id(prestito_id)
    if prestito is None:
        abort(404)
    if prestito["proprietario_id"] != session["utente_id"]:
        abort(403)
    return prestito


@prestiti_bp.route("/prestiti/<int:prestito_id>/accetta", methods=["POST"])
@login_richiesto
def accetta(prestito_id):
    """Il proprietario accetta la richiesta: il libro diventa non disponibile."""
    prestito = _prestito_ricevuto(prestito_id)
    if prestito["stato"] != "richiesto":
        flash("La richiesta non e' piu' in attesa.", "warning")
    else:
        Prestito.cambia_stato(prestito_id, "accettato")
        Libro.imposta_disponibilita(prestito["libro_id"], False)
        flash("Richiesta accettata: il libro risulta in prestito.", "success")
    return redirect(url_for("prestiti.elenco"))


@prestiti_bp.route("/prestiti/<int:prestito_id>/rifiuta", methods=["POST"])
@login_richiesto
def rifiuta(prestito_id):
    """Il proprietario rifiuta la richiesta di prestito."""
    prestito = _prestito_ricevuto(prestito_id)
    if prestito["stato"] != "richiesto":
        flash("La richiesta non e' piu' in attesa.", "warning")
    else:
        Prestito.cambia_stato(prestito_id, "rifiutato")
        flash("Richiesta rifiutata.", "info")
    return redirect(url_for("prestiti.elenco"))


@prestiti_bp.route("/prestiti/<int:prestito_id>/restituzione", methods=["POST"])
@login_richiesto
def dichiara_restituzione(prestito_id):
    """Il richiedente dichiara di aver riconsegnato il libro.

    Non basta a chiudere il prestito: chi ha il libro non puo' "auto-restituirlo".
    Il libro tornera' disponibile solo con la conferma del proprietario.
    """
    prestito = Prestito.trova_per_id(prestito_id)
    if prestito is None:
        abort(404)
    if prestito["richiedente_id"] != session["utente_id"]:
        abort(403)
    if prestito["stato"] != "accettato":
        flash("Puoi dichiarare la riconsegna solo di un prestito accettato.", "warning")
    else:
        # Azione del richiedente: nessuna notifica a lui stesso (il
        # proprietario la vede tra le azioni in attesa del suo badge)
        Prestito.cambia_stato(prestito_id, "in_restituzione",
                              notifica_richiedente=False)
        flash("Riconsegna dichiarata: in attesa della conferma del proprietario.", "success")
    return redirect(url_for("prestiti.elenco"))


@prestiti_bp.route("/prestiti/<int:prestito_id>/restituito", methods=["POST"])
@login_richiesto
def restituito(prestito_id):
    """Il proprietario CONFERMA la restituzione: solo ora il prestito si
    chiude e il libro torna disponibile."""
    prestito = _prestito_ricevuto(prestito_id)
    if prestito["stato"] != "in_restituzione":
        flash("Prima il richiedente deve dichiarare la riconsegna del libro.", "warning")
    else:
        # Il prestito chiuso sparisce dall'elenco del richiedente: niente
        # notifica (non resterebbe nulla da aprire)
        Prestito.cambia_stato(prestito_id, "restituito",
                              notifica_richiedente=False)
        Libro.imposta_disponibilita(prestito["libro_id"], True)
        flash("Restituzione confermata: il libro e' di nuovo disponibile.", "success")
    return redirect(url_for("prestiti.elenco"))
