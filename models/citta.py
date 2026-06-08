# models/citta.py — Elenco di citta' italiane con le relative coordinate.
# Serve a tradurre la citta' scelta dall'utente (menu a tendina) in una coppia
# (lat, lon), evitando l'inserimento manuale delle coordinate. Soluzione interna
# (un dizionario Python), senza servizi esterni di geocodifica.

# Citta' -> (latitudine, longitudine) del centro citta'.
CITTA = {
    "Ancona": (43.6158, 13.5189),
    "Bari": (41.1171, 16.8719),
    "Bologna": (44.4949, 11.3426),
    "Cagliari": (39.2238, 9.1217),
    "Catania": (37.5079, 15.0830),
    "Firenze": (43.7696, 11.2558),
    "Genova": (44.4056, 8.9463),
    "Lecce": (40.3515, 18.1750),
    "Milano": (45.4642, 9.1900),
    "Napoli": (40.8518, 14.2681),
    "Padova": (45.4064, 11.8768),
    "Palermo": (38.1157, 13.3615),
    "Perugia": (43.1107, 12.3908),
    "Pisa": (43.7228, 10.4017),
    "Roma": (41.9028, 12.4964),
    "Torino": (45.0703, 7.6869),
    "Trento": (46.0700, 11.1190),
    "Trieste": (45.6495, 13.7768),
    "Venezia": (45.4408, 12.3155),
    "Verona": (45.4384, 10.9916),
}


def elenco_citta():
    """Restituisce i nomi delle citta' in ordine alfabetico (per il menu)."""
    return sorted(CITTA.keys())


def coordinate_di(citta):
    """Restituisce (lat, lon) della citta', oppure None se non presente."""
    return CITTA.get(citta)
