-- Solo sobre la base sintética marcada, después de medir la variante truncada.
-- Conserva las cardinalidades. V1 cambia de viaje antes de sus últimas 100
-- filas y su racha actual usa las coordenadas de Atocha de la fixture C5.
WITH recent AS (
    SELECT id FROM vehicle_position_observation WHERE source_vehicle_id = 'V1'
    ORDER BY observed_at DESC, id DESC LIMIT 100
)
UPDATE vehicle_position_observation
SET source_trip_id = CASE WHEN id IN (SELECT id FROM recent)
                          THEN '1022J19502C5' ELSE 'bench-previous-trip' END,
    latitude = 40.4066191, longitude = -3.6894391
WHERE source_vehicle_id = 'V1';
ANALYZE vehicle_position_observation;
