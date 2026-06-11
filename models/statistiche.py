# models/statistiche.py — Query aggregate per la dashboard statistiche (T7).
# Solo dati aggregati (conteggi e raggruppamenti SQL con GROUP BY): nessuna
# informazione personale degli utenti viene esposta nelle statistiche.
from models.db import get_connection


def _interroga(sql, parametri=None):
    """Esegue una SELECT e restituisce tutte le righe."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql, parametri or ())
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def totali():
    """Numeri principali della rete: utenti, libri, prestiti, citta' coperte."""
    riga = _interroga(
        """
        SELECT
            (SELECT COUNT(*) FROM utenti)                AS utenti,
            (SELECT COUNT(*) FROM libri)                 AS libri,
            (SELECT COUNT(*) FROM prestiti)              AS prestiti,
            (SELECT COUNT(DISTINCT citta) FROM libri)    AS citta
        """
    )[0]
    return riga


def libri_per_citta():
    """Numero di libri condivisi in ogni citta' (ordine decrescente)."""
    return _interroga(
        """
        SELECT citta, COUNT(*) AS n
        FROM libri
        GROUP BY citta
        ORDER BY n DESC, citta
        """
    )


def prestiti_per_stato():
    """Numero di prestiti in ciascuno stato del ciclo di vita."""
    return _interroga(
        """
        SELECT stato, COUNT(*) AS n
        FROM prestiti
        GROUP BY stato
        ORDER BY n DESC
        """
    )


def libri_piu_richiesti(quanti=5):
    """I libri con piu' richieste di prestito ricevute (titolo e conteggio)."""
    return _interroga(
        """
        SELECT l.titolo, COUNT(p.id) AS n
        FROM prestiti p
        JOIN libri l ON l.id = p.libro_id
        GROUP BY l.id, l.titolo
        ORDER BY n DESC, l.titolo
        LIMIT %s
        """,
        (quanti,),
    )


def disponibilita():
    """Quanti libri sono disponibili e quanti in prestito/non disponibili."""
    return _interroga(
        """
        SELECT disponibile, COUNT(*) AS n
        FROM libri
        GROUP BY disponibile
        """
    )
