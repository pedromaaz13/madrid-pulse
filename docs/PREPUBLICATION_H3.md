# PREPUBLICATION_H3.md — Controles previos a publicar la integración H3

**Fecha:** 2026-11-24 · **Rama:** `integration/h3-audited` (HEAD tras este documento: ver `git rev-parse`) · **Estado:** propuesta; nada se ha empujado, abierto como PR ni fusionado. El repositorio es **público** (decisión del propietario).
**Veredicto de producto sin cambios:** NO-GO para despliegue público; CONDITIONAL GO para el código local integrado; FR-01 y FR-02 abiertos.

## 1. Secretos (decisión 3)
Gitleaks 8.30.1 (fórmula `homebrew-core`, MIT, código fuente `github.com/gitleaks/gitleaks`, SHA-256 de la fuente `e90fb266…9eaf9abb`). Ejecutado con `--redact` sobre: historial completo de `integration/h3-audited` (160 commits), rango nuevo (99 commits) y árbol de trabajo, antes de los commits documentales `308d950` y de este documento (solo texto; repetir el escaneo al final, ver §8). **0 hallazgos.** Sustituye al escaneo previo por patrones. Credencial presente por diseño: `POSTGRES_PASSWORD=madrid_pulse_local` (contenedores desechables locales; en `infra/docker/docker-compose.yml`, `ci.yml`, un doc de evidencia). No es un secreto; no se reutiliza fuera de entornos desechables.
Límite: Gitleaks no detecta datos personales no secretos (ver §4).

## 2. Licencias y obligaciones (decisión 2) — **LICENSE no añadida**
Recomendación: **MIT** para el código propio. No hay incompatibilidad que lo impida, con las salvedades siguientes, que deben quedar visibles en un `NOTICE`/README al añadirla.

| Material | Licencia | Efecto sobre MIT | Acción |
|---|---|---|---|
| Dependencias Python directas y transitivas instaladas (pydantic, duckdb, fastapi, starlette, uvicorn, httpx, anyio, h11, click…) | MIT / BSD-3 / PSF-2.0 | compatibles | ninguna |
| `psycopg` 3.3.9 + `psycopg-binary` | **LGPL-3.0** | compatible: se usa como dependencia instalada vía pip, no se incluye ni se modifica su código | no vendorizar ni modificar; mantener como dependencia externa |
| `certifi` | MPL-2.0 | compatible (dependencia externa) | ninguna |
| npm (lockfile, 277 paquetes): MIT 202, ISC 19, Apache-2.0 17, MPL-2.0 12 (14 entradas `lightningcss*`, solo dev), BSD 16, BlueOak 5, otras permisivas; `caniuse-lite` CC-BY-4.0 (dev) | permisivas/débilmente copyleft de archivo | compatibles; ninguna es AGPL/GPL | si se redistribuye el bundle (`dist`) incluir avisos de MapLibre/dependencias de runtime |
| Fixtures OSM (`tests/fixtures/osm_c5_real`, `osm_c4_real`) | **ODbL-1.0** (share-alike, DEC-024) | **no se cubren con MIT**: son bases derivadas que siguen ODbL | el `LICENSE` debe decir expresamente que `tests/fixtures/osm_*` y los datos OSM no son MIT |
| GTFS/GTFS-RT Renfe y fixtures derivadas | CC BY 4.0 (atribución "Origen de los datos: Renfe Operadora") | no se relicencian | atribución en README/NOTICE; el ZIP GTFS no se versiona (`data/` fuera de Git) |
| GTFS CRTM | CRTM-LDA (mismo tipo de licencia al compartir datos CRTM; "Powered by CRTM") | no se relicencian | atribución; revisar si alguna fixture contiene datos CRTM antes de publicar |
| Via Península | AGPL-3.0 | **sin impacto**: solo estudio conceptual, sin código copiado (NOGO-002) | mantener |
| Teselas | `https://tile.openstreetmap.org` en `apps/web/src/map/MapView.tsx:195` | la política de uso de OSM **no admite uso en producción intensivo**; atribución ODbL visible en el mapa (verificada en capturas) | **bloquea despliegue público** (ya figura como gate de H4-10); no bloquea publicar el código |
| Kit instalado (`docs/hitos/hito-03/…`, prototipos) | autoría propia/del propietario; sin licencia de terceros hallada | cubierto por el aviso del repositorio | confirmar con el propietario que es material suyo |

**Incompatibilidades bloqueantes: ninguna.** Decisiones para el propietario antes de añadir `LICENSE`: (a) MIT (recomendada) frente a Apache-2.0 (concesión explícita de patentes; algo más de texto); (b) titular del copyright en la cabecera (no lo asumo); (c) aceptar la cláusula de exclusión de materiales de terceros.

