# models/prestito.py — Model per l'entita' Prestito (accesso ai dati su MySQL).
# La richiesta di prestito e' "simulata": non c'e' uno scambio reale, ma il
# ciclo di vita degli stati e' completo (richiesto -> accettato/rifiutato,
# accettato -> restituito), come previsto dalla traccia.
from models.db import get_connection


class Prestito:
    """Operazioni di persistenza per la tabella 'prestiti'."""

    @staticmethod
    def crea(libro_id, richiedente_id):
        """Registra una nuova richiesta di prestito e ne restituisce l'id."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO prestiti (libro_id, richiedente_id) VALUES (%s, %s)",
                (libro_id, richiedente_id),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def trova_per_id(prestito_id):
        """Restituisce il prestito con libro e proprietario, o None.

        Include l'id del proprietario del libro (utile per verificare chi
        puo' accettare/rifiutare la richiesta).
        """
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT p.*, l.titolo, l.utente_id AS proprietario_id
                FROM prestiti p
                JOIN libri l ON l.id = p.libro_id
                WHERE p.id = %s
                """,
                (prestito_id,),
            )
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def attivo(libro_id, richiedente_id):
        """True se l'utente ha gia' una richiesta in corso per quel libro
        (richiesta in attesa, prestito accettato o riconsegna da confermare)."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT COUNT(*) AS n FROM prestiti
                WHERE libro_id = %s AND richiedente_id = %s
                  AND stato IN ('richiesto', 'accettato', 'in_restituzione')
                """,
                (libro_id, richiedente_id),
            )
            return cur.fetchone()["n"] > 0
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def inviati(richiedente_id):
        """Richieste di prestito inviate dall'utente, con libro e proprietario.

        I prestiti conclusi ('restituito') non compaiono: alla conferma della
        restituzione la riga sparisce dall'elenco del richiedente.
        """
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT p.*, l.titolo, l.autore, l.copertina,
                       u.nome AS proprietario_nome, u.cognome AS proprietario_cognome
                FROM prestiti p
                JOIN libri l ON l.id = p.libro_id
                JOIN utenti u ON u.id = l.utente_id
                WHERE p.richiedente_id = %s AND p.stato <> 'restituito'
                ORDER BY p.data_richiesta DESC
                """,
                (richiedente_id,),
            )
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def ricevuti(proprietario_id):
        """Richieste ricevute sui libri dell'utente, con libro e richiedente."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT p.*, l.titolo, l.autore, l.copertina, l.disponibile,
                       u.nome AS richiedente_nome, u.cognome AS richiedente_cognome
                FROM prestiti p
                JOIN libri l ON l.id = p.libro_id
                JOIN utenti u ON u.id = p.richiedente_id
                WHERE l.utente_id = %s
                ORDER BY p.data_richiesta DESC
                """,
                (proprietario_id,),
            )
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def conta_in_attesa(proprietario_id):
        """Numero di azioni che il proprietario deve decidere: richieste di
        prestito in attesa e riconsegne da confermare (badge in navbar)."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT COUNT(*) AS n
                FROM prestiti p
                JOIN libri l ON l.id = p.libro_id
                WHERE l.utente_id = %s
                  AND p.stato IN ('richiesto', 'in_restituzione')
                """,
                (proprietario_id,),
            )
            return cur.fetchone()["n"]
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def conta_novita(richiedente_id):
        """Numero di esiti (accettato/rifiutato/restituito) che il richiedente
        non ha ancora visto (alimenta il badge di notifica in navbar)."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT COUNT(*) AS n FROM prestiti
                WHERE richiedente_id = %s AND notifica_richiedente = TRUE
                """,
                (richiedente_id,),
            )
            return cur.fetchone()["n"]
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def segna_novita_vista(prestito_id, richiedente_id):
        """Segna come letto l'esito di UN prestito (il richiedente ne ha
        aperto il dettaglio). Il filtro su richiedente_id garantisce che
        ognuno possa azzerare solo le proprie notifiche."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                UPDATE prestiti SET notifica_richiedente = FALSE
                WHERE id = %s AND richiedente_id = %s
                """,
                (prestito_id, richiedente_id),
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def cambia_stato(prestito_id, stato, notifica_richiedente=True):
        """Aggiorna lo stato del prestito.

        Per le decisioni del proprietario (accettato/rifiutato) si accende la
        notifica per il richiedente; per le transizioni avviate dal
        richiedente stesso (in_restituzione) o che chiudono il prestito
        togliendo la riga dal suo elenco (restituito) si passa False.
        """
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                UPDATE prestiti
                SET stato = %s, notifica_richiedente = %s
                WHERE id = %s
                """,
                (stato, notifica_richiedente, prestito_id),
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()
