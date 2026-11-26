# MP-036 · Comandos de ejecución offline

## PostgreSQL desechable

Ejecutar con las dependencias Python locales ya disponibles. Rutas
privadas del dump y del ZIP solo disponibles en la máquina de captura.

```bash
capture=/Users/matu/Documents/DATA/madrid-pulse/data/capture/2026-11-26
dump="$capture/analysis/session-1-20261126T090138Z.dump"
manifest="$capture/session-1/manifest.json"
gtfs=/Users/matu/Documents/DATA/madrid-pulse/data/gtfs_static/fomento_transit.zip
shasum -a 256 -c "$dump.sha256"
docker run --pull=never --name mp036-isolated -d -p 127.0.0.1:5459:5432 \
  -e POSTGRES_DB=mp036_capture -e POSTGRES_USER=mp_test \
  -e POSTGRES_PASSWORD=mp_local postgis/postgis:17-3.5
until docker exec mp036-isolated pg_isready -U mp_test -d mp036_capture; do sleep 1; done
docker exec mp036-isolated createdb -U mp_test mp036_bench
docker exec mp036-isolated createdb -U mp_test mp036_ci
export MADRID_PULSE_ENV=test MADRID_PULSE_REQUIRE_DB=1
for database in mp036_capture mp036_bench mp036_ci; do
  export MADRID_PULSE_DATABASE_URL="postgresql://mp_test:mp_local@127.0.0.1:5459/$database"
  for migration in infra/migrations/*.up.sql; do
    if [[ $database == mp036_bench && $migration == *0004* ]]; then
      docker exec -i mp036-isolated psql -X -v ON_ERROR_STOP=1 -U mp_test -d "$database" \
        < docs/evidence/mp-026b/carga.sql
    fi
    docker exec -i mp036-isolated psql -X -v ON_ERROR_STOP=1 -U mp_test -d "$database" < "$migration"
  done
  python -m infra.operate.mark_disposable_db
done
docker cp "$dump" mp036-isolated:/tmp/mp036.dump
docker exec mp036-isolated sh -ec "pg_restore -l /tmp/mp036.dump | awk '/TABLE DATA public/ && !/spatial_ref_sys/' > /tmp/data.toc
pg_restore -L /tmp/data.toc --single-transaction --disable-triggers -U mp_test -d mp036_capture /tmp/mp036.dump"
docker exec mp036-isolated psql -X -U mp_test -d mp036_capture -c 'ANALYZE'
docker exec mp036-isolated psql -X -U mp_test -d mp036_bench -c 'ANALYZE'
```

## RED y GREEN

```bash
root=$PWD
base=$(mktemp -d /tmp/mp036-base.XXXXXX)
verified=$(mktemp -d /tmp/mp036-verified.XXXXXX)
git archive 4bc8612 | tar -x -C "$base"
git archive ee92097 | tar -x -C "$verified"
cp apps/api/tests/test_anchor_history.py "$base/apps/api/tests/"
cp -R tests/fixtures/mp036 "$base/tests/fixtures/"
export MADRID_PULSE_DATABASE_URL=postgresql://mp_test:mp_local@127.0.0.1:5459/mp036_ci
(cd "$base" && python -m unittest apps.api.tests.test_anchor_history -v)
(cd "$verified" && python -m unittest $(awk '/^            [a-z].* \\/ {print $1}' .github/workflows/ci.yml) -v)
(cd "$verified" && python scripts/governance/check_docs.py)
(cd "$verified" && python -m unittest tests.governance.test_governance -v)
```

## Clasificación y coste

```bash
segment_file=infra/operate/validation/segments.py
mkdir -p "$base/$(dirname "$segment_file")"
git show "9587b3e:$segment_file" > "$base/$segment_file"
export MADRID_PULSE_DATABASE_URL=postgresql://mp_test:mp_local@127.0.0.1:5459/mp036_capture
export MADRID_PULSE_ENV=replay MADRID_PULSE_MODE=replay MADRID_PULSE_SHORT_NAME=''
export MADRID_PULSE_GTFS_SOURCE="$gtfs"
(cd "$base" && PYTHONPATH=. python "$root/docs/evidence/mp-036/classify.py" "$manifest")
(cd "$verified" && PYTHONPATH=".:$base" python "$root/docs/evidence/mp-036/classify.py" "$manifest")

unset MADRID_PULSE_GTFS_SOURCE MADRID_PULSE_SHORT_NAME
export MADRID_PULSE_ENV=test
export MADRID_PULSE_DATABASE_URL=postgresql://mp_test:mp_local@127.0.0.1:5459/mp036_bench
(cd "$base" && PYTHONPATH=. python "$root/docs/evidence/mp-036/bench.py")
(cd "$verified" && PYTHONPATH=. python "$root/docs/evidence/mp-036/bench.py")

docker container rm --force --volumes mp036-isolated
docker ps -a --filter 'name=^/mp036-isolated$' --format '{{.Names}}'
python -c 'from shutil import rmtree; from sys import argv; rmtree(argv[1]); rmtree(argv[2])' "$base" "$verified"
```

