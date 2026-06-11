# controllers/statistiche.py — Controller della dashboard statistiche (T7).
# Dashboard AMMINISTRATIVA: l'accesso e' riservato agli utenti con ruolo
# 'admin' (decoratore admin_richiesto). I grafici sono generati LATO SERVER
# con matplotlib (dispensa "Rappresentazione grafica dei dati",
# Programmazione 2): ogni grafico e' un'immagine PNG prodotta al volo da una
# rotta dedicata e inclusa nella pagina con un normale tag <img>.
import io

import matplotlib
matplotlib.use("Agg")  # backend senza finestre: disegna su file/memoria
import matplotlib.pyplot as plt

from flask import Blueprint, render_template, send_file, abort

from models import statistiche
from controllers.auth import admin_richiesto

statistiche_bp = Blueprint("statistiche", __name__)

# Colore identitario del progetto (lo stesso --brand-color del CSS)
COLORE_BRAND = "#d6a447"


@statistiche_bp.route("/statistiche")
@admin_richiesto
def dashboard():
    """Dashboard amministrativa: numeri principali + grafici."""
    return render_template("statistiche.html",
                           totali=statistiche.totali(),
                           piu_richiesti=statistiche.libri_piu_richiesti())


def _png(figura):
    """Serializza la figura matplotlib in PNG e la restituisce al browser."""
    buffer = io.BytesIO()
    figura.savefig(buffer, format="png", bbox_inches="tight", dpi=110)
    plt.close(figura)
    buffer.seek(0)
    return send_file(buffer, mimetype="image/png")


def _grafico_libri_citta():
    """Grafico a barre: libri condivisi per citta'."""
    dati = statistiche.libri_per_citta()
    citta = [r["citta"] for r in dati]
    conteggi = [r["n"] for r in dati]

    figura, assi = plt.subplots(figsize=(7, 4))
    assi.bar(citta, conteggi, color=COLORE_BRAND)
    assi.set_ylabel("Libri condivisi")
    assi.set_title("Libri per città")
    assi.tick_params(axis="x", rotation=45)
    # Asse Y con soli numeri interi (si contano libri)
    assi.yaxis.get_major_locator().set_params(integer=True)
    return figura


def _grafico_prestiti_stato():
    """Grafico a torta: prestiti per stato del ciclo di vita."""
    dati = statistiche.prestiti_per_stato()
    stati = [r["stato"].replace("_", " ") for r in dati]
    conteggi = [r["n"] for r in dati]

    figura, assi = plt.subplots(figsize=(5, 4))
    if conteggi:
        assi.pie(conteggi, labels=stati, autopct="%1.0f%%", startangle=90)
    assi.set_title("Prestiti per stato")
    return figura


def _grafico_disponibilita():
    """Grafico a torta: libri disponibili e in prestito / non disponibili."""
    dati = statistiche.disponibilita()
    etichette = {1: "Disponibili", 0: "Non disponibili"}
    nomi = [etichette[int(r["disponibile"])] for r in dati]
    conteggi = [r["n"] for r in dati]

    figura, assi = plt.subplots(figsize=(5, 4))
    if conteggi:
        assi.pie(conteggi, labels=nomi, autopct="%1.0f%%", startangle=90,
                 colors=[COLORE_BRAND, "#adb5bd"])
    assi.set_title("Disponibilità dei libri")
    return figura


def _grafico_piu_richiesti():
    """Grafico a barre orizzontali: i libri piu' richiesti in prestito."""
    dati = statistiche.libri_piu_richiesti()
    titoli = [r["titolo"] for r in dati]
    conteggi = [r["n"] for r in dati]

    figura, assi = plt.subplots(figsize=(7, 4))
    assi.barh(titoli, conteggi, color=COLORE_BRAND)
    assi.invert_yaxis()  # il piu' richiesto in alto
    assi.set_xlabel("Richieste di prestito ricevute")
    assi.set_title("Libri più richiesti")
    assi.xaxis.get_major_locator().set_params(integer=True)
    return figura


# Nome del grafico nell'URL -> funzione che lo disegna
GRAFICI = {
    "libri-citta": _grafico_libri_citta,
    "prestiti-stato": _grafico_prestiti_stato,
    "disponibilita": _grafico_disponibilita,
    "piu-richiesti": _grafico_piu_richiesti,
}


@statistiche_bp.route("/statistiche/grafico/<nome>.png")
@admin_richiesto
def grafico(nome):
    """Genera e restituisce il grafico richiesto come immagine PNG."""
    if nome not in GRAFICI:
        abort(404)
    return _png(GRAFICI[nome]())
