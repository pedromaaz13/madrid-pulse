# Hito 3 — Autonomía acotada en Orca (protocolo nocturno)

## Propósito

El propietario autoriza ejecutar MP-016→MP-022 localmente sin tener que aprobar cada revisión, test, comando habitual o traspaso Claude/Codex. **Esta autorización no puede cambiar por sí sola permisos de Orca/macOS**, ni levanta prohibiciones del repositorio. La seguridad del sistema, la integridad de otros repositorios y la protección de secretos tienen prioridad sobre la velocidad.

## Preparación en la interfaz — la realiza el propietario ANTES del encargo

1. Orca → Settings (`Cmd+,`) → **Agents → Agent Permissions**: preferir `Auto` para las **nuevas** sesiones Claude/Codex si esa versión lo ofrece. `Auto` intenta aprobar acciones rutinarias; `Manual` interrumpe más; **no se exige ni recomienda `Yolo`/Full access** para este hito. Las sesiones ya abiertas pueden mantener el modo anterior: verificar el modo real del coordinador y de los workers creados, sin presuponer que cambiar el ajuste los modificó.
2. Orca → Settings → **Agent Orchestration**: activar **Let coordinators approve worker permission prompts** cuando esté disponible. Esto permite que el coordinador resuelva autorizaciones de workers con un motivo, dentro del alcance aprobado; no le da un poder sin restricciones. La opción puede variar por versión de Orca: buscarla en Settings sin inventar nombres ni ejecutar comandos no soportados.
3. Comprobar las herramientas de Orchestration en la versión instalada con `orca status --json` y `orca skills get orchestration --full`, y que el coordinador consigue lanzar/verificar un worker de lectura sin quedar bloqueado. No usar el comando legado `orca orchestration run` como lanzador. Evitar duplicar runs existentes: recuperar por `check`/estado.
4. Si se necesitan capturas visuales, comprobar antes Screen Recording para Orca o el agente que realmente capture pantalla. **No activar Accessibility, Camera, Full Disk Access ni otros permisos de macOS si no son estrictamente necesarios** y no están ya autorizados. Un fallo de permiso se registra y se trabaja en tareas independientes.
5. Para una ejecución nocturna local, mantener Orca, el ordenador y el acceso a red operativos; comprobar batería/alimentación. macOS puede suspender al cerrar la tapa. El propietario puede optar voluntariamente por una herramienta normal de mantenimiento de vigilia de macOS, pero ningún agente modifica por su cuenta ajustes energéticos del sistema.

Documentación consultada: https://orca.dev/docs/settings y https://orca.dev/docs/cli/orchestration. Validar siempre con la ayuda **local** de la versión instalada.

## Qué puede aprobar el coordinador por adelantado

**Solo dentro del worktree de Madrid Pulse correspondiente**, con origen y consecuencias verificables:

- Inspección de repo/código/estado Git, lectura de docs y fuentes públicas; lectura de logs sin secretos.
- Crear o recuperar los worktrees de las tareas del hito, editar código y documentación dentro de ellos, `git diff`/`git status`, commits locales con identidad preexistente y sin coautores.
- Pruebas, lint, typecheck, compilación, validación de datos/fixtures, procesos de desarrollo y navegación local en el navegador de pruebas.
- Iniciar/parar **solo** los servicios aislados de Madrid Pulse en Docker Compose sin borrar volúmenes; comprobar primero nombres y puertos. Nunca tocar los contenedores de otros proyectos.
- Instalar dependencias del proyecto desde lockfiles/versiones conocidas tras comprobar su procedencia y scripts ejecutados; no autorizar elevación de privilegios o instalaciones globales nuevas.
- Operaciones de Orca para lanzar workers, leer mensajes, enviar `worker_done`, reintentar errores recuperables y aprobar acciones rutinarias de sus workers mediante la capacidad explícita de orquestación, con motivo registrado.

**Jamás aprobar automáticamente** ni ejecutar por inferencia:

- `git push`, abrir/fusionar PR, hacer merge/rebase sobre `main`, cambiar `git config` o publicar código/artefactos.
- `rm -rf`, `git clean -fd`, `git reset --hard`, borrar worktrees/ramas/volúmenes, migraciones destructivas sobre la base existente, sobrescribir ediciones locales incompatibles, limpiar recursos de otros proyectos.
- Acceder o transmitir secretos, credenciales, llaveros, datos privados de otras aplicaciones o información de terceros no relacionada.
- Cambios de permisos macOS, `sudo`, instalación de agentes persistentes/LaunchAgents, cambios del firewall o acceso global al disco.
- Contratar/desplegar cloud, servicios de pago o aceptar licencias nuevas, exposición pública, llamadas masivas no verificadas a terceros o modificación de políticas de gobernanza.
- Ejecutar scripts descargados/desconocidos o código no auditado con acceso amplio al host; no usar mecanismos para saltarse el sandbox o el sistema de aprobaciones.

Ante una solicitud fuera de la autorización: **denegar o detener solo la acción afectada**, registrar el motivo, conservar cambios, continuar tareas independientes y devolver el gate al propietario al final. Si un permiso del propio coordinador necesita presencia humana, no lo esquives usando otro proceso, `osascript`, un agente diferente o una cuenta nueva.

## Autonomía recuperable, no improvisación continua

- Mantener Run, task_id, dispatch_id, worktree, rama, base, HEAD, ejecución, última prueba, resultado revisor, next action y permisos denegados en `docs/STATUS.md` o registro complementario. No dejar decisiones basadas únicamente en el contexto de chat.
- Elegir un worker propietario por escritura en cada worktree; el revisor recibe el mismo estado, comprueba el diff y repite los tests críticos. Corregir hasta revisión aprobada sobre el HEAD actual.
- Realizar checkpoints locales de código y evidencia sin reescribir historia compartida. La ausencia de respuesta o una tasa límite no autoriza una revisión ficticia: marcar `REVIEW`/`BLOCKED` y reanudar cuando se pueda.
- Si el proceso se suspende, usar el estado persistente de Orca y Git; no reiniciar todo el hito ni borrar workers por incertidumbre.
- Pausa automática ante pérdida repetida de datos, divergencia de esquema, bucle de reintentos, recursos elevados, bloqueo de seguridad o riesgo de corrupción. Evitar polling agresivo o backoff infinito.

**No se puede prometer cero prompts:** `Auto` y la aprobación coordinada reducen interrupciones, pero controles del sistema, operaciones sensibles y diferencias de versión pueden seguir exigiendo la presencia del propietario.
