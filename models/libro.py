# models/libro.py — Model per l'entita' Libro (accesso ai dati su MySQL).
# Operazioni CRUD sui libri di un utente. La copertina e' memorizzata come nome
# di file (l'immagine sta in static/uploads); la "miniatura" e' ottenuta in fase
# di visualizzazione tramite CSS, senza librerie di elaborazione immagini.
from models.db import get_connection


class Libro:
    """Operazioni di persistenza per la tabella 'libri'."""

    @staticmethod
    def crea(utente_id, titolo, autore, anno, descrizione, copertina, lat, lon):
        """Inserisce un nuovo libro e ne restituisce l'id."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO libri
                    (utente_id, titolo, autore, anno, descrizione, copertina, lat, lon)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (utente_id, titolo, autore, anno, descrizione, copertina, lat, lon),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def trova_per_id(libro_id):
        """Restituisce il libro con l'id indicato (dict) o None."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM libri WHERE id = %s", (libro_id,))
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def trova_per_utente(utente_id):
        """Restituisce tutti i libri di un utente, dal piu' recente."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT * FROM libri WHERE utente_id = %s ORDER BY data_inserimento DESC",
                (utente_id,),
            )
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def aggiorna(libro_id, titolo, autore, anno, descrizione, lat, lon, copertina=None):
        """Aggiorna i dati di un libro.

        Se 'copertina' e' None la copertina esistente NON viene modificata;
        se e' una stringa, viene sostituita.
        """
        conn = get_connection()
        cur = conn.cursor()
        try:
            if copertina is None:
                cur.execute(
                    """
                    UPDATE libri
                    SET titolo=%s, autore=%s, anno=%s, descrizione=%s, lat=%s, lon=%s
                    WHERE id=%s
                    """,
                    (titolo, autore, anno, descrizione, lat, lon, libro_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE libri
                    SET titolo=%s, autore=%s, anno=%s, descrizione=%s, lat=%s, lon=%s, copertina=%s
                    WHERE id=%s
                    """,
                    (titolo, autore, anno, descrizione, lat, lon, copertina, libro_id),
                )
            conn.commit()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def elimina(libro_id):
        """Elimina un libro dato il suo id."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM libri WHERE id = %s", (libro_id,))
            conn.commit()
        finally:
            cur.close()
            conn.close()
