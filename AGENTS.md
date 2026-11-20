# AGENTS.md — Protocolo de colaboración entre agentes

Este documento define cómo trabajan los agentes de desarrollo dentro de Madrid Pulse. Es vinculante para cualquier agente que opere en este repositorio.

## Quiénes son los agentes

**Orca es el IDE/entorno de trabajo, no un agente.** No tiene criterio propio, no ejecuta tareas ni revisa código. Es el lugar donde trabajan los agentes.

Los únicos dos agentes de desarrollo son:

- **Claude Code** (Anthropic)
- **OpenAI Codex**

Cada tarea del backlog (`docs/TASKS.md`) asigna explícitamente un **agente ejecutor** y un **agente revisor**, que siempre es el agente contrario. Ningún agente revisa su propio trabajo.

## Regla de autoría — obligatoria

**El único contribuidor que debe figurar en el historial de GitHub (en `origin`, en PRs, en `main`) es el propietario humano del repositorio, `pedromaaz13`.**

Esta regla tiene dos partes que no deben confundirse:

**Dentro del worktree de la tarea, los agentes SÍ pueden commitear** (régimen de autonomía acotada, ver "Modelo de autonomía por hito" más abajo): esto permite iterar implementar → revisar → corregir → re-verificar sin bloquear cada ronda esperando al propietario. Un commit de iteración dentro de la rama `mp-00X-nombre-corto` **nunca** sale de ese worktree hasta que el propietario decide fusionarlo.

**Ningún agente, bajo ninguna circunstancia, debe:**

1. Ejecutar `git push` hacia `origin`, `git merge` hacia `main`, ni crear o fusionar Pull Requests — eso es exclusivamente del propietario.
2. Modificar `git config user.name` o `user.email`.
3. Añadir trailers `Co-authored-by: Claude`, `Co-authored-by: Codex`, `Co-authored-by: Anthropic`, `Co-authored-by: OpenAI` ni equivalentes, **tampoco en los commits de iteración dentro del worktree**.
4. Usar cuentas de bot para crear commits.
5. Añadir firmas automáticas de generación por IA o secciones de "contribución de agentes" en README, CHANGELOG o archivos de atribución del proyecto.

El propietario humano revisa el estado final del worktree y es quien realiza el push, abre el PR y fusiona a `main`. La documentación técnica puede —y debe— identificar a Claude Code y Codex como herramientas de desarrollo empleadas en el proyecto y describir sus responsabilidades, sin atribuirles autoría de commit en el historial compartido (`origin`/`main`).

No existe ninguna excepción de "commitear en nombre del propietario si lo pide explícitamente": el propietario commitea él mismo cuando quiere un commit fuera del régimen de iteración en worktree descrito arriba.

## Reglas de colaboración

1. **Ejecutor y revisor independiente.** Cada tarea tiene un agente ejecutor y un revisor distinto, fijados en `docs/TASKS.md`. El revisor nunca es el mismo agente que implementó la tarea.
2. **Un único worktree por tarea, compartido secuencialmente.** Cada tarea `MP-XXX` vive en una única rama/worktree (`mp-00X-nombre-corto`) durante todo su ciclo de vida. Ejecutor y revisor trabajan **secuencialmente dentro de ese mismo worktree** — no se crea un worktree o rama adicional solo para revisar (ver "Protocolo de coordinación en Orca" más abajo).
3. **Revisión real, no superficial.** El revisor inspecciona el diff completo y ejecuta las comprobaciones pertinentes (tests, lint, typecheck, validación de migraciones, verificación de contratos de datos) antes de aprobar. No se reescribe a ciegas: se audita.
4. **`main` protegida.** Nunca se modifica `main` directamente. Todo cambio entra por rama y PR.
5. **No trabajo simultáneo descoordinado.** No se trabaja sobre los mismos archivos en paralelo sin coordinación explícita entre agentes/propietario.
6. **Ningún test se declara superado sin haberse ejecutado realmente.** Está prohibido reportar "tests pasan" sin evidencia de ejecución real (salida de comando, log, captura).
7. **Actualización obligatoria de seguimiento.** Toda tarea debe actualizar `docs/TASKS.md`, `docs/STATUS.md` y `docs/CHANGELOG.md` con evidencia verificable al completarse o cambiar de estado.
8. **No se cambia arquitectura sin ADR.** Ninguna decisión arquitectónica (stack, modelo de datos, contratos de API, estrategia de almacenamiento) se modifica sin proponer y documentar un ADR en `docs/adr/`.
9. **DONE requiere revisión superada.** Una tarea no se marca `DONE` hasta que el agente revisor documenta su aprobación en `docs/TASKS.md`.
10. **Autorización para avanzar — por hito.** No se empieza un **hito** (rango de tareas, ver más abajo) sin autorización del propietario. Dentro de un hito ya autorizado, una tarea individual **no** necesita una autorización nueva: empieza en cuanto sus dependencias directas estén `DONE` (revisor aprobó) — no es necesario que ya estén fusionadas en `main` (ver "Modelo de autonomía por hito" para el mecanismo exacto).

