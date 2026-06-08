-- 01_schema.sql — Schema relazionale del database "Biblioteca Diffusa".
-- Modello dati a tre entita': utenti, libri, prestiti.
-- La componente geospaziale e' realizzata con coppie di colonne lat/lon
-- (numeriche), su cui si applica la formula di Haversine per la ricerca per
-- distanza (vedi 03_haversine_demo.sql). Soluzione coerente con le dispense di
-- Basi di Dati e Programmazione 2 (nessun tipo spaziale dedicato richiesto).

USE biblioteca_diffusa;

SET NAMES utf8mb4;

-- ---------------------------------------------------------------------------
-- Tabella UTENTI
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS utenti (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    nome                VARCHAR(100)    NOT NULL,
    email               VARCHAR(150)    NOT NULL UNIQUE,
    -- Hash SHA-256 della password in esadecimale (64 caratteri) -> Task T2.
    password_hash       CHAR(64)        NOT NULL,
    citta               VARCHAR(100),
    -- Posizione di riferimento dell'utente (per centratura mappa).
    lat                 DECIMAL(9, 6),
    lon                 DECIMAL(9, 6),
    data_registrazione  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------------
-- Tabella LIBRI
-- Ogni libro appartiene a un utente ed e' geolocalizzato (lat/lon proprie:
-- normalmente coincidono con la posizione del proprietario, ma restano
-- indipendenti per flessibilita').
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS libri (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    utente_id           INT             NOT NULL,
    titolo              VARCHAR(200)    NOT NULL,
    autore              VARCHAR(150)    NOT NULL,
    anno                INT,
    descrizione         TEXT,
    -- Nome file della copertina/miniatura salvata in static/uploads (Task T3).
    copertina           VARCHAR(255),
    lat                 DECIMAL(9, 6)   NOT NULL,
    lon                 DECIMAL(9, 6)   NOT NULL,
    disponibile         BOOLEAN         NOT NULL DEFAULT TRUE,
    data_inserimento    TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_libri_utente
        FOREIGN KEY (utente_id) REFERENCES utenti(id)
        ON DELETE CASCADE,
    -- Indici a supporto delle ricerche piu' frequenti (Task T4).
    INDEX idx_libri_titolo (titolo),
    INDEX idx_libri_autore (autore),
    INDEX idx_libri_posizione (lat, lon)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------------
-- Tabella PRESTITI
-- Richiesta di prestito (simulata) di un libro da parte di un utente diverso
-- dal proprietario. Lo stato segue un piccolo ciclo di vita.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS prestiti (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    libro_id        INT         NOT NULL,
    richiedente_id  INT         NOT NULL,
    stato           ENUM('richiesto', 'accettato', 'rifiutato', 'restituito')
                    NOT NULL DEFAULT 'richiesto',
    data_richiesta  TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_prestiti_libro
        FOREIGN KEY (libro_id) REFERENCES libri(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_prestiti_richiedente
        FOREIGN KEY (richiedente_id) REFERENCES utenti(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
