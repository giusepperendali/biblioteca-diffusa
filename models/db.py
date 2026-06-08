# models/db.py — Gestione della connessione al database MySQL.
# Strato Model dell'architettura MVC: centralizza l'accesso ai dati usando il
# modulo pymysql, lo stesso illustrato nella dispensa "Configurazione e uso di
# un database MySQL con Python" (Programmazione 2). I parametri di connessione
# provengono da config.Config.
import pymysql
import pymysql.cursors

from config import Config


def get_connection():
    """Apre e restituisce una nuova connessione al database MySQL.

    Si usa DictCursor (funzionalita' di pymysql) per ottenere le righe come
    dizionari, accedendo ai campi per nome di colonna invece che per indice.
    Il chiamante e' responsabile della chiusura (connection.close()).
    """
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor,
    )
