# controllers/auth.py — Controller per registrazione, login, logout e profilo.
# Gestisce l'autenticazione tramite sessione Flask (Tecnologie Web) e si appoggia
# al Model Utente per la persistenza e la verifica delle credenziali (SHA-256).
from functools import wraps

from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash
)

from models.utente import Utente

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
