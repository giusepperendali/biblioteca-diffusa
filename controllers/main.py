# controllers/main.py — Controller delle pagine generali (home).
# Il Controller riceve le richieste, applica la logica e sceglie la View da
# renderizzare. Le rotte sono organizzate in un Blueprint, come da dispensa.
from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    """Pagina iniziale dell'applicazione."""
    return render_template("home.html")
