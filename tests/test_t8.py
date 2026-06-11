# test_t8.py — Verifica del Task T8 (sicurezza: HTTPS/TLS e sessione).
# Controlla la generazione del certificato autofirmato (file PEM validi,
# caricabili dal modulo ssl della libreria standard), le proprieta' del
# certificato (soggetto localhost, chiave RSA 2048, firma SHA-256, validita')
# e le impostazioni di sicurezza del cookie di sessione.
import os
import ssl
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import genera_certificato
from app import app


def main():
    esiti = []

    # 1) La generazione crea i due file PEM
    percorso_cert, percorso_chiave = genera_certificato.genera()
    esiti.append(("certificato e chiave creati",
                  os.path.exists(percorso_cert) and os.path.exists(percorso_chiave)))

    # 2) I file sono in formato PEM (intestazioni standard)
    with open(percorso_cert) as f:
        testo_cert = f.read()
    with open(percorso_chiave) as f:
        testo_chiave = f.read()
    esiti.append(("formato PEM corretto",
                  "BEGIN CERTIFICATE" in testo_cert
                  and "BEGIN PRIVATE KEY" in testo_chiave))

    # 3) La coppia certificato+chiave e' caricabile dal modulo ssl standard
    #    (la stessa operazione fatta da Flask all'avvio in HTTPS)
    try:
        contesto = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        contesto.load_cert_chain(percorso_cert, percorso_chiave)
        caricabile = True
    except ssl.SSLError:
        caricabile = False
    esiti.append(("coppia TLS caricabile dal modulo ssl", caricabile))

    # 4) Proprieta' del certificato: soggetto, algoritmi e validita'
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives.asymmetric import rsa

    with open(percorso_cert, "rb") as f:
        certificato = x509.load_pem_x509_certificate(f.read())
    cn = certificato.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    chiave_pubblica = certificato.public_key()
    adesso = datetime.datetime.now(datetime.timezone.utc)
    esiti.append(("soggetto 'localhost', RSA 2048, firma SHA-256, in validita'",
                  cn == "localhost"
                  and isinstance(chiave_pubblica, rsa.RSAPublicKey)
                  and chiave_pubblica.key_size == 2048
                  and certificato.signature_hash_algorithm.name == "sha256"
                  and certificato.not_valid_before_utc <= adesso
                  <= certificato.not_valid_after_utc))

    # 5) Cookie di sessione protetto: HttpOnly e SameSite impostati
    esiti.append(("cookie di sessione HttpOnly + SameSite=Lax",
                  app.config["SESSION_COOKIE_HTTPONLY"] is True
                  and app.config["SESSION_COOKIE_SAMESITE"] == "Lax"))

    # 6) Le password restano memorizzate come hash SHA-256 (difesa in
    #    profondita' insieme al canale cifrato) — verifica gia' del T2,
    #    qui si ricontrolla il principio sull'utente admin
    from models.utente import Utente, hash_password
    admin = Utente.trova_per_email("admin@example.com")
    esiti.append(("password admin memorizzata come SHA-256",
                  admin is not None
                  and admin["password_hash"] == hash_password("password123")))

    # Esiti
    print("--- Esiti T8 ---")
    tutti_ok = True
    for descrizione, ok in esiti:
        print("  [%s] %s" % ("OK " if ok else "KO ", descrizione))
        tutti_ok = tutti_ok and ok
    print("\n" + ("TUTTI I TEST SUPERATI" if tutti_ok else "ALCUNI TEST FALLITI"))
    assert tutti_ok, "Almeno un test del T8 e' fallito"


if __name__ == "__main__":
    main()
