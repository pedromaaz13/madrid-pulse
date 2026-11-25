# MP-023 — Evidencia de ejecución

## Aislamiento registrado antes de las pruebas

- Base: `madrid_pulse`, esquema `public`, rol propietario temporal `mp023` (superusuario creado por la imagen para aplicar PostGIS y las migraciones).
- DSN con credencial ficticia: `postgresql://mp023:mp023_local@127.0.0.1:5451/madrid_pulse`.
- Host `127.0.0.1`, puerto **5451**, imagen local `postgis/postgis:17-3.5`, contenedor propio `mp023-check`. `docker ps --filter publish=5451` no mostró contenedores antes del arranque.
- El puerto no es 5433. El contenedor compartido queda fuera de las ejecuciones. El destino protegido solo se usa como entrada de una prueba interceptada sin conexión.
- Los datos de la prueba viven en el volumen anónimo del contenedor y se eliminan con `docker rm -fv mp023-check`. Migraciones desde cero.
- Despacho solicitado: Codex `gpt-6.2-sol`, esfuerzo `medium`.

## Entrega para revisión

- Código verificado en `7642d53b260f424b73a6b9b2eeeff450993a7165`, desde `aee334e`. El cambio exige una URL y un entorno canónicos, impide el destino compartido por defecto y comprueba el comentario de la base para escrituras en test/replay y para integración.
- Orca informó `gpt-6.2-sol` y `medium` tanto en `launch.requested` como en `launch.effective` para `ctx_ec9cf011f7d8`, según `orca orchestration worker-show --dispatch ctx_ec9cf011f7d8 --json --full`. El proceso Codex se lanzó como `app-server`, sin estos parámetros en su argv.
- Python 3.12.3 y dependencias fijadas en `requirements.txt`, tomadas de un entorno virtual local ya disponible. Node 22.13.1. El worktree de la suite carecía de `data/`.

| Comprobación | Resultado | Evidencia |
|---|---|---|
| PostgreSQL desde cero con ambas migraciones | PASS. PostgreSQL 17.5 y PostGIS 3.5.2 | [postgres.log](postgres.log) |
| Regresión sobre `beb9434` | RED esperado, salida 1. Los tres casos fallan: los arranques intentan entrar en la ruta de conexión/exportación o continúan, el caso de integración se ejecuta en la base sin marca y la configuración acepta el destino local protegido | [RED.log](RED.log) |
| Regresión y arranques reales sobre `7642d53` antes de aplicar la marca | GREEN, 8 casos pasan. Colector, API y snapshotter sin variables salen con códigos 1, 3 y 1. Los recuentos de las cinco tablas hot son cero antes y después. Los dos escritores de replay se detienen también ante la base sin marca | [GREEN.log](GREEN.log) |
| Suite Python de los 28 módulos de CI con marca | PASS. 283 casos, 18 skips, salida 0 | [GREEN.log](GREEN.log) |
| Ingesta del colector y consulta HTTP en la API con URL canónica | PASS. Una observación insertada con el colector real y HTTP 200 para su identificador mediante el TestClient de la API, con la variable obsoleta definida a un valor distinto | [GREEN.log](GREEN.log) |
| Arranque real del snapshotter con base marcada | PASS. Seis ficheros Parquet en un directorio temporal eliminado después de la comprobación | [snapshotter.log](snapshotter.log) |
| Frontend con `npm ci --offline --no-audit --no-fund` | PASS. Lint, typecheck, 89 tests y build. Vite advierte del tamaño de algunos bundles | [frontend.log](frontend.log) |
| Ruff en Python modificado, sintaxis Bash y gobernanza | PASS. 36 casos de gobernanza. Una primera comprobación Ruff sobre todo el repositorio dio 34 avisos en archivos ajenos al cambio (`scratch/` y `packages/geo/tools/render_preview.py`) | [static.log](static.log) |
| Búsqueda literal de `5433` en el árbol versionado, con las exclusiones solicitadas | FAIL literal. Ocho coincidencias preexistentes en coordenadas, una distancia y un ID de nodo repetido en dos relaciones OSM. La comprobación de `5433` como valor aislado devuelve cero coincidencias. Se conservaron las fixtures porque los bytes de las relaciones se usan en los checksums y versiones de geometría | [static.log](static.log) |
| Limpieza del contenedor y volumen, y del worktree RED | PASS. Contenedor, volumen anónimo y worktree eliminado | [cleanup.log](cleanup.log) |

**NO EJECUTADO** GitHub Actions remoto, operación con feeds en vivo y
benchmark que necesita el ZIP oficial. Las verificaciones se ejecutaron
localmente, con capturas congeladas o payloads de prueba y sin contactar
el puerto compartido.

Para repetir la regresión, prepara la base de este informe y aplica las
migraciones, dejando el comentario sin marca. Para RED, copia solo
`tests/e2e/database_isolation_checks.py` a un worktree temporal de
`beb9434` y ejecuta la clase `SafeConfigurationRegressionTests`. Para
GREEN, usa ese mismo arnés desde el commit del cambio. Corre
`SafeConfigurationRegressionTests` y `SafeConfigurationTests` antes de
marcar, y los 28 módulos de CI seguidos de `CanonicalUrlIntegrationTest`
después de marcar. Los logs incluyen los comandos y el SHA-256 del
arnés, que contiene el payload sintético determinista.
