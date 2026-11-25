# CROSSWALK.md — Equivalencias entre sistemas de identificación

**Fecha:** 2026-11-25. Regla: **un trabajo, un ID canónico.** Los demás identificadores son alias, tracks o subtareas con correspondencia a un `MP-xxx` existente; **no inflan el backlog**. Fuente estructurada: `docs/governance/PROJECT_STATE.json`.

## 1. Fases históricas (F), hitos (H) y tareas (MP)
| Fase `docs/PLAN.md` | Hito | Tareas |
|---|---|---|
| F0 | H0 | MP-001 |
| F1 | H1 | MP-002, MP-003 |
| F2 | H1 | MP-004, MP-005 |
| F3 | H1 | MP-006, MP-007 |
| F4 | H1 | MP-008, MP-009 |
| F5 | H2 | MP-010, MP-011 |
| F6 | H2 | MP-012 |
| F7 | H2 | MP-013 |
| F8 | H2 | MP-014 |
| F9 | H2 | MP-015 |
| F10 (expansión) | H3 (parcial, solo Madrid y solo local) | MP-016 … MP-022 |
| — | AUD | AUD-00 … AUD-09 (auditoría de H3; AUD-02 y AUD-03 comparten informe) |
| — | H4 | MP-023 … MP-035 (planificado; ver §2) |

## 2. H4 ↔ MP (`docs/H4_MP_MAPPING.md`)
H4-11→MP-023 · H4-00→MP-024 · H4-04→MP-025a/b · H4-01→MP-026a/b · H4-10→MP-027 · H4-12→MP-028 · H4-03→MP-029 · H4-05→MP-030 · H4-06→MP-031 · H4-07→MP-032 · H4-08→MP-033 · H4-13→MP-034 · H4-09→MP-035. `H4-02` descartado. Los desgloses `a/b` separan lo independiente de lo dependiente del ADR (026) y el cierre determinista de la validación Live (025).

## 3. Hallazgos (FR) → tarea que los corrige
| FR | Severidad | Corrección planificada |
|---|---|---|
| FR-01 trenes `STOPPED_AT` o sin salir se mueven | P0 | MP-024 (ADR) → MP-025a (cierre determinista) → MP-025b (validación Live) |
| FR-02 `?at=` publica `unknown` con edades negativas | P0 | MP-026a |
| FR-07 snapshot no consistente | P1 (incluido en los 16 P1) | MP-026b |
| FR-19 vigencia GTFS (catálogo vence el 2026-12-19) | **P2**, bloquea publicar | MP-026a |
| Resto de FR (los 16 P1 incluyen FR-07; 24 P2 incluyen FR-19) | — | `docs/audits/hito-03/FINDINGS_REGISTER.md`; registro estructurado en MP-034 |

## 4. MVP 0 (D-01…D-06, `docs/deployment/MVP0_IMPLEMENTATION_PLAN.md`) y Live staging (D-10…D-19)
| D | Qué es | Relación con MP |
|---|---|---|
| D-01 captura 90 min | precursor reducido de MP-028 | usa el colector existente; no sustituye a MP-028 |
| D-02…D-06 | track MVP 0 (demo estática) | **sin equivalente MP**: es un entregable de superficie (contrato de demo + adaptador), no corrección de motor; no bloquea Live ni MP-025/026 |
| D-04 teselas configurables | comparte alcance con MP-027 (fuente de teselas, legal) | coordinar archivos (`MapView.tsx`) |
| D-10 | = **MP-023** | alias (`alias_of`; no cuenta como tarea) |
| D-13 | = parte FR-19 de **MP-026a** | alias (`alias_of`; no cuenta como tarea) |
| D-19 (cierre de FR-01 **y FR-02**) | = **MP-024 + MP-025a/b** (FR-01) **y MP-026a** (FR-02) | solo referencia; no existe como tarea en `PROJECT_STATE.json` |
| D-11, D-12, D-14…D-18 | subalcance de staging **propuesto**, separado de MP-032 local hasta decisión del propietario (`PROPOSAL-STAGING-LIVE`) | no tareas nuevas automáticas |
> **Superado:** las filas D-01…D-07 de la sección «MVP 0» de `docs/deployment/MVP_RELEASE_CHECKLIST.md` (primera versión) quedan sustituidas por `MVP0_IMPLEMENTATION_PLAN.md`; D-10…D-19 siguen vigentes.

## 5. Design Discovery (DES-00…DES-09, `docs/design/DESIGN_DISCOVERY_A_B_C.md`)
Subtareas internas de discovery; **no** son tareas MP ni autorización de H4. Correspondencia: DES-01/DES-08 (baseline y verificación visual) alimentan MP-030 (procedencia y rótulos) y su gate visual; la elección A/B/C es gate humano previo a cualquier rediseño productivo.

## 6. Tareas de estudio ARC/DAT/GEO/UX/SRV/ANA/OPS/REL (`docs/research/COMPARATIVE_ARCHITECTURE_2026-11-24.md` §18)
| Propuesta del estudio | Equivale a |
|---|---|
| ARC-01 ADR de movimiento temporal | MP-024 |
| DAT-01 aislamiento de PostgreSQL | MP-023 |
| DAT-02 captura y calibración | MP-028 |
| MOV-01 modelo de estados y paradas | MP-025a |
| API-01 snapshot coherente | MP-026b |
| API-02 reloj replay | MP-026a |
| GEO-01 completar corredores | MP-029 |
| GEO-02 PoC de grafo | **posterior a la beta**, propuesta (`PROPOSAL-GEO-BUILD`); no es MP-029 |
| GEO-03 build geográfico reproducible | **sin MP**: propuesta (`PROPOSAL-GEO-BUILD`) |
| UX-01 procedencia visual | MP-030 |
| UX-02 basemap vectorial y design system | MP-027 (teselas) + track Design (DES) |
| UX-03 vías compartidas y símbolos | MP-029 + DES-07 |
| UX-04 benchmarks Playwright/MapLibre | MP-033 + DES-08 |
| SRV-01 / SRV-02 snapshot publisher y manifest | **sin MP**: propuesta de extensión (opcional, tras beta) |
| ANA-01 métricas y denominadores | MP-031 |
| OPS-01 / OPS-02 compose, staging, CI/CD, backups | MP-032 (subalcance; propuesta de MP-036 si se separa) |
| OPS-03 soak 72 h y carga | MP-032 / MP-033 |
| REL-01 release-readiness | MP-035 |

## 7. Extensiones posibles — solo propuestas, sin reservar ningún número `MP-`
Registradas en `proposed_extensions` de `PROJECT_STATE.json`; el propietario decide si existen y qué ID reciben:
1. **PROPOSAL-STAGING-LIVE** — staging Live (Docker/Caddy/backups) como tarea propia; solo si MP-032 se desborda.
2. **PROPOSAL-SNAPSHOT-PUBLISHER** — PoC de snapshot publisher y manifest versionado (SRV-01/02); diferido a beta con métricas.
3. **PROPOSAL-GEO-BUILD** — grafo OSM/Geofabrik y build geográfico reproducible (GEO-02/03); solo si el PoC valida.
