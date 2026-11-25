# Operación continua supervisada — propuesta ejecutable (MP-021)

Este directorio contiene todo lo necesario para mantener el colector de
Madrid Pulse funcionando de forma **continua y supervisada**, y para medir lo
que cuesta hacerlo. Es el entregable 5 de MP-021.

> **Estado honesto, antes que nada.** Lo que hay aquí está *ejecutado y medido
> en local*. **No** hay ningún host persistente contratado, ningún servicio de
> pago, ningún despliegue público, y por tanto **ninguna operación 24/7
> verificada**. Ver "Qué NO está desplegado" al final.

## Los tres estados, que no son el mismo

`SIGUIENTES-HITOS.md` exige declararlos por separado, y aquí se hace:

| Estado | Qué significa | Dónde está Madrid Pulse hoy |
|---|---|---|
| **Demo local** | Se ejecuta a mano, mientras alguien mira | Alcanzado desde MP-007 |
| **Operación local supervisada** | Arranca sola, se reinicia sola, archiva sola, en el equipo del propietario | **Alcanzado en MP-021**: las piezas de este directorio, ejecutadas y medidas |
| **24/7 verificado** | Host persistente, medido durante días, con disponibilidad demostrada | **NO alcanzado.** Requiere decisión del propietario sobre coste y licencias (ADR-0007) |

## Qué pieza hace qué

| Fichero | Para qué | Dónde aplica |
|---|---|---|
| `supervise-collector.sh` | Supervisor portable: reinicia el colector si muere, con retroceso exponencial acotado y bitácora de reinicios | Cualquier equipo, sin permisos especiales |
| `daily-archive.sh` | Archiva un día de servicio (export + los cuatro agregados). Por omisión, el de ayer en Europe/Madrid | Cualquier equipo |
| `com.madridpulse.collector.plist.template` | Agente `launchd`: `KeepAlive` reinicia el colector y lo arranca al iniciar sesión | macOS (el equipo real disponible hoy) |
| `com.madridpulse.archive.plist.template` | Agente `launchd`: archivo diario a las 03:15 locales | macOS |
| `madrid-pulse-collector.service.template` | Unidad `systemd` con `Restart=always` y endurecimiento básico | Linux, cuando exista un host autorizado |
| `madrid-pulse-archive.{service,timer}.template` | Temporizador `systemd` del archivo diario, con `Persistent=true` | Linux |
| `measure-cost.py` | **Mide** una ventana real y extrapola a 24/72 h, marcando la extrapolación como tal | Cualquiera |

### Por qué hace falta un supervisor

`python -m services.collector` ya es un bucle infinito que tolera un fallo de
red en un feed sin pararse (MP-006). Lo que no tolera por sí solo es **morir**:
mantiene una conexión PostgreSQL larga y, si la base se reinicia, el proceso
termina. "Continuo" significa que algo lo vuelve a levantar. Eso es todo lo que
añaden estas piezas — ninguna reimplementa el colector ni cambia su
comportamiento.

### Por qué el archivo diario se puede reintentar sin miedo

`services/snapshotter/export.py` reemplaza de forma atómica el subárbol
`date=<fecha>` de cada tabla, y los cuatro agregados se reescriben con orden
explícito. Reprocesar el mismo día dos veces produce un archivo byte-idéntico
(verificado con test real contra PostgreSQL: `services/snapshotter/tests/test_idempotency.py`).
Si una ejecución se pierde porque el equipo estaba apagado, basta con lanzarla
a mano con la fecha correspondiente.

## Arranque rápido (operación local)

Define la URL de una base autorizada en otro puerto. En las plantillas de
servicio, sustituye también `<<DEPLOYMENT_ENV>>` por el entorno elegido.
Consulta [Aislamiento de PostgreSQL](../../docs/operations/DATABASE_ISOLATION.md).

```bash
# 1. Supervisor del colector (deja el proceso en primer plano; Ctrl-C lo para)
MADRID_PULSE_ENV=dev MADRID_PULSE_DATABASE_URL=postgresql://madrid_pulse:...@127.0.0.1:5442/madrid_pulse \
MADRID_PULSE_GTFS_SOURCE="$PWD/data/gtfs_static/fomento_transit.zip" \
  infra/operate/supervise-collector.sh

# 2. Archivo del día anterior, con el núcleo Madrid completo
MADRID_PULSE_ENV=dev MADRID_PULSE_DATABASE_URL=postgresql://madrid_pulse:...@127.0.0.1:5442/madrid_pulse \
MADRID_PULSE_GTFS_SOURCE="$PWD/data/gtfs_static/fomento_transit.zip" \
MADRID_PULSE_SHORT_NAME= \
SNAPSHOTTER_OUTPUT_DIR="$PWD/data/parquet" \
  infra/operate/daily-archive.sh

# 3. Medir lo que cuesta (ver docs/evidence/mp-021-coste-colector-continuo.md)
MADRID_PULSE_ENV=dev MADRID_PULSE_DATABASE_URL=postgresql://madrid_pulse:...@127.0.0.1:5442/madrid_pulse \
PYTHONPATH="$PWD" .venv/bin/python infra/operate/measure-cost.py \
  --window-start 2026-11-23T05:23:00Z \
  --size-before-bytes <pg_database_size antes> \
  --samples-csv data/operate/rss_samples.csv \
  --parquet-dir data/parquet
```

`MADRID_PULSE_SHORT_NAME=` **vacío** es lo que hace que el mart cubra las 12
líneas / 42 rutas del catálogo Madrid y no solo el piloto C5
(`SnapshotterConfig.line_filter`).

## Coste medido

La medición real y sus cifras viven en
[`docs/evidence/mp-021-coste-colector-continuo.md`](../../docs/evidence/mp-021-coste-colector-continuo.md).
Resumen de lo que ese documento demuestra: el colector cabe holgadamente en el
equipo del propietario y su consumo de red y disco es pequeño; el coste real de
pasar a 24/7 no es técnico sino de **host y licencias**, que es precisamente la
decisión que corresponde al propietario.

## Qué NO está desplegado (y por qué)

- **No hay host persistente.** No se ha contratado ningún VPS, contenedor
  gestionado, base de datos gestionada ni almacenamiento de objetos. ADR-0007
  reserva al propietario toda decisión real de coste o licencia, y el encargo
  de MP-021 lo repite de forma explícita.
- **No se ha instalado el agente `launchd` en el equipo del propietario.**
  Instalar un agente que arranca solo en su sesión es un cambio en **su**
  máquina, no un artefacto del repositorio. Las plantillas están listas y la
  instalación son dos órdenes documentadas arriba.
- **No se declara "24/7 verificado".** La ventana medida es de minutos, no de
  días. Un portátil que se suspende interrumpe la captura, y eso aparece en el
  histórico como lo que es: un hueco de cobertura, visible y contado
  (`/api/v1/history/days` → `circulations_unobserved`).
- **DEC-004 (retención del histórico) sigue abierta.** La medición de este hito
  da por fin cifras reales con las que decidirla, pero la decisión es del
  propietario.

## Qué haría falta para pasar a 24/7 (decisión del propietario)

1. Elegir host persistente y aceptar su coste (ADR-0007: gate real).
2. Revisar la licencia de uso del feed de Renfe para operación continua no
   supervisada (`docs/legal/`), que no es lo mismo que el uso de desarrollo.
3. Fijar DEC-004 con las cifras ya medidas.
4. Operar y **medir** varios días seguidos antes de llamarlo "verificado".
