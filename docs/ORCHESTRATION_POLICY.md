# ORCHESTRATION_POLICY.md — Política de orquestación de agentes (Hito 4 en adelante)

**Estado:** BORRADOR para aprobación del propietario. No entra en vigor hasta que lo apruebe.
**Alcance:** hitos nuevos (H4+). **No reescribe** los registros históricos de modelos de los hitos 1–3 ni de la auditoría H3 (`docs/audits/hito-03/ORCA_DISPATCH_AND_REVIEW_LOG.md` y los `STATUS.md`/`TASKS.md` de cada tarea): allí constan los modelos realmente usados (`gpt-5.6-*`, `sonnet`/`opus`, etc.).
**Precedencia:** `AGENTS.md` y `CLAUDE.md` mandan sobre este documento; las decisiones del propietario mandan sobre todo.
**Evidencia de compatibilidad:** `docs/ORCHESTRATION_COMPATIBILITY.md`.

## 1. Modelos y esfuerzos

Los identificadores se pasan **siempre explícitos** a `orca orchestration worker-start --model <id> --effort <level>`; nunca se confía en el modelo por defecto de la herramienta (el de Codex cambió de `gpt-6-luna` a `gpt-6.2-sol` durante la auditoría H3).

| Rol | Modelo · esfuerzo | Uso |
|---|---|---|
| Coordinador | `claude-sonnet-5-5` · medium | despacho, dependencias, registro, verificación puntual. Sube a high solo para resolver contradicciones entre informes. |
| Arquitectura crítica y revisión adversarial | `claude-opus-5-5` · high | ADR, decisiones complejas, revisión de P0 y de geometría/movimiento |
| Ingeniería habitual | `gpt-6.2-sol` · medium | backend, SQL, colector, API, operación, documentación técnica |
| Debugging complejo y revisión de código | `gpt-6.2-sol` · high | fallos difíciles, regresiones, revisión de diffs |
| Geometría ferroviaria, movimiento y lógica temporal críticos | `gpt-6.2-astra` · high | ver §2 sobre escalado |
| Frontend y validación visual | `gpt-6.1-terra` · medium/high **solo si** se confirman navegador, interacción y capturas | **hoy NO confirmado** (§4) |
| Auxiliar mecánico (inventarios, extracción, formato) | `claude-haiku-5-5` o `gpt-6-luna` · low | sin juicio de arquitectura; **nunca** único revisor ni gate |

Extensión propuesta (a aprobar): `claude-sonnet-5-5` · high como ejecutor de frontend/documentación y como revisor de tareas P1 rutinarias (ya lo decidió el propietario para el revisor de H4-11).

**Legacy** (`gpt-6-sol`, `gpt-6.1-sol`, `gpt-6-astra`, `gpt-5.6-*`): no se usan en desarrollos nuevos salvo justificación escrita en el spec de la tarea.

## 2. Escalado de esfuerzo

- `xhigh`/`max`/`ultra` **no son valores por defecto**. Se piden solo si (a) una pasada `high` ha resultado insuficiente (registrada con su evidencia) o (b) hay evidencia técnica que justifique directamente el esfuerzo superior (p. ej. depuración de una carrera sin reproducción estable).
- Opus y Astra se reservan para problemas donde su capacidad aporte valor verificable; no se usan por "importancia percibida".
- Todo escalado queda en el registro de despacho con su motivo.

## 3. Independencia y validación