## Modelo de autonomía por hito

Ver [ADR-0007](docs/adr/0007-autonomy-model.md) para el contexto y las alternativas consideradas. Resumen operativo vinculante:

- El propietario autoriza explícitamente un **hito**: un rango de tareas con un objetivo de negocio claro, registrado en `docs/STATUS.md` → "Hito autorizado actualmente". No autoriza cada `MP-XXX` por separado.
- Dentro del hito vigente, una tarea empieza en cuanto sus dependencias directas (`docs/TASKS.md` → campo "Depende de") están **`DONE`** (revisor aprobó) — sin pedir una autorización nueva. Si una tarea cae fuera del hito vigente, sí se necesita autorización explícita antes de empezarla.
- **`DONE` no exige estar ya fusionada en `main`.** Si lo exigiera, el propietario tendría que fusionar en tiempo real después de cada tarea para que la siguiente pudiera empezar — exactamente la supervisión constante que este modelo busca eliminar. El worktree de una tarea dependiente se crea **a partir de la rama de su dependencia directa** (`git worktree add -b mp-00X... <rama-de-la-dependencia>`), no desde `main`, en cuanto esa dependencia está `DONE`. Esto encadena ramas (`mp-002-... → mp-003-... → mp-004-...`) sin que el propietario tenga que fusionar nada entre medias. El propietario decide cuándo fusionar a `main` — en lote al cierre del hito, o antes si lo prefiere — fusionando la rama más avanzada de la cadena (que arrastra todas las anteriores) o cada tramo por separado; ninguna decisión de merge bloquea el avance de las tareas siguientes.
- **Worktrees simultáneos son el comportamiento normal**, no una excepción, cuando dos o más tareas del hito no dependen entre sí (p. ej. MP-005 y MP-010, ambas solo dependientes de MP-004): cada una crea su worktree a partir de la rama de MP-004 (`DONE`) de forma independiente, y sigue su propio ciclo ejecutor/revisor secuencial *interno*. La regla 2 ("un worktree por tarea") sigue aplicando tal cual — es un worktree por tarea, no un único worktree para todo el hito.
- Los únicos gates que detienen el avance en tiempo real durante un hito autorizado son decisiones reales de **licencia o coste** (lista exacta y ejemplos en ADR-0007 — no incluye, por ejemplo, decisiones de visibilidad del repositorio como DEC-003).
- Un cambio de arquitectura sigue exigiendo un ADR (regla 8, no se relaja). El agente que lo propone lo redacta y lo registra como **`Propuesto`** (nunca `Aceptado`) en `docs/adr/README.md` y `docs/DECISIONS.md`, y puede aplicarlo de forma provisional dentro del ciclo de revisión cruzada sin esperar aprobación síncrona. El propietario revisa los ADR `Propuesto` en lote al cierre del hito y decide: promoverlos a `Aceptado`, pedir cambios, o rechazarlos. Esto es coherente con `docs/adr/README.md`: ningún ADR se marca `Aceptado` sin esa revisión explícita del propietario — durante la autonomía, simplemente se trabaja bajo `Propuesto` mientras se espera esa revisión, en vez de bloquear la tarea.
- Un desacuerdo entre Claude Code y Codex que no converge tras varias rondas de corrección/re-verificación deja la tarea en `BLOCKED` (no interrumpe el resto del hito si las demás tareas son independientes en el grafo) y se recoge en el reporte de cierre de hito, no en una interrupción en tiempo real.

### Convergencia de ramas para tareas con varias dependencias (resolución de DEC-015)

Cuando una tarea depende directamente de más de una tarea anterior (p. ej. MP-012 depende de MP-008, MP-010 y MP-011), antes de abrir su worktree se comprueba, para cada dependencia, si ya es ancestro de la rama candidata a base con:

```sh
git merge-base --is-ancestor <rama-de-la-dependencia> <rama-candidata-a-base>
```

