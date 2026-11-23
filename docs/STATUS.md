# STATUS.md — Tablero vivo

> Punto de entrada del estado actual. El detalle por tarea vive en `docs/TASKS.md`; el historial de cambios, en `docs/CHANGELOG.md`.

## Hito autorizado actualmente

**Hito 1 — `MP-002` → `MP-009`: completado, aprobado por revisión cruzada el `2026-11-19`, y fusionado a `main` por el propietario (`pedromaaz13`) el `2026-11-19`.** PR #1 (`mp-009-historical-export` → `main`), commit de merge `f567d3c`. Confirmado: `git merge-base --is-ancestor 8be1272 f567d3c` → `0` (el último commit de la cadena MP-009 es ancestro de `main`; nada quedó sin integrar).

```text
Cobertura: F1 (factibilidad) + F2 (contratos) + F3 (persistencia/colector) + F4 (calidad/histórico)
Objetivo de salida: colector idempotente validado + quality engine + histórico exportado y replayable.
Cadena: MP-002 → MP-003 → MP-004 → MP-005 → MP-006 → MP-007 → MP-008 → MP-009.
Gates activos: decisiones reales de licencia o coste, conforme a ADR-0007.
```

MP-001 está `DONE`: Codex aprobó la revisión cruzada y, conforme a ADR-0007, no fue necesario que la rama estuviera fusionada en `main` para que una tarea dependiente avanzara. La rama paralela `chore/mp-001-foundation` (bitácora administrativa parcial, superada por el registro completo de la cadena `mp-00X`, ver nota de proceso más abajo) y los 9 worktrees `mp-002` a `mp-009` se conservan intactos tal como exige el propietario — ninguno se ha borrado.

**Hito 2 autorizado por el propietario el `2026-11-19`: `MP-010` → `MP-015` ("Live Railway MVP").**

```text
Cobertura: F5 (geometría y topología) + F6 (motor de movimiento) + F7 (API) + F8 (frontend) + F9 (E2E/readiness)
Objetivo de salida: primera app local funcional mostrando la C5 en vivo — topología GTFS real, geometría OSM,
  motor de movimiento con cuatro estados, API /api/v1 propia, frontend React/MapLibre, E2E + CI.
Tabla ejecutor/revisor (fijada por el propietario, coherente con docs/TASKS.md):
  MP-010 Topología GTFS      → Ejecutor Codex   · Revisor Claude
  MP-011 Geometrías OSM      → Ejecutor Claude   · Revisor Codex
  MP-012 Motor de movimiento → Ejecutor Codex   · Revisor Claude
  MP-013 FastAPI             → Ejecutor Claude   · Revisor Codex
  MP-014 React/MapLibre      → Ejecutor Codex   · Revisor Claude
  MP-015 E2E y MVP readiness → Ejecutor Claude   · Revisor Codex
Gates activos: decisiones reales de licencia o coste, conforme a ADR-0007. Además, por instrucción explícita
  del propietario para este hito: ningún push/PR/merge se ejecuta sin solicitar autorización en el momento
  (revierte, para Hito 2, la autorización puntual ya consumida en el cierre de Hito 1 — ver AGENTS.md).
No se avanza fuera de MP-010→MP-015 sin nueva autorización explícita (p. ej. no se implementa la red completa
  de Cercanías Madrid en este hito — eso es Hito 3, solo backlog de planificación, ver docs/PLAN.md F10 y la
  bitácora de este documento).
```

### Política de selección de modelo (Hito 2, fijada por el propietario)

- **Modelo principal: Claude Sonnet, esfuerzo de razonamiento alto** — por defecto para coordinación en Orca, implementación ordinaria, desarrollo de API/frontend, tests automatizados y revisiones cruzadas rutinarias.
- **Escalado: Claude Opus, esfuerzo de razonamiento alto** — solo con justificación técnica concreta (geometría/arquitectura geoespacial compleja, resolución ambigua de topología ferroviaria, algoritmos de map-matching/movimiento, errores persistentes que Sonnet no resuelve, decisiones arquitectónicas de alto impacto, revisión avanzada de UX/rendimiento/arquitectura frontend). Nunca se escala solo porque una tarea "parece importante" sin evaluar primero si Sonnet basta.
- **Verificación empírica realizada el `2026-11-19` (no se asumió ni inventó ningún identificador):** `orca orchestration worker-start --help` confirma que `--model`/`--effort` son parámetros reales y soportados para lanzar un agente Claude (`--model` acepta "opaque provider model ids"; `--effort` requiere `--model`). El identificador verificado empíricamente para "Sonnet" es `sonnet` y para "Opus" es `opus` (documentado como ejemplo real por Orca: `--model opus --effort high`); el esfuerzo de razonamiento se pasa como `--effort high`.
- **Discrepancia señalada al propietario:** el encargo nombra "Claude Sonnet 5.5" / "Claude Opus 5.5 High" como modelos. El contexto de entorno de esta sesión solo confirma la existencia de **Sonnet 5** y **Opus 5** (además de Haiku 4.5) como los modelos Claude más recientes disponibles — no se ha podido verificar ningún identificador "5.5". Siguiendo la instrucción explícita de no inventar identificadores, los workers de Hito 2 se lanzan con `--model sonnet --effort high` (por defecto) y `--model opus --effort high` (escalado), que son los identificadores reales confirmados, no una invención de "5.5".
- Codex: se usa el modelo/nivel de razonamiento disponible más adecuado, priorizando razonamiento alto para geometría, movimiento, contratos e integración, conforme a los roles ya fijados en `docs/TASKS.md`.

**Hito 3 autorizado por el propietario el `2026-11-22`: `MP-016` → `MP-022` ("Hito 3 — toda Cercanías Madrid, mapa map-first").**

```text
Cobertura: fiabilidad realtime (MP-016) + catálogo Madrid (MP-017) + geometría ferroviaria (MP-018) +
  arquitectura API/snapshots (MP-019) + frontend/movimiento UX (MP-020) + histórico/analítica (MP-021) +
  validación integral (MP-022).
Objetivo de salida: mapa funcional, dinámico e interactivo de toda la red de Cercanías Madrid (no solo C5),
  map-first, con separación raw/matched/rendered, movimiento fluido entre polls, servicios programados sin
  GPS diferenciados de los observados, búsqueda/filtros/seguimiento/tableros, e History/Explore con cobertura
  verificable.
Cadena: MP-016 → MP-017 → MP-018 → MP-019 → MP-020 → MP-021 → MP-022 (estrictamente secuencial).
Tabla ejecutor/revisor (fijada por el propietario vía el kit `docs/hitos/hito-03/PLAN-Y-ACEPTACION.md`):
  MP-016 Fiabilidad realtime    → Ejecutor Codex   · Revisor Claude
  MP-017 Catálogo Madrid        → Ejecutor Claude  · Revisor Codex
  MP-018 Geometría ferroviaria  → Ejecutor Codex   · Revisor Claude
  MP-019 API/snapshots          → Ejecutor Claude  · Revisor Codex
  MP-020 Frontend/movimiento UX → Ejecutor Claude  · Revisor Codex
  MP-021 Histórico/analítica    → Ejecutor Claude  · Revisor Codex
  MP-022 Validación integral    → Ejecutor Codex   · Revisor Claude
Fuente del kit: `~/Documents/DATA/Madrid-Pulse-Orca-Hito3-FINAL/` (versión `hito3-v4-definitivo`), instalado
  en `docs/hitos/hito-03/` de cada worktree de esta cadena vía `instalar.py` (--comprobar, luego real);
  `data/hito-03/` queda fuera de Git (`/data/` ya en `.gitignore`). Integridad verificada: 48 archivos,
  hashes OK; replay reproducido (42 rutas, 12 líneas/variantes, corte 1532: 119 matches/49 SKIPPED, corte
  1533: 121 matches/49 SKIPPED) antes de tocar código.
Criterios de aceptación vinculantes adicionales (no solo PLAN-Y-ACEPTACION.md): `MATRIZ-CIERRE-MADRID.md`,
  `AMPLIACION-ACEPTACION-MADRID-Y-HORARIOS.md`, `ANEXO-CRITICO-POSICION-Y-RELOJ.md` (los tres en
  `docs/hitos/hito-03/`). Protocolo de autonomía/permisos del coordinador: `AUTONOMIA-ORCA-Y-PERMISOS.md`
  (mismo directorio) — el coordinador puede aprobar solicitudes rutinarias de workers dentro del worktree
  autorizado, con motivo registrado; nunca push/PR/merge, operaciones destructivas, cloud de pago, cambios
  de permisos del sistema, ni licencias nuevas sin autorización puntual del propietario.
Gates activos: decisiones reales de licencia/coste conforme a ADR-0007; cualquier decisión arquitectónica
  nueva (p. ej. el contrato temporal de MP-019, elegido por ADR comparativo según
  `MEJORAS-PRODUCTO-VALIDADAS.md`) sigue el proceso de ADR, nunca autopromovida a `Aceptado`.
No se avanza fuera de MP-016→MP-022 sin nueva autorización explícita (AVE/LD/MD, despliegue público 24/7,
  dbt obligatorio y expansión multimodal quedan para Hito 4+, ver `docs/hitos/hito-03/SIGUIENTES-HITOS.md`).
```

## Auditoría independiente de preparación para integración

**OpenAI Codex — `2026-11-19`: APROBADA, sin bloqueantes reales para integrar `mp-009-historical-export` en `main`.** El estado auditado (`c8d3bd0`, antes de registrar esta entrada) contiene de forma lineal y sin merges todo MP-001 → MP-009: `git merge-base --is-ancestor 3e7b533 c8d3bd0` devuelve `0`, y el recorrido desde `origin/main` (`5b45227`) hasta `c8d3bd0` contiene los 23 commits esperados. Los 23 tienen autor y committer `Pedro Matute <pedromaaz13@gmail.com>` y ninguno incluye un trailer literal `Co-authored-by:`.

Evidencia reproducida de forma independiente:

- La rama paralela `chore/mp-001-foundation` se separa en `3e7b533` y añade cinco commits (`fac945c` → `15820ac`) que solo modifican `docs/STATUS.md`, `docs/TASKS.md` y `docs/CHANGELOG.md`. Su contenido es seguimiento administrativo hasta MP-005 en `REVIEW`; la autorización del Hito 1, sus condiciones operativas, los hallazgos y cierres de MP-002 → MP-005 ya están reflejados —con estado final y mayor detalle— en esta rama. No se encontró contenido único material cuya ausencia causase pérdida al integrar únicamente `mp-009-historical-export`.
- Worktrees muestreados limpios antes de registrar esta auditoría: clon original, `mp-004-fixtures`, `mp-007-collector` y `chore/mp-001-foundation`; este worktree también estaba limpio.
- Diff `origin/main..HEAD`: 95 ficheros (92 añadidos, `README.md` modificado y dos renombres `R100` hacia `docs/research/`), sin cachés, entornos virtuales ni temporales versionados. `git diff --check` solo informa de una línea en blanco final en cada una de las tres fixtures JSON; son avisos cosméticos y las pruebas que las parsean pasan.
- Suites ejecutadas realmente: contratos 31/31, fixtures 6/6, collector 9/9, quality 13/13 y snapshotter 5/5 — **64/64 en verde**. PostgreSQL conservó exactamente los recuentos `668/484/3/120/0` en `vehicle_position_observation` / `trip_update_observation` / `service_alert` / `source_ingestion_run` / `data_quality_event` antes y después; no quedó residuo de pruebas.
- Escaneo de secretos: no se encontraron claves, tokens, ficheros de entorno ni llaves privadas. La única contraseña es `madrid_pulse_local`, credencial de desarrollo local usada exclusivamente contra `127.0.0.1:5433`.
- Enlaces: 48 enlaces relativos Markdown comprobados en el repositorio, 0 rotos. `docs/TASKS.md` marca MP-001 → MP-009 como `DONE`; este documento declara el Hito 1 completado y prohíbe iniciar MP-010 sin autorización nueva; `docs/CHANGELOG.md` conserva el historial de las nueve tareas.

**Veredicto de integración:** `mp-009-historical-export` está preparada para que el propietario la integre en `main`; no se identificaron omisiones, pérdida documental, problemas de autoría ni bloqueantes técnicos. Los tres avisos de whitespace en fixtures son los únicos hallazgos abiertos y no son bloqueantes.

## Auditoría independiente de preparación para integración (Hito 2)

**OpenAI Codex — `2026-11-20`: APROBADA, sin bloqueantes reales para integrar
`mp-015-e2e-readiness` en `main`.** El estado auditado es `a6ade4e` (antes
de registrar esta sección) y el rango es `origin/main..HEAD`, desde
`f567d3c`: 33 commits lineales que contienen MP-010 → MP-015 completos.

### Parte 1 — Evidencia de integración reproducida

- **Ancestría y linealidad.** Se comprobaron todas las referencias, no solo
  la base y el tip:

  ```text
  $ for ref in origin/main mp-010-gtfs-topology mp-011-osm-geometry mp-012-movement-engine mp-013-fastapi mp-014-frontend; do git merge-base --is-ancestor "$ref" HEAD; ...; done
  origin/main -> exit 0 (f567d3c)
  mp-010-gtfs-topology -> exit 0 (0a31640)
  mp-011-osm-geometry -> exit 0 (da5f5e1)
  mp-012-movement-engine -> exit 0 (1c1529d)
  mp-013-fastapi -> exit 0 (2e883aa)
  mp-014-frontend -> exit 0 (a1067b2)
  $ git rev-list --count origin/main..HEAD
  33
  $ git rev-list --merges origin/main..HEAD --oneline
  [sin salida]
  ```

  Por tanto, el tip contiene todos los tips intermedios y puede integrarse por
  fast-forward desde el `origin/main` auditado; no hay merge commits ocultos.

- **Autoría.** El recorrido individual mostró los 33 commits con autor y
  committer de Pedro. La reducción de identidades y la búsqueda de trailers
  dieron:

  ```text
  $ git log origin/main..HEAD --format='%an <%ae>|%cn <%ce>' | sort | uniq -c
       33 Pedro Matute <pedromaaz13@gmail.com>|Pedro Matute <pedromaaz13@gmail.com>
  $ git log origin/main..HEAD --format='%H%n%B%n---' | rg -in '^Co-authored-by:'
  [sin salida]
  ```

- **Diff real.** `git diff --stat origin/main..HEAD` enumera 109 ficheros,
  `31280 insertions(+), 99 deletions(-)`; la clasificación independiente por
  `--name-status` da `A=74 M=35 R=0 total=109`. Incluye la CI, API, frontend,
  topología/geometría/movimiento, gold/replay, fixtures GTFS/OSM y su
  documentación. No hay cachés, entornos, builds ni temporales rastreados:

  ```text
  $ git ls-files | rg '(^|/)(node_modules|dist|build|\.venv|venv|__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache)(/|$)|(^|/)(\.DS_Store|.*\.pyc|.*\.pyo)$'
  [sin salida]
  $ git diff --check origin/main..HEAD
  [sin salida]
  ```

  A diferencia de la auditoría de Hito 1, este rango no deja ni siquiera
  avisos cosméticos de whitespace. El build sí emitió el aviso informativo de
  Vite por chunks mayores de 500 kB; no es un fallo del build ni un artefacto
  versionado.

- **Suite Python contra la base real de desarrollo.** Antes y después se
  consultaron las cinco tablas en el orden
  `vehicle_position_observation/trip_update_observation/service_alert/source_ingestion_run/data_quality_event`:

  ```text
  $ docker exec madrid-pulse-postgres-1 psql ... -c 'SELECT (SELECT count(*) ...);'
  668|484|3|120|0
  $ MADRID_PULSE_DATABASE_URL=...:5433/... MADRID_PULSE_DATABASE_DSN=...:5433/... .venv/bin/python -m unittest <las 18 suites de CI> -v
  Ran 115 tests in 12.835s
  OK
  real soak read-only: rows=668, near_corridor=177, max_map_matched_jump_kmh=666.4, after=668
  $ docker exec madrid-pulse-postgres-1 psql ... -c 'SELECT (SELECT count(*) ...);'
  668|484|3|120|0
  ```

  Resultado real: **115 passed, 0 failed, 0 skip**; la base conservó
  exactamente `668/484/3/120/0`.

- **Suite Python desde cero.** Se creó el contenedor desechable aislado
  `madrid-pulse-audit-hito2-task0687344` sobre `postgis/postgis:17-3.5`, en
  `127.0.0.1:55433` (distinto de desarrollo), se esperó `pg_isready`, y se
  aplicó `infra/migrations/0001_init.up.sql` con `ON_ERROR_STOP=1`. La salida
  confirmó `CREATE EXTENSION`, 14 `CREATE TABLE`, 5 `CREATE INDEX` y `COMMIT`.
  Después:

  ```text
  $ MADRID_PULSE_DATABASE_URL=...:55433/... MADRID_PULSE_DATABASE_DSN=...:55433/... .venv/bin/python -m unittest <las 18 suites de CI> -v
  Ran 115 tests in 4.746s
  OK (skipped=5)
  $ docker exec madrid-pulse-audit-hito2-task0687344 psql ... -c 'SELECT (SELECT count(*) ...);'
  0|0|0|0|0
  $ docker stop madrid-pulse-audit-hito2-task0687344
  madrid-pulse-audit-hito2-task0687344
  ```

  Resultado real: **110 passed, 0 failed, 5 skip** explícitos, todos ligados
  al soak local irrepetible de MP-007; replay, persistencia y contratos
  reproducibles sí se ejecutaron. Las pruebas limpiaron sus filas y el
  contenedor se autoeliminó.

- **Frontend con la versión de CI (`Node 22.13.1`).** Se ejecutaron por
  separado los cuatro gates:

  ```text
  $ fnm exec --using=22.13.1 npm run lint
  eslint . --max-warnings 0                         [exit 0]
  $ fnm exec --using=22.13.1 npm run typecheck
  tsc -b --pretty false                             [exit 0]
  $ fnm exec --using=22.13.1 npm test
  Test Files  2 passed (2); Tests  5 passed (5)
  $ fnm exec --using=22.13.1 npm run build
  ✓ built in 231ms
  Verified production MapLibre worker (550754 bytes)
  ```

- **Secretos y artefactos sensibles.** La búsqueda sobre ficheros rastreados
  de cabeceras de llave privada y formatos comunes (`AKIA`, tokens GitHub,
  `sk-`, `AIza`) no devolvió coincidencias; tampoco hay `.env`, `.pem`,
  `.key`, `.p12`, `.pfx`, `id_rsa` o `id_ed25519` versionados. La búsqueda de
  credenciales embebidas devuelve únicamente:

  ```text
  .github/workflows/ci.yml:29: ...madrid_pulse:madrid_pulse_local@127.0.0.1:5433...
  .github/workflows/ci.yml:30: ...madrid_pulse:madrid_pulse_local@127.0.0.1:5433...
  apps/api/config.py:26: ...madrid_pulse:madrid_pulse_local@127.0.0.1:5433...
  services/collector/config.py:34: ...madrid_pulse:madrid_pulse_local@127.0.0.1:5433...
  services/snapshotter/config.py:16: ...madrid_pulse:madrid_pulse_local@127.0.0.1:5433...
  ```

  Es la única contraseña encontrada y está limitada a la credencial local
  esperada; no hay claves, tokens ni ficheros de entorno reales.

- **Enlaces Markdown.** Un comprobador resolvió los enlaces relativos de los
  `docs/*.md` y `docs/adr/*.md` añadidos o tocados en el rango:

  ```text
  files=21 relative_links=50 broken=0
  ```

  Las referencias a `adr/0013-no-literal-dbt-engine.md` resuelven desde
  `ARCHITECTURE`, `CHANGELOG`, `DECISIONS`, `PLAN`, `STATUS` y el índice de
  ADRs; no hay enlaces rotos.

- **Cierre documental.** `docs/TASKS.md` marca individualmente MP-010,
  MP-011, MP-012, MP-013, MP-014 y MP-015 como `DONE`; la sección "Tarea
  actual" de este documento marca MP-015 `DONE` y las cinco secciones de
  tareas cerradas hacen lo mismo con sus predecesoras. `docs/CHANGELOG.md`
  conserva las seis tareas y, en particular, no oculta los hallazgos: registra
  las dos rondas de MP-015, las cuatro rondas visuales de MP-014 y las
  correcciones de MP-011/MP-013. Los recuentos históricos `114/114` y
  `109+5` permanecen donde describen ejecuciones anteriores, seguidos por la
  corrección verificable a `115/115` y `110+5`; esta auditoría vuelve a
  confirmar estos últimos recuentos.

**Veredicto de integración:** `mp-015-e2e-readiness` está lista para que el
propietario la integre en `main` por fast-forward desde `f567d3c`. No se
identificaron pérdidas documentales, problemas de autoría, residuos de
pruebas, secretos, enlaces rotos ni bloqueantes técnicos. El warning de
tamaño de chunks de Vite es una oportunidad de optimización futura, no un
fallo de readiness.

### Parte 2 — Revisión de ADRs pendientes de promoción

La recomendación se contrastó con el código y el esquema reales, no solo con
la auto-descripción de cada ADR:

| ADR | Evidencia de implementación al cierre de Hito 2 | Veredicto |
|---|---|---|
| ADR-0002 — fuentes | Renfe tiene licencia, disponibilidad, esquema e integración reales verificados. CRTM solo tiene licencia `VERIFIED`; `docs/legal/DATA_SOURCES.md` conserva disponibilidad técnica `PENDING MP-003` y ningún componente lo integra. DEC-006 todavía nombra ambas como fuentes primarias. | **Apto, pero requiere actualizar antes de dar por cerrada la verificación.** No se debe borrar simplemente "pendiente": cambiar `Estado` por **`Aceptado (fuentes): Renfe verificada e integrada; CRTM con licencia verificada, disponibilidad técnica e integración pendientes`**. Para evitar drift, DEC-006 debe distinguir Renfe como fuente primaria implementada y CRTM como fuente complementaria evaluada/licenciada pero aún no integrada. |
| ADR-0005 — contrato API | `apps/api/main.py` publica siete rutas reales bajo `/api/v1`; `schemas.py` expone `position.mode/confidence`, `observation.age_s`, `delay.coverage` y `quality.flags`; `openapi.json` coincide. Las tablas gold ya se calculan, pero los cuatro endpoints history/metrics siguen diferidos y el propio ADR lo dice. | **Apto para promoción a `Aceptado` sin cambios.** Los endpoints pendientes son alcance funcional futuro y no contradicen la decisión arquitectónica de contrato propio versionado. |
| ADR-0008 — identidad de ruta | `Topology` conserva los cinco `route_id` completos como rutas distintas, `route_groups()` agrupa por `(network_id, short_name)`, la resolución de trip es literal, el colector filtra núcleo `10` y el esquema exige `UNIQUE(network_id, source_route_id)`. La tabla `route` local sigue sin poblarse, pero no se colapsa identidad en ninguna capa implementada. | **Apto para promoción a `Aceptado` sin cambios.** La ausencia de un loader persistente de `route` no invalida la identidad adoptada y ya aplicada en topología/API. |
| ADR-0009 — campos no observados | Contratos y migración mantienen `speed_kmh`/`bearing` nullable, usan `current_stop_id`, omiten `effect/cause/header_text` y conservan `description_language`; `packages.gtfs` resuelve `stop_id`/secuencia sin alterar el raw. Los tests de parseo y normalización pasan. | **Apto para promoción a `Aceptado` sin cambios.** |
| ADR-0010 — deduplicación | El hash cubre el `model_dump` bruto completo; el colector compara por clave de entidad y no implementa `seen_count`. Sin embargo, el SQL real desempata timestamps repetidos con `id DESC`, corrección bloqueante de MP-007 que el ADR no recoge. | **Apto, pero requiere actualizar antes de promover.** Sustituir la frase **``ORDER BY observed_at DESC LIMIT 1``** por **``ORDER BY observed_at DESC, id DESC LIMIT 1`` (y `active_period_start DESC, id DESC` para alertas)**, explicando que `id DESC` hace determinista el último poll cuando el timestamp de fuente empata. |
| ADR-0011 — piloto frente a producto | La lógica de GTFS, geo y movimiento no contiene el literal de la línea piloto; API y frontend derivan líneas/IDs de topología. Los defaults `C5` de `ApiConfig`/`SnapshotterConfig` son configuración sustituible, no filtros hardcodeados. | **Apto para promoción a `Aceptado` sin cambios.** |
| ADR-0012 — frontera de movement | `packages/movement` es puro y sin persistencia en producción; depende de contracts/geo/gtfs, recibe topología/corredor/umbrales, devuelve `MovementPosition` tipado con modo, confianza, edad, fuente y anomalías. FastAPI lo consume sin incorporar el algoritmo a HTTP. | **Apto para promoción a `Aceptado` sin cambios.** |
| ADR-0013 — sin motor dbt literal | `requirements.txt` incluye DuckDB pero no `dbt-core`/`dbt-duckdb`; `gold.py` implementa y prueba las capas por núcleo/línea/estación y `analytics/dbt/` solo documenta la disciplina y la decisión reversible. ADR-0003 permanece intacto. | **Apto para promoción a `Aceptado` sin cambios.** |

**Balance de promoción recomendado:** seis ADRs (`0005`, `0008`, `0009`,
`0011`, `0012`, `0013`) pueden promoverse sin cambios; ADR-0010 necesita una
corrección textual precisa antes de promoverse; ADR-0002 ya está aceptado a
nivel de fuentes, pero su coletilla no está completamente resuelta y debe
reformularse —no eliminarse— para distinguir el estado real de Renfe y CRTM.
No se cambió el campo `Estado` de ningún ADR durante esta auditoría.

