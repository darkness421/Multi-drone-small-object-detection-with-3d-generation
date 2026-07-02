#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

usage() {
  cat <<'EOF'
Usage:
  BASELINE_WEIGHT=... \
  CORE1_WEIGHT=... \
  CORE2_WEIGHT=... \
  CORE3_WEIGHT=... \
  CORE12_WEIGHT=... \
  FULL_WEIGHT=... \
  IMAGES="img1.jpg img2.jpg" \
  bash scripts/ubuntu/run_core_ablation_gradcam_plan.sh

Optional:
  TARGET_LAYER=auto-neck-last
  OUT_DIR=outputs/qualitative/gradcam/core_ablation

This creates a Grad-CAM/attention visualization plan for the final detector
core-module ablation. The current Grad-CAM entrypoint records the plan and
dependency status; full CAM rendering is enabled after the final YOLO target
layer is fixed.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

required_vars=(
  BASELINE_WEIGHT
  CORE1_WEIGHT
  CORE2_WEIGHT
  CORE3_WEIGHT
  CORE12_WEIGHT
  FULL_WEIGHT
  IMAGES
)

for var_name in "${required_vars[@]}"; do
  if [[ -z "${!var_name:-}" ]]; then
    echo "Missing required environment variable: $var_name" >&2
    usage >&2
    exit 2
  fi
done

weights=(
  "$BASELINE_WEIGHT"
  "$CORE1_WEIGHT"
  "$CORE2_WEIGHT"
  "$CORE3_WEIGHT"
  "$CORE12_WEIGHT"
  "$FULL_WEIGHT"
)

read -r -a images <<< "$IMAGES"
if [[ ${#images[@]} -eq 0 ]]; then
  echo "IMAGES must contain at least one image path." >&2
  exit 2
fi

python -m evaluation.gradcam_yolo \
  --weights "${weights[@]}" \
  --images "${images[@]}" \
  --target-layer "${TARGET_LAYER:-auto-neck-last}" \
  --out-dir "${OUT_DIR:-outputs/qualitative/gradcam/core_ablation}"
