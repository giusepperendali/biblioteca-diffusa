# models/utente.py — Model per l'entita' Utente (accesso ai dati su MySQL).
# Include l'hashing delle password con SHA-256 (algoritmo SHA trattato in
# Cybersecurity): la password in chiaro non viene mai memorizzata, ma solo il
# suo digest esadecimale.
import hashlib

from models.db import get_connection


def hash_password(password):
    """Restituisce il digest SHA-256 (esadecimale) della password.

    Nota didattica: SHA-256 e' una funzione di hash crittografica
    unidirezionale (Cybersecurity). In un sistema di produzione si
    aggiungerebbe un 'salt' per utente; qui si resta sull'uso base trattato
    nelle dispense.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class Utente:
    """Operazioni di persistenza per la tabella 'utenti'."""

    @staticmethod
    def crea(nome, cognome, email, password, citta=None, lat=None, lon=None):
        """Inserisce un nuovo utente memorizzando l'hash della password.

        Restituisce l'id del nuovo utente.
        """
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO utenti (nome, cognome, email, password_hash, citta, lat, lon)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (nome, cognome, email, hash_password(password), citta, lat, lon),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def trova_per_email(email):
        """Restituisce l'utente con l'email indicata (dict) o None."""
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT * FROM utenti WHERE email = %s", (email,))
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def trova_per_id(utente_id):
        """Restituisce l'utente con l'id indicato (dict) o None."""
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT * FROM utenti WHERE id = %s", (utente_id,))
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def verifica_credenziali(email, password):
        """Verifica email + password. Ritorna l'utente (dict) se valide, altrimenti None."""
        utente = Utente.trova_per_email(email)
        if utente and utente["password_hash"] == hash_password(password):
            return utente
        return None

    @staticmethod
    def conta_libri(utente_id):
        """Numero di libri posseduti dall'utente (per la pagina profilo)."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM libri WHERE utente_id = %s", (utente_id,))
            return cur.fetchone()[0]
        finally:
            cur.close()
            conn.close()