## Resolución de DEC-015 (mecánica de convergencia de ramas, antes de MP-012)

**Resuelto el `2026-11-19`, documentado aquí y en `docs/DECISIONS.md`/`AGENTS.md`.** La pregunta abierta era qué rama usar como base y cómo integrar las demás cuando una tarea depende de varias ramas potencialmente distintas (caso previsto: MP-012 depende de MP-008, MP-010 y MP-011).

Con Hito 1 ya fusionado a `main`, el caso concreto de MP-012 **deja de requerir una fusión real de ramas divergentes**: MP-008 ya es ancestro de `main` (se fusionó como parte de la cadena MP-002→MP-009). Si MP-010 y MP-011 se ramifican a partir de `main` (o de una rama que a su vez parte de `main`, como esta misma `chore/hito-2-coordination`), entonces la cadena resultante — `main → MP-010 → MP-011` — ya contiene a MP-008 de forma transitiva. MP-012 puede ramificar simplemente desde la rama de MP-011 sin ningún `git merge` real: sus tres dependencias (MP-008, MP-010, MP-011) son todas ancestros de ese punto.

**Mecanismo general (para este y futuros casos de convergencia múltiple), registrado en `AGENTS.md`:** antes de abrir el worktree de una tarea con varias dependencias directas, comprobar con `git merge-base --is-ancestor <dependencia> <candidata-a-base>` si cada dependencia ya es ancestro de la rama candidata a base (normalmente la más "profunda" en la cadena). Si todas lo son, se ramifica directamente desde esa rama — no hace falta fusión. Solo si una dependencia **no** es ancestro de la otra (p. ej. dos ramas que de verdad divergieron sin que ninguna absorbiera a la otra vía `main`) se necesita una fusión real (`git merge` de la rama no-ancestro sobre la rama base elegida, documentando el resultado y cualquier conflicto en `docs/STATUS.md` antes de continuar). Este hito no necesita ese caso general porque la estructura tras el merge de Hito 1 ya lo evita.

## Tarea actual

**MP-021 — Histórico y continuidad analítica**

Ejecutor: Claude (escalado a Opus) · Revisor: OpenAI Codex · Estado: **REVIEW**

Worktree/rama: `mp-021-historico`, ramificada desde `mp-020-mapa-y-tablero` (MP-020 `DONE`, `b616ae6`). Datos del kit repuestos con `instalar.py --solo-datos` (10 ficheros).

### Alcance de MP-021

Histórico consultable por circulación ligado a la identidad/fecha de Live (MP-019/020), mart reproducible con numeradores/denominadores de cobertura (extendiendo `services/snapshotter/gold.py` de un núcleo a todo el catálogo Madrid vía MP-017/018/019), exportación idempotente (reprocesar el mismo día de servicio dos veces produce el mismo resultado exacto), History/Explore mínimo navegable conectado a los botones ya deshabilitados en `apps/web/src/ui/TopBar.tsx` (`disabled title="Histórico y Explore se entregan en MP-021"`), y propuesta ejecutable de colector continuo supervisado con coste medido — sin declarar «24/7 confirmado» ni contratar ningún servicio de pago sin aprobación explícita del propietario.

### Prohibido explícitamente en MP-021 (kit, `MEJORAS-PRODUCTO-VALIDADAS.md`)

SQL Lab, dbt obligatorio, cuentas de usuario, infraestructura distribuida. El histórico y Explore mínimo del kit se mantienen tal cual están definidos — no se amplía el alcance.

### Entorno heredado de MP-020 (disponible, no asumir que sigue vivo sin comprobarlo)

Backend replay en `127.0.0.1:8010` (GTFS completo del núcleo), Vite dev en `127.0.0.1:5181`, contenedor desechable `mp020-replay-db` en `127.0.0.1:5434` con los cortes `1532`/`1533` ingeridos; base de desarrollo `5433` intacta. El worker de MP-020 lo mantiene en pie a la espera de que MP-021 lo reutilice o indique que puede pararlo.

### Nota heredada de MP-019 (DEC-038, pendiente del propietario)

Con conexión PostgreSQL por petición, ~66 ms de los ~69 ms de p50 de `/api/v1/health` son solo abrir la conexión. Sigue pendiente del propietario, no se toma en MP-021.

### Nota heredada de MP-020 (limitación conocida, no divergencia)

`route_color` real de Renfe no se expone en `/api/v1/catalog`; el frontend usa una paleta propia determinista por `line_id`. Sigue abierto: MP-021 **no** lo ha cambiado, porque tocar `/api/v1/catalog` habría modificado el contrato de MP-019, que el encargo prohíbe. Queda para MP-022 o para el propietario. (El dato existe: `packages.gtfs.Route.color` lo parsea desde `routes.txt`.)

### Entregado en MP-021 (pendiente de auditoría de Codex)

1. **Idempotencia real del archivo frío** — preparación en `.staging/` y sustitución atómica por día de servicio; un origen vacío nunca borra un día archivado. Los cuatro agregados son byte-estables. DEC-040, [ADR-0015](adr/0015-cold-archive-and-history-contract.md).
2. **Histórico consultable por circulación** — mart `circulation_daily_history` (vehículo + viaje + día de servicio) con los huecos como filas y métricas `NULL`, nunca `0`; expuesto en `/api/v1/history/*` sin tocar el contrato de MP-019.
3. **Mart sobre el catálogo Madrid completo** — 42 rutas / 12 líneas vía `SnapshotterConfig.line_filter`; límite (a) de DEC-033 cerrado con `packages.gtfs.scheduled_service_ids_for_date`.
4. **History y Explore navegables** — botones de `TopBar.tsx` conectados, ida y vuelta Live ↔ History con la misma identidad, inspección visual real con 8 capturas.
5. **Operación continua supervisada con coste medido** — `infra/operate/` y `docs/evidence/mp-021-coste-colector-continuo.md`.

### Lo que MP-021 deja explícitamente sin hacer

- **No hay «24/7 verificado»**: la ventana medida son 13 min 43 s; las cifras de 24/72 h son proyecciones marcadas como tales. No se ha contratado ningún servicio de pago ni desplegado ningún host persistente (ADR-0007), ni instalado el agente `launchd` en el equipo del propietario.
- **DEC-004** (retención del histórico) ya tiene por fin la medición que esperaba (≈19 MB/día, ≈7 GB/año en Parquet ZSTD), pero la decisión sigue siendo del propietario.
- **DEC-033 (b) y (c)** siguen abiertos: el umbral de puntualidad de 300 s no tiene histórico con el que calibrarse, y `data_quality_event.entity_ref` sigue sin referenciar nunca una parada.
- **DEC-038** (pool de conexiones) sigue pendiente del propietario; MP-021 no la toma.

### Entorno levantado por MP-021 (se puede parar cuando el revisor termine)

API `127.0.0.1:8011` y Vite `127.0.0.1:5182` sirviendo **este** worktree, sobre la base de replay `mp020-replay-db` (`5434`, solo lectura) y un archivo frío en el scratchpad de la sesión. Contenedor desechable propio `mp021-collector-db` (`5435`) creado para la medición de coste; no se ha borrado ningún contenedor, worktree ni fixture de otra tarea. El entorno de MP-020 (`8010`/`5181`) se dejó intacto.

## Tareas cerradas de la cadena

## MP-020 — Mapa y tablero (React/MapLibre) (cerrada)

**MP-020 — Mapa y tablero (React/MapLibre)**

Ejecutor: Claude (escalado a Opus) · Revisor: OpenAI Codex · Estado: **DONE** (aprobado el 2026-11-22)

Worktree/rama: `mp-020-mapa-y-tablero`, ramificada desde `mp-019-snapshot-api` (MP-019 `DONE`, `7b87e6b`). Datos del kit repuestos con `instalar.py --solo-datos`.

### Alcance de MP-020

Reconstruir `apps/web/` (hoy limitado a C5 y a los endpoints antiguos `/lines`/`/live/vehicles`/`/health` con un único `Promise.all`, MP-014) como la experiencia map-first de `diseno/live.html`/mockups, consumiendo el nuevo contrato de MP-019 (`/api/v1/catalog` cacheable, `/api/v1/snapshot` ligero, `/api/v1/stations/{id}/board`): mapa persistente de toda Cercanías Madrid, búsqueda, multiselección de líneas, tablero de estación, seguimiento, movimiento fluido por longitud de arco sobre `ProgressEnvelope` (fórmula ya fijada por MP-019: `t0 = dwell_until or reference_at; progress(t) = min(progress_m_at_reference + speed_mps*max(0, t-t0), max_progress_m)`, válida hasta `rendered.valid_until`), nunca interpolando lat/lon en recta.

### Nota heredada de MP-019 (DEC-038, pendiente del propietario)

Con conexión PostgreSQL por petición, ~66 ms de los ~69 ms de p50 de `/api/v1/health` son solo abrir la conexión. Si el frontend sondea cada 20s, esta latencia es relevante para medir fluidez real — la decisión de introducir un pool (nueva dependencia) sigue pendiente del propietario, no se toma en MP-020.

### Qué se construyó

`apps/web/` reconstruido en cuatro incrementos (selección+ficha → movimiento+seguimiento → estación/línea/búsqueda → enlaces/móvil), con `App.tsx` reducido a composición y la lógica repartida en `src/api/`, `src/domain/`, `src/hooks/`, `src/map/` y `src/ui/`:

- **Adquisición:** un hook por recurso (catálogo, snapshot, salud, tablero), con una lectura en vuelo por recurso, timeout y cancelación propios, descarte de respuestas antiguas por `revision`, catálogo revalidado con `ETag`/`304` y pausa/revalidación por visibilidad de la pestaña. Un fallo parcial conserva el último valor bueno; una respuesta con éxito no rejuvenece el dato.
- **Mapa:** una sola instancia MapLibre con fuentes GeoJSON reconciliadas por identidad de circulación (vehículo+viaje+día de servicio, no `vehicle_id`), reloj de presentación en `requestAnimationFrame` fuera de `setState`, y anillo de la última lectura confirmada cuando el símbolo es proyectado o congelado.
- **Movimiento:** evaluación de la `ProgressEnvelope` del contrato y proyección del progreso dirigido sobre la polilínea del patrón; nunca interpolación lat/lon en recta, y congelación al agotarse `valid_until`.
- **Navegación:** búsqueda de estación y línea con y sin tilde, multiselección de líneas con contadores del mismo ámbito que el mapa, tablero de estación, seguimiento explícito separado de la selección, y estado restaurable en la URL con `pushState`.

### Resultado y evidencia

Entregado en `REVIEW`. Evidencia ejecutada en `docs/evidence/mp-020-inspeccion-navegador.md` y capturas en `docs/evidence/mp-020-capturas/`. Lo verificado de verdad en navegador (no solo con tests) está resumido en la ficha de MP-020 de `docs/TASKS.md`; lo esencial: **60 s continuos** de la app real con 13 muestras de fotogramas intermedios avanzando a los **22,0 m/s** que declara la envolvente (1 316,7 m, sin teletransporte), la coordenada del cliente cayendo sobre la del backend con **error < 1 m**, y cámara/selección/seguimiento sobreviviendo a dos sondeos y a una caída y recuperación del backend mientras la edad del dato sigue avanzando.

Suites reales con Node `22.13.1`: **49/49** en `apps/web` (lint y typecheck limpios, build con worker de MapLibre verificado byte a byte) y **233/233** en el backend, que no se tocó, con los recuentos de PostgreSQL intactos (`668/484/3/120/0`).

**Siete defectos reales que ningún test automatizado detectó** se encontraron y corrigieron mirando el navegador. El primero repite el género de fallo de MP-014: el chunk diferido de `maplibre-gl.css` carga después de la hoja propia y su `.maplibregl-map { position: relative }` ganaba al `position: absolute` del contenedor, que quedaba con **altura 0** y sin mapa visible. El más interesante de contrato: **`snapshot_id` no sirve como señal de «hay dato nuevo»**, porque es identidad de contenido y se repite entre sondeos cuando los vehículos no cambian aunque `display_at` avance — usarlo congelaba el mapa con movimiento reducido; la señal correcta es la `revision`.

### Entorno de la demostración (reproducible por el revisor)

Backend real con el **GTFS completo** del núcleo (`data/hito-03/replay/fomento_transit.zip`, 42 `route_id` / 12 líneas / 103 patrones / 95 estaciones) en modo replay sobre un PostgreSQL **desechable** (`mp020-replay-db`, `127.0.0.1:5434`) con las capturas congeladas `1532`/`1533` ingeridas por el colector real: 122 circulaciones, 44 con coordenada `map_matched` y 78 con GPS bruto etiquetado. **La base de desarrollo (`5433`) no se tocó.** El frontend admite `?at=<ISO>` para recorrer ese corte de forma repetible, con la etiqueta `REPLAY` y el instante siempre visibles.

El backend se sirvió en el puerto `8010` porque `8000` estaba ocupado por una instancia ajena a este worktree, que no se detuvo ni se modificó; por eso `vite.config.ts` acepta ahora `MADRID_PULSE_API_TARGET`, conservando `127.0.0.1:8000` por defecto.

### Nota abierta para el revisor (no bloqueante)

El GTFS oficial publica `route_color` real de Renfe, pero el contrato `/api/v1/catalog` de MP-019 no expone ese campo y MP-020 tenía prohibido reescribir el contrato. La paleta de líneas del cliente es por tanto una **elección de presentación propia**, determinista por `line_id` y sin identificadores incrustados (ADR-0011), **no** el color corporativo del operador. Queda anotado por si MP-021/MP-022 deciden publicarlo.

### Auditoría independiente y cierre

OpenAI Codex auditó el diff completo `74667c0..5f8b739` y no encontró
hallazgos abiertos. La inspección visual real se reprodujo en Chrome DevTools
contra la API `8010` y Vite `5181` desde la sesión coordinadora de Orca, porque
la superficie Chrome no estaba disponible en la sesión aislada del revisor:
se observó el mapa completo (12 líneas, 103 patrones y 95 estaciones), trenes
de varias líneas, degradación honesta sin vaciado ni rejuvenecimiento, URL
restaurable y ficha real de la circulación C5 `19656`, seguimiento explícito y
layout usable a `390x844`. La consola no mostró errores de aplicación; el 404
de `favicon.ico` es cosmético y los abortos iniciales corresponden al montaje
doble esperado de React StrictMode. El gesto de arrastre y la media feature de
movimiento reducido no pudieron repetirse desde esa herramienta concreta; se
aceptan con la evidencia ejecutada del implementador, los tests de regresión y
la auditoría del flujo de estado (`followIntent`/`cameraDetached`) y del sello
por `revision` en el bucle de presentación.

La auditoría de código confirmó: adquisición independiente por recurso, sin
`Promise.all`; descarte temporal por `revision` y uso de `snapshot_id` solo
para deduplicar contenido del informador; proyección de `progress_m` sobre la
polilínea indexada del patrón; identidad estable vehículo+viaje+día de
servicio; una única instancia MapLibre y reloj `requestAnimationFrame` fuera
de `setState`; y limitación de `route_color` declarada. El arreglo del mapa
invisible es efectivo: `.map-canvas` conserva `width` y `height` al 100 % aun
cuando el CSS diferido de MapLibre sustituye `position: absolute` por
`relative`, evitando el contenedor de altura cero.

Verificación reejecutada: frontend completo con Node **22.13.1** (lint,
typecheck, **49/49** tests y build; worker MapLibre de 550754 bytes), backend
exacto de CI **233/233** sin `skip` contra desarrollo con recuentos
`668/484/3/120/0`, y la misma suite sobre PostGIS fresco con migraciones
`0001`+`0002` (**233 ejecutados, 5 `skip` explícitos** por ausencia normal del
soak local). `git diff --check` está limpio; los cinco commits tienen autor y
committer exclusivos de Pedro Matute y no contienen `Co-authored-by`.

**Veredicto: APROBADA, sin hallazgos abiertos.** MP-020 pasa a `DONE`; MP-021
puede ramificar desde esta rama conforme al hito autorizado. La paleta propia
por falta de `route_color` en `/api/v1/catalog` permanece como limitación
conocida, no como divergencia silenciosa.


## MP-019 — Contrato de snapshot/API coherente (cerrada)

**MP-019 — Contrato de snapshot/API coherente**

Ejecutor: Claude (escalado a Opus) · Revisor: OpenAI Codex · Estado: **DONE** (aprobado por OpenAI Codex el 2026-11-22)

Worktree/rama: `mp-019-snapshot-api`, ramificada desde `mp-018-corredores-madrid` (MP-018 `DONE`, `728c667`). Datos del kit repuestos con `instalar.py --solo-datos`.

### Alcance de MP-019

Unificar el catálogo completo de MP-017 (`packages.gtfs.catalog`) y el catálogo de corredores de MP-018 (`packages.geo.catalog`, con `PositionMatch` raw→matched ya trazable) en un contrato de snapshot/API coherente: catálogo cacheable separado del snapshot operativo ligero, `snapshot_id` no asumido como ordenable, ETA con edad de GPS/feed/ETA distintas y procedencia, capa `rendered` (completa raw→matched→rendered) elegida mediante ADR comparativo de las tres alternativas de contrato temporal de `docs/hitos/hito-03/MEJORAS-PRODUCTO-VALIDADAS.md` (sección MP-019) — sin duplicar el motor de movimiento de MP-012.

### Decisión del contrato temporal — ADR-0014 (`Propuesto`)

El ADR se escribió **antes** de implementar, como exige el encargo, y está
registrado en `docs/adr/README.md` y en DEC-036. Alternativa elegida: la **1**
del encargo (progreso temporal compacto calculado por el backend),
materializada como una `ProgressEnvelope` por circulación y **extendiendo**
`packages/movement` de forma aditiva.

- **Alternativa 2 (cálculo puro compartido o equivalencia por replay)
  descartada:** el cliente es TypeScript y el motor Python; "compartir el
  cálculo" exigiría compilar a WASM (dependencia y presupuesto nuevos, no
  autorizados) o mantener una segunda implementación y demostrar su
  equivalencia — exactamente la implementación divergente que el encargo
  prohíbe, y duplicaría en el cliente reglas que no son de presentación (qué
  observación es utilizable, filtrado de saltos del feed de hasta 787 km/h,
  DEC-010).
- **Alternativa 3 (interpolación con búfer entre anclas) descartada como
  contrato principal, conservada como caso explícito:** es la única forma
  honesta de etiquetar `interpolated_between_known_anchors` y el contrato la
  soporta para replay y para un cliente que declare retraso de presentación,
  pero no puede ser *el* contrato del directo: exige un ancla futura que en
  vivo no existe, impondría un retraso de ~20 s (cadencia real medida en
  MP-003) a todos los usuarios y, al detenerse el feed, el caso difícil
  reaparece igual.
- Dos alternativas más, no planteadas en el encargo, evaluadas y descartadas en
  el ADR: bajar `observed_max_age_s` a 0 (rompería la semántica publicada de
  los cuatro estados de ADR-0004/DEC-010 sin necesidad) y escribir un segundo
  motor en `apps/api/` (violaría ADR-0012).

### Implementación entregada para revisión

- `packages/movement/rendering.py` (nuevo, dentro del paquete existente): los
  seis `rendering_method` del anexo, `ProgressEnvelope` compacta (una sola
  expresión monótona y acotada, sin array de puntos futuros, con espera
  programada respetada de verdad) y los instantes separados. Reutiliza
  `TripSchedule`/`service_seconds`/`MovementThresholds`; no reimplementa
  map-matching, horario ni límites físicos.
- Extensiones aditivas del motor: `MovementPosition.anchor_progress_m`
  (ancla realmente usada), `MovementEngine(schedule_cache=...)` opcional e
  inyectable, `TripSchedule.dwell_end_seconds`, y `build_trip_schedule` emite
  llegada **y** salida cuando difieren — sin eso el horario absorbía las
  esperas reales (11 paradas en la fixture C5, 60 s en Madrid-Atocha) y
  `dwell_until` no podía existir sin inventarlo.
- `apps/api/snapshot.py`: catálogo cacheable, snapshot operativo y tablero.
  `apps/api/db.py`: lecturas por lote (`latest_trip_updates`,
  `vehicles_for_trips`), `revision_marker` con ámbito del clúster y
  `feed_published_at` por observación.
- Endpoints nuevos `GET /api/v1/catalog` (`ETag`/`304`), `GET /api/v1/snapshot`
  (`no-store`) y `GET /api/v1/stations/{station_id}/board`. Todo **aditivo**:
  `/api/v1` conserva compatibilidad, no se abre `/v2` (ADR-0005).
- Migración `0002_api_batch_indexes`: tres índices medidos, solo estructuras de
  acceso.

### Las dos cautelas que MP-018 dejó abiertas — decisión tomada, no ignorada

1. **`shared_track_way_ids` no verifica SHA-256 como `_load_source`.** MP-019
   **no usa** ese helper: el snapshot consume exclusivamente
   `build_madrid_corridor_catalog`, cuyo `_load_source` sí valida el checksum
   de cada `GeometrySourceSpec` antes de construir el corredor. Ninguna
   afirmación de integridad del contrato depende del helper; queda como
   utilidad de inspección de MP-018 y se deja registrada aquí para que no se
   use como evidencia aislada en MP-020+.
2. **`match_position` devuelve `geometry_version` también en fallbacks
   `RAW`/`UNLOCATED`.** El contrato lo trata exactamente como pidió MP-018: se
   publica `map_matched` **solo** con `resolution == map_matched` y
   `projection` real, y en los fallbacks la versión viaja en un campo distinto,
   `geometry_candidate_version` (geometría candidata/contextual, no acredita
   proyección). `RenderedPosition` lo valida en construcción y rechaza
   `geometry_version` fuera del espacio `map_matched`; hay test de regresión.

### Evidencia ejecutada

- Suite Python exacta de CI, ya con `apps.api.tests.test_snapshot_contract`
  (36 tests) y `packages.movement.tests.test_rendering` (17 tests):
  **`Ran 206 tests ... OK`** contra la base de desarrollo, **sin ningún
  `skip`**; recuentos `668/484/3/120/0` idénticos antes y después y soak
  intacto (`rows=668, near_corridor=177, after=668`).
- Misma suite contra un contenedor PostgreSQL **fresco y desechable** con
  `0001`+`0002` aplicadas desde cero: **206 ejecutados, OK con 5 `skip`
  explícitos** (los del soak irrepetible de MP-007, DEC-035) — se declaran por
  separado, nunca como 206 pases en ambos. Repetido tres veces.
- Frontend con Node `20.20.0` (CI fija `22.13.1`): `npm ci`, lint, typecheck,
  **5/5 tests**, build con worker MapLibre `550754` bytes, idéntico a MP-018.
- `docs/evidence/mp-019-tres-snapshots-replay.md`: tres snapshots reales sobre
  las capturas congeladas `1532`/`1533` con reloj controlado y contenedor
  desechable. 119 y 121 vehículos de Madrid ingeridos (recuentos del kit),
  **44 de 119** con coordenada `map_matched` y 75 con GPS bruto etiquetado
  (honesto: solo 28 de 103 patrones tienen corredor validado tras MP-018),
  **13 circulaciones map-matcheadas con avance real** entre capturas, revisión
  `3 → 6 → 8` en el mismo ámbito, fallo parcial que degrada solo
  `delays_and_eta` sin vaciar vehículos ni rejuvenecer el GPS, y congelado que
  conserva el último dato válido con `revision.sequence` detenida.
- `docs/evidence/mp-019-explain-y-bench.md`: `EXPLAIN (ANALYZE, BUFFERS)` de
  las cuatro consultas y p50/p95 en dos datasets (fixture C5 y núcleo Madrid
  completo: 42 rutas / 12 líneas / 103 patrones), con equipo documentado
  (Apple M1, 8 GB, PostgreSQL 17.5). El snapshot pasa de 14 a 103 patrones sin
  cambio medible (8,47 → 8,59 ms de p50 con conexión reutilizada).
- Ausencia de N+1 probada además por conteo de `execute` reales sobre la
  conexión: constante entre 6 y 18 vehículos en `/snapshot`, entre 4 y 14 en
  `/live/vehicles`, y sin consulta por fila en el tablero.

### Hallazgos abiertos (registrados, no silenciados)

1. **El coste dominante de cada petición es abrir la conexión, no la
   consulta:** ~66 ms de los 68,91 ms de p50 de `/api/v1/health`. Registrado
   como **DEC-038** (pendiente del propietario) porque un pool
   (`psycopg_pool`) es una dependencia nueva, mismo criterio que
   DEC-019/DEC-030. La evidencia publica las dos columnas medidas.
2. **El `stop_time_update` por parada no está persistido** en el modelo
   canónico (solo `next_stop_id`, el primer no-`SKIPPED`): no existe evidencia
   directa de `SKIPPED` por parada. El tablero lo declara en `limitations` y
   expone `operator_next_stop_id` con la posición relativa como señal derivada,
   sin afirmar que una parada concreta fue omitida.
3. **Ningún `source_trip_id` del soak de MP-007 (`2026-11-19`) resuelve contra
   el ZIP GTFS del kit (`2026-11-20`):** Renfe regenera los `trip_id` entre
   publicaciones. No es un fallo de resolución — es la razón por la que la
   evidencia con datos reales se produjo con las capturas `1532`/`1533`, de la
   misma fecha que ese ZIP, y no con el soak.
