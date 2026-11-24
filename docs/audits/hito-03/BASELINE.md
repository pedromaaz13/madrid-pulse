# AUD-00 — Baseline real del Hito 3 y verificación de entorno

**Ejecuta:** Claude Sonnet (coordinador, actuando directamente — ver nota de alcance al final)
**Revisa:** Codex Terra · Medium (pendiente, dispatch en curso)
**Fecha:** 2026-11-23
**Rama de auditoría:** `audit/hito-03-adversarial`, creada desde `mp-022-validacion-integrada` @ `beb9434`
**Worktree:** `<WORKTREES>/audit-hito-03`

No se ha modificado código funcional, base de datos ni contratos. Este documento registra solo hechos verificados con comandos reales, reproducibles por cualquiera que tenga este repositorio.

---

## 1. HEAD real de la cadena MP-016 → MP-022

Comando: `git worktree list` + `git log -1 --format='HEAD %h %ci'` en cada worktree, 2026-11-23.

| Tarea | Rama | HEAD | Commit (fecha) | `git status --short` |
|---|---|---|---|---|
| MP-016 | `mp-016-fiabilidad-live` | `92c1b09` | 2026-11-22 03:22:37 +0100 | limpio |
| MP-017 | `mp-017-catalogo-madrid` | `c28d5e4` | 2026-11-22 03:53:36 +0100 | limpio |
| MP-018 | `mp-018-corredores-madrid` | `728c667` | 2026-11-22 04:29:13 +0100 | limpio |
| MP-019 | `mp-019-snapshot-api` | `7b87e6b` | 2026-11-22 17:38:52 +0100 | limpio |
| MP-020 | `mp-020-mapa-y-tablero` | `b616ae6` | 2026-11-22 23:16:20 +0100 | limpio |
| MP-021 | `mp-021-historico` | `1ecbc8f` | 2026-11-23 11:34:18 +0100 | limpio |
| MP-022 | `mp-022-validacion-integrada` | `beb9434` | 2026-11-23 12:31:26 +0100 | limpio |

**Verificación de encadenamiento real** (no solo fechas crecientes — ascendencia Git real), `git merge-base --is-ancestor <a> <b>`:

```
main (990c95d) → 92c1b09 (MP-016) → c28d5e4 (MP-017) → 728c667 (MP-018)
→ 7b87e6b (MP-019) → b616ae6 (MP-020) → 1ecbc8f (MP-021) → beb9434 (MP-022)
```

Las seis comprobaciones consecutivas y la comprobación contra `main` devolvieron `OK`. **La rama final `mp-022-validacion-integrada` contiene realmente el trabajo encadenado de las siete tareas** — no es una rama paralela ni reescrita.

**Remoto:** `git ls-remote --heads origin` (GitHub, `pedromaaz13/madrid-pulse`) no devuelve ninguna de las siete ramas `mp-016`→`mp-022`: el Hito 3 existe **solo en local**, confirmando la instrucción de no auditar únicamente `origin/main`.

**Autoría:** verificada en turnos anteriores de esta sesión, commit a commit, en las 7 ramas: exclusivamente `Pedro Matute <pedromaaz13@gmail.com>`, sin `Co-authored-by`. No reverificado de nuevo en este documento — ver `docs/CHANGELOG.md`/`docs/STATUS.md` de cada worktree para el detalle commit a commit ya registrado al cierre de cada tarea.

---

## 2. Verificación de modelos y esfuerzo disponibles (obligatoria antes de cualquier despacho)

### Claude (vía Orca)

Confirmado en esta sesión y en el cierre de Hito 2 (`docs/STATUS.md`, sección "Política de selección de modelo"): los identificadores reales soportados por `orca orchestration worker-start --model <id> --effort <level>` para Claude son `sonnet` y `opus`. La guía de la skill `orchestration` (`orca skills get orchestration --full`) confirma niveles de esfuerzo reales para Claude Opus 5.5: `low=5, medium=10, high=15, xhigh=40` (escala interna de razonamiento, no 0-100) — **`medium` y `high` son ambos niveles reales**, no inventados.

El prompt de esta auditoría pide "Claude Sonnet Medium" como coordinador y "Claude Opus High"/"Claude Sonnet High" para tareas específicas: **ambos combinaciones son reales y soportadas**, sin alternativa necesaria.

### Codex (vía Orca)

Comando: `codex --help`, `cat ~/.codex/config.toml`, `cat ~/.codex/models_cache.json`.

