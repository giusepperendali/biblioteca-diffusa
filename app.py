# app.py — Inizializzazione dell'applicazione Flask (punto di ingresso)
# Architettura MVC come da dispensa "MVC FLASK" (Tecnologie Web):
#   - models/       -> Model       (gestione e persistenza dei dati, MySQL)
#   - controllers/  -> Controller  (logica applicativa e instradamento richieste, Blueprint)
#   - views/        -> View        (template HTML renderizzati con Jinja2 + Bootstrap)
from flask import Flask

from controllers.main import main_bp
from controllers.auth import auth_bp


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

    return app


app = create_app()


if __name__ == "__main__":
    # Avvio del server di sviluppo. In produzione si userebbe un WSGI server
    # con HTTPS/TLS (vedi Task sicurezza).
    app.run(debug=True)
