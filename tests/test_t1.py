# test_t1.py — Verifica del Task T1 (database e ricerca geospaziale).
# Esegue alcuni controlli sul database popolato dai container Docker:
#  - conteggio righe nelle tre tabelle
#  - ricerca geospaziale (Haversine) con la funzione SQL distanza_km
#  - confronto tra il calcolo SQL e quello Python (models/geo.py)
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.db import get_connection
from models.geo import distanza_km as py_dist

ROMA = (41.9028, 12.4964)


def main():
    conn = get_connection()
    cur = conn.cursor()

    print("--- Conteggio righe ---")
    for tabella in ("utenti", "libri", "prestiti"):
        cur.execute("SELECT COUNT(*) AS n FROM " + tabella)
        print(f"  {tabella:10}: {cur.fetchone()['n']}")

    print("\n--- Libri entro 100 km dal centro di Roma (Haversine SQL) ---")
    cur.execute(
        """
        SELECT titolo, lat, lon, ROUND(distanza_km(%s, %s, lat, lon), 2) AS km
        FROM libri
        HAVING km <= 100
        ORDER BY km
        """,
        ROMA,
    )
    righe = cur.fetchall()
    for r in righe:
        print(f"  {r['km']:>7} km  {r['titolo']}")
    print(f"  Totale entro 100 km: {len(righe)} libri")

    print("\n--- Confronto SQL vs Python (libro piu lontano in lista) ---")
    ultimo = righe[-1]
    sql_km = float(ultimo["km"])
    py_km = py_dist(ROMA[0], ROMA[1], float(ultimo["lat"]), float(ultimo["lon"]))
    coincidono = abs(sql_km - py_km) < 0.05
    print(f"  '{ultimo['titolo']}': SQL={sql_km} km  Python={round(py_km, 2)} km  -> coincidono: {coincidono}")

    print("\n--- Esempio join: prestiti con libro e richiedente ---")
    cur.execute(
        """
        SELECT p.stato, l.titolo, u.nome AS richiedente
        FROM prestiti p
        JOIN libri l   ON l.id = p.libro_id
        JOIN utenti u  ON u.id = p.richiedente_id
        ORDER BY p.id
        """
    )
    for r in cur.fetchall():
        print(f"  [{r['stato']:11}] {r['titolo']} <- {r['richiedente']}")

    cur.close()
    conn.close()
    print("\nTutti i controlli completati.")
    assert coincidono, "SQL e Python NON coincidono!"


if __name__ == "__main__":
    main()
