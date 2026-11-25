# DESIGN_DISCOVERY_EXECUTION_OVERRIDES.md — Adaptaciones vigentes del Design Discovery

**Fecha:** 2026-11-25 · **Estado:** vigente para cualquier ejecución futura de `DES-00…DES-09`; **no autoriza ejecutarla**.
**Documento original:** [`DESIGN_DISCOVERY_A_B_C.md`](DESIGN_DISCOVERY_A_B_C.md) (edición 2026-11-23). Se conserva **íntegro**: su matriz DES-00…DES-09 y sus permisos históricos no se alteran. Este fichero solo corrige lo que hoy ya no es verdad. En caso de contradicción, **manda este documento**.

## 1. Estado de las precondiciones
| Precondición del original (§1, §7.3) | Estado verificado (2026-11-25) |
|---|---|
| «Si AUD-00→AUD-09 sigue activa, no lanzar DES-00» | **Cumplida.** AUD-00…AUD-09 terminó y se integró en `main` (merge `7583ca5`, PR #3). No se reabre. Es la única precondición que se actualiza. |
| «No presupongas que el frontend H3 está en `main`» | El frontend H3 **está** en `main` (`7583ca5`). Baseline de producto: `beb9434`. |
| Ejecución de DES-xx | **No iniciada.** Sigue pendiente de la orden del propietario. |
| Elección A/B/C e integración productiva | **Gate humano abierto** (`HG-DESIGN-CHOICE` en `PROJECT_STATE.json`). No se integra rediseño productivo antes de la elección. |

## 2. Capacidades reales de los agentes (sustituye al §7.1 donde discrepe)
- **`gpt-6.1-terra` (Codex) puede implementar y revisar React/TypeScript, pero en Orca NO dispone de navegador** (`docs/ORCHESTRATION_COMPATIBILITY.md`: `No browser is available`, `agent.browsers.list() = []`, coincidente con cuatro observaciones previas).
- Por tanto **ninguna tarea puede atribuir a Terra Playwright, capturas, comportamiento móvil ni validación visual ejecutada.** Las filas DES-01 y DES-08 del original asignan a Terra el rol de «especialista browser/UX»: esa parte queda reasignada así:

| Tarea | Original | Vigente |
|---|---|---|
| DES-01 captura Playwright del frontend actual | Terra ejecuta, Claude revisa | **Claude `claude-sonnet-5-5` · high** ejecuta la inspección real **solo tras preflight** (comprobar que Chrome DevTools/Playwright existe y responde); Codex `gpt-6.2-sol` · medium revisa **código y artefactos** declarando que no tiene navegador |
| DES-08 verificación A/B/C en navegador real | Terra ejecuta | Igual que DES-01: ejecución visual por Claude con preflight; Codex audita artefactos/código |
| DES-07 iconografía | Terra ejecuta | Terra puede implementar la parte de código React/TS; las mediciones de FPS/legibilidad en navegador las hace Claude con preflight |
| Terra en el resto | — | Puede implementar o revisar código React/TS **sin** navegador |

- **Preflight obligatorio:** antes de declarar nada visual, el worker comprueba que la herramienta existe. Si no hay navegador: resultado **`NOT RUN`**, el **gate visual permanece abierto** y se informa; nunca `PASS` por inferencia ni mockups presentados como capturas.
- Efectos de la política (`docs/ORCHESTRATION_POLICY.md`): `claude-sonnet-5-5` medium coordina y high para frontend/revisiones importantes; Opus/Astra solo ante problema complejo demostrado; el modelo efectivo se registra (argv durante la ejecución), no el autoinforme.

## 3. Fuentes de diseño (discovery, sin instalación)
Anthropic `frontend-design`, Hallmark (`nutlope/hallmark`) e Impeccable (`pbakaus/impeccable`) se **consultan y comprueban** en DES-02 (versión, licencia, hooks, permisos). Prohibido: instalaciones globales, modo `live`/Apply inseguro, y copiar código con licencia incompatible con el MIT del repositorio. Resultado de DES-02 = decisión de uso, no integración.

## 4. Rechazado expresamente
El antiguo **Premium Design Kit** (negro/lima/dashboard genérico, `~/Downloads/Madrid-Pulse-Premium-Design-Kit`) fue **rechazado por el propietario**. No se reutiliza como dirección visual ni se presenta como alternativa aprobada. Puede citarse solo para explicar por qué falló.

## 5. Límites que se mantienen
- DES-xx son **subtareas internas de discovery**, no tareas MP ni autorización de Hito 4 (`docs/roadmap/CROSSWALK.md`).
- El trabajo visual corre en **worktree aislado** y no puede tocar los archivos de MVP 0 (D-03, D-04) ni de MP-030 (`apps/web/src/ui/*`, `App.tsx`, `MapView.tsx`).
- Los tres conceptos (**A Titanium Control, B Immersive Rail Map, C Contemporary Signal**), los mockups navegables, las capturas BASELINE/CONCEPT y la comparación terminan en el **gate humano de elección** (DES-09).
