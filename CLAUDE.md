# CLAUDE.md — Instrucciones operativas del repositorio Madrid Pulse

Este archivo es específico del repositorio `madrid-pulse` y rige el comportamiento de Claude Code dentro de él. Complementa, y no sustituye, `AGENTS.md`, que es la fuente de verdad del protocolo de colaboración entre agentes.

## Rol

Dentro de este repositorio actúas como **agente ejecutor o revisor**, según lo que indique la tarea asignada en `docs/TASKS.md`. El agente contrario es **OpenAI Codex**. **Orca es el IDE, no un agente.**

## Antes de empezar cualquier tarea

1. Lee `docs/PLAN.md`, `docs/TASKS.md`, `docs/STATUS.md`, `docs/DECISIONS.md` y los ADRs relevantes en `docs/adr/`.
2. Identifica el ID de tarea (`MP-XXX`) que está dentro del **hito autorizado vigente** (`docs/STATUS.md` → "Hito autorizado actualmente") y cuyas dependencias directas ya están `DONE` (revisor aprobó — **no** necesitan estar ya fusionadas en `main`: ver "Modelo de autonomía por hito" en `AGENTS.md` y ADR-0007). Dentro de ese hito no necesitas una autorización nueva por cada tarea individual; sí necesitas autorización explícita para una tarea fuera del hito vigente o para empezar un hito nuevo.
3. Confirma que trabajas en el worktree/rama único de esa tarea (`mp-00X-nombre-corto`) — no abras un worktree o rama adicional para tu parte del trabajo; ese worktree es compartido con Codex de forma secuencial (ver "Protocolo de worktree" más abajo).
4. Inspecciona el código y la documentación existente antes de modificar nada.
5. Verifica si la tarea tiene dependencias no resueltas (`docs/TASKS.md`) — no implementes sobre dependencias incompletas.

## Protocolo de worktree — un único worktree por tarea

Madrid Pulse usa **un worktree por tarea `MP-XXX`, nunca uno por agente**. Dentro de ese worktree, tú (Claude Code) y Codex trabajáis secuencialmente: quien implementa, implementa; el otro revisa en ese mismo worktree; si hay hallazgos, el primero corrige y el segundo vuelve a verificar — sin crear ramas o worktrees adicionales solo para la revisión, salvo una necesidad técnica real y documentada en `docs/STATUS.md`.

- Si eres el **ejecutor**: al terminar tu ronda, deja el worktree en estado revisable (tests ejecutados de verdad, evidencia registrada) y **delega directamente a Codex a través de Orca** cuando esa función esté disponible, en vez de esperar a que el propietario reenvíe el trabajo. Si la delegación directa no está disponible, informa al propietario para que la gestione.
- Si eres el **revisor** de una tarea que ejecutó Codex: audita el diff dentro de ese mismo worktree, no en uno nuevo. Si encuentras problemas, documenta los hallazgos y delega de vuelta a Codex (directamente vía Orca si es posible) para que corrija; vuelve a verificar cuando te lo devuelvan.
- En cuanto una tarea queda `DONE` (revisor aprobó), puedes abrir el worktree de cualquier tarea que dependa directamente de ella **ramificando desde su rama**, no desde `main` — no necesitas esperar a que el propietario la fusione, ni pedir una autorización nueva, siempre que siga dentro del hito autorizado vigente (`docs/STATUS.md` → "Hito autorizado actualmente"). El propietario decide cuándo fusionar a `main` (en lote al cierre del hito u otro momento que prefiera); ese momento no bloquea tu avance. Si una tarea no depende de la que acabas de cerrar, puedes tener su worktree abierto ya en paralelo, desde antes.
- La delegación directa entre agentes vía Orca agiliza el ciclo implementar → revisar → corregir → re-verificar, pero **nunca** sustituye al propietario en las operaciones de Git — ver regla de autoría abajo.

## Durante la tarea

- No cambies decisiones de arquitectura sin proponer un ADR en `docs/adr/`.
- No inventes campos, estructuras o comportamientos de las APIs de Renfe, CRTM u otras fuentes externas. Todo debe basarse en verificación empírica real (ver MP-002/MP-003) o quedar marcado explícitamente como `UNVERIFIED`/`PENDING`.
- Preserva los metadatos de atribución y licencia de cualquier fuente de datos que toques (`docs/legal/`).
- Añade pruebas para cualquier regla de parseo, transformación o validación que escribas.
- Ejecuta lint, typecheck, tests unitarios e integración reales antes de reportar la tarea como lista. No declares un test superado sin haberlo ejecutado.
- Aplica los principios de datos de `AGENTS.md`: UTC interno, idempotencia, raw ≠ normalizado, observado ≠ estimado, dato ausente ≠ cero, puntualidad siempre con cobertura.
- No copies código de Via Península (AGPL-3.0). Estudia sus conceptos y reimplementa de forma independiente.

## Al terminar la tarea

1. Actualiza `docs/TASKS.md` (estado, evidencia) y `docs/STATUS.md` (tablero vivo).
2. Añade una entrada real a `docs/CHANGELOG.md` — nunca una entrada que describa algo no implementado.
3. Prepara un resumen de revisión conciso y delega directamente a Codex vía Orca (en el mismo worktree) para que pueda auditar sin tener que reconstruir todo el contexto.
4. No marques la tarea como `DONE`: déjala en `REVIEW` hasta que Codex complete su auditoría —y, si hay hallazgos, hasta que tú corrijas y Codex vuelva a verificar en ese mismo worktree— y el propietario la acepte.

## Reglas de autoría — obligatorio en cada acción de Git

Puedes commitear **dentro del worktree de la tarea** (rama `mp-00X-nombre-corto`) para iterar sin bloquear cada ronda esperando al propietario — ver "Protocolo de worktree" arriba y "Modelo de autonomía por hito" en `AGENTS.md`. Esos commits de iteración nunca salen de ese worktree por tu cuenta.

Dicho esto, **nunca**, ni dentro del worktree ni fuera de él:

- Ejecutes `git push` hacia `origin`, `git merge` hacia `main`, ni crees o fusiones Pull Requests — el propietario humano (`pedromaaz13`) es quien realiza esas acciones.
- Modifiques `git config user.name` / `user.email`.
- Añadas trailers `Co-authored-by: Claude`, `Co-authored-by: Anthropic` ni equivalentes a ningún commit, incluidos los commits de iteración en el worktree.
- Añadas firmas de generación por IA en README, CHANGELOG ni archivos de atribución del producto.

No existe una excepción de "commitear en nombre del propietario si lo pide" — si el propietario quiere un commit fuera del régimen de iteración en worktree, lo hace él mismo.

## Alcance de MP-001 específicamente

Durante MP-001 no se escribe código de producto, no se instalan dependencias, no se configuran servicios cloud ni se levantan contenedores. El entregable es exclusivamente documental: estructura de repositorio, gobernanza, planificación y backlog. Cualquier desviación de este alcance requiere autorización explícita del propietario.

## Coherencia con AGENTS.md

Si detectas una contradicción entre este archivo y `AGENTS.md`, señálala y corrige este archivo — `AGENTS.md` es la fuente de verdad.
