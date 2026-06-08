# controllers/libri.py — Controller per la gestione dei libri dell'utente.
# CRUD dei libri posseduti (lista, aggiunta, modifica, eliminazione) con upload
# della copertina. Le rotte sono protette: ogni utente gestisce solo i propri
# libri. La posizione del libro e' indicata scegliendo una citta' (menu a
# tendina): da essa si ricavano le coordinate lat/lon per la ricerca geospaziale.
from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash, abort
)

from models.libro import Libro
from models.utente import Utente
from models.citta import elenco_citta, coordinate_di
from controllers.auth import login_richiesto
from immagini import salva_immagine, rimuovi_immagine

libri_bp = Blueprint("libri", __name__)


def _libro_di_proprieta(libro_id):
    """Restituisce il libro se appartiene all'utente in sessione, altrimenti
    interrompe con 403/404."""
    libro = Libro.trova_per_id(libro_id)
    if libro is None:
        abort(404)
    if libro["utente_id"] != session["utente_id"]:
        abort(403)
    return libro


@libri_bp.route("/libri")
@login_richiesto
def lista():
    """Elenco dei libri dell'utente autenticato."""
    libri = Libro.trova_per_utente(session["utente_id"])
    return render_template("libri_lista.html", libri=libri)


@libri_bp.route("/libri/nuovo", methods=["GET", "POST"])
@login_richiesto
def nuovo():
    utente = Utente.trova_per_id(session["utente_id"])
    if request.method == "POST":
        dati, errore = _leggi_form()
        if errore:
            flash(errore, "danger")
            return render_template("libro_form.html", libro=dati,
                                   citta_disponibili=elenco_citta(), azione="nuovo")
        try:
            copertina = salva_immagine(request.files.get("copertina"))
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("libro_form.html", libro=dati,
                                   citta_disponibili=elenco_citta(), azione="nuovo")

        Libro.crea(
            session["utente_id"], dati["titolo"], dati["autore"], dati["anno"],
            dati["descrizione"], copertina, dati["citta"], dati["lat"], dati["lon"],
        )
        flash("Libro aggiunto alla tua biblioteca.", "success")
        return redirect(url_for("libri.lista"))

    # GET: preseleziona la citta' del profilo dell'utente, se disponibile
    iniziale = {"citta": utente["citta"]}
    return render_template("libro_form.html", libro=iniziale,
                           citta_disponibili=elenco_citta(), azione="nuovo")


@libri_bp.route("/libri/<int:libro_id>/modifica", methods=["GET", "POST"])
@login_richiesto
def modifica(libro_id):
    libro = _libro_di_proprieta(libro_id)
    if request.method == "POST":
        dati, errore = _leggi_form()
        if errore:
            flash(errore, "danger")
            dati["id"] = libro_id
            dati["copertina"] = libro["copertina"]
            return render_template("libro_form.html", libro=dati,
                                   citta_disponibili=elenco_citta(), azione="modifica")
        try:
            nuova_copertina = salva_immagine(request.files.get("copertina"))
        except ValueError as e:
            flash(str(e), "danger")
            dati["id"] = libro_id
            dati["copertina"] = libro["copertina"]
            return render_template("libro_form.html", libro=dati,
                                   citta_disponibili=elenco_citta(), azione="modifica")

        # Se e' stata caricata una nuova copertina, rimuovi la vecchia
        if nuova_copertina:
            rimuovi_immagine(libro["copertina"])

        Libro.aggiorna(
            libro_id, dati["titolo"], dati["autore"], dati["anno"],
            dati["descrizione"], dati["citta"], dati["lat"], dati["lon"],
            copertina=nuova_copertina,
        )
        flash("Libro aggiornato.", "success")
        return redirect(url_for("libri.lista"))

    return render_template("libro_form.html", libro=libro,
                           citta_disponibili=elenco_citta(), azione="modifica")


@libri_bp.route("/libri/<int:libro_id>/elimina", methods=["POST"])
@login_richiesto
def elimina(libro_id):
    libro = _libro_di_proprieta(libro_id)
    rimuovi_immagine(libro["copertina"])
    Libro.elimina(libro_id)
    flash("Libro eliminato.", "info")
    return redirect(url_for("libri.lista"))


def _leggi_form():
    """Legge e valida i campi del form libro.

    Restituisce (dati, errore): 'errore' e' None se i dati sono validi.
    Le coordinate lat/lon vengono ricavate dalla citta' scelta.
    """
    dati = {
        "titolo": request.form.get("titolo", "").strip(),
        "autore": request.form.get("autore", "").strip(),
        "descrizione": request.form.get("descrizione", "").strip() or None,
        "citta": request.form.get("citta", "").strip(),
    }

    if not dati["titolo"] or not dati["autore"]:
        return dati, "Titolo e autore sono obbligatori."

    # Anno: facoltativo, ma se presente deve essere un numero
    anno_raw = request.form.get("anno", "").strip()
    if anno_raw:
        try:
            dati["anno"] = int(anno_raw)
        except ValueError:
            return dati, "L'anno deve essere un numero."
    else:
        dati["anno"] = None

    # Citta' obbligatoria: da essa si ricavano le coordinate
    coordinate = coordinate_di(dati["citta"])
    if coordinate is None:
        return dati, "Seleziona una citta' valida dall'elenco."
    dati["lat"], dati["lon"] = coordinate

    return dati, None
