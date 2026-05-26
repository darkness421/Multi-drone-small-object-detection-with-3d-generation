#!/usr/bin/env bash
set -euo pipefail

export WAIT_FOR=${WAIT_FOR:-server-large-comparison}
export SESSION=${SESSION:-server-top3-proposed-screening}
export CONFIG=${CONFIG:-configs/experiments/top3_proposed_detector_screening.yaml}
export GPUS=${GPUS:-0}
export SKIP_COMPLETED=${SKIP_COMPLETED:-1}
export COMPLETED_RESULTS_CSV=${COMPLETED_RESULTS_CSV:-outputs/experiments/server_with_proposed_results.csv,outputs/experiments/top3_proposed_results.csv}
export WAIT_AFTER_START=${WAIT_AFTER_START:-0}
export RESTART_VIEWER=${RESTART_VIEWER:-1}
export RESTART_DUAL_VIEW=${RESTART_DUAL_VIEW:-1}

cd "$(dirname "$0")/../.."
exec bash scripts/ubuntu/train_proposed_ablation_after_session.sh
