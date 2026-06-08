-- 02_seed.sql — Dati di test del database "Biblioteca Diffusa".
-- Popola le tabelle con utenti in diverse citta' italiane (coordinate reali),
-- libri geolocalizzati e alcune richieste di prestito. Eseguito automaticamente
-- al primo avvio del container Docker, cosi' che il DB sia subito utilizzabile.
--
-- NOTA password: per tutti gli utenti di test la password in chiaro e'
-- "password123". Il campo password_hash contiene il relativo SHA-256
-- (gestione hashing implementata nel Task T2 - Autenticazione).

USE biblioteca_diffusa;

SET NAMES utf8mb4;

-- ---------------------------------------------------------------------------
-- UTENTI (id 1..6)
-- ---------------------------------------------------------------------------
INSERT INTO utenti (nome, email, password_hash, citta, lat, lon) VALUES
('Giulia Rossi',    'giulia.rossi@example.com',    'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Roma',    41.902800, 12.496400),
('Marco Bianchi',   'marco.bianchi@example.com',   'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Milano',  45.464200,  9.190000),
('Sofia Esposito',  'sofia.esposito@example.com',  'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Napoli',  40.851800, 14.268100),
('Luca Ferrari',    'luca.ferrari@example.com',    'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Torino',  45.070300,  7.686900),
('Elena Conti',     'elena.conti@example.com',     'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Firenze', 43.769600, 11.255800),
('Davide Greco',    'davide.greco@example.com',    'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Bologna', 44.494900, 11.342600);

-- ---------------------------------------------------------------------------
-- LIBRI (id 1..14) — geolocalizzati nei pressi della citta' del proprietario
-- ---------------------------------------------------------------------------
INSERT INTO libri (utente_id, titolo, autore, anno, descrizione, lat, lon, disponibile) VALUES
-- Giulia Rossi (Roma)
(1, 'Il nome della rosa',          'Umberto Eco',                    1980, 'Giallo storico ambientato in un monastero medievale.',        41.905000, 12.498000, TRUE),
(1, 'Se questo e'' un uomo',        'Primo Levi',                     1947, 'Memoriale della deportazione ad Auschwitz.',                   41.899000, 12.502000, TRUE),
(1, 'Il Gattopardo',               'Giuseppe Tomasi di Lampedusa',   1958, 'Romanzo sul tramonto dell''aristocrazia siciliana.',          41.910000, 12.490000, FALSE),
(1, 'Uno, nessuno e centomila',    'Luigi Pirandello',               1926, 'Romanzo sull''identita'' e la percezione del se''.',          41.930000, 12.520000, TRUE),
-- Marco Bianchi (Milano)
(2, 'I promessi sposi',            'Alessandro Manzoni',             1827, 'Il romanzo storico per eccellenza della letteratura italiana.', 45.466000,  9.188000, TRUE),
(2, 'La coscienza di Zeno',        'Italo Svevo',                    1923, 'Romanzo psicologico in forma di memoriale.',                   45.460000,  9.195000, TRUE),
-- Sofia Esposito (Napoli)
(3, 'L''amica geniale',            'Elena Ferrante',                 2011, 'Storia di amicizia femminile nella Napoli del dopoguerra.',     40.853000, 14.270000, TRUE),
(3, 'Il giorno della civetta',     'Leonardo Sciascia',              1961, 'Romanzo sulla mafia siciliana.',                               40.849000, 14.265000, TRUE),
-- Luca Ferrari (Torino)
(4, 'Le citta'' invisibili',       'Italo Calvino',                  1972, 'Dialoghi immaginari tra Marco Polo e Kublai Khan.',            45.072000,  7.685000, TRUE),
(4, 'Tre uomini in barca',         'Jerome K. Jerome',               1889, 'Classico umoristico di un viaggio sul Tamigi.',                45.068000,  7.690000, TRUE),
-- Elena Conti (Firenze)
(5, 'La Divina Commedia',          'Dante Alighieri',                1320, 'Il poema sacro, viaggio nei tre regni dell''oltretomba.',      43.771000, 11.254000, TRUE),
(5, 'Il Decameron',               'Giovanni Boccaccio',             1353, 'Cento novelle narrate da dieci giovani fiorentini.',           43.768000, 11.258000, TRUE),
-- Davide Greco (Bologna)
(6, 'Q',                           'Luther Blissett',                1999, 'Romanzo storico ambientato nella Riforma protestante.',        44.496000, 11.341000, TRUE),
(6, 'Cuore',                       'Edmondo De Amicis',              1886, 'Diario di un alunno nella scuola dell''Italia post-unitaria.', 44.493000, 11.345000, TRUE);

-- ---------------------------------------------------------------------------
-- PRESTITI — richieste di esempio nei vari stati del ciclo di vita
-- ---------------------------------------------------------------------------
INSERT INTO prestiti (libro_id, richiedente_id, stato) VALUES
(1, 2, 'richiesto'),    -- Marco chiede "Il nome della rosa" a Giulia
(5, 1, 'accettato'),    -- Giulia chiede "I promessi sposi" a Marco
(7, 4, 'restituito'),   -- Luca ha gia' restituito "L'amica geniale" a Sofia
(11, 6, 'rifiutato');   -- Davide ha chiesto "La Divina Commedia" a Elena (rifiutato)