1. **Proveedor contrario:** ejecutor y revisor son de proveedores distintos. Nadie revisa su propio código ni su propio documento; la autodelegación (un worker que crea otro worker para revisarse) invalida la revisión.
2. **Revisión exhaustiva inicial:** en su primera pasada el revisor lista **todas** las objeciones detectables, clasificadas **B** (bloqueante) o **A** (recomendación), cada una con su evidencia.
3. **Máximo dos rondas ordinarias.** La 2ª solo verifica las correcciones de la lista de la 1ª; no es una auditoría nueva ni añade objeciones que ya eran detectables, salvo un **descubrimiento material nuevo** (que debe declararse como tal). Si queda un bloqueo real tras la 2ª, se registra y el coordinador **escala al propietario**; no hay 3ª ronda automática.
4. **Validación de arneses.** Antes de usar un script de diagnóstico como evidencia: (a) cada constante (horizonte, tolerancias, umbrales) se cita con `archivo:línea` del código de producción y se comprueba que coincide; (b) las fixtures llevan su hash; (c) el arnés llama a las funciones de producción, no a una reimplementación; (d) se registra con qué HEAD se ejecutó. *Lección H3:* los arneses de AUD-01/AUD-04 usaban 190 s frente a los 180 s de producción y siete rondas no lo detectaron.
5. **Regresión antes/después.** Para cada defecto corregido en H4 se exige una prueba que **falle contra `beb9434`** y pase tras la corrección, siempre que el fallo sea reproducible. Excepciones justificadas por escrito en la tarea. *Lección H3:* 283 + 89 pruebas pasaban con dos P0 presentes.
6. **Un cambio posterior a la aprobación invalida el cierre:** el revisor evalúa el nuevo HEAD y repite las pruebas pertinentes.
7. **`DONE` solo lo declara el coordinador** con dictamen válido del revisor sobre el HEAD real y con el propietario como aceptación final del hito. Una prueba no ejecutada es `NO EJECUTADO`, nunca aprobada.

## 4. Capacidades verificadas y su uso

| Capacidad | Estado (2026-11-24) | Regla |
|---|---|---|
| Despacho de `claude-sonnet-5-5` medium y `claude-opus-5-5` high | **Confirmado** (recibo de Orca + argv `--model=… --effort=…`) | sin restricción |
| Despacho de `gpt-6.1-terra` medium | recibo aceptado; **identidad efectiva no verificable de forma independiente** (el runtime solo declara "GPT-6") | capturar argv durante la ejecución en el primer despacho real |
| Navegador en workers de Codex lanzados por Orca | **NO disponible** (`No browser is available`, `agent.browsers.list() = []`; coincide con 4 observaciones previas) | `gpt-6.1-terra` **no** se asigna a validación visual mientras no cambie. Habilitar navegador/Computer Use implica ajustes del sistema: **decisión del propietario**, nunca del agente. |
| Chrome DevTools en workers de Claude | **Condicional**: el MCP puede estar "conectando" al arrancar (las pruebas de humo no lo tenían cargado; el worker de AUD-05 sí lo tuvo) | **preflight**: el worker comprueba que la herramienta existe antes de declarar nada visual; si no está, lo dice y para |
| Resto (`gpt-6.2-sol`, `gpt-6.2-astra`, `claude-haiku-5-5`, `gpt-6-luna`) | catálogo Codex confirmado para los de Codex; sin prueba de despacho | se verifican en su **primer despacho real** (recibo + argv); si hay incompatibilidad, parar y escalar |

**Evidencia visual (regla vinculante):** ningún agente declara verificada una interacción de navegador sin haberla ejecutado y sin conservar un artefacto comprobable (captura, JSON de medición o transcripción de DevTools en `docs/.../capturas/`). Una revisión solo de código **no** equivale a una revisión visual; el informe debe decir cuál de las dos hizo. Si el revisor no tiene navegador, audita artefactos y código y declara el límite; el coordinador puede reproducir los puntos decisivos.

## 5. Aislamiento obligatorio (lección PR-01)

Antes de cualquier ejecución con capacidad de escritura, el worker verifica y registra **DSN, host, puerto, base, esquema, rol/permisos y persistencia**. Reglas:
- **Prohibido** cualquier DSN a `127.0.0.1:5433` (base de desarrollo compartida, línea base alterada `895/646/8/126/8`, conservada por decisión del propietario) y prohibido depender de defaults implícitos.
- Solo contenedores PostgreSQL **desechables propios**, con puerto propio, destruidos al terminar; migraciones desde cero.
- Los specs incluyen el preámbulo de aislamiento de la plantilla (§ plantilla). H4-11 sustituirá la protección documental por protección en código (fallo seguro, una sola variable, marca de base desechable).
- 5433 no se usa para resultados reproducibles que dependan de su estado original (skips contra desarrollo: limitación conservada).

