# Único prompt vigente — Hito 3 v3

Pegar este contenido como mensaje a Claude coordinador en Orca. Esta autorización surte efecto cuando el propietario lo envía; la presencia del archivo no autoriza ejecución por sí sola.

Claude, coordina el desarrollo local de Madrid Pulse desde este kit v3. La carpeta del kit es la que te indico o adjunto en este mensaje. Autorizo MP-016→MP-022 con el alcance de PLAN-Y-ACEPTACION.md y los ajustes de MEJORAS-PRODUCTO-VALIDADAS.md. Mantén toda Cercanías Madrid, Live, movimiento verificable e History/Explore mínimo. No añadas las quince tareas UX como una segunda cadena.

Lee AGENTS.md, CLAUDE.md, TASKS, STATUS y CHANGELOG del clon; después PLAN-Y-ACEPTACION.md, REVISION-Y-DECISIONES.md, MEJORAS-PRODUCTO-VALIDADAS.md, ANEXO-CRITICO-POSICION-Y-RELOJ.md, MATRIZ-CIERRE-MADRID.md y PROMPTS.md del kit. Revisa el prototipo y las interacciones antes de MP-020. El informe extenso de referencia es consulta técnica, no otro reparto de tareas.

Contrasta HEAD y los worktrees locales con la base remota auditada 990c95d. Conserva cambios y tareas aprobadas; registra diferencias y correspondencias de IDs. Si hay workers activos, recupera sus despachos. Si el hito está avanzado, ejecuta solo el delta pendiente, sin reiniciarlo.

Mantén reparto y dependencias MP-016→022 del plan. Sonnet con esfuerzo alto coordina; verifica los modelos realmente disponibles y registra solicitado/efectivo. No inventes comandos, parámetros ni versiones. Usa workers reales del proveedor asignado y revisión independiente del proveedor contrario. Trabajan por turnos en un único worktree por tarea. Repite correcciones/revisión hasta aprobación del último estado; no simules el otro proveedor.

Comprueba antes que data/hito-03 queda excluido de Git; si no lo está, añade solo la regla /data/hito-03/ al archivo local indicado por git rev-parse --git-path info/exclude, conservando su contenido. No cambies git config. Encarga al primer ejecutor instalar el kit en el worktree correspondiente con instalar.py --worktree RUTA --comprobar y después sin --comprobar. Si hay documentación local editada, el instalador se detendrá antes de sobrescribirla: integra manualmente el delta conservando cambios. No borres la edición local para forzar la instalación. En siguientes worktrees repón datos con --solo-datos cuando sea necesario.

Prioridades técnicas:
- MP-016: parser SKIPPED, raw, UTC, último éxito, fuente obsoleta y replay identificado.
- MP-017/018: circulación/fecha/patrón/sentido, catálogo Madrid completo y geometría trazable sin unir huecos.
- MP-019: snapshot coherente/cacheable, SQL batch, tablero real y edad fuente/ancla/ETA. Decide por ADR la solución temporal más simple que permite movimiento; no impongas trayectorias futuras ni dupliques reglas. Un hash de snapshot no se ordena como contador.
- MP-020: App.tsx como composición, cargas independientes, objetos estables, fichas, búsqueda, líneas múltiples, enlaces, seguimiento que cede al gesto, móvil/teclado/reduced motion. Movimiento sobre vías con evidencia y presentación separadas. Una parada SKIPPED no congela el tren entero. Favoritos y efectos solo si no retrasan el recorrido principal.
- MP-021/022: histórico por circulación, denominadores, replay idempotente, operación local supervisada y E2E real; cobertura de toda Madrid con límites visibles.

Conserva los datos originales del replay y el parche como referencia; comprueba aplicabilidad antes de usarlo. Para escenarios no incluidos en los dos cortes, añade fixtures claramente etiquetadas o capturas con manifiesto. No llames a Valfiguer desde producción ni copies código de Vía Península. Conserva el arreglo del worker MapLibre y evita APIs privadas.

Avanza autónomamente dentro del hito autorizado sin pedir aprobación por tarea o revisión. Actualiza TASKS, STATUS y CHANGELOG y registra dispatch, rol, modelo, worktree, base, HEAD, pruebas reales, skips y próxima acción. Los cambios arquitectónicos se documentan como ADR propuesto, no aceptado.

Quedan fuera push, PR, merge a main, cambios de git config, limpieza destructiva y contratación cloud. Los commits locales de iteración siguen AGENTS.md y la identidad ya configurada. Detén solo la parte afectada por un gate real de coste/licencia o bloqueo técnico irrecuperable, documentándolo y avanzando en tareas independientes.

Al cerrar entrega ramas/commits para mi integración, pruebas ejecutadas, matriz por línea/patrón, capturas y grabación de la app real, medidas con entorno de prueba y tabla previsto/entregado/pendiente. No declares DONE sin revisión independiente ni confundas maqueta, fixture o compilación con producto validado.

