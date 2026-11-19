# ADR-0007: Modelo de autonomía acotada para la ejecución del backlog

- **Estado:** Aceptado
- **Fecha:** 2026-11-18
- **Decisores:** Propietario del repositorio (`pedromaaz13`)

## Contexto

El propietario pidió que, a partir de MP-002, el desarrollo avance sin necesitar su confirmación en cada tarea individual (`MP-XXX`) ni su intervención en cada ronda de implementar → revisar → corregir → re-verificar entre Claude Code y Codex. Esto entra en tensión directa con dos reglas ya aceptadas en `AGENTS.md`/`CLAUDE.md`:

- Regla 10 de colaboración: "no se inicia una tarea posterior en la cadena de dependencias sin autorización del propietario" — interpretada originalmente como autorización por tarea individual.
- Regla de autoría: ningún agente ejecuta operaciones de Git — lo que impedía que el ciclo "worktree se cierra al fusionar → se abre el siguiente" avanzara sin que el propietario mergeara cada tarea en tiempo real.

Sin resolver esta tensión explícitamente, cualquier intento de "autonomía total" habría exigido romper silenciosamente una de las dos reglas, lo cual viola la regla 8 (no se cambia nada de gobernanza sin ADR) y el principio de no tomar decisiones irreversibles o de gran alcance sin que el propietario las apruebe explícitamente.

Se presentaron al propietario tres preguntas concretas y estas son sus respuestas:

1. Alcance de autorización previa → **por hito, no todo el backlog de una vez**.
2. Commits de los agentes dentro del worktree de la tarea → **sí, permitidos** (el merge a `main` sigue siendo solo del propietario).
3. Qué debe pausar el desarrollo autónomo para pedir su decisión → **únicamente decisiones de licencia o coste** (no se seleccionaron como gate ni las llamadas reales a gran escala contra Renfe/CRTM, ni los cambios de arquitectura sin ADR previo, ni el desacuerdo entre agentes).

## Decisión

### 1. Autorización por hito, no por tarea individual

El propietario autoriza explícitamente un **hito** (un rango de tareas con un objetivo de negocio claro, normalmente varias fases de `docs/PLAN.md`), no cada `MP-XXX` por separado. Mientras el hito esté autorizado y una tarea esté dentro de él, el agente ejecutor puede empezarla en cuanto sus dependencias (`docs/TASKS.md`) estén en `DONE`, sin pedir confirmación adicional. Al completarse el hito (o si una tarea cae fuera de su rango), se detiene y se pide autorización para el siguiente hito — la regla 10 se reinterpreta así: "no se empieza un hito sin autorización", no "no se empieza una tarea sin autorización".

El hito actualmente autorizado se registra en `docs/STATUS.md` → "Hito autorizado actualmente".

### 2. Commits de iteración dentro del worktree, nunca push/PR/merge

Los agentes pueden ejecutar `git commit` **dentro de la rama/worktree de la tarea en curso** para iterar sin bloquear cada ronda de revisión esperando al propietario. Nunca pueden: `git push` a `origin`, crear o fusionar Pull Requests, fusionar a `main`, modificar `git config`, ni añadir trailers de coautoría de agente — ni siquiera en esos commits de iteración. El propietario revisa el estado final del worktree y es quien hace push, abre PR y fusiona. Ver `AGENTS.md` → "Regla de autoría" (reescrita en esta misma tarea para eliminar la contradicción que detectó Codex en la revisión de MP-001: antes existía una excepción de "commitear si el propietario lo pide" que entraba en conflicto con la prohibición absoluta de commit).

### 3. Gates de pausa limitados a licencia/coste

Durante un hito autorizado, el desarrollo autónomo **solo se detiene** para pedir una decisión del propietario cuando aparece una decisión real de **licencia o coste** — por ejemplo: DEC-002 (licencia del código propio), DEC-004 (retención/coste del histórico), contratar un servicio cloud de pago, o adoptar una licencia de terceros con obligaciones nuevas. **DEC-003 (visibilidad pública/privada del repositorio) no es un gate de este tipo** — no es una decisión de licencia ni de coste, es una decisión de gobernanza que puede resolverse en cualquier momento sin bloquear ninguna tarea (ver `docs/DECISIONS.md`).

Explícitamente **no son gates de pausa en tiempo real**:
- Las llamadas reales a gran escala contra los endpoints de Renfe/CRTM (MP-003 y el colector de MP-007 pueden operar de forma sostenida dentro del hito autorizado).
- Un cambio de arquitectura: sigue exigiendo un ADR (regla 8, no se relaja). El agente que lo propone lo redacta y lo registra como **`Propuesto`** (nunca `Aceptado`) en `docs/adr/README.md` y `docs/DECISIONS.md`, y puede aplicarlo de forma provisional dentro del ciclo de revisión cruzada Claude↔Codex sin esperar una aprobación síncrona del propietario. El propietario revisa todos los ADR en estado `Propuesto` en lote al cierre del hito y decide: promoverlos a `Aceptado`, pedir cambios, o rechazarlos. Esto no contradice la regla de `docs/adr/README.md` de que ningún ADR se marca `Aceptado` sin autorización del propietario — durante la autonomía se trabaja bajo `Propuesto` en vez de bloquear la tarea esperando esa autorización.
- Un desacuerdo entre Claude Code y Codex: si tras varias rondas de corrección/re-verificación no convergen, la tarea se marca `BLOCKED` en `docs/TASKS.md`/`docs/STATUS.md` y se deja ahí — no se interrumpe al propietario en tiempo real, se recoge en el reporte de cierre de hito.

### 4. Paralelismo entre ramas independientes del grafo de dependencias

Cuando el grafo de `docs/TASKS.md` tiene dos tareas que dependen del mismo ancestro pero no entre sí (p. ej. MP-005 y MP-010, ambas solo dependientes de MP-004), pueden ejecutarse en **worktrees independientes y simultáneos**, cada uno con su propio ciclo ejecutor/revisor secuencial interno. Esto no es una excepción a "un worktree por tarea"; es la aplicación literal de esa regla a dos tareas distintas que pueden avanzar en paralelo.

## Alternativas consideradas

- **Autonomía total sin ningún gate:** descartada — el propietario pidió explícitamente mantener al menos las decisiones de licencia/coste bajo su control.
- **Mantener autorización por tarea individual:** descartada por el propietario — es la que generaba la dependencia de supervisión constante que quería eliminar.
- **Permitir push/merge autónomo a main:** no se consideró una alternativa real — contradice el requisito más enfático del propietario desde el inicio del proyecto (único contribuidor visible en GitHub).

## Consecuencias

- `docs/STATUS.md` debe mantener siempre visible el hito autorizado vigente y su rango de tareas.
- `docs/TASKS.md` y `docs/PLAN.md` reflejan este modelo (ver notas añadidas en ambos en esta misma tarea).
- Cualquier gate de licencia/coste que aparezca durante la ejecución autónoma se registra en `docs/DECISIONS.md` como nueva entrada `PENDING` y pausa solo la tarea afectada, no el resto del hito si son independientes en el grafo.
- Este ADR puede revisarse si la experiencia de los primeros hitos revela que el conjunto de gates es insuficiente o excesivo — cualquier cambio a este ADR sigue requiriendo autorización del propietario (regla 8).
