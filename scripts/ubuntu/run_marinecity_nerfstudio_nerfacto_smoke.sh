#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

GPU=${GPU:-0}
IMAGE=${IMAGE:-ghcr.io/nerfstudio-project/nerfstudio:latest}
DATA_DIR=${DATA_DIR:-outputs/experiments/3d_generation/marinecity_real_capture_neural3d}
OUT_DIR=${OUT_DIR:-outputs/experiments/3d_generation/nerfstudio_runs}
LOG_DIR=${LOG_DIR:-outputs/logs/marinecity_nerfstudio_gpu0}
EXPERIMENT=${EXPERIMENT:-marinecity_nerfacto_smoke}
TIMESTAMP=${TIMESTAMP:-$(date +%Y%m%d_%H%M%S)}
MAX_ITERS=${MAX_ITERS:-50}

DATA_ABS=$(realpath "$DATA_DIR")
OUT_ABS=$(realpath -m "$OUT_DIR")
LOG_ABS=$(realpath -m "$LOG_DIR")
mkdir -p "$OUT_ABS" "$LOG_ABS"

TRAIN_LOG="$LOG_ABS/${EXPERIMENT}_${TIMESTAMP}_train.log"
EVAL_LOG="$LOG_ABS/${EXPERIMENT}_${TIMESTAMP}_eval.log"
MANIFEST="$OUT_ABS/${EXPERIMENT}_${TIMESTAMP}_manifest.json"

echo "[nerfstudio] start train $(date -Is) gpu=$GPU data=$DATA_ABS out=$OUT_ABS max_iters=$MAX_ITERS" | tee "$TRAIN_LOG"

docker run --rm \
  --gpus "device=$GPU" \
  -v "$DATA_ABS:/data:ro" \
  -v "$OUT_ABS:/nerfstudio-output:rw" \
  "$IMAGE" \
  ns-train nerfacto \
    --data /data \
    --output-dir /nerfstudio-output \
    --experiment-name "$EXPERIMENT" \
    --timestamp "$TIMESTAMP" \
    --max-num-iterations "$MAX_ITERS" \
    --steps-per-save "$MAX_ITERS" \
    --steps-per-eval-all-images "$MAX_ITERS" \
    --vis tensorboard \
    --viewer.quit-on-train-completion True \
  2>&1 | tee -a "$TRAIN_LOG"

CONFIG_HOST=$(find "$OUT_ABS" -path "*$EXPERIMENT*$TIMESTAMP*config.yml" -print -quit)
if [[ -z "$CONFIG_HOST" || ! -f "$CONFIG_HOST" ]]; then
  echo "[nerfstudio] config.yml not found after training" | tee -a "$TRAIN_LOG"
  exit 2
fi
CONFIG_REL=${CONFIG_HOST#"$OUT_ABS"/}
CONFIG_CONTAINER="/nerfstudio-output/$CONFIG_REL"
EVAL_JSON="$OUT_ABS/${EXPERIMENT}_${TIMESTAMP}_eval.json"
RENDER_DIR="$OUT_ABS/${EXPERIMENT}_${TIMESTAMP}_renders"

echo "[nerfstudio] start eval $(date -Is) config=$CONFIG_HOST" | tee "$EVAL_LOG"
docker run --rm \
  --gpus "device=$GPU" \
  -v "$DATA_ABS:/data:ro" \
  -v "$OUT_ABS:/nerfstudio-output:rw" \
  "$IMAGE" \
  ns-eval \
    --load-config "$CONFIG_CONTAINER" \
    --output-path "/nerfstudio-output/$(basename "$EVAL_JSON")" \
    --render-output-path "/nerfstudio-output/$(basename "$RENDER_DIR")" \
  2>&1 | tee -a "$EVAL_LOG"

cat > "$MANIFEST" <<JSON
{
  "status": "nerfstudio_nerfacto_smoke_complete",
  "updated_at": "$(date -Is)",
  "image": "$IMAGE",
  "gpu": "$GPU",
  "data_dir": "$DATA_ABS",
  "out_dir": "$OUT_ABS",
  "experiment": "$EXPERIMENT",
  "timestamp": "$TIMESTAMP",
  "max_iters": $MAX_ITERS,
  "config": "$CONFIG_HOST",
  "eval_json": "$EVAL_JSON",
  "render_dir": "$RENDER_DIR",
  "train_log": "$TRAIN_LOG",
  "eval_log": "$EVAL_LOG"
}
JSON

echo "[nerfstudio] complete $(date -Is) manifest=$MANIFEST"
