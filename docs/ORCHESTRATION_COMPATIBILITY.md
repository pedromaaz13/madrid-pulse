# ORCHESTRATION_COMPATIBILITY.md — Informe de compatibilidad de modelos y capacidades

**Fecha:** 2026-11-24 · **Elabora:** coordinador (`claude-sonnet-5-5` · medium) · **Método:** primero catálogo, configuración y recibos existentes; después **tres** despachos de solo lectura autorizados por el propietario. Ningún despacho modificó el repositorio ni bases de datos.

## 1. Sin worker (catálogo y configuración)
Fuente: `~/.codex/models_cache.json` (recuperado 2026-11-24T08:00Z, `codex-cli 0.171.0`) y `~/.codex/config.toml`.

| Modelo | Visibilidad / descripción oficial | Esfuerzos | Resultado |
|---|---|---|---|
| `gpt-6.2-sol` | list · "Fast, go-to model for coding and everyday work" | low…ultra | **vigente**; es también el default actual de la herramienta |
| `gpt-6.2-astra` | list · "Our most capable model for complex coding and professional work" | low…ultra | **vigente** |
| `gpt-6.1-terra` | list · "Efficient model that excels at visual understanding and computer use" | low…ultra | **vigente** |
| `gpt-6-luna` | list · "Fast and affordable model for easier tasks" | low…max | vigente (sin etiqueta Legacy) |
| `gpt-6-sol`, `gpt-6.1-sol`, `gpt-6-astra`, `gpt-5.6-sol/terra/luna` | list · "Legacy" / "Previous generation" | — | **no usar** en desarrollos nuevos |
| `gpt-reserve`, `codex-auto-review` | hide | — | no se usan |

Observación: el modelo por defecto de Codex cambió durante la auditoría H3 (`gpt-6-luna` → `gpt-6.2-sol`). Por eso la política exige `--model` explícito.
Claude: no hay catálogo local; `claude-sonnet-5-5`, `claude-opus-5-5` y `claude-haiku-5-5` constan en el entorno del coordinador. Orca acepta ids opacos (`worker-start --help`).
Recibos existentes: `worker-show --full` **no** expone modelo/esfuerzo; el recibo de `worker-start` solo repite lo solicitado. La identidad efectiva se comprobó mediante el **argv** del proceso mientras corría.

## 2. Despachos de prueba (3, solo lectura)
| Prueba | Despacho | Resultado |
|---|---|---|
| `claude-sonnet-5-5` · medium | `ctx_b1c8e4c5e6f6` | **Confirmado.** Recibo `model=claude-sonnet-5-5, effort=medium`; argv del proceso `--effort=medium --model=claude-sonnet-5-5`. El autoinforme "esfuerzo 5" no es fiable (no usar el autoinforme como evidencia). Sin herramientas de navegador cargadas (el MCP de Chrome DevTools figuraba "conectando"). |
| `claude-opus-5-5` · high | `ctx_4d8bee5c2567` | **Confirmado.** Recibo y argv `--effort=high --model=claude-opus-5-5`; autoinforme 15 = `high` en su escala interna. Sin navegador cargado por la misma razón. |
| `gpt-6.1-terra` · medium (navegador) | `ctx_49d421dfe418` | Despacho aceptado (recibo `gpt-6.1-terra`/`medium`). **Navegador NO disponible:** "No browser is available"; `agent.browsers.list()` = `[]`. No pudo abrir la página local de prueba ni generar captura. El runtime solo se declara "GPT-6"; el proceso ya no existía al comprobar argv, así que **la identidad efectiva de Codex no queda verificada de forma independiente**. |

El resultado de Terra coincide con 4 observaciones previas (MP-020, MP-021, MP-022, AUD-05): los workers de Codex lanzados por Orca no tienen navegador, aunque el plugin de navegador figura activado en la configuración de la aplicación Codex. Habilitar esa superficie implica ajustes de permisos del sistema: **no se intentó** y es decisión del propietario.

## 3. No probado (diferido a los primeros despachos reales)
`gpt-6.2-sol`, `gpt-6.2-astra`, `claude-haiku-5-5`, `gpt-6-luna`: catálogo confirmado para los de Codex; sin incompatibilidad demostrada. Se verificará recibo + argv (capturado durante la ejecución) en el primer despacho de cada uno.

## 4. Comprobaciones de seguridad del propio ensayo
- Base 5433 sin cambios: `max(source_ingestion_run.id) = 3095`, 126 filas (igual que antes de las pruebas).
- `git status` limpio en el worktree de auditoría tras las pruebas; el único artefacto fue una página HTML de prueba en el scratchpad de la sesión (sin PNG).

## 5. Consecuencias para la política
1. `gpt-6.1-terra` **no** se asigna a frontend/validación visual mientras no haya navegador utilizable en workers de Orca.
2. Las tareas visuales se ejecutan con Claude + Chrome DevTools (con *preflight* de que la herramienta existe), y la revisión de Codex audita código y artefactos declarando que no tiene navegador; el coordinador reproduce los puntos decisivos.
3. La identidad efectiva se captura del argv **durante** la ejecución; el autoinforme del modelo no cuenta.
4. Capturar la identidad efectiva de Codex requiere leer el argv mientras el worker está vivo; si no es posible, se registra "solo recibo de Orca".