## 3. Capturas (decisión 5)
46 PNG (28 de auditoría, 14+ de MP-020/021, 4 de diseño), 62,5 MiB de blobs en el historial. Revisadas visualmente por muestreo representativo (Live escritorio, móvil 390, búsqueda, caída de fuente, Explore) y por metadatos: **0 PNG con metadatos tEXt/iTXt/eXIf**; son solo el viewport de la aplicación (sin barra del navegador, sesión, cookies ni cuentas); contienen solo datos públicos de Renfe y teselas OSM con atribución visible (en recortes con zoom aparece el icono de atribución). Límite: no inspeccioné cada una de las 46 a resolución completa (muestreo de 5 capturas de tipos distintos + el resto agrupado por tipo y nombre; el propietario habló de 42, el inventario real es 46 incluidos los 4 diseños del kit); repetir en pantalla antes del push si se quiere revisión exhaustiva.
**Impacto de eliminar o sustituir:** los PNG pesados entran en MP-020 (`5f8b739`/`2728e02`); reescribir su aparición cambia el SHA de **77 de los 100 commits** nuevos, incluido `beb9434` (baseline de regresión de H4 y citado en todos los informes de la auditoría) y toda la cadena de worktrees. Borrarlos en un commit nuevo no reduce el clon (siguen en el historial). **Recomendación: no reescribir.** 62,5 MiB y ficheros ≤4,4 MiB están por debajo de los límites de GitHub (100 MiB por fichero). Opcional posterior: archivo de originales como artefacto externo y, en commits nuevos, versiones optimizadas — requiere tu decisión; **no se ha hecho nada**.

## 4. Rutas locales y datos personales (decisión 4)
Commit `308d950`: 11 rutas absolutas en 10 documentos sustituidas por marcadores (`<WORKTREES>`, `<REPO_LOCAL>`, `<SCRATCHPAD>`); solo cambia el texto de rutas. `INTEGRATION_PROPOSAL.md` (citado por AUD-09) cambió solo en esas rutas. El **historial anterior conserva** las rutas originales (se descarta reescribir). El nombre de usuario del sistema revelado es el del propietario; no son credenciales.
**Dato personal a decidir:** 158 commits usan `pedromaaz13@gmail.com` como autor y 4 el correo `noreply` de GitHub. Al publicar, el correo personal queda visible permanentemente en el historial. Es la decisión de identidad del propietario; si se quiere ocultar, hay que **reescribir autoría** (cambia todos los SHA; no se propone). Alternativa sin reescritura: activar "Keep my email private" solo protege commits futuros.

## 5. Scripts, kit y duplicados (decisión 6)
- `scratch/` (22 scripts `aud0*_*.py` + `scratch/aud04_web/shapes.test.ts`): **se conservan**; 9 informes los citan por ruta como evidencia reproducible. Mover a `docs/audits/hito-03/scripts/` cambiaría rutas citadas; recomendado solo con un commit de actualización de referencias — no lo hago ahora.
- `docs/hitos/hito-03/referencia/historico-v2` y `historico-v3`: comparados con `cmp`; los 4 ficheros homónimos **difieren** (v2 ≠ v3) y `MATRIZ-CIERRE-MADRID.md` de v2 es prefijo de v3. No son duplicados exactos; `VERIFICACION-KIT.md` y `REVISION-Y-DECISIONES.md` los referencian. **No se elimina nada.** Los 3 avisos de espacios finales de `git diff --check` afectan a este kit; se dejan (documentos históricos).

## 6. CI (decisión 9)
`.github/workflows/ci.yml` se dispara en `push` a `main` y en `pull_request`; jobs `python` (PostGIS 17-3.5, migraciones, 28 módulos) y `frontend` (Node 22.13.1: `npm ci`, lint, typecheck, test, build).
**Simulación local, no es GitHub Actions:** `git archive HEAD` (sin `data/`), contenedor PostGIS desechable en el puerto 55439 (no 5433), migraciones 0001+0002, los 28 módulos del workflow: **283 tests, OK, 18 skipped** (esperado). Frontend: 89/89, lint, typecheck, build verificados antes en el worktree. **Solo una ejecución real del workflow sobre el PR demuestra CI en verde**; el último verde en `main` es de 2026-11-20 y no cubre el código de H3.

## 7. Integración Git (decisión 8)
- GitHub ofrece "Create a merge commit", "Squash" y "Rebase"; **squash y rebase reescriben SHAs** (descartados). No existe fast-forward en la interfaz.
- Opción A (recomendada): push de la rama `integration/h3-audited` a `origin`, PR contra `main` (CI corre sobre el código H3), revisión humana y, **tras CI verde**, o bien "Create a merge commit" (crea un commit de fusión; conserva los 100 commits y sus SHA) o bien fast-forward por línea de comandos `git push origin integration/h3-audited:main` (historial lineal; GitHub marca el PR como fusionado). Con el fast-forward, `main` queda sin commit de fusión. `main` no tiene protecciones, el push directo sería posible; usarlo solo tras el PR revisado.
- Opción B (si A se complica): merge commit desde la interfaz. Sin impacto en SHA.
Impacto en el historial: **ninguno** (no se reescribe nada); 100 commits nuevos sobre `990c95d`.

## 8. Secuencia exacta propuesta (cada paso requiere tu autorización explícita)
0. Gitleaks repetido sobre `4637153` (historial completo + árbol): 0 hallazgos; repetir si se añaden commits.
1. Decidir licencia/titular y correo (§2, §4) → commit documental `LICENSE` + `NOTICE` (no hecho).
2. `git push -u origin integration/h3-audited` (publica 100 commits; repositorio público).
3. Abrir PR `integration/h3-audited` → `main` con título y cuerpo que declaren NO-GO público; esperar CI real (python + frontend).
4. Revisión humana del PR; si CI falla, corregir en la misma rama (commits nuevos).
5. Integrar: merge commit (UI) o `git push origin integration/h3-audited:main` (ff).
6. Ramas de trabajo (`mp-016…022`, `audit/hito-03-adversarial`, `chore/h4-planning`) se mantienen; `main` = base de H4. **H4 no empieza** sin tu autorización del alcance y la matriz.
No hay despliegue en ningún paso.
