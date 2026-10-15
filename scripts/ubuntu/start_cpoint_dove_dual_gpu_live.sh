#!/usr/bin/env bash
set -euo pipefail

SESSION="${SESSION:-cvpr-cpoint-dove}"
RUN_TAG="${RUN_TAG:-$(date +%Y%m%d_%H%M%S)}"
DOVE_REPO="${DOVE_REPO:-/home/oem/projects/dove-wm-cvpr-2027}"
CPOINT_PACKAGE="${CPOINT_PACKAGE:-/home/oem/projects/cpoint-cvpr-2027/CPOINT_CORE_EVIDENCE_CORRECTED_M3_20261015_FINAL}"
CPOINT_RUN="${CPOINT_RUN:-/mnt/ssd2/meme_comparison/results/cpoint_m3_seadronessee_unseen_20261015}"
E1_MODELS="${E1_MODELS:-/mnt/ssd2/meme_comparison/results/cpoint_v21_corrected_local_review_20261010/models_complete}"
CAPTURE_ROOT="${CAPTURE_ROOT:-/home/oem/UAV/uav_marinecity/outputs/isaac_exports}"
CHECKPOINT="${CHECKPOINT:-/home/oem/projects/multi-uav-marine-city/outputs/detectors/server_yolov11_p2p4_balanced/20260610_073629_proposed_p2p4_balanced_selfattn_tiny_frelu_yolo11l_visdrone_yolov11_p2_balanced_seed123/ultralytics/weights/best.pt}"
PYTHON="${PYTHON:-/home/oem/anaconda3/envs/com3d-ace/bin/python}"

DOVE_OUTPUT="$DOVE_REPO/outputs/dove_wm/detector_proxy_pilot_${RUN_TAG}"
CPOINT_OUTPUT="$CPOINT_PACKAGE/followup/seadronessee_exact_score_audit_${RUN_TAG}"
LOG_ROOT="$DOVE_REPO/outputs/live/cpoint_dove_${RUN_TAG}"
mkdir -p "$LOG_ROOT"

for path in "$DOVE_REPO" "$CPOINT_PACKAGE" "$CPOINT_RUN" "$CAPTURE_ROOT" "$CHECKPOINT" "$PYTHON"; do
  if [[ ! -e "$path" ]]; then
    echo "Missing required path: $path" >&2
    exit 2
  fi
done

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  exit 0
fi

printf '%s\n' \
  "run_tag=$RUN_TAG" \
  "dove_output=$DOVE_OUTPUT" \
  "cpoint_output=$CPOINT_OUTPUT" \
  "dove_gpu=physical_gpu0" \
  "cpoint_lane=physical_gpu1_reserved; exact-statistics audit is CPU-bound" \
  > "$LOG_ROOT/run.env"

tmux new-session -d -s "$SESSION" -n live \
  "bash -o pipefail -c 'cd $DOVE_REPO; CUDA_VISIBLE_DEVICES=0 $PYTHON scripts/run_dove_wm_detector_proxy_pilot.py --capture-root $CAPTURE_ROOT --checkpoint $CHECKPOINT --output-dir $DOVE_OUTPUT --device 0 2>&1 | tee $LOG_ROOT/dove_gpu0.log; rc=\${PIPESTATUS[0]}; echo; echo DOVE-WM_exit_status=\$rc; echo Output=$DOVE_OUTPUT; exec bash'"

tmux split-window -h -t "$SESSION:live.0" \
  "bash -o pipefail -c 'cd $CPOINT_PACKAGE/code; CUDA_VISIBLE_DEVICES=1 $PYTHON scripts/analyze_seadronessee_exact_and_scores.py --package-root $CPOINT_PACKAGE --run-root $CPOINT_RUN --model-root $E1_MODELS/seed20261009 --model-root $E1_MODELS/seed20261010 --model-root $E1_MODELS/seed20261011 --output-dir $CPOINT_OUTPUT 2>&1 | tee $LOG_ROOT/cpoint_gpu1.log; rc=\${PIPESTATUS[0]}; echo; echo C_POINT_exit_status=\$rc; echo Output=$CPOINT_OUTPUT; exec bash'"

tmux split-window -v -t "$SESSION:live.0" \
  "watch -n 2 --color 'nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw --format=csv,noheader,nounits; echo; echo GPU_processes; nvidia-smi pmon -c 1'"

tmux split-window -v -t "$SESSION:live.1" \
  "while true; do clear; printf 'C_POINT + DOVE-WM live run: %s\\n\\n' '$RUN_TAG'; printf '%s\\n' '--- DOVE GPU0 ---'; tail -n 10 '$LOG_ROOT/dove_gpu0.log' 2>/dev/null || true; printf '%s\\n' '--- C_POINT analysis lane ---'; tail -n 10 '$LOG_ROOT/cpoint_gpu1.log' 2>/dev/null || true; sleep 2; done"

tmux select-layout -t "$SESSION:live" tiled
tmux set-option -t "$SESSION" remain-on-exit on

echo "Started $SESSION"
echo "DOVE-WM GPU0 output: $DOVE_OUTPUT"
echo "C_POINT output: $CPOINT_OUTPUT"
echo "Logs: $LOG_ROOT"

if [[ -n "${DISPLAY:-}" ]] && command -v gnome-terminal >/dev/null 2>&1; then
  nohup gnome-terminal --title="C_POINT + DOVE-WM live" -- tmux attach-session -t "$SESSION" \
    >"$LOG_ROOT/terminal-launch.log" 2>&1 &
fi
