# MVP_RELEASE_CHECKLIST.md — Tareas, criterios y secuencia

Fecha: 2026-11-24. **Propuesta; no autoriza implementar ni contratar.** Política: `docs/ORCHESTRATION_POLICY.md` (coordinación `claude-sonnet-5-5` medium; backend/CI `gpt-6.2-sol` medium; Opus solo ante decisión arquitectónica compleja: **no se necesita ninguna**). Ejecutor y revisor de proveedores distintos; cada tarea con prueba que falle sin el cambio. IDs `D-xx` provisionales; no colisionan con `MP-023+` de H4.

## MVP 0 — URL pública con demo congelada

| ID | Tarea | Tipo | Ejecutor (modelo · esf.) | Revisor contrario | Aceptación |
|---|---|---|---|---|---|
| D-01 | Captura local de 30–60 min (colector + BD desechable puerto propio, nunca 5433) y GTFS | config | propietario/coordinador (`sonnet-5-5` · medium) | `gpt-6.2-sol` · medium | `manifest.json` con rango, SHA-256 y nº de ciclos; sin escritura en 5433 |
| D-02 | Exportador estático (`scripts/export_static_demo.py`) usando la API real en replay | dev | `gpt-6.2-sol` · medium | `sonnet-5-5` · high | salida reproducible (mismo hash en dos ejecuciones); snapshot exportado == respuesta de la API para 3 instantes; tamaño total informado |
| D-03 | Modo `VITE_DATA_MODE=static` en el cliente + reloj en bucle | dev frontend | `sonnet-5-5` · high | `gpt-6.2-sol` · high | vitest: mapeo `at`→fichero, límites de ventana, sin llamadas a `/api` en build estático; la salud nunca dice `live` |
| D-04 | Teselas configurables (`VITE_TILE_URL`) + atribución Renfe/OSM visible en pie | dev frontend | `sonnet-5-5` · medium | `gpt-6.2-sol` · medium | test del texto de atribución; captura 1440 y 390 px verificada por revisor Claude con DevTools |
| D-05 | Aviso permanente: captura del 2026-11-20, limitaciones y FR-01/FR-02 | dev frontend | `sonnet-5-5` · medium | `gpt-6.2-sol` · medium | texto citado a `FINDINGS_REGISTER`; visible en móvil |
| D-06 | `base` de Vite + workflow Actions → GitHub Pages (solo desde `main`, sin secretos) | CI | `gpt-6.2-sol` · medium | `sonnet-5-5` · high | despliegue de prueba en rama; URL abre mapa y Replay; `verify-build` pasa con `base` |
| D-07 | Comprobación final: sin secretos en `dist/`, sin llamadas a `localhost`, Lighthouse básico | verif | `sonnet-5-5` · medium | `gpt-6.2-sol` · medium | informe con comandos y resultados |

Puertas humanas: aprobar publicar con FR-01/FR-02 rotulados; elegir proveedor de teselas; activar Pages (acción en GitHub); titular/dominio. Estimación: **1–2 jornadas** de trabajo de agentes más la captura.

## MVP 1 — Live (no público hasta cumplir los criterios de abajo)

| ID | Tarea | Tipo | Ejecutor · esf. | Revisor | Aceptación |
|---|---|---|---|---|---|
| D-10 | = MP-023 (H4-11) defaults seguros de BD | corrección | `gpt-6.2-sol` · medium | `sonnet-5-5` · high | arranque sin variables → error y 0 filas; falla en `beb9434` |
| D-11 | Dockerfiles (API, colector) + `compose.prod.yml` + Caddy mismo origen | infra | `gpt-6.2-sol` · medium | `sonnet-5-5` · high | `docker compose up` desde cero sirve front+API; BD sin puerto publicado (comprobado con `docker ps`) |
| D-12 | Migraciones idempotentes en arranque | dev | `gpt-6.2-sol` · medium | `sonnet-5-5` · medium | 0001+0002 desde cero y repetidas sin error |
| D-13 | Descarga/validación del GTFS con aviso de vigencia (FR-19) | dev | `gpt-6.2-sol` · high | `sonnet-5-5` · high | GTFS vencido detectado en `/health`; falla en `beb9434` |
| D-14 | Purga/retención de BD caliente + archivo en volumen | dev | `gpt-6.2-sol` · medium | `sonnet-5-5` · high | crecimiento medido ≤ umbral en 24 h; requiere DEC-004 |
| D-15 | Rate limit + `/healthz` + cabeceras de seguridad | dev/config | `gpt-6.2-sol` · medium | `sonnet-5-5` · medium | ráfaga de N peticiones limitada; liveness sin BD |
| D-16 | `pg_dump` nocturno, copia externa y **restauración probada** | infra | `gpt-6.2-sol` · medium | `sonnet-5-5` · high | restauración en BD vacía con recuento de filas |
| D-17 | CD por SSH/`compose pull` desde `main` con aprobación manual | CI | `gpt-6.2-sol` · medium | `sonnet-5-5` · high | sin despliegue sin aprobación; secretos solo en Actions |
| D-18 | Operación supervisada ≥24 h (ideal 72 h) en el VPS | verif | `sonnet-5-5` · medium | `gpt-6.2-sol` · high | = H4-07 |
| D-19 | Cierre de FR-01 y FR-02 | corrección P0 | H4-00/H4-04/H4-01 según matriz | Opus 5.5 · high (P0, ya planificado) | pruebas que fallan en `beb9434`; gate H4-09 |

## Criterios que desbloquean un MVP Live público
1. FR-01 y FR-02 cerrados con prueba de regresión que falla en `beb9434` y revisión independiente; sin otro P0 abierto.
2. Defaults de BD seguros (D-10) y base sin exposición pública.
3. GTFS vigente verificado automáticamente (D-13) y cobertura de geometría declarada en la interfaz.
4. Operación supervisada ≥24 h sin huecos inexplicados, y restauración de copia probada.
5. Atribuciones Renfe/OSM visibles; teselas con proveedor aprobado y clave restringida por dominio.
6. Rate limit y retención activos; secretos fuera del repositorio y del build.
7. Veredicto **GO** del gate H4-09 y tu autorización explícita (publicación, coste y dominio).

## Secuencia de publicación recomendada
1. Merge del PR #3 (tu aprobación) → `main`.
2. D-01…D-07 → **URL pública del demo** (MVP 0).
3. Decidir VPS/Railway y presupuesto; D-10…D-17 en paralelo a H4-11/H4-00/H4-04/H4-01.
4. D-18 y gate H4-09 → decisión de abrir Live.