4. **Nota de proceso sobre contenedores frescos:** `pg_isready` responde ya con
   el servidor temporal que la imagen arranca para `initdb` y luego apaga; la
   primera corrida contra un contenedor recién creado puede fallar con
   `server closed the connection unexpectedly`. Hay que esperar la línea
   `ready to accept connections` **posterior** a
   `PostgreSQL init process complete`. No es un fallo del repositorio.

### Primera auditoría independiente de Codex — dos hallazgos bloqueantes, corregidos

Codex reprodujo con éxito todo lo sustantivo de la primera entrega (suite en
verde contra desarrollo y contra PostGIS fresco con las dos migraciones,
frontend con Node `22.13.1` real, ausencia de N+1 con su propio conteo de
`execute`, `ETag`/`304`/`no-store`, respuesta fuera de orden, tablero programado
sin GPS, migración simétrica, autoría y `git diff --check` limpios) y no aprobó
por **dos hallazgos reales de aritmética temporal**, la misma familia de error
que el proyecto ya corrigió en MP-009 (DEC-021) y MP-013. Ambos reproducidos con
cifras y corregidos; evidencia completa en
`docs/evidence/mp-019-dst-y-horas-extendidas.md` y decisión en **DEC-039**.

**Hallazgo 1 — la inversa del día de servicio fallaba en los cambios de hora.**
`service_instant` sumaba los segundos *después* de convertir la medianoche a
UTC, o sea sobre un desplazamiento fijo: el `2026-03-29` la hora GTFS `03:30` se
reconstruía como `04:30+02:00` y el `2026-10-25` como `02:30+01:00`. La causa
raíz era más sutil que el síntoma: `service_seconds` restaba dos `datetime`
*aware* con el **mismo** `tzinfo`, caso que Python resuelve de forma naive, así
que en realidad era aritmética de reloj de pared y acertaba *por accidente*; al
escribir la inversa sobre UTC se eligió sin saberlo un modelo temporal distinto.
Corregido con una **única** implementación explícita en ambas direcciones
(`service_seconds` / `service_day_instant` nueva, en
`packages/movement/schedule.py`), a la que `apps/api/snapshot.py` delega para
que la API y el motor no puedan volver a divergir. Dos casos límite declarados
en el propio docstring: la hora que no existe en el adelanto se resuelve con el
desplazamiento previo al salto (comprobado que el feed real publica **0** horas
en esa franja, `02:xx`/`26:xx`, sobre 3,5 M de `stop_times`) y la hora ambigua
del atraso toma su primera ocurrencia.

**Hallazgo 2 — la fecha de servicio se elegía por reloj civil y perdía los
viajes `24:xx`.** A las `00:02` del 21 de noviembre, el viaje real
`1023V20533C4` (C4, `23:50` → `24:32`, patrón `validated` contra la relación OSM
`11332`) se resolvía contra el día 21: `service_seconds` daba 120 en vez de
86 520 y el motor lo situaba a **10 445 m** de su posición real, además de
marcarlo `expired` porque su `service_id` no está programado el 21. No es
marginal: **742 circulaciones del núcleo Madrid** tienen horas `24:xx` en el ZIP
oficial. Corregido con `apps.api.service.ServiceDateResolver`, que resuelve la
fecha **por circulación** con una ventana de ambigüedad derivada del propio feed
(su máximo `arrival`/`departure` menos 24 h: 3 180 s con el ZIP real, `0.0`
cuando no hay horas extendidas, y entonces el comportamiento es idéntico al
anterior). Un día candidato se admite solo si el `service_id` del viaje está
realmente programado en él **y** el instante cae dentro de su horario publicado;
si ninguno lo contiene, se conserva la fecha civil. La fecha resuelta gobierna
posición **y** `circulation_status`, el snapshot publica `service_date` por
circulación, y el tablero cruza los dos días candidatos con `service_date` por
entrada y `service_dates_considered`. Antes de la corrección, 23 llamadas del
día de servicio anterior eran invisibles en el tablero de Chamartín a esa hora.

**Fixture real nueva, sin tocar la aprobada.** `tests/fixtures/gtfs_c5_real/` no
tiene ninguna hora `24:xx` (máximo `23:53`), y ampliarla habría cambiado su
SHA-256 y con él el `gtfs_version` del que dependen la matriz de cobertura ya
aprobada de MP-018 (comparada byte a byte) y aserciones de MP-010/MP-017. Se
añade por eso `tests/fixtures/gtfs_24h_real/` con dos circulaciones extraídas
literalmente del ZIP oficial —una con corredor validado y otra sin geometría—,
su manifiesto completo y la herramienta genérica
`packages.gtfs.tools.extract_trips_fixture` (los `trip_id` son argumentos, sin
identificadores en la lógica). Registrada además en `docs/legal/ATTRIBUTION.md`
y `docs/legal/DATA_SOURCES.md`, aplicando por adelantado el mismo criterio que
el hallazgo legal de MP-018.

### Segunda auditoría independiente de Codex — un tercer hallazgo bloqueante, corregido

Codex confirmó que los dos hallazgos anteriores quedaron bien corregidos (la
reconstrucción DST es correcta, los dos trips `24:xx` resuelven a su fecha real,
la fixture nueva es byte-idéntica a una regeneración, 222/222 + 5 `skip`,
frontend `22.13.1`, replay con las siete invariantes, autoría y diff limpios) y
encontró un **tercer bloqueante de la misma familia** al revisar precisamente
esa corrección.

**Hallazgo 3 — la ventana del tablero no determinaba sus días de servicio.**
`build_station_board` derivaba sus días candidatos de `resolver.candidates`,
calculado con `now`, así que en cuanto `now` rebasaba el horizonte de horas
extendidas del feed dejaba de consultar el día anterior **aunque `lookback_s`
todavía lo cubriera**. Reproducido con `tests/fixtures/gtfs_24h_real/`,
estación `17000`, `lookback_s=600`: la llamada real de `1023V20533C4` a las
`24:32` (las `00:32` en reloj de pared, justo donde se agota el horizonte de esa
fixture) se veía a las `00:32` y **desaparecía a las `00:33`**, un minuto
después de ocurrir. Reproducido también contra el ZIP completo con
`1023V21644C2` (llamada `24:53`, estación `70200`): presente a las `00:53`,
ausente a las `00:54`.

**El mismo error existía en el sentido contrario**, y eso no venía en el
informe: la ventana hacia delante tampoco consultaba el día de servicio
siguiente. A las `23:55` del 20, con `lookahead_s=3600`, el tablero de la
estación `35002` devolvía `considerados=['2026-11-20']` y perdía
`1024S27997C5`, que sale a las `00:01` del día de servicio 21 — a seis minutos,
dentro de la anticipación pedida.

Corregido con `apps.api.service.service_dates_covering(start, end,
extended_horizon_s)`, que devuelve en orden cronológico todos los días cuyo
tramo `[medianoche local, +24 h + horizonte]` intersecta la ventana. El tablero
la llama con su ventana real (`window_start`/`window_end`) y
`ServiceDateResolver` con la ventana degenerada `[now, now]`, que reproduce
exactamente su comportamiento anterior para resolver la fecha de **una
circulación** en el snapshot. Los límites de cada día se calculan con
`service_day_instant`, de modo que la cobertura también es correcta en los dos
días de cambio de hora. El límite pasa a ser la **ventana pedida**: la llamada
se ve de `00:31` a `00:42` y desaparece en `00:43`, y la `24:53` del ZIP de
`00:53` a `01:03`.

Las entradas de dos días de servicio distintos salen ordenadas por **instante
absoluto**, comprobado con el ZIP (`23:50`, `23:53`, `23:56`, `00:01` del día
siguiente, `24:17`, `24:39`), así que mezclarlos no altera el orden.

**Las 11 regresiones nuevas se comprobaron contra el código anterior:** con
`candidates = resolver.candidates` la clase nueva produce 13 fallos (incluidos
los `subTest` minuto a minuto) y con la corrección pasa 5/5. Evidencia completa
en `docs/evidence/mp-019-dst-y-horas-extendidas.md` (sección «Hallazgo 3»);
DEC-039 ampliada.

### Matriz de evidencia reejecutada al completo tras la corrección

- Suite Python exacta de CI, con las 27 regresiones de las dos rondas:
  **`Ran 233 tests ... OK`** contra la base de desarrollo, **sin ningún
  `skip`**; recuentos `668/484/3/120/0` idénticos antes y después y soak intacto
  (`rows=668, near_corridor=177, after=668`). Evolución: 206 en la primera
  entrega → 222 tras la primera ronda → 233 tras la segunda.
- Misma suite contra PostgreSQL **fresco y desechable** con `0001`+`0002`
  aplicadas desde cero: **233 ejecutados, OK con 5 `skip` explícitos** (soak
  irrepetible de MP-007, DEC-035) — declarados por separado, nunca como 233
  pases en ambos.
- Frontend con **Node `22.13.1`**, la versión que fija CI: `npm ci` sin
  vulnerabilidades, lint, typecheck, **5/5 tests** y build con worker MapLibre
  `550754` bytes. (La primera entrega se verificó con `20.20.0`; hallazgo de
  proceso de la auditoría, corregido.)
- Replay de tres snapshots sobre las capturas reales `1532`/`1533` en
  contenedor desechable: invariantes de nuevo en verde (119 y 121 vehículos,
  44 `map_matched`, 13 con avance real, revisión `3 → 6 → 7` monotónica en su
  ámbito, parcial que degrada solo `delays_and_eta`, congelado que no
  rejuvenece).
- `EXPLAIN` y p50/p95: ninguna forma de consulta cambió en ninguna de las tres
  correcciones, así que los planes siguen vigentes; cifras remedidas en los
  tres escenarios del tablero sobre el núcleo completo — un día candidato
  (p50 8,20 / p95 12,56 ms), dos hacia atrás tras medianoche
  (p50 10,27 / p95 13,95 ms) y dos hacia delante antes de medianoche
  (p50 6,46 / p95 8,56 ms). Cruzar un día adicional cuesta ~2 ms de p50 y su
  índice se memoiza por fecha.

### Revisión final independiente de OpenAI Codex — APROBADA

Codex auditó el delta hasta `60a6eb3` y reprodujo de forma propia los dos
límites sobre el ZIP completo: con `lookback_s=600`, `1023V21644C2` permanece
visible hasta `01:03` y sale a `01:04`; a las `23:55`, con
`lookahead_s=3600`, `1024S27997C5` aparece a las `00:01` consultando los días
20 y 21. La lista mezclada de ambos días conserva el orden por instante
absoluto.

Se reejecutaron los 11 tests focales, la suite exacta de CI (**233/233**, sin
`skip`) contra desarrollo, la misma suite contra PostGIS fresco con ambas
migraciones (**233 ejecutados, 5 `skip` explícitos**), el frontend completo con
Node **22.13.1** (lint, typecheck, 5/5 tests y build) y el replay de tres
snapshots (siete invariantes en verde; fallo parcial limitado a
`delays_and_eta`). `git diff --check` quedó limpio y todos los commits desde la
base pertenecen exclusivamente a Pedro Matute, sin `Co-authored-by`.

**Veredicto: APROBADA, sin hallazgos abiertos.** MP-019 pasa a `DONE` y MP-020
puede ramificar desde esta rama conforme al hito autorizado. ADR-0014 sigue
`Propuesto` y DEC-039 registrada como propuesta; solo el propietario puede
promoverlas (ADR-0007).


## MP-018 — Corredores ferroviarios por patrón y sentido (cerrada)

**MP-018 — Corredores ferroviarios por patrón y sentido**

Ejecutor: OpenAI Codex · Revisor: Claude Code · Estado: **DONE** (aprobado por Claude Code el 2026-11-22)

Worktree/rama: `mp-018-corredores-madrid`, ramificada desde `mp-017-catalogo-madrid` (MP-017 `DONE`, `c28d5e4`). Datos del kit repuestos con `instalar.py --solo-datos`.

### Alcance de MP-018

Extender `packages/geo` (hoy un único corredor OSM fijo para C5, MP-011) a un catálogo de corredores por patrón/sentido, reutilizando `Corridor`/`build_corridor`/`ChainGap` tal cual. Mínimo real a descargar/verificar: revalidar C5 sin huecos, un ramal de C4 con geometría OSM real (mismo formato que `tests/fixtures/osm_c5_real/MANIFEST.md`), y un tramo compartido entre dos líneas (identificado desde el catálogo de MP-017, confirmado o descartado con datos reales, no forzado). Matriz de cobertura honesta (`validated`/`partial`/`pending`) para los patrones de las 12 líneas — `pending` es el resultado esperado para la mayoría, no un fallo.

### Implementación entregada para revisión

- `packages/geo/catalog.py`: índice por `PatternIdentity` (`route_id` + secuencia
  ordenada de paradas; el GTFS real no publica `direction_id`, por lo que no se
  inventa), estados `validated`/`partial`/`pending`, verificación de checksum,
  continuidad, distancia y orden de estaciones. Reutiliza sin reescribir
  `Corridor`/`build_corridor`/`ChainGap`.
- `PositionMatch`: conserva raw y expone `Projection`, `progress_m`,
  `geometry_version` y `distance_from_raw_m` cuando el corredor es validado.
  Un patrón `partial`/`pending` conserva GPS bruto etiquetado; raw ausente queda
  `unlocated`. No implementa `rendered` ni snapshot/API (MP-019).
- Fixture OSM real C4 versionada en `tests/fixtures/osm_c4_real/`: C4a ambos
  sentidos (`11332`, `9174510`) y C4b Colmenar→Parla (`9174511`), SHA-256,
  ODbL/atribución y comando reproducible. Las tres relaciones encadenan sin
  huecos. `9174510` y `9174511` comparten 77 IDs literales de `way`: vía física
  común confirmada, no solo estaciones coincidentes.
- Overpass devolvió `HTTP 502` al solicitar C4b Parla→Colmenar (`9174512`) y
  volvió a devolverlo al reintentar. El sentido se conserva `pending`; no se
  interpreta el fallo del endpoint como relación inexistente.
- Matriz completa reproducible en
  `docs/evidence/mp-018-corridor-coverage.csv`: **103 patrones / 12 líneas**.

| Línea | validated | partial | pending | Motivo principal |
|---|---:|---:|---:|---|
| C1 | 0 | 0 | 4 | sin geometría descargada |
| C2 | 0 | 0 | 14 | sin geometría descargada |
| C3 | 0 | 0 | 4 | sin geometría descargada |
| C4 | 5 | 0 | 0 | tronco verificado sobre relaciones C4a |
| C4a | 8 | 0 | 0 | ambos sentidos reales verificados |
| C4b | 3 | 1 | 4 | Colmenar→Parla real; variante de 14 paradas ambigua; sentido opuesto pendiente tras 502 |
| C5 | 12 | 2 | 0 | regresión MP-011; variantes de 7 paradas sin relación propia quedan partial |
| C7 | 0 | 0 | 14 | sin geometría descargada |
| C8a | 0 | 0 | 9 | sin geometría descargada |
| C8b | 0 | 0 | 4 | sin geometría descargada |
| C9 | 0 | 0 | 6 | sin geometría descargada |
| C10 | 0 | 0 | 13 | sin geometría descargada |
| **Total** | **28** | **3** | **72** | mayoría pending honesta, como exige MP-018 |

### Evidencia ejecutada

- `python3 -m unittest packages.geo.tests.test_catalog packages.geo.tests.test_real_feed -v`
  → **19/19 OK** (11 catálogo + 8 regresión C5; tras añadir la prueba semántica
  `partial` para geometría real no utilizable).
- Lista Python exacta de `.github/workflows/ci.yml`, incluyendo el nuevo módulo
  `packages.geo.tests.test_catalog`, con el entorno virtual ya instalado de
  MP-017 y `MADRID_PULSE_DATABASE_URL`/`DSN` a `127.0.0.1:5433` →
  **Ran 153 tests ... OK**; soak real `rows=668`, `near_corridor=177`,
  `after=668`.
- PostgreSQL real antes/después (consultas directas):
  `vehicle_position_observation=668`, `trip_update_observation=484`,
  `service_alert=3`, `source_ingestion_run=120`, `data_quality_event=0`.
- `npm ci` y, con Node `22.13.1`, `npm run lint`, `npm run typecheck`,
  `npm test`, `npm run build` → lint/typecheck verdes, **5/5 tests**, build
  Vite verificado (worker MapLibre 550754 bytes).
- `python3 -m compileall -q packages/geo` y `git diff --check` → sin errores.

Estado `REVIEW`: Codex no marca `DONE`; queda pendiente auditoría independiente
de Claude Code sobre el diff completo y re-verificación en este worktree.

### Primera revisión independiente (Claude Opus) — corrección documental pendiente de re-verificación

El revisor confirmó lo sustantivo de MP-018: CSV byte-idéntico al regenerado;
77 `way` compartidos que forman un tramo contiguo de 41,65 km
Parla–Cantoblanco, con 15 estaciones a menos de 50 m del eje OSM; C5 con
`gaps=0` y rechazo correcto al inyectar una discontinuidad; guard de sentido
que degrada a `partial` al vincular deliberadamente el sentido contrario; y
las tres fixtures C4 byte-idénticas a una nueva ejecución de `fetch_fixture`.
Ejecutó además la suite completa contra desarrollo y contra un segundo
PostgreSQL fresco desechable: **153/153 OK sin ningún `skip`** contra
desarrollo y **153 ejecutados, OK con 5 `skip` explícitos** (los cinco del
soak irrepetible de MP-007 documentados en DEC-035) contra el contenedor
fresco — se declaran por separado, no como 153 pases en ambos. Esta
verificación fresca fue realizada por el revisor; no se atribuye a la entrega
inicial de Codex y debe incluirse desde el ejecutor en futuras tareas
siguiendo el precedente de MP-015/016/017.

Único hallazgo bloqueante de esa ronda: DEC-024 y los registros legales
centrales aún nombraban solo la base derivada C5. Corregido sin cambiar código:
`docs/legal/ATTRIBUTION.md`, `docs/legal/DATA_SOURCES.md` (`osm.rail_geometry`)
y DEC-024 ahora cubren también `tests/fixtures/osm_c4_real/` y las relaciones
`11332`/`9174510`/`9174511`. La tarea permanece en `REVIEW` hasta que el mismo
revisor verifique esta corrección.

Notas no bloqueantes para MP-019 (no se corrigen en MP-018):

- `shared_track_way_ids` lee las fixtures directamente y no verifica SHA-256;
  `_load_source` sí lo hace. Un consumidor no debe tratar el helper aislado como
  evidencia de integridad sin validar antes el `GeometrySourceSpec`.
- `match_position` conserva `geometry_version` también en fallbacks `RAW` y
  `UNLOCATED`, aunque no exista una proyección real. MP-019 debe interpretar
  ese campo como versión de la geometría candidata/contextual y exigir
  `resolution=map_matched` + `projection` para afirmar que hubo map-matching.

### Segunda revisión independiente (Claude Opus) — APROBADA

Auditado el delta `933aa20..1b19df8` y el estado acumulado hasta `1b19df8`. La
corrección es **exclusivamente documental**: `git diff --stat 933aa20..1b19df8 --
packages/ tests/ apps/ services/ infra/ .github/` sale vacío, así que código y
fixtures son byte-idénticos al commit ya auditado en la primera ronda y esa
auditoría sigue siendo válida sin repetirla.

Los tres registros legales quedan completos y con la misma vara que la entrada
C5/DEC-024 original: `ATTRIBUTION.md` añade la fixture `osm_c4_real/` con la
misma clasificación (base derivada, no render), licencia `ODbL-1.0`, atribución
`© OpenStreetMap contributors`, separación de la licencia del código y reenvío
al manifiesto para fuente/fecha/checksums; la fila `osm.rail_geometry` de
`DATA_SOURCES.md` enumera ya los dos juegos de relaciones; y DEC-024 cubre ambas
fixtures con el *share-alike* por base derivada. Verifiqué contra las propias
fixtures que cada afirmación nueva es cierta: `11332`, `9174510` y `9174511`
llevan realmente `ref=C-4` y `network=Cercanías Madrid`, con `official_ref=C-4a`
las dos primeras y `C-4b` la tercera. Barrido completo de la documentación: los
únicos ficheros que siguen nombrando solo C5 son el manifiesto propio de
`osm_c5_real/` (correcto, el de C4 es el suyo) y `MVP_READINESS.md`, que es el
acta congelada de cierre de Hito 2 y debe seguir describiendo lo que existía
entonces. `LICENSE_MATRIX.md` es doctrina ODbL genérica y no inventaría
fixtures, por lo que cubre ambas sin cambio.

Re-verificación propia sobre `1b19df8`: suite exacta de CI **153/153 OK sin
`skip`** contra la base de desarrollo, recuentos `668/484/3/120/0` intactos
antes y después, y `git diff --check` limpio en todo el rango
`47f2732..1b19df8`. Autoría del commit de corrección exclusivamente
`Pedro Matute <pedromaaz13@gmail.com>` como autor y committer, sin
`Co-authored-by` ni firmas de generación por IA.

Corregí como revisor una única imprecisión en el acta de la ronda anterior: el
texto declaraba «153/153 OK en ambos», cuando mi corrida contra el contenedor
fresco fue de 153 ejecutados con 5 `skip` explícitos (el soak irrepetible de
MP-007, DEC-035). El precedente de MP-015/016/017 es declarar siempre los
`skip` por separado, nunca presentarlos como pases. Nada más que señalar.

**Veredicto: APROBADA, sin hallazgos abiertos.** MP-018 pasa a `DONE` y queda
disponible como base geométrica para MP-019. Las dos notas no bloqueantes
(SHA-256 en `shared_track_way_ids`, `geometry_version` en fallbacks
`RAW`/`UNLOCATED`) quedan registradas arriba como pendientes explícitas de
MP-019, no como deuda silenciosa.


## MP-017 — Catálogo completo de Madrid (identidad y vigencia) (cerrada)

**MP-017 — Catálogo completo de Madrid (identidad y vigencia)**

Ejecutor: Claude Code · Revisor: OpenAI Codex · Estado: **DONE**

Worktree/rama: `mp-017-catalogo-madrid`, ramificada desde `mp-016-fiabilidad-live` (MP-016 `DONE`). Datos del kit repuestos con `instalar.py --solo-datos` (no versionados, `/data/` en `.gitignore`).

### Alcance de MP-017

1. **Catálogo completo** (`packages/gtfs/catalog.py`, nuevo): `build_catalog(topology)` agrupa el GTFS completo del núcleo por línea/variante/patrón, reutilizando `route_groups()`/`validate_topology()` ya existentes de MP-010 — conserva una línea aunque no tenga ningún patrón válido (todos sus trips huérfanos) o ningún vehículo observado.
2. **Enumeración explícita de servicios programados**: `scheduled_service_ids_for_date`/`scheduled_trip_instances_for_date` aplican `calendar.txt` (día de la semana + rango) y, si existe, `calendar_dates.txt` (excepciones `ADDED`/`REMOVED`) — distinto del fallback `PositionMode.SCHEDULED` del motor de movimiento, que solo resuelve un `trip_id` ya conocido por el feed en vivo, no enumera el día completo. **Hallazgo real:** el ZIP oficial de Renfe verificado en esta tarea (descarga del kit, 2026-11-20) **no incluye `calendar_dates.txt`** — el soporte queda listo para cuando exista, pero hoy `calendar.txt` sigue siendo la única fuente real.
3. **Avisos por estación:** Renfe publica alertas por `stopId` sin `routeId` (hallazgo P1 real de `docs/hitos/hito-03/referencia/01-auditoria-live.md`, ej. `AVISO_527127` para `stopId=60104`, Valdemoro) — el filtro anterior, solo por prefijo de núcleo de `route_id`, las descartaba como fuera de alcance. `_persist_alerts` acepta ahora un conjunto opcional `madrid_stop_ids` (cargado una vez al arrancar el colector desde el GTFS real, `MADRID_PULSE_GTFS_SOURCE`) y resuelve por ruta O por estación; sin ese catálogo, conserva el comportamiento anterior (documentado, no fabricado).
4. **Un retraso viejo no completa el viaje de hoy:** `apps/api/db.latest_trip_update` exigía solo `source_trip_id`, sin cota temporal — como un `trip_id` GTFS recurre cada día que su `service_id` está activo, el retraso de ayer podía seguir siendo "el último" hasta que llegara una fila de hoy. Se añade `observed_after` (ventana de 20h desde `apps/api/service.py`, cubre el día de servicio completo de Cercanías incluidos los `24:xx`).

### Pruebas y evidencia ejecutada

- `packages.gtfs.tests.test_catalog` (nuevo, 10 tests): 6 síncronos con topología sintética (excepciones `calendar_dates` ADD/REMOVE, huérfano no fabricado, línea con 0 patrones conservada) + 4 gateados por la presencia del ZIP oficial completo (`skip` explícito si no está, mismo criterio que el soak de MP-007): 42 `route_id`/12 líneas reales, `stopId` 60104 real en el catálogo Madrid, trip real `1023V19788C5` con horas `24:02`/`24:05`/`24:08` enumerado sin desplazar `service_date`, un `SPECIAL_` nunca aparece como instancia programada.
- `services.collector.tests.test_collector_cycle` (+3 tests): aviso por estación se descarta sin catálogo (comportamiento anterior conservado), se persiste con el catálogo real, y un `stopId` fuera del catálogo dado sigue descartándose (no se "adivina" Madrid por tener cualquier `stopId`).
- `apps.api.tests.test_api_contract` (+2 tests): un retraso insertado hace 26h no se devuelve para el viaje de hoy; uno de hace 2h sí.
- Suite completa (lista exacta de CI, +`packages.gtfs.tests.test_catalog`) contra la base de desarrollo real → **138/138 OK**; recuento `668/484/3/120/0` confirmado antes y después.
- Misma suite contra un segundo contenedor PostgreSQL fresco desechable, **con `data/` renombrado temporalmente fuera del worktree** (simulando CI real, donde el ZIP oficial no existe) → **138 tests, 9 `skip`** (5 del soak histórico de MP-007 + 4 nuevos de `test_catalog` gateados por el ZIP ausente, ninguno inesperado) — contenedor eliminado al terminar, `data/` restaurado.
- `git diff --check` limpio.
- `.github/workflows/ci.yml` actualizado con el nuevo módulo `packages.gtfs.tests.test_catalog`.

