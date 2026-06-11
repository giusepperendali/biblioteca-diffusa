# test_t7.py — Verifica del Task T7 (dashboard statistiche amministrativa).
# Controlla che /statistiche sia riservata all'admin (redirect per anonimi,
# 403 per gli utenti normali), i numeri coerenti con il database, la
# generazione dei grafici PNG lato server (firma del formato PNG nei byte
# restituiti), il rifiuto di nomi di grafico inesistenti e l'assenza di dati
# personali nella dashboard.
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import statistiche

# I file PNG iniziano sempre con questi 8 byte (firma del formato)
FIRMA_PNG = b"\x89PNG\r\n\x1a\n"


def main():
    esiti = []
    app.config["TESTING"] = True

    # 1) Riservata all'admin: anonimo -> redirect al login; utente normale
    #    -> 403; amministratore -> 200 (vale anche per i PNG dei grafici)
    anonimo = app.test_client()
    r = anonimo.get("/statistiche")
    anonimo_respinto = r.status_code == 302 and "/login" in r.headers["Location"]

    normale = app.test_client()
    normale.post("/login", data={"email": "giulia.rossi@example.com",
                                 "password": "password123"})
    vietata = normale.get("/statistiche").status_code == 403
    grafico_vietato = normale.get("/statistiche/grafico/libri-citta.png").status_code == 403
    esiti.append(("dashboard riservata all'admin",
                  anonimo_respinto and vietata and grafico_vietato))

    client = app.test_client()
    client.post("/login", data={"email": "admin@example.com",
                                "password": "password123"})
    r = client.get("/statistiche")
    corpo = r.get_data(as_text=True)
    esiti.append(("/statistiche raggiungibile dall'admin", r.status_code == 200))

    # 2) I numeri principali in pagina coincidono con i conteggi del DB
    tot = statistiche.totali()
    esiti.append(("totali coerenti con il database",
                  str(tot["utenti"]) in corpo and str(tot["libri"]) in corpo
                  and str(tot["prestiti"]) in corpo and str(tot["citta"]) in corpo))

    # 3) Le query aggregate quadrano tra loro
    somma_citta = sum(r["n"] for r in statistiche.libri_per_citta())
    somma_disp = sum(r["n"] for r in statistiche.disponibilita())
    somma_stati = sum(r["n"] for r in statistiche.prestiti_per_stato())
    esiti.append(("aggregazioni coerenti (libri e prestiti)",
                  somma_citta == tot["libri"] and somma_disp == tot["libri"]
                  and somma_stati == tot["prestiti"]))

    # 4) Ogni grafico viene generato come PNG valido
    for nome in ("libri-citta", "prestiti-stato", "disponibilita", "piu-richiesti"):
        r = client.get("/statistiche/grafico/%s.png" % nome)
        ok = (r.status_code == 200
              and r.mimetype == "image/png"
              and r.data.startswith(FIRMA_PNG))
        esiti.append(("grafico PNG '%s'" % nome, ok))

    # 5) Nome di grafico inesistente -> 404
    r = client.get("/statistiche/grafico/inesistente.png")
    esiti.append(("grafico inesistente -> 404", r.status_code == 404))

    # 6) Privacy: nella dashboard non compaiono i nomi degli utenti del seed
    esiti.append(("nessun dato personale nella dashboard",
                  "Rossi" not in corpo and "Bianchi" not in corpo
                  and "Esposito" not in corpo))

    # Esiti
    print("--- Esiti T7 ---")
    tutti_ok = True
    for descrizione, ok in esiti:
        print("  [%s] %s" % ("OK " if ok else "KO ", descrizione))
        tutti_ok = tutti_ok and ok
    print("\n" + ("TUTTI I TEST SUPERATI" if tutti_ok else "ALCUNI TEST FALLITI"))
    assert tutti_ok, "Almeno un test del T7 e' fallito"


if __name__ == "__main__":
    main()
