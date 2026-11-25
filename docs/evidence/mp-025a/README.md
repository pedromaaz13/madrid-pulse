# MP-025a · entrega para revisión cruzada

Ejecutor asignado por el despacho: Codex gpt-6.2-astra · high. Base local y
origin/main en 2b71d17. Implementación 5de418d y corrección de desempate
2e668a0. La revisión corresponde a Claude Opus High.

## Qué se implementó

| Regla | Comportamiento y evidencia |
|---|---|
| §4.1 | El motor identifica su observación efectiva por instante y hash. Un último GPS rechazado conserva el estado del anterior. El bloque map_matched describe el último GPS. AC-T8 incluye rechazo y empate de timestamps. |
| §4.2 y §4.6 | TripSchedule conserva las ocurrencias de parada. La envolvente aplica cancelación, coherencia, retenciones por el operador, límites de recorrido, pre-salida y velocidad por tramo. R8 conserva la espera probada en zona. El tiempo de viaje y de espera se mide entre instantes UTC. |
| §4.3 | API y OpenAPI exponen procedencia, retención, tope, identidad y congelación. La fase cambia por fotograma. Veinte envolventes sintéticas con 115 instantes cruzan Python y TypeScript de producción con tolerancia 1e-6 m. |
| §4.4 | La base por run incluye únicamente actualizaciones admisibles al estar disponible el ancla. Una actualización posterior modifica la señal del operador. La congelación conserva el progreso al final autorizado, separado del confirmado. La migración 0003 guarda la huella del catálogo y los parámetros en el run para detectar cambios o ausencia de procedencia tras reiniciar. |
| §4.5 y §4.8 | Se distinguen horario, GPS bruto, corredor, interpolación, congelación y ausencia de posición. Con lag cero, position y rendered coinciden en estimated y stale. R-SKIP conserva el tope hasta nueva evidencia. |

## Resultados reproducidos

- **RED, beb9434.** Checkout temporal con las pruebas y fixtures superpuestas.
  El comando terminó con código 1 y 72 aserciones de subcasos fallidas. Entre
  las regresiones están M1 25/25, M2 y M2b 17/17, M3 4/4, M4 7/7, M5 20/44,
  M6, sintéticos de parada y DST, cancelación y caducidad. M7 es guarda.
  En AC-T4 la separación máxima medida fue 429,387875 m. El total RED incluye
  también predicados nuevos evaluados sobre la base anterior. [Comando, HEAD, hashes y salida](RED.txt).
- **GREEN, 2e668a0.** Checkout limpio. Los módulos de CI ejecutaron **309 tests
  Python**, 18 omitidos y cero fallos. Son los 298 anteriores con cinco casos
  autorizados actualizados y 11 tests nuevos. La suite de gobernanza ejecutó
  otros 36 tests. check_docs y regeneración de OpenAPI sin diff pasaron.
  [Comandos y salida](GREEN.txt) · [Cambios individuales autorizados](../mp025a/expectativas.md).
- **Frontend.** Node 22.13.1. npm ci offline, lint, typecheck, 109 tests de
  Vitest y build pasaron. Vite conserva el aviso de tamaño de chunk. [Salida](frontend.txt).
- **F1.** Siete escenarios de disponibilidad sobre los 44 vehículos (incluyen
  los 25 en ventana), incluidas cancelaciones visibles por primera vez a +181 s,
  anulación y cancelaciones antiguas. Las aserciones exigen igualdad exacta
  del progreso a +180, +181 y +400 s. La carga retroactiva reproducible
  causa 1.310,66 m de retroceso si se incluye como en replay explícito.
  Su exclusión del directo preserva el progreso. La prueba de dos colectores
  arranca dos procesos con polling desconectado de la red, comprueba salida
  distinta de cero y diagnóstico del segundo, y vuelve a adquirir el bloqueo
  tras cerrar el primero. [Pruebas PostgreSQL](../../../tests/e2e/test_stop_state_db.py).
- **Reinicio de proceso.** Tres invocaciones independientes con los argumentos
  seed, end y stale del script siguiente confirmaron el run y leyeron el
  progreso antes y después de expirar. Ambos procesos lectores obtuvieron
  40.829,822067 m. Ejecutar en la base marcada con
  `PYTHONPATH=. python docs/evidence/mp-025a/reinicio.py <acción>`.
  [Script](reinicio.py) · [Salida](reinicio.txt).
- **Aislamiento.** Único PostgreSQL en 127.0.0.1:5454. La conexión se registró
  antes de operar. Huella de ingesta contrastada con la API, migración
  down/up ejecutada y destrucción de contenedor y volumen confirmada.
  [DSN](database.txt) · [Huella](perfil.txt) · [Marca y retirada](aislamiento.txt).
- **AC-T7.** ADR §4.3, DATA_CONTRACTS, ProgressEnvelopeOut, ProgressEnvelope
  y movement.ts toman t0 como dwell_until o reference_at y aplican
  min(inicial + velocidad × max(0, t − t0), tope). El constructor prohíbe
  dwell_until anterior a reference_at. Cap se serializa redondeado hacia
  arriba a ms. Los tests sitúan fotogramas a ambos lados de la transición.

## Huecos del ADR y límites para el propietario

El contrato ya tenía schedule_relationship. Se utiliza para la última relación
admisible conocida por orden de run, separada de la actualización base que
autoriza el movimiento. No hizo falta otro campo. La enmienda no especificaba
cómo conservar las versiones del ancla: la huella persistida incluye el
catálogo completo de geometrías, el GTFS y los umbrales. Es conservadora ante
un cambio de geometría de otro patrón. Las filas anteriores a la migración o
ingeridas sin GTFS carecen de huella y al caducar usan anchor_version_changed.
Tampoco fijaba los literales de stop_state.source; se usan operator, schedule
y trip_update. Un run de carga con started_at anterior al de algún id menor
queda fuera de la base de actualizaciones del directo.

La garantía depende del colector único y de poder reconstruir la misma ancla
y versiones. No hay garantía de reproducción exacta por hora civil. Quedan
UNVERIFIED en vivo la semántica de IN_TRANSIT_TO/INCOMING_AT, la latencia de
salidas retenidas, la entrada real en zona a partir de las muestras y la
visibilidad histórica por hora de publicación. R-SKIP puede retener una
circulación que omite una parada. Una cancelación tardía puede permitir
avance hasta la siguiente ancla o el final de la envolvente.

El salto sintético de recuperación respecto de la estimación del motor fue
311,371489 m. MP-025b debe medir en vivo p50 ≤ 200 m sobre al menos 500 pares.
MP-028 calibra P-024. **NO EJECUTADO**: captura en vivo y validación de esos
supuestos; AC-T6/§4.7, reservados a MP-026b; verificación visual de rótulos y
consumo de vigencia, reservados a MP-030.
