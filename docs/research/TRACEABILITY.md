# TRACEABILITY.md

Vincula decisiones y tareas con la evidencia de la investigación original que las fundamenta, y marca explícitamente qué queda como **verificación reproducible pendiente** frente a lo que la investigación cita como ya comprobado.

## Advertencia metodológica

`deep-research-report.md` contiene citas internas de investigación (marcadores `citeturn...`) que respaldan afirmaciones dentro del propio informe. **Esas citas no equivalen por sí mismas a una verificación reproducible por Madrid Pulse** — son evidencia de que la investigación consultó una fuente, no de que el equipo del proyecto haya reproducido esa comprobación. Los enlaces originales (URLs) se conservan íntegros en el documento; lo que debe comprobarse de forma propia está marcado como `PENDING` en `docs/legal/DATA_SOURCES.md`, `docs/DECISIONS.md` y en el backlog (`docs/TASKS.md`, MP-002/MP-003).

## Mapa decisión → evidencia → verificación

| Decisión/ADR | Evidencia en la investigación | Tipo de evidencia | Verificación propia |
|---|---|---|---|
| ADR-0001 (alcance C5) | `MADRID_PULSE_BRIEF_INICIAL.md` §1 | Decisión de producto / preferencia explícita | No aplica — es una decisión, no un hecho a verificar |
| ADR-0002 (fuentes Renfe/CRTM) | `deep-research-report.md` §"Datos, algoritmos, licencias y límites", endpoints `gtfsrt.renfe.com/*` | Hipótesis de trabajo citada por la investigación | `PENDING` — MP-002 (licencia), MP-003 (accesibilidad real) |
| ADR-0003 (almacenamiento híbrido) | `deep-research-report.md` §"Arquitectura objetivo, histórico y coste mínimo"; volumen de referencia de Valfiguer (≈11–21 MB/día) | Extrapolación explícitamente señalada como "solo una referencia" por el propio informe | `PENDING` — MP-007/MP-009 (medición real) |
| ADR-0004 (modelo de posición) | `deep-research-report.md` §"Movimiento del tren" | Propuesta de diseño con umbrales marcados como no fijados | `PENDING` — MP-003 (frecuencia real), MP-012 (calibración) |
| ADR-0005 (contrato de API) | `deep-research-report.md` §"Contratos API propios" vs. `MADRID_PULSE_BRIEF_INICIAL.md` §4 | Dos propuestas no idénticas de la misma investigación | `PENDING` — MP-013 (reconciliación formal) |
| ADR-0006 (política AGPL) | `deep-research-report.md` §"Via Península", licencia AGPL-3.0 | Hallazgo de investigación marcado como "preliminar" por el propio informe | `PENDING` — inspección directa del fichero LICENSE del repo de Via Península (no realizada todavía) |
| DEC-006 (fuentes primarias ≠ Valfiguer) | `deep-research-report.md` §"Para el MVP, las fuentes primarias deben ser directamente Renfe" | Recomendación explícita de la investigación | No aplica — es una decisión de diseño adoptada, no un hecho externo |
| Frecuencias de polling (~20s/30s/60s) | `deep-research-report.md` §"Datos, algoritmos, licencias" (atribuido a comportamiento observado de Valfiguer) | Observación de un tercero sobre su propio sistema, **no medición propia** | `PENDING` — MP-003, medir directamente, no asumir |
| Catálogo de anomalías de calidad | `deep-research-report.md` §"calidad de datos", `Niltra/cercanias` | Problemas empíricos reportados por terceros | `PENDING` — confirmar cuáles se reproducen con datos reales propios en MP-008 |

## Qué significa `PENDING` en la práctica

Una fila `PENDING` significa: la investigación da una base razonable para planificar, pero **ninguna tarea posterior puede tratar ese dato como hecho confirmado hasta que la tarea de verificación correspondiente (MP-002/MP-003 principalmente) produzca evidencia propia** (captura real, fecha de verificación, respuesta de endpoint, texto de licencia leído directamente en la fuente).

## Mantenimiento de este documento

Cuando MP-002/MP-003 completen una verificación, esta tabla debe actualizarse para reflejar `VERIFIED (fecha)` en lugar de `PENDING`, con referencia a dónde queda registrada la evidencia (`docs/legal/DATA_SOURCES.md`, logs de MP-003, etc.).
