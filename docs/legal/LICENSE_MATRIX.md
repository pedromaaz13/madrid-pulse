# LICENSE_MATRIX.md

Matriz de licencias de todas las fuentes y proyectos de referencia usados por Madrid Pulse. Estado general: **PENDING de verificación formal en MP-002** salvo donde se indique lo contrario. Esta matriz no sustituye la lectura de la licencia original en su fuente.

| Fuente/Proyecto | Licencia declarada por la investigación | Verificado (MP-002) | Implicación para Madrid Pulse |
|---|---|---|---|
| Renfe Data (GTFS/GTFS-RT Cercanías) | Creative Commons Attribution 4.0 | `PENDING` | Reutilización comercial y no comercial permitida; requiere citar fuente, conservar info de actualización, no insinuar respaldo/patrocinio de Renfe. |
| CRTM (GTFS Cercanías Madrid) | Uso comercial y no comercial permitido, con requisitos propios de reutilización/atribución | `PENDING` | Permite obras de valor añadido; revisar requisitos exactos de atribución antes de publicar. |
| OpenStreetMap | ODbL | `PENDING` | Exige atribución (`© OpenStreetMap contributors` visible en UI). Si se distribuye una base de datos derivada, revisar obligaciones de share-alike de esa base derivada — no del software que la consulta. |
| Via Península (repo) | AGPL-3.0 | `PENDING` — inspeccionar LICENSE real del repo antes de cualquier reutilización literal | **No copiar ni importar código.** Solo estudio conceptual de arquitectura, ADRs y patrones. Reutilizar código literal requeriría ADR explícito evaluando obligaciones AGPL sobre la obra derivada — no autorizado por defecto. |
| Valfiguer | No determinada / no verificada | `PENDING` | No se consume su API como dependencia de producción. Benchmark de producto únicamente. |
| Niltra/cercanias | MIT (según investigación) | `PENDING` | Permite estudio y reutilización de patrones de calidad de datos con atribución mínima MIT si se reutiliza código literal (actualmente no se prevé reutilizar código, solo el principio de cobertura vs. puntualidad). |
| xaviour-ai-2026/atlas-ferroviario | No determinada | `PENDING` | Solo referencia conceptual hasta confirmar licencia. |
| Código propio de Madrid Pulse | **Pendiente de decisión del propietario** (MIT / Apache-2.0 / otra) | — | Ver `docs/DECISIONS.md` DEC-002. No bloquea MP-001 a MP-006. |

## Reglas derivadas

- Ningún dato de Renfe/CRTM se presenta sin atribución visible en la UI una vez exista frontend (MP-014).
- Ninguna geometría derivada de OSM se distribuye sin `© OpenStreetMap contributors` visible.
- Ningún código de Via Península se copia literalmente sin un ADR específico que evalúe y acepte las obligaciones AGPL-3.0 correspondientes.
- Esta matriz se actualiza en MP-002 con fecha de verificación real, no solo con lo citado por la investigación.
