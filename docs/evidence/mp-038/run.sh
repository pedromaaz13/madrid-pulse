#!/usr/bin/env bash
# Ejecutar desde cualquier directorio, con las dependencias Python instaladas localmente.
set -euo pipefail
umask 077

if [[ $# -lt 3 || $# -gt 5 || ! "$3" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo "Uso: $0 CAPTURA GTFS_ZIP IDENTIFICADOR [--operativa-j1 | --jornada2 DIRECTORIO_SESION]" >&2
    exit 2
fi
capture="$(cd "$1" && pwd -P)"
gtfs="$(cd "$(dirname "$2")" && pwd -P)/$(basename "$2")"
root="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
analysis="$capture/analysis"
dump="$analysis/session-1-20261126T090138Z.dump"
manifest="$capture/session-1/manifest.json"
mode="${4:-}"
dump_sha=95b578603f6cd8f0faee93f7207c2313b61c51056dd72fe13f2bbfb452922ea1
manifest_sha=5de84ef60f84769cf962f05e20fd1b7ba910832441e13a2883f9c2eaf2cdbb6e
case "$mode:$#" in
    :3|--operativa-j1:4) ;;
    --jornada2:5)
        session="$(cd "$5" && pwd -P)"
        dump="$analysis/session-2-20261127T095451Z.dump"
        manifest="$session/manifest.json"
        dump_sha=6a325074c48c021428084af9741772187204f8abc8862cd22376e7ff922ca75f
        manifest_sha=60cabc28a997d8bc0b28c6c2ac11890214932c6091bcc06ebf1923fddab18cbe
        (cd "$analysis" && shasum -a 256 -c "$(basename "$dump").sha256")
        (cd "$session" && shasum -a 256 -c capture.dump.sha256)
        cmp "$dump" "$session/capture.dump"
        ;;
    *) echo "Modo de replay no válido" >&2; exit 2 ;;
esac
output="$analysis/mp038-$3.json"
port="${MP038_PORT:-5470}"
case "$port" in
    5470|5471) ;;
    *) echo 'MP038_PORT debe ser 5470 o 5471' >&2; exit 2 ;;
esac
container="mp038-evaluation-$port"
python_bin="$(command -v "${MP038_PYTHON:-python}")"
test -f "$gtfs"
test ! -e "$output"
test ! -e "$output.sha256"
if docker ps -a --filter "name=^/${container}$" --format '{{.Names}}' | grep -q .; then
    echo "El nombre del contenedor está ocupado: $container" >&2
    exit 1
fi
if lsof -nP "-iTCP:$port" -sTCP:LISTEN; then
    echo "El puerto local $port está ocupado" >&2
    exit 1
fi