### Primera revisión de Codex — dos hallazgos reales, corregidos

Codex auditó `92c1b09..1276c9f`: replay correcto, 138/138 contra desarrollo (`668/484/3/120/0` intacto), 138+9 skip contra PostGIS fresco, frontend y `git diff --check` en verde, autoría confirmada. Dos omisiones bloqueantes reales frente a `PLAN-Y-ACEPTACION.md`/`MATRIZ-CIERRE-MADRID.md`:

1. **Versión/procedencia e identidad red/operador ausentes:** `Catalog`/`LineVariant`/`ScheduledTripInstance` no llevaban `gtfs_version` ni `network_id`/`operator` — el kit exige explícitamente "versiones y procedencia" e "identidad completa red/operador de circulación" (MP-017), no solo `trip_id`/`route_id` (que por sí solos no distinguen núcleos, ver ADR-0008). Corregido: `Catalog.gtfs_version: str` (obligatorio, mismo identificador que `/api/v1/health` ya publica vía `_source_version`), `ScheduledTripInstance.network_id`/`operator` (derivados de `Route.network_id` y la constante documentada `OPERATOR = "Renfe"`, único operador integrado en el alcance actual, DEC-006).
2. **Sin "estado activo separado de último histórico":** `latest_vehicle_histories`/`list_vehicles` devuelven todo vehículo histórico sin cota — la ventana de 20h de la primera entrega solo afectaba a `trip_update_observation` (retrasos), no a la propia circulación. Corregido: nuevo campo `VehicleOut.circulation_status` (`active`/`expired`/`unresolved`), calculado comparando el `service_id` real del `trip_id` del vehículo contra `scheduled_service_ids_for_date(topology, service_date)` — distinto de `quality.stale` (que mide solo antigüedad del GPS, no si el servicio sigue programado hoy).

Añadidos 3 tests (provenance/identidad del catálogo real; `circulation_status` activo/caducado/sin resolver con el trip real de la fixture reducida, calendario de un solo día). Suite completa reejecutada: **141/141 contra desarrollo** (`668/484/3/120/0` intacto) y **141 tests/10 skip** contra un segundo contenedor PostgreSQL fresco desechable con `data/` ausente (simulando CI real) — el skip adicional es el nuevo test de provenance, gateado igual que los otros 4 por la ausencia del ZIP oficial. `git diff --check` limpio. Reenviado a Codex para segunda verificación.

### Segunda revisión de Codex — un hallazgo real, corregido

Codex confirmó que los dos hallazgos de la primera ronda quedaban resueltos (31 tests de catálogo/API en verde, `circulation_status` correcto, autoría y `git diff --check` limpios), pero encontró un hallazgo real nuevo: **el contrato OpenAPI congelado quedó desincronizado.** Añadir `VehicleOut.circulation_status` cambia la forma real que sirve `app.openapi()`, pero `apps/api/openapi.json` no se regeneró, y `apps/web/src/types.ts` + el ejemplo de `docs/DATA_CONTRACTS.md` seguían describiendo el contrato anterior.

Corregido: `apps/api/openapi.json` regenerado con el comando exacto ya documentado en `apps/api/README.md`; `apps/web/src/types.ts` (`Vehicle.circulation_status`) y el ejemplo + campo obligatorio nuevo en `docs/DATA_CONTRACTS.md` sincronizados. Añadido además el `test_committed_openapi_json_matches_the_live_schema` que pedía Codex ("comprobación pertinente"): compara `app.openapi()` contra el JSON congelado en cada corrida, para que este tipo de drift falle en CI en vez de requerir una auditoría manual futura.

Suite completa reejecutada: **142/142 contra desarrollo** (`668/484/3/120/0` intacto); frontend lint/typecheck/5 tests/build en verde tras tocar `types.ts`. `git diff --check` limpio. Reenviado a Codex para tercera verificación.

### Tercera revisión de Codex — APROBADA

Codex auditó el delta `07cdf6e..2663837` y el estado acumulado hasta `2663837`: OpenAPI congelado coincide exactamente con `app.openapi()`, `circulation_status` sincronizado en OpenAPI/`types.ts`/`DATA_CONTRACTS.md` y el nuevo test impide drift futuro. Repitió 15 tests focales de contrato/`circulation_status`/catálogo, frontend completo, autoría, recuentos `668/484/3/120/0`, `git diff --check` y limpieza del worktree — todo en verde, único aviso informativo conocido (chunks Vite >500 kB, no bloqueante). **Veredicto: APROBADA, sin hallazgos.** MP-017 pasa a `DONE`.


## MP-016 — Fiabilidad realtime (SKIPPED, UTC, live/replay) (cerrada)

**MP-016 — Fiabilidad realtime (SKIPPED, UTC, live/replay)**

Ejecutor: OpenAI Codex · Revisor: Claude Code · Estado: **DONE**

Worktree/rama: `mp-016-fiabilidad-live`, ramificada directamente desde `main` (`990c95d`, que ya contiene toda la cadena MP-010→MP-015 fusionada vía PR #2). Primer commit (`d0f4b3c`): instalación verificada del kit externo Hito 3 v4 (`docs/hitos/hito-03/`), integridad y replay confirmados antes de tocar código (ver "Hito autorizado actualmente" arriba para el detalle completo de alcance/criterios).

### Alcance de MP-016

Reproducir y corregir, contra el HEAD real (no asumiendo que el parche de referencia (`data/hito-03/madrid-pulse-live.patch`, 11 ficheros) aplica literalmente):

1. Paradas `trip_update` con `schedule_relationship=SKIPPED` sin campo `arrival` — deben tratarse a nivel de parada/ETA, nunca congelar por sí solas la circulación completa (solo cancelación real, espera acreditada, falta de trayectoria o caducidad justifican ese comportamiento).
2. Timestamps leídos de PostgreSQL deben normalizarse a UTC explícito (el parche de referencia toca `apps/api/db.py` con `.astimezone(timezone.utc)` en varios puntos — verificar si psycopg ya devuelve aware datetimes en este HEAD antes de aplicar ciegamente).
3. Distinción explícita Live/Replay documentada y reproducible localmente.
4. Salud de feed/colector/GPS medida y expuesta por separado, no como un único estado agregado.

### Pruebas que debe superar antes de pasar a `REVIEW`

- Replay (`python3 data/hito-03/replay/comprobar.py`) reproduce los conteos de fixture ya verificados en la instalación: corte `1532` → 119 vehículos Madrid/119 matches/49 `SKIPPED` sin `arrival`; corte `1533` → 121/121/49. Estos conteos son de la fixture congelada, no una expectativa del feed real de hoy.
- Suite real del proyecto contra PostgreSQL real (no solo la sonda Python del replay).
- Casos explícitos: respuesta inválida del feed, reloj desfasado, colector detenido (comprobar en pantalla qué ve una persona cuando el colector se detiene — instrucción explícita del propietario para la revisión de Claude).

### Implementación entregada para revisión

- `SKIPPED` sin `arrival` se acepta en raw y nunca se elige como próxima parada comercial; no se fabrica horario ni se congela la circulación. Descarga o validación inválida queda como `source_ingestion_run.status=error` con hash de los bytes recibidos; JSON roto conserva observaciones previas y un feed válido vacío queda `ok` con 0 entidades.
- Todas las lecturas `timestamptz` que entran en contratos canónicos desde API/calidad se convierten explícitamente a UTC. Reproducción real: `SHOW TIME ZONE` devolvió `Europe/Madrid`, psycopg entregó `2026-11-20T15:32:00+01:00`, el contrato lo rechazó antes del límite y aceptó `2026-11-20T14:32:00+00:00` tras normalizar.
- Salud separada por `alerts`, `trip_updates` y `vehicle_positions`; `data_age_s` usa la cabecera real y `poll_age_s` la edad del sondeo. Un sondeo reciente de fichero viejo y un colector detenido producen `stale` por razones distinguibles. La salida real con el colector detenido mostró HTTP 200 y los tres feeds `stale`, con `poll_age_s≈267886` y `data_age_s≈267890`, no un falso `ok`.
- `MADRID_PULSE_MODE=replay|live` es explícito. Live rechaza fixtures, modos desconocidos y catálogos fuera de vigencia; `/health` publica modo, SHA-256 y ventana GTFS. README contiene ambos arranques. El rótulo mínimo de App cambia `Actualizado` por `Consulta`, porque esa hora es del navegador, no de la fuente.
- Cambio de viaje del mismo vehículo: si la observación anterior tiene otro `trip_id`, el servicio pasa `previous=None` al motor; regresión añadida.

### Diferencias respecto al parche de referencia

`git apply --check data/hito-03/madrid-pulse-live.patch` sí fue limpio contra `d7447c3`; sus 11 ficheros se incorporaron tras auditar su intención. Se amplió deliberadamente con configuración/metadata Live-Replay (`config.py`, `gtfs_source.py`, `main.py`, esquemas y documentación), `poll_age_s`, casos JSON roto/feed vacío/colector detenido/cambio de viaje y contrato/OpenAPI. No se abordaron filtrado de históricos, selectores de avisos por estación, catálogo completo ni geometría multi-corredor: pertenecen al snapshot/identidad/geometría de MP-017→MP-019 según el kit, y adelantarlos aquí violaría el alcance.

### Evidencia ejecutada

- `python3 data/hito-03/replay/comprobar.py` → `1532`: 119 vehículos Madrid, 119 matches, 469 updates, 49 SKIPPED; `1533`: 121, 121, 474, 49.
- `.venv/bin/python -m unittest ... -v` (lista exacta de CI) contra desarrollo → `Ran 123 tests ... OK`; recuentos antes/después intactos: `vehicle=668`, `trip=484`, `alerts=3`, `runs=120`, `quality=0`.
- Mismo comando contra contenedor desechable `postgis/postgis:17-3.5` en `127.0.0.1:55416`, migración desde cero → `Ran 123 tests ... OK (skipped=5)`; 118 ejecutados en verde, 5 skips esperados por el soak histórico. Contenedor `mp016-postgis-fresh` eliminado al terminar; no tenía volumen y sus datos efímeros no son recuperables ni necesarios.
- `npm run lint && npm run typecheck && npm test && npm run build` → lint/typecheck verdes, 2 ficheros/5 tests verdes, build Vite verde y worker MapLibre verificado (`550754 bytes`).
- `git diff --check`, OpenAPI regenerado y suite focalizada de 36 tests se ejecutan de nuevo en el cierre previo al commit.

### Revisión independiente de Claude Code — APROBADA

Auditoría completa sobre `f9c3e2b` (autoría exclusiva de Pedro Matute, sin coautores, confirmado con `git log --format='%an <%ae>|%cn <%ce>'`). Revisé el diff real punto por punto, no solo el resumen del ejecutor:

- `packages/contracts/raw.py`/`normalize.py`: `arrival` pasa a opcional, `schedule_relationship` se añade con alias `scheduleRelationship` y `exclude_if` — verifiqué que `exclude_if` es un parámetro real de `pydantic.Field` en la versión instalada (`2.13.4`, no un kwarg inventado) ejecutando `inspect.signature(Field)` y probando parseo/serialización directamente en el intérprete. `next_stop_id` ahora salta las paradas `SKIPPED` al elegir la próxima parada comercial.
- `services/collector/collector.py`: el parseo/validación se movió dentro del `try`, así un JSON roto o un esquema inesperado queda registrado en `source_ingestion_run` con el hash real de los bytes recibidos (antes quedaba fuera del bloque, hallazgo P0 de la auditoría) — confirmado con los 3 tests nuevos (`test_schema_failure_records_payload_hash_and_no_source_time`, `test_broken_json_is_an_error_but_does_not_delete_existing_observations`, `test_valid_empty_feed_is_success_not_network_failure`).
- `apps/api/service.py` (`feed_health`): separa `poll_age_s` (edad del sondeo) de `data_age_s` (edad real de la cabecera `source_timestamp`), exactamente el hallazgo P0 de la auditoría (antes usaba `started_at` para ambos). **Verificado en vivo, no solo en test unitario** (instrucción explícita del propietario): arranqué la API de este worktree contra la base de desarrollo real en un puerto aparte (`8099`, sin colector corriendo) y `/api/v1/health` devolvió los tres feeds en `stale` con `poll_age_s≈268163`/`data_age_s≈268169` — nunca un falso `ok`, coincide en orden de magnitud con lo reportado por Codex.
- `apps/api/db.py`/`packages/quality/db.py`: conversión `.astimezone(timezone.utc)` en todos los puntos de lectura — necesaria en este HEAD (no un arreglo ya obsoleto), consistente con el hallazgo de huso horario de la auditoría.
- `apps/api/gtfs_source.py`: modo `live` rechaza explícitamente rutas de fixture y GTFS fuera de vigencia; `gtfs_version`/`gtfs_valid_from`/`gtfs_valid_until` se exponen en `/health`.
- `apps/api/service.py` (`_movement_position`): `previous` ya no se pasa al motor cuando pertenece a otro `trip_id` — confirmado con `test_previous_observation_from_another_trip_is_not_passed_to_engine`.
- `apps/web/src/App.tsx`: rótulo cambiado de "Actualizado" a "Consulta" — correcto, es la hora del navegador, no la de la fuente.

**Re-ejecución independiente, no solo lectura del reporte:**
- `python3 data/hito-03/replay/comprobar.py` → idéntico a lo reportado (1532: 119/119/49; 1533: 121/121/49).
- Suite completa (lista exacta de CI) contra la base de desarrollo real → **123/123 OK**; recuento `668/484/3/120/0` confirmado antes y después, sin residuo.
- Misma suite contra un segundo contenedor PostgreSQL fresco desechable (`postgis/postgis:17-3.5`, puerto `55417`, sin volumen) con migración desde cero → **123 tests, 5 skip, 118 en verde** — contenedor eliminado al terminar.
- Frontend: `lint`/`typecheck`/`test` (5/5)/`build` en verde, worker MapLibre verificado (`550754 bytes`), `git diff --check` limpio.

**Veredicto: APROBADO, sin hallazgos.** Las diferencias respecto al parche de referencia (ampliación con `poll_age_s`, casos JSON roto/feed vacío/cambio de viaje, configuración Live/Replay) están justificadas y dentro del alcance declarado de MP-016; lo deliberadamente diferido (catálogo completo, geometría multi-corredor, avisos por estación, filtrado histórico) pertenece correctamente a MP-017→MP-019 según el kit. MP-016 pasa a `DONE`.


## MP-015 — E2E y readiness MVP (cerrada)

**MP-015 — E2E y readiness MVP**

Ejecutor: Claude Code · Revisor: OpenAI Codex · Estado: **DONE**

Worktree/rama: `mp-015-e2e-readiness`, ramificada desde `mp-014-frontend` (MP-014 `DONE`). Dependencias MP-009/MP-012/MP-013 confirmadas como ancestros de `mp-014-frontend` con `git merge-base --is-ancestor` antes de ramificar (mismo mecanismo que DEC-015).

### Alcance real (decisión de secuenciación, no reducción de alcance)

`docs/TASKS.md`/`docs/PLAN.md` (F9) definen MP-015 como: replay E2E, pipeline DuckDB/dbt de métricas con cobertura, CI verde, checklist de MVP, ADRs reconciliados. Hallazgo antes de empezar: `analytics/dbt/` y `analytics/duckdb/` siguen vacíos (solo README) — su README decía que se implementarían "como parte de MP-009", pero MP-009 (DEC-021) deliberadamente difirió `daily_line_metrics`/`station_daily_metrics` por `route_id`/`station_id` porque esa resolución (`trip_id`→`route_id`, `stop_id`→`station_id`) dependía de MP-010, que no era su dependencia. Con MP-010→MP-014 ya `DONE`, esa resolución existe de verdad (`packages.gtfs.Topology`) — MP-015 es la primera tarea que puede construir esas métricas sin inventar un join no verificado.

Orden de trabajo elegido (cada paso se implementa, se prueba de verdad y se documenta antes de pasar al siguiente, igual que el resto del hito):

1. Resolución Python real `trip_id`→`route_id`/`stop_id`→`station_id` sobre el Parquet raw ya exportado por MP-009, extendiendo `services/snapshotter/gold.py` (seguir usando DuckDB como único motor, conforme DEC-021 — no se añaden `pandas`/`pyarrow`), calculando `daily_line_metrics`/`station_daily_metrics` reales directamente ahí.
2. **Corrección tras ejecutar el paso 1:** no se introduce un proyecto dbt-core/dbt-duckdb literal (decisión tomada y documentada como [ADR-0013](adr/0013-no-literal-dbt-engine.md)/DEC-034, no la planificación original de esta misma lista) — la resolución `route_id`/`station_id` es lógica Python que no encaja en SQL puro sin duplicarla, y DEC-021 ya fijó un único motor sin dependencias añadidas. `services/snapshotter/gold.py` ya aplica la disciplina dbt (capas, tests, documentación) sin el motor dbt.
3. CI (`.github/workflows/`) que ejecute las suites reales (Python + frontend) en cada push/PR.
4. Replay E2E determinista en `tests/e2e/` sobre fixtures reales ya existentes (sin llamadas de red en vivo, para que CI no dependa de Renfe/OSM/CRTM) que ejercite el pipeline completo: ingestión canónica → PostgreSQL → motor de movimiento → API → build de frontend.
5. Auditoría de contenido de los 12 ADRs contra la implementación real — se corrige redacción/contenido que ya no coincide con lo implementado; **la promoción de `Propuesto` a `Aceptado` sigue siendo decisión exclusiva del propietario** (ADR-0007), no se cambia ningún `Estado` sin su aprobación explícita.
6. Checklist de preparación de MVP (documento nuevo) resumiendo el estado real de Hito 2 para la aceptación del propietario.

### Checklist de MP-015

- [x] Resolución real `route_id`/`station_id` sobre datos exportados, con tests.
- [x] **`daily_line_metrics`/`station_daily_metrics` calculadas de verdad (DEC-033/DEC-034):** `services/snapshotter/gold.py` extendido con `build_line_daily_metrics`/`build_station_daily_metrics` sobre `packages.gtfs.Topology`, en vez de dbt-duckdb literal — decisión documentada ([ADR-0013](adr/0013-no-literal-dbt-engine.md)/DEC-034): la resolución es lógica Python que no encaja en SQL puro sin duplicarla, y DEC-021 ya fijó un único motor sin dependencias añadidas. 10 tests nuevos reales (fixture GTFS + PostgreSQL), corrida real contra el soak completo del `2026-11-19`: 3 filas en `daily_line_metrics`, 18 en `station_daily_metrics`.
- [x] **CI real (DEC-035):** `.github/workflows/ci.yml` — job Python (PostgreSQL de servicio, migraciones desde cero, suite real) + job frontend (lint/typecheck/test/build). Verificado de verdad en ambos sentidos: 114/114 contra la base de desarrollo (sin `skip`), 110 en verde + 5 `skip` explícitos (de 115) contra un contenedor PostgreSQL fresco simulando CI exactamente. Hallazgo real corregido en el proceso: 5 tests usaban `CollectorConfig()` en vez de `.from_env()`, ignorando `MADRID_PULSE_DATABASE_URL` en silencio.
- [x] **Replay E2E determinista (`tests/e2e/test_replay.py`):** inyecta bytes de fixtures reales como respuesta del `fetcher` del colector real — JSON crudo con forma de Renfe → colector → PostgreSQL real → resolución GTFS → API real, sin red en vivo. Dos escenarios reales: la fixture de MP-004 (nunca fabrica una resolución) y un payload sintético con forma real para un trip que sí existe en la GTFS reducida (resuelve `route_id`/posición de extremo a extremo).
- [x] **Auditoría de contenido de los 12 ADRs completa (sin cambiar ningún `Estado` a `Aceptado`):** balance final tras dos rondas de revisión de Codex. ADR-0002: aclara que CRTM quedó verificado por licencia pero nunca integrado (solo Renfe se implementó). ADR-0004: corrige la nomenclatura real de campos (`position.mode`, no `position_mode`; sin `source` público). ADR-0005: nota de drift real añadida (las tablas gold por línea/estación ya se calculan desde MP-015/DEC-033; los endpoints history/metrics siguen sin implementar). ADR-0008/0009/0010: corrigen la referencia obsoleta "pendiente... en el cierre de Hito 1" (ese cierre ya ocurrió el 2026-11-19 sin promoción) a "cierre de Hito 2", igual que `docs/adr/README.md` y `docs/DECISIONS.md` (DEC-017/DEC-013). **ADR-0003 permanece intacto, sin modificación de su texto** — una primera ronda lo había editado para eliminar la implicación de dbt-core literal, lo que violaba el proceso de ADR (regla 8, `AGENTS.md`); revertido, y esa decisión se documenta ahora en el nuevo [ADR-0013](adr/0013-no-literal-dbt-engine.md) (`Propuesto`), referenciado también desde `docs/ARCHITECTURE.md`/`docs/PLAN.md`/`analytics/dbt/README.md`/DEC-034. Los otros ADRs (0001, 0006, 0007, 0011, 0012) se verificaron contra la implementación real sin encontrar drift.
- [x] **Checklist de preparación de MVP (`docs/MVP_READINESS.md`):** resumen ejecutivo del cumplimiento del objetivo de Hito 2, demo local reproducible, estado real de tests, principios de datos verificados, hallazgos clave, límites conocidos documentados y pendientes exclusivos de gobernanza del propietario. También recuperado `docs/HITO_3_BACKLOG.md` (Sección 7 de la autorización) desde la rama `chore/hito-2-coordination`, que había divergido de la cadena `mp-010`→`mp-015` y se habría perdido al fusionar a `main` sin traerlo explícitamente.
- [x] `docs/TASKS.md`/`docs/STATUS.md`/`docs/CHANGELOG.md`/`docs/DATA_CONTRACTS.md`/`docs/DECISIONS.md` actualizados con evidencia real.

### Resultado y límites

Implementación completa, lista para revisión cruzada de Codex. Resumen de
las seis fases: (1) `daily_line_metrics`/`station_daily_metrics` reales
(DEC-033); (2) CI real + replay E2E determinista, con un hallazgo real
corregido en el proceso (DEC-035, 5 tests ignoraban
`MADRID_PULSE_DATABASE_URL`); (3) auditoría de contenido de los 12 ADRs, 6
corregidos, ningún `Estado` cambiado; (4) `docs/MVP_READINESS.md` y
recuperación de `docs/HITO_3_BACKLOG.md` desde una rama divergente que se
habría perdido al fusionar.

Verificación ejecutada: 114/114 tests Python contra la base de desarrollo
(102 previos + 10 de la fase 1 + 2 de E2E replay); contra un PostgreSQL
recién creado (migraciones aplicadas desde cero, simulando CI) 109 en verde
+ 5 `skip` explícitos y documentados (dependen del soak real irrepetible de
MP-007, DEC-035). Frontend: lint/typecheck/5 tests/build en verde.
PostgreSQL restaurado exactamente a `668/484/3/120/0` en todos los casos.
Corrida real end-to-end del exportador (`python -m services.snapshotter
2026-11-19` contra el soak completo): 3 líneas, 18 estaciones, sin filas
fabricadas. Límites documentados en DEC-033 (calendario sin excepciones,
umbral de puntualidad calibrable, sin `data_quality_events_count` por
estación) y DEC-035 (alcance real de CI: la suite de replay/contrato es
reproducible desde cero; los tests atados al histórico puntual de MP-007 no
lo son por diseño y se saltan explícitamente, nunca fallan en silencio ni se
declaran superados sin ejecutarse).

### Bloqueos

Ninguno tras la corrección de la primera ronda de revisión de Codex (ver
abajo). Pendiente de re-verificación real de Codex antes de `DONE`.

### Primera revisión de Codex — seis hallazgos reales, todos corregidos

Codex verificó de forma independiente (re-ejecutó la suite completa contra
la base de desarrollo y contra su propio contenedor PostgreSQL fresco,
114/109+5 confirmados) y encontró seis problemas reales:

1. **Escala de porcentaje incorrecta:** `build_line_daily_metrics` calculaba
   `delay_coverage_pct`/`on_time_pct_of_covered` como fracción `0..1`, pero
   `infra/migrations/0001_init.up.sql` (`numeric(5,2) CHECK BETWEEN 0 AND 100`)
   y `docs/DATA_CONTRACTS.md` (ejemplo `78.3`/`87.2`) exigen `0..100`.
   Corregido (`* 100`, redondeado a 2 decimales); añadido un test de
   regresión explícito (`test_percentages_match_the_real_0_100_schema_not_a_0_1_fraction`).
2. `docs/DATA_CONTRACTS.md`/`apps/api/README.md`/ADR-0005 seguían diciendo
   que las tablas gold "siguen vacías" — corregido: ya se calculan
   (DEC-033), lo que falta es solo exponerlas vía endpoint.
3. `docs/MVP_READINESS.md` describía mal la semántica `NULL` real —
   corregido: `delay_coverage_pct` nunca es `NULL` para una fila emitida
   (toda fila tiene `trips_scheduled >= 1` por construcción);
   `on_time_pct_of_covered` sí, cuando `trips_with_delay_data = 0`.
4. **Hallazgo de proceso real:** DEC-034 había reescrito la "Decisión" de
   [ADR-0003](adr/0003-storage-strategy.md) (`Aceptado`) sin pasar por el
   proceso de ADR (regla 8, `AGENTS.md`). Corregido: revertido el texto de
   ADR-0003 a su redacción original; DEC-034 queda como nota de
   implementación a nivel `DECISIONS.md`, sin tocar la Decisión aceptada.
5. `docs/HITO_3_BACKLOG.md` (área 5) repetía el dato obsoleto "~24
   vehículos C5" — corregido con el desglose real de DEC-029 (4 C5 + 19
   otras líneas + 1 refuerzo sin resolver).
