# H4_TASK_MATRIX.md — Matriz de tareas del Hito 4 (propuesta para aprobación)

**Estado:** PROPUESTA. No autoriza implementar nada, abrir worktrees de tarea, despachar ni aceptar ADR. Solo el propietario autoriza la serie `MP-023+`.
**Origen:** `docs/audits/hito-03/NEXT_STEPS_PROPOSAL.md` (detalle de cada tarea, problema, fuentes, riesgos y pruebas de cierre) ajustado a `docs/ORCHESTRATION_POLICY.md`. El alcance sigue los hallazgos reales de la auditoría; **este documento solo reasigna modelos y añade la regla de regresión**. Los modelos de la auditoría H3 (`gpt-5.6-*`) constan en su registro y no se reescriben.
**Base:** `beb9434` (baseline de regresión de cada defecto). Esfuerzos: S/M/L como en la propuesta original.

## Reparto

| ID | Pri · esf. | Ejecutor (modelo · esfuerzo) | Revisor, proveedor contrario (modelo · esfuerzo) | Dependencias | Prueba de aceptación principal (comando y umbral en la propuesta) | Gate humano |
|---|---|---|---|---|---|---|
| **H4-13** Registro estructurado de hallazgos *(mejora de trazabilidad, NO dependencia de los P0)* | P1 · S | `gpt-6.2-sol` · medium | `claude-sonnet-5-5` · high | — | `findings.yaml` con los FR-xx de H3; script que regenera recuentos; test que falla si un informe cita una cifra distinta | — |
| **H4-11** Defaults peligrosos de PostgreSQL | P1 · S | `gpt-6.2-sol` · medium | `claude-sonnet-5-5` · high | — | arrancar colector/API sin variables → error y 0 filas; una sola variable; tests se niegan sobre base no desechable; cero literal `5433` fuera de docs/dev; falla en `beb9434` | — |
| **H4-10** Portada, legal y puertas falsables | P1 · S | `claude-sonnet-5-5` · medium | `gpt-6.2-sol` · medium | — | portada sin "no hay código"; fila legal de teselas; una puerta = un número + un comando | proveedor de teselas; DEC-002/003 |
| **H4-00** Enmienda ADR-0014 (estado de parada) | P0 · M | `claude-opus-5-5` · high | `gpt-6.2-astra` · high | — | ADR con 3 alternativas y criterios numéricos; cada FR del sistema S1 cubierto por una regla | **aprobación del ADR antes de H4-04** |
| **H4-04** Modelo de estado de parada (implementación) | P0 · L | `gpt-6.2-astra` · high | `claude-opus-5-5` · high | H4-00 aprobado (calibración con H4-12) | 0/25 `STOPPED_AT` con GPS idéntico publican `speed_mps>0`; 0 pre-salida con avance; `19656` retiene espera; retroceso ≤1 m; DST sin avance fabricado; **todas fallan en `beb9434`** | revisión del diff real |
| **H4-01** Replay, snapshot consistente y vigencia GTFS | P0 · M | `gpt-6.2-sol` · high | `claude-opus-5-5` · high (es P0) | H4-00 §5 para FR-07 | `?at=` sin `unknown`/edades negativas; carrera reproducida → coherente; GTFS vencido detectado; **fallan en `beb9434`** | — |
| **H4-12** Captura en vivo (≥2 h, ≥3 días) | P1 · M | `gpt-6.2-sol` · medium | `claude-sonnet-5-5` · high | H4-11 | cada hipótesis H1–H4 evaluada con su umbral, comandos registrados | autorizar captura continua local |
| **H4-03** Corredores, ramales y catálogo honesto | P1 · L | `gpt-6.2-astra` · high | `claude-opus-5-5` · high | modelo de segmentos (en H4-00 o ADR propio) | por lote: 0 `ChainGap`, paradas ≤150 m, orden monótono, matriz por circulaciones y llamadas; antes/después | descargas OSM + atribución; C4b invertida |
| **H4-05** Interfaz: procedencia y rótulos veraces | P1 · M | `gpt-6.1-terra` · medium/high (React/TS, **sin validación visual propia**) | `claude-sonnet-5-5` · high (revisor con Chrome DevTools, preflight; la validación visual independiente es suya) | contrato de H4-00 §3/§4 | vitest sobre `METHOD_STYLES`; capturas antes/después 1440 y 390×844; **el coordinador reproduce los puntos visuales decisivos** | — |
| **H4-06** Métricas de cierre honestas | P1 · S | `claude-sonnet-5-5` · medium | `gpt-6.2-sol` · high | H4-12 | `route_coverage_pct` no puede ser 100 % por construcción; umbral visible en API y Explore | — |
| **H4-07** Operación supervisada local medida | P1 · M | `gpt-6.2-sol` · medium | `claude-sonnet-5-5` · high | H4-11 | ventana ≥24 h (ideal 72 h) sin huecos inexplicados; carrera de AUD-08 repetida sin "2 runs/1 posición"; restore verificado | host persistente; coste |
| **H4-08** Rendimiento y coste | P1 · M | `gpt-6.2-sol` · high | `claude-sonnet-5-5` · high | H4-01; H4-07 para retención | p50/p95 con 1/10/50/100 clientes; H7a/H7b; benchmark del pool | **DEC-038 y DEC-004 son del propietario** |
| **H4-09** Gate de publicación | P0 · M | `gpt-6.2-astra` · high | `claude-opus-5-5` · high | todos cerrados o `BLOCKED` documentados | cada FR re-evaluado en el nuevo HEAD con su prueba; GO/CONDITIONAL/NO-GO para despliegue público | decisión de publicar; push/PR/merge |

