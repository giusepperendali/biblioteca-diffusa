# test_t5.py — Verifica del Task T5 (mappa dei libri con Leaflet).
# Controlla la pagina pubblica /mappa (inclusione di Leaflet, dati dei
# marcatori nella pagina) e il raggruppamento dei libri per citta' (un
# segnaposto per citta' con contatore), inclusa la conversione delle
# coordinate in float (serializzabilita' JSON).
# Non crea dati: usa i libri del seed (non assume che siano gli unici).
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.libro import Libro
from models.citta import coordinate_di
from controllers.mappa import _raggruppa_per_citta


def main():
    esiti = []
    app.config["TESTING"] = True
    client = app.test_client()

    # 1) /mappa e' pubblica (accessibile senza login)
    r = client.get("/mappa")
    corpo = r.get_data(as_text=True)
    esiti.append(("/mappa pubblica senza login", r.status_code == 200))

    # 2) La pagina include la libreria Leaflet (CSS e JS) e il contenitore
    esiti.append(("pagina con Leaflet e contenitore mappa",
                  "leaflet.css" in corpo and "leaflet.js" in corpo
                  and 'id="mappa"' in corpo))

    # 3) I dati dei marcatori sono nella pagina (titolo di un libro del seed)
    esiti.append(("dati marcatori nella pagina",
                  "Il nome della rosa" in corpo and "MARCATORI" in corpo))

    # 4) Raggruppamento: un marcatore per citta'; nessun libro perso
    libri = Libro.cerca()
    marcatori = _raggruppa_per_citta(libri)
    citta_distinte = {l["citta"] for l in libri}
    n_libri_marcatori = sum(len(m["libri"]) for m in marcatori)
    esiti.append(("un marcatore per citta' distinta",
                  len(marcatori) == len(citta_distinte)))
    esiti.append(("nessun libro perso nel raggruppamento",
                  n_libri_marcatori == len(libri)))

    # 5) I libri di Roma del seed (coordinate vicine ma diverse tra loro)
    #    stanno tutti nello stesso marcatore, al centro citta', con contatore
    roma = next((m for m in marcatori if m["citta"] == "Roma"), None)
    n_roma = sum(1 for l in libri if l["citta"] == "Roma")
    lat_roma, lon_roma = coordinate_di("Roma")
    esiti.append(("libri di Roma in un unico marcatore con contatore",
                  roma is not None and len(roma["libri"]) == n_roma >= 4))
    esiti.append(("marcatore posizionato al centro citta'",
                  roma is not None
                  and roma["lat"] == float(lat_roma) and roma["lon"] == float(lon_roma)))

    # 6) I marcatori sono serializzabili in JSON (lat/lon float, non Decimal)
    try:
        json.dumps(marcatori)
        serializzabile = True
    except TypeError:
        serializzabile = False
    esiti.append(("marcatori serializzabili in JSON", serializzabile))

    # Esiti
    print("--- Esiti T5 ---")
    tutti_ok = True
    for descrizione, ok in esiti:
        print("  [%s] %s" % ("OK " if ok else "KO ", descrizione))
        tutti_ok = tutti_ok and ok
    print("\n" + ("TUTTI I TEST SUPERATI" if tutti_ok else "ALCUNI TEST FALLITI"))
    assert tutti_ok, "Almeno un test del T5 e' fallito"


if __name__ == "__main__":
    main()
