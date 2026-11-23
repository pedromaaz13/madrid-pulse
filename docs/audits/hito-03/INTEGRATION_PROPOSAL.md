# Propuesta de integración del Hito 3 (solo propuesta; sin push, PR ni merge)

**Fecha:** 2026-11-23 · **Elabora:** coordinador. Ningún agente ha ejecutado `git push`, PR ni merge, ni lo hará. Las decisiones y comandos son del propietario.

## 1. Estado de ramas (HEAD reales verificados con `git rev-parse`)

| Orden | Rama | HEAD | Depende de |
|---|---|---|---|
| 0 | `main` | `990c95d` | — |
| 1 | `mp-016-fiabilidad-live` | `92c1b09` | main |
| 2 | `mp-017-catalogo-madrid` | `c28d5e4` | MP-016 |
| 3 | `mp-018-corredores-madrid` | `728c667` | MP-017 |
| 4 | `mp-019-snapshot-api` | `7b87e6b` | MP-018 |
| 5 | `mp-020-mapa-y-tablero` | `b616ae6` | MP-019 |
| 6 | `mp-021-historico` | `1ecbc8f` | MP-020 |
| 7 | `mp-022-validacion-integrada` | `beb9434` | MP-021 |
| A | `audit/hito-03-adversarial` | ver `git rev-parse` al integrar (HEAD vivo; actualmente `0e95eda` o posterior) | MP-022 (`beb9434`) |

Encadenamiento comprobado con `git merge-base --is-ancestor` (AUD-00, revisado por Codex): cada HEAD es ancestro del siguiente y `main` es ancestro de MP-016. Ninguna rama está en `origin`.

## 2. Opciones de integración
- **Opción 1 (recomendada para el código del hito):** un único PR `mp-022-validacion-integrada` → `main`. Al ser `main` ancestro directo, el historial de las siete tareas entra completo y lineal (fast-forward posible). Un solo punto de revisión; se pierden los PR por tarea.
- **Opción 2:** siete PR secuenciales, uno por rama, cada uno contra `main` tras fusionar el anterior. Más trazabilidad por tarea, más trabajo y siete ejecuciones de CI.
- **La rama de auditoría (A):** integrarla **aparte y después**, o mantenerla fuera de `main`. Contiene documentación (`docs/audits/hito-03/`, `docs/audits/hito-03/capturas/`) y **scripts de diagnóstico en `scratch/`** (22 ficheros `aud0*_*.py`); recomiendo **no fusionar `scratch/`** (reproducibilidad de la auditoría sí, pero no es código de producto) o moverlo a `docs/audits/hito-03/scripts/`.

## 3. Pruebas asociadas (reejecutadas de forma independiente en el cierre)
- Python (lista exacta de `.github/workflows/ci.yml` en MP-022): **283 tests OK**; los skips dependen del entorno (1, 5 o 18 según base y presencia de `data/` — ver AUD-08). En CI real con checkout limpio sin `data/`: 283 OK con 18 skips (13 por el ZIP GTFS).
- Frontend Node 22.13.1: **89/89**, lint, typecheck y build (worker MapLibre 550 754 B).
- La verificación "sin skips contra la base de desarrollo 5433" **ya no reproduce** por el incidente documentado en `INCIDENT_5433.md`.

## 4. Riesgos de integrar
1. **Fusionar no equivale a publicar.** La auditoría confirma P0/P1 de producto (movimiento pre-salida y post-llegada, cobertura de geometría 28/103, `unknown` en replay, carrera de snapshot). Integrar en `main` deja esos defectos en la rama principal; recomiendo etiquetarlo como "hito local cerrado, no apto para publicación" hasta el veredicto de AUD-09.
2. **Migración `0002_api_batch_indexes`**: solo estructuras de acceso; con rollback seguro, pero hay que aplicarla antes de usar la API del hito.
3. **ADR-0014 y ADR-0015 siguen `Propuesto`**; integrar no los acepta. Tu decisión.
4. **Valores por defecto apuntan a 5433** (`services/collector/config.py`, `apps/api/config.py`): riesgo operativo ya materializado en el incidente.
5. **Datos fuera de Git** (`data/hito-03/`, `data/parquet/`): quien clone debe reponerlos con `instalar.py --solo-datos`.
6. **`git diff --check main...mp-022-validacion-integrada` da 3 avisos de espacios finales** (4 líneas), todos en documentos del kit instalado bajo `docs/hitos/hito-03/referencia/` (`04-ux-plan-original.md`, `historico-v3/REVISION-Y-DECISIONES.md`, `PROMPT-UNICO-ORCA.md`, `MEJORAS-PRODUCTO-VALIDADAS.md`). No son código; los cierres por tarea comprobaron el delta propio de cada commit, no el rango completo. No bloquea, pero un PR con comprobaciones estrictas los mostrará.
7. **Autoría:** todos los commits son `Pedro Matute <pedromaaz13@gmail.com>`, sin coautores; conviene comprobarlo antes del push (`git log --format='%an %ae %b' main..mp-022-validacion-integrada | grep -ci co-authored` debe dar 0).

## 5. Comprobaciones previas recomendadas al propietario antes de empujar
```bash
git -C /Users/matu/Documents/DATA/madrid-pulse log --format='%an <%ae>' main..mp-022-validacion-integrada | sort -u
git -C /Users/matu/Documents/DATA/madrid-pulse log main..mp-022-validacion-integrada | grep -ci 'co-authored-by'
git -C /Users/matu/Documents/DATA/madrid-pulse diff --check main...mp-022-validacion-integrada   # hoy: 3 avisos en docs del kit
```
