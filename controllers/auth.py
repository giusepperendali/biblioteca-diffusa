# controllers/auth.py — Controller per registrazione, login, logout e profilo.
# Gestisce l'autenticazione tramite sessione Flask (Tecnologie Web) e si appoggia
# al Model Utente per la persistenza e la verifica delle credenziali (SHA-256).
from functools import wraps

from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash, abort
)

from models.utente import Utente
from immagini import salva_immagine, rimuovi_immagine

auth_bp = Blueprint("auth", __name__)


def login_richiesto(view):
    """Decoratore: protegge una rotta consentendola solo agli utenti autenticati."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "utente_id" not in session:
            flash("Devi accedere per visualizzare questa pagina.", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapper


def admin_richiesto(view):
    """Decoratore: rotta riservata all'amministratore (dashboard statistiche).

    Il ruolo viene verificato sul database (non solo in sessione), cosi' un
    eventuale cambio di ruolo ha effetto immediato.
    """
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "utente_id" not in session:
            flash("Devi accedere per visualizzare questa pagina.", "warning")
            return redirect(url_for("auth.login"))
        utente = Utente.trova_per_id(session["utente_id"])
        if utente is None or utente["ruolo"] != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapper


@auth_bp.route("/registrazione", methods=["GET", "POST"])
def registrazione():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        cognome = request.form.get("cognome", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        citta = request.form.get("citta", "").strip() or None

        # Validazione minima dei campi obbligatori
        if not nome or not cognome or not email or not password:
            flash("Nome, cognome, email e password sono obbligatori.", "danger")
            return render_template("registrazione.html", nome=nome, cognome=cognome, email=email, citta=citta)

        # L'email deve essere univoca
        if Utente.trova_per_email(email):
            flash("Questa email risulta gia' registrata.", "danger")
            return render_template("registrazione.html", nome=nome, cognome=cognome, citta=citta)

        Utente.crea(nome, cognome, email, password, citta)
        flash("Registrazione completata! Ora puoi accedere.", "success")
        return redirect(url_for("auth.login"))

    return render_template("registrazione.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        utente = Utente.verifica_credenziali(email, password)
        if utente:
            # Si memorizzano in sessione solo i dati essenziali
            session["utente_id"] = utente["id"]
            session["utente_nome"] = utente["nome"]
            # Il ruolo serve alla navbar per mostrare le voci da admin
            session["utente_ruolo"] = utente["ruolo"]
            flash("Bentornato, %s!" % utente["nome"], "success")
            return redirect(url_for("auth.profilo"))

        flash("Email o password non corretti.", "danger")
        return render_template("login.html", email=email)

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Disconnessione effettuata.", "info")
    return redirect(url_for("main.home"))


@auth_bp.route("/profilo")
@login_richiesto
def profilo():
    utente = Utente.trova_per_id(session["utente_id"])
    num_libri = Utente.conta_libri(utente["id"])
    return render_template("profilo.html", utente=utente, num_libri=num_libri)


@auth_bp.route("/profilo/foto", methods=["POST"])
@login_richiesto
def carica_foto():
    """Carica o sostituisce la foto del profilo dell'utente."""
    utente = Utente.trova_per_id(session["utente_id"])
    try:
        nuova_foto = salva_immagine(request.files.get("foto"))
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("auth.profilo"))

    if nuova_foto is None:
        flash("Seleziona un'immagine da caricare.", "warning")
        return redirect(url_for("auth.profilo"))

    # Rimuove la foto precedente, se presente, e salva la nuova
    rimuovi_immagine(utente["foto"])
    Utente.aggiorna_foto(utente["id"], nuova_foto)
    flash("Foto del profilo aggiornata.", "success")
    return redirect(url_for("auth.profilo"))


@auth_bp.route("/profilo/foto/rimuovi", methods=["POST"])
@login_richiesto
def rimuovi_foto():
    """Rimuove la foto del profilo dell'utente (file + riferimento nel DB)."""
    utente = Utente.trova_per_id(session["utente_id"])
    if utente["foto"]:
        rimuovi_immagine(utente["foto"])
        Utente.aggiorna_foto(utente["id"], None)
        flash("Foto del profilo rimossa.", "info")
    return redirect(url_for("auth.profilo"))
