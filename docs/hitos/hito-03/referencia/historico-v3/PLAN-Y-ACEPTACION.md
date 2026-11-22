# Hito 3 · Plan de trabajo y criterios de cierre — v3

**Consolidación v3:** conservar siete tareas y reparto. Integrar MEJORAS-PRODUCTO-VALIDADAS.md y REVISION-Y-DECISIONES.md. La tabla UX del informe de referencia no añade tareas ni cambia responsables.

Objetivo de producto: desde el móvil puedo buscar Alcorcón, leer la próxima salida con su procedencia, seguir el viaje sobre la vía y abrir su histórico. La red completa se descubre desde el GTFS de Madrid y cada patrón declara su grado de cobertura.

Esta planificación parte de main 990c95d. Al comenzar, compara con HEAD, el hito vigente y los IDs de docs/TASKS.md. Las asignaciones siguientes son la propuesta para la autorización del propietario. Si un identificador ya está ocupado, conserva su tarea y reasigna el nuevo bloque documentando la equivalencia. STATUS, TASKS y CHANGELOG siguen siendo el registro del trabajo real. El estado de este documento es planificación.

**Claude Sonnet coordina el hito en Orca.** Todos los encargos de la tabla piden esfuerzo alto. El coordinador verifica al arrancar qué modelos ofrece cada proveedor y registra el modelo efectivo conforme a PROMPTS.md.

| Tarea y worktree sugerido | Ejecuta | Revisa | Entrega comprobable | Depende de |
|---|---|---|---|---|
| MP-016 · mp-016-fiabilidad-live | Codex · gpt-6.2-sol | Claude · sonnet | Integrar auditoría y material de diseño. Reproducir main, revisar el parche, tratar SKIPPED, validar UTC y mostrar edad de la fuente. Arranque local documentado con modos live y replay explícitos. | MP-015 |
| MP-017 · mp-017-catalogo-madrid | Claude · sonnet | Codex · gpt-6.2-sol | Catálogo completo versionado por núcleo, línea, variante y patrón. Estado activo separado de último histórico. Resolver avisos por estación, cambios de viaje, medianoche y cancelaciones sin fabricar matches. | MP-016 |
| MP-018 · mp-018-corredores-madrid | Codex · gpt-6.2-astra | Claude · opus | Corredores GTFS/OSM por patrón y sentido. Mantener último punto GPS y su distancia al trazado. Versionar el catálogo de geometrías y medir cobertura de cada línea. | MP-017 |
| MP-019 · mp-019-snapshot-api | Claude · opus | Codex · gpt-6.2-astra | Publicar una instantánea coherente y cacheable, con tablero de estación, ETA por parada con método y procedencia, novedad y metadatos de edad. API compatible, sin consulta SQL por vehículo. | MP-018 |
| MP-020 · mp-020-mapa-y-tablero | Claude · opus | Codex · gpt-6.2-sol | Implementar Live en React/MapLibre con mapa, búsqueda, multiselección de líneas, tablero, ficha de tren, seguimiento y cinta de eventos. Adaptar diseño a móvil y teclado. | MP-019 |
| MP-021 · mp-021-historico | Claude · opus | Codex · gpt-6.2-astra | Archivo propio, exportación idempotente, historial consultable por circulación y demo Explore con cobertura. Entregar configuración reproducible del colector continuo y estimación de coste medida. | MP-020 |
| MP-022 · mp-022-validacion-integrada | Codex · gpt-6.2-sol | Claude · sonnet | Replay y recorrido completo por Live → History; pruebas sin señal y con recuperación; métricas por línea, capturas escritorio/móvil y limitaciones. Dossier para integración del propietario. | MP-021 |

Claude Opus recibe las decisiones de arquitectura del contrato de API, el rediseño de Live y el histórico. Codex Astra recibe la implementación geométrica y las revisiones que cruzan SQL, API y modelo de datos. La cadena es secuencial por las dependencias de este plan. El ejecutor y el revisor usan por turnos el mismo worktree y el orquestador abre el siguiente desde el commit local aprobado.

## Qué se prueba en cada entrega

