# genera_certificato.py — Genera il certificato TLS autofirmato per HTTPS (T8).
# Crea la coppia chiave privata RSA + certificato X.509 firmato con SHA-256
# (algoritmi RSA e SHA trattati nelle dispense di Cybersecurity) e la salva
# nella cartella certificati/. Con i file presenti, app.py avvia il server in
# HTTPS: il traffico (credenziali comprese) viaggia cifrato con TLS.
#
# NOTA: un certificato AUTOFIRMATO va bene per lo sviluppo locale (il browser
# mostrera' un avviso, da accettare); in esercizio il certificato verrebbe
# emesso da una Certification Authority riconosciuta.
#
# Uso:  python genera_certificato.py
import datetime
import ipaddress
import os

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

CARTELLA = "certificati"
PERCORSO_CERTIFICATO = os.path.join(CARTELLA, "certificato.pem")
PERCORSO_CHIAVE = os.path.join(CARTELLA, "chiave.pem")
GIORNI_VALIDITA = 365


def genera():
    """Genera chiave privata e certificato autofirmato per localhost."""
    os.makedirs(CARTELLA, exist_ok=True)

    # 1) Chiave privata RSA a 2048 bit (crittografia asimmetrica)
    chiave = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # 2) Certificato X.509 autofirmato: soggetto ed emittente coincidono
    soggetto = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Biblioteca Diffusa (sviluppo)"),
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IT"),
    ])
    adesso = datetime.datetime.now(datetime.timezone.utc)
    certificato = (
        x509.CertificateBuilder()
        .subject_name(soggetto)
        .issuer_name(soggetto)
        .public_key(chiave.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(adesso)
        .not_valid_after(adesso + datetime.timedelta(days=GIORNI_VALIDITA))
        # Nomi per cui il certificato e' valido (accesso locale)
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        )
        # 3) Firma del certificato con la chiave privata, digest SHA-256
        .sign(chiave, hashes.SHA256())
    )

    # 4) Salvataggio in formato PEM (file di testo Base64)
    with open(PERCORSO_CHIAVE, "wb") as f:
        f.write(chiave.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    with open(PERCORSO_CERTIFICATO, "wb") as f:
        f.write(certificato.public_bytes(serialization.Encoding.PEM))

    return PERCORSO_CERTIFICATO, PERCORSO_CHIAVE


if __name__ == "__main__":
    cert, chiave = genera()
    print("Certificato creato: %s" % cert)
    print("Chiave privata    : %s" % chiave)
    print("Ora 'python app.py' avviera' il server in HTTPS (https://127.0.0.1:5000).")
    print("Il certificato e' autofirmato: il browser mostrera' un avviso, e' normale.")
