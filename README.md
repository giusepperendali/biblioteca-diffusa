# Biblioteca Diffusa

Software web di **geolocalizzazione culturale** per la condivisione del
patrimonio librario di utenti privati.

Project Work del Corso di Studi in *Informatica per le Aziende Digitali (L-31)* —
Università Telematica Pegaso · Tema 4 "Sharing technologies", traccia 14.

## Stack tecnologico

Tutte le tecnologie sono trattate nelle dispense del Corso di Studi.

| Componente | Tecnologia | Insegnamento di riferimento |
|------------|-----------|------------------------------|
| Backend | Python + Flask (pattern MVC) | Tecnologie Web · Programmazione 2 |
| Database | MySQL (relazionale) | Basi di Dati · Programmazione 2 |
| Frontend | HTML + CSS + Bootstrap + JS | Tecnologie Web |
| Mappa | Leaflet | Tecnologie Web (integrazione JS) |
| Geolocalizzazione | colonne lat/lon + formula di Haversine | Basi di Dati · Programmazione 2 |
| Miniature copertine | Pillow | Programmazione 2 |
| Grafici statistiche | matplotlib (lato server) | Programmazione 2 |
| Sicurezza | HTTPS/TLS + hashing SHA | Cybersecurity |

## Struttura del progetto (MVC)

```
.
├── app.py             # Inizializzazione Flask (punto d'ingresso)
├── config.py          # Configurazione (chiave segreta, parametri MySQL)
├── requirements.txt   # Dipendenze Python
├── controllers/       # Controller: rotte e logica applicativa (Blueprint)
├── models/            # Model: accesso e persistenza dati su MySQL
├── views/
│   └── templates/     # View: template HTML (Jinja2 + Bootstrap)
├── static/            # CSS, JS e immagini
│   ├── css/
│   ├── js/
│   └── uploads/       # Copertine caricate dagli utenti
├── database/          # Script SQL eseguiti all'avvio di MySQL (schema, dati, funzioni)
├── tests/             # Script di verifica
├── docker-compose.yml # Servizio MySQL (Docker)
└── docs/              # Documentazione del Project Work
```

## Database (MySQL via Docker)

Gli script in `database/` vengono eseguiti automaticamente al **primo avvio** del
container, in ordine alfabetico:

| File | Contenuto |
|------|-----------|
| `01_schema.sql` | Schema: tabelle `utenti`, `libri`, `prestiti` (con colonne `lat`/`lon`) |
| `02_seed.sql` | Dati di test (6 utenti, 14 libri, 4 prestiti) |
| `03_haversine.sql` | Funzione SQL `distanza_km()` per la ricerca per distanza |

Avvio del database (chi clona il repository ottiene il DB già popolato):

```powershell
docker compose up -d      # avvia MySQL e carica schema + dati
docker compose down       # ferma il container (i dati restano nel volume)
docker compose down -v    # azzera tutto e ricarica gli script al prossimo avvio
```

Credenziali di sviluppo (in `docker-compose.yml` e `config.py`): database
`biblioteca_diffusa`, utente `biblioteca` / `bibliopw` su `localhost:3306`.
Password di test degli utenti del seed: `password123`.

Verifica rapida del database:

```powershell
.\.venv\Scripts\python.exe tests\test_t1.py
```

## Avvio in locale

```powershell
# 1. Creare e attivare l'ambiente virtuale
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Installare le dipendenze
pip install -r requirements.txt

# 3. Avviare l'applicazione
python app.py
```

L'applicazione sarà raggiungibile su http://127.0.0.1:5000/

## Stato di avanzamento

- [x] **T0** — Setup ambiente e struttura MVC
- [x] **T1** — Database (schema MySQL + dati di test + Haversine)
- [x] **T2** — Autenticazione e profilo utente (registrazione/login, hashing SHA-256, sessioni)
- [ ] **T3** — Gestione libri e miniature
- [ ] **T4** — Ricerca testuale e geospaziale
- [ ] **T5** — Mappa (Leaflet)
- [ ] **T6** — Dettaglio libro e richiesta di prestito
- [ ] **T7** — Dashboard statistiche
- [ ] **T8** — Sicurezza (HTTPS/TLS)
- [ ] **T9** — Documento Pegaso
- [ ] **T10** — Finalizzazione
