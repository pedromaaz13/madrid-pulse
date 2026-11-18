# DATA_SOURCES.md

Registro de fuentes de datos externas. **Estado: PENDING de verificación formal (MP-002/MP-003).** Lo que aquí figura procede de la investigación (`docs/research/`) y debe tratarse como hipótesis de trabajo citada, no como verificación reproducible propia, hasta que MP-002/MP-003 confirmen cada fila con fecha y evidencia.

Cada fuente debe registrar, como mínimo, los campos siguientes (ver `docs/DATA_MODEL.md` para cómo se persisten):

```text
source_id
publisher
dataset_name
source_url
license
attribution_text
fetched_at
source_updated_at
checksum
schema_version
```

## Fuentes candidatas

| source_id | Publisher | Dataset | URL | Licencia (según investigación, UNVERIFIED) | Estado de verificación |
|---|---|---|---|---|---|
| `renfe.gtfs_rt.vehicle_positions` | Renfe | GTFS-RT Vehicle Positions Cercanías | `https://gtfsrt.renfe.com/vehicle_positions.json` | CC BY 4.0 (declarado en portal Renfe Data, a confirmar por dataset) | `PENDING` — MP-003 |
| `renfe.gtfs_rt.trip_updates` | Renfe | GTFS-RT Trip Updates Cercanías | `https://gtfsrt.renfe.com/trip_updates.json` | CC BY 4.0 (a confirmar) | `PENDING` — MP-003 |
| `renfe.gtfs_rt.alerts` | Renfe | GTFS-RT Service Alerts Cercanías | `https://gtfsrt.renfe.com/alerts.json` | CC BY 4.0 (a confirmar) | `PENDING` — MP-003 |
| `renfe.gtfs.static` | Renfe | GTFS estático Cercanías (Fichero_CER) | `https://data.renfe.com/dataset/horarios-cercanias` | CC BY 4.0 (declarado en portal Renfe Data) | `PENDING` — MP-002/MP-003 |
| `crtm.gtfs.cercanias_madrid` | CRTM / Comunidad de Madrid | GTFS Cercanías Madrid | identificado vía NAP del Ministerio (URL exacta a confirmar en MP-002) | Uso comercial y no comercial permitido, con requisitos propios de reutilización/atribución (a confirmar) | `PENDING` — MP-002 |
| `cmadrid.stats.1923861` | Comunidad de Madrid | Estadísticas agregadas | `https://datos.comunidad.madrid/dataset/1923861` | A verificar (período, definición, licencia, granularidad) | `PENDING` — MP-002 |
| `osm.rail_geometry` | OpenStreetMap contributors | Geometría ferroviaria | `https://www.openstreetmap.org/` | ODbL | `PENDING` — confirmar obligaciones de share-alike si se distribuye BD derivada (MP-011) |

## Fuentes de referencia (NO fuentes de datos de producción)

Estas no se consumen como dependencia de Madrid Pulse; se estudian como referencia conceptual de producto/arquitectura, con restricciones distintas:

| Proyecto | URL | Uso permitido | Licencia (según investigación) |
|---|---|---|---|
| Via Península | `https://viapeninsula.gariasf.com/` · repo `https://github.com/gariasf/viapeninsula` | Solo estudio conceptual (arquitectura, ADRs, patrones). **No copiar código.** | AGPL-3.0 (preliminar — inspeccionar LICENSE real antes de cualquier reutilización literal) |
| Valfiguer | `https://trenes.valfiguer.com/` · artículo `https://valfiguer.com/es/blog/despues-de-urda-un-mapa-abierto-de-los-trenes` | Benchmark de funcionalidad/producto, no API de producción | No verificada — no asumir disponibilidad de repo público sin comprobarlo |
| Niltra/cercanias | `https://github.com/Niltra/cercanias` | Referencia conceptual de calidad de datos | MIT (según investigación, confirmar en MP-002) |
| xaviour-ai-2026/atlas-ferroviario | `https://github.com/xaviour-ai-2026/atlas-ferroviario` | Referencia conceptual | A confirmar en MP-002 |

## Reglas de uso

1. No se trata ninguna fuente como "ya validada" sin fecha de verificación y evidencia reproducible registrada aquí.
2. No se consume la API de Valfiguer en producción; es benchmark, no dependencia.
3. No se copia código AGPL de Via Península — ver `docs/legal/LICENSE_MATRIX.md` y [ADR-0006](../adr/0006-licensing-policy.md).
4. Cualquier endpoint o dataset que cambie de contrato respecto a lo aquí documentado debe actualizar esta tabla y registrar el cambio en `docs/DECISIONS.md`.