## Verificación del delta de revisión

Usa el mismo procedimiento de preparación con un contenedor propio
`mp036-delta` publicado solo en `127.0.0.1:5459`. Mantén la carga
sintética inicial hasta terminar todas las mediciones truncadas.
Los comandos siguientes usan la raíz del worktree y las dependencias
Python y Node instaladas localmente.

```bash
root=$PWD
evidence="$root/docs/evidence/mp-036"
local_run=$(mktemp -d /tmp/mp036-delta-check.XXXXXX)
for entry in base:4bc8612 red:a7e01b8 final:121c438; do
  label=${entry%%:*}
  revision=${entry##*:}
  mkdir "$local_run/$label"
  git archive "$revision" | tar -x -C "$local_run/$label"
done
cp apps/api/tests/test_anchor_history.py "$local_run/red/apps/api/tests/"
export MADRID_PULSE_ENV=test MADRID_PULSE_REQUIRE_DB=1 MADRID_PULSE_MODE=replay
export MADRID_PULSE_DATABASE_URL=postgresql://mp_test:mp_local@127.0.0.1:5459/mp036_ci
(cd "$local_run/red" && python -m unittest apps.api.tests.test_anchor_history -v)
(cd "$local_run/final" && python -m unittest $(awk '/^            [a-z].* \\/ {print $1}' .github/workflows/ci.yml) -v)
(cd "$local_run/final" && python scripts/governance/check_docs.py)
(cd "$local_run/final" && python -m unittest tests.governance.test_governance -v)
(cd "$local_run/final" && python -c 'import json; from apps.api.main import app; print(json.dumps(app.openapi(), indent=2, sort_keys=True), end="")' > "$local_run/openapi.json")
cmp apps/api/openapi.json "$local_run/openapi.json"

export MADRID_PULSE_ENV=replay MADRID_PULSE_SHORT_NAME=''
export MADRID_PULSE_DATABASE_URL=postgresql://mp_test:mp_local@127.0.0.1:5459/mp036_capture
export MADRID_PULSE_GTFS_SOURCE="$gtfs"
segment_file=infra/operate/validation/segments.py
mkdir -p "$local_run/base/$(dirname "$segment_file")"
git show "9587b3e:$segment_file" > "$local_run/base/$segment_file"
(cd "$local_run/final" && PYTHONPATH=".:$local_run/base" python "$evidence/classify.py" "$manifest")
for kind in samples frames; do
  for label in base red final; do
    (cd "$local_run/$label" && PYTHONPATH=. python "$evidence/impact.py" "$kind" "$local_run/$label/$kind.json")
  done
  python "$evidence/impact.py" "$kind" "$local_run/base/$kind.json" "$local_run/red/$kind.json" "$local_run/final/$kind.json"
done
for label in base red final; do
  (cd "$local_run/$label" && PYTHONPATH=. python "$evidence/bench_real.py")
done

unset MADRID_PULSE_GTFS_SOURCE MADRID_PULSE_SHORT_NAME
export MADRID_PULSE_ENV=test MADRID_PULSE_DATABASE_URL=postgresql://mp_test:mp_local@127.0.0.1:5459/mp036_bench
for mode in truncated complete; do
  if [[ "$mode" == complete ]]; then
    docker exec -i mp036-delta psql -X -v ON_ERROR_STOP=1 -U mp_test -d mp036_bench < "$evidence/bench_complete.sql"
  fi
  for label in base red final; do
    (cd "$local_run/$label" && PYTHONPATH=. python "$evidence/bench_delta.py" "$mode")
  done
done
docker container rm --force --volumes mp036-delta
python -c 'from shutil import rmtree; from sys import argv; rmtree(argv[1])' "$local_run"
```

Las trazas de `impact.py` se usan para comparar y se eliminan con los
directorios temporales. Solo se versionan contadores y los casos
puntuales del dictamen.
