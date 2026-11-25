# MILESTONES.md — Fases e hitos

Fuente estructurada: [`docs/governance/PROJECT_STATE.json`](../governance/PROJECT_STATE.json). Las tablas entre marcadores `GENERATED` se regeneran con `python scripts/governance/sync_docs.py`; **no se editan a mano**. Todo lo demás es texto humano y se conserva.

## Fases originales F0–F10 (roadmap de `docs/PLAN.md`)

<!-- BEGIN GENERATED: phases-table -->

| ID | Fase | Tareas | implementation_status | closure | Hallazgos abiertos | Evidencia del gate | Fuente |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F0 | Gobierno y documentación | MP-001 | IMPLEMENTED | CLOSED | — | MP-001 DONE; propietario autorizó Hito 1 el 2026-11-18 | [docs/PLAN.md](../PLAN.md) |
| F1 | Factibilidad real de datos | MP-002, MP-003 | IMPLEMENTED | CLOSED | — | MP-002/MP-003 DONE; [docs/legal/LICENSE_MATRIX.md](../legal/LICENSE_MATRIX.md); [docs/research/MP-003-probe-findings.md](../research/MP-003-probe-findings.md) | [docs/PLAN.md](../PLAN.md) |
| F2 | Contratos y calidad de datos | MP-004, MP-005 | IMPLEMENTED | CLOSED | — | MP-004/MP-005 DONE | [docs/PLAN.md](../PLAN.md) |
| F3 | Persistencia e ingesta mínima | MP-006, MP-007 | IMPLEMENTED_WITH_OPEN_GATE | OPEN | — | Dedupe y migraciones verificados; el gate de 24 h NO tiene evidencia (soak real = 668 filas). Cierre: MP-032/D-18. | [docs/PLAN.md](../PLAN.md) |
| F4 | Motor de calidad e histórico | MP-008, MP-009 | IMPLEMENTED_WITH_OPEN_GATE | OPEN | — | Anomalías cubiertas por test; replay de día completo sin evidencia (solo ventana de soak). Cierre: MP-028/MP-032. | [docs/PLAN.md](../PLAN.md) |
| F5 | Geometría y topología | MP-010, MP-011 | IMPLEMENTED | CLOSED | — | MP-010/MP-011 DONE; la cobertura de la red completa es otra cuestión (H3/MP-029). | [docs/PLAN.md](../PLAN.md) |
| F6 | Motor de movimiento | MP-012 | IMPLEMENTED | CLOSED | FR-01 | Gate histórico cumplido en MP-012; la auditoría H3 halló FR-01 (P0) en el motor entregado: se corrige en MP-024/MP-025a/b. | [docs/PLAN.md](../PLAN.md) |
| F7 | API propia | MP-013 | IMPLEMENTED | CLOSED | FR-02 | Gate histórico cumplido en MP-013; la auditoría H3 halló FR-02 (P0) en la API: se corrige en MP-026a. | [docs/PLAN.md](../PLAN.md) |
| F8 | Frontend Live | MP-014 | IMPLEMENTED | CLOSED | FR-01 | Gate histórico cumplido en MP-014; el rótulo de estados depende de la corrección de FR-01 (MP-030). | [docs/PLAN.md](../PLAN.md) |
| F9 | Histórico / Explore y endurecimiento | MP-015 | IMPLEMENTED | CLOSED | — | MP-015 DONE; PR #2 fusionado por el propietario el 2026-11-20 (990c95d) | [docs/PLAN.md](../PLAN.md) |
| F10 | Expansión | MP-016, MP-017, MP-018, MP-019, MP-020, MP-021, MP-022 | IMPLEMENTED_WITH_OPEN_GATE | OPEN | — | H3 amplió C5→núcleo Madrid solo en local; resto de España, AVE/LD/MD y capa colaborativa NO iniciados; gate no definido. | [docs/PLAN.md](../PLAN.md) |

<!-- END GENERATED: phases-table -->

## Hitos, auditoría y tracks

<!-- BEGIN GENERATED: milestones-table -->

