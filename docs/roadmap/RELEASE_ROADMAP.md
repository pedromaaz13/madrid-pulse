# RELEASE_ROADMAP.md — De la demo al servicio Live

**Fecha:** 2026-11-25 · **Estado:** propuesta de secuencia; **ninguna etapa está autorizada** salvo lo indicado. Estado real de cada etapa: [`MILESTONES.md`](MILESTONES.md) y `docs/governance/PROJECT_STATE.json`. Detalle técnico: [`docs/plans/MVP_LIVE_END_TO_END.md`](../plans/MVP_LIVE_END_TO_END.md) (PROPUESTA) y `docs/deployment/`.

## Punto de partida (verificado)
`main` = `7583ca5` contiene H1–H3 y la auditoría. **Solo existe en local**: no hay URL pública ni servicio desplegado. Veredicto: **NO-GO despliegue público; CONDITIONAL GO código local**. FR-01 y FR-02 (P0) abiertos.

## Secuencia
```text
 [hoy] H3 integrado ─► H4 P0 (MP-023/024/025a/026a/b) ──────────────┐
         │                                                           ▼
         ├─► MVP 0 (D-01..D-06): URL de demo ──(paralelo, sin pisar)─► Live staging ─► Beta Live ─► Ampliación Cercanías ─► Multimodal
         └─► Design A/B/C (DES-00..09) ──► elección humana ──► rediseño (fuera de este roadmap hasta elegir)
```
| Etapa | Qué entrega | Depende de | Gate de salida | Coste/decisión (propietario) |
|---|---|---|---|---|
| **R0 H4 P0 + base** | MP-023 (BD segura), MP-024 (ADR estado de parada), MP-026a (replay, GTFS), después MP-025a/b y MP-026b, MP-028 (captura) | H3 integrado | FR-01/FR-02 cerrados con prueba RED en `beb9434` y GREEN tras el fix; ADR-0014 aprobado por el propietario antes de MP-025 | solo tiempo de agentes |
| **R1 URL de demo (MVP 0)** | sitio estático con tramas **observadas** reales, sin movimiento ni ETA inventados, atribuciones y fecha de captura | D-01..D-06; no bloquea R0 ni lo exige | Gate 0 (plan §10) + aprobación expresa antes de publicar | GitHub Pages 0 €; teselas (OpenFreeMap candidato, condiciones por verificar) |
| **R2 Live staging** | VPS Docker/Caddy + collector + FastAPI + PostGIS + frontend, backups, retención, monitorización | R0 cerrado en lo P0; MP-023; D-10..D-18 | Gate 1: ciclos reales, FR-01/02/07/19 verificados, reinicio y restauración probados, mismo origen/HTTPS | VPS ≈ 8–11 €/mes (precios por verificar) vs Railway ≈ 14–16 USD |
| **R3 Beta Live pública** | URL pública con cobertura declarada, rate limit y atribución | R2 + ≥24 h (ideal 72 h) monitorizadas + MP-035 GO | Gate 2 + decisión humana de publicar (`HG-LIVE-PUBLIC`) | operación continua |
| **R4 Ampliación Cercanías** | más líneas con trazado validado (MP-029, PoC de grafo) | R3 | cobertura ponderada medida; sin proyectar sobre vías no verificadas | sin coste de infra adicional previsto |
| **R5 Multimodal / expansión** | otros operadores o modos | R4 | por definir | no planificado; fuera de alcance actual |

## Reglas de la secuencia
1. **Live público no se autoriza** mientras FR-01/FR-02, seguridad de BD, GTFS vigente, soak 24 h, restauración de backup, legal/rate limit/atribución, cobertura declarada y aprobación humana no estén todos cumplidos (hard gate MP-035).
2. La demo **no** es un frontend alternativo ni un requisito para arreglar Live; usa un contrato propio de observaciones y no pasa por el motor defectuoso.
3. Design A/B/C avanza en worktree aislado y **no** toca `MapView.tsx`, `App.tsx` ni `ui/*` mientras D-03/D-04/MP-030 los usen; la elección es gate humano.
4. CDN, snapshot publisher y R2 son escalado opcional **tras** medir; PMTiles propio no es decisión irreversible.
5. Cada etapa cierra con dictamen sobre un HEAD concreto y evidencia; un CI verde no equivale a cero P0.
