# controllers/mappa.py — Controller della mappa dei libri condivisi (T5).
# Pagina pubblica con la mappa (libreria Leaflet, unica dipendenza esterna
# concordata) di tutti i libri della rete. Il Controller prepara i dati dei
# marcatori in una struttura serializzabile in JSON; il template li passa al
# JavaScript che disegna la mappa (static/js/mappa.js).
from flask import Blueprint, render_template

from models.libro import Libro
from models.citta import coordinate_di

mappa_bp = Blueprint("mappa", __name__)


def _raggruppa_per_citta(libri):
    """Raggruppa i libri per citta' -> lista di marcatori.

    Un solo segnaposto per citta', con il numero di libri come contatore e
    l'elenco nel fumetto: evita segnaposto sovrapposti quando piu' libri
    hanno coordinate vicine ma non identiche. Il marcatore e' posizionato al
    centro citta' (models/citta.py); per citta' non in elenco si usano le
    coordinate del primo libro. lat/lon convertiti da Decimal a float per la
    serializzazione JSON.
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
        gruppi[chiave]["libri"].append({
            "id": libro["id"],
            "titolo": libro["titolo"],
            "autore": libro["autore"],
            "proprietario": "%s %s" % (libro["proprietario_nome"],
                                       libro["proprietario_cognome"]),
            "disponibile": bool(libro["disponibile"]),
        })
    return list(gruppi.values())


@mappa_bp.route("/mappa")
def mappa():
    """Mappa di tutti i libri condivisi (pagina pubblica)."""
    libri = Libro.cerca()  # nessun filtro: tutti i libri, con proprietario
    return render_template("mappa.html",
                           marcatori=_raggruppa_per_citta(libri),
                           totale_libri=len(libri))
