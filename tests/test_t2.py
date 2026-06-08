# test_t2.py — Verifica del Task T2 (autenticazione e profilo).
# Controlla: coerenza dell'hash SHA-256 con i dati di seed, login con utente
# esistente, protezione della rotta /profilo, registrazione di un nuovo utente,
# e logout. Usa il test client di Flask. Pulisce l'utente creato al termine.
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.utente import Utente, hash_password
from models.db import get_connection

EMAIL_TEST = "nuovo.utente.t2@example.com"


def elimina_utente(email):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM utenti WHERE email = %s", (email,))
        conn.commit()
    finally:
        cur.close()
        conn.close()


def main():
    esiti = []

    # 1) L'hash SHA-256 di "password123" coincide con quello nei dati di seed
    atteso = "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f"
    esiti.append(("hash SHA-256 coerente con il seed", hash_password("password123") == atteso))

    app.config["TESTING"] = True
    client = app.test_client()

    # 2) /profilo senza login -> redirect a /login
    r = client.get("/profilo")
    esiti.append(("/profilo protetto (redirect senza login)", r.status_code == 302 and "/login" in r.headers["Location"]))

    # 3) Login con utente di seed
    r = client.post("/login", data={"email": "giulia.rossi@example.com", "password": "password123"})
    esiti.append(("login seed -> redirect a /profilo", r.status_code == 302 and "/profilo" in r.headers["Location"]))

    # 4) /profilo dopo login mostra il nome utente
    r = client.get("/profilo")
    esiti.append(("/profilo accessibile dopo login", r.status_code == 200 and "Giulia Rossi" in r.get_data(as_text=True)))

    # 5) Login con password errata -> niente redirect, messaggio di errore
    client.get("/logout")
    r = client.post("/login", data={"email": "giulia.rossi@example.com", "password": "sbagliata"})
    esiti.append(("login con password errata respinto", r.status_code == 200 and "non corretti" in r.get_data(as_text=True)))

    # 6) Registrazione di un nuovo utente
    elimina_utente(EMAIL_TEST)  # pulizia preventiva
    r = client.post("/registrazione", data={
        "nome": "Utente Prova", "email": EMAIL_TEST,
        "password": "segreta456", "citta": "Genova",
    })
    creato = Utente.trova_per_email(EMAIL_TEST)
    esiti.append(("registrazione crea l'utente", creato is not None and r.status_code == 302))

    # 7) La password del nuovo utente e' salvata come hash (mai in chiaro)
    esiti.append(("password salvata come hash SHA-256",
                  creato is not None
                  and creato["password_hash"] == hash_password("segreta456")
                  and creato["password_hash"] != "segreta456"))

    # 8) Il nuovo utente riesce ad accedere
    r = client.post("/login", data={"email": EMAIL_TEST, "password": "segreta456"})
    esiti.append(("login del nuovo utente", r.status_code == 302 and "/profilo" in r.headers["Location"]))

    # 9) Logout pulisce la sessione (/profilo torna protetto)
    client.get("/logout")
    r = client.get("/profilo")
    esiti.append(("logout -> /profilo di nuovo protetto", r.status_code == 302))

    # Pulizia
    elimina_utente(EMAIL_TEST)

    print("--- Esiti T2 ---")
    tutti_ok = True
    for descrizione, ok in esiti:
        print(f"  [{'OK ' if ok else 'KO '}] {descrizione}")
        tutti_ok = tutti_ok and ok
    print("\n" + ("TUTTI I TEST SUPERATI" if tutti_ok else "ALCUNI TEST FALLITI"))
    assert tutti_ok, "Almeno un test del T2 e' fallito"


if __name__ == "__main__":
    main()
