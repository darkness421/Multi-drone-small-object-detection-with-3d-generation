#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT=${REPO_ROOT:-/home/oem/projects/multi-uav-marine-city}
cd "$REPO_ROOT"

OUT_DIR=${AEROGRAPH_PLUMBING_OUT_DIR:-outputs/reasoning/aerograph_prompt_pack_eval_plumbing_test}

python scripts/run_aerograph_prompt_pack.py \
  --provider command \
  --command "python scripts/aerograph_plumbing_provider.py" \
  --out-dir "$OUT_DIR" \
  --resume \
  --retry-unconfigured \
  --checkpoint-every 10 \
  --plumbing-test

python scripts/build_aerograph_reasoner_table.py
python scripts/check_aerograph_nonmock_readiness.py
python scripts/check_paper_artifact_readiness.py
python scripts/build_accv_status_snapshot.py

echo "[AeroGraph plumbing] complete. This output is not paper evidence: $OUT_DIR"
