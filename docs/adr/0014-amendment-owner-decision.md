# Registro de la decisión del propietario sobre la enmienda de ADR-0014 (MP-024)

**Fecha:** 2026-11-25 · **Decide:** el propietario del repositorio (`pedromaaz13`), por comunicación directa en la sesión de coordinación. Este registro **solo anota** lo decidido y lo que no; no es una aprobación generada por un agente ni por un workflow.
**Documento decidido:** [`0014-amendment-stop-state.md`](0014-amendment-stop-state.md) (enmienda 1 de ADR-0014; ADR en estado `Propuesto` hasta esta decisión) y su evidencia [`../evidence/mp-024/`](../evidence/mp-024/README.md).

## Decisión (dirección de diseño aprobada)
1. **Alternativa A** (estado de parada del operador) **con la alternativa C como degradación R8**.
2. **F1** para R-STALE: al caducar, congelar en el final autorizado de la envolvente inmutable por run, **distinguiendo** el final estimado y la última posición confirmada (`frozen_basis`, `last_confirmed_progress_m`).
3. **Perfil P-024 como valores provisionales:** τ = 50 m, espera mínima 30 s, edad máxima de cancelación 600 s, **pendientes de calibración en MP-028**.

## Limitaciones aceptadas expresamente por el propietario
- Retención de algunas salidas inmediatamente posteriores a `STOPPED_AT` (3/27 medidas en el corte).
- Aplicación **diferida** de las cancelaciones a la envolvente (desde la siguiente ancla; entretanto se señalizan sin mover la coordenada).
- **Requisito de un único colector** para la garantía de no retroceso de F1.
- **Ausencia de garantía de replay exacto por hora civil**: solo reconstrucción exacta dado el identificador del ancla/run.

## Lo que esta decisión NO hace
- **No** convierte el dictamen histórico de Codex `gpt-6.2-astra` (CHANGES_REQUESTED parcial sobre B2, y la verificación focalizada del delta final) en APPROVED; el dictamen se conserva tal cual. Las correcciones posteriores (`68d7df7`) siguen sin verificación independiente.
- **No** declara validados los supuestos `UNVERIFIED` (semántica en vivo de `IN_TRANSIT_TO`/`INCOMING_AT`, latencia de las salidas retenidas, visibilidad histórica de publicación por hora, precisión de la entrada por muestras en vivo): su validación queda en MP-028/MP-025b/MP-026b/MP-032.
- **No** cierra `HG-H4-SCOPE` ni otros gates humanos, **no** autoriza la BD 5433, captura continua, contratación ni publicación Live.

## Autorizaciones que acompañan a la decisión
- **MP-025a** (Codex `gpt-6.2-astra` · high → revisor Claude Opus High) y **MP-026b** (Codex `gpt-6.2-sol` · high → revisor Claude Opus High), con estos requisitos: pruebas de regresión rojas en `beb9434` y equivalencia Python↔TypeScript del ADR; F1 con final estimado y última posición confirmada distinguidos; **control efectivo de colector único** antes de operar con la garantía y **exclusión de cargas retroactivas del directo**; **cancelaciones conocidas señalizadas** aunque la envolvente no cambie; **no declarar resuelta la reproducción exacta por hora civil** sin evidencia de publicación/visibilidad y su prueba; **limitaciones por cambio de geometría o versión explícitas** (`anchor_version_changed`); rótulos de interfaz y vigencia desde el snapshot **pendientes de MP-030**. Los PR de desarrollo nuevos quedan para revisión, **sin merge automático**.
