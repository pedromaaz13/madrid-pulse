# DATA_SOURCES.md

Registro de fuentes externas de Madrid Pulse. **Licencias verificadas formalmente en MP-002 el `2026-11-18`** contra las páginas oficiales y los ficheros `LICENSE` enlazados en este documento. La verificación de licencia no sustituye el probe técnico de disponibilidad, esquema y cobertura que corresponde a MP-003.

Cada captura persistida debe conservar, como mínimo, los campos siguientes (ver [`docs/DATA_MODEL.md`](../DATA_MODEL.md)):

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

## Fuentes de datos candidatas a producción

| source_id | Publisher | Dataset | source_url | Licencia exacta | Verificación | Restricciones y estado operativo |
|---|---|---|---|---|---|---|
| `renfe.gtfs_rt.vehicle_positions` | Renfe Operadora | Ubicación de los vehículos — GTFS-RT Cercanías | [portal](https://data.renfe.com/dataset/ubicacion-vehiculos) · [JSON](https://gtfsrt.renfe.com/vehicle_positions.json) | Creative Commons Attribution 4.0 International (`CC BY 4.0`) + condiciones generales de [Renfe Data](https://data.renfe.com/legal) | `VERIFIED 2026-11-18` | Citar `Origen de los datos: Renfe Operadora`; identificar dataset y licencia; mencionar última actualización si viene informada; conservar metadatos de actualización y reutilización; no desnaturalizar ni sugerir respaldo/patrocinio. Disponibilidad y esquema: `VERIFIED 2026-11-18` (MP-003) — `200 OK`, JSON real (no protobuf), ~20–22 s de refresco medido, feed **nacional** (C5 existe también en Asturias y Sevilla; ver `docs/research/MP-003-probe-findings.md` §3). |
| `renfe.gtfs_rt.trip_updates` | Renfe Operadora | Horarios de viaje — GTFS-RT Trip Updates Cercanías | [portal](https://data.renfe.com/es/dataset/horarios-viaje-cercanias) · [JSON](https://gtfsrt.renfe.com/trip_updates.json) | `CC BY 4.0` + condiciones generales de Renfe Data | `VERIFIED 2026-11-18` | Mismas condiciones Renfe anteriores. Disponibilidad y esquema: `VERIFIED 2026-11-18` (MP-003) — `200 OK`, incluye `delay` en segundos por parada; cobertura de Madrid en un único poll fue 0/302, `PENDING` confirmar con ventana de monitorización más larga (ver findings §5). |
| `renfe.gtfs_rt.alerts` | Renfe Operadora | Incidencias y avisos — GTFS-RT Service Alerts Cercanías | [portal](https://data.renfe.com/es/dataset/incidencias-avisos) · [JSON](https://gtfsrt.renfe.com/alerts.json) | `CC BY 4.0` + condiciones generales de Renfe Data | `VERIFIED 2026-11-18` | Mismas condiciones Renfe anteriores. Disponibilidad y esquema: `VERIFIED 2026-11-18` (MP-003) — `200 OK`, 82 alertas activas observadas, `routeId` por entidad informada (confirma el `route_id` completo como identificador, no el código de línea). |
| `renfe.gtfs.static` | Renfe Operadora | Horarios cercanías (`Fichero_CER`) — GTFS estático | [recurso oficial](https://data.renfe.com/es/dataset/77525d66-f095-46d0-80c0-37f735d4342f/resource/6f1523c6-a9e3-48e3-9ace-bb107a762be6) · [descarga real](https://ssl.renfe.com/ftransit/Fichero_CER_FOMENTO/fomento_transit.zip) | `CC BY 4.0` + condiciones generales de Renfe Data | `VERIFIED 2026-11-18` | Mismas condiciones Renfe anteriores. Descarga real `VERIFIED 2026-11-18` (MP-003): el enlace del portal es una página CKAN, no el fichero; el enlace de descarga real (`ssl.renfe.com`) funcionó sin el fallo SSL mencionado en MP-002, `200 OK`, zip de 15,7 MB, `Last-Modified` del mismo día. Contiene `agency/calendar/routes/shapes/stop_times/stops/transfers/trips.txt`. |
| `crtm.gtfs.cercanias_madrid` | Consorcio Regional de Transportes de Madrid (CRTM) / Comunidad de Madrid | Oferta planificada de la Red de Cercanías Madrid — horarios y topología GTFS | [catálogo Comunidad de Madrid](https://datos.comunidad.madrid/dataset/red_de_cercanias_oferta_planificada_horarios_topologia) · [NAP](https://nap.transportes.gob.es/ConjuntoDato/Detail/962) | [Licencia de datos abiertos y estáticos del CRTM para su portal de datos abiertos (`CRTM-LDA`)](https://www.crtm.es/licencia-de-uso) | `VERIFIED 2026-11-18` | Uso comercial/no comercial, copia, adaptación y combinación permitidos. Los datos compartidos deben conservar el mismo tipo de licencia; las obras de valor añadido pueden usar otra. Citar CRTM, indicar si son datos brutos o explotados y mostrar `Powered by CRTM` enlazado; conservar metadatos; mantener información actualizada; no falsear, dañar la imagen del sistema ni sugerir patrocinio. Acceso NAP observado con inicio de sesión: disponibilidad técnica `PENDING MP-003`. |
| `cmadrid.stats.1923861` | Comunidad de Madrid; fuente declarada: Observatorio del Ferrocarril de España (MITMS) | Viajeros subidos y bajados en trenes de cercanías por estaciones | [catálogo Comunidad de Madrid](https://datos.comunidad.madrid/dataset/1923861) | Creative Commons Attribution 4.0 International (`CC BY 4.0`) | `VERIFIED 2026-11-18` | Atribuir a Comunidad de Madrid y a la fuente indicada, enlazar la licencia e indicar cambios. Es estadística agregada de toda España, no feed operativo ni fuente exclusiva de C5. |
| `osm.rail_geometry` | OpenStreetMap contributors; publicada por OpenStreetMap Foundation | Datos de OpenStreetMap usados para geometría ferroviaria | [OpenStreetMap](https://www.openstreetmap.org/) · [copyright/licencia](https://www.openstreetmap.org/copyright) | Open Data Commons Open Database License 1.0 (`ODbL-1.0`) | `VERIFIED 2026-11-22` | Atribución visible `© OpenStreetMap contributors` y enlace/aviso ODbL. La mera consulta no relicencia el software cliente. **Clasificación confirmada en MP-011 y extendida en MP-018:** las fixtures congeladas `tests/fixtures/osm_c5_real/` y `tests/fixtures/osm_c4_real/` (extractos de nodos/`ways`/relaciones vía Overpass API, no renders) son bases de datos derivadas en el sentido de ODbL y se distribuyen bajo esa misma licencia con atribución (DEC-024), independientemente de la licencia de código del repositorio (`DEC-002`, pendiente). Relaciones C5: `11331`/`3418148`/`3418149`/`3418150`, agrupadas por `route_master=3418151`; relaciones C4a/C4b: `11332`/`9174510`/`9174511`. Fuente, fecha, checksums y regeneración constan en el `MANIFEST.md` de cada fixture. |

## Proyectos y servicios de referencia

No son dependencias de datos de producción. Sus licencias se registran para evitar que el estudio conceptual se convierta accidentalmente en reutilización de código.

| source_id | Publisher | Dataset/proyecto | source_url | Licencia exacta / estado | Verificación | Restricciones |
|---|---|---|---|---|---|---|
| `reference.viapeninsula` | gariasf | Via Península (código fuente) | [repositorio](https://github.com/gariasf/viapeninsula) · [`LICENSE`](https://github.com/gariasf/viapeninsula/blob/main/LICENSE) | GNU Affero General Public License v3.0 (`AGPL-3.0`, identificador devuelto por GitHub) | `VERIFIED 2026-11-18`; blob `fe6b9036ba1818c79c15f802a586a9711ece2b97` | Solo estudio conceptual. **No copiar ni importar código.** Una obra derivada o una modificación operada por red puede activar obligaciones de código fuente correspondiente (sección 13); cualquier reutilización literal requiere ADR y decisión de licencia. |
| `reference.valfiguer.trenes` | 3XA ECOM LLC / Valfiguer | trenes.valfiguer.com (servicio, API y datos normalizados) | [servicio](https://trenes.valfiguer.com/) · [datos/API](https://trenes.valfiguer.com/datos) · [artículo](https://valfiguer.com/es/blog/despues-de-urda-un-mapa-abierto-de-los-trenes) | Datos/API normalizados: `CC BY 4.0`; **código de la aplicación: licencia desconocida, sin repositorio público verificable localizado** | `PARTIAL 2026-11-18`: licencia de datos verificada; código no verificable | Benchmark de producto únicamente; no API upstream ni reutilización de código. La cuenta pública `github.com/valfiguer` y las páginas oficiales inspeccionadas no enlazaban un repositorio de esta aplicación. Ver DEC-016. |
| `reference.niltra.cercanias` | David Navas (`Niltra`) | `Niltra/cercanias` (código fuente) | [repositorio](https://github.com/Niltra/cercanias) · [`LICENSE`](https://github.com/Niltra/cercanias/blob/main/LICENSE) | MIT License (`MIT`) | `VERIFIED 2026-11-18`; blob `3288fcde6cacddaa0f5183e7627f31e9b23fc292` | Referencia conceptual. Si se copiara una porción sustancial, conservar aviso de copyright y permiso; actualmente no se copia código. |
| `reference.atlas_ferroviario` | Atlas Ferroviario contributors (`xaviour-ai-2026`) | `atlas-ferroviario` (código fuente) | [repositorio](https://github.com/xaviour-ai-2026/atlas-ferroviario) · [`LICENSE`](https://github.com/xaviour-ai-2026/atlas-ferroviario/blob/main/LICENSE) | MIT License para el código fuente (`MIT`), seguida de aviso separado: los datos de tren pertenecen a Renfe y se reutilizan bajo `CC BY 4.0` | `VERIFIED 2026-11-18`; blob `f52bf95013bfcfc1b5cb391d38ffeb2d6a0c406e` | Referencia conceptual. El detector de GitHub devuelve `NOASSERTION` por el aviso añadido, pero el texto real concede MIT al código. Conservar aviso MIT si hubiera copia sustancial; no confundir licencia de código con la de datos. |

## Checklist de evidencia MP-002

Hora de cierre de la comprobación: `2026-11-18T15:16:53Z` (UTC).

| Fuente | URL/fichero accedido realmente | Resultado observado |
|---|---|---|
| Renfe GTFS estático | Recurso `Horarios cercanías` y página legal de Renfe Data | El recurso muestra `Creative Commons Attribution 4.0`; la página legal impone cita, fecha de actualización, conservación de metadatos y prohibición de sugerir respaldo. |
| Renfe Vehicle Positions | Dataset `Ubicación de los vehículos` y página legal | Dataset y recursos JSON/PB muestran `Creative Commons Attribution 4.0`. |
| Renfe Trip Updates | Dataset `Horarios de viaje` y página legal | Dataset y recursos JSON/PB muestran `Creative Commons Attribution 4.0`. |
| Renfe Alerts | Dataset `Incidencias y avisos` y página legal | Dataset y recursos JSON/PB muestran `Creative Commons Attribution 4.0`. |
| CRTM GTFS Cercanías Madrid | Catálogo Comunidad de Madrid, ficha NAP 962 y licencia oficial CRTM | El catálogo identifica `CRTM Licencia de datos abiertos (LDA)`; la licencia oficial contiene las condiciones resumidas arriba. NAP identifica CRTM como responsable. |
| Estadística Comunidad de Madrid 1923861 | Catálogo autonómico y catálogo nacional datos.gob.es | Licencia enlazada a `CC BY 4.0`; se verificó que el ámbito declarado es toda España. |
| OpenStreetMap | Página oficial de copyright/licencia OSM y guía de la OSMF | Datos bajo `ODbL-1.0`, con atribución y *share-alike* al distribuir bases derivadas. |
| Via Península | `LICENSE` real de la rama `main` | Cabecera `GNU AFFERO GENERAL PUBLIC LICENSE — Version 3`; GitHub identifica SPDX `AGPL-3.0`. |
| Valfiguer | Artículo oficial, `/datos`, aviso legal, búsqueda/listado de repos públicos de la cuenta oficial | Datos normalizados bajo `CC BY 4.0`; no se localizó repositorio de implementación ni licencia de código verificable. |
| Niltra/cercanias | `LICENSE` real de la rama `main` | Texto MIT, copyright 2026 David Navas; SPDX `MIT`. |
| atlas-ferroviario | `LICENSE` real de la rama `main` | Texto MIT para código, copyright 2026 Atlas Ferroviario contributors, más aviso de datos Renfe `CC BY 4.0`. |

## Reglas de uso

1. La licencia está verificada; la accesibilidad, esquema, cobertura C5 y estabilidad de los feeds Renfe/CRTM no se dan por verificadas hasta MP-003.
2. Valfiguer se mantiene como benchmark y no como dependencia de producción; la licencia de sus datos no autoriza a suponer una licencia para su implementación.
3. No se copia código de Via Península; ver `LICENSE_MATRIX.md` y [ADR-0006](../adr/0006-licensing-policy.md).
4. Todo cambio de URL, licencia o condiciones debe fecharse y registrarse en `docs/DECISIONS.md`.
