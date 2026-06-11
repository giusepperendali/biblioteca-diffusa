# test_t4.py — Verifica del Task T4 (ricerca testuale e geospaziale).
# Controlla la ricerca per titolo/autore (LIKE, anche parziale e senza
# distinzione maiuscole/minuscole), la ricerca per distanza con la formula di
# Haversine inline in SQL (coerente con l'equivalente Python in models/geo.py),
# la combinazione dei due filtri e la pagina pubblica /ricerca.
# Non crea dati: usa i libri del seed (non assume che siano gli unici presenti).
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.libro import Libro
from models.citta import coordinate_di
from models.geo import distanza_km

ROMA_LAT, ROMA_LON = coordinate_di("Roma")
MILANO_LAT, MILANO_LON = coordinate_di("Milano")


def main():
    esiti = []
    app.config["TESTING"] = True
    client = app.test_client()

    # 1) /ricerca e' pubblica (accessibile senza login)
    r = client.get("/ricerca")
    esiti.append(("/ricerca pubblica senza login", r.status_code == 200))

    # 2) Ricerca testuale per titolo (parziale)
    trovati = Libro.cerca(testo="rosa")
    esiti.append(("ricerca per titolo ('rosa')",
                  any("Il nome della rosa" == l["titolo"] for l in trovati)))

    # 3) Ricerca testuale per autore, senza distinzione di maiuscole
    minusc = Libro.cerca(testo="calvino")
    maiusc = Libro.cerca(testo="CALVINO")
    esiti.append(("ricerca per autore, case-insensitive",
                  any("invisibili" in l["titolo"] for l in minusc)
                  and len(minusc) == len(maiusc)))

    # 4) I risultati includono i dati del proprietario
    esiti.append(("risultati con nome del proprietario",
                  all("proprietario_nome" in l and "proprietario_cognome" in l
                      for l in trovati) and len(trovati) > 0))

    # 5) Geospaziale: entro 50 km da Roma -> ci sono i libri di Roma,
    #    nessun risultato oltre il raggio
    vicini = Libro.cerca(lat=ROMA_LAT, lon=ROMA_LON, raggio_km=50)
    esiti.append(("entro 50 km da Roma: libri di Roma inclusi",
                  any(l["titolo"] == "Il nome della rosa" for l in vicini)
                  and all(l["distanza_km"] <= 50 for l in vicini)))

    # 6) Geospaziale: il raggio esclude le citta' lontane e include le vicine.
    #    Da Roma: Napoli ~190 km e Firenze ~230 km (incluse con raggio 250),
    #    Milano ~480 km (esclusa).
    medi = Libro.cerca(lat=ROMA_LAT, lon=ROMA_LON, raggio_km=250)
    titoli_medi = [l["titolo"] for l in medi]
    esiti.append(("entro 250 km da Roma: Napoli/Firenze si', Milano no",
                  "L'amica geniale" in titoli_medi          # Napoli
                  and "La Divina Commedia" in titoli_medi   # Firenze
                  and "I promessi sposi" not in titoli_medi # Milano
                  ))

    # 7) Risultati geospaziali ordinati per distanza crescente
    distanze = [l["distanza_km"] for l in medi]
    esiti.append(("risultati ordinati per distanza", distanze == sorted(distanze)))

    # 8) La distanza SQL (Haversine inline) coincide con quella Python (geo.py)
    libro = vicini[0]
    d_python = distanza_km(ROMA_LAT, ROMA_LON, libro["lat"], libro["lon"])
    esiti.append(("distanza SQL coerente con models/geo.py",
                  abs(libro["distanza_km"] - d_python) < 0.1))

    # 9) Ricerca combinata: testo + distanza
    combinata_si = Libro.cerca(testo="promessi", lat=MILANO_LAT, lon=MILANO_LON, raggio_km=50)
    combinata_no = Libro.cerca(testo="promessi", lat=ROMA_LAT, lon=ROMA_LON, raggio_km=50)
    esiti.append(("ricerca combinata testo+distanza",
                  any(l["titolo"] == "I promessi sposi" for l in combinata_si)
                  and len(combinata_no) == 0))

    # 10) Pagina /ricerca: la ricerca testuale mostra il libro trovato
    r = client.get("/ricerca?q=rosa")
    esiti.append(("/ricerca?q=rosa mostra il risultato",
                  r.status_code == 200 and "Il nome della rosa" in r.get_data(as_text=True)))

    # 11) Pagina /ricerca: ricerca geospaziale con distanza indicata
    r = client.get("/ricerca?q=&citta=Roma&raggio=50")
    corpo = r.get_data(as_text=True)
    esiti.append(("/ricerca per citta' mostra le distanze",
                  r.status_code == 200 and "km da Roma" in corpo and "km" in corpo))

    # 12) Form inviato vuoto -> messaggio di avviso, nessuna ricerca
    r = client.get("/ricerca?q=&citta=")
    esiti.append(("form vuoto: avviso all'utente",
                  "Indica un testo" in r.get_data(as_text=True)))

    # 13) Raggio non valido -> si usa il valore predefinito (nessun errore)
    r = client.get("/ricerca?q=&citta=Roma&raggio=abc")
    esiti.append(("raggio non numerico gestito senza errori", r.status_code == 200))

    # Esiti
    print("--- Esiti T4 ---")
    tutti_ok = True
    for descrizione, ok in esiti:
        print("  [%s] %s" % ("OK " if ok else "KO ", descrizione))
        tutti_ok = tutti_ok and ok
    print("\n" + ("TUTTI I TEST SUPERATI" if tutti_ok else "ALCUNI TEST FALLITI"))
    assert tutti_ok, "Almeno un test del T4 e' fallito"


if __name__ == "__main__":
    main()
