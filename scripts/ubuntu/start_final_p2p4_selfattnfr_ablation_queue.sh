#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
SESSION=${SESSION:-final-p2p4-selfattnfr-ablation-queue}

mkdir -p outputs/logs/final_p2p4_selfattnfr_ablation_queue outputs/experiments/final_p2p4_selfattnfr_ablation_queue

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n queue \
  "cd '$PWD' && CONDA_ENV='$CONDA_ENV' bash scripts/ubuntu/run_final_p2p4_selfattnfr_ablation_queue.sh; exec bash"

echo "Started final P2P4-SelfAttnFR ablation queue: $SESSION"
echo "Attach with: tmux attach -t $SESSION"
echo "Log: outputs/logs/final_p2p4_selfattnfr_ablation_queue/queue.log"
echo "Plan: outputs/experiments/final_p2p4_selfattnfr_ablation_queue/plan.tsv"
