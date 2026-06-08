# models/geo.py — Utilita' geospaziali lato Python.
# Implementazione della formula di Haversine in Python (Programmazione 2),
# equivalente alla stessa formula usata inline nelle query SQL per la ricerca
# per distanza (Basi di Dati). Utile quando il calcolo va fatto in applicazione
# anziche' nella query.
import math

RAGGIO_TERRA_KM = 6371.0  # raggio medio terrestre in chilometri


def distanza_km(lat1, lon1, lat2, lon2):
    """Distanza in km tra due punti (lat, lon) secondo la formula di Haversine."""
    # Conversione da gradi a radianti
    rlat1, rlon1, rlat2, rlon2 = map(math.radians, (lat1, lon1, lat2, lon2))

    d_lat = rlat2 - rlat1
    d_lon = rlon2 - rlon1

    a = (math.sin(d_lat / 2) ** 2
         + math.cos(rlat1) * math.cos(rlat2) * math.sin(d_lon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))

    return RAGGIO_TERRA_KM * c
