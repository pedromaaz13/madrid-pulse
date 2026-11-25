# Captura local supervisada de Renfe (MP-028)

Cada jornada usa una sesión de al menos 120 minutos. Repite la captura en
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
orden y registra sus nombres y hashes en `mp028_capture.migration`. Una segunda
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
| `MADRID_PULSE_GTFS_SOURCE` | `/Users/matu/Documents/DATA/madrid-pulse/data/gtfs_static/fomento_transit.zip` |
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
calculada. El arranque valida que el ZIP cubre la fecha local actual.
[SHA-256 del ZIP](../research/MP-003-probe-findings.md#11-cierre-de-pendientes-por-mp-010-2026-11-19) · [Vigencia del ZIP del kit](../audits/hito-03/PRODUCT_AUDIT.md)

## Arranque, supervisión y parada

```bash
/Users/matu/Documents/DATA/madrid-pulse/.venv/bin/python infra/operate/capture/run-session.py 5 --smoke
/Users/matu/Documents/DATA/madrid-pulse/.venv/bin/python infra/operate/capture/run-session.py 121
```

Ejecuta el primer comando para el smoke. El segundo deja un minuto de margen
sobre las dos horas para la inicialización del colector. Para las jornadas
largas, mantén el equipo despierto y supervisa el fichero `collector.log`
cuya carpeta imprime el script. Comprueba que siguen apareciendo runs de
los tres feeds. El smoke prueba el bloqueo MP-025a con un segundo arranque
protegido contra polling. Espera el código 1 y el mensaje «Ya hay otro
colector activo», registrados en `collector-lock.log`. Tras la parada,
`database_lock_released` confirma que se puede volver a adquirir el bloqueo.

El supervisor queda en primer plano y guarda los PID del supervisor y del
colector en `session.json`. Ctrl+C, SIGTERM o SIGHUP al supervisor interrumpen
la sesión de forma ordenada. Al alcanzar el plazo, el supervisor envía SIGINT al
colector y espera que libere la conexión y cierre sus transacciones. Si no
responde en 15 s, fuerza la salida y la registra. Una salida anticipada del
colector o una parada manual produce una sesión incompleta y una salida del
supervisor distinta de cero. Revisa el log antes de reanudar. Evita arrancar
manualmente otro colector o el supervisor continuo de MP-021 sobre esta base.
[Operación supervisada de MP-021](../../infra/operate/README.md) · [Coste medido](../evidence/mp-021-coste-colector-continuo.md)

## Evidencia y reanudación entre días

Los artefactos se conservan en
`/Users/matu/Documents/DATA/madrid-pulse/data/capture/`, ignorado por Git.
La fecha corresponde al arranque en Europe/Madrid. Las jornadas se guardan
en `<fecha>/session-<n>/` con numeración creciente y el smoke en
`<fecha>/smoke/`. Cada carpeta contiene `collector.log`,
`metadata.json` (identidad y configuración inicial), `session.json` (PID,
intervalo y parada) y `manifest.json`. La copia local del ZIP se guarda
por SHA-256 en `gtfs/`. Las observaciones y eventos se conservan en el
volumen. Si el ZIP activo cambia durante la ventana, el supervisor lo
registra y devuelve un error.

El manifiesto incluye HEAD, estado del árbol, configuración sin
credenciales, vigencia del ZIP,
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

Las pruebas del manifiesto usan datos sintéticos y no requieren red ni base.

```bash
python3 -m unittest discover -s infra/operate/capture -v
```

1. Al terminar una jornada, confirma el cierre, revisa el manifiesto y
   conserva la carpeta aunque la sesión haya sido interrumpida. Si se perdió
   la conexión al cerrar, una vez restaurada la base se puede regenerar el
   manifiesto con el mismo Python y `infra/operate/capture/capture_manifest.py
   <carpeta-de-sesión>`. Requiere que `session.json` tenga hora de fin.
2. Para la siguiente fecha, ejecuta el mismo comando de 121 min. El script
   vuelve a verificar la base, consulta sus migraciones y asigna una carpeta
   nueva. Si Docker estaba detenido, arráncalo y conserva el volumen.
3. Si el GTFS requiere refresco, prepara y valida un candidato mientras el
   colector esté parado, según el [protocolo de refresco](GTFS_STATIC_REFRESH.md).
   Sustituye el archivo activo entre sesiones y verifica el nuevo identificador
   en el siguiente manifiesto. Conserva ambos ZIP locales y sus ventanas.
4. Evalúa cada fecha con su duración, cobertura por feed y huecos. Si una
   sesión no alcanza la duración requerida, repite una sesión completa sin
   borrar la anterior. El intervalo nocturno entre jornadas queda sin
   observación.

La captura es local. Quedan fuera el hosting, los servicios de pago, las
exportaciones públicas, el replay dentro de esta base y cualquier purga.
La redistribución requeriría la atribución de Renfe Operadora (CC BY 4.0) y
las condiciones del portal. Consulta también la atribución de OSM para las
geometrías. [Atribución](../legal/ATTRIBUTION.md)
