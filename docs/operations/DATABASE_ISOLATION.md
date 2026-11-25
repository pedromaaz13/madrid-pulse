# Aislamiento de PostgreSQL

La API, el colector y el snapshotter requieren `MADRID_PULSE_DATABASE_URL` y
`MADRID_PULSE_ENV`. Valídalas antes de arrancar. Una URL ausente o en blanco
detiene el arranque antes de conectar. Si aún tienes `MADRID_PULSE_DATABASE_DSN`
en tu entorno, quítala y exporta `MADRID_PULSE_DATABASE_URL`. La API solo usa
la URL canónica, incluso cuando están definidas las dos.

Usa una URL `postgresql://rol:contraseña@host:puerto/base` con un único host.
Indica el puerto explícitamente si difiere del estándar de PostgreSQL (5432).
No se admiten servicios libpq ni un destino heredado de `PGHOSTADDR` o
`PGPORT`. Codifica los caracteres reservados de la URL en las credenciales.

| `MADRID_PULSE_ENV` | Uso | Requisito de aislamiento |
|---|---|---|
| `test` | Integración y CI | Marca obligatoria para las suites PostgreSQL, el colector y el snapshotter |
| `replay` | Reprocesar capturas congeladas | Misma marca para herramientas de replay, colector, snapshotter y suites PostgreSQL |
| `dev` | Desarrollo local en una base explícita | Los servicios pueden usar una base propia persistente sin marca |
| `live` | Operación con fuentes en vivo | Los servicios pueden usar una base persistente autorizada sin marca |

Las herramientas `apps.api.tools.replay_three_snapshots` y
`apps.api.tools.build_closure_matrix` requieren la marca en todos los
entornos porque reproducen capturas sobre una base desechable.

`MADRID_PULSE_MODE=replay|live` controla el catálogo y el reloj de la API.
Configúralo por separado. `MADRID_PULSE_ENV` controla el aislamiento y no
cambia las fuentes del colector. Para un replay sin red usa las herramientas
de replay con capturas congeladas.

## Crear una base desechable

Desde la raíz del repositorio, con las dependencias de `requirements.txt`
instaladas, usa un nombre y un puerto libres que controles. El ejemplo usa
credenciales locales ficticias.

```bash
docker run --pull=never --name mp-sandbox -d \
  -p 127.0.0.1:5442:5432 \
  -e POSTGRES_DB=madrid_pulse -e POSTGRES_USER=mp_test \
  -e POSTGRES_PASSWORD=mp_local postgis/postgis:17-3.5

export MADRID_PULSE_ENV=test
export MADRID_PULSE_DATABASE_URL=postgresql://mp_test:mp_local@127.0.0.1:5442/madrid_pulse

# Espera a que este comando indique que PostgreSQL acepta conexiones.
docker exec mp-sandbox pg_isready -h 127.0.0.1 -U mp_test -d madrid_pulse

(
  set -e
  for migration in infra/migrations/*.up.sql; do
    docker exec -i mp-sandbox psql -X -v ON_ERROR_STOP=1 \
      -U mp_test -d madrid_pulse < "$migration"
  done
  python -m infra.operate.mark_disposable_db
)
```

El script requiere el rol propietario de la base y pone el comentario exacto
`madrid-pulse:disposable` en la base que indica la URL. Ejecútalo solo sobre
una base recién creada y desechable. La marca es un control operativo contra
errores de destino. El colector la consulta en la conexión que usará para
ingestar. El snapshotter la comprueba antes de tocar el archivo Parquet. Los
tests PostgreSQL la comprueban antes de ejecutar el caso. Si falta la marca,
la configuración es inválida o la base no está disponible, el caso se salta
con un diagnóstico explícito. CI fija `MADRID_PULSE_REQUIRE_DB=1` para que
esos casos fallen. Los skips por ausencia de datos de pruebas se mantienen.
El comentario se consulta sin modificar datos.

Para terminar, elimina únicamente el contenedor y el volumen anónimo que
creaste en el ejemplo:

```bash
docker rm -fv mp-sandbox
```

## Base compartida en 127.0.0.1:5433

Consérvala tal como está. Queda fuera de pruebas, replay, migraciones y limpieza.
La validación rechaza el puerto 5433 en cualquier host antes de conectar, ya
sea un nombre, un alias o una dirección IPv4 o IPv6. El mensaje de rechazo
remite a esta guía. La única excepción es una confirmación expresa del
operador mediante `MADRID_PULSE_ALLOW_SHARED_DEV_DB=1` en `dev` o `live`.
Deja la variable sin definir en las plantillas de operación.

El criterio de cero literales `5433` fuera de la base compartida excluye
`docs/`, `infra/docker/`, `tests/fixtures/` y
`apps/web/src/__fixtures__/`. Los dos literales de código autorizados son
las constantes explícitas de `packages/database.py` y del arnés
`tests/e2e/database_isolation_checks.py`.

## Un colector por base

F1 requiere que el orden de los runs del directo coincida con su orden de
confirmación. El proceso de polling adquiere el bloqueo asesor de sesión
PostgreSQL 1297101395 antes de abrir los feeds. Un segundo proceso sale con
código 1 y el diagnóstico «Ya hay otro colector activo». El cierre de la
conexión libera el bloqueo, también tras una caída. Las cargas históricas
deben dirigirse a una base de replay separada.

El productor registra GTFS, versiones de geometría por patrón y umbrales de
la envolvente. El colector usa el núcleo completo para procesar las alertas.
La API puede seleccionar otra línea mediante MADRID_PULSE_SHORT_NAME. Para
un tren concreto se compara únicamente la geometría de su patrón. Si falta
el GTFS, el colector avisa y conserva el dato bruto. Sin huella verificable,
tanto la primera respuesta como la caducada retienen en el ancla.

La migración 0004 clasifica un run al insertarlo comparando started_at con
el máximo visible entre ids menores. El colector permite un retroceso del
reloj de MADRID_PULSE_RETRO_TOLERANCE_S segundos (2 por defecto, inclusive).
Un cambio NTP mayor puede clasificar una ingesta en directo como retroactiva.
La tolerancia también puede admitir una carga histórica antedatada dentro de
ese margen. Esta heurística necesita el escritor único y cargas de replay
separadas. Un escritor externo con hora actual y commit tardío puede eludirla.

### Diagnóstico de exclusión del colector

El bloqueo pertenece a la sesión PostgreSQL del proceso de polling. Un
SIGSTOP detiene Python y deja viva esa sesión. El supervisor puede repetir
la salida de «otro colector activo». En la base afectada, identifica el
backend titular antes de actuar:

```sql
SELECT a.pid AS backend_pid, a.application_name, a.client_addr, a.client_port,
       a.backend_start, a.state
FROM pg_locks l JOIN pg_stat_activity a ON a.pid = l.pid
WHERE l.locktype = 'advisory' AND l.granted AND l.classid = 0
  AND l.objid = 1297101395 AND l.objsubid = 1
  AND a.datname = current_database();
```

Identifica el PID del colector en el supervisor y contrasta conexión y puerto.
Reanuda el proceso suspendido con SIGCONT si debe continuar, o para su
supervisor y termina ese proceso para sustituirlo. Verifica que desapareció
el titular antes de arrancar el sustituto. Para una sesión medio abierta
sin proceso recuperable, un operador con permisos puede terminar el backend
verificado con pg_terminate_backend. Es un PID del servidor, distinto del PID
del colector. El bloqueo necesita conexión dedicada o pooling de sesión;
el pooling por transacción rompe esa condición.