| ID | Hito | implementation_status | review_status | integration_status | deployment_status | closure | Merge (PR · SHA · fecha) | Gate | Evidencia |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H0 | Hito 0 — Fundación y gobernanza (MP-001) | IMPLEMENTED | APPROVED | MERGED | NOT_APPLICABLE | CLOSED | 5b45227 · 2026-11-18 | MP-001 aprobado por Codex; Hito 1 autorizado por el propietario | [docs/TASKS.md#mp-001](../TASKS.md#mp-001) |
| H1 | Hito 1 — Datos, colector, calidad e histórico (MP-002→MP-009) | IMPLEMENTED_WITH_OPEN_GATE | APPROVED | MERGED | NOT_DEPLOYED | CLOSED | #1 · f567d3c · 2026-11-19 | Revisión cruzada aprobada 2026-11-19; PR #1 fusionado por el propietario | [docs/STATUS.md](../STATUS.md) |
| H2 | Hito 2 — Live Railway MVP local C5 (MP-010→MP-015) | IMPLEMENTED | APPROVED | MERGED | NOT_DEPLOYED | CLOSED | #2 · 990c95d · 2026-11-20 | MVP_READINESS aceptado; PR #2 fusionado por el propietario | [docs/MVP_READINESS.md](../MVP_READINESS.md) |
| H3 | Hito 3 — Cercanías Madrid completo, solo local (MP-016→MP-022) | IMPLEMENTED_WITH_OPEN_GATE | APPROVED | MERGED | NOT_DEPLOYED | OPEN | #3 · 7583ca5 · 2026-11-24 | Cierre técnico revisado; cierre de producto abierto: FR-01 y FR-02 (P0) sin corregir; NO-GO para despliegue público | [docs/audits/hito-03/AUDIT_EXECUTIVE_DECISION.md](../audits/hito-03/AUDIT_EXECUTIVE_DECISION.md) |
| AUD | Auditoría adversarial H3 (AUD-00→AUD-09) | IMPLEMENTED | APPROVED | MERGED | NOT_APPLICABLE | CLOSED | #3 · 7583ca5 · 2026-11-24 | AUD-09 aprobado por revisor de proveedor contrario; decisión final del propietario: ver human_gates | [docs/audits/hito-03/AUDIT_EXECUTIVE_DECISION.md](../audits/hito-03/AUDIT_EXECUTIVE_DECISION.md); [docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md](../audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md) |
| H4 | Hito 4 — Corrección de P0 y base operativa (MP-023→MP-035) | PLANNED | NOT_REVIEWED | NOT_INTEGRATED | NOT_DEPLOYED | OPEN | — | Autorización del propietario del alcance y la matriz; ADR-0014 enmendado aprobado antes de MP-025 | [docs/H4_MP_MAPPING.md](../H4_MP_MAPPING.md); [docs/H4_TASK_MATRIX.md](../H4_TASK_MATRIX.md) |
| MVP0 | MVP 0 — Primera URL de demostración estática (D-01→D-06) | PLANNED | NOT_REVIEWED | NOT_INTEGRATED | NOT_DEPLOYED | OPEN | — | Gate 0 + aprobación del propietario antes de publicar | [docs/deployment/MVP0_IMPLEMENTATION_PLAN.md](../deployment/MVP0_IMPLEMENTATION_PLAN.md); [docs/plans/MVP_LIVE_END_TO_END.md](../plans/MVP_LIVE_END_TO_END.md) |
| DESIGN | Design Discovery A/B/C (DES-00→DES-09) | PLANNED | NOT_REVIEWED | NOT_INTEGRATED | NOT_APPLICABLE | OPEN | — | Elección humana de concepto; no hay rediseño productivo antes | [docs/design/DESIGN_DISCOVERY_A_B_C.md](../design/DESIGN_DISCOVERY_A_B_C.md); [docs/design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md](../design/DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md) |
| LIVE_STAGING | Live técnico supervisado en staging (D-10→D-19) | PLANNED | NOT_REVIEWED | NOT_INTEGRATED | NOT_DEPLOYED | OPEN | — | Gate 1; hosting y coste son decisión del propietario | [docs/deployment/MVP_RELEASE_CHECKLIST.md](../deployment/MVP_RELEASE_CHECKLIST.md); [docs/plans/MVP_LIVE_END_TO_END.md](../plans/MVP_LIVE_END_TO_END.md) |
| BETA_PUBLIC | Beta pública funcional | PLANNED | NOT_REVIEWED | NOT_INTEGRATED | NOT_DEPLOYED | OPEN | — | Gate 2 + MP-035 GO + aprobación del propietario | [docs/plans/MVP_LIVE_END_TO_END.md](../plans/MVP_LIVE_END_TO_END.md) |
| EXPANSION | Ampliación de cobertura Cercanías y multimodal | NOT_STARTED | NOT_REVIEWED | NOT_INTEGRATED | NOT_DEPLOYED | OPEN | — | Posterior a beta; sin tareas ni autorización | [docs/roadmap/RELEASE_ROADMAP.md](RELEASE_ROADMAP.md) |

<!-- END GENERATED: milestones-table -->
