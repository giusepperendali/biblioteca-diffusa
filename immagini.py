# immagini.py — Utility condivise per il caricamento delle immagini.
# Usate sia per le copertine dei libri (Task T3) sia per la foto del profilo.
# Le immagini vengono salvate in static/uploads con un nome univoco. Non si usa
# alcuna libreria di elaborazione immagini: il ridimensionamento (miniatura)
# avviene in fase di visualizzazione tramite CSS.
import os
import uuid

from flask import current_app

from config import Config


def estensione_consentita(nome_file):
    """True se l'estensione del file e' tra quelle ammesse."""
    return (
        "." in nome_file
        and nome_file.rsplit(".", 1)[1].lower() in Config.ESTENSIONI_COPERTINA
    )


def salva_immagine(file_caricato):
    """Salva l'immagine caricata in static/uploads con un nome univoco.

    Restituisce il nome del file salvato, oppure None se non e' stato caricato
    alcun file. Solleva ValueError se l'estensione non e' ammessa.
    """
    if not file_caricato or file_caricato.filename == "":
        return None
    if not estensione_consentita(file_caricato.filename):
        raise ValueError("Formato immagine non supportato.")

    estensione = file_caricato.filename.rsplit(".", 1)[1].lower()
    nome_univoco = "%s.%s" % (uuid.uuid4().hex, estensione)
    cartella = os.path.join(current_app.static_folder, "uploads")
    os.makedirs(cartella, exist_ok=True)
    file_caricato.save(os.path.join(cartella, nome_univoco))
    return nome_univoco


def rimuovi_immagine(nome_file):
    """Elimina dal disco un'immagine in static/uploads, se presente."""
    if not nome_file:
        return
    percorso = os.path.join(current_app.static_folder, "uploads", nome_file)
    if os.path.exists(percorso):
        os.remove(percorso)
