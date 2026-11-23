# Coste medido del colector continuo supervisado (MP-021)

Medición **real**, no una estimación, de una ventana de operación continua del
colector de Madrid Pulse contra los feeds en vivo de Renfe. El informe crudo
que produjo la herramienta está en
[`mp-021-medicion-coste.json`](mp-021-medicion-coste.json); la herramienta que lo produjo es
`infra/operate/measure-cost.py`.

> **Qué NO demuestra este documento.** La ventana medida son **13 minutos y 43
> segundos**, no 24 ni 72 horas. Todas las cifras de 24/72 h de este documento
> son **proyecciones** a partir de esa ventana, marcadas como tales. No
> autorizan decir "24/7 verificado", y no se dice. Ver
> [`infra/operate/README.md`](../../infra/operate/README.md), sección "Los tres
> estados".

## Cómo se midió

| | |
|---|---|
| Ventana | `2026-11-23T05:23:20Z` → `2026-11-23T05:37:03Z` (823,2 s) |
| Supervisor | `infra/operate/supervise-collector.sh`, el entregado en este hito |
| Origen | Feeds reales de Renfe (`gtfsrt.renfe.com`), no fixtures |
| Base | PostgreSQL **desechable** `mp021-collector-db` en `127.0.0.1:5435`, creada para esto con las dos migraciones aplicadas desde cero |
| Cadencia | `COLLECTOR_POLL_INTERVAL_SECONDS=30` (el valor por defecto, derivado del `max-age=30` real de los feeds, MP-003) |
| Muestreo de CPU/RSS | `ps` cada 30 s sobre el proceso del colector |

La base de desarrollo (`5433`) y la del replay de MP-020 (`5434`) **no se
tocaron**: la medición escribe exclusivamente en la base desechable. Los
recuentos de la base de desarrollo siguen en `668/484/3/120/0`.

## Lo medido

### Ingesta

| Magnitud | Valor |
|---|---|
| Ciclos completos (3 feeds cada uno) | **21** |
| Ejecuciones de ingesta | 63 |
| Ejecuciones con error | **0** |
| Posiciones de vehículo | 2 671 (127,2 por ciclo) |
| Actualizaciones de viaje | 1 191 (56,7 por ciclo) |
| Avisos de servicio | 22 |
| Eventos de calidad | 145 |

### Recursos del proceso

| Magnitud | Valor |
|---|---|
| RSS máximo | **18,6 MB** |
| RSS medio | 15,0 MB |
| CPU total de la ventana | 21,42 s (5 instancias de proceso) |

**Matiz importante y medido, no supuesto:** de esos 21,42 s, **~6,5 s los gasta
cada arranque** del colector parseando el ZIP GTFS oficial de 15 MB para
resolver los avisos por estación (`_load_madrid_stop_ids`, hallazgo de MP-017).
Las tres instancias largas de la ventana consumieron 7,74 s, 6,56 s y 7,10 s —
es decir, casi todo su consumo fue el arranque, y el sondeo en régimen apenas
cuesta décimas de segundo por ciclo. La ventana incluye **tres reinicios
provocados a propósito** (ver "Recuperación verificada"), así que el 2,6 % de
un núcleo que da la extrapolación está **inflado** por esos arranques: en
operación estable el consumo real es sensiblemente menor.

### Transferencia

| Feed | Bytes por descarga |
|---|---|
| `vehicle_positions.json` | 174 560 |
| `trip_updates.json` | 190 563 |
| `alerts.json` | 68 825 |
| **Total por ciclo** | **433 948 B (≈ 424 KB)** |

**Los tres feeds ignoran `Accept-Encoding: gzip`**: el cuerpo comprimido y el
descomprimido miden exactamente lo mismo en las seis muestras. No hay nada que
optimizar del lado del cliente; es el origen el que no comprime. Se registra
como dato, no como problema a resolver en este hito.

### Almacenamiento

| Magnitud | Valor |
|---|---|
| Crecimiento de PostgreSQL en la ventana | **2 580 480 B (2,46 MB)** |
| Coste por fila en PostgreSQL (con índices) | ≈ 631 B |
| Parquet ZSTD del día medido | 199 989 B para 4 092 filas |
| Coste por fila en Parquet | **≈ 48,9 B** |

La compresión en frío es de aproximadamente **13:1** frente a la tabla
caliente. Es coherente con lo medido en MP-009 (1 272 filas → ~76 KB) a una
escala 3× mayor y con el catálogo Madrid completo, no solo C5.

## Lo proyectado (no observado)

> Proyección lineal desde las 21 ciclos de la ventana. Una captura real de 24 h
> tendría franjas nocturnas con mucho menos tráfico, así que estas cifras son
> probablemente un **techo**, no una media.

