#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT=${REPO_ROOT:-/home/oem/projects/multi-uav-marine-city}
QUEUE_LOOP=${QUEUE_LOOP:-0}
QUEUE_INTERVAL_SEC=${QUEUE_INTERVAL_SEC:-900}
QUEUE_MAX_ITER=${QUEUE_MAX_ITER:-1}
OVERLEAF_WORKTREE=${OVERLEAF_WORKTREE:-/tmp/accv-overleaf-sync}

cd "$REPO_ROOT"

LOG_DIR="$REPO_ROOT/outputs/logs/accv_paper_gate_queue"
mkdir -p "$LOG_DIR"

run_step() {
  local name="$1"
  shift
  echo
  echo "===== ${name} ====="
  if "$@"; then
    echo "[OK] ${name}"
  else
    local code=$?
    echo "[WARN] ${name} failed with exit code ${code}"
    FAILED_STEPS+=("${name}:${code}")
  fi
}

run_once() {
  local ts
  ts=$(date +"%Y%m%d_%H%M%S")
  local log_path="$LOG_DIR/run_${ts}.log"
  FAILED_STEPS=()

  {
    echo "[ACCV queue] started_at=$(date -Is)"
    echo "[ACCV queue] repo=$REPO_ROOT"
    echo "[ACCV queue] branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
    echo "[ACCV queue] head=$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
    echo "[ACCV queue] loop=$QUEUE_LOOP interval_sec=$QUEUE_INTERVAL_SEC"

    run_step "latex patch integrity" python scripts/check_latex_patch_integrity.py
    run_step "paper artifact readiness" python scripts/check_paper_artifact_readiness.py
    run_step "MarineCity 3D completion readiness" python scripts/check_marinecity_3d_completion_readiness.py
    run_step "AeroGraph non-mock readiness" python scripts/check_aerograph_nonmock_readiness.py
    run_step "external gate capabilities" python scripts/check_external_gate_capabilities.py
    run_step "AeroGraph reasoner table refresh" python scripts/build_aerograph_reasoner_table.py
    run_step "MarineCity simulation dashboard" python scripts/build_marinecity_simulation_dashboard.py
    run_step "live detector dashboard" env PYTHONPATH=. python scripts/build_live_training_dashboard.py --out outputs/reports/live/training_dashboard.png
    run_step "ACCV workflow snapshot" python scripts/build_accv_status_snapshot.py
    run_step "ACCV remaining gates queue" python scripts/build_accv_remaining_gates_queue.py

    echo
    echo "===== Overleaf linked repo status ====="
    if [[ -d "$OVERLEAF_WORKTREE/.git" || -f "$OVERLEAF_WORKTREE/.git" ]]; then
      git -C "$OVERLEAF_WORKTREE" log --oneline -3 || true
      git -C "$OVERLEAF_WORKTREE" status --short --branch || true
    else
      echo "[WARN] Overleaf worktree not found: $OVERLEAF_WORKTREE"
    fi

    echo
    if [[ ${#FAILED_STEPS[@]} -eq 0 ]]; then
      echo "[ACCV queue] all local gates completed"
    else
      echo "[ACCV queue] completed with warnings: ${FAILED_STEPS[*]}"
    fi
    echo "[ACCV queue] log=$log_path"
    echo "[ACCV queue] finished_at=$(date -Is)"
  } 2>&1 | tee "$log_path"
}

iteration=0
while true; do
  iteration=$((iteration + 1))
  run_once

  if [[ "$QUEUE_LOOP" != "1" ]]; then
    break
  fi
  if [[ "$QUEUE_MAX_ITER" != "0" && "$iteration" -ge "$QUEUE_MAX_ITER" ]]; then
    break
  fi
  sleep "$QUEUE_INTERVAL_SEC"
done
