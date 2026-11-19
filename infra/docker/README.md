# PostgreSQL/PostGIS local

El Compose de Madrid Pulse usa un proyecto, una red, un volumen y un puerto host
propios. El puerto es `127.0.0.1:5433`; no colisiona ni interactúa con el Postgres
de `traza-app` publicado en `54322`. La imagen oficial `postgis/postgis:17-3.5`
se fija a `linux/amd64` porque esa etiqueta no publica manifiesto ARM64; Docker
Desktop la ejecuta mediante emulación en Macs Apple Silicon.

Desde la raíz del repositorio:

```bash
docker compose -p madrid-pulse -f infra/docker/docker-compose.yml up -d
docker compose -p madrid-pulse -f infra/docker/docker-compose.yml ps
```

Para detener únicamente Madrid Pulse, conservando sus datos:

```bash
docker compose -p madrid-pulse -f infra/docker/docker-compose.yml down
```

No se debe usar `docker compose down` sin `-p madrid-pulse` y sin el fichero
explícito. Tampoco se debe usar `--volumes` salvo que se quiera borrar de forma
deliberada la base local de Madrid Pulse. Estos comandos no seleccionan, paran ni
eliminan ningún contenedor `*-traza-app`.
