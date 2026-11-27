# Captura local supervisada de Renfe (MP-028)

Cada jornada requiere al menos 120 minutos de cobertura efectiva. Repite la captura en
al menos tres fechas distintas de Europe/Madrid. El smoke de 5 a 10 minutos
comprueba el circuito antes de la primera jornada. Reserva las sesiones con
servicio activo para obtener vehículos y cambios de ancla. La comprobación
posterior MP-025b necesita 500 pares válidos como mínimo y un salto mediano
al llegar el ancla de hasta 200 m. El smoke no mide ese criterio.
[Correspondencia del hito](../H4_MP_MAPPING.md) · [Criterios del modelo](../adr/0014-amendment-stop-state.md#8-criterios-de-aceptación-de-mp-025a)

## Preparación

Ejecuta desde la raíz del worktree, con Docker local y un Python con las
dependencias de `requirements.txt` del repositorio. En el equipo de captura
puedes usar el entorno existente del checkout principal.

```bash
infra/operate/capture/prepare-db.sh
docker port mp028-capture
```

El script crea o reutiliza el contenedor `mp028-capture` con
`postgis/postgis:17-3.5` (linux/amd64), el volumen `mp028-capture-data` y la
publicación TCP `127.0.0.1:5466`. Comprueba imagen, montaje y publicación
antes de reutilizarlo. Aplica las migraciones up de `infra/migrations/` en
orden en el esquema `public` y registra sus nombres y hashes en
`mp028_capture.migration`. Una segunda
ejecución conserva los datos y comprueba los hashes. Si la preparación falla,
consulta `docker logs mp028-capture` y vuelve a ejecutar el script al resolver
la causa. Conserva el contenedor y el volumen incluso ante una incidencia.
La base compartida del puerto 5433, `madrid-pulse-postgres-1` y el Compose del
proyecto quedan fuera del protocolo.
[Aislamiento de PostgreSQL](DATABASE_ISOLATION.md)

El supervisor fija estas variables en el proceso de captura. El usuario y la
contraseña del DSN son ficticios, para este contenedor local.

| Variable | Valor |
|---|---|
| `MADRID_PULSE_ENV` | `live` |
| `MADRID_PULSE_DATABASE_URL` | `postgresql://mp028_capture:mp028_capture_local@127.0.0.1:5466/mp028_capture` |
| `MADRID_PULSE_GTFS_SOURCE` | Copia archivada por SHA-256 del ZIP elegido para la sesión |
| `COLLECTOR_POLL_INTERVAL_SECONDS` | `30` |
| `COLLECTOR_REQUEST_TIMEOUT_SECONDS`, `COLLECTOR_MAX_RETRIES`, `COLLECTOR_BACKOFF_BASE_SECONDS` | Valores del colector (10 s, 3 y 1 s) |

Se leen las posiciones, actualizaciones de viaje y alertas públicas de
Renfe; se persiste el ámbito de Cercanías Madrid que aplica el colector.
La pausa de 30 s empieza tras cada ronda de tres feeds. Los reintentos de
transporte usan el retroceso del colector dentro de esa ronda. El catálogo
se calcula con la API para todo el núcleo Madrid y el perfil P-024 con
los defaults de producción.

El SHA-256 esperado para el smoke es
`58ac554356acddfffb2411f48ada26b5ff4655549e6957372906cf7a38e4ba4e`.
Para ese ZIP, `apps/api` calcula la vigencia inclusiva
**2026-11-19 a 2026-12-18**, tanto para Madrid completo como para C5.
La ventana **2026-11-20 a 2026-12-19** de la planificación corresponde a
otra evidencia de GTFS. La captura usa el ZIP indicado y su vigencia
calculada. El arranque valida que el ZIP cubre la fecha local actual. El supervisor
comprueba la vigencia durante la captura y solicita el cierre al detectar una
fecha local fuera de la ventana inclusiva.
[SHA-256 del ZIP](../research/MP-003-probe-findings.md#11-cierre-de-pendientes-por-mp-010-2026-11-19) · [Vigencia del ZIP del kit](../audits/hito-03/PRODUCT_AUDIT.md)

## Arranque, supervisión y parada

```bash
/Users/matu/Documents/DATA/madrid-pulse/.venv/bin/python infra/operate/capture/run-session.py 5 --smoke
/Users/matu/Documents/DATA/madrid-pulse/.venv/bin/python infra/operate/capture/run-session.py 120 --max-civil-minutes 360 --gap-seconds 120
```

Ejecuta el primer comando para un smoke con 5 minutos efectivos y un tope
civil de 15 minutos por defecto. El segundo fija el objetivo de una jornada
en 120 minutos efectivos. Por defecto el tope civil es 360 minutos y el
umbral de huecos es 120 segundos. Arranca las jornadas en la ventana
confirmada por el propietario, mantén el equipo despierto y comprueba en
`collector.log` que siguen apareciendo runs de los tres feeds. El smoke
prueba el bloqueo del colector con un segundo arranque
protegido contra polling. Espera el código 1 y el mensaje «Ya hay otro
colector activo», registrados en `collector-lock.log`. Tras la parada,
`database_lock_released` confirma que se puede volver a adquirir el bloqueo.

El supervisor queda en primer plano y guarda los PID del supervisor y del
colector en `session.json`. Al alcanzar el objetivo efectivo o el tope civil,
o al recibir Ctrl+C, SIGTERM o SIGHUP, envía SIGINT al colector y espera a que
cierre sus transacciones y libere la conexión. Si no responde en 15 s, fuerza
la salida y la registra. `stop_reason` recoge el disparador, por ejemplo
`effective_target`, `civil_limit`, `gtfs_out_of_validity`, `collector_exit`,
`wall_clock_reversed` o el nombre de la señal. El código 0 exige el objetivo
efectivo, una parada limpia, el SHA-256 del GTFS verificado, un volcado y un
manifiesto, y ausencia de errores de cierre o errores de ingesta sin explicar.
`completed`, `closure_errors`, `unexplained_errors` y el código del colector
permiten diagnosticar una sesión incompleta. Evita arrancar
manualmente otro colector o el supervisor continuo de MP-021 sobre esta base.
[Operación supervisada de MP-021](../../infra/operate/README.md) · [Coste medido](../evidence/mp-021-coste-colector-continuo.md)

### Recuperar un colector huérfano

Si el arranque rechaza el bloqueo del fichero `.mp028.lock`, usa
`lsof <ruta-de-capture>/.mp028.lock` para identificar el supervisor que lo
mantiene abierto. Envía SIGINT al supervisor activo para que pueda cerrar
su propia sesión. Conserva el fichero de bloqueo.

Si el supervisor anterior desapareció y PostgreSQL conserva el bloqueo
`1297101395`, el arranque informa del PID del backend, del puerto cliente y
de `application_name`, que en las sesiones nuevas incluye el PID local del
colector. El PID del backend pertenece al contenedor. Para identificar el
proceso local, contrasta el PID de la aplicación o el `collector_pid` del
`session.json` anterior con `ps -p <PID> -o pid,ppid,lstart,command` y, si
procede, con `lsof -nP -a -p <PID> -iTCP:5466`. La consulta de solo lectura
permite comprobar qué backend retiene el bloqueo antes y después de la parada.

```bash
docker exec mp028-capture psql -X -U mp028_capture -d mp028_capture -c "
SELECT l.pid AS backend_pid, a.application_name, a.client_port
FROM pg_locks l JOIN pg_stat_activity a USING (pid)
WHERE l.locktype = 'advisory' AND l.granted AND a.datname = current_database()
  AND l.classid = 0 AND l.objid = 1297101395 AND l.objsubid = 1"
```

Una vez identificado el proceso local y confirmado que la captura anterior
ha quedado huérfana, usa `kill -INT <PID-local>`. Espera a que se cierre y
repite la consulta. Si el proceso persiste o no puedes identificarlo con
seguridad, revisa su bitácora con el propietario antes de intervenir. El
supervisor mantiene el bloqueo intacto y rechaza el arranque mientras se
retenga. Conserva el contenedor, el volumen y la evidencia anterior.

## Evidencia y reanudación entre días

Los artefactos se conservan en
`/Users/matu/Documents/DATA/madrid-pulse/data/capture/`, ignorado por Git.
La fecha corresponde al arranque en Europe/Madrid. Las jornadas se guardan
en `<fecha>/session-<n>/` con numeración creciente y el smoke en
`<fecha>/smoke-<n>/`. Cada carpeta de captura contiene `collector.log`,
`metadata.json` (identidad y configuración inicial), `session.json` (PID,
intervalo y parada) y `manifest.json`. Si PostgreSQL falla al cierre, el
manifiesto conserva la cobertura observada por el supervisor y deja en
`null` las métricas que requieren la consulta final.
El supervisor archiva el GTFS como `gtfs/<sha256>.zip` y usa esa copia durante
toda la captura. El manifiesto incluye la ruta original, la ruta archivada,
el SHA-256 y la vigencia. El cierre verifica de nuevo el hash de la copia
utilizada.

Al cerrar el colector y comprobar que dejó libre el bloqueo, el supervisor
ejecuta `pg_dump` de solo lectura y guarda `capture.dump` en formato custom
y `capture.dump.sha256` en el directorio de la sesión. El dump contiene una
instantánea acumulada de la base dedicada hasta ese cierre. Usa el intervalo
del manifiesto para aislar la jornada al analizar una restauración. Un segundo
intento valida el par existente y conserva los ficheros. Si el volcado falla,
la sesión queda incompleta. Un volcado tomado tras más ingestión representaría
otro corte de la base.

El manifiesto v2 registra en `collector` el HEAD, la rama (o `null` en
HEAD separado), si el árbol tenía cambios y la versión del perfil
(`profile_version`, SHA-256 de la huella exacta). También incluye la
configuración sin credenciales, la vigencia del ZIP,
versión GTFS, hash del catálogo de geometría, geometrías utilizables por
patrón, huella exacta de MP-025a y su SHA-256, umbrales P-024, migraciones,
periodo UTC y Madrid, intentos y errores, filas calientes, vehículos únicos y
eventos de calidad. Las filas de observación se atribuyen por run y los
eventos de calidad por fecha UTC en la misma ventana. El denominador por feed
suma los intentos persistidos y los fallos inesperados identificados en el
log. El porcentaje queda en `null` si no hubo intentos. Los intervalos
superiores a 60 s entre inicios de ciclos correctos incluyen los extremos de
la sesión. Esos huecos hacen visibles las interrupciones aunque el
porcentaje de los intentos efectuados sea alto. Los errores de reintento
son fallos de peticiones individuales y pueden coexistir con un ciclo correcto.
Las rondas iniciadas se cuentan a partir del primer feed, posiciones.

`civil_duration_s` es el tiempo de pared desde el arranque hasta el cierre
del colector. El tope civil inicia la parada, que puede tomar hasta 15 s
adicionales en condiciones normales. `effective_coverage_s` suma los
intervalos entre los inicios de dos rondas consecutivas correctas. Una
ronda correcta tiene los tres feeds en orden, con transacciones confirmadas,
estado `ok` y la huella esperada. El tiempo de arranque, la cola tras la
última ronda y los intervalos cortados por fallos o interrupciones quedan
fuera de la suma. Un fallo de feed registrado o reintentos de transporte
explicados permiten seguir recogiendo cobertura. Los fallos inesperados,
la pérdida de base, una huella incoherente y los errores sin clasificar
impiden completar la sesión.

`suspension_gaps` guarda los extremos UTC, la duración del intervalo entre
muestras y el avance de pared menos el avance monotónico. Una diferencia
superior a 2 s indica una discontinuidad de reloj. También se registra una
pausa de supervisión superior al umbral de ciclos aunque ambos relojes
avancen juntos. Una corrección de reloj puede producir la misma señal que
una suspensión. `cycle_gaps` guarda los intervalos superiores al umbral sin
rondas correctas, incluidos los extremos de la sesión. Para los pares de
MP-025b, exige que ambos puntos pertenezcan al mismo tramo de
`coverage_segments`. Aplica esos tramos sobre UTC y conserva el GTFS y el
perfil registrados para cada sesión.

Las pruebas del manifiesto y la simulación del supervisor usan datos
sintéticos y no requieren red ni base.

```bash
python3 -m unittest discover -s infra/operate/capture -v
```

1. Al terminar una jornada, confirma el cierre, revisa el manifiesto y
   conserva la carpeta aunque la sesión haya sido interrumpida. Si se perdió
   la conexión al cerrar, una vez restaurada la base se puede regenerar el
   manifiesto con el mismo Python y `infra/operate/capture/capture_manifest.py
   <carpeta-de-sesión>`. Requiere que `session.json` tenga hora de fin.
2. Para la siguiente fecha autorizada, usa el mismo objetivo de 120 min efectivos. El script
   vuelve a verificar la base, consulta sus migraciones y asigna una carpeta
   nueva. Si Docker estaba detenido, arráncalo y conserva el volumen.
3. Si el GTFS requiere refresco, prepara y valida un candidato mientras el
   colector esté parado, según el [protocolo de refresco](GTFS_STATIC_REFRESH.md).
   Conserva el ZIP anterior y entrega la ruta del candidato al supervisor
   con `--gtfs-source <ruta-al-nuevo-zip>`. Verifica el identificador y la
   vigencia nuevos en el siguiente manifiesto.
4. Evalúa cada fecha con su cobertura efectiva, cobertura por feed y huecos.
   Si queda incompleta, conserva la sesión y repite en la siguiente ventana
   confirmada por el propietario. El intervalo nocturno entre jornadas queda
   sin observación.

La captura es local. Quedan fuera el hosting, los servicios de pago, las
exportaciones públicas, el replay dentro de esta base y cualquier purga.
La redistribución requeriría la atribución de Renfe Operadora (CC BY 4.0) y
las condiciones del portal. Consulta también la atribución de OSM para las
geometrías. [Atribución](../legal/ATTRIBUTION.md)
