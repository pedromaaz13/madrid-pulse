-- Huella del catálogo y parámetros con los que se ingirió el ancla.
-- NULL identifica runs históricos sin procedencia de presentación.
ALTER TABLE source_ingestion_run ADD COLUMN anchor_profile text
    DEFAULT NULLIF(current_setting('madrid_pulse.anchor_profile', true), '');