**016 · Reproducción.** En el primer corte congelado: 119 de Madrid, 119 coincidencias con el ZIP completo, 28 ubicables en el piloto C5, 119 retrasos reportados tras el arreglo. En el segundo: 121 coincidencias. Las 49 paradas SKIPPED sin arrival deben aceptarse en cada corte. Repetir con una respuesta inválida, reloj desfasado y colector detenido. Se puede ejecutar la sonda de cruce con Python estándar; la prueba de ingesta y API requiere PostGIS y las dependencias del proyecto. La sonda sola no acredita el parche. Explicar cómo distingue Live el dataset de la fixture y cuándo reiniciar el backend.

**017 · Identidad y vigencia.** En el ZIP congelado, validar 42 route_id agrupados en 12 nombres de línea/variante. Mantener las 12 en catálogo aunque alguna tenga cero vehículos en el corte. Probar el stopId 60104, los dos servicios sucesivos de un vehículo, un SPECIAL sin trip programado y una circulación con hora 24:xx. Un retraso viejo no puede completar el viaje de hoy.

**018 · Geometría.** Revisar C5, un ramal C4 y un tramo compartido. Inspeccionar desvío lateral, estaciones fuera de orden y discontinuidades. Entregar la tabla de *todos* los patrones con fuente, versión y estado: validado, parcial o pendiente. El mapa podrá presentar GPS bruto con etiqueta si el corredor no permite interpolar. Conservar como dato faltante cualquier posición desconocida.

**019 · Contrato.** A partir de tres snapshots (normal, parcial y congelado), comprobar por separado transporte, edad del feed, edad del GPS y vigencia de la ETA. Medir con EXPLAIN y tiempos p50/p95 en condiciones documentadas. El último snapshot válido sobrevive al fallo de un feed con advertencia visible. Evitar caché de datos viejos rotulados como nuevos. Versionar cambios de contrato y documentar rutas realmente disponibles.

**020 · Diseño.** Abrir diseno/live.html y los PNG antes de implementar. La estación seleccionada, cámara y foco sobreviven a dos polls y a un error recuperable. Las animaciones siguen la geometría correspondiente. Validar con teclado, movimiento reducido, pantalla de 390 px y escritorio. Probar menú de línea, cinta pausada, tamaño táctil, salida de seguimiento al arrastrar y acceso a tablero si WebGL falla. La maqueta demuestra interacción con datos propios de ejemplo; producción utiliza la API.

**021 · Producto analítico.** Una captura repetida conserva una observación única. Reprocesar dos veces un día reproduce los mismos agregados. Recuperar qué retraso y qué procedencia se conocían a una hora concreta. Verificar numerador y denominador del porcentaje y qué devuelve una franja sin muestra. Demostrar captura sin navegador y reinicio del proceso. La puesta en marcha en un proveedor de pago requiere la decisión de coste del propietario.

**022 · Cierre.** Cruzar un viaje desde fuente hasta API y pantalla y desde el histórico hasta el mart. Incluir tabla «previsto / entregado / evidencia / pendiente», resultados de tests y descartes por línea. Documentar mediciones reales de fluidez, latencia, volumen y coste proyectado. El propietario integra cuando la revisión independiente esté aprobada.

## Alcance posterior

La propuesta de dbt contempla un ADR nuevo frente al ADR-0013 y comparar el primer mart frente al gold vigente. SQL Lab, cuentas de usuarios, roles de analista, despliegue de pago y un broker de eventos tienen su diseño en referencia/03-arquitectura-analitica.md. La autorización de este paquete cubre la preparación local y el alcance descrito en 016–022. Cada ampliación sigue su decisión de producto o coste.

## Aceptación adicional v3

Las mejoras de frontend y contrato se distribuyen entre las tareas existentes según MEJORAS-PRODUCTO-VALIDADAS.md. MP-019 compara alternativas de movimiento antes de fijar formato; MP-020 mantiene selección, cámara, objeto/fecha y recursos parciales. Los escenarios adicionales a 1532/1533 se etiquetan como fixtures derivadas/sintéticas o nuevas capturas verificadas. SKIPPED afecta a la parada, no paraliza automáticamente la circulación. Favoritos y efectos no bloquean el recorrido principal. No ordenar hashes de snapshot como secuencias.