**Hallazgo real que el propietario debe conocer antes de aprobar el despacho:** los tres identificadores que pide el prompt (`gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`) **sí existen** como slugs reales y seleccionables (`"visibility": "list"` en `models_cache.json`, obtenido del backend de OpenAI, no inventado por mí) — pero los tres están marcados explícitamente como **modelos "Legacy"** en su propia metadata:

| Slug | Nombre | Descripción oficial | Esfuerzo por defecto | Niveles soportados |
|---|---|---|---|---|
| `gpt-5.6-sol` | GPT-5.6-Sol | *"Legacy model for coding and everyday work."* | `low` | low, medium, high, xhigh, max, ultra |
| `gpt-5.6-terra` | GPT-5.6-Terra | *"Legacy balanced model for agentic coding."* | `medium` | low, medium, high, xhigh, max, ultra |
| `gpt-5.6-luna` | GPT-5.6-Luna | *"Legacy fast model for simpler tasks."* | `medium` | low, medium, high, xhigh, max |

El modelo configurado por defecto en este entorno (`~/.codex/config.toml`: `model = "gpt-6-luna"`) pertenece a una generación **posterior** que ni siquiera aparece en este mismo `models_cache.json` — es decir, hay una familia `gpt-6-*` más nueva disponible en esta instalación, que el propio prompt de esta auditoría **prohíbe explícitamente usar** ("No utilizar... `gpt-6.*`...").

**Decisión tomada, dentro de lo ya autorizado por el propio prompt:** uso `gpt-5.6-sol`/`gpt-5.6-terra`/`gpt-5.6-luna` tal cual se pidieron — son reales y seleccionables, y el prompt ya excluyó explícitamente la alternativa más nueva (`gpt-6.*`). No se trata de una alternativa degradada por mi parte: es la selección literal del propietario, verificada como real en vez de asumida. Registro aquí, como exige el propio protocolo, que son "legacy" según el proveedor — si el propietario prefiere la familia `gpt-6.*` a pesar de su instrucción previa, es una decisión suya, no mía.

`gpt-reserve` (visibility `hide`, "Fast and affordable agentic coding model") y `codex-auto-review` (visibility `hide`) también existen pero no se pidieron ni se usan.

**Esfuerzo:** uso minúsculas verificadas (`low`/`medium`/`high`/`xhigh`/`max`/`ultra`), no las mayúsculas del prompt ("Medium"/"High"), que no son el formato real del parámetro.

### EGM (Elephant-Goldfish Model)

Comando: `which egm`, `find ~ -iname "*elephant-goldfish*"`, `pip show elephant-goldfish-model`.

**Resultado: no instalado en este entorno.** No hay binario, carpeta ni paquete Python con ese nombre en el sistema. Conforme a la instrucción explícita del propietario ("No instales software externo... sin autorización", "No afirmes que has ejecutado EGM si no has comprobado su funcionamiento"):

- **No se instalará EGM sin autorización explícita.**
- AUD-07 se ejecutará como una **revisión adversarial equivalente con un worker en contexto nuevo**, etiquetada expresamente como "no constituye una ejecución oficial de EGM" — tal como el propio prompt prevé para este caso exacto.

---

## 3. Qué significa esto para el resto de la auditoría

- La baseline de código/documentación es real y verificable: las siete ramas están donde dicen estar, encadenadas de verdad, limpias de cambios sin commitear.
- Los despachos a Codex de esta auditoría usarán `--model gpt-5.6-sol|gpt-5.6-terra|gpt-5.6-luna --effort <low|medium|high|xhigh|max|ultra>` exactamente como pide el prompt, con la salvedad documentada de que el proveedor los califica como "legacy" — un hecho a tener en cuenta si alguna auditoría posterior rinde peor de lo esperado y hay que decidir si vale la pena repetirla con la familia más nueva (decisión del propietario, no mía).
- AUD-07 (EGM) se ejecutará como equivalente no oficial, nunca presentado como "EGM real".
- Ningún agente ha tocado código de producto, migraciones, datos persistentes ni ha hecho `push`/PR/merge. Esta rama (`audit/hito-03-adversarial`) contiene y contendrá solo documentación de auditoría.

**Próximo paso:** dispatch de Codex Terra · Medium para revisar este documento de forma independiente (reproducir las comprobaciones de ascendencia Git y confirmar la lectura de `models_cache.json`) antes de declarar AUD-00 `DONE` y empezar AUD-01/AUD-02/AUD-05.
