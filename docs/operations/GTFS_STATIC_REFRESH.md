# Refresco del GTFS estático de Renfe

Consulta `GET /api/v1/health` en modo live. Programa el refresco cuando
`gtfs_status` sea `expiring`. `MADRID_PULSE_GTFS_EXPIRING_DAYS` configura
el aviso y su valor por defecto es 7. El día `gtfs_valid_until` está incluido
en la ventana, según el calendario de Madrid. Si la API sigue en ejecución
después de esa fecha, health, catálogo y snapshot declaran `expired`.

1. Desde la raíz del repositorio, con el entorno Python de la API y su
   configuración de red, prepara un ZIP candidato en un directorio local.
   Conserva el ZIP activo mientras lo verificas.

   ```sh
   mkdir -p data/gtfs_static
   gtfs_refresh_dir=$(mktemp -d "$PWD/data/gtfs_static/refresh.XXXXXX")
   gtfs_refresh_zip="$gtfs_refresh_dir/fomento_transit.zip"
   python -m apps.api.tools.fetch_gtfs_static "$gtfs_refresh_zip"
   ```

2. Carga el candidato con la misma configuración que usa el servicio
   y comprueba sus fechas y SHA-256. Este comando valida la configuración y
   el catálogo sin conectarse a PostgreSQL. Usa la URL y el entorno que ya
   tiene configurados la API.

   ```sh
   MADRID_PULSE_MODE=live MADRID_PULSE_GTFS_SOURCE="$gtfs_refresh_zip" python -c '
   from apps.api.config import ApiConfig
   from apps.api.gtfs_source import load_network
   network = load_network(ApiConfig.from_env())
   print(network.gtfs_version, network.gtfs_valid_from, network.gtfs_valid_until)
   '
   ```

   Confirma que la vigencia cubre la fecha actual y se extiende más allá del
   ZIP activo. Si falla la carga o el proveedor aún publica la misma ventana,
   conserva la configuración activa y revisa el origen antes de reintentar.

3. Conserva el candidato en una ruta estable y configura
   `MADRID_PULSE_GTFS_SOURCE` con esa ruta. Reinicia la API para cargarlo.
   Si el colector también usa esta variable para resolver avisos por estación,
   actualiza su ruta y reinícialo para que use el mismo ZIP.

4. Comprueba en `/api/v1/health` el SHA-256, las fechas y `gtfs_status`.
   Confirma que `/api/v1/catalog` publica la versión nueva y que
   `/api/v1/snapshot` referencia ese catálogo y declara el mismo estado.
   Conserva el ZIP anterior para revertir el cambio mientras siga vigente.
