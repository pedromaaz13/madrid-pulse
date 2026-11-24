# Propuesta de integración del Hito 3 en `main` (versión verificada, 2026-11-24)

**Complementa** `docs/audits/hito-03/INTEGRATION_PROPOSAL.md` (versión del coordinador del 2026-11-23, que se conserva intacta porque AUD-09 la citó; sus HEAD y notas quedaron desactualizados). **Ningún agente ha hecho ni hará `git push`, PR ni merge.** Todo lo de abajo son comprobaciones de solo lectura o locales y una secuencia propuesta para tu autorización.

## 1. Rama de integración propuesta
`integration/h3-audited` = `chore/h4-planning` (`ce05316`) + **3 commits documentales** (sección 6). Contiene: código `MP-016`→`MP-022` (`beb9434`), documentos y scripts de la auditoría (`acb5749`) y la política de orquestación/matriz H4 (`ce05316`).

## 2. Ancestralidad real (`git merge-base --is-ancestor`)
`main(990c95d)` → `mp-016` → `mp-017` → `mp-018` → `mp-019` → `mp-020` → `mp-021` → `mp-022 (beb9434)` → `audit/hito-03-adversarial (acb5749)` → `chore/h4-planning (ce05316)` → `integration/h3-audited`: **las nueve comprobaciones consecutivas dan OK; 0 commits de merge; historia 100 % lineal** (96 commits sobre `main`). `main` local = `origin/main` = `990c95d`.
⇒ La integración es posible por **fast-forward**, conservando todos los SHA.

## 3. Diffs
`main...chore/h4-planning`: 285 ficheros, +64 181 / −1 198. Entre `beb9434` y `ce05316` **no cambia ningún fichero fuera de `docs/` y `scratch/`** (comprobado): el código funcional es exactamente el aprobado en MP-022. Nuevos: 48 ficheros `apps/web`, 42 `docs/audits` (informes + 42 capturas PNG, 61,8 MB), 34 kit `docs/hitos/hito-03`, 32 `docs/evidence`, 13 fixtures, 9 `infra/operate`, `scratch/` (23 ficheros).

## 4. Tests (sobre `ce05316`, PostgreSQL 17-3.5 desechable propio en 5441, migraciones 0001+0002 desde cero; nunca 5433)
- Python, lista exacta de `.github/workflows/ci.yml` (28 módulos): **283 OK, 5 skips** (con `data/` del kit y una sola URL de BD). En un checkout limpio sin `data/`, lo que verá GitHub Actions: 283 OK con **18 skips** (13 por el ZIP GTFS oficial) — reproducido por AUD-08.
- Frontend, Node 22.13.1: `npm ci`, eslint (0 avisos), `tsc -b`, **89/89** vitest, build OK, worker MapLibre **550 754 B**.
- La verificación histórica «sin skips contra desarrollo (5433)» ya no reproduce (`INCIDENT_5433.md`).
- `main` tuvo CI verde el 2026-11-20; **el CI de GitHub no ha ejecutado nunca el código del Hito 3** (primera ejecución real al empujar): riesgo de diferencias de entorno no vistas en local.

## 5. Visibilidad, licencia y secretos
- **El repositorio `pedromaaz13/madrid-pulse` es PÚBLICO** (`gh repo view`: `visibility: PUBLIC`, último push 2026-11-20) y **no tiene licencia** (`licenseInfo: null`, sin fichero `LICENSE`). Todo lo que se empuje queda público. DEC-002 (licencia) y DEC-003 (visibilidad) seguían «pendientes» en los documentos: **la visibilidad ya es pública de hecho**. Sin licencia, el código queda con todos los derechos reservados por defecto y las fixtures OSM siguen obligadas por ODbL (`docs/legal/`). `main` no tiene protección de rama.
- **Escaneo de secretos** (NV-14): no hay `gitleaks`/`trufflehog`/`detect-secrets` instalados y **no se instalan sin tu autorización**; se hizo un escaneo por patrones sobre las 65 432 líneas añadidas en `main..ce05316`: **0** claves privadas, AWS, tokens GitHub/Slack/Google/OpenAI/Anthropic, JWT/Bearer. Únicos hallazgos genéricos, todos locales y de prueba: `madrid_pulse_local` y `aud06_local` (contraseñas de contenedores desechables y defaults de desarrollo que ya figuran en `main`). Correo en el contenido: solo el tuyo de autoría (`pedromaaz13@gmail.com`, ya en el historial público); el otro correo de tu cuenta no aparece. Ficheros sensibles/generados (`.env`, `.dump`, `.parquet`, `.zip`, `.sqlite`, `__pycache__`, `.log`): **ninguno versionado**; `.gitignore` los cubre. El dump de 5433 no está en el repo. **Limitación:** es un escaneo por patrones, no un escáner dedicado; se puede repetir con uno si lo autorizas.
- **Rutas locales:** `/Users/matu/orca/...` y `/Users/matu/Documents/...` aparecen en 9 documentos (informes de auditoría, log, plantilla). Revela el nombre de usuario del equipo; no son credenciales. **No se han modificado** porque forman parte de los resultados de la auditoría; si prefieres redactarlas, es un commit documental aparte que decides tú.
- **`scratch/` (23 ficheros, 22 scripts Python + 1 vitest):** revisados: sin credenciales, sin llamadas de red, sin DSN a 5433, sin rutas locales; son los comandos reproducibles que citan los informes (moverlos obligaría a editar rutas citadas en documentos aprobados). **Se conservan en `scratch/`**; no entran en CI ni en el lint (`apps/web` solo lintea su carpeta; CI lista módulos explícitos).
- **Capturas:** 42 PNG de la auditoría (61,8 MB; el mayor 4,4 MB, bajo el límite de GitHub); `main` no tiene PNG hoy. Se conservan como evidencia; optimizarlas o llevarlas a una *release* es decisión tuya.
- Kit instalado (`docs/hitos/hito-03/`, 34 ficheros): texto de tus propios encargos y un prototipo HTML/PNG propio; las referencias a Via Península y Valfiguer son análisis conceptual (sin código copiado). Es decisión tuya si lo quieres público.