- **Si todas las dependencias son ancestros** de la rama candidata (normalmente la más "profunda" de la cadena — en el caso de MP-012, la rama de MP-011, que a su vez parte de MP-010), se ramifica directamente desde ahí. No hace falta ningún `git merge`: la nueva rama ya contiene a todas sus dependencias en su historial.
- **Si alguna dependencia no es ancestro** (divergencia real — dos cadenas que nunca se encontraron), se resuelve con un `git merge` real de la rama no-ancestro sobre la rama base elegida, **antes** de empezar a implementar la tarea, documentando en `docs/STATUS.md` qué rama se eligió como base, cuál se fusionó, y cualquier conflicto encontrado y cómo se resolvió.
- Este mecanismo se aplica de forma transitiva: no hace falta que una dependencia sea ancestro directo, basta con que lo sea en el historial de commits (herencia a través de `main` o de cualquier rama intermedia cuenta).

## Protocolo de coordinación en Orca — un worktree por tarea

Madrid Pulse usa **un worktree por tarea**, no un worktree por agente. Dentro de ese worktree único, Claude Code y Codex trabajan **secuencialmente**: uno implementa, el otro revisa, el primero corrige, el segundo verifica de nuevo — tantas rondas como haga falta, sobre la misma rama/worktree.

1. **Apertura del worktree.** Cuando una tarea `MP-XXX` está dentro del hito autorizado vigente y sus dependencias directas ya están `DONE`, se abre un único worktree/rama (`mp-00X-nombre-corto`) para esa tarea — creado a partir de la rama de su dependencia directa, no necesariamente desde `main` (ver "Modelo de autonomía por hito": `DONE` no exige estar fusionada en `main`). Esto ocurre sin necesitar una autorización nueva por cada tarea. Si dos o más tareas del hito no dependen entre sí, sus worktrees pueden abrirse simultáneamente, cada uno desde la rama de su propio ancestro común. Cada worktree es el espacio de trabajo compartido de ambos agentes durante el ciclo de vida de su propia tarea.
2. **Implementación.** El agente ejecutor trabaja en ese worktree: código, tests, documentación de la tarea (`docs/TASKS.md`, `docs/STATUS.md`).
3. **Entrega para revisión.** Al terminar una ronda, el ejecutor deja el worktree en un estado revisable (tests ejecutados, evidencia registrada) y **delega directamente al agente revisor a través de Orca** cuando la delegación directa entre agentes esté disponible — sin necesidad de pasar por el propietario en cada ronda intermedia. Si la delegación directa no está disponible, el propietario actúa como intermediario para avisar al revisor.
4. **Revisión en el mismo worktree.** El revisor audita el diff **dentro de ese mismo worktree/rama** — no abre uno nuevo. Revisar no requiere aislamiento de rama salvo necesidad técnica real (p. ej. el revisor necesita reproducir un estado que entra en conflicto con cambios sin commitear del ejecutor); si eso ocurre, se documenta explícitamente el motivo en `docs/STATUS.md` antes de crear cualquier rama/worktree adicional.
5. **Corrección y re-verificación.** Si el revisor encuentra problemas, los documenta y delega de vuelta al ejecutor (de nuevo, directamente vía Orca cuando sea posible) para que corrija en el mismo worktree. El revisor vuelve a verificar. Se repite hasta que el revisor aprueba explícitamente.
6. **Cierre funcional del worktree.** Una vez el revisor aprueba la tarea (`DONE` en `docs/TASKS.md`), el worktree queda listo para que la siguiente tarea dependiente ramifique desde él — no es necesario esperar a que el propietario fusione a `main` para que la cadena avance (ver "Modelo de autonomía por hito"). El propietario fusiona a `main` cuando decide — en lote al cierre del hito, o antes — revisando los commits de iteración, haciendo `push` y abriendo/fusionando el PR. Ese merge a `main` es lo que cierra formalmente el worktree a efectos de `AGENTS.md`, pero no bloquea el trabajo ya en marcha sobre las ramas dependientes.
7. **Tarea siguiente, nuevo worktree.** Para cada tarea que dependa directamente de la que se acaba de dejar `DONE`, se abre su worktree a partir de esa rama (no de `main`) en cuanto está `DONE` — dentro de un hito autorizado, esto no requiere una autorización nueva (regla 10, reinterpretada por hito) ni esperar el merge a `main`. Una tarea que no dependa de la recién cerrada puede tener su worktree abierto ya desde antes, en paralelo (ver "Modelo de autonomía por hito").