| Magnitud | 24 h | 72 h |
|---|---|---|
| Ciclos completos | ≈ 2 203 | ≈ 6 610 |
| Descarga | **912 MB** | **2 736 MB (2,7 GB)** |
| Crecimiento de PostgreSQL caliente | **258 MB** | **775 MB** |
| Filas archivables | ≈ 405 000 | ≈ 1 215 000 |
| Parquet ZSTD resultante | **≈ 19 MB** | **≈ 57 MB** |
| CPU | ≤ 2,6 % de un núcleo (cota alta: incluye tres reinicios provocados) | — |
| RSS | 18,6 MB (no crece con el tiempo: el colector no acumula estado) | — |

### Qué significa esto para el coste real

- **El equipo no es el problema.** 19 MB de RSS y menos del 3 % de un núcleo
  caben en cualquier host, incluido el más barato de cualquier proveedor.
- **El almacenamiento tampoco.** A ~19 MB/día en Parquet, **un año entero de
  histórico frío son ~7 GB**. Con la propuesta de retención de 12 meses de
  `docs/DATA_MODEL.md`, el coste de almacenamiento es de céntimos al mes en
  cualquier almacén de objetos. Esto es exactamente lo que DEC-004 esperaba
  para poder decidirse ("debe fijarse después de medir volumen/coste real");
  la decisión sigue siendo del propietario.
- **Lo que sí cuesta es la transferencia de bajada**: ~0,9 GB/día, ~27 GB/mes.
  Está dentro de la franquicia de casi cualquier VPS, pero no es despreciable
  en un servicio facturado por tráfico.
- **PostgreSQL caliente necesita purga, como ya decidía DEC-011/NOGO-003**: a
  258 MB/día, sin purga la base crecería ~7,5 GB/mes. El modelo
  caliente+Parquet no es una preferencia estética, es lo que hace esto viable.

## Recuperación verificada

La propiedad que define "supervisado" se probó provocando los fallos, no
razonando sobre ellos:

| Fallo provocado | Resultado observado |
|---|---|
| `kill -9` al proceso del colector | El supervisor registró `terminó con código 137 tras 408s (reinicio nº 1)`, esperó 5 s y arrancó un proceso nuevo (PID 18799 → 19602). La ingesta continuó. |
| `docker restart` de PostgreSQL (**antes** de la corrección) | **Defecto real encontrado así.** El colector **no murió**: siguió vivo descartando los tres feeds cada 30 s con `psycopg.OperationalError: the connection is lost`. 90 s después el recuento de `source_ingestion_run` seguía congelado en 42. Ningún supervisor puede rescatar un proceso que no cae. |
| `docker restart` de PostgreSQL (**después** de la corrección) | El colector terminó con **código 75** (`EX_TEMPFAIL`), el supervisor registró `terminó con código 75 tras 69s`, reintentó a los 5 s y la ingesta se reanudó (48 → 51 ejecuciones). |

La corrección está en `services/collector/__main__.py` y es deliberadamente
pequeña: una `psycopg.OperationalError` termina el proceso con un código de
salida distinguible en vez de ser tragada por el `except Exception` que protege
de fallos de un feed. La regresión queda fijada en
`services/collector/tests/test_supervised_loop.py`, que comprueba las dos ramas:
la conexión perdida sale con 75 y sin intentar los demás feeds, y un fallo de un
feed concreto sigue sin tumbar el ciclo.

## Reproducirlo

```bash
docker run -d --name mp021-collector-db --platform linux/amd64 \
  -e POSTGRES_DB=madrid_pulse -e POSTGRES_USER=madrid_pulse \
  -e POSTGRES_PASSWORD=madrid_pulse_local -p 127.0.0.1:5435:5432 \
  -v "$PWD/infra/migrations:/migrations:ro" postgis/postgis:17-3.5
docker exec mp021-collector-db sh -eu -c \
  'for m in /migrations/*.up.sql; do psql -q -v ON_ERROR_STOP=1 -U madrid_pulse -d madrid_pulse -f "$m"; done'

MADRID_PULSE_DATABASE_URL=postgresql://madrid_pulse:madrid_pulse_local@127.0.0.1:5435/madrid_pulse \
MADRID_PULSE_GTFS_SOURCE="$PWD/data/hito-03/replay/fomento_transit.zip" \
  infra/operate/supervise-collector.sh /tmp/mp021-logs &

# …dejar correr, muestreando `ps` cada 30 s en un CSV…

.venv/bin/python infra/operate/measure-cost.py \
  --database-url postgresql://madrid_pulse:madrid_pulse_local@127.0.0.1:5435/madrid_pulse \
  --window-start <inicio ISO> --size-before-bytes <pg_database_size antes> \
  --samples-csv /tmp/rss_samples.csv --parquet-dir /tmp/mp021-archive
```

El contenedor `mp021-collector-db` se creó para esta medición y es desechable;
no se ha borrado ningún contenedor, worktree ni fixture de otra tarea.
