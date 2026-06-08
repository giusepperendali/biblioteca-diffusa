# test_t3.py — Verifica del Task T3 (gestione libri e copertine).
# Controlla CRUD dei libri, upload della copertina, rifiuto di estensioni non
# ammesse, protezione (un utente non puo' modificare i libri altrui) ed
# eliminazione con rimozione del file. Pulisce i dati creati al termine.
import sys
import os
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.utente import Utente
from models.libro import Libro


def _login(client, email, password):
    return client.post("/login", data={"email": email, "password": password})


def main():
    esiti = []
    app.config["TESTING"] = True

    giulia = Utente.trova_per_email("giulia.rossi@example.com")
    client = app.test_client()

    # 1) /libri protetto senza login
    r = client.get("/libri")
    esiti.append(("/libri protetto senza login", r.status_code == 302 and "/login" in r.headers["Location"]))

    # 2) Login e accesso alla lista
    _login(client, "giulia.rossi@example.com", "password123")
    r = client.get("/libri")
    esiti.append(("/libri accessibile dopo login", r.status_code == 200))

    n_iniziali = len(Libro.trova_per_utente(giulia["id"]))

    # 3) Creazione libro senza copertina
    r = client.post("/libri/nuovo", data={
        "titolo": "Libro Test T3", "autore": "Autore Test",
        "anno": "2020", "lat": "41.9", "lon": "12.5",
    })
    creato = next((l for l in Libro.trova_per_utente(giulia["id"]) if l["titolo"] == "Libro Test T3"), None)
    esiti.append(("creazione libro", r.status_code == 302 and creato is not None
                  and len(Libro.trova_per_utente(giulia["id"])) == n_iniziali + 1))

    # 4) Creazione libro CON copertina (upload file)
    r = client.post("/libri/nuovo", data={
        "titolo": "Libro Con Copertina", "autore": "A", "lat": "41.9", "lon": "12.5",
        "copertina": (io.BytesIO(b"contenuto-immagine-di-test"), "cover.png"),
    }, content_type="multipart/form-data")
    con_cop = next((l for l in Libro.trova_per_utente(giulia["id"]) if l["titolo"] == "Libro Con Copertina"), None)
    percorso_cover = None
    if con_cop and con_cop["copertina"]:
        percorso_cover = os.path.join(app.static_folder, "uploads", con_cop["copertina"])
    esiti.append(("upload copertina salva il file", percorso_cover is not None and os.path.exists(percorso_cover)))

    # 5) Estensione non ammessa -> rifiutata, nessun libro creato
    r = client.post("/libri/nuovo", data={
        "titolo": "Libro Bad", "autore": "A", "lat": "41.9", "lon": "12.5",
        "copertina": (io.BytesIO(b"x"), "file.exe"),
    }, content_type="multipart/form-data")
    bad = any(l["titolo"] == "Libro Bad" for l in Libro.trova_per_utente(giulia["id"]))
    esiti.append(("estensione non valida rifiutata", (not bad) and "non supportato" in r.get_data(as_text=True)))

    # 6) Modifica del libro
    r = client.post("/libri/%d/modifica" % creato["id"], data={
        "titolo": "Libro Test T3 Modificato", "autore": "Autore Test",
        "lat": "41.9", "lon": "12.5",
    })
    mod = Libro.trova_per_id(creato["id"])
    esiti.append(("modifica libro", r.status_code == 302 and mod["titolo"] == "Libro Test T3 Modificato"))

    # 7) Un altro utente NON puo' modificare i libri di Giulia (403)
    client2 = app.test_client()
    _login(client2, "marco.bianchi@example.com", "password123")
    r = client2.post("/libri/%d/modifica" % creato["id"], data={
        "titolo": "hack", "autore": "x", "lat": "1", "lon": "1",
    })
    esiti.append(("altro utente non puo' modificare (403)", r.status_code == 403))

    # 8) Eliminazione (pulizia) + rimozione del file copertina
    file_cover = con_cop["copertina"]
    client.post("/libri/%d/elimina" % creato["id"])
    client.post("/libri/%d/elimina" % con_cop["id"])
    rimossi = Libro.trova_per_id(creato["id"]) is None and Libro.trova_per_id(con_cop["id"]) is None
    file_rimosso = not os.path.exists(os.path.join(app.static_folder, "uploads", file_cover))
    esiti.append(("eliminazione libri + rimozione file copertina", rimossi and file_rimosso))

    # Esiti
    print("--- Esiti T3 ---")
    tutti_ok = True
    for descrizione, ok in esiti:
        print("  [%s] %s" % ("OK " if ok else "KO ", descrizione))
        tutti_ok = tutti_ok and ok
    print("\n" + ("TUTTI I TEST SUPERATI" if tutti_ok else "ALCUNI TEST FALLITI"))
    assert tutti_ok, "Almeno un test del T3 e' fallito"


if __name__ == "__main__":
    main()
