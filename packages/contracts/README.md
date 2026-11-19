# packages/contracts

Contrato canónico interno de Madrid Pulse, implementado en MP-005 contra las
fixtures reales de MP-004 (a su vez capturadas en vivo en MP-003).

```text
raw.py         Modelos Pydantic que reflejan EXACTAMENTE el JSON bruto de
               Renfe (vehicle_positions, trip_updates, alerts). Ningún campo
               aquí debe existir sin haberse observado realmente.
nucleo.py      Tabla de prefijos de núcleo de Cercanías (verificada en MP-003,
               ver docs/research/MP-003-probe-findings.md §3) y helpers de
               disambiguación — "C5" no es único entre núcleos.
canonical.py   Esquema normalizado interno: VehiclePositionObservation,
               TripUpdateObservation, ServiceAlert, FeedHealth. UTC siempre;
               dato ausente = None, nunca 0; nucleo_prefix se deriva (computed
               field), no se acepta como entrada independiente.
normalize.py   Funciones puras raw -> canonical (sin red, sin base de datos).
tests/         Tests de esquema reales (contra tests/fixtures/) y sintéticos
               (JSON Schema, rechazo de datos inválidos, casos no observados).
```

## Hallazgos de esta tarea (ver ADR-0009/DEC-018)

Construir el contrato contra datos reales reveló que `docs/DATA_MODEL.md`
(escrito antes de cualquier verificación empírica) asumía tres cosas que el
feed real no cumple: `speed_kmh`/`bearing` no se observan nunca, la parada se
identifica por `stopId` no por `stop_sequence`, y las alertas no traen
`effect`/`cause`/`header_text`. `docs/DATA_MODEL.md` y los modelos de este
paquete ya reflejan la realidad observada, no la asumida.

## Ejecutar los tests

```sh
python3 -m unittest discover -s packages/contracts/tests -p 'test_*.py' -v
```

Sin red, sin base de datos — solo lee `tests/fixtures/*.json`.
