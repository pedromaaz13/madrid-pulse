#!/usr/bin/env bash
#
# Supervisor portable del colector de Madrid Pulse (MP-021).
#
# `python -m services.collector` ya es un bucle infinito (MP-006) y tolera un
# fallo de red en un feed sin pararse. Lo que NO tolera por sí solo es morir:
# si PostgreSQL se reinicia, la conexión larga se rompe y el proceso termina.
# Este script es la pieza que falta para "continuo supervisado" sin introducir
# ninguna dependencia nueva ni ningún servicio de pago: reinicia el colector
# con retroceso exponencial acotado y deja un registro de cada reinicio.
#
# Es deliberadamente simple y de un solo fichero. En un host con `systemd` o
# `launchd` se prefiere la unidad correspondiente de este mismo directorio
# (`Restart=always` / `KeepAlive`), que además sobrevive a un reinicio del
# equipo; este script cubre el caso de un portátil o una sesión sin permisos
# para instalar servicios.
#
# Uso:
#   infra/operate/supervise-collector.sh [directorio-de-logs]
#
# Variables relevantes (las mismas que `services/collector/config.py`):
#   MADRID_PULSE_DATABASE_URL, MADRID_PULSE_ENV, MADRID_PULSE_GTFS_SOURCE,
#   COLLECTOR_POLL_INTERVAL_SECONDS, COLLECTOR_REQUEST_TIMEOUT_SECONDS
#
# Parar: Ctrl-C, o `kill` al PID de este script (propaga y espera al hijo).

set -euo pipefail

: "${MADRID_PULSE_DATABASE_URL:?Define MADRID_PULSE_DATABASE_URL}"
: "${MADRID_PULSE_ENV:?Define MADRID_PULSE_ENV}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="${1:-${REPO_ROOT}/data/operate/logs}"
PYTHON="${MADRID_PULSE_PYTHON:-${REPO_ROOT}/.venv/bin/python}"

# Retroceso entre reinicios: empieza corto para un fallo transitorio y se
# alarga si el colector muere una y otra vez, para no castigar ni al host ni
# al origen con un bucle de reintentos.
BACKOFF_MIN_S=5
BACKOFF_MAX_S=300

mkdir -p "${LOG_DIR}"
SUPERVISOR_LOG="${LOG_DIR}/supervisor.log"

log() {
  printf '%s supervisor %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "${SUPERVISOR_LOG}" >&2
}

child_pid=""
terminate() {
  log "señal recibida: parando el colector"
  if [ -n "${child_pid}" ] && kill -0 "${child_pid}" 2>/dev/null; then
    kill -TERM "${child_pid}" 2>/dev/null || true
    wait "${child_pid}" 2>/dev/null || true
  fi
  exit 0
}
trap terminate INT TERM

if [ ! -x "${PYTHON}" ]; then
  log "no existe el intérprete ${PYTHON}; defina MADRID_PULSE_PYTHON"
  exit 2
fi

backoff="${BACKOFF_MIN_S}"
restarts=0
log "iniciando; logs en ${LOG_DIR}"

while true; do
  started_at="$(date +%s)"
  set +e
  (cd "${REPO_ROOT}" && PYTHONPATH="${REPO_ROOT}" "${PYTHON}" -m services.collector) \
    >>"${LOG_DIR}/collector.log" 2>&1 &
  child_pid=$!
  wait "${child_pid}"
  status=$?
  set -e
  child_pid=""
  ran_for=$(( $(date +%s) - started_at ))
  restarts=$(( restarts + 1 ))
  log "el colector terminó con código ${status} tras ${ran_for}s (reinicio nº ${restarts})"

  # Si aguantó un rato, el fallo fue puntual: se vuelve al retroceso mínimo.
  if [ "${ran_for}" -ge 60 ]; then
    backoff="${BACKOFF_MIN_S}"
  fi
  log "reintentando en ${backoff}s"
  sleep "${backoff}"
  backoff=$(( backoff * 2 ))
  if [ "${backoff}" -gt "${BACKOFF_MAX_S}" ]; then
    backoff="${BACKOFF_MAX_S}"
  fi
done
