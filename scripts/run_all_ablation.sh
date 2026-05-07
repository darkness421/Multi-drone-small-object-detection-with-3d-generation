#!/usr/bin/env bash
set -euo pipefail

CONFIG=${1:-configs/com3d_ace_base.yaml}
bash scripts/eval_detector.sh "${CONFIG}"
bash scripts/generate_evidence_tokens.sh "${CONFIG}"
bash scripts/run_graph_fusion.sh "${CONFIG}"
bash scripts/run_ambiguity_eval.sh "${CONFIG}"
bash scripts/run_reobserve_policy.sh "${CONFIG}"
bash scripts/run_vlm_verification.sh "${CONFIG}"

