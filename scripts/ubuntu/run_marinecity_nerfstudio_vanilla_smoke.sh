#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

GPU=${GPU:-0}
ENV_NAME=${ENV_NAME:-marinecity-nerfstudio}
DATA_DIR=${DATA_DIR:-outputs/experiments/3d_generation/marinecity_real_capture_neural3d}
OUT_DIR=${OUT_DIR:-outputs/experiments/3d_generation/nerfstudio_native_runs}
LOG_DIR=${LOG_DIR:-outputs/logs/marinecity_nerfstudio_gpu0}
EXPERIMENT=${EXPERIMENT:-marinecity_vanilla_nerf_smoke}
TIMESTAMP=${TIMESTAMP:-$(date +%Y%m%d_%H%M%S)}
MAX_ITERS=${MAX_ITERS:-100}
CAMERA_SCALE=${CAMERA_SCALE:-0.5}

DATA_ABS=$(realpath "$DATA_DIR")
OUT_ABS=$(realpath -m "$OUT_DIR")
LOG_ABS=$(realpath -m "$LOG_DIR")
mkdir -p "$OUT_ABS" "$LOG_ABS"

TRAIN_LOG="$LOG_ABS/${EXPERIMENT}_${TIMESTAMP}_train.log"
EVAL_LOG="$LOG_ABS/${EXPERIMENT}_${TIMESTAMP}_eval.log"
RAW_EVAL_JSON="$OUT_ABS/${EXPERIMENT}_${TIMESTAMP}_ns_eval.json"
METRIC_JSON="$OUT_ABS/${EXPERIMENT}_${TIMESTAMP}_metric_row.json"
RENDER_DIR="$OUT_ABS/${EXPERIMENT}_${TIMESTAMP}_renders"
MANIFEST="$OUT_ABS/${EXPERIMENT}_${TIMESTAMP}_manifest.json"

echo "[nerfstudio-native] start train $(date -Is) gpu=$GPU env=$ENV_NAME data=$DATA_ABS out=$OUT_ABS max_iters=$MAX_ITERS" | tee "$TRAIN_LOG"

CUDA_VISIBLE_DEVICES="$GPU" \
conda run --no-capture-output -n "$ENV_NAME" \
  ns-train vanilla-nerf \
    --data "$DATA_ABS" \
    --output-dir "$OUT_ABS" \
    --experiment-name "$EXPERIMENT" \
    --timestamp "$TIMESTAMP" \
    --max-num-iterations "$MAX_ITERS" \
    --steps-per-save "$MAX_ITERS" \
    --steps-per-eval-all-images "$MAX_ITERS" \
    --steps-per-eval-batch "$MAX_ITERS" \
    --vis tensorboard \
    --viewer.quit-on-train-completion True \
    --machine.device-type cuda \
    --pipeline.datamanager.camera-res-scale-factor "$CAMERA_SCALE" \
    nerfstudio-data \
  2>&1 | tee -a "$TRAIN_LOG"

CONFIG_HOST=$(find "$OUT_ABS" -path "*$EXPERIMENT*$TIMESTAMP*config.yml" -print -quit)
if [[ -z "$CONFIG_HOST" || ! -f "$CONFIG_HOST" ]]; then
  echo "[nerfstudio-native] config.yml not found after training" | tee -a "$TRAIN_LOG"
  exit 2
fi

echo "[nerfstudio-native] start eval $(date -Is) config=$CONFIG_HOST" | tee "$EVAL_LOG"
CUDA_VISIBLE_DEVICES="$GPU" \
conda run --no-capture-output -n "$ENV_NAME" \
  ns-eval \
    --load-config "$CONFIG_HOST" \
    --output-path "$RAW_EVAL_JSON" \
    --render-output-path "$RENDER_DIR" \
  2>&1 | tee -a "$EVAL_LOG"

conda run --no-capture-output -n "$ENV_NAME" python - "$RAW_EVAL_JSON" "$METRIC_JSON" "$CONFIG_HOST" "$RENDER_DIR" "$TRAIN_LOG" "$EVAL_LOG" "$MAX_ITERS" <<'PY'
import json
import sys
from pathlib import Path

raw_path = Path(sys.argv[1])
out_path = Path(sys.argv[2])
config_path = Path(sys.argv[3])
render_dir = Path(sys.argv[4])
train_log = Path(sys.argv[5])
eval_log = Path(sys.argv[6])
max_iters = int(sys.argv[7])

payload = json.loads(raw_path.read_text(encoding="utf-8"))
results = payload.get("results", payload)

def first(*keys):
    for key in keys:
        if key in results:
            return results[key]
        if key in payload:
            return payload[key]
    return ""

row = {
    "method": "nerf",
    "scene": "marinecity_real_capture",
    "status": "complete_native_vanilla_nerf_smoke",
    "PSNR": first("psnr", "PSNR"),
    "SSIM": first("ssim", "SSIM"),
    "LPIPS": first("lpips", "LPIPS"),
    "FPS": first("fps", "FPS"),
    "train_time_min": "",
    "VRAM_GB": "",
    "disk_GB": "",
    "checkpoint": str(config_path),
    "render_dir": str(render_dir),
    "notes": f"Nerfstudio vanilla-nerf native CUDA 12.8 smoke, max_iters={max_iters}; train_log={train_log}; eval_log={eval_log}",
}
out_path.write_text(json.dumps(row, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({"metric_row": str(out_path), "row": row}, indent=2, ensure_ascii=False))
PY

python scripts/import_marinecity_3d_metrics.py "$METRIC_JSON" --overwrite
python scripts/build_marinecity_3d_results_table.py
python scripts/check_marinecity_3d_completion_readiness.py

cat > "$MANIFEST" <<JSON
{
  "status": "nerfstudio_vanilla_smoke_complete",
  "updated_at": "$(date -Is)",
  "gpu": "$GPU",
  "env_name": "$ENV_NAME",
  "data_dir": "$DATA_ABS",
  "out_dir": "$OUT_ABS",
  "experiment": "$EXPERIMENT",
  "timestamp": "$TIMESTAMP",
  "max_iters": $MAX_ITERS,
  "camera_scale": "$CAMERA_SCALE",
  "config": "$CONFIG_HOST",
  "raw_eval_json": "$RAW_EVAL_JSON",
  "metric_json": "$METRIC_JSON",
  "render_dir": "$RENDER_DIR",
  "train_log": "$TRAIN_LOG",
  "eval_log": "$EVAL_LOG"
}
JSON

echo "[nerfstudio-native] complete $(date -Is) manifest=$MANIFEST"