Cambios respecto a `NEXT_STEPS_PROPOSAL.md`: modelos nuevos; **H4-13 nueva** (precondición de la regla de fuente única de verdad); H4-01 y H4-09 pasan a revisor Opus por ser P0; H4-05 sin ejecutor `gpt-6.1-terra` porque **no hay navegador confirmado** para él; H4-02 sigue descartado; ampliaciones (AVE/LD/MD) fuera del H4.

## Orden y concurrencia (≤2 pesados por proveedor)
```text
Fase 0 (baratas, en paralelo):  H4-13 · H4-11 · H4-10
Fase 1:                         H4-00 (gate: aprobación del ADR) ─► H4-04      H4-01 (FR-02/FR-19 ya; FR-07 tras H4-00)
Fase 2:                         H4-12 (tras H4-11)    H4-03 lote 1 (coste cero) ─► lotes 2–3
Fase 3:                         H4-05 (tras contrato H4-00)   H4-06 (tras H4-12)   H4-07 ─► H4-08
Gate:                           H4-09
```
Presupuesto: las tareas con Opus/Astra son las caras (H4-00, H4-04, H4-03, H4-09 y las revisiones P0); el resto va en `medium` salvo justificación.

## Decisiones que requiere el propietario antes de despachar
1. Aprobar este alcance y reparto (o modificarlo).
2. Aprobar la extensión `claude-sonnet-5-5` · high (ejecutor frontend, revisor P1) — ver política §1.
3. `gpt-6.1-terra`: sin navegador en Orca; ¿se mantiene fuera del frontend, o se estudia habilitar navegador (ajuste del sistema, tuyo)?
4. Orden: ¿Fase 0 primero (recomendado) o H4-00 en paralelo?
5. Gates de H4-10 (teselas, licencia) cuando lleguen.

## Decisiones del propietario (2026-11-24) — registradas, implementación NO autorizada
1. Política general de modelos aceptada; `claude-sonnet-5-5` medium (coordinación) y **high** (frontend y revisiones técnicas importantes).
2. `gpt-6.1-terra` disponible para React/TypeScript/frontend **sin navegador**; no es validador visual independiente mientras no tenga acceso verificado (H4-05 reasignado en consecuencia: la validación visual la hace el revisor Claude).
3. Sin más pruebas de humo por ahora (los demás modelos se verifican en su primer despacho real: recibo + argv).
4. H4-13 se mantiene como mejora de trazabilidad, no como dependencia de los P0.
5. Prioridad: H4-11, H4-00, H4-04, H4-01; el gate de aprobación humana de ADR-0014 se conserva antes de H4-04.
6. Antes de despachar cada tarea: ejecutor, modelo exacto, esfuerzo, revisor contrario y pruebas que reproduzcan el defecto original (fallan en `beb9434`).
7. Historial de la auditoría y estado de todas las ramas conservados.
Estado: **Hito 3 y auditoría AUD-00…AUD-09 terminados; Hito 4 solo planificado.**

## Correspondencia con la numeración definitiva
Ver `docs/H4_MP_MAPPING.md` (`H4-xx` ↔ `MP-023+`, con las divisiones MP-025a/b y MP-026a/b pedidas por el propietario el 2026-11-24). La referencia `H4-xx` se conserva en este documento.
