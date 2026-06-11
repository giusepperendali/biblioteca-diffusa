# app.py — Inizializzazione dell'applicazione Flask (punto di ingresso)
# Architettura MVC come da dispensa "MVC FLASK" (Tecnologie Web):
#   - models/       -> Model       (gestione e persistenza dei dati, MySQL)
#   - controllers/  -> Controller  (logica applicativa e instradamento richieste, Blueprint)
#   - views/        -> View        (template HTML renderizzati con Jinja2 + Bootstrap)
import os

from flask import Flask, session

from controllers.main import main_bp
from controllers.auth import auth_bp
from controllers.libri import libri_bp
from controllers.ricerca import ricerca_bp
from controllers.mappa import mappa_bp
from controllers.prestiti import prestiti_bp
from controllers.statistiche import statistiche_bp
from models.prestito import Prestito


def create_app():
    """Application factory: crea e configura l'istanza Flask.

    I template stanno in views/templates (non nella cartella di default
    'templates') perché seguiamo la suddivisione MVC della dispensa, in cui
    la View risiede sotto la cartella views/.
    """
    app = Flask(
        __name__,
        template_folder="views/templates",
        static_folder="static",
    )
    app.config.from_object("config.Config")

    # Registrazione dei Blueprint (un modulo Controller per area funzionale)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(libri_bp)
    app.register_blueprint(ricerca_bp)
    app.register_blueprint(mappa_bp)
    app.register_blueprint(prestiti_bp)
    app.register_blueprint(statistiche_bp)

    # Filtro Jinja per mostrare le date nel formato italiano gg/mm/aaaa.
    @app.template_filter("data_it")
    def data_it(valore):
        if valore is None:
            return ""
        return valore.strftime("%d/%m/%Y")

    # Variabile disponibile in TUTTI i template: notifiche per il badge
    # "Prestiti" in navbar = richieste da decidere sui propri libri (lato
    # proprietario) + esiti non ancora visti (lato richiedente).
    @app.context_processor
    def notifiche_prestiti():
        if "utente_id" in session:
            totale = (Prestito.conta_in_attesa(session["utente_id"])
                      + Prestito.conta_novita(session["utente_id"]))
            return {"notifiche_prestiti": totale}
        return {"notifiche_prestiti": 0}

    return app


app = create_app()


if __name__ == "__main__":
    # --- Sicurezza del canale: HTTPS/TLS (Task T8, dispense Cybersecurity) ---
    # Se il certificato locale esiste (creato con genera_certificato.py),
    # il server parte in HTTPS: tutto il traffico, credenziali comprese,
    # viaggia cifrato con TLS. In produzione si userebbe un WSGI server
    # dietro un certificato emesso da una Certification Authority.
    from genera_certificato import PERCORSO_CERTIFICATO, PERCORSO_CHIAVE

    if os.path.exists(PERCORSO_CERTIFICATO) and os.path.exists(PERCORSO_CHIAVE):
        # Con HTTPS attivo il cookie di sessione viaggia solo su canale cifrato
        app.config["SESSION_COOKIE_SECURE"] = True
        app.run(debug=True,
                ssl_context=(PERCORSO_CERTIFICATO, PERCORSO_CHIAVE))
    else:
        # Certificati assenti: avvio in HTTP semplice (solo sviluppo).
        # Per attivare HTTPS: python genera_certificato.py
        app.run(debug=True)
