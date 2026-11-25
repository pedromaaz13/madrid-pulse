#!/usr/bin/env bash
#
# Archivo diario de un día de servicio (MP-021).
#
# Ejecuta `python -m services.snapshotter <fecha>`, que exporta las cinco
# tablas hot a Parquet y recalcula los cuatro agregados. Es **idempotente por
# día de servicio** (ver `services/snapshotter/export.py`): volver a lanzarlo
# sobre el mismo día produce exactamente el mismo archivo, así que se puede
# reintentar sin riesgo tras un fallo.
#
# Sin argumento archiva el día de servicio de AYER en Europe/Madrid, que es lo
# que corresponde a una ejecución de madrugada: el día en curso todavía no ha
# terminado y archivarlo daría un día incompleto rotulado como cerrado.
#
# Uso:
#   infra/operate/daily-archive.sh [YYYY-MM-DD]

set -euo pipefail

: "${MADRID_PULSE_DATABASE_URL:?Define MADRID_PULSE_DATABASE_URL}"
: "${MADRID_PULSE_ENV:?Define MADRID_PULSE_ENV}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON="${MADRID_PULSE_PYTHON:-${REPO_ROOT}/.venv/bin/python}"

if [ "$#" -ge 1 ]; then
  SERVICE_DATE="$1"
else
  SERVICE_DATE="$(TZ=Europe/Madrid date -v-1d +%Y-%m-%d 2>/dev/null \
    || TZ=Europe/Madrid date -d 'yesterday' +%Y-%m-%d)"
fi

cd "${REPO_ROOT}"
PYTHONPATH="${REPO_ROOT}" exec "${PYTHON}" -m services.snapshotter "${SERVICE_DATE}"
