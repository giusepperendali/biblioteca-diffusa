# config.py — Configurazione dell'applicazione.
# I parametri vengono letti da variabili d'ambiente con valori di default
# adatti allo sviluppo locale. La classe Config viene caricata in app.py con
# app.config.from_object("config.Config"), come mostrato nella dispensa MVC FLASK.
import os


class Config:
    # Chiave segreta per la firma dei cookie di sessione (Flask).
    # In sviluppo si usa un default; in esercizio va impostata via ambiente.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-cambiami")

    # --- Parametri di connessione al database MySQL ---
    # Vengono effettivamente utilizzati a partire dal Task "Database" (T1).
    # I default coincidono con il servizio MySQL definito in docker-compose.yml,
    # cosi' l'app si collega senza ulteriore configurazione dopo "docker compose up".
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
    MYSQL_USER = os.environ.get("MYSQL_USER", "biblioteca")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "bibliopw")
    MYSQL_DB = os.environ.get("MYSQL_DB", "biblioteca_diffusa")
