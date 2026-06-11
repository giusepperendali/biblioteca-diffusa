# models/libro.py — Model per l'entita' Libro (accesso ai dati su MySQL).
# Operazioni CRUD sui libri di un utente. La copertina e' memorizzata come nome
# di file (l'immagine sta in static/uploads); la "miniatura" e' ottenuta in fase
# di visualizzazione tramite CSS, senza librerie di elaborazione immagini.
from models.db import get_connection


class Libro:
    """Operazioni di persistenza per la tabella 'libri'."""

    @staticmethod
    def crea(utente_id, titolo, autore, anno, descrizione, copertina, citta, lat, lon):
        """Inserisce un nuovo libro e ne restituisce l'id."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO libri
                    (utente_id, titolo, autore, anno, descrizione, copertina, citta, lat, lon)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (utente_id, titolo, autore, anno, descrizione, copertina, citta, lat, lon),
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
    def trova_con_proprietario(libro_id):
        """Restituisce il libro con i dati del proprietario (per la scheda)."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT l.*, u.nome AS proprietario_nome,
                       u.cognome AS proprietario_cognome,
                       u.citta AS proprietario_citta, u.foto AS proprietario_foto
                FROM libri l
                JOIN utenti u ON u.id = l.utente_id
                WHERE l.id = %s
                """,
                (libro_id,),
            )
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def imposta_disponibilita(libro_id, disponibile):
        """Marca il libro come disponibile o meno (gestione prestiti)."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE libri SET disponibile = %s WHERE id = %s",
                (disponibile, libro_id),
            )
            conn.commit()
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
    def aggiorna(libro_id, titolo, autore, anno, descrizione, citta, lat, lon,
                 disponibile=True, copertina=None):
        """Aggiorna i dati di un libro.

        Se 'copertina' e' None la copertina esistente NON viene modificata;
        se e' una stringa, viene sostituita. 'disponibile' permette al
        proprietario di rendere o meno il libro prestabile.
        """
        conn = get_connection()
        cur = conn.cursor()
        try:
            if copertina is None:
                cur.execute(
                    """
                    UPDATE libri
                    SET titolo=%s, autore=%s, anno=%s, descrizione=%s, citta=%s,
                        lat=%s, lon=%s, disponibile=%s
                    WHERE id=%s
                    """,
                    (titolo, autore, anno, descrizione, citta, lat, lon,
                     disponibile, libro_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE libri
                    SET titolo=%s, autore=%s, anno=%s, descrizione=%s, citta=%s,
                        lat=%s, lon=%s, disponibile=%s, copertina=%s
                    WHERE id=%s
                    """,
                    (titolo, autore, anno, descrizione, citta, lat, lon,
                     disponibile, copertina, libro_id),
                )
            conn.commit()
        finally:
            cur.close()
            conn.close()

    # Espressione SQL della distanza in km tra il libro (l.lat, l.lon) e un
    # punto dato: formula di Haversine scritta inline nella query (stessa
    # formula di models/geo.py). Segnaposto, nell'ordine: lat, lat, lon.
    _HAVERSINE_SQL = """(6371.0 * 2 * ASIN(SQRT(
        POW(SIN(RADIANS(l.lat - %s) / 2), 2)
        + COS(RADIANS(%s)) * COS(RADIANS(l.lat))
        * POW(SIN(RADIANS(l.lon - %s) / 2), 2)
    )))"""

    @staticmethod
    def cerca(testo=None, lat=None, lon=None, raggio_km=None,
              escludi_utente_id=None):
        """Ricerca tra i libri condivisi da tutti gli utenti.

        Filtri (combinabili tra loro):
        - testo: ricerca parziale su titolo O autore (operatore LIKE);
        - lat/lon + raggio_km: solo i libri entro 'raggio_km' km dal punto,
          con la distanza calcolata dalla formula di Haversine inline;
        - escludi_utente_id: esclude i libri di quell'utente (chi cerca non
          deve vedere i propri, ma solo quelli degli altri).

        Ogni risultato include nome e cognome del proprietario e, se la
        ricerca e' geospaziale, la colonna calcolata 'distanza_km' (i
        risultati sono ordinati dal piu' vicino).
        """
        campi = "l.*, u.nome AS proprietario_nome, u.cognome AS proprietario_cognome"
        parametri = []

        geospaziale = lat is not None and lon is not None and raggio_km is not None
        if geospaziale:
            campi += ", " + Libro._HAVERSINE_SQL + " AS distanza_km"
            parametri.extend([lat, lat, lon])

        sql = "SELECT " + campi + " FROM libri l JOIN utenti u ON u.id = l.utente_id"

        # Clausole WHERE combinabili (in AND tra loro)
        condizioni = []
        if testo:
            condizioni.append("(l.titolo LIKE %s OR l.autore LIKE %s)")
            parametri.extend(["%" + testo + "%", "%" + testo + "%"])
        if escludi_utente_id is not None:
            condizioni.append("l.utente_id <> %s")
            parametri.append(escludi_utente_id)
        if condizioni:
            sql += " WHERE " + " AND ".join(condizioni)

        if geospaziale:
            # La colonna calcolata si filtra con HAVING (non e' utilizzabile
            # nella clausola WHERE) e si usa anche per l'ordinamento.
            sql += " HAVING distanza_km <= %s ORDER BY distanza_km"
            parametri.append(raggio_km)
        else:
            sql += " ORDER BY l.titolo"

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(sql, parametri)
            return cur.fetchall()
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
