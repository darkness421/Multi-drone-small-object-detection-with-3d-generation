#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <weight1.pt> [weight2.pt ...] -- <image1> [image2 ...]"
  exit 2
fi

weights=()
images=()
mode=weights
for arg in "$@"; do
  if [[ "$arg" == "--" ]]; then
    mode=images
    continue
  fi
  if [[ "$mode" == "weights" ]]; then
    weights+=("$arg")
  else
    images+=("$arg")
  fi
done

if [[ ${#weights[@]} -eq 0 || ${#images[@]} -eq 0 ]]; then
  echo "Provide at least one weight and one image, separated by --."
  exit 2
fi

python -m evaluation.gradcam_yolo \
  --weights "${weights[@]}" \
  --images "${images[@]}" \
  --out-dir outputs/qualitative/gradcam
