#!/usr/bin/env bash
set -euo pipefail
cd /home/oem/projects/multi-uav-marine-city
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export CONDA_ENV=com3d-ace
export MPLCONFIGDIR=/home/oem/projects/multi-uav-marine-city/.cache/matplotlib
export YOLO_CONFIG_DIR=/home/oem/projects/multi-uav-marine-city/.cache/ultralytics
mkdir -p "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR"
echo "START model=rtdetr-l.pt seed=123 physical_gpu=1 at $(date -Is)"
conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model rtdetr-l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 2 --device 1 --seed 123 --project outputs/detectors/server_baselines --name rtdetr-l_visdrone_seed123 2>&1 | tee outputs/logs/server_baselines/rtdetr-l_visdrone_seed123.log
if [[ 1 == 1 ]]; then
  run_dir=$(find outputs/detectors/server_baselines -maxdepth 1 -type d -name "*_rtdetr-l_visdrone_seed123" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_baselines --name eval_rtdetr-l_visdrone_seed123)
    if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
    conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_baselines/rtdetr-l_visdrone_seed123.log
  fi
fi
echo "DONE model=rtdetr-l.pt seed=123 physical_gpu=1 at $(date -Is)"
