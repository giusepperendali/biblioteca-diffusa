-- 03_haversine.sql — Funzione SQL per la distanza geografica (formula di Haversine).
-- Calcola la distanza in chilometri tra due punti dati in (lat, lon), usando il
-- raggio medio terrestre (6371 km). Viene impiegata nella ricerca geospaziale
-- "libri piu' vicini a me" (Task T4), evitando l'uso di tipi spaziali dedicati
-- non trattati nelle dispense di Basi di Dati.
--
-- Esempio d'uso (libri entro 100 km dal centro di Roma, ordinati per distanza):
--   SELECT titolo, distanza_km(41.9028, 12.4964, lat, lon) AS km
--   FROM libri
--   HAVING km <= 100
--   ORDER BY km;

USE biblioteca_diffusa;

DROP FUNCTION IF EXISTS distanza_km;

DELIMITER $$

CREATE FUNCTION distanza_km(
    lat1 DECIMAL(9, 6),
    lon1 DECIMAL(9, 6),
    lat2 DECIMAL(9, 6),
    lon2 DECIMAL(9, 6)
)
RETURNS DOUBLE
DETERMINISTIC
BEGIN
    DECLARE raggio_terra DOUBLE DEFAULT 6371;  -- raggio medio terrestre in km
    -- LEAST(1.0, ...) protegge ACOS da valori marginalmente > 1 dovuti agli
    -- arrotondamenti in virgola mobile (es. distanza tra un punto e se stesso).
    RETURN raggio_terra * ACOS(
        LEAST(1.0,
            COS(RADIANS(lat1)) * COS(RADIANS(lat2)) * COS(RADIANS(lon2) - RADIANS(lon1))
            + SIN(RADIANS(lat1)) * SIN(RADIANS(lat2))
        )
    );
END$$

DELIMITER ;
