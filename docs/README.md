# docs/README.md — Índice canónico

Lee en este orden: [`../README.md`](../README.md) → este índice → [`STATUS.md`](STATUS.md) → [`PLAN.md`](PLAN.md) → [`TASKS.md`](TASKS.md). Estado real a **2026-11-25**: H1–H3 y la auditoría están en `main` (`7583ca5`, etiqueta `h3-local-audited`); **nada está desplegado**; veredicto **NO-GO despliegue público / CONDITIONAL GO código local**; FR-01 y FR-02 (P0) abiertos; H4, MVP 0 y Design están **planificados, no iniciados**.

## Vigente (estado y gobierno)
| Documento | Para qué |
|---|---|
| [`STATUS.md`](STATUS.md) | Portada de estado (sección generada) + bitácora histórica |
| [`PLAN.md`](PLAN.md) | Roadmap narrativo F0–F10 con su estado real |
| [`TASKS.md`](TASKS.md) | Fichas MP-001…022 e índice generado de lo planificado |
| [`roadmap/MILESTONES.md`](roadmap/MILESTONES.md) | Fases e hitos con exit gates (tablas generadas) |
| [`roadmap/RELEASE_ROADMAP.md`](roadmap/RELEASE_ROADMAP.md) | Demo → Live staging → beta → ampliación |
| [`roadmap/CROSSWALK.md`](roadmap/CROSSWALK.md) | Equivalencias F/H/MP/D/DES/FR y estudios ARC/DAT/GEO/UX/OPS |
| [`governance/PROJECT_STATE.json`](governance/PROJECT_STATE.json) | **Fuente estructurada canónica** |
| [`governance/UPDATE_PROTOCOL.md`](governance/UPDATE_PROTOCOL.md) | Transiciones, responsables y cierre |
| [`governance/DISPATCH_LOG.md`](governance/DISPATCH_LOG.md) | Quién ejecutó y revisó cada tarea, modelo, esfuerzo y verificación |
| [`DECISIONS.md`](DECISIONS.md), [`adr/`](adr/) | Decisiones (ADR-0014 y 0015 siguen `Propuesto`) |
| [`CHANGELOG.md`](CHANGELOG.md) | Cambios confirmados |
| [`ORCHESTRATION_POLICY.md`](ORCHESTRATION_POLICY.md), [`ORCHESTRATION_COMPATIBILITY.md`](ORCHESTRATION_COMPATIBILITY.md) | Política y capacidades de agentes |
| [`../AGENTS.md`](../AGENTS.md), [`../CLAUDE.md`](../CLAUDE.md) | Protocolo de colaboración y autoría |

## Vigente (diseño técnico y legal)
[`ARCHITECTURE.md`](ARCHITECTURE.md) · [`DATA_MODEL.md`](DATA_MODEL.md) · [`DATA_CONTRACTS.md`](DATA_CONTRACTS.md) · [`DATA_QUALITY.md`](DATA_QUALITY.md) · [`DEVELOPMENT.md`](DEVELOPMENT.md) · [`legal/`](legal/) (licencias y atribución) · [`../LICENSE`](../LICENSE) y [`../NOTICE.md`](../NOTICE.md).

## Propuestas (no aprobadas)
| Documento | Estado |
|---|---|
| [`plans/MVP_LIVE_END_TO_END.md`](plans/MVP_LIVE_END_TO_END.md) | PROPUESTA 2026-11-24, importada íntegra |
| [`research/COMPARATIVE_ARCHITECTURE_2026-11-24.md`](research/COMPARATIVE_ARCHITECTURE_2026-11-24.md) | Investigación comparativa (Vía Península, Electricity Maps: AGPL, solo estudio conceptual) |
| [`design/DESIGN_DISCOVERY_A_B_C.md`](design/DESIGN_DISCOVERY_A_B_C.md) + [`design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md`](design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md) | Discovery A/B/C no iniciado; los overrides mandan |
| [`H4_MP_MAPPING.md`](H4_MP_MAPPING.md), [`H4_TASK_MATRIX.md`](H4_TASK_MATRIX.md) | Hito 4 planificado (MP-023…035), no autorizado |
| [`deployment/`](deployment/) | MVP 0 (`MVP0_IMPLEMENTATION_PLAN.md`), teselas, VPS, opciones, checklist |

## Evidencia e histórico (no se reescribe)
[`audits/hito-03/`](audits/hito-03/) (auditoría H3: informes, registro de despachos, decisión ejecutiva) · [`evidence/`](evidence/) (evidencia por tarea) · [`hitos/`](hitos/) (kits de hito instalados) · [`research/`](research/) (investigación original) · [`INTEGRATION_H3_VERIFIED.md`](INTEGRATION_H3_VERIFIED.md) y [`PREPUBLICATION_H3.md`](PREPUBLICATION_H3.md) (integración) · [`MVP_READINESS.md`](MVP_READINESS.md) (cierre de H2) · [`HITO_3_BACKLOG.md`](HITO_3_BACKLOG.md).

## Cómo se mantiene
Edita `governance/PROJECT_STATE.json`, ejecuta `python scripts/governance/sync_docs.py` y `python scripts/governance/check_docs.py`. CI repite la comprobación. Las aprobaciones humanas solo se registran cuando existen.
