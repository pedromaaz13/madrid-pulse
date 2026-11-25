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
| `dev` | Desarrollo local en una base explícita | Puede usar una base propia persistente |
| `live` | Operación con fuentes en vivo | Puede usar una base persistente autorizada |

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
    psql -X -v ON_ERROR_STOP=1 "$MADRID_PULSE_DATABASE_URL" -f "$migration"
  done
  python -m infra.operate.mark_disposable_db
)
```

El script requiere el rol propietario de la base y pone el comentario exacto
`madrid-pulse:disposable` en la base que indica la URL. Ejecútalo solo sobre
una base recién creada y desechable. La marca es un control operativo contra
errores de destino. El colector la consulta en la conexión que usará para
ingestar. El snapshotter la comprueba antes de tocar el archivo Parquet. Los
tests PostgreSQL la comprueban antes de ejecutar el caso y se saltan con un
diagnóstico explícito si falta. El comentario se consulta sin modificar datos.

Para terminar, elimina únicamente el contenedor y el volumen anónimo que
creaste en el ejemplo:

```bash
docker rm -fv mp-sandbox
```

## Base compartida en 127.0.0.1:5433

Consérvala tal como está. Queda fuera de pruebas, replay, migraciones y limpieza.
`test` y `replay` rechazan el destino antes de conectar. En `dev` o `live`
también se rechaza, salvo confirmación expresa del operador mediante
`MADRID_PULSE_ALLOW_SHARED_DEV_DB=1`. Déjala sin definir en los entornos de
pruebas y en las plantillas de operación.
