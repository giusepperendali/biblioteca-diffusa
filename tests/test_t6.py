# test_t6.py — Verifica del Task T6 (scheda libro e richiesta di prestito).
# Controlla la scheda pubblica del libro, l'invio della richiesta di prestito
# (simulata) con le sue regole (login, no proprietario, no doppioni, no libro
# non disponibile), il ciclo di stati richiesto -> accettato -> restituito e
# richiesto -> rifiutato con l'effetto sulla disponibilita' del libro, e le
# protezioni (solo il proprietario decide). Crea un libro di prova e lo
# elimina al termine (i prestiti collegati si cancellano in cascata).
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.utente import Utente
from models.libro import Libro
from models.prestito import Prestito


def _login(client, email, password="password123"):
    return client.post("/login", data={"email": email, "password": password})


def _prestito_di(richiedente_id, libro_id):
    """Il prestito (piu' recente) di un richiedente per un dato libro."""
    return next((p for p in Prestito.inviati(richiedente_id)
                 if p["libro_id"] == libro_id), None)


def main():
    esiti = []
    app.config["TESTING"] = True

    giulia = Utente.trova_per_email("giulia.rossi@example.com")
    marco = Utente.trova_per_email("marco.bianchi@example.com")
    sofia = Utente.trova_per_email("sofia.esposito@example.com")

    # 1) Scheda pubblica del libro (senza login): dati visibili ma, per
    #    privacy, NIENTE nome del proprietario (solo l'invito ad accedere)
    anonimo = app.test_client()
    r = anonimo.get("/libri/1")
    corpo = r.get_data(as_text=True)
    esiti.append(("scheda pubblica senza nome del proprietario (privacy)",
                  r.status_code == 200 and "Il nome della rosa" in corpo
                  and "Giulia" not in corpo
                  and "per vedere chi lo condivide" in corpo))

    # 2) Scheda di un libro inesistente -> 404
    r = anonimo.get("/libri/99999")
    esiti.append(("scheda libro inesistente -> 404", r.status_code == 404))

    # 3) La richiesta di prestito richiede il login
    r = anonimo.post("/libri/1/richiedi")
    esiti.append(("richiesta protetta senza login",
                  r.status_code == 302 and "/login" in r.headers["Location"]))

    # Libro di prova di Giulia per il ciclo completo
    libro_id = Libro.crea(giulia["id"], "Libro Prestito T6", "Autore T6",
                          2021, None, None, "Roma", 41.9028, 12.4964)

    # 4) Marco invia la richiesta di prestito
    cl_marco = app.test_client()
    _login(cl_marco, "marco.bianchi@example.com")
    cl_marco.post("/libri/%d/richiedi" % libro_id)
    prestito = _prestito_di(marco["id"], libro_id)
    esiti.append(("richiesta di prestito creata",
                  prestito is not None and prestito["stato"] == "richiesto"))

    # 5) Una seconda richiesta dello stesso utente viene bloccata
    r = cl_marco.post("/libri/%d/richiedi" % libro_id, follow_redirects=True)
    n_richieste = sum(1 for p in Prestito.inviati(marco["id"])
                      if p["libro_id"] == libro_id)
    esiti.append(("doppia richiesta bloccata",
                  n_richieste == 1 and "gia'" in r.get_data(as_text=True)))

    # 6) Il proprietario non puo' chiedere in prestito il proprio libro
    cl_giulia = app.test_client()
    _login(cl_giulia, "giulia.rossi@example.com")
    cl_giulia.post("/libri/%d/richiedi" % libro_id)
    esiti.append(("proprietario non puo' auto-richiedere",
                  _prestito_di(giulia["id"], libro_id) is None))

    # 7) /prestiti protetta e con la richiesta nelle due viste
    r = anonimo.get("/prestiti")
    protetta = r.status_code == 302 and "/login" in r.headers["Location"]
    r = cl_marco.get("/prestiti")
    inviata_visibile = "Libro Prestito T6" in r.get_data(as_text=True)
    r = cl_giulia.get("/prestiti")
    ricevuta_visibile = "Libro Prestito T6" in r.get_data(as_text=True)
    esiti.append(("/prestiti protetta e con inviate/ricevute",
                  protetta and inviata_visibile and ricevuta_visibile))

    # 8) Solo il proprietario puo' accettare (il richiedente riceve 403)
    r = cl_marco.post("/prestiti/%d/accetta" % prestito["id"])
    esiti.append(("non proprietario non accetta (403)", r.status_code == 403))

    # 9) Il proprietario accetta: stato 'accettato', libro non disponibile
    novita_prima = Prestito.conta_novita(marco["id"])
    cl_giulia.post("/prestiti/%d/accetta" % prestito["id"])
    prestito_agg = Prestito.trova_per_id(prestito["id"])
    libro_agg = Libro.trova_per_id(libro_id)
    esiti.append(("accettazione -> libro in prestito",
                  prestito_agg["stato"] == "accettato"
                  and not libro_agg["disponibile"]))

    # 9b) L'accettazione notifica il richiedente: badge in navbar e pallino
    #     rosso sul bottone "Dettagli"; la notifica resta finche' Marco non
    #     apre il dettaglio (?apri=<id>), che la segna come letta
    notificato = Prestito.conta_novita(marco["id"]) == novita_prima + 1
    badge = "notifiche-prestiti" in cl_marco.get("/libri").get_data(as_text=True)
    pallino = "notifica-dettagli" in cl_marco.get("/prestiti").get_data(as_text=True)
    ancora_da_leggere = Prestito.conta_novita(marco["id"]) == novita_prima + 1
    corpo = cl_marco.get("/prestiti?apri=%d" % prestito["id"]).get_data(as_text=True)
    letta = Prestito.conta_novita(marco["id"]) == novita_prima
    dettaglio = "ha accettato la tua richiesta" in corpo
    esiti.append(("esito accettato notificato al richiedente",
                  notificato and badge and pallino))
    esiti.append(("apertura del dettaglio segna l'esito come letto",
                  ancora_da_leggere and letta and dettaglio))

    # 10) Libro non disponibile: nuove richieste bloccate
    cl_sofia = app.test_client()
    _login(cl_sofia, "sofia.esposito@example.com")
    cl_sofia.post("/libri/%d/richiedi" % libro_id)
    esiti.append(("richiesta su libro non disponibile bloccata",
                  _prestito_di(sofia["id"], libro_id) is None))

    # 11) Restituzione a due passi.
    # 11a) Il proprietario NON puo' chiudere il prestito da solo: serve prima
    #      la dichiarazione di riconsegna del richiedente
    cl_giulia.post("/prestiti/%d/restituito" % prestito["id"])
    ancora_accettato = Prestito.trova_per_id(prestito["id"])["stato"] == "accettato"
    esiti.append(("conferma impossibile senza dichiarazione di riconsegna",
                  ancora_accettato))

    # 11b) Solo il richiedente puo' dichiarare la riconsegna (altri: 403)
    r = cl_sofia.post("/prestiti/%d/restituzione" % prestito["id"])
    esiti.append(("dichiarazione riconsegna riservata al richiedente (403)",
                  r.status_code == 403))

    # 11c) Il richiedente dichiara la riconsegna: stato 'in_restituzione',
    #      il libro NON e' ancora disponibile, il proprietario ha
    #      un'azione in attesa in piu' (badge)
    attesa_prima = Prestito.conta_in_attesa(giulia["id"])
    cl_marco.post("/prestiti/%d/restituzione" % prestito["id"])
    prestito_agg = Prestito.trova_per_id(prestito["id"])
    esiti.append(("dichiarazione riconsegna -> in_restituzione, libro ancora bloccato",
                  prestito_agg["stato"] == "in_restituzione"
                  and not Libro.trova_per_id(libro_id)["disponibile"]
                  and Prestito.conta_in_attesa(giulia["id"]) == attesa_prima + 1))

    # 11d) La CONFERMA del proprietario chiude il prestito: libro di nuovo
    #      disponibile e riga sparita dall'elenco del richiedente
    cl_giulia.post("/prestiti/%d/restituito" % prestito["id"])
    prestito_agg = Prestito.trova_per_id(prestito["id"])
    esiti.append(("conferma del proprietario -> libro di nuovo disponibile",
                  prestito_agg["stato"] == "restituito"
                  and Libro.trova_per_id(libro_id)["disponibile"]))
    esiti.append(("prestito concluso rimosso dall'elenco del richiedente",
                  _prestito_di(marco["id"], libro_id) is None))

    # 12) Rifiuto: la richiesta di Sofia (ora possibile) viene rifiutata,
    #     il libro resta disponibile e Sofia riceve la notifica dell'esito
    novita_sofia_prima = Prestito.conta_novita(sofia["id"])
    cl_sofia.post("/libri/%d/richiedi" % libro_id)
    prestito_sofia = _prestito_di(sofia["id"], libro_id)
    cl_giulia.post("/prestiti/%d/rifiuta" % prestito_sofia["id"])
    prestito_agg = Prestito.trova_per_id(prestito_sofia["id"])
    libro_agg = Libro.trova_per_id(libro_id)
    esiti.append(("rifiuto -> libro resta disponibile",
                  prestito_agg["stato"] == "rifiutato"
                  and libro_agg["disponibile"]))
    esiti.append(("rifiuto notificato al richiedente",
                  Prestito.conta_novita(sofia["id"]) == novita_sofia_prima + 1))

    # 13) Badge di notifica in navbar: una nuova richiesta incrementa il
    #     contatore delle richieste in attesa del proprietario
    n_prima = Prestito.conta_in_attesa(giulia["id"])
    cl_sofia.post("/libri/%d/richiedi" % libro_id)  # dopo il rifiuto puo' riprovare
    n_dopo = Prestito.conta_in_attesa(giulia["id"])
    corpo = cl_giulia.get("/libri").get_data(as_text=True)
    esiti.append(("contatore richieste in attesa aggiornato", n_dopo == n_prima + 1))
    esiti.append(("badge notifiche visibile in navbar", "notifiche-prestiti" in corpo))

    # 14) Il proprietario gestisce la disponibilita' dal form di modifica
    #     (checkbox): senza spunta -> non disponibile, con spunta -> disponibile
    dati_form = {"titolo": "Libro Prestito T6", "autore": "Autore T6", "citta": "Roma"}
    cl_giulia.post("/libri/%d/modifica" % libro_id, data=dati_form)
    non_disp = not Libro.trova_per_id(libro_id)["disponibile"]
    dati_form["disponibile"] = "on"
    cl_giulia.post("/libri/%d/modifica" % libro_id, data=dati_form)
    di_nuovo_disp = bool(Libro.trova_per_id(libro_id)["disponibile"])
    esiti.append(("disponibilita' gestibile dal form di modifica",
                  non_disp and di_nuovo_disp))

    # 15) Pulizia: eliminando il libro spariscono anche i prestiti (CASCADE)
    cl_giulia.post("/libri/%d/elimina" % libro_id)
    esiti.append(("eliminazione libro -> prestiti in cascata",
                  Libro.trova_per_id(libro_id) is None
                  and Prestito.trova_per_id(prestito["id"]) is None
                  and Prestito.trova_per_id(prestito_sofia["id"]) is None))

    # Esiti
    print("--- Esiti T6 ---")
    tutti_ok = True
    for descrizione, ok in esiti:
        print("  [%s] %s" % ("OK " if ok else "KO ", descrizione))
        tutti_ok = tutti_ok and ok
    print("\n" + ("TUTTI I TEST SUPERATI" if tutti_ok else "ALCUNI TEST FALLITI"))
    assert tutti_ok, "Almeno un test del T6 e' fallito"


if __name__ == "__main__":
    main()