**Preferencia explícita:** delegar directamente de un agente a otro mediante Orca cuando esa función esté disponible, en lugar de que cada ronda de ida y vuelta pase por el propietario. Esto acelera el ciclo implementar → revisar → corregir → re-verificar sin diluir la responsabilidad de revisión cruzada ni la regla de autoría (sección anterior): la delegación agente-a-agente nunca sustituye al propietario en las operaciones de Git.

## Flujo de trabajo estándar

```text
Issue / tarea MP-XXX (dentro de un hito ya autorizado por el propietario)
        │
        ▼
 dependencias directas en estado DONE (no necesita estar fusionada en main)
 → se abre worktree para la tarea, ramificado desde la rama de la dependencia
 (en paralelo con cualquier otra tarea del hito que no dependa de esta)
        │
        ▼
 agente ejecutor implementa en el worktree
        │
        ▼
 tests locales + lint + typecheck (ejecutados realmente)
        │
        ▼
 delegación directa vía Orca → agente revisor (mismo worktree)
        │
        ▼
 agente revisor audita el diff en el mismo worktree
        │
        ├──► si hay hallazgos: delegación de vuelta al ejecutor → corrige → el revisor re-verifica (repetir)
        │
        ▼
 revisor aprueba explícitamente
        │
        ▼
 evidencia registrada en TASKS.md + STATUS.md
        │
        ▼
 tarea queda DONE → worktree de cualquier tarea dependiente puede abrirse YA, ramificado desde
 aquí, sin esperar merge a main ni autorización nueva (mientras siga dentro del hito vigente)
        │
        ▼
 propietario humano decide cuándo fusionar a main (en lote al cierre del hito, o antes) —
 el momento del merge no bloquea el avance de las tareas que ya ramificaron desde aquí
```

## Convenciones de rama, commit y PR

```text
Ramas:        mp-00X-nombre-corto           (p. ej. mp-007-collector)
              UNA rama/worktree por tarea — no una por agente ni una adicional para revisión.
              Excepción documentada: MP-001 vive en `chore/mp-001-foundation`, nombre anterior
              a fijar esta convención (la rama ya existía cuando se definió el protocolo).
              MP-002 en adelante sigue `mp-00X-nombre-corto` sin excepción.
PR title:     [MP-00X] Descripción corta
Commits:      tipo(ámbito): descripción [MP-00X]
              feat(collector): add Renfe vehicle polling [MP-007]
              test(collector): add duplicate snapshot fixture [MP-007]
              docs(status): record collector validation [MP-007]
```

Un PR no se considera listo para revisión sin: tests relevantes ejecutados, lint y typecheck en verde, validación de migraciones cuando aplique, y verificación de licencia/fuente de datos cuando el cambio toque ingestión o atribución. El PR se abre sobre la misma rama de la tarea una vez el revisor ha aprobado dentro del worktree — no antes.

## Principios de datos — aplicables a cualquier agente

- Todos los timestamps internos se almacenan en **UTC** (`timestamptz`); `Europe/Madrid` solo se aplica en presentación y al interpretar calendarios de servicio GTFS.
- La ingestión debe ser **idempotente**.
- El dato bruto de la fuente (`raw`) nunca se confunde con el dato normalizado.
- Una posición **observada** nunca se presenta como si fuera **interpolada** o **estimada**, y viceversa — ver `docs/DATA_QUALITY.md`.
- Un dato ausente nunca se representa como cero.
- Toda métrica de puntualidad debe exponer su **cobertura** (qué fracción de los viajes tenía dato de retraso disponible), no solo el porcentaje agregado.
- No se inventan campos ni comportamientos de la API de Renfe: todo contrato con fuentes externas se valida empíricamente (ver MP-002, MP-003) antes de documentarse como hecho.

## Licencias de terceros

- **Via Península** (AGPL-3.0): solo estudio conceptual de arquitectura, ADRs y patrones de diseño. **No copiar ni importar su código fuente.** Cualquier intención de reutilizar código literal requiere un ADR específico evaluando las obligaciones AGPL antes de proceder.
- **Valfiguer**: usar como referencia de producto/funcionalidad, no como dependencia de API en producción.
- Ver `docs/legal/LICENSE_MATRIX.md` para la matriz completa de fuentes y licencias.

## Relación con `CLAUDE.md`

`CLAUDE.md` en la raíz de este repositorio contiene las mismas reglas adaptadas como instrucciones operativas para Claude Code. Ambos documentos deben mantenerse coherentes; si entran en contradicción, prevalece este documento (`AGENTS.md`) como fuente de verdad del protocolo, y debe corregirse `CLAUDE.md`.
