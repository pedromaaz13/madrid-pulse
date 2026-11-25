# MP-026b · Entrega para revisión cruzada

Ejecutor del despacho: Codex `gpt-6.2-sol` · high. Base de MP-025a:
`1d9a424`. Consistencia y pruebas: `f022421`. Consulta de actualizaciones
acotada: `a51563b`. Revisión pendiente de
Claude `claude-opus-5-5` · high.

## Cambio de lectura

Snapshot y tablero leen marcador, vehículos (incluidos los laterales del
estado de parada), actualizaciones y salud bajo la misma transacción
`REPEATABLE READ READ ONLY`. La API abre una conexión por petición y los
constructores cierran la transacción al terminar la fase SQL. La construcción
en memoria ocurre después. Un savepoint permite consultar el OID de la base
si PostgreSQL deniega el acceso a `pg_control_system()`, conservando la
instantánea y dejando pasar los errores de consulta restantes.

El marcador aplica el corte de reloj de MP-026a. §4.7 habla del máximo
visible y el contrato preexistente aplica `started_at <= reloj`. Se
interpreta el máximo sobre los runs visibles **y elegibles**. Así, una
base con runs futuros al reloj también puede devolver `sequence: null`.
Con base vacía, snapshot devuelve los feeds esperados como `unknown` y
cero vehículos. El tablero conserva las llamadas del calendario como
`scheduled_only`. La salud acota por `run.id` antes de ordenar y limitar
las muestras. Las lecturas auxiliares de la envolvente dependen de la cota
del ancla o de la cota de la respuesta según la consulta.

§4.7 conserva `snapshot_id` y `tiebreak`. El código heredado calcula el hash
con las entradas seleccionadas; el tablero incorpora salud y actualizaciones
pero su hash no recorre todas las observaciones o llamadas. La equivalencia
AC-T6 se prueba comparando el JSON completo con reloj fijo. La secuencia
puede coincidir aunque cambien los datos, incluso cuando la ingesta tardía
reservó un ID inferior. Los constructores aceptan una transacción externa
repetible para el uso explícito de una instantánea importada.

## Evidencia

- **RED esperado.** [Salida](RED.txt) de
  `python -m unittest apps.api.tests.test_snapshot_consistency -v` sobre un
  checkout temporal de `1d9a424` con solo el módulo nuevo superpuesto.
  Los ocho casos fallaron (nueve fallos contando ambos subcasos de limpieza).
  AUD-06 devuelve la cota de los dos runs con una posición; la petición
  siguiente, con la misma cota, devuelve ambas.
- **GREEN.** Los módulos Python de CI ejecutaron 323 casos en 67,623 s.
  Se conservan los 315 casos de MP-025a y los mismos 18 omitidos, con ocho
  casos nuevos en verde. [Salida desde checkout limpio de `a51563b`](GREEN.txt).
  Se comprueban el orden marcador → vehículo → actualización,
  la igualdad del JSON con una segunda conexión que importa
  `pg_export_snapshot()`, los IDs de referencia hasta la cota, el commit
  inverso, la base vacía, la concurrencia de peticiones y el estado
  `IDLE` tras un error SQL o una cancelación de consulta. El caso de
  permisos verifica que el fallback conserva el rol y la instantánea.
- **PASS.** `python scripts/governance/check_docs.py`, los 36 tests de
  `tests.governance.test_governance` y la comparación byte a byte de
  OpenAPI regenerado. [Salida](CONTRATO.txt).
- **PASS.** Matriz de cobertura y herramienta de benchmark con
  `--reuse-connection` sobre la carga de prueba. [Comandos y salida](TOOLS.txt).
- **NO EJECUTADO.** Validación frontend. OpenAPI cambia descripciones.
  Los campos, tipos y clientes TypeScript conservan su forma.
- **Aislamiento.** Solo PostgreSQL desechable en `127.0.0.1:5455` con
  `madrid-pulse:disposable`, sin capturas remotas. [DSN, marca y limpieza](aislamiento.txt).

## Rendimiento

La carga reproduce los volúmenes de MP-025a (300.000 runs, 100.000 posiciones,
100.000 actualizaciones, 100 vehículos y 100 viajes). Se desplazaron las
fechas para medir dentro del día de la fixture C5 y se incluyó un viaje con
observación y retraso en el tablero. Cada revisión usa la misma base, reloj
y conexiones por petición. Para cada endpoint se calientan 10 solicitudes
y se miden otras 60 con TestClient. Los tiempos incluyen SQL, construcción
de respuesta y serialización en el mismo proceso.

El perfil previo señalaba que la consulta de actualizaciones recorría las
filas de la ventana antes de elegir la primera por viaje. `a51563b` busca
una fila elegible por viaje mediante un lateral acotado y el índice existente
en `source_trip_id, observed_at DESC, id DESC`. Mantiene los filtros, el
desempate por ID y una sola consulta por lote.

| Endpoint | MP-025a p50 / p95 | Consistencia p50 / p95 | Entrega p50 / p95 |
|---|---:|---:|---:|
| Snapshot | 1.484,90 / 1.605,30 ms | 1.467,59 / 1.583,92 ms | 206,44 / 239,72 ms |
| Tablero | 154,64 / 178,54 ms | 160,48 / 188,56 ms | 156,98 / 184,78 ms |

El paso de MP-025a a `f022421` aísla el cambio de consistencia, con su
transacción, savepoint y filtros por ID, antes de optimizar la consulta.
En el tablero el incremento observado fue +5,84 ms p50 y +10,02 ms p95.
En el snapshot dominaba la consulta de actualizaciones y la medición del
cambio de consistencia dio −17,31 ms p50 y −21,38 ms p95. El camino de
éxito añade `SET TRANSACTION`, `SAVEPOINT` y `RELEASE SAVEPOINT`. El
benchmark compara latencias de la respuesta completa en este equipo.
[Carga, comandos y salida](BENCH.txt).

## Alcance de la verificación

AC-T6 garantiza consistencia dentro de cada respuesta. La visibilidad
histórica por hora civil sigue `UNVERIFIED` según la decisión del propietario.
FR-01 y `HG-H4-SCOPE` siguen fuera del cierre de esta entrega. Los rótulos
y la vigencia en UI corresponden a MP-030.
