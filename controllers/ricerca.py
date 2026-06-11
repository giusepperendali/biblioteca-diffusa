# controllers/ricerca.py — Controller della ricerca dei libri condivisi (T4).
# Pagina pubblica (non richiede login): chiunque puo' cercare i libri della
# rete per testo (titolo/autore) e/o per vicinanza geografica, indicando una
# citta' di riferimento e un raggio in km. Le coordinate della citta' vengono
# ricavate dal menu a tendina (models/citta.py) e la distanza e' calcolata
# nella query SQL con la formula di Haversine.
from flask import Blueprint, render_template, request, flash, session

from models.libro import Libro
from models.citta import elenco_citta, coordinate_di

ricerca_bp = Blueprint("ricerca", __name__)

# Raggi di ricerca proposti nel menu a tendina (in km).
RAGGI_KM = (10, 25, 50, 100, 250, 500)
RAGGIO_PREDEFINITO = 50


@ricerca_bp.route("/ricerca")
def cerca():
    """Form di ricerca e relativi risultati (testuale e/o geospaziale)."""
    # 'q' presente tra i parametri = il form e' stato inviato (anche vuoto).
    inviata = "q" in request.args

    testo = request.args.get("q", "").strip()
    citta = request.args.get("citta", "").strip()

    # Raggio: deve essere uno dei valori proposti; altrimenti si usa il default.
    try:
        raggio = int(request.args.get("raggio", RAGGIO_PREDEFINITO))
    except ValueError:
        raggio = RAGGIO_PREDEFINITO
    if raggio not in RAGGI_KM:
        raggio = RAGGIO_PREDEFINITO

    risultati = None
    if inviata:
        lat = lon = None
        if citta:
            coordinate = coordinate_di(citta)
            if coordinate is None:
                flash("Seleziona una citta' valida dall'elenco.", "danger")
                citta = ""
            else:
                lat, lon = coordinate

        if not testo and not citta:
            flash("Indica un testo da cercare oppure una citta'.", "warning")
        else:
            risultati = Libro.cerca(
                testo=testo or None,
                lat=lat, lon=lon,
                raggio_km=raggio if citta else None,
                # Chi e' autenticato non vede i propri libri tra i risultati
                escludi_utente_id=session.get("utente_id"),
            )

    return render_template(
        "ricerca.html",
        testo=testo, citta=citta, raggio=raggio,
        citta_disponibili=elenco_citta(), raggi=RAGGI_KM,
        risultati=risultati,
    )
