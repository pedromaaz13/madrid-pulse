# LICENSE_MATRIX.md

Matriz de licencias verificada formalmente en MP-002. Fecha de verificación: `2026-11-18`; cierre de evidencia: `2026-11-18T15:16:53Z` (UTC). Esta matriz resume obligaciones operativas y no sustituye el texto original enlazado.

| Fuente/proyecto | Licencia exacta y evidencia oficial | Estado | Implicación para Madrid Pulse |
|---|---|---|---|
| Renfe Data — GTFS estático Cercanías | `CC BY 4.0` en el [recurso oficial](https://data.renfe.com/es/dataset/77525d66-f095-46d0-80c0-37f735d4342f/resource/6f1523c6-a9e3-48e3-9ace-bb107a762be6), más [condiciones Renfe Data](https://data.renfe.com/legal) | `VERIFIED 2026-11-18` | Se permite uso comercial/no comercial, copia, modificación, extracción y combinación. Citar `Origen de los datos: Renfe Operadora`, conservar actualización/metadatos, indicar cambios conforme a CC BY y no insinuar respaldo. |
| Renfe Data — GTFS-RT Vehicle Positions | `CC BY 4.0` en [Ubicación de los vehículos](https://data.renfe.com/dataset/ubicacion-vehiculos), más condiciones Renfe Data | `VERIFIED 2026-11-18` | Mismas obligaciones Renfe. La licencia no garantiza continuidad ni exactitud del feed. |
| Renfe Data — GTFS-RT Trip Updates | `CC BY 4.0` en [Horarios de viaje](https://data.renfe.com/es/dataset/horarios-viaje-cercanias), más condiciones Renfe Data | `VERIFIED 2026-11-18` | Mismas obligaciones Renfe. |
| Renfe Data — GTFS-RT Alerts | `CC BY 4.0` en [Incidencias y avisos](https://data.renfe.com/es/dataset/incidencias-avisos), más condiciones Renfe Data | `VERIFIED 2026-11-18` | Mismas obligaciones Renfe. |
| CRTM — GTFS Cercanías Madrid | [Licencia de datos abiertos y estáticos del CRTM (`CRTM-LDA`)](https://www.crtm.es/licencia-de-uso), enlazada por el [catálogo del dataset](https://datos.comunidad.madrid/dataset/red_de_cercanias_oferta_planificada_horarios_topologia) | `VERIFIED 2026-11-18` | Uso comercial/no comercial y obras de valor añadido permitidos. Al compartir los datos CRTM, mismo tipo de licencia; las obras de valor añadido pueden tener otra. Exige `Powered by CRTM` enlazado, indicar bruto/explotado, conservar metadatos/actualización, no falsear ni sugerir patrocinio. |
| Comunidad de Madrid — estadísticas 1923861 | [`CC BY 4.0`](https://creativecommons.org/licenses/by/4.0/legalcode.es), declarado por el [catálogo](https://datos.comunidad.madrid/dataset/1923861) | `VERIFIED 2026-11-18` | Atribución, enlace a licencia e indicación de cambios. Ámbito declarado: toda España; no confundir con datos operativos exclusivos de Madrid/C5. |
| OpenStreetMap | Open Data Commons Open Database License 1.0 (`ODbL-1.0`) en la [página oficial](https://www.openstreetmap.org/copyright) | `VERIFIED 2026-11-18` | Atribución visible y aviso/enlace ODbL. Consultar o superponer datos no relicencia el software. Distribuir una **base derivada** de OSM exige ofrecer esa base bajo ODbL; una **base colectiva** con capas independientes no extiende automáticamente la reciprocidad a las capas separadas. Clasificar el artefacto antes de MP-011/publicación. |
| Via Península | GNU Affero General Public License v3.0 (`AGPL-3.0`, identificador devuelto por GitHub) en [`LICENSE`](https://github.com/gariasf/viapeninsula/blob/main/LICENSE), blob `fe6b9036...` | `VERIFIED 2026-11-18` | **No copiar ni importar código.** Solo estudio conceptual. Código modificado/derivado servido por red puede exigir ofrecer el código fuente correspondiente (AGPL §13); reutilización literal requiere ADR y decisión explícita. |
| Valfiguer — datos/API | `CC BY 4.0` en su página oficial de [datos y API](https://trenes.valfiguer.com/datos) | `VERIFIED 2026-11-18` | Si se reutilizasen sus datos normalizados, usar el texto de atribución que publica Valfiguer. Madrid Pulse no los usará como upstream de producción. |
| Valfiguer — implementación | No se encontró repositorio público verificable ni licencia de código en el artículo, el servicio o la cuenta pública GitHub inspeccionada | `UNKNOWN 2026-11-18` | No asumir que “abierto” describe el código. Benchmark de producto solamente; ninguna copia de implementación. Ver DEC-016. |
| Niltra/cercanias | MIT License (`MIT`) en [`LICENSE`](https://github.com/Niltra/cercanias/blob/main/LICENSE), blob `3288fcde...` | `VERIFIED 2026-11-18` | Conservar copyright y permiso si se copia una parte sustancial. Uso actual: referencia conceptual, sin código copiado. |
| xaviour-ai-2026/atlas-ferroviario | MIT License para el código, más aviso separado de datos Renfe `CC BY 4.0`, en [`LICENSE`](https://github.com/xaviour-ai-2026/atlas-ferroviario/blob/main/LICENSE), blob `f52bf950...` | `VERIFIED 2026-11-18` | El código es MIT aunque GitHub muestre `NOASSERTION` por el apéndice. No trasladar la licencia del código a los datos ni viceversa. |
| Código propio de Madrid Pulse | Pendiente de decisión del propietario | — | Ver DEC-002. No altera las licencias de datos, pero debe ser compatible con cualquier material que se incorporase; actualmente no se incorpora código de referencia. |

## Resoluciones explícitas

### ODbL: consulta frente a base derivada

- Mostrar un mapa, consultar OSM o mantener una capa independiente junto a datos propios exige atribución, pero no convierte por sí solo el software de Madrid Pulse en ODbL.
- Alterar o construir sobre la base OSM y **distribuir la base resultante** activa el *share-alike*: la base derivada debe ofrecerse bajo ODbL y hacerse disponible conforme a sus términos.
- Antes de publicar la geometría calculada en MP-011 se documentará si el artefacto es base derivada, base colectiva o *produced work*. Hasta entonces no se distribuye una base de geometría derivada sin revisión.

### AGPL: estudio frente a reutilización

- Leer README, ADRs, contratos y patrones de Via Península no incorpora código a Madrid Pulse.
- Copiar, adaptar o derivar su implementación sí puede someter la obra resultante a AGPL; el uso mediante red añade la obligación específica de ofrecer el código fuente correspondiente a quienes interactúan con la versión modificada.
- La política vigente es *clean-room conceptual*: especificación propia e implementación independiente. No se ha copiado código en MP-002.

## Reglas derivadas

- Cada salida de Renfe/CRTM/OSM debe llevar la atribución aplicable descrita en `ATTRIBUTION.md`.
- Metadatos de fuente, licencia y fecha de actualización se preservan en almacenamiento y exportaciones.
- Ninguna licencia verificada garantiza disponibilidad, exactitud, frecuencia o cobertura; esas propiedades se prueban en MP-003.
- Cualquier cambio de licencia o intención de incorporar código AGPL se trata como gate de licencia conforme a ADR-0007.