tmp="$(mktemp -d /tmp/mp038.XXXXXXXX)"
baseline="$tmp/baseline"
container_id=""
volume=""
cleanup() {
    local code=$?
    trap - EXIT
    if [[ -n "$container_id" ]]; then
        docker rm -fv "$container_id" || code=1
        if docker inspect "$container_id" >/dev/null 2>&1 ||
           docker volume inspect "$volume" >/dev/null 2>&1 ||
           lsof -nP "-iTCP:$port" -sTCP:LISTEN; then
            code=1
        fi
    fi
    if [[ -d "$baseline" ]]; then
        git -C "$root" worktree remove "$baseline" || code=1
    fi
    if [[ ! -d "$baseline" ]]; then
        rm -rf "$tmp"
    fi
    exit "$code"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

if [[ "$mode" != --jornada2 ]]; then
    shasum -a 256 -c "$dump.sha256"
fi
printf '%s  %s\n' "$dump_sha" "$dump" "$manifest_sha" "$manifest" | shasum -a 256 -c -
find "$capture" -type f -exec shasum -a 256 {} + > "$tmp/originals.sha256"
shasum -a 256 "$gtfs" >> "$tmp/originals.sha256"
cp "$dump" "$tmp/copy.dump"
cmp "$dump" "$tmp/copy.dump"

container_id="$(docker run --pull=never --name "$container" --label madrid-pulse.task=MP-038 -d \
    -p "127.0.0.1:$port:5432" -e POSTGRES_DB=mp038 -e POSTGRES_USER=mp_test \
    -e POSTGRES_PASSWORD=mp_local postgis/postgis:17-3.5)"
volume="$(docker inspect -f '{{range .Mounts}}{{.Name}}{{end}}' "$container_id")"
test "$(docker port "$container_id" 5432/tcp)" = "127.0.0.1:$port"
for ((n = 0; n < 60; n++)); do
    if docker exec "$container_id" pg_isready -h 127.0.0.1 -U mp_test -d mp038 >/dev/null; then
        break
    fi
    sleep 1
done
docker exec "$container_id" pg_isready -h 127.0.0.1 -U mp_test -d mp038
for migration in "$root"/infra/migrations/*.up.sql; do
    docker exec -i "$container_id" psql -X -v ON_ERROR_STOP=1 -U mp_test -d mp038 < "$migration"
done

export MADRID_PULSE_ENV=replay MADRID_PULSE_MODE=replay MADRID_PULSE_SHORT_NAME=""
export MP038_PORT="$port"
export MADRID_PULSE_DATABASE_URL="postgresql://mp_test:mp_local@127.0.0.1:$port/mp038"
export MADRID_PULSE_GTFS_SOURCE="$gtfs" PYTHONPATH="$root"
if [[ -n "$mode" ]]; then
    unset MADRID_PULSE_STOP_ZONE_RADIUS_M MADRID_PULSE_MIN_DWELL_S MADRID_PULSE_CANCEL_MAX_AGE_S
    export MADRID_PULSE_ANCHOR_HISTORY_DEPTH=256 MADRID_PULSE_ANCHOR_REACQUIRE_SAMPLES=2
    git -C "$root" diff --exit-code 0c518fa -- apps packages services infra/migrations
fi
cd "$root"
"$python_bin" -m infra.operate.mark_disposable_db
docker exec "$container_id" psql -XAt -U mp_test -d mp038 -c \
    "select current_database(),current_schema(),current_user,shobj_description(oid, 'pg_database') from pg_database where datname=current_database()"
docker cp "$tmp/copy.dump" "$container_id:/tmp/copy.dump"
docker exec "$container_id" sh -ec 'pg_restore -l /tmp/copy.dump | awk "/TABLE DATA public/ && !/spatial_ref_sys/" > /tmp/data.toc
pg_restore -L /tmp/data.toc --single-transaction --disable-triggers -U mp_test -d mp038 /tmp/copy.dump'

git worktree add --detach "$baseline" 4bc86128d44a9b83f8f9747df5cf83ce593f0194
git diff --exit-code 4bc8612 HEAD -- infra/migrations
for variant in baseline correction; do
    tree="$root"
    if [[ "$variant" = baseline ]]; then tree="$baseline"; fi
    (
        cd "$tree"
        trace_args=()
        if [[ -n "$mode" ]]; then trace_args+=(--session-audit); fi
        "$python_bin" -m infra.operate.validation.mp038_trace ${trace_args[@]+"${trace_args[@]}"} "$manifest" "$tmp/copy.dump" > "$tmp/$variant.json"
        if [[ "$mode" == --jornada2 ]]; then
            "$python_bin" -m infra.operate.validation.mp038_streaks --session-only "$manifest" > "$tmp/$variant-streaks.json"
        elif [[ -z "$mode" ]]; then
            "$python_bin" -m infra.operate.validation.mp038_streaks "$manifest" > "$tmp/$variant-streaks.json"
        fi
    )
    echo "PASS replay $variant"
done
if [[ -z "$mode" || "$mode" == --jornada2 ]]; then
    "$python_bin" -m infra.operate.validation.mp038_streaks "$tmp/baseline-streaks.json" \
        "$tmp/correction-streaks.json" > "$tmp/streaks.json"
fi
if [[ -n "$mode" ]]; then
    "$python_bin" -m infra.operate.validation.mp038_session "$tmp/baseline.json" \
        "$tmp/correction.json" "$tmp/result.json" "$tmp/streaks.json"
else
    "$python_bin" -m infra.operate.validation.mp038_compare "$tmp/baseline.json" \
        "$tmp/correction.json" "$tmp/streaks.json" > "$tmp/result.json"
fi
if [[ "$mode" == --jornada2 ]]; then cmp "$dump" "$session/capture.dump"; fi
cmp "$dump" "$tmp/copy.dump"
shasum -a 256 -c "$tmp/originals.sha256"
(
    cd "$analysis"
    set -o noclobber
    cat "$tmp/result.json" > "$(basename "$output")"
    shasum -a 256 "$(basename "$output")" > "$(basename "$output.sha256")"
    shasum -a 256 -c "$(basename "$output.sha256")"
)
