# controllers/libri.py — Controller per la gestione dei libri dell'utente.
# CRUD dei libri posseduti (lista, aggiunta, modifica, eliminazione) con upload
# della copertina. Le rotte sono protette: ogni utente gestisce solo i propri
# libri. La miniatura della copertina e' resa via CSS in fase di visualizzazione.
import os
import uuid

from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash,
    current_app, abort
)

from config import Config
from models.libro import Libro
from models.utente import Utente
from controllers.auth import login_richiesto

libri_bp = Blueprint("libri", __name__)


def _estensione_consentita(nome_file):
    """True se l'estensione del file e' tra quelle ammesse per le copertine."""
    return (
        "." in nome_file
        and nome_file.rsplit(".", 1)[1].lower() in Config.ESTENSIONI_COPERTINA
    )


def _salva_copertina(file_caricato):
    """Salva l'immagine caricata in static/uploads con un nome univoco.

    Restituisce il nome del file salvato, oppure None se non e' stato caricato
    alcun file. Solleva ValueError se l'estensione non e' ammessa.
    """
    if not file_caricato or file_caricato.filename == "":
        return None
    if not _estensione_consentita(file_caricato.filename):
        raise ValueError("Formato immagine non supportato.")

    estensione = file_caricato.filename.rsplit(".", 1)[1].lower()
    nome_univoco = "%s.%s" % (uuid.uuid4().hex, estensione)
    cartella = os.path.join(current_app.static_folder, "uploads")
    os.makedirs(cartella, exist_ok=True)
    file_caricato.save(os.path.join(cartella, nome_univoco))
    return nome_univoco


def _rimuovi_copertina(nome_file):
    """Elimina dal disco il file di copertina, se presente."""
    if not nome_file:
        return
    percorso = os.path.join(current_app.static_folder, "uploads", nome_file)
    if os.path.exists(percorso):
        os.remove(percorso)


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
            return render_template("libro_form.html", libro=dati, azione="nuovo")
        try:
            copertina = _salva_copertina(request.files.get("copertina"))
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("libro_form.html", libro=dati, azione="nuovo")

        Libro.crea(
            session["utente_id"], dati["titolo"], dati["autore"], dati["anno"],
            dati["descrizione"], copertina, dati["lat"], dati["lon"],
        )
        flash("Libro aggiunto alla tua biblioteca.", "success")
        return redirect(url_for("libri.lista"))

    # GET: precompila le coordinate con quelle del profilo dell'utente
    iniziale = {"lat": utente["lat"], "lon": utente["lon"]}
    return render_template("libro_form.html", libro=iniziale, azione="nuovo")


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
            return render_template("libro_form.html", libro=dati, azione="modifica")
        try:
            nuova_copertina = _salva_copertina(request.files.get("copertina"))
        except ValueError as e:
            flash(str(e), "danger")
            dati["id"] = libro_id
            dati["copertina"] = libro["copertina"]
            return render_template("libro_form.html", libro=dati, azione="modifica")

        # Se e' stata caricata una nuova copertina, rimuovi la vecchia
        if nuova_copertina:
            _rimuovi_copertina(libro["copertina"])

        Libro.aggiorna(
            libro_id, dati["titolo"], dati["autore"], dati["anno"],
            dati["descrizione"], dati["lat"], dati["lon"], copertina=nuova_copertina,
        )
        flash("Libro aggiornato.", "success")
        return redirect(url_for("libri.lista"))

    return render_template("libro_form.html", libro=libro, azione="modifica")


@libri_bp.route("/libri/<int:libro_id>/elimina", methods=["POST"])
@login_richiesto
def elimina(libro_id):
    libro = _libro_di_proprieta(libro_id)
    _rimuovi_copertina(libro["copertina"])
    Libro.elimina(libro_id)
    flash("Libro eliminato.", "info")
    return redirect(url_for("libri.lista"))


def _leggi_form():
    """Legge e valida i campi del form libro.

    Restituisce (dati, errore): 'errore' e' None se i dati sono validi.
    """
    dati = {
        "titolo": request.form.get("titolo", "").strip(),
        "autore": request.form.get("autore", "").strip(),
        "descrizione": request.form.get("descrizione", "").strip() or None,
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

    # Coordinate: obbligatorie e numeriche (la geolocalizzazione e' centrale)
    try:
        dati["lat"] = float(request.form.get("lat", "").strip())
        dati["lon"] = float(request.form.get("lon", "").strip())
    except ValueError:
        return dati, "Latitudine e longitudine sono obbligatorie e numeriche."

    return dati, None
