# controllers/mappa.py — Controller della mappa dei libri condivisi (T5).
# Pagina pubblica con la mappa (libreria Leaflet, unica dipendenza esterna
# concordata) di tutti i libri della rete. Il Controller prepara i dati dei
# marcatori in una struttura serializzabile in JSON; il template li passa al
# JavaScript che disegna la mappa (static/js/mappa.js).
from flask import Blueprint, render_template, session

from models.libro import Libro
from models.citta import coordinate_di

mappa_bp = Blueprint("mappa", __name__)


def _raggruppa_per_citta(libri, includi_proprietario=True):
    """Raggruppa i libri per citta' -> lista di marcatori.

    Un solo segnaposto per citta', con il numero di libri come contatore e
    l'elenco nel fumetto: evita segnaposto sovrapposti quando piu' libri
    hanno coordinate vicine ma non identiche. Il marcatore e' posizionato al
    centro citta' (models/citta.py); per citta' non in elenco si usano le
    coordinate del primo libro. lat/lon convertiti da Decimal a float per la
    serializzazione JSON.

    Privacy: con includi_proprietario=False (utente non autenticato) il nome
    di chi condivide NON viene inserito nei dati inviati al browser.
    """
    gruppi = {}
    for libro in libri:
        chiave = libro["citta"]
        if chiave not in gruppi:
            coordinate = coordinate_di(chiave)
            if coordinate is None:
                coordinate = (libro["lat"], libro["lon"])
            gruppi[chiave] = {
                "lat": float(coordinate[0]),
                "lon": float(coordinate[1]),
                "citta": chiave,
                "libri": [],
            }
        voce = {
            "id": libro["id"],
            "titolo": libro["titolo"],
            "autore": libro["autore"],
            "disponibile": bool(libro["disponibile"]),
        }
        if includi_proprietario:
            voce["proprietario"] = "%s %s" % (libro["proprietario_nome"],
                                              libro["proprietario_cognome"])
        gruppi[chiave]["libri"].append(voce)
    return list(gruppi.values())


@mappa_bp.route("/mappa")
def mappa():
    """Mappa di tutti i libri condivisi (pagina pubblica)."""
    libri = Libro.cerca()  # nessun filtro: tutti i libri, con proprietario
    marcatori = _raggruppa_per_citta(
        libri, includi_proprietario="utente_id" in session)
    return render_template("mappa.html",
                           marcatori=marcatori,
                           totale_libri=len(libri))
