# Registro de despachos y revisiones — Auditoría adversarial Hito 3

Mantenido en vivo por el coordinador (Claude Sonnet) a medida que cada `AUD-ID` reporta. AUD-09 puede partir de este registro en vez de reconstruirlo desde cero.

**Run:** `run_3b3bfaf88f3d` · **Worktree:** `/Users/matu/orca/workspaces/madrid-pulse/audit-hito-03` (rama `audit/hito-03-adversarial`, base `mp-022-validacion-integrada@beb9434`)

| AUD-ID | Rol | Agente / modelo / esfuerzo (solicitado = efectivo) | Dispatch | Task | Commit | Veredicto |
|---|---|---|---|---|---|---|
| AUD-00 | Ejecutor | Claude Sonnet — hecho directamente por el coordinador (inventario mecánico, bajo riesgo) | — | `task_5e5d12f76982` | `0fbabe3` | — |
| AUD-00 | Revisor | Codex `gpt-5.6-terra` · medium | `ctx_34a13efbb75a` | `task_71d356947672` | — | **APPROVED** |
| AUD-02 | Ejecutor | Codex `gpt-5.6-sol` · high | `ctx_99b3f28c3b64` | `task_b03ab623492c` | `81b246c` | entregado |
| AUD-02 | Revisor | Claude `sonnet` · high | `ctx_10b070f167d5` | `task_d0968d994508` | — | **APPROVED (5/5)**, con reproducción propia de los 5 hallazgos citados |
| AUD-03 | Ejecutor | Codex `gpt-5.6-sol` · high | `ctx_8e6da472a2f5` | `task_cc9d4fbec491` | *(en curso)* | *(en curso)* |
| AUD-05 | Ejecutor | Claude `sonnet` · high | `ctx_f88f1e4cca5e` | `task_f3b4f5788326` | *(en curso — hit límite de sesión 16:00 CET, reanudado)* | *(en curso)* |
| AUD-07 | Ejecutor | Claude `sonnet` · medium | `ctx_7f0fde0b7e4f` | `task_a9deb9865cbc` | `44c98cb`, `ea49e6a` | **completado** — revisión independiente real de Codex (`ctx_db3c9aa62ac8`, settled/succeeded) incorporada: 2 P1→P2, 2 P1 confirmados, 1 hallazgo descartado |
| AUD-01 | — | Claude `opus` · high (pendiente de despachar) | — | `task_8bf54c0799dd` | — | en cola |
| AUD-04 | — | Claude `opus` · high (pendiente de despachar) | — | `task_e6d1bf8a933e` | — | en cola |
| AUD-06 | — | Codex `gpt-5.6-terra` · high (pendiente de despachar) | — | `task_7982bf79c176` | — | en cola |
| AUD-08 | — | Codex `gpt-5.6-terra` · high (pendiente, depende de AUD-02/03/04/05/06) | — | `task_e0212d2fd3fe` | — | pendiente de dependencias |
| AUD-09 | — | Claude `opus` · high (pendiente, depende de todo) | — | `task_2e01f9d87b46` | — | pendiente de dependencias |

## Hallazgos reales reportados hasta ahora (resumen, no sustituye los documentos completos)

- **AUD-02** (reconstrucción GTFS, confirmado 5/5 por revisión independiente):
  - 12/42/103/95 coinciden con lo que afirmaba el cierre del Hito 3.
  - **121 trips huérfanos** (7 en `10T0035C5`, 114 en `10T0097C8b`).
  - Solo **40 de 103 `route_id`** tienen al menos un patrón asociado.
  - Solo **102 de 103 patrones** tienen ≥2 paradas; el patrón `10T0098C8b` tiene una sola parada (`12006`, Cercedilla).
  - **`calendar_dates.txt` ausente del ZIP real** — confirmado con `unzip -Z1` sobre el zip oficial (SHA-256 coincide), y `packages.gtfs.load_feed` sobre el feed real da `topology.calendar_dates == ()`. El manejo ADD/REMOVE que MP-017 dio por probado solo se verificó con fixtures sintéticas, nunca contra el ZIP real — **posible brecha real entre lo que el cierre de MP-017 afirmó y lo que el dato real permite verificar**.
  - **Bug real (sin impacto actual) en `ServiceDateResolver`**: `apps/api/service.py::service_dates_covering` resta un día fijo (`_service_date(start) - timedelta(days=1)`) sin escalar con `extended_horizon_s`; con un horizonte GTFS de 49:00+ (>48h) resolvería mal la fecha de servicio. El ZIP real de Madrid tiene un horizonte de solo 3180s, por lo que **hoy no se manifiesta**, pero el código no lo impide si el horizonte creciera.

*(Esta tabla se actualizará según reporten AUD-03, AUD-05, AUD-07 y el resto.)*