6. `docs/MVP_READINESS.md` decía "cada push/PR" cuando el `on:` real de
   `ci.yml` es `push` a `main` + `pull_request` — corregido con la
   redacción precisa (los worktrees de tarea nunca se empujan a `origin`
   directamente).

Los seis se corrigieron en este mismo worktree; 115/115 tests (114 + 1
nuevo de regresión) verificados de nuevo contra la base de desarrollo y
contra un segundo contenedor PostgreSQL fresco desechable (110 en verde +
5 `skip`, de 115).

### Segunda revisión de Codex — tres hallazgos reales, todos corregidos

Codex re-verificó la corrección funcional de la primera ronda (13/13 tests
de `services.snapshotter.tests.test_gold` + `test_export_replay`, guard
`0..100` correcto) y encontró tres incoherencias documentales/de gobernanza
nuevas, introducidas por la propia corrección de la primera ronda:

1. **Mismatch ADR-0003 vs. resto de la documentación:** revertir solo el
   texto de ADR-0003 (hallazgo #4 de la primera ronda) dejó una
   contradicción nueva: ADR-0003 (`Aceptado`) vuelve a decir "consumido vía
   DuckDB/dbt", pero `docs/ARCHITECTURE.md` (diagrama y sección DuckDB),
   `docs/PLAN.md` (F9), `analytics/dbt/README.md` y DEC-034 seguían
   afirmando que dbt-core/dbt-duckdb literal no forma parte del stack —
   `docs/ARCHITECTURE.md` incluso decía "decidido en MP-015", asentando una
   decisión de arquitectura sin el proceso de ADR. Corregido creando
   [ADR-0013](adr/0013-no-literal-dbt-engine.md) (`Propuesto`, conforme a
   ADR-0007): ADR-0003 permanece intacto; ADR-0013 documenta formalmente
   que MP-015 no introduce el motor dbt-core. Las cuatro referencias ahora
   apuntan a ADR-0013 en vez de asentar la decisión sin respaldo.
2. `docs/STATUS.md:166` decía "109/115 + 5 skip"; el resultado real es
   "110 en verde + 5 `skip`" (de 115) — corregido (ya constaba bien en
   `docs/CHANGELOG.md`).
3. El checklist de esta misma sección y `docs/CHANGELOG.md` seguían
   describiendo "6 ADRs corregidos" incluyendo ADR-0003 y sin mencionar
   drift en ADR-0005 — tras el revertido, el balance final es el inverso:
   ADR-0003 quedó intacto (no corregido) y ADR-0005 sí recibió una nota de
   drift real (tablas gold ya no vacías desde MP-015/DEC-033). Ambas
   descripciones actualizadas para reflejar el balance final.

Los tres se corrigieron en este mismo worktree, en esta ronda puramente
documental — sin cambios de código, por lo que no se repitió la suite
completa (conforme a la propia indicación de Codex); se verificó
`git diff --check` (sin problemas de espacio en blanco) y coherencia de
referencias cruzadas vía `rg` sobre DEC-034/ADR-0003/ADR-0013 en todo el
repositorio.

### Aprobación final de Codex

**APROBADA el `2026-11-20`.** Codex inspeccionó el diff completo de MP-015,
validó la justificación de `station_daily_metrics` contra
`packages/quality/engine.py`, revisó críticamente los ADRs y comparó
`docs/HITO_3_BACKLOG.md` con su versión original en
`chore/hito-2-coordination`. Ejecutó de forma independiente 114/114 tests
Python contra la base de desarrollo, 110 en verde + 5 `skip` (de 115)
contra un PostgreSQL fresco con migraciones desde cero, y frontend
lint/typecheck/5 tests/build; después de la primera corrección re-ejecutó
13/13 tests gold+replay, incluido el guard de porcentajes `0..100`. Los
contenedores temporales se eliminaron y la base de desarrollo conservó sus
recuentos.

La revisión encontró seis problemas reales en la primera ronda y tres
incoherencias de gobernanza/documentación en la segunda. Todos quedaron
corregidos en `267d072` y `9e5efe1`, respectivamente, y re-verificados. El
diff final pasa `git diff --check`; ADR-0013 queda correctamente
`Propuesto`, pendiente de la decisión exclusiva del propietario. No quedan
bloqueantes técnicos ni documentales para cerrar MP-015.

### Siguiente paso

MP-015 cierra funcionalmente la cadena del Hito 2. No se inicia Hito 3 sin
autorización explícita. El propietario decide ahora la auditoría de
integración final, la revisión/promoción de los ADRs `Propuesto` y el
momento de fusionar a `main`.


**MP-014 — Frontend React/MapLibre C5**

Ejecutor: OpenAI Codex · Revisor: Claude Code · Estado: **DONE**

Worktree/rama: `mp-014-frontend`, ramificada desde `mp-013-fastapi` (MP-013 `DONE`).

### Checklist de MP-014

- [x] `apps/web/`: React + TypeScript + MapLibre consumiendo `/api/v1/*` real (MP-013) — nunca Renfe/CRTM directamente, nunca mocks en la demo final.
- [x] **Gap de geometría resuelto (DEC-031):** `LineOut.geometry` nullable expone cada `Corridor.segments` por separado y las 23 estaciones proyectadas/ordenadas; no conecta paradas ni asigna el único corredor a otra línea. Test real contra GTFS/OSM y OpenAPI regenerado.
- [x] Los cuatro estados de posición (`observed`/`estimated`/`stale`/`scheduled`) tienen forma, color, opacidad y explicación textual diferentes (ADR-0004). Un ciclo real fresco los produjo simultáneamente: 24/2/4/1.
- [x] Campos `null` honestos: 114 de 145 vehículos reales quedaron sin ubicar tras el smoke; se contabilizan y listan explícitamente, sin ruta/posición inventada. `delay.coverage=missing` se explica como ausencia de dato.
- [x] **Gate visual aprobado (cuarta verificación):** Claude reconstruyó la build de producción y, en navegador real, cargó el preview en tres pestañas nuevas e independientes (carga en frío) — las tres mostraron el corredor y las 23 estaciones de inmediato, sin errores de consola, confirmando la corrección de la carrera de `load`. Dev reverificado sin regresión. Interacción comprobada: el toggle "Trazado" oculta/muestra el corredor correctamente sin afectar estaciones ni vehículos.
- [x] Arquitectura preparada para más líneas (ADR-0011): selector y estado derivados de `(network_id, line_id)` de la API; ningún literal de línea en componentes, hooks ni lógica compartida (la única coincidencia textual en `package-lock.json` pertenece a hashes de integridad).
- [x] Via Península/Valfiguer no se consumen ni se copia código/diseño; implementación independiente.
- [x] Smoke real de consumo API: PostgreSQL + GTFS oficial completo + `uvicorn` + Vite; `/lines` devolvió el corredor real y `/live/vehicles` los cuatro modos simultáneos. La carga visual del mapa permanece incluida en el gate anterior.
- [x] `docs/TASKS.md`/`docs/STATUS.md`/`docs/CHANGELOG.md`/`docs/DATA_CONTRACTS.md`/`docs/DECISIONS.md` actualizados con evidencia y límites reales.

### Resultado y límites

Implementación completa y en revisión: frontend estático genérico multi-línea,
contrato aditivo de geometría real y pruebas reproducibles. Comandos de la demo:

```sh
docker compose -p madrid-pulse -f infra/docker/docker-compose.yml up -d
.venv/bin/python -m apps.api.tools.fetch_gtfs_static
MADRID_PULSE_GTFS_SOURCE=data/gtfs_static/fomento_transit.zip .venv/bin/uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
cd apps/web && npm ci && npm run dev
```

Verificación ejecutada: regresión Python 102/102 (12 API + 90 previos);
frontend `npm run lint`, `npm run typecheck`, Vitest 5/5 y `npm run build`,
todo en verde. Smoke vivo tras un poll real:
145 vehículos, 31 map-matched (`observed` 24, `estimated` 2, `stale` 4,
`scheduled` 1). Esto confirma contrato/datos, no el gate visual pendiente.
Los runs `585–588` creados por el smoke y sus eventos derivados se retiraron
por ID/timestamp; PostgreSQL quedó restaurado a `668/484/3/120/0`.

Hallazgo fuera del cambio frontend: el feed fresco de `trip_updates` trajo un
`stopTimeUpdate` `SKIPPED` sin `arrival` y el contrato crudo del colector lo
rechazó. `vehicle_positions` sí se actualizó correctamente; la UI representa
salud/cobertura ausente sin inventar valores. Se deja para MP-015/colector.

Primera revisión visual de Claude: bloqueante reproducido en `npm run dev` —
`GET /node_modules/.vite/deps/maplibre-gl-worker.mjs` respondía `504`, por lo
que el worker no procesaba las fuentes GeoJSON. Corregido excluyendo MapLibre
del prebundle: el módulo ESM directo responde `200`. También se añadieron
`id`/`name`/`htmlFor` al selector, y Claude confirmó el flujo dev correcto en
su segunda pasada. Esa revisión detectó un fallo independiente de producción:
el worker no se emitía y la ruta devolvía el fallback HTML. Corregido con un
asset explícito y `setWorkerUrl` solo en producción. `npm run build` valida
ahora igualdad byte a byte; preview devolvió `text/javascript`, 550.754 bytes y
el mismo SHA-256 que dependencia/dist, mientras `/api/v1/lines` siguió sirviendo
1 segmento/23 estaciones. La tercera revisión visual de Claude confirmó el
worker, pero detectó una carrera de carga en frío. `MapView` ya no registra
listeners `once("load")` por cada línea: el handler inicial marca readiness y
aplica los últimos datos/capas; los cambios posteriores consultan ese estado.
Los errores de MapLibre se registran explícitamente. Frontend re-verificado:
lint, typecheck, 5/5 tests y build en verde. Cuarta revisión visual de Claude:
build de producción reconstruida, preview en tres pestañas nuevas e
independientes (carga en frío) — 3/3 mostraron el corredor/23 estaciones de
inmediato, sin errores de consola. Dev revalidado sin regresión; interacción
del toggle "Trazado" comprobada. MP-014 aprobada como `DONE` por el revisor.

### Bloqueos

Ninguno. Las cuatro rondas de revisión (geometría/arquitectura, worker de
Vite dev, worker de build de producción, carrera de carga en frío) quedaron
corregidas y verificadas con navegador real. MP-014 cerrada como `DONE`.

### Siguiente paso

Completado: MP-015 ya ramificó su worktree desde `mp-014-frontend` (ver "Tarea actual" arriba) sin esperar merge a `main`, conforme al hito autorizado y ADR-0007.

**MP-013 — FastAPI v1**

Ejecutor: Claude Code · Revisor: OpenAI Codex · Estado: **DONE**

Worktree/rama: `mp-013-fastapi`, ramificada desde `mp-012-movement-engine` (MP-012 `DONE`). MP-005/MP-007 (sus otras dependencias) ya ancestros de `main`, confirmado con `git merge-base --is-ancestor origin/main HEAD`.

### Checklist de MP-013

- [x] `apps/api/`: FastAPI real (`fastapi==0.121.2`, `uvicorn[standard]==0.38.0`, `httpx==0.28.1` para tests — DEC-030), sin reimplementar resolución GTFS/geometría/movimiento.
- [x] **Hallazgo real:** `route`/`station`/`trip`/`trip_stop` siguen vacías en PostgreSQL y `vehicle_position_observation.trip_id` sigue `NULL` en los 668 registros reales — confirmado por consulta directa. La API resuelve `trip_id`→`route_id`/`stop_id` vía `packages.gtfs.Topology` en memoria, nunca por `JOIN` SQL a esas tablas.
- [x] 7 endpoints reales: `health`, `live/vehicles`(`/{vehicle_id}`), `lines`(`/{line_id}`), `stations`(`/{station_id}`); `history`/`metrics` diferidos explícitamente (DEC-027, `docs/DATA_CONTRACTS.md`).
- [x] `/api/v1/health` calcula `data_age_s`/`unchanged_for_s`/`status` reales desde `source_ingestion_run`, nunca fabricados.
- [x] `/api/v1/live/vehicles` combina la última/penúltima observación real por vehículo con `MovementEngine.position()` (MP-012); nunca fabrica `route_id`/`line`/`position` cuando el `trip_id` no resuelve — devuelve `null` honesto.
- [x] **Hallazgo real (DEC-029):** de los 24 vehículos distintos del soak real de MP-007, solo 4 son C5 (`10T0017C5`/`10T0018C5`); 19 son otras líneas del núcleo (C1, C2, C3, C4, C4a, C4b, C8a, C8b, C10) y 1 (`SPECIAL_10_91567C2`) no resuelve, confirmado contra el GTFS estático completo — confirma empíricamente DEC-020.
- [x] **Corregido tras la revisión de Codex (hallazgo documental):** el primer recuento listaba solo 5 líneas (C1/C3/C4a/C4b/C8b) y omitía C2/C4/C8a/C10 y el trip `SPECIAL_` sin resolver — recruzados los 24 pares reales contra `trips.txt` del ZIP completo para la cifra definitiva.
- [x] **Hallazgo real (DEC-028):** un único corredor OSM (`relation_3418150`) basta para ambos sentidos reales de C5: `build_trip_schedule` detecta el sentido de cada trip comparando el orden de sus paradas contra el corredor.
- [x] OpenAPI generado y congelado en `apps/api/openapi.json`.
- [x] `apps/api/tools/fetch_gtfs_static.py`: descarga el GTFS completo real para que `/api/v1/live/vehicles` resuelva vehículos C5 en ejecución local (la fixture reducida de MP-010 solo tiene 15 trips representativos, insuficiente para el feed en vivo).
- [x] App arrancada de verdad con `uvicorn` y probada con `curl` real (`/api/v1/lines`, `/docs`), no solo `TestClient`.
- [x] 9 tests de contrato nuevos (fixture reducida + PostgreSQL real + un caso sintético de extremo a extremo con un trip real) + regresión completa: **99/99 en verde**.
- [x] `docs/TASKS.md`/`docs/STATUS.md`/`docs/CHANGELOG.md`/`docs/DATA_CONTRACTS.md`/ADR-0005/DECISIONES actualizados con evidencia real.

### Resultado y límites

API real conforme a `docs/DATA_CONTRACTS.md` para los endpoints `live`/`lines`/`stations`/`health`; `history`/`metrics` diferidos explícitamente (DEC-027) porque los agregados diarios siguen sin poblarse desde MP-009. Sin literales de línea en la lógica (ADR-0011): `network_id`/`short_name` son configuración.

Ejecución final real (`.venv`, Python 3.12): 101/101 tests — API 11, movement 11, GTFS 7, geo 8, contratos 31, fixtures 6, collector 9, quality 13, snapshotter 5. Suites con PostgreSQL ejecutadas con el contenedor `madrid-pulse` levantado por el ejecutor; recuentos finales `668/484/3/120/0` sin residuo.

**Revisión independiente de OpenAI Codex (`2026-11-19`): NO APROBADA en primera ronda.** Reprodujo de forma propia: PostgreSQL `route`/`station`/`trip`=0 y `trip_id` resuelto=0; volumen `668/484/3/120/0` antes/después; GTFS oficial descargado y verificado (15.717.009 bytes); DEC-028 confirmado en los 4 trips C5 reales; 9 API + 90 regresión en verde; servidor `uvicorn` real arrancado y probado con `curl` (`health`/`live/vehicles`/`docs` → `200`). Hallazgos:

- **Bloqueante 1:** `apps/api/service.py` solo calculaba `observation.age_s` cuando el motor de movimiento resolvía una posición — para los 20/24 vehículos reales que no son C5, `reported_at` era real pero `age_s` quedaba `null` aunque es calculable directamente desde el timestamp crudo.
- **Bloqueante 2:** `_movement_position` pasaba `service_date=now.astimezone(timezone.utc).date()`, pero `packages.movement.schedule.service_seconds` interpreta esa fecha como calendario Europe/Madrid (`docs/DATA_MODEL.md`). Cerca de medianoche (p. ej. `2026-11-19T23:30Z` = `2026-11-20 00:30` CET) ambas fechas difieren en un día real, desplazando el horario esperado.
- **Menor documental:** DEC-029 listaba solo 5 líneas no-C5 (C1/C3/C4a/C4b/C8b) y omitía C2/C4/C8a/C10 y un trip de refuerzo (`SPECIAL_10_91567C2`) que no resuelve contra ningún `route_id` — el cruce completo de Codex contra `trips.txt` dio la cifra real.

**Corrección de Claude Code (`2026-11-19`), lista para re-verificación:**

- **Bloqueante 1 corregido:** `age_s` ahora se calcula siempre como `(now - observation.reported_at)`, independiente de si la ruta/posición resuelve. Verificado revirtiendo el fix: el nuevo test (`test_live_vehicles_always_report_raw_observation_age`) falla con `age_s` `None` contra el código anterior y pasa con el fix restaurado.
- **Bloqueante 2 corregido:** `service_date` se calcula ahora con conversión explícita a Europe/Madrid (`now.astimezone(ZoneInfo("Europe/Madrid")).date()`), no la fecha UTC. Verificado revirtiendo el fix: el nuevo test (`test_service_date_uses_europe_madrid_calendar_not_utc`, cubre borde de invierno CET y verano CEST) falla con `AttributeError` contra el código anterior y pasa con el fix restaurado.
- **Menor corregido:** recruzados los 24 pares reales `(source_vehicle_id, source_trip_id)` contra `trips.txt` del GTFS completo. Cifra definitiva: 4 C5, 19 de otras 9 líneas (C1, C2, C3, C4, C4a, C4b, C8a, C8b, C10), 1 (`SPECIAL_10_91567C2`) sin resolver. DEC-029, `apps/api/README.md`, `docs/CHANGELOG.md` y este documento corregidos.

101/101 tests en verde (99 + 2 de regresión nuevos). La segunda verificación de Codex confirmó funcionalmente ambos bloqueantes y el cruce GTFS completo; quedó únicamente un docstring residual con la lista anterior de 5 líneas.

**Revisión final independiente de OpenAI Codex (`2026-11-19`): APROBADA, sin hallazgos abiertos.** El commit `15170c4` corrige exclusivamente ese docstring: ahora registra 19 vehículos de C1/C2/C3/C4/C4a/C4b/C8a/C8b/C10 más 1 trip de refuerzo sin resolver. `git diff --check c82e62f..15170c4` está limpio y el diff contiene solo 4 inserciones/3 borrados en `apps/api/tests/test_api_contract.py`. La suite contractual aislada se reejecutó contra PostgreSQL real: 11/11 `OK`, con recuentos finales `668/484/3/120/0`; el contenedor se bajó sin borrar el volumen. Autor y committer de `15170c4`: `Pedro Matute <pedromaaz13@gmail.com>`, sin coautor. MP-013 pasa a `DONE`.

### Bloqueos

Ninguno.

### Siguiente paso

MP-014 (Frontend React/MapLibre, ejecutor Codex) ramificó su worktree desde `mp-013-fastapi` sin esperar merge a `main`, conforme al hito autorizado y ADR-0007 — registrado arriba en "Tarea actual".

**MP-012 — Motor de movimiento v1**

Ejecutor: OpenAI Codex · Revisor: Claude Code · Estado: **DONE** (aprobado el 2026-11-19)

Worktree/rama: `mp-012-movement-engine`, ramificada desde `mp-011-osm-geometry` (MP-011 `DONE`). DEC-015 resuelto: `git merge-base --is-ancestor origin/main HEAD` confirmado `true` desde `mp-011-osm-geometry` — MP-008 (ancestro de `main`), MP-010 y MP-011 quedan todos satisfechos sin fusión real (ver `AGENTS.md`).

### Checklist de MP-012

- [x] Motor de movimiento con los cuatro estados `OBSERVED` (0–60s) / `ESTIMATED` (>60–180s) / `STALE` (>180s) / `SCHEDULED` (sin observación plausible), conforme a ADR-0004; defaults parametrizados en `MovementThresholds`.
- [x] Pipeline de ADR-0004 completo: resolución GTFS → `Corridor.project_station` → progreso acumulado → perfil de `stop_times` → offset temporal → interpolación → límites de aceleración/velocidad/retroceso; una muestra imposible no borra la anterior plausible.
- [x] `MovementPosition` expone `position_mode`, `confidence` decreciente, `age_s`, `source`, timestamps, progreso y anomalías; fuentes distintas impiden confundir estimado/stale/scheduled con observado.
- [x] Calibración real: `60s/180s` mantenidos porque la cadencia ~20–22s equivale a ~3/~8 polls perdidos. Separados `max_estimated_speed_kmh=160` (trayectoria fabricada) y `unusable_jump_speed_kmh=900` (discontinuidad del feed): MP-008 midió 246–787 km/h crudos y MP-012 666,4 km/h map-matched en el volumen real.
- [x] Tests deterministas: cuatro transiciones, confianza/fuente, offset horario, velocidad/aceleración, salto de estación, retroceso, off-track, salto imposible, rango empírico 700 km/h aceptado, UTC y cambio de día/horas GTFS >24.
- [x] Validación real PostgreSQL de solo lectura: 668 observaciones antes y después, 177 a ≤200 m del corredor, máximo salto map-matched 666,4 km/h; volumen completo `668/484/3/120/0` intacto tras toda la regresión.
- [x] Ubicación decidida en ADR-0012 (`Propuesto`): `packages/movement` orquesta las capas existentes sin contaminar `geo` con horarios ni `quality` con generación de posiciones.
- [x] `off_track`/`backward_jump`/`station_skip_anomaly` calculados y expuestos. Persistencia diferida explícitamente: el `CHECK`/modelo v1 de `data_quality_event` pertenece a observaciones crudas y MP-012 no crea una tabla de derivados; cualquier persistencia futura requiere migración con dueño/clave claros.
- [x] `docs/TASKS.md`/`docs/STATUS.md`/`docs/CHANGELOG.md`/`docs/DATA_QUALITY.md`/ADR-0004/ADR-0012/DEC-026 actualizados con evidencia real.

### Resultado y límites

Motor genérico implementado en `packages/movement/`, sin literal de la línea piloto en la lógica. `point_at_arc_length` completa la API geométrica genérica como inversa de `arc_length_to`. El motor exige un corredor continuo por trip y rechaza explícitamente geometrías con huecos en vez de fabricar distancia. La topología huérfana sin `stop_times` sigue produciendo error explícito, no un recorrido inventado.

Ejecución final real (`.venv`, Python 3.12): 90/90 tests en verde — movement 11, GTFS 7, geo 8, contratos 31, fixtures 6, collector 9, quality 13, snapshotter 5. Las suites con PostgreSQL se ejecutaron con el contenedor `madrid-pulse` levantado por el ejecutor; recuentos finales `668/484/3/120/0`. `compileall` y `git diff --check` sin errores.

- [x] **Revisión independiente de Claude Code (2026-11-19): APROBADA.** `packages/movement/model.py`, `schedule.py`, `engine.py` leídos íntegros. 90/90 tests reejecutados de forma propia (10 deterministas movement + 1 integración real + 79 de regresión GTFS/geo/contratos/fixtures/collector/quality/snapshotter), subiendo y bajando el contenedor `madrid-pulse` yo mismo; integración de solo lectura reproducida con los mismos resultados exactos (668→668 posiciones, 177 a ≤200 m del corredor, máximo map-matched `666,4 km/h`). Verificado matemáticamente: `directed_progress`/`physical_arc` correctos en ambos sentidos del corredor; la estimación nunca retrocede y queda acotada por velocidad (160 km/h) y aceleración (1,2 m/s²); el fallback a la última observación plausible reaplica la clasificación de estado completa por recursión en vez de forzar `OBSERVED` de forma artificial; la separación entre límite físico (160 km/h) y filtro de discontinuidad de fuente (900 km/h) es coherente con los hallazgos reales de MP-008/MP-012. Confirmado por lectura directa que `engine.py`/`model.py`/`schedule.py` no contienen el literal `"C5"`. Identidad Git de `1edfa14` correcta (`Pedro Matute <pedromaaz13@gmail.com>`, sin coautor), `git diff --check` limpio, sin secretos. Evalué si esta revisión requería escalar a Opus (candidato explícito del propietario para revisiones algorítmicas complejas) y no fue necesario: todas las decisiones de diseño se pudieron verificar directamente con razonamiento estándar. Sin hallazgos bloqueantes ni menores.

### Bloqueos

Ninguno. ADR-0012 permanece `Propuesto` hasta revisión formal del propietario al cierre de Hito 2.

### Siguiente paso

MP-012 está `DONE`. MP-013 (FastAPI v1, ejecutor Claude Code, revisor Codex) ramificó su worktree desde `mp-012-movement-engine` sin esperar merge a `main`, conforme al hito autorizado y ADR-0007 — registrado arriba en "Tarea actual".

**MP-011 — Prototipo de geometría ferroviaria sobre OSM**

Ejecutor: Claude Code · Revisor: OpenAI Codex · Estado: **DONE**

Worktree/rama: `mp-011-osm-geometry`, ramificada desde `mp-010-gtfs-topology` (MP-010 `DONE`).

### Checklist de MP-011

- [x] `packages/geo/overpass.py`: cliente Overpass API genérico (relación por id o por `ref`/`network`), sin literales de línea en la lógica; solo `urllib` de la librería estándar.
- [x] `packages/geo/corridor.py`: encadena los `ways` de vía (`role=""`) de una relación OSM en el orden declarado, uniendo por nodo extremo compartido; un hueco real se registra como `ChainGap`, nunca se fabrica una unión inexistente.
- [x] `packages/geo/geometry.py`: Haversine real + proyección punto-polilínea (plano local equirrectangular por consulta), sin `shapely`/`pyproj`.
- [x] Descarga real de las 4 relaciones direccionales OSM de C5 Madrid (`11331`/`3418148`/`3418149`/`3418150`, `ref=C-5`/`network=Cercanías Madrid`, agrupadas por el `route_master` `3418151`): las 4 encadenan sus `ways` de vía sin huecos.
- [x] Las 23 estaciones reales de la ruta larga (ambos sentidos, GTFS `10T0017C5`/`10T0018C5`) proyectan en orden monótono sobre su corredor correspondiente, distancia máxima real 63,7 m.
- [x] **Hallazgo:** la ruta corta (`10T0047C5`/`48C5`) no tiene relación OSM propia — su patrón base de 6 estaciones es una subsecuencia contigua literal de la ruta larga; la variante de 7 estaciones con Atocha solo es monótona y no contigua. No se fabrica geometría separada.
- [x] **Hallazgo:** las relaciones `3418148`/`3418149` ("Fuenlabrada→Atocha→Móstoles-El Soto") son la ruta larga truncada en Fuenlabrada, no coinciden con el patrón real de 6 estaciones de la ruta corta — documentado como variante real no usada (DEC-025).
- [x] **Hallazgo:** `usage=main` (30 `ways`)/`usage=branch` (60 `ways`) en la vía — trazado troncal potencialmente compartido vs. ramal específico de C5; no verificado qué otras líneas comparten el tramo (DEC-025).
- [x] "C5"/"C-5" colisiona también en OSM entre núcleos (Asturias, Sevilla, Cantabria, Valencia, Madrid) — mismo patrón que ADR-0008/DEC-017 ya documentó para el GTFS de Renfe.
- [x] Fixture real congelada y atribuida (`tests/fixtures/osm_c5_real/`): 4 relaciones, checksums y proceso en `MANIFEST.md`; licencia ODbL de la base de datos derivada confirmada (DEC-024).
- [x] Evidencia visual real: `packages/geo/tools/render_preview.py` genera un SVG del corredor + estaciones; renderizado y revisado en navegador (Chrome DevTools MCP, captura completa) — forma real de la C5 reconocible, estaciones sin saltos sobre la vía.
- [x] 79/79 tests en verde: 8 geo nuevos + 71 de regresión (7 GTFS + 31 contratos + 6 fixtures GTFS-RT + 9 colector + 13 calidad + 5 snapshotter), incluidas 9 integraciones reales contra PostgreSQL.
- [x] `docs/TASKS.md`/`docs/STATUS.md`/`docs/CHANGELOG.md`/`docs/DECISIONS.md`/`docs/legal/ATTRIBUTION.md`/`docs/legal/DATA_SOURCES.md` actualizados con evidencia real antes de delegar a revisión.

### Resultado y límites

Geometría real de la C5 Madrid derivada de 4 relaciones OSM reales, validada contra las 23 estaciones reales del GTFS con distancia máxima 63,7 m y orden monótono. La API (`Corridor.project_station`, `build_corridor`) queda disponible para MP-012/MP-013 sobre cualquier relación configurada, sin literales de línea en la lógica. Limitaciones documentadas, no ocultas: `10T0035C5` sigue sin validar (huérfano desde MP-010), el reparto exacto de trazado troncal compartido con otras líneas no se verificó, y la correspondencia OSM↔GTFS para la ruta corta se resuelve por subsegmento del corredor largo, no por una relación OSM dedicada (no existe una).

### Bloqueos

**Revisión independiente de OpenAI Codex (`2026-11-19`): NO APROBADA en primera ronda.** Hallazgos devueltos al ejecutor en este mismo worktree:

- **Bloqueante — `ChainGap` se registra pero la geometría aún fabrica la unión.** Con dos `ways` sintéticos desconectados, `build_corridor` produce correctamente un `ChainGap`, pero concatena ambos en una única `polyline`; `project_station` y `corridor_length_m` interpretan entonces el par de extremos alrededor del hueco como un segmento real. Reproducción independiente: una consulta situada en el centro del hueco proyectó con `distance_m=0.0`. Debe representarse/ignorarse explícitamente la discontinuidad en los cálculos y añadirse una prueba que falle con el comportamiento actual.
- **Menor — evidencia y documentación cuentan mal la suite y la ruta corta.** `python3 -m unittest packages.geo.tests.test_real_feed -v` ejecuta 6 tests, no 7; el total real es 77 (6 geo + 71 regresión), no 78. La fixture GTFS contiene 7 estaciones para `10T0047C5`, no 6. Las 7 sí proyectan monótonamente sobre el mismo corredor de `10T0017C5` (máximo independiente: 37,3 m), pero no son una subsecuencia contigua de paradas de la ruta larga: omiten cuatro paradas intermedias. Debe reservarse “subsegmento contiguo” para la geometría de vía y corregirse el recuento en `docs/TASKS.md`, `docs/STATUS.md`, `docs/CHANGELOG.md`, `docs/DECISIONS.md`, `packages/geo/README.md`, fixture/manifiesto y comentarios/tests afectados.
- **Menor — checksums anunciados pero ausentes.** `packages/geo/README.md` afirma que el manifiesto contiene checksums, pero `tests/fixtures/osm_c5_real/MANIFEST.md` no lista ninguno. Añadir los cuatro SHA-256 o retirar la afirmación; la opción preferible es añadirlos para preservar trazabilidad.

Evidencia ya reproducida por el revisor: 6 geo + 7 GTFS + 31 contratos + 6 fixtures + 9 colector + 13 calidad + 5 snapshotter, todos en verde; PostgreSQL `668/484/3/120/0` antes y después; render documentado generado como HTML/SVG real; identidad Git de `fbc3fde` correcta y `git diff --check` limpio. Pendiente corrección y re-verificación antes de aprobar.

**Corrección de Claude Code (`2026-11-19`), lista para re-verificación de Codex:**

- **Bloqueante corregido:** `Corridor` ahora tiene `segments` (tramos realmente continuos, separados en cada `ChainGap`); `project_station`/`corridor_length_m` solo operan dentro de un tramo, nunca interpolando a través de un hueco. Verificado revirtiendo el fix: el nuevo test de regresión (`test_gap_between_disconnected_ways_is_not_fabricated_as_track`, dos `ways` sintéticos desconectados) falla con `AttributeError: 'Corridor' object has no attribute 'segments'` contra el código anterior, y pasa con el fix restaurado. `render_preview.py` corregido en paralelo: dibuja un `<polyline>` por tramo, no uno solo que uniría visualmente un hueco real.
- **Menor corregido (recuento):** 8 tests geo (no 7), 79 totales (no 78) — contado de nuevo con un venv fresco (`python3 -m venv` + `pip install -r requirements.txt`), subiendo/bajando el contenedor yo mismo y confirmando `668/484/3/120/0` antes y después.
- **Menor corregido (sobre-reclamo "subsegmento contiguo"):** separado en dos tests y dos afirmaciones distintas. La variante base de 6 estaciones de `10T0047C5` (sin Atocha) SÍ es una subsecuencia contigua real (verificado por comparación literal de IDs: aparece en el índice 16 del patrón largo de 23 estaciones). La variante real de 7 estaciones (con Atocha antepuesta) proyecta en orden monótono sobre el mismo corredor pero NO es contigua — omite 4 paradas intermedias reales (Méndez Álvaro, Doce de Octubre, Orcasitas, Puente Alcocer). `packages/geo/README.md`, `docs/TASKS.md` y este documento corregidos para no confundir ambas afirmaciones.
- **Menor corregido (checksums):** 4 SHA-256 añadidos a `tests/fixtures/osm_c5_real/MANIFEST.md`, recalculados y verificados contra los ficheros reales (`hashlib.sha256` sobre cada JSON, comparación exacta con el valor documentado).

Commit de corrección `f795036`. Reenviado a Codex para segunda verificación en este mismo worktree.

**Segunda verificación independiente de OpenAI Codex (`2026-11-19`): APROBADA.** El revisor leyó íntegramente `packages/geo/corridor.py` y repitió una reproducción sintética propia: dos `ways` desconectados producen 2 `segments`; un punto en el centro del hueco proyecta a `2223,9 m` del tramo real más próximo (no ~0), y `corridor_length_m=2223,9 m` suma únicamente los dos tramos, sin el hueco. El test bloqueante dirigido pasó 1/1 y `packages.geo.tests.test_real_feed` pasó 8/8.

Regresión propia: 71/71 en verde (7 GTFS + 31 contratos + 6 fixtures GTFS-RT + 9 colector + 13 calidad + 5 snapshotter), con las integraciones reales ejecutadas contra PostgreSQL sin `skip`; recuentos persistentes `668/484/3/120/0` idénticos antes y después. El contenedor se levantó con `--wait` y se bajó sin `-v`, conservando el volumen. La comparación literal independiente sitúa el patrón base de 6 estaciones en el índice 16 del patrón largo de 23; la variante de 7 con Atocha ocupa las posiciones `11,16,17,18,19,20,21`, por lo que no es contigua y omite cuatro estaciones. Los cuatro SHA-256 recalculados coinciden exactamente con `MANIFEST.md`; `git diff --check fbc3fde..f795036` está limpio e identidad de autor/committer de `f795036` es `Pedro Matute <pedromaaz13@gmail.com>`, sin coautor. Sin hallazgos bloqueantes ni menores abiertos; MP-011 pasa a `DONE`.

### Siguiente paso

MP-011 está `DONE`. DEC-015 resuelto y aplicado: MP-012 (ejecutor Codex, revisor Claude Code) ramificó directamente desde `mp-011-osm-geometry` sin fusión real — registrado arriba en "Tarea actual".

**MP-010 — Topología GTFS C5**

Ejecutor: OpenAI Codex · Revisor: Claude Code · Estado: **DONE** (aprobado el 2026-11-19)

Worktree/rama: `mp-010-gtfs-topology`, ramificada desde `chore/hito-2-coordination` (que a su vez parte de `main`, post-merge de Hito 1 — MP-004, su única dependencia directa, ya es ancestro de `main`).

### Checklist de MP-010

- [x] `packages/gtfs/`: parser en streaming de topología GTFS estático (`routes`/`trips`/`stops`/`stop_times`/`shapes`/`calendar`) desde ZIP o directorio, con comprobación de esquema y sin campos inventados.
- [x] Las 5 variantes `source_route_id` de C5 Madrid (`10T0017C5`, `10T0018C5`, `10T0035C5`, `10T0047C5`, `10T0048C5`) permanecen como rutas distintas y se agrupan por `(network_id, short_name)`.
- [x] Resolución genérica de `route_id`/`trip_id`/`stop_id`: filtros parametrizados, JOIN literal de trip estático, fallback solo para `routeId` explícito de trips `ADDED`, rechazo de contradicciones y prueba que impide literales de línea en la lógica.
- [x] Validación real de recorrido: 14 patrones ordenados, incluidos pares inversos completos y cortos. **Hallazgo:** el GTFS de Renfe no contiene `direction_id`; la dirección verificable es `stop_sequence` + `shape_id`, y no se fabrica una columna ausente.
- [x] **Hallazgo real:** `10T0035C5` tiene 8 trips y cero `stop_times` en el ZIP completo. El validador los informa como huérfanos de fuente y no inventa recorrido.
- [x] Fixture real reducida, reproducible y atribuida (`tests/fixtures/gtfs_c5_real/`): 5 rutas, 15 trips representativos, 23 estaciones, 168 stop_times, 630 puntos de shape y 4 servicios; URL/checksums/proceso en su `MANIFEST.md` (DEC-023).
- [x] 71/71 tests en verde: 7 GTFS nuevos + 64 regresiones (31 contratos, 6 fixtures GTFS-RT, 9 colector, 13 calidad, 5 snapshotter), incluidas 9 integraciones reales contra PostgreSQL. Ejecución adicional contra el ZIP oficial completo: 5 rutas, 8.160 trips, 23 estaciones, 165.205 stop_times, 630 puntos, 30 servicios, 14 patrones, 8 huérfanos, 0 errores de validación.
- [x] `docs/TASKS.md`/`docs/STATUS.md`/`docs/CHANGELOG.md` actualizados con evidencia real antes de delegar a revisión.

### Resultado y límites

Topología C5 parseada y validada contra la descarga oficial del `2026-11-19`. La API queda disponible para MP-012/MP-013 mediante `Topology.resolve_trip_route_id`, `resolve_trip_route` y `resolve_stop_sequences`; opera sobre cualquier línea configurada. El fichero completo no se versiona: son ~15,7 MB comprimidos/~298 MB extraídos y cambia con upstream; se conserva una fixture real mínima reproducible con checksum (DEC-023).

- [x] **Revisión independiente de Claude Code (2026-11-19): APROBADA.** Código íntegro de `packages/gtfs/` leído (parser, topology, tests, tool de reducción). 71/71 tests reejecutados de forma propia: 7 GTFS + 31 contratos + 6 fixtures GTFS-RT + 9 colector + 13 calidad + 5 snapshotter — subiendo y bajando el contenedor `madrid-pulse` yo mismo (no reutilizando solo el reporte de Codex) y confirmando los recuentos reales `668/484/3/120/0` idénticos antes y después, sin residuo. Confirmado con lectura directa que `parser.py`/`topology.py` no contienen el literal `"C5"` y que la resolución es genérica por `route_ids`/`network_id`/`short_name` (ADR-0011) — reforzado por un test de regresión que falla si se reintroduce el literal. `git diff --check` limpio, sin secretos en el diff, identidad Git (`Pedro Matute <pedromaaz13@gmail.com>`, sin coautor) y enlaces a ADR-0011/DEC-022/DEC-023 verificados. Fixture reducida (52 KB) con checksum, atribución `CC BY 4.0` y proceso reproducible documentado en su `MANIFEST.md`. Sin hallazgos bloqueantes ni menores.

### Bloqueos

Ninguno. Los 8 trips huérfanos y la ausencia de `direction_id` son propiedades verificadas del upstream, preservadas explícitamente y confirmadas de forma independiente, no defectos ocultos ni datos suplidos.

### Siguiente paso

MP-010 está `DONE`. MP-011 (Prototipo de geometría ferroviaria sobre OSM, ejecutor Claude Code, revisor Codex) ramificó su worktree desde `mp-010-gtfs-topology` sin esperar merge a `main`, conforme al hito autorizado y ADR-0007 — registrado arriba en "Tarea actual".

**MP-009 — Exportador histórico (Parquet particionado)**

Ejecutor: Claude Code · Revisor: OpenAI Codex · Estado: **DONE** (aprobado el 2026-11-19)

Worktree/rama: `mp-009-historical-export`, ramificada desde `mp-008-quality-engine` (MP-008 `DONE`)

### Checklist de MP-009

- [x] `services/snapshotter/export.py`: DuckDB como único motor (lee PostgreSQL vía `ATTACH ... TYPE POSTGRES`, escribe Parquet nativo); sin `pandas`/`pyarrow` adicionales (DEC-021).
- [x] Partición `date=YYYY-MM-DD/hour=HH` siempre calculada sobre Europe/Madrid, nunca UTC directo — ver hallazgo real abajo.
- [x] **Hallazgo real:** los datos del soak test de MP-007 (`23:31:42 UTC` 18-nov) pertenecen al día de servicio **19-nov** en Europe/Madrid (CET, UTC+1) — exactamente el error que `docs/DATA_MODEL.md` ya advertía. 3 tests de regresión puros (incluido CEST/verano) en `test_export.py`.
- [x] Test de replay real (`test_export_replay.py`): día de prueba conocido, COMPROMETIDO (no `rollback()`, DuckDB usa conexión `libpq` propia), exportado y verificado sin pérdida; limpieza explícita en `finally`.
- [x] Exportación real completa del día `2026-11-19` (datos reales, no fixtures): 1272 filas (668+484+120+0+0), ~76 KB ZSTD particionado; releído con consulta DuckDB independiente, recuento exacto.
- [x] `services/snapshotter/gold.py`: resumen diario por núcleo (1 fila para Madrid: 668 posiciones/24 vehículos, 484 actualizaciones/24 viajes). **Limitación deliberada documentada:** no calcula `daily_line_metrics`/`station_daily_metrics` (requieren resolución `route_id`/`station_id` diferida a MP-010, ADR-0009) — ver DEC-021.
- [x] CLI (`python -m services.snapshotter YYYY-MM-DD`) probado de punta a punta contra PostgreSQL real.
- [x] 64 tests reales en verde: 31 contratos + 6 fixtures + 9 colector + 13 calidad + 5 snapshotter.
- [x] Identidad Git verificada; contenedor `madrid-pulse` detenido al finalizar la implementación (volumen real conservado); `*-traza-app` intactos.
- [x] **Primera revisión independiente de Codex (dispatch `ctx_d2b95955a73a`): no aprobada** — reejecutó las 64 pruebas, confirmó la conversión Europe/Madrid y el export/gold reales, y encontró un bloqueante real: las 3 `service_alert` reales (ingeridas el 19-nov vía `ingestion_run` 78) desaparecían del export de ese día porque `export.py` particionaba `service_alert` por `active_period_start` (ventana de vigencia del aviso) en vez de por cuándo se observó — esa tabla no tiene columna propia de observación.
- [x] Corregido uniendo `service_alert` a `source_ingestion_run` y usando `started_at` de esa ejecución; verificado revirtiendo el fix (el test ampliado falla `0 != 1` exactamente como reportó Codex) y restaurándolo (pasa). Reexportado el día real: `service_alert` pasa de 0 a 3 filas. Test de replay ampliado para cubrir las 5 tablas (antes solo 2).
- [x] **Segunda revisión independiente de Codex (dispatch `ctx_095ae1499806`): APROBADA** — 2/2 tests de replay ampliados en verde contra PostgreSQL real; limpieza de las 5 tablas confirmada (`vp/tu/alert/dqe/run = 0` tras el test). Export real independiente: 668/484/**3**/120/0; los tres avisos esperados aparecen en Parquet ligados al run 78. Diff, identidad Git y aislamiento de contenedores correctos.

### Resultado y límites

El exportador mueve de verdad datos reales de PostgreSQL a Parquet particionado sin pérdida, con dos trampas reales encontradas y corregidas con evidencia, no solo teóricas: el huso horario Europe/Madrid vs. UTC, y la semántica temporal de `service_alert` (vigencia vs. observación). El agregado gold queda deliberadamente acotado a núcleo (no a línea/estación) hasta que MP-010 resuelva las FK necesarias — documentado, no improvisado.

### Bloqueos

Ninguno: el bloqueante real de la primera revisión de Codex (semántica temporal de `service_alert`) está corregido y re-verificado independientemente; la limitación de alcance del agregado gold está documentada y no bloquea el criterio de aceptación real (replay sin pérdida de la capa raw).

### Siguiente paso

MP-009 y el Hito 1 (`MP-002` → `MP-009`) están completos. El worktree queda listo para revisión del propietario; no se inicia MP-010 ni otro hito hasta que el propietario lo autorice expresamente. **Nota añadida al preparar Hito 2 (`2026-11-19`):** el propietario autorizó y fusionó Hito 1 a `main`; MP-010 arrancó en su propio worktree, registrado arriba en "Tarea actual".

**MP-008 — Quality engine**

Ejecutor: OpenAI Codex · Revisor: Claude Code · Estado: **DONE** (aprobado el 2026-11-19)

Worktree/rama: `mp-008-quality-engine`, ramificada desde `mp-007-collector` (MP-007 `DONE`)

### Checklist de MP-008

- [x] Cinco flags del `CHECK` de MP-006 implementados: `stale`, `implausible_speed`, `missing_id`, `duplicate_snapshot`, `clock_anomaly`.
- [x] Reglas puras en `packages/quality/engine.py`, separadas de red/BD; capa PostgreSQL en `packages/quality/db.py`.
- [x] Umbrales calibrables y nombrados: stale 180s, velocidad 200km/h, feed congelado 180s, drift de reloj 300s; documentados como puntos de partida, no contrato de Renfe.
- [x] Velocidad implícita calculada por Haversine entre posiciones consecutivas del mismo vehículo, sin usar `speed_kmh` de origen.
- [x] `duplicate_snapshot` opera sobre el hash completo del feed sostenido en el tiempo; dos polls normales iguales no disparan la regla.
- [x] Eventos y `quality_flags` persistidos dentro de la misma transacción atómica del colector; flags de feed no se atribuyen falsamente a una observación.
- [x] 13 tests de calidad: al menos disparo + falso positivo por cada regla, rollover UTC de medianoche y dos integraciones PostgreSQL reales con rollback.
- [x] Suite completa ejecutada: **59/59** (31 contratos + 6 fixtures + 9 colector + 13 calidad), todas `OK`.
- [x] Casos anómalos ausentes de las fixtures reales marcados explícitamente como sintéticos; no se presentan como observados.
- [x] Contenedor `madrid-pulse-postgres-1` dejado levantado para la revisión, volumen real conservado; contenedores `*-traza-app` verificados intactos.
- [x] **Revisión independiente de Claude Code (2026-11-19): APROBADA.** Reproducidas
  59/59 pruebas contra el mismo PostgreSQL real (668/484/3/120 registros del
  soak test de MP-007, intactos). Revisado el diseño (reglas puras vs.
  persistencia, transacción atómica, reutilización del patrón `id DESC` de
  MP-007 en el historial de calidad).
  **Hallazgo empírico documentado, no bloqueante:** al repetir 117 pares
  reales de posiciones consecutivas del soak test contra
  `check_implausible_speed`, 12/117 (~10%) dispararon con velocidades
  implícitas de 246–787 km/h. Inspección de la secuencia del vehículo
  `21053` confirmó que son saltos reales entre filas ya almacenadas (20-40s,
  varios km), no un error de cálculo — indica que Renfe actualiza posición
  en saltos más gruesos que el cadencia de poll, no como GPS continuo.
  Registrado para considerarlo al calibrar el umbral en MP-012 (ya
  documentado como "a calibrar, no verdad de diseño").

### Resultado y límites

El motor queda integrado antes de persistir para aprovechar los objetos canónicos de MP-005 y conservar atomicidad con MP-007, sin duplicar el colector. Las reglas geométricas `off_track`, `backward_jump` y `station_skip_anomaly` siguen diferidas a MP-012: requieren map-matching y no caben en el `CHECK` actual.

### Bloqueos

Ninguno. Los umbrales requieren calibración operativa futura (ver hallazgo de `implausible_speed` arriba), tal como exige `docs/DATA_QUALITY.md`, pero no bloquean el punto de partida probado.

### Siguiente paso

MP-008 está `DONE`. MP-009 puede ramificar desde `mp-008-quality-engine` sin esperar merge a `main`, conforme al hito autorizado y ADR-0007.

**MP-007 — Collector idempotente**

Ejecutor: Claude Code · Revisor: OpenAI Codex · Estado: **DONE** (aprobado el 2026-11-19)

Worktree/rama: `mp-007-collector`, ramificada desde `mp-006-postgis-schema` (MP-006 `DONE`)

### Checklist de MP-007

- [x] `services/collector/http_client.py`: `fetch_with_retry` con backoff exponencial y timeout, solo `urllib` (sin dependencia nueva para HTTP).
- [x] `services/collector/db.py`: capa de acceso a PostgreSQL (MP-006); corregido un bug real de transacciones (ver más abajo) para que cada ciclo se comprometa como unidad atómica.
- [x] `services/collector/collector.py`: `run_cycle` = fetch → parse → filtro de alcance (núcleo Madrid, ADR-0008) → dedupe (ADR-0010) → persist, con el ciclo entero en una sola transacción.
- [x] `services/collector/__main__.py`: bucle de polling infinito, un feed fallido no detiene el colector completo.
- [x] `docs/adr/0010-dedup-strategy.md` (nuevo, `Propuesto`): hash completo de la entidad comparado contra la última fila almacenada por clave de entidad; sin `seen_count`.
- [x] 46 tests reales en verde (31 contratos + 6 fixtures + 9 colector); 5 de los 9 del colector son integración real contra PostgreSQL (no mocks de BD).
- [x] **Soak test real de 20 minutos** contra los 3 feeds en vivo: 40 ciclos, 0 errores, 1155 entidades insertadas, 304 deduplicadas, 2622 fuera de alcance; durabilidad confirmada con una conexión `psql` nueva tras el proceso.
- [x] **3 hallazgos reales corregidos** (feed en vivo, no cubiertos por fixtures de MP-003/MP-004): `trip_id` de refuerzo `SPECIAL_<núcleo>_<resto>`, `stopTimeUpdate[].arrival` sin `delay`, respuesta real sin la clave `entity`. Los tres con test de regresión. Detalle en `docs/research/MP-003-probe-findings.md` §10.
- [x] **1 bug de transacciones corregido antes de producción:** `with conn.transaction()` por `INSERT` individual, con una conexión de larga duración, dejaba `vehicle_position_observation` sin comprometer mientras `source_ingestion_run` sí persistía — detectado verificando con una conexión nueva, no confiando en la ausencia de excepción. Corregido centralizando la transacción en `run_cycle`.
- [x] **Hallazgo de alcance documentado, no bloqueante** (DEC-020): el filtro descarta por núcleo (Madrid), no todavía por línea C5 específica (ADR-0001 `Aceptado`) — acotar a C5 requiere la resolución `trip_id`→`route_id` de MP-010.
- [x] Identidad Git verificada en cada commit; contenedor `madrid-pulse` detenido al finalizar (volumen con los datos reales del soak test conservado); `*-traza-app` intactos.
- [x] **Primera revisión independiente de Codex (dispatch `ctx_a674a371ce8a`): no aprobada** — reejecutó las 45 pruebas, consultó el feed vivo (el snapshot puntual no contenía `SPECIAL_`/`ADDED`), confirmó esos casos en el volumen real conservado del soak test y encontró un bloqueante real: `latest_payload_hash` sin desempate (`ORDER BY observed_at DESC` solo) producía una fila duplicada real en su reproducción de 3 ciclos (`(1, 6)` en vez de `(0, 7)` en el tercer ciclo) cuando dos filas de la misma entidad comparten `observed_at`.
- [x] Corregido con `id DESC` como desempate secundario en las 3 consultas de `_LATEST_HASH_QUERIES`; verificado revirtiendo el fix temporalmente y confirmando que el nuevo test (`test_tied_observed_at_does_not_break_dedup_on_third_cycle`) falla exactamente como reportó Codex y pasa con el fix restaurado. 46 tests en verde.
- [x] **Segunda revisión independiente de Codex (dispatch `ctx_801574c4ef71`): aprobada** — inspeccionó el diff de `3f83699`, ejecutó el test de regresión específico contra PostgreSQL real (`OK`) y repitió las 46 pruebas completas (31 contratos + 6 fixtures + 9 colector, todas `OK`). Confirmado que `id DESC` resuelve el empate en las tres consultas de deduplicación. **APROBADO.**

### Resultado y límites

El colector ingiere y deduplica de verdad contra el feed en vivo de Renfe, con evidencia de ejecución sostenida de 20 minutos sin errores. No resuelve `trip_id` contra el GTFS estático (diferido a MP-010 por ADR-0009) ni acota a C5 específicamente (DEC-020) — ambas limitaciones ya estaban previstas y documentadas antes de empezar la tarea, no son hallazgos de última hora sin plan.

### Bloqueos

Ninguno. El bloqueante real encontrado por la primera revisión de Codex (dedup no determinista) está corregido y verificado independientemente; los dos puntos de alcance documentados no bloquean el cierre de MP-007 según los criterios de aceptación de `docs/TASKS.md`.

### Siguiente paso

MP-007 está `DONE`. MP-008 puede abrir su worktree desde `mp-007-collector` conforme al hito autorizado y al modelo de autonomía de ADR-0007, sin esperar merge a `main`.

**MP-006 — Esquema PostgreSQL/PostGIS v1**

Ejecutor: OpenAI Codex · Revisor: Claude Code · Estado: **DONE** (aprobado el 2026-11-19)

Worktree/rama: `mp-006-postgis-schema`, ramificada desde `mp-005-contrato-canonico` (MP-005 `DONE`)

### Checklist de MP-006

- [x] Compose aislado: proyecto `madrid-pulse`, imagen `postgis/postgis:17-3.5`,
  puerto `127.0.0.1:5433`, red y volumen nombrados propios; los contenedores
  `*-traza-app` no se tocaron.
- [x] `0001_init.up.sql` transaccional: PostGIS y las 14 entidades de aplicación
  (más `source_feed_version`, exigida por el versionado GTFS y su FK), constraints
  e índices B-tree/GIST.
- [x] Correspondencia canónica documentada: `entity_count`, `affected_route_ids`,
  `latitude`/`longitude`, `raw_vehicle_label`, `next_stop_id`,
  `nucleo_prefix`/`nucleo_name`/`nucleo_prefixes`; `geom` generado desde las
  coordenadas y nullable cuando la fuente no aporta posición.
- [x] Migración aplicada sobre PostgreSQL/PostGIS real con `ON_ERROR_STOP=1`:
  `CREATE TABLE` ×14, `CREATE INDEX` ×5 y `COMMIT`; PostGIS `3.5.2`.
- [x] Datos válidos insertados; `geom` generado como `POINT(-3.689 40.406)` y
  observación sin posición persistida con `latitude`, `longitude` y `geom` nulos.
- [x] Constraints probadas con fallos reales (todos exit 1): duplicado de
  `(network_id, source_route_id)`, de `(service_date, source_trip_id)` y de
  `(ingestion_run_id, payload_hash)` rechazados por sus `UNIQUE` respectivos.
- [x] Rollback real con `ON_ERROR_STOP=1`: 14 tablas eliminadas y `COMMIT`;
  consulta posterior `remaining_application_tables = 0`. PostGIS se conserva
  porque la imagen instala extensiones dependientes antes de la migración.
- [x] Ciclo final `down → up` repetido desde cero: ambos comandos exit 0.
- [x] Suites de regresión reejecutadas: contratos 23/23 `OK`; fixtures 6/6 `OK`.
- [x] `docker compose ... config --quiet` y `git diff --check`: exit 0.
- [x] Contenedor de Madrid Pulse detenido al finalizar; volumen propio conservado
  con la migración final aplicada para que el propietario pueda reanudarlo.
- [x] Revisión independiente de Claude Code (2026-11-19): **APROBADA**. Reproducido
  el ciclo completo de forma propia (no solo verificado el reporte de Codex):
  rollback necesario primero porque el volumen ya tenía el esquema cargado, luego
  `up → datos de prueba → 3 duplicados rechazados → down → up` otra vez, todo
  `exit 0`/`exit 1` según corresponde. GIST confirmados en `vehicle_position_observation.geom`
  y `station.geom`. Confirmada la ausencia real de `effect`/`cause`/`header_text`
  y `current_stop_sequence`. Suites de regresión reejecutadas de forma
  independiente (23/23 y 6/6). `check_links.py`: 46 enlaces, ninguno roto.
  Identidad Git verificada. Contenedores `*-traza-app` intactos.
  **Hallazgo (corregido en esta misma revisión):** este documento había
  reemplazado el registro completo de MP-005 en "Tarea actual" por el de MP-006
  sin archivarlo primero aquí, rompiendo el patrón de MP-002/MP-003/MP-004 —
  corregido moviendo el registro íntegro de MP-005 a esta sección.

### Resultado y límites

SQL plano permite auditar el DDL inicial sin introducir todavía un framework de
migraciones. El rollback elimina el esquema de aplicación pero no usa
`DROP EXTENSION ... CASCADE`: las extensiones PostGIS dependientes vienen
preinstaladas por la imagen y no pertenecen a esta migración.

### Bloqueos

Ninguno.

### Siguiente paso

MP-006 está `DONE`. MP-007 puede ramificar desde `mp-006-postgis-schema` sin
esperar merge a `main`, conforme al hito autorizado y ADR-0007.

**MP-005 — Contrato canónico interno**

Ejecutor: Claude Code · Revisor: OpenAI Codex · Estado: **DONE** (aprobado el 2026-11-18)

Worktree/rama: `mp-005-contrato-canonico`, ramificada desde `mp-004-fixtures` (MP-004 `DONE`)

### Checklist de MP-005

- [x] `packages/contracts/raw.py`: modelos Pydantic que reflejan exactamente el JSON bruto observado en MP-003/MP-004 (sin inventar campos); acepta campos nuevos no verificados sin fallar (`extra="ignore"`).
- [x] `packages/contracts/nucleo.py`: tabla de prefijos de núcleo verificada en MP-003, con `is_madrid`/`nucleo_name`.
- [x] `packages/contracts/canonical.py`: `VehiclePositionObservation`, `TripUpdateObservation`, `ServiceAlert`, `FeedHealth` — UTC siempre, dato ausente = `None` nunca `0`, `nucleo_prefix` derivado como `computed_field` (no aceptado como entrada independiente).
- [x] `packages/contracts/normalize.py`: funciones puras `raw → canonical`, sin red ni base de datos.
- [x] 23 tests reales ejecutados (`python3 -m unittest discover -s packages/contracts/tests -p 'test_*.py' -v`) → `OK`: parseo contra fixtures reales, normalización (incluido el test de colisión núcleo/C5 a nivel de contrato canónico), sintéticos (JSON Schema, rechazo de datos inválidos, caso multi-núcleo no observado), enforcement UTC y regresión de campos `raw` no observados.
- [x] **Hallazgo:** `docs/DATA_MODEL.md` asumía `speed_kmh`/`bearing`/`current_stop_sequence` y `effect`/`cause`/`header_text` de alertas que el feed real NUNCA emite (verificado contra ~800 entidades combinadas de MP-003/MP-004). Corregido `docs/DATA_MODEL.md`, `docs/DATA_QUALITY.md` (nota sobre cómo calcular `implausible_speed` sin un campo de origen), registrado DEC-018/ADR-0009 (`Propuesto`).
- [x] Autocorregido antes de delegar: una edición introdujo una fila duplicada en `docs/DATA_QUALITY.md` (`off_track` repetida) — detectado y corregido en la misma ronda, sin necesitar que Codex lo señalara.
- [x] Primera revisión independiente de Codex (dispatch `ctx_ea1d5cf46d74`): **no aprobada** — reejecutó la suite (17/17 OK en su entorno) y auditó el diff campo a campo. 3 bloqueantes + 1 menor:
  - **Bloqueante 1:** `RawActivePeriod.end` no tenía el comentario de "campo opcional no observado" que sí llevan los demás campos documentados tras el hallazgo de MP-005 — se corrigió **añadiendo un comentario**, lo que resultó insuficiente (ver 2ª ronda).
  - **Bloqueante 2:** el esquema canónico documentaba "UTC siempre" pero no lo exigía — un `datetime` naive o con offset no UTC pasaría la validación sin error. Corregido con `field_validator` en los 4 modelos (`VehiclePositionObservation`, `TripUpdateObservation`, `ServiceAlert`, `FeedHealth`), con 5 tests nuevos que prueban el rechazo real.
  - **Bloqueante 3:** `docs/research/TRACEABILITY.md` no señalaba que el modelo candidato original (`deep-research-report.md`) queda contradicho por esta verificación — añadida la fila correspondiente sin editar el documento de investigación congelado.
  - **Menor:** `ADR-0009` decía erróneamente que Codex podía promover el ADR a `Aceptado` (contrario a `AGENTS.md`/ADR-0007: solo el propietario puede) — corregido; `raw.py` tenía un error de redacción ("ninguno de los dos" para tres campos) — corregido.
- [x] Segunda revisión independiente de Codex (dispatch `ctx_ded900b82f20`): **no aprobada** — señaló correctamente que un comentario no resuelve una contradicción: `raw.py:1-9` declara explícitamente que el módulo no debe contener campos no observados, y `RawActivePeriod.end` seguía ahí. Corregido de verdad esta vez: `end` **eliminado** de `RawActivePeriod` (no solo comentado); `normalize.py`/`canonical.py` ajustados; añadido un test de regresión (`test_raw_active_period_has_no_unobserved_end_field`) que falla si alguien lo reintroduce sin verificarlo, incluso si el JSON de origen lo trae (se ignora por `extra="ignore"`). 23 tests en total.
- [x] Tercera revisión independiente de Codex: **APROBADA**, sin hallazgos abiertos — reejecutó 23/23 tests; confirmó independientemente que `RawActivePeriod.model_fields == {"start"}`, que un `end` extra se ignora sin convertirse en atributo, que fechas naive y `+02:00` se rechazan mientras UTC se acepta, y que trazabilidad, ADR, enlaces, secretos y whitespace son coherentes.

### Resultado y límites

El contrato canónico se valida contra datos reales (MP-004) y sintéticos. La separación `raw`/`canonical` evita que un cambio futuro del feed de Renfe se propague directamente al resto del sistema sin pasar por una capa de normalización explícita. Los hallazgos de campos no observados (ADR-0009) son correcciones al modelo candidato de MP-001, no contradicciones nuevas sin resolver.

### Bloqueos

Ninguno.

### Siguiente paso

MP-005 está `DONE`. MP-006 pudo ramificar desde esta rama sin esperar merge a `main`, conforme al hito autorizado y ADR-0007.

**MP-004 — Fixtures reproducibles**

Ejecutor: OpenAI Codex · Revisor: Claude Code · Estado: **DONE** (aprobado el 2026-11-18)

Worktree/rama: `mp-004-fixtures`, ramificada desde `mp-003-probe-c5` (MP-003 `DONE`)

### Checklist de MP-004

- [x] Capturas frescas directas de `vehicle_positions.json`, `trip_updates.json` y `alerts.json`: `200 application/json`, sin guardar cabeceras ni cookies.
- [x] Tres fixtures JSON reducidas y versionables: 394 → 10 posiciones, 401 → 8 actualizaciones y 76 → 3 alertas.
- [x] Cada fixture conserva entidades de Madrid; posiciones conserva además C5 con prefijos `20`, `30` y `40` para probar la colisión entre núcleos.
- [x] `tests/fixtures/MANIFEST.md` registra fecha UTC, endpoint, recuentos y SHA-256.
- [x] Tests offline con Python `unittest`: envoltura GTFS-RT, esquema por feed, integridad SHA-256, cobertura Madrid y rechazo del filtro ingenuo por etiqueta C5.
- [x] Ejecución real: `python3 -m unittest discover -s tests/fixtures -p 'test_*.py' -v` → 6 tests, `OK` (0.001 s).
- [x] Los tres ficheros pasan `python3 -m json.tool`; hashes re-verificados con `shasum -a 256`.
- [x] Revisión independiente de Claude Code: SHA-256 recalculados de forma propia (coinciden), suite re-ejecutada (6/6 `OK`), inspección del test de colisión C5 confirmando que es sustantivo (un filtro ingenuo por etiqueta captura 4 núcleos, el correcto aísla solo Madrid), sin cookies/secretos, enlaces y licencias revalidados. **APROBADO.**

### Resultado y límites

Las fixtures se cargan exclusivamente desde disco y no incluyen código de red ni dependencias externas. La captura de posiciones no contenía ninguna entidad sin `position`; el caso observado en MP-003 no se fabricó. `pytest` no estaba instalado, por lo que se eligió `unittest` de la biblioteca estándar para mantener la suite reproducible sin instalación adicional.

### Bloqueos

Ninguno.

### Siguiente paso

MP-004 está `DONE`. MP-005 (Contrato canónico interno, ejecutor Claude Code, revisor Codex) puede ramificar desde `mp-004-fixtures` sin esperar merge a `main`.

**MP-003 — Probe real de feeds C5 (GTFS + GTFS-RT)**

Ejecutor: Claude Code · Revisor: OpenAI Codex · Estado: **DONE** (aprobado el 2026-11-18)

Worktree/rama: `mp-003-probe-c5`, ramificada desde `mp-002-fuentes-licencias` (MP-002 `DONE`)

### Checklist de MP-003

- [x] `vehicle_positions.json` probado en vivo: `200 OK`, JSON real (GTFS-RT 2.0), 3 polls espaciados ~20 s confirmando frecuencia de refresco real (~20–22 s).
- [x] `trip_updates.json` probado en vivo: `200 OK`, 302 entidades, esquema con `delay` en segundos por parada.
- [x] `alerts.json` probado en vivo: `200 OK`, 82 alertas activas, confirma `routeId` completo por entidad informada.
- [x] GTFS estático descargado realmente (15,7 MB, `200 OK`) desde el enlace real (`ssl.renfe.com`, distinto del enlace de portal que había fallado en MP-002) e inspeccionado (`routes/trips/stops/calendar/shapes/stop_times/transfers/agency.txt`).
- [x] **Hallazgo crítico:** "C5" no es único — existe también en Asturias (`20T0011C5`) y Andalucía (`30T0009C5`) en el mismo feed nacional. Registrado como DEC-017/ADR-0008 (`Propuesto`); `docs/DATA_MODEL.md` corregido.
- [x] Resolución de `trip_id` del feed en vivo contra GTFS estático: **igualdad literal de cadena** contra el campo `trip_id` de `trips.txt` (3er campo del CSV), confirmado 403/403 (y 404/404 en la re-verificación de Codex con datos frescos) — es un `JOIN` directo, no requiere reconstrucción por `(service_id, vehículo, línea)`.
- [x] `docs/legal/DATA_SOURCES.md` actualizado de `PENDING MP-003` a `VERIFIED` para los 4 recursos Renfe.
- [x] `docs/research/MP-003-probe-findings.md`, `docs/TASKS.md`, `docs/CHANGELOG.md`, `docs/DECISIONS.md` actualizados.
- [x] Primera revisión independiente de Codex (dispatch `ctx_61d7dd4fd86b`): **no aprobada** — repitió los probes en vivo él mismo (no solo leyó el reporte), incluida una comparación sistemática `comm -12`/`comm -23` de los 403 `trip_id` en vivo contra `trips.txt`. 2 bloqueantes + 2 menores:
  - **Bloqueante 1:** 403/403 `trip_id` en vivo coinciden literalmente con `trips.txt` — contradice la afirmación anterior de este documento. Causa raíz: un `grep` propio anclado al campo equivocado (`trip_id` es el 3er campo de `trips.txt`, no el 1º). Corregido en `docs/research/MP-003-probe-findings.md` §7 con la comparación de conjuntos completa.
  - **Bloqueante 2:** `docs/DATA_MODEL.md` tenía `UNIQUE(network_id, source_route_id)` junto con una nota que agrupaba 5 `source_route_id` bajo un único `route.id` — cardinalidad imposible. Corregido: 5 filas `route.id`, agrupadas por `(network_id, short_name)`.
  - **Menor:** findings afirmaba falsamente que el GTFS no incluía `shapes.txt` (sí lo incluye, está en la propia tabla del documento). Corregido.
  - **Menor:** no se había medido la frecuencia de `trip_updates`/`alerts` (solo `vehicle_positions`). Medido: `trip_updates` Δ42s, `alerts` Δ20s (2 polls cada uno).
  - Codex confirmó que el resto de pendientes (cobertura larga de `trip_updates`, CRTM, shapes/stop_times detallados, cambio de día) están razonablemente fuera de alcance de MP-003.
- [x] Revisión final independiente de Codex: **APROBADA**, sin hallazgos abiertos. Repetida la comparación con datos frescos: 404/404 `trip_id` vivos coinciden literalmente con `trips.txt`, 0 sin match. Confirmada la coherencia de cardinalidad entre `docs/DATA_MODEL.md`, DEC-017 y ADR-0008; enlaces, secretos y licencias revalidados.

### Resultado y límites

Los tres feeds GTFS-RT y el GTFS estático están disponibles, accesibles y documentados con esquema real. El hallazgo de la colisión de "C5" entre núcleos es el resultado más importante de esta tarea y obliga a una corrección de `docs/DATA_MODEL.md` (ver DEC-017/ADR-0008, `Propuesto`, pendiente de promoción por el propietario).

**Pendiente explícito, no bloqueante para MP-003, a resolver en tareas posteriores:** cobertura real de `trip_updates` para Madrid en ventana más larga (en el único poll realizado, Madrid tuvo 0/302 — no se puede concluir si es casualidad puntual o un patrón, ver findings §5); descarga del GTFS de CRTM (el NAP exigía login, no se probó); validación detallada de `shapes`/`stop_times` de las 5 variantes de C5 Madrid (corresponde a MP-010); comportamiento en cambio de día de servicio (corresponde a MP-012).

### Bloqueos

Ninguno. El hallazgo de la colisión de "C5" no bloquea MP-003 (ya está documentado y corregido en el modelo); sí debe tenerse en cuenta en MP-005 (contrato canónico) y MP-007 (colector) antes de implementarlos.

### Siguiente paso

MP-004 puede ramificar desde `mp-003-probe-c5` conforme al hito autorizado y al grafo de dependencias; no necesita esperar a que el propietario fusione esta rama a `main`.

### MP-001 y MP-002 — cerradas en ramas anteriores de esta cadena

**MP-002 — Matriz de fuentes y licencias**

Ejecutor: OpenAI Codex · Revisor: Claude Code · Estado: **DONE** (aprobado por Claude Code el 2026-11-18)

Worktree/rama: `mp-002-fuentes-licencias`

### Checklist de MP-002

- [x] Documentación y ADRs obligatorios leídos antes de modificar archivos.
- [x] Renfe GTFS estático verificado como `CC BY 4.0` en el recurso oficial.
- [x] Renfe GTFS-RT Vehicle Positions, Trip Updates y Alerts verificados como `CC BY 4.0` en sus datasets oficiales.
- [x] Condiciones adicionales de Renfe Data verificadas: atribución, actualización, conservación de metadatos y no patrocinio.
- [x] GTFS Cercanías Madrid identificado en Comunidad de Madrid/NAP y licencia propia `CRTM-LDA` verificada en CRTM.
- [x] Requisitos CRTM documentados: `Powered by CRTM`, bruto/explotado, actualización/metadatos, no falseamiento/no patrocinio.
- [x] OpenStreetMap verificado como `ODbL-1.0`; consulta/base colectiva separadas de una base derivada distribuida.
- [x] `LICENSE` de Via Península verificado como `AGPL-3.0`; política de no copiar código preservada.
- [x] `LICENSE` de Niltra/cercanias verificado como MIT.
- [x] `LICENSE` de atlas-ferroviario verificado: MIT para código más aviso Renfe `CC BY 4.0` para datos.
- [x] Valfiguer verificado: datos/API normalizados `CC BY 4.0`; no se localizó repo público de implementación ni licencia de código (DEC-016).
- [x] Dataset estadístico Comunidad de Madrid 1923861 verificado como `CC BY 4.0` y de ámbito declarado nacional.
- [x] `DATA_SOURCES.md`, `LICENSE_MATRIX.md` y `ATTRIBUTION.md` actualizados con evidencia y fecha real.
- [x] `TASKS.md`, `STATUS.md`, `CHANGELOG.md` y `DECISIONS.md` actualizados.
- [x] Revisión independiente de Claude Code: re-verificación propia (no solo lectura del reporte de Codex) vía `gh api` y fetch directo de `data.renfe.com`, `crtm.es` y los ficheros `LICENSE` reales de los tres repos de referencia. Todas las afirmaciones de Codex se confirmaron exactas, incluido el matiz MIT-pero-`NOASSERTION` de atlas-ferroviario. **APROBADO.**

### Resultado y límites

No apareció una incompatibilidad que bloquee el uso previsto de las fuentes primarias. Renfe y CRTM permiten reutilización comercial y no comercial con sus respectivas condiciones; OSM es utilizable con atribución, pero una base derivada distribuida debe cumplir ODbL. Via Península permanece estrictamente como referencia conceptual por AGPL.

La verificación de MP-002 cubre **licencia y atribución**, no disponibilidad técnica, esquema, frecuencia ni cobertura C5. Esas propiedades siguen `PENDING MP-003`. El portal Renfe mostraba un fallo histórico SSL en el comprobador del recurso GTFS estático y NAP pedía inicio de sesión para descargar el GTFS CRTM; ambos se probarán técnicamente en MP-003 y no alteran la licencia verificada.

### Bloqueos

Ninguno. La licencia desconocida de la implementación Valfiguer no bloquea porque DEC-006 prohíbe usarla como dependencia de producción; queda registrada en DEC-016 y en la matriz.

### Siguiente paso

MP-002 está `DONE`. MP-003 ramifica desde esta rama (`mp-002-fuentes-licencias`) sin esperar merge a `main`, conforme a ADR-0007.

### Nota de proceso (ramas encadenadas)

Esta rama se bifurcó de `chore/mp-001-foundation` en el commit `3e7b533`, **antes** de que esa rama recibiera un commit posterior (`fac945c`) registrando la aceptación de MP-001 por el propietario y la autorización de Hito 1. Codex infirió correctamente esa autorización por el contexto del encargo (no por leer un `STATUS.md` ya actualizado, que en esta rama no existía todavía) y la registró aquí de forma independiente. Resultado: `chore/mp-001-foundation` y esta rama tienen ahora dos redacciones distintas, pero no contradictorias, de "MP-001 está DONE / Hito 1 autorizado". Claude Code alineó el campo `Estado` de MP-001 en `docs/TASKS.md` de ambas ramas a `DONE` para que la reconciliación en el merge final sea trivial. **Lección para hitos futuros:** si se edita el `STATUS.md` de la rama base después de que una rama hija ya se bifurcó, esa edición no llega a la hija automáticamente — hay que reconciliarla explícitamente, como aquí.

## Bitácora

| Timestamp UTC | Tarea | Evento | Evidencia |
|---|---|---|---|
| `2026-11-18` | MP-001 | Revisión cruzada aprobada; tarea tratada como `DONE` para la cadena autorizada | `docs/TASKS.md`; dispatch de revisión `ctx_0ee25a6a5d2c` |
| `2026-11-18` | Hito 1 | Propietario autoriza explícitamente `MP-002` → `MP-009` | Despacho Orca de MP-002 (`task_8f7f49749f10`) |
| `2026-11-18T15:16:53Z` | MP-002 | Cierre de verificación formal de licencias y condiciones | Checklist y enlaces en `docs/legal/DATA_SOURCES.md` |
| `2026-11-18T15:16:53Z` | MP-002 | Hallazgo Valfiguer: datos/API `CC BY 4.0`, implementación sin repo/licencia verificable | DEC-016; `docs/legal/LICENSE_MATRIX.md` |
| `2026-11-18T15:16:53Z` | MP-002 | Entregables documentales completados; tarea pasa a `REVIEW` | `docs/TASKS.md`; commit local de MP-002 |
| `2026-11-18` | MP-002 | Revisión independiente de Claude Code (gh api + fetch directo de Renfe/CRTM/LICENSE reales): **APROBADO**, sin hallazgos bloqueantes ni menores sobre el contenido. Hallazgo de proceso (divergencia de ramas) documentado y reconciliado | — |
| `2026-11-18T15:28–15:31Z` | MP-003 | Probe real de los 3 feeds GTFS-RT (3 polls de `vehicle_positions` espaciados ~20 s, 1 poll de `trip_updates` y `alerts`) y descarga real del GTFS estático (15,7 MB) | `docs/research/MP-003-probe-findings.md` |
| `2026-11-18` | MP-003 | Hallazgo crítico: "C5" no es único en el feed nacional (también en Asturias y Andalucía); corregido `docs/DATA_MODEL.md`, registrado DEC-017/ADR-0008 (`Propuesto`) | `docs/DECISIONS.md`; `docs/adr/0008-route-identity.md` |
| `2026-11-18` | MP-003 | Entregables completados; tarea pasa a `REVIEW`, delegada a Codex para revisión independiente en este mismo worktree | `docs/TASKS.md`; commit local de MP-003 |
| `2026-11-18` | MP-003 | Revisión de Codex (repitiendo probes en vivo él mismo): no aprobada — 2 bloqueantes (trip_id sí coincide literalmente con trips.txt; cardinalidad imposible en DATA_MODEL.md) + 2 menores (shapes.txt sí incluido; faltaba medir frecuencia de trip_updates/alerts) | dispatch `ctx_61d7dd4fd86b` |
| `2026-11-18` | MP-003 | Los 4 hallazgos corregidos tras verificación propia (comparación de conjuntos 403/403, medición real de trip_updates Δ42s y alerts Δ20s); reenviado a Codex | `bdf263e` |
| `2026-11-18` | MP-003 | Segunda revisión de Codex (con descarga fresca, 404/404 confirmado): **no aprobada** — hallazgo menor residual: `docs/STATUS.md` conservaba la afirmación bloqueante ya desmentida en un bullet que no se había actualizado; además "alerts sin cambios de contenido" se basaba solo en igual recuento, no en comparación real de contenido | dispatch `ctx_e4a31f1e7e61` |
| `2026-11-18` | MP-003 | Revisión final de Codex: **APROBADA** — 404/404 `trip_id` resueltos por igualdad literal, 0 sin match; cardinalidad, documentación, enlaces, secretos y licencias coherentes. MP-003 pasa a `DONE` | revisión posterior a `f6d8ee9` |
| `2026-11-18T16:01Z` | MP-004 | Capturas frescas de los 3 feeds; fixtures reducidas 394→10, 401→8 y 76→3 con hashes SHA-256 documentados | `tests/fixtures/MANIFEST.md` |
| `2026-11-18T16:04Z` | MP-004 | Suite offline ejecutada: 6 tests `unittest`, `OK`; JSON y hashes revalidados; tarea pasa a `REVIEW` | `tests/fixtures/test_parse_fixtures.py`; `docs/TASKS.md` |
| `2026-11-18` | MP-004 | Revisión independiente de Claude Code: hashes y suite re-ejecutados, test de colisión C5 inspeccionado y confirmado sustantivo. **APROBADO**, sin hallazgos. MP-004 pasa a `DONE` | commit pendiente |
| `2026-11-18` | MP-005 | Contrato canónico implementado (`packages/contracts/`) con 17 tests reales (reales + sintéticos) ejecutados en verde | commit pendiente |
| `2026-11-18` | MP-005 | Hallazgo: `speed_kmh`/`bearing`/`current_stop_sequence`/`effect`/`cause`/`header_text` del modelo candidato nunca aparecen en el feed real; corregidos `docs/DATA_MODEL.md`/`docs/DATA_QUALITY.md`, registrado DEC-018/ADR-0009 (`Propuesto`) | — |
| `2026-11-18` | MP-005 | Tarea pasa a `REVIEW`, delegada a Codex para revisión independiente en este mismo worktree | — |
| `2026-11-18` | MP-005 | Primera revisión de Codex: no aprobada — 3 bloqueantes + 1 menor, todos reales (comentario inconsistente, falta de enforcement UTC, falta de trazabilidad, redacción incorrecta en ADR-0009) | dispatch `ctx_ea1d5cf46d74` |
| `2026-11-18` | MP-005 | Los 4 hallazgos corregidos: `require_utc`/`require_utc_or_none` añadidos con 5 tests nuevos (22 en total), `TRACEABILITY.md` actualizado, `ADR-0009` y `raw.py` corregidos; reenviado a Codex | commit `cf11012` |
| `2026-11-18` | MP-005 | Segunda revisión de Codex: no aprobada — el bloqueante 1 de la ronda anterior solo se había documentado con un comentario, no resuelto; `raw.py` seguía declarando `end` pese a que el propio módulo prohíbe campos no observados | dispatch `ctx_ded900b82f20` |
| `2026-11-18` | MP-005 | `end` eliminado de `RawActivePeriod` (no solo comentado); `normalize.py`/`canonical.py` ajustados; test de regresión añadido (23 tests); reenviado a Codex para tercera verificación | commit `a9b1172` |
| `2026-11-18` | MP-005 | Tercera revisión independiente de Codex: **APROBADA** — 23/23 tests, esquema `raw`, enforcement UTC, trazabilidad, ADR, enlaces, secretos y whitespace verificados; tarea pasa a `DONE` | revisión posterior a `a9b1172` |
| `2026-11-18T22:53:33Z` | MP-006 | Migración PostGIS aplicada, constraints probadas con duplicados reales, rollback verificado (`0` tablas de aplicación) y ciclo final `down → up` completado; tarea pasa a `REVIEW` | `infra/migrations/`; salida real de `psql` documentada en TASKS/checklist |
| `2026-11-19` | MP-006 | Revisión independiente de Claude Code: ciclo `up/down/up` reproducido desde cero en el worktree, 3 `UNIQUE` rechazados de verdad, 2 `GIST` confirmados, ausencia de campos no observados verificada, suites de regresión reejecutadas (23/23, 6/6), 46 enlaces sin romper. **APROBADA**. Hallazgo de proceso: `STATUS.md` había perdido el checklist completo de MP-005 al no archivarlo antes de escribir el de MP-006; corregido en la misma revisión. Tarea pasa a `DONE` | commit `30507cf`; commit de revisión pendiente |
| `2026-11-18T23:31Z–23:51Z` | MP-007 | Soak test real de 20 min contra los 3 feeds en vivo: 40 ciclos, 0 errores, 1155 insertadas/304 dedup/2622 fuera de alcance; durabilidad confirmada con conexión `psql` nueva | `services/collector/`; log del soak test |
| `2026-11-18` | MP-007 | 3 hallazgos reales corregidos (trip_id `SPECIAL_`, `arrival` sin `delay`, `entity` ausente) y 1 bug de transacciones corregido antes de producción (commits parciales con conexión de larga duración); tarea pasa a `REVIEW`, delegada a Codex en este mismo worktree | `packages/contracts/nucleo.py`; `packages/contracts/raw.py`; `services/collector/db.py` |
| `2026-11-19` | MP-007 | Primera revisión de Codex: no aprobada — bloqueante real reproducido (dedup no determinista por `observed_at` empatado, fila duplicada real en reproducción de 3 ciclos) | dispatch `ctx_a674a371ce8a` |
| `2026-11-19` | MP-007 | Corregido con `id DESC` como desempate en `_LATEST_HASH_QUERIES`; verificado revirtiendo el fix y confirmando que el test de regresión reproduce exactamente el fallo reportado y pasa con el fix restaurado; reenviado a Codex para segunda verificación | — |
| `2026-11-19` | MP-007 | Segunda revisión independiente de Codex: test específico y suite completa (46/46) reejecutados contra PostgreSQL real; fix de desempate confirmado. **APROBADA**. MP-007 pasa a `DONE` | dispatch `ctx_801574c4ef71`; commit de revisión pendiente |
| `2026-11-19` | MP-008 | Motor de cinco reglas implementado e integrado transaccionalmente en el colector; umbrales calibrables documentados y reglas geométricas diferidas explícitamente a MP-012 | `packages/quality/`; `services/collector/` |
| `2026-11-19` | MP-008 | Suite completa ejecutada contra PostgreSQL real: 59/59 (31 contratos + 6 fixtures + 9 colector + 13 calidad), incluidos 10 casos mínimos disparo/no-disparo, medianoche UTC y persistencia/feed congelado con rollback. Tarea pasa a `REVIEW` para Claude Code | `packages/quality/tests/`; dispatch `ctx_63638731fde4` |
| `2026-11-19` | MP-008 | Revisión independiente de Claude Code: 59/59 reproducidas contra el mismo PostgreSQL real; diseño auditado. Hallazgo empírico no bloqueante: 12/117 pares reales de posiciones consecutivas del soak test disparan `implausible_speed` (246–787 km/h) — saltos reales de posición, no bug de cálculo; registrado para calibración en MP-012. **APROBADA**. Tarea pasa a `DONE` | commit `c3db20b`; commit de revisión pendiente |
| `2026-11-19` | MP-009 | Exportador DuckDB implementado; hallazgo real de huso horario (Europe/Madrid vs. UTC) encontrado y corregido antes de delegar; export real del 19-nov (1272 filas, ~76 KB ZSTD) y test de replay verificados; tarea pasa a `REVIEW`, delegada a Codex en este mismo worktree | `services/snapshotter/`; commit `0119c6a` |
| `2026-11-19` | MP-009 | Primera revisión de Codex: no aprobada — bloqueante real reproducido (3 `service_alert` reales desaparecían del export por particionar por `active_period_start` en vez de por observación real vía `ingestion_run_id`) | dispatch `ctx_d2b95955a73a` |
| `2026-11-19` | MP-009 | Corregido uniendo `service_alert` a `source_ingestion_run`; replay ampliado a las 5 tablas; verificado revirtiendo el fix (falla `0≠1` como reportó Codex) y restaurándolo; reexportado el día real: `service_alert` pasa de 0 a 3; reenviado a Codex para segunda verificación | — |
| `2026-11-19` | MP-009 / Hito 1 | Segunda revisión independiente de Codex aprobada: replay ampliado 2/2, limpieza completa, export real 668/484/3/120/0 y tres alertas confirmadas en Parquet. MP-009 pasa a `DONE`; Hito 1 (`MP-002` → `MP-009`) completo, pendiente de decisión del propietario sobre el siguiente hito | dispatch `ctx_095ae1499806` |
| `2026-11-19` | Hito 1 | Auditoría independiente de Codex (dispatch no registrado como `ctx_` en esta rama, ver worktree `mp-009-historical-export`): **APROBADA**, sin bloqueantes. Propietario crea PR #1 (`mp-009-historical-export` → `main`) y lo fusiona él mismo | PR #1; commit de merge `f567d3c` |
| `2026-11-19` | Hito 2 | Propietario autoriza explícitamente `MP-010` → `MP-015` ("Live Railway MVP"), fija la tabla ejecutor/revisor, la política de selección de modelo y los límites de autonomía (sin push/PR/merge sin autorización puntual; identidad Git exclusiva del propietario; sin coautores de agente) | mensaje de autorización del propietario, `2026-11-19` |
| `2026-11-19` | Hito 2 | Sincronización inicial: `git fetch`/`git pull --ff-only` confirma `main` local al día con `origin/main`; verificado que `8be1272` (tope de `mp-009-historical-export`) es ancestro de `f567d3c`, sin commits perdidos. Verificación empírica (no asumida) de que `orca orchestration worker-start --model/--effort` son parámetros reales para Claude; identificadores confirmados `sonnet`/`opus` (no existe un "5.5" verificable en este entorno) | `agent-context.json`; `worker-start --help` |
| `2026-11-19` | Hito 2 | DEC-015 resuelto: con Hito 1 ya en `main`, la convergencia de MP-012 (MP-008+MP-010+MP-011) no requiere `git merge` real — basta ramificar la cadena MP-010→MP-011 desde una rama que ya contenga a `main` (y por tanto a MP-008) como ancestro; mecanismo general documentado en `AGENTS.md` para casos futuros con divergencia real | este documento; `AGENTS.md` |
| `2026-11-19` | Hito 2 | ADR-0011 (`Propuesto`) redactado: distingue el piloto técnico de Hito 2 (C5) del objetivo de primera versión pública (toda la red de Cercanías Madrid), sin reescribir ADR-0001 (`Aceptado`) — amplía su alcance de implementación sin contradecir su decisión ya aceptada | `docs/adr/0011-public-scope-vs-technical-pilot.md` |
| `2026-11-19` | Hito 2 | Worktrees de MP-010 (ejecutor Codex) y, tras su cierre, MP-011 (ejecutor Claude Code) preparados ramificando desde esta rama de coordinación (`chore/hito-2-coordination`, a su vez ramificada desde `main`) | `docs/TASKS.md` |
| `2026-11-19` | MP-010 | Parser/validador GTFS implementado; 71/71 tests (7 nuevos + 64 regresiones, 9 integraciones PostgreSQL reales) y ejecución adicional contra ZIP oficial completo (5 rutas, 8.160 trips, 165.205 stop_times, 14 patrones, 8 huérfanos, 0 errores). Hallazgos: upstream sin `direction_id` y variante `10T0035C5` sin stop_times. Compose Madrid Pulse detenido sin borrar volumen; `*-traza-app` intactos. Tarea pasa a `REVIEW` para Claude Code | `packages/gtfs/`; `tests/fixtures/gtfs_c5_real/MANIFEST.md`; DEC-023 |
| `2026-11-19` | MP-010 | Revisión independiente de Claude Code: código íntegro leído, 71/71 tests reejecutados subiendo/bajando el contenedor propio, recuentos reales `668/484/3/120/0` confirmados idénticos antes/después, ausencia del literal `"C5"` en la lógica verificada, identidad Git y enlaces a ADR-0011/DEC-022/DEC-023 correctos. **APROBADA, sin hallazgos.** MP-010 pasa a `DONE` | commit `add8aa6`; este documento |
| `2026-11-19` | MP-011 | Geometría OSM real implementada (`packages/geo/`): 4 relaciones direccionales de C5 Madrid descargadas y encadenadas sin huecos; 23 estaciones reales proyectadas en orden monótono (máx. 63,7 m); ruta corta confirmada como subsegmento del corredor largo. Evidencia visual real en navegador (Chrome DevTools MCP). 78/78 tests en verde. Hallazgos documentados como ambigüedades (DEC-025), no forzados: relaciones Fuenlabrada-truncadas sin coincidir con la ruta corta real, `usage=main`/`branch` sin verificar reparto exacto, huérfano `10T0035C5` aún sin validar. Overpass API devolvió `502` por capacidad varias veces; reintentos con pocos segundos de espera tuvieron éxito. Fixture ODbL congelada y atribuida (DEC-024). Tarea pasa a `REVIEW` para OpenAI Codex | `packages/geo/`; `tests/fixtures/osm_c5_real/MANIFEST.md`; DEC-024; DEC-025 |
| `2026-11-19` | MP-011 | Primera revisión de Codex: no aprobada — bloqueante real reproducido (`ChainGap` registrado pero la geometría seguía fabricando una unión a través del hueco; repro sintética con `distance_m=0.0`) + 2 menores (recuento de tests incorrecto; una variante real de 7 estaciones de `10T0047C5` se documentó como "subsegmento contiguo" sin serlo) + checksums anunciados pero ausentes | dispatch `ctx_6b6ad999cdfe` |
| `2026-11-19` | MP-011 | Corregido: `Corridor.segments` separa tramos reales (verificado revirtiendo el fix — el test de regresión falla exactamente como describió Codex y pasa con el fix restaurado); `render_preview.py` dibuja un `<polyline>` por tramo; ruta corta dividida en variante base contigua (6 estaciones, verificado por comparación literal de IDs) y variante con Atocha monótona-pero-no-contigua (7 estaciones); 4 SHA-256 añadidos y verificados en `MANIFEST.md`. 79/79 tests en verde (8 geo + 71 regresión). Reenviado a Codex para segunda verificación | — |
| `2026-11-19` | MP-011 | Segunda verificación independiente de Codex aprobada sobre `f795036`: repro sintética propia a `2223,9 m` del tramo más cercano (sin geometría fabricada), 8 geo + 71 regresión en verde, PostgreSQL `668/484/3/120/0` antes/después, patrones corto base/variante comprobados literalmente, 4 SHA-256 coincidentes, diff limpio e identidad Git correcta. MP-011 pasa a `DONE` | dispatch `ctx_24d7ea61fba0` |
| `2026-11-19` | MP-012 | DEC-015 resuelto y aplicado: `git merge-base --is-ancestor origin/main HEAD` confirmado desde `mp-011-osm-geometry`; worktree `mp-012-movement-engine` abierto sin fusión real. Dispatchado a Codex (ejecutor) con contexto de ADR-0004 (pipeline, cuatro estados), frecuencias reales medidas en MP-003 y el hallazgo de `implausible_speed` de MP-008 para calibración | `docs/TASKS.md`; `docs/STATUS.md` |
| `2026-11-19` | MP-012 | Implementación de Codex lista para revisión: `packages/movement` + ADR-0012; pipeline completo, cuatro estados/fuentes explícitos, flags topológicos y calibración. 90/90 tests en verde. Integración real read-only: 668→668 posiciones, 177 cerca del corredor, máximo salto map-matched 666,4 km/h; volumen final `668/484/3/120/0`. Tarea pasa a `REVIEW` para Claude Code | `packages/movement/`; `docs/adr/0012-movement-package-boundary.md` |
| `2026-11-19` | MP-012 | Revisión independiente de Claude Code: código íntegro leído, 90/90 tests reejecutados subiendo/bajando el contenedor propio, integración real reproducida con resultados idénticos (668→668, 177 cerca del corredor, 666,4 km/h), pipeline verificado matemáticamente (offset bidireccional, límites velocidad/aceleración, fallback recursivo correcto), ausencia del literal `"C5"` confirmada, identidad Git y enlaces ADR-0012/DEC-026 correctos. Evaluada y descartada la escalada a Opus por no ser necesaria. **APROBADA, sin hallazgos.** MP-012 pasa a `DONE` | commit `1edfa14`; este documento |
| `2026-11-19` | MP-013 | API FastAPI real implementada (`apps/api/`): 7 endpoints (`health`/`live/vehicles`(`/{id}`)/`lines`(`/{id}`)/`stations`(`/{id}`)), `history`/`metrics` diferidos explícitamente (DEC-027). Hallazgo real: `route`/`station`/`trip` siguen vacías y `trip_id` sigue `NULL` en PostgreSQL — resolución vía `Topology` en memoria, no `JOIN` SQL. Hallazgos DEC-028 (un corredor basta para ambos sentidos) y DEC-029 (solo 4/24 vehículos del soak son C5, confirma DEC-020 con datos reales). App arrancada con `uvicorn` y probada con `curl` real. 99/99 tests en verde. Tarea pasa a `REVIEW` para OpenAI Codex | `apps/api/`; `apps/api/openapi.json`; DEC-027–030 |
| `2026-11-19` | MP-013 | Primera revisión de Codex: no aprobada — 2 bloqueantes reales reproducidos (`age_s` `null` para vehículos sin ruta resuelta aunque calculable; `service_date` usaba fecha UTC en vez de Europe/Madrid, desplazando el horario cerca de medianoche) + 1 menor (recuento de líneas no-C5 incompleto en DEC-029) | dispatch `ctx_792a5fe349ba` |
| `2026-11-19` | MP-013 | Corregido: `age_s` se calcula siempre desde `observation.reported_at`; `service_date` usa conversión explícita a Europe/Madrid (verificado revirtiendo ambos fixes — los tests nuevos fallan exactamente como describió Codex y pasan con el fix restaurado); DEC-029 corregido con el cruce completo (4 C5, 19 de 9 líneas distintas, 1 sin resolver). 101/101 tests en verde. Reenviado a Codex para segunda verificación | — |
| `2026-11-19` | MP-013 | Revisión final independiente de Codex aprobada sobre `15170c4`: el único residuo documental ya enumera C1/C2/C3/C4/C4a/C4b/C8a/C8b/C10 y el trip de refuerzo sin resolver; diff mínimo y limpio, 11/11 tests API en verde, PostgreSQL `668/484/3/120/0`, identidad Git correcta y sin coautor. **APROBADA, sin hallazgos abiertos.** MP-013 pasa a `DONE` | dispatch `ctx_1235555422b3`; commit `15170c4` |
| `2026-11-19` | MP-014 | Worktree `mp-014-frontend` abierto, ramificado desde `mp-013-fastapi` (MP-013 `DONE`). Dispatchado a Codex (ejecutor) con énfasis explícito en calidad visual real (inspección en navegador, no solo tests), diferenciación clara de los cuatro estados de posición y arquitectura genérica multi-línea (ADR-0011) | `docs/TASKS.md`; `docs/STATUS.md` |
| `2026-11-19` | MP-014 | Implementación de Codex lista para revisión: `LineOut.geometry` aditivo/nullable (DEC-031), `apps/web` React/TypeScript/MapLibre genérico multi-línea, nulls y cobertura ausente explícitos, atribución OSM visible. Regresión Python 102/102; frontend lint/typecheck/3 tests/build en verde. Smoke real con GTFS oficial y poll fresco: 145 vehículos, 31 map-matched y cuatro estados simultáneos (24/2/4/1); runs del smoke retirados y PostgreSQL restaurado a `668/484/3/120/0`. Browser indisponible en la sesión Codex; por instrucción del coordinador, Claude ejecutará el gate visual desktop/estrecho/consola/interacciones antes de aprobar. Tarea pasa a `REVIEW`, no `DONE` | `apps/api/`; `apps/web/`; DEC-031/032; dispatch `ctx_878dc753a9a8` |
| `2026-11-19` | MP-014 | Primera revisión visual real de Claude: responsive/estados/nulls/atribución correctos, pero bloqueante en Vite dev (`maplibre-gl-worker.mjs` prebundled → `504`; corredor/estaciones invisibles) y menor de selector sin `id/name`. Codex aplica el fix confirmado diagnósticamente por Claude (`optimizeDeps.exclude: maplibre-gl`), añade `id`/`name`/`htmlFor`, comprueba módulo directo `200`, preview con API real (1 segmento/23 estaciones) y repite lint/typecheck/3 tests/build en verde. Producción no usa `.vite/deps`: worker empaquetado en chunk `MapView`. Queda en `REVIEW` para segunda pasada visual de Claude | `apps/web/vite.config.ts`; `apps/web/src/App.tsx`; dispatch `ctx_173c5fc5e12c` |
| `2026-11-19` | MP-014 | Segunda revisión visual de Claude confirma dev correcto y descubre el worker ausente en build/preview (la ruta devolvía fallback HTML). Codex emite el worker como asset explícito, fija su URL solo en producción y añade verificación byte a byte al build; lint/typecheck/3 tests/build en verde. Preview comprobado con worker `text/javascript` de 550.754 bytes y SHA-256 idéntico a la dependencia; API real devuelve el corredor. Queda en `REVIEW` para tercera pasada visual dev + preview de Claude | `apps/web/vite.config.ts`; `apps/web/src/MapView.tsx`; `apps/web/scripts/verify-build.mjs`; dispatch `ctx_2ce422035b3e` |
| `2026-11-19` | MP-014 | Tercera revisión visual de Claude confirma worker/dev, pero reproduce 2/2 una carrera menor de carga en frío que retrasa corredor/estaciones al siguiente poll. Codex sustituye listeners `once("load")` tardíos por readiness persistente y aplicación del último estado desde el handler inicial, registra errores MapLibre y añade regresiones jsdom; lint/typecheck/5 tests/build en verde y worker validado (550.754 bytes). Queda en `REVIEW` para cuarta pasada visual en varias pestañas nuevas de Claude | `apps/web/src/MapView.tsx`; `apps/web/src/MapView.test.tsx`; dispatch `ctx_180bdc48fbc5` |
| `2026-11-19` | MP-014 | Cuarta revisión visual de Claude: build de producción reconstruida, preview en tres pestañas nuevas e independientes (carga en frío) — 3/3 mostraron corredor/23 estaciones de inmediato, sin errores de consola. Dev revalidado, interacción del toggle "Trazado" comprobada. Las cuatro rondas de hallazgos quedan cerradas; MP-014 aprobada `DONE` por el revisor | commit `d4abedb`; `docs/TASKS.md`; `docs/STATUS.md` |

## Cómo usar este documento

Al empezar una tarea, comprobar aquí el hito autorizado y en `docs/TASKS.md` que sus dependencias directas están `DONE`. Ningún estado `DONE` se declara sin aprobación del revisor, y ningún test/verificación se reporta sin evidencia ejecutada.
