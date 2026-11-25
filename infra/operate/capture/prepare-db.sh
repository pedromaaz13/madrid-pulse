#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
container=mp028-capture
volume=mp028-capture-data
image=postgis/postgis:17-3.5
owner=mp028_capture

if ! docker container inspect "$container" >/dev/null 2>&1; then
  docker run --detach --name "$container" --platform linux/amd64 \
    --publish 127.0.0.1:5466:5432 --volume "$volume:/var/lib/postgresql/data" \
    --env POSTGRES_DB="$owner" --env POSTGRES_USER="$owner" \
    --env POSTGRES_PASSWORD=mp028_capture_local "$image"
fi

spec=$(docker container inspect --format '{{.Config.Image}} {{json .HostConfig.PortBindings}} {{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Type}} {{.Name}} {{.RW}}{{end}}{{end}}' "$container")
expected="$image "'{"5432/tcp":[{"HostIp":"127.0.0.1","HostPort":"5466"}]}'" volume $volume true"
if [[ "$spec" != "$expected" ]]; then
  printf 'La configuración de %s difiere de la base aislada esperada.\n' "$container" >&2
  exit 1
fi
if [[ $(docker container inspect --format '{{.State.Running}}' "$container") != true ]]; then
  docker start "$container"
fi

# La conexión TCP evita el servidor temporal sin red de la inicialización.
for ((i=0; i<60; i++)); do
  if docker exec "$container" pg_isready -q -h 127.0.0.1 -U "$owner" -d "$owner"; then
    break
  fi
  sleep 1
done

# DDL y registro de hashes se confirman juntos. El bloqueo serializa preparaciones.
{
  printf '%s\n' 'SELECT pg_advisory_xact_lock(1297101396);' \
    'CREATE SCHEMA IF NOT EXISTS mp028_capture;' \
    'CREATE TABLE IF NOT EXISTS mp028_capture.migration (name text PRIMARY KEY, sha256 text NOT NULL, applied_at timestamptz NOT NULL DEFAULT now());'
  for migration in infra/migrations/*.up.sql; do
    name=${migration##*/}
    hash=$(shasum -a 256 "$migration")
    hash=${hash%% *}
    printf '%s\n' "DO \$\$ BEGIN IF EXISTS (SELECT 1 FROM mp028_capture.migration WHERE name = '$name' AND sha256 <> '$hash') THEN RAISE EXCEPTION 'Cambió el contenido de $name'; END IF; END \$\$;" \
      "SELECT NOT EXISTS (SELECT 1 FROM mp028_capture.migration WHERE name = '$name') AS apply_migration \\gset" \
      '\if :apply_migration'
    sed -e '/^BEGIN;$/d' -e '/^COMMIT;$/d' "$migration"
    printf '\n%s\n' "INSERT INTO mp028_capture.migration (name, sha256) VALUES ('$name', '$hash');" '\endif'
  done
  printf '%s\n' 'SELECT name, sha256 FROM mp028_capture.migration ORDER BY name;'
} | docker exec -i "$container" psql -X --single-transaction -v ON_ERROR_STOP=1 \
  -U "$owner" -d "$owner" -f -