## 6. Cambios documentales de integración (únicos; ninguno altera resultados ni código)
| Commit | Qué cambia | Por qué |
|---|---|---|
| `b93b856` | `README.md`: aviso superior «versión local auditada — NO-GO para despliegue público» con enlace a la decisión; `docs/STATUS.md`: bloque de integración | Requisito 7: los P0 no se ocultan. El resto del README sigue desactualizado (FR-11) y se declara en el propio aviso |
| `f1416ce` | `docs/H4_MP_MAPPING.md` (nuevo), referencia en `docs/H4_TASK_MATRIX.md`, `DEC-043` (conservar 5433) y `DEC-044` (política y numeración) en `docs/DECISIONS.md` | Numeración `MP-023+` con correspondencia `H4-xx`; registrar tus decisiones |
| (este commit) | este documento (`docs/INTEGRATION_H3_VERIFIED.md`) | resultados verificados; no toca `INTEGRATION_PROPOSAL.md` de la auditoría |
No se tocó: informes AUD, `scratch/`, código, kit, ADR, TASKS de hitos cerrados, registros de modelos históricos. ADR-0014/0015 siguen `Propuesto`.

## 7. Riesgos de integrar
1. **Publicación inmediata de todo** (repo público) incluyendo informes que describen P0 abiertos: es coherente con el aviso, pero es información pública sobre defectos.
2. **Primer CI real del Hito 3** puede fallar por entorno (p. ej. 18 skips, Node, caché).
3. **README** sigue contradiciendo el estado real fuera del aviso superior (FR-11).
4. **Sin licencia** (DEC-002) y teselas OSMF sin política registrada (FR-12).
5. **Squash o «Rebase and merge»** destruirían los SHA y la cadena de ramas: usar *fast-forward* o *merge commit*, **nunca squash**.
6. Rutas locales y capturas pesadas en historia pública (no reversible sin reescribir historia).

## 8. Secuencia exacta propuesta (para tu autorización; nada se ejecuta hasta entonces)
```bash
cd /Users/matu/Documents/DATA/madrid-pulse
# 0. Estado previo (solo lectura)
git status --short                                   # limpio
git fetch origin && git rev-parse main origin/main   # ambos 990c95d
git log --format='%an <%ae>' main..integration/h3-audited | sort -u        # solo Pedro Matute
git log main..integration/h3-audited | grep -ci 'co-authored-by'           # 0
git diff --check main...integration/h3-audited      # 3 avisos en docs del kit (ya conocidos)

# Opción A (recomendada): PR revisable, historia lineal conservada
git push -u origin integration/h3-audited
gh pr create --base main --head integration/h3-audited --title "Hito 3 (MP-016..MP-022) + auditoría adversarial + política H4 — versión local auditada, NO-GO público" --body-file <cuerpo que apruebes>
#   esperar CI; fusionar con «Create a merge commit» (conserva todos los SHA). NO usar «Squash» ni «Rebase and merge» (reescriben SHA).

# Opción B: fast-forward local y push directo (main no tiene protección)
git switch main && git merge --ff-only integration/h3-audited && git push origin main
```
Después (con tu aprobación): etiquetar `h3-local-audited` en el HEAD fusionado; base del Hito 4 = `main`; **no** desarrollar H4 sobre `chore/h4-planning`.

## 9. Qué necesito de ti para integrar
1. Autorización expresa del push/PR/merge y de la opción (A o B).
2. ¿Se mantiene el repo **público**? Si no, cambiar visibilidad **antes** de empujar.
3. ¿Aceptas publicar sin licencia (DEC-002 pendiente) o decides una antes?
4. ¿Redactar las rutas locales de los informes (commit documental aparte) o dejarlas?
5. ¿Repetir el escaneo con un escáner dedicado (requiere instalarlo, tu autorización)?
6. Capturas: dejar tal cual (61,8 MB) u optimizar/llevar a *release*.
7. Kit `docs/hitos/hito-03/`: ¿público o excluido de `main`?
