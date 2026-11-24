# H4_MP_MAPPING.md — Correspondencia `H4-xx` ↔ `MP-023+`

**Estado:** propuesta para aprobación (el propietario ordenó la numeración definitiva `MP-023+` el 2026-11-24; la asignación concreta se confirma al aprobar el plan). Se **conserva** la referencia `H4-xx` en la documentación de planificación (`docs/H4_TASK_MATRIX.md`, `docs/audits/hito-03/NEXT_STEPS_PROPOSAL.md`), que no se reescribe. Implementación **no autorizada**.

| MP | H4 | Tarea | Prioridad | Dependencias (aprobadas) | Gate humano |
|---|---|---|---|---|---|
| **MP-023** | H4-11 | Eliminar defaults peligrosos de PostgreSQL | P1·S | — | — |
| **MP-024** | H4-00 | Enmienda de ADR-0014 (estado de parada) | P0·M | — | **aprobación del ADR-0014 enmendado** |
| **MP-025a** | H4-04 (cierre determinista) | Modelo de estado de parada: implementación y pruebas sobre cortes congelados | P0·L | MP-024 aprobado | revisión del diff real |
| **MP-025b** | H4-04 (validación Live) | Validación en vivo posterior del modelo (salto p50 ≤ 200 m, ≥ 500 pares) | P0·S | MP-025a, MP-028 | — |
| **MP-026a** | H4-01 (independiente) | FR-02 replay `?at=` y FR-19 vigencia del GTFS | P0·S | — (puede ir en paralelo con MP-024) | — |
| **MP-026b** | H4-01 (dependiente del ADR) | FR-07 snapshot consistente (`revision`) | P0·S | MP-024 aprobado (§5) | — |
| MP-027 | H4-10 | Portada, legal y puertas falsables | P1·S | — | teselas; DEC-002/003 |
| MP-028 | H4-12 | Captura en vivo (≥ 2 h, ≥ 3 días) | P1·M | MP-023 | autorizar captura continua local |
| MP-029 | H4-03 | Corredores, ramales y catálogo honesto | P1·L | modelo de segmentos | descargas OSM + atribución |
| MP-030 | H4-05 | Interfaz: procedencia y rótulos veraces | P1·M | contrato de MP-024 | — |
| MP-031 | H4-06 | Métricas de cierre honestas | P1·S | MP-028 | — |
| MP-032 | H4-07 | Operación supervisada local medida | P1·M | MP-023 | host persistente; coste |
| MP-033 | H4-08 | Rendimiento y coste | P1·M | MP-026a/b, MP-032 | DEC-038, DEC-004 |
| MP-034 | H4-13 | Registro estructurado de hallazgos (**trazabilidad; no bloquea los P0**) | P1·S | — | — |
| MP-035 | H4-09 | Gate de publicación | P0 (gate)·M | todos cerrados o `BLOCKED` | decisión de publicar; push/PR/merge |

`H4-02` sigue descartado. Las ampliaciones (AVE/LD/MD) quedan fuera.

## Ajustes pedidos por el propietario (2026-11-24) que cada tarea debe cumplir
- **MP-023:** la prueba de fallo seguro **no se conecta ni escribe** en la base persistente 5433 (se prueba con contenedor desechable y con DSN inválido/ausente; la comprobación se hace por inspección de configuración y por fallo antes de abrir conexión).
- **MP-024:** el ADR enmendado requiere aprobación humana **antes** de MP-025.
- **MP-026:** separa lo independiente (replay/snapshot/GTFS: 026a) de lo que depende del nuevo ADR (026b).
- **MP-025:** separa el **cierre determinista** (025a, cortes congelados) de la **validación Live posterior** (025b); 025a puede cerrar sin 025b y lo declara.
- **Toda tarea:** ejecutor, modelo exacto, esfuerzo, revisor independiente del proveedor contrario, y una prueba de regresión que **falle contra el baseline `beb9434`** y pase tras la corrección (excepciones justificadas por escrito).
