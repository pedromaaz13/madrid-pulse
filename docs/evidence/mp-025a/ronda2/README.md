# MP-025a · Corrección de la revisión de 5514016

Ejecutor asignado: Codex gpt-6.2-astra, high. Commit de producto y pruebas
c506723. El dictamen anterior es CHANGES_REQUESTED. La reverificación
corresponde a Claude Opus High.

| Hallazgo | Cambio o límite | Comprobación |
|---|---|---|
| **B1** | Una huella nula, antigua, indescifrable o discordante produce retención desde el primer fotograma con `hold_reason` y `frozen_basis` explícitos. Se comparan GTFS, geometría del patrón del tren y parámetros relevantes. SHORT_NAME y la geometría de otros patrones no intervienen en esa comparación. | Con cada una de las dos huellas ensayadas, **8/44 → 0/44** retrocesos al expirar y **2.371,039612 → 0 m** de máximo. Pruebas del punto de entrada del colector sin GTFS y del colector de núcleo completo con API filtrada a C5. [RED](continuidad-RED.txt) · [GREEN](continuidad-GREEN.txt) |
| **B2** | La migración 0004 clasifica los runs una vez, con backfill del histórico y trigger para inserciones. La consulta recorre los ids de vehículo distintos por índice, recupera hasta dos muestras de cada uno y usa búsquedas por viaje/run con LIMIT 1. | Misma carga sintética del revisor y mismos datos antes y después. Tres consultas de aplicación pasaron de **7.343–7.471 ms a 13,83–17,05 ms**. [Plan y tiempos RED](perf-RED.txt) · [Plan y tiempos GREEN](perf-GREEN.txt) |
| **B3** | El tablero y el snapshot comparten la selección de la relación por run, la ventana MP-017 de 20 h y el predicado de edad de cancelación. La señal conocida y la base inmutable del ancla siguen separadas. | Viaje recurrente sin GPS: a −86.400 y −601 s vuelve a schedule_only, sin señal de cancelación ni ETA cancelada en tablero. A −600 s ambos señalan CANCELED y el snapshot queda unlocated. [RED](RED.txt) · [GREEN](GREEN.txt) |
| A1 | Tolerancia parametrizada ante pequeños saltos NTP, 2 s por defecto. La heurística se evalúa en el momento del INSERT. Una carga fuera del colector puede eludir la garantía. | Prueba con tolerancia de 3,5 s y ambos lados del límite. La prueba histórica de 1.310,66 m sigue en la suite. |
| A2 | Documentados SIGSTOP, diagnóstico del backend titular por pg_locks/pg_stat_activity, identificación del proceso, recuperación y limitación del pooling por transacción. | [Procedimiento operativo](../../../operations/DATABASE_ISOLATION.md). Sin cambio de supervisor o keepalives. |
| A3 | 0003 up/down idempotentes. El down elimina la procedencia y al reconstruir se retiene desde el primer instante. Documentados rollback y backfill de 0004. | Reaplicación sobre 300.000 runs y ciclo down/up. [Salida](migraciones.txt) · [Manual](../../../../infra/migrations/README.md) |
| A4 | Coordinación con MP-026b: las lecturas de anteriores, base y relación conocida, incluida la consulta por lote del tablero, deben entrar en la misma instantánea MVCC de la respuesta y respetar su sequence. La señal conocida puede proceder de un run posterior al ancla. | Contrato de integración documentado aquí. §4.7 y AC-T6 quedan a MP-026b. |
| A5 | La versión de fuente, los parámetros y la procedencia se construyen con código de packages. El colector dejó de importar apps.api. Avisa y conserva el GPS bruto con huella desconocida si falta el GTFS o si no se pudo verificar la geometría. | Pruebas de colector sin GTFS y coincidencia del patrón con filtros de línea diferentes. |
| A6 | Antes de reference_at y con causa nula, Python y TypeScript devuelven `hold:null`. | Pruebas de fase en ambos runtimes. |
| A7 | hold_reason y stop_state.source tipados mediante Literal en los esquemas de respuesta y enumerados en DATA_CONTRACTS. | OpenAPI regenerado y comparado con el esquema generado desde el checkout limpio. |
| A8 | La parte de AC-T1 «aviso visible (vitest)» está **diferida a MP-030**. | NO EJECUTADO. Los tests de dominio sí cubren progreso, fase y congelación. |
| A9 | /vehicles conserva las coordenadas del motor. /snapshot.position publica la posición presentada en estimated/stale con lag cero. Puede haber diferencias del orden de 429 m entre endpoints. La relación por run y el retraso por observed_at pueden proceder de filas distintas. | Limitación documentada para los consumidores. |
| A10 | La recuperación sintética próxima a la estimación del motor da **311,371489 m** de salto presentado. | La suite conserva la medición. En vivo sigue UNVERIFIED hasta MP-025b, p50 ≤ 200 m con al menos 500 pares. |

## Reproducción y resultados

- Para la regresión funcional se ejecutó `python -m unittest tests.e2e.test_stop_state_review -v` con el producto de 5514016 y se repitieron los casos con la corrección. Para el salto se ejecutó `PYTHONPATH=. python docs/evidence/mp-025a/ronda2/continuidad.py` contra ambas versiones y las mismas fixtures.
- Para rendimiento se creó un contenedor propio con la imagen local postgis/postgis:17-3.5, en 127.0.0.1:5454, y se marcó la base como desechable. Con el esquema de 5514016 se ejecutó [carga.sql](carga.sql): 300.000 runs, 100 vehículos y 100 viajes. Se ejecutó `PYTHONPATH=. python docs/evidence/mp-025a/ronda2/perf.py` antes y después de aplicar 0004, sobre esa misma población. EXPLAIN ANALYZE pasó de 10.609,348 a 16,169 ms. El umbral de referencia era 160 ms. Los tiempos son de esta máquina y carga sintética.
- La suite completa usó otro contenedor recién creado y marcado, en el mismo puerto. Se conservaron los 298 casos previos con las cinco expectativas ya autorizadas; en esta ronda se ajustaron fixtures y expectativas añadidas por MP-025a y se incorporaron seis casos Python de revisión.
- **PASS.** Suite Python: 315 tests, 18 omitidos. Gobernanza: 36 tests y check_docs. Frontend: 110 tests de Vitest, lint, typecheck y build. OpenAPI regenerado sin diff. Reinicio F1 en tres procesos: [lecturas idénticas](reinicio.txt). Vite mantiene el aviso de tamaño de chunk.
- [Comando completo de CI, HEAD, suite Python, gobernanza y OpenAPI](GREEN.txt) · [Node 22.13.1, lint, typecheck, Vitest y build](frontend.txt) · [DSN, marca y limpieza](aislamiento.txt).

La continuidad al expirar se midió para una ancla fija. Un cambio de geometría
entre consultas puede cambiar la proyección del GPS. Continúan pendientes la
calibración en MP-028, la semántica y latencia en vivo y la reproducción
histórica por hora civil.
