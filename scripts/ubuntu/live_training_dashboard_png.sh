#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

INTERVAL=${INTERVAL:-30}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
DASHBOARD=${DASHBOARD:-outputs/reports/live/training_dashboard.png}

export MPLCONFIGDIR="${MPLCONFIGDIR:-$PWD/.cache/matplotlib}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$PWD/.cache}"
export MPLBACKEND="${MPLBACKEND:-Agg}"
mkdir -p "$MPLCONFIGDIR" "$XDG_CACHE_HOME" "$(dirname "$DASHBOARD")"

echo "Live PNG dashboard loop"
echo "  dashboard: $DASHBOARD"
echo "  interval:  ${INTERVAL}s"
echo ""

while true; do
  started_at=$(date -Is)
  if conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.build_live_training_dashboard --out "$DASHBOARD"; then
    echo "[$started_at] updated $DASHBOARD"
  else
    echo "[$started_at] dashboard update failed" >&2
  fi
  sleep "$INTERVAL"
done
