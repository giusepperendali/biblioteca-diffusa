# models/db.py — Gestione della connessione al database MySQL.
# Strato Model dell'architettura MVC: centralizza l'accesso ai dati usando il
# connettore ufficiale mysql-connector-python (Programmazione 2 - uso dei dati
# MySQL da Python). I parametri di connessione provengono da config.Config.
import mysql.connector

from config import Config


def get_connection():
    """Apre e restituisce una nuova connessione al database MySQL.

    Il chiamante e' responsabile della chiusura (connection.close()),
    tipicamente in un blocco try/finally.
    """
    return mysql.connector.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
    )