## 6. Registro estructurado de hallazgos (fuente única de verdad)

Un fichero estructurado (propuesta: `docs/findings/findings.yaml`, tarea H4-13) con una entrada por hallazgo:
`id` (estable, `FR-xx`), `titulo`, `componente`, `severidad` (P0/P1/P2/DESCARTADO/NO_VERIFICADO), `bloquea_publicacion` (si/cond/no, servicio|repositorio), `estado`, `baseline_head`, `evidencia[]` (comando, HEAD, artefacto, SHA-256), `prueba_aceptacion` (id, comando, "falla en `beb9434`": sí/no), `tarea_h4`, `revisor`, `historial[]`. Los informes Markdown derivan sus recuentos de ese fichero (script de generación), no mantienen cifras manuales. El `FINDINGS_REGISTER.md` de H3 **se conserva íntegro** como histórico y siembra el fichero.

## 7. Trazabilidad de despachos

Por cada despacho el registro (`docs/audits/…/` o `docs/orchestration/dispatch-log` del hito) guarda: tarea, rol, **modelo y esfuerzo solicitados**, **efectivos cuando puedan confirmarse** (argv del proceso mientras corre; el autoinforme del modelo no es fiable: p. ej. un "esfuerzo 5" declarado por Sonnet medium), capacidades de herramientas confirmadas, HEAD, comandos de prueba y resultado, dictamen, hash de commits. El registro se mantiene al mismo tiempo que ocurre, con rutas explícitas en `git add`; los registros históricos no se reescriben, solo se añaden correcciones fechadas.

## 8. Costes y concurrencia

- Máximo **2 workers pesados por proveedor** a la vez, y menos si el consumo de cuota, la carga de la máquina o las dependencias lo aconsejan. Los límites de uso son por cuenta y paralizaron la auditoría H3 cinco veces (una por créditos agotados): no se compra cuota ni se cambia de plan sin decisión del propietario.
- No se crean subagentes para lo que el coordinador resuelve de forma trivial. Profundidad de delegación 1; sin sub-workers no autorizados.
- Sin análisis duplicado ni relecturas completas del repositorio: cada tarea produce un paquete verificable (HEAD, inputs, comandos, checksums) que el revisor reproduce en los puntos decisivos.
- Esfuerzo por defecto medium; ver §2.

## 9. Protocolo de devolución del dictamen

1. El ejecutor entrega en `REVIEW` con `worker_done` (qué hizo, comandos reales, resultados PASS/FAIL/NO EJECUTADO, límites declarados, commit).
2. El coordinador despacha al revisor del proveedor contrario con el HEAD y la lista objetiva de criterios (no "confirma que está bien").
3. El revisor responde `APPROVED` | `CHANGES_REQUESTED` | `BLOCKED` con la lista B/A, evidencia reproducida y qué **no** pudo verificar (p. ej. sin navegador).
4. `CHANGES_REQUESTED` vuelve al ejecutor (máx. 1 vuelta ordinaria, §3.3); el revisor verifica solo lo listado.
5. El coordinador registra el dictamen y declara `DONE`; el propietario acepta.
6. Gates humanos intocables: push, PR, merge, aceptación de ADR, licencias, costes, despliegue público, cambios de permisos del sistema, modificación de datos persistentes.

## 10. Criterios de cierre de una tarea
Dictamen `APPROVED` sobre el HEAD final; pruebas de aceptación ejecutadas (con la regresión antes/después de §3.5); registro de hallazgos actualizado; registro de despacho completo; sin escritura en bases persistentes; autoría `Pedro Matute <pedromaaz13@gmail.com>` sin `Co-authored-by` ni cambios de `git config`.
