#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

GPU=${GPU:-1}
ACTIVE_GPU=${ACTIVE_GPU:-0}
IMAGE=${IMAGE:-nvcr.io/nvidia/isaac-sim:5.1.0}
CONTAINER_NAME=${CONTAINER_NAME:-isaac-gpu1-smoke-$(date +%Y%m%d-%H%M%S)}
CONFIG=${CONFIG:-configs/sim/marinecity_isaac_container_smoke.yaml}
CONTAINER_OUT=${CONTAINER_OUT:-/tmp/com3d_isaac_smoke_exports}
HOST_OUT=${HOST_OUT:-outputs/isaac_exports/marinecity_gpu1_container_smoke}
LOG_DIR=${LOG_DIR:-outputs/logs/gpu1_isaac51_container_smoke}
TIMEOUT_SECONDS=${TIMEOUT_SECONDS:-300}

mkdir -p "$HOST_OUT" "$LOG_DIR"

log_file="$LOG_DIR/${CONTAINER_NAME}.log"
plan_path="$CONTAINER_OUT/capture_plan.json"
template_path="$CONTAINER_OUT/isaac_replicator_capture_template.py"

echo "[Isaac 5.1 GPU${GPU} smoke] started at $(date -Is)" | tee -a "$log_file"
echo "Image: $IMAGE" | tee -a "$log_file"
echo "Host GPU: $GPU" | tee -a "$log_file"
echo "Container active GPU: $ACTIVE_GPU" | tee -a "$log_file"
echo "Config: $CONFIG" | tee -a "$log_file"
echo "Host output: $HOST_OUT" | tee -a "$log_file"

nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits 2>&1 | tee -a "$log_file"

docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true

set +e
timeout "${TIMEOUT_SECONDS}s" docker run \
  --name "$CONTAINER_NAME" \
  --gpus "\"device=${GPU}\"" \
  --entrypoint /isaac-sim/python.sh \
  -e ACCEPT_EULA=Y \
  -e PRIVACY_CONSENT=Y \
  -e PRIVACY_USERID=oem@local \
  -e PYTHONPATH=/workspace \
  -v "$PWD:/workspace:ro" \
  -w /workspace \
  "$IMAGE" \
  simulation/isaac/export_rgb_depth_pose.py \
    --config "$CONFIG" \
    --plan-out "$plan_path" \
    --template-out "$template_path" \
    --active-gpu "$ACTIVE_GPU" \
    --isaac-smoke 2>&1 | tee -a "$log_file"
rc=${PIPESTATUS[0]}
set -e

if [[ "$rc" -ne 0 ]]; then
  echo "[Isaac 5.1 GPU${GPU} smoke] failed rc=$rc at $(date -Is)" | tee -a "$log_file"
  echo "Leaving container for inspection: $CONTAINER_NAME" | tee -a "$log_file"
  exit "$rc"
fi

docker cp "$CONTAINER_NAME:$CONTAINER_OUT/." "$HOST_OUT/" 2>&1 | tee -a "$log_file"
docker rm "$CONTAINER_NAME" >/dev/null

echo "[Isaac 5.1 GPU${GPU} smoke] complete at $(date -Is)" | tee -a "$log_file"
echo "Capture plan: $HOST_OUT/capture_plan.json" | tee -a "$log_file"
echo "Replicator template: $HOST_OUT/isaac_replicator_capture_template.py" | tee -a "$log_file"
