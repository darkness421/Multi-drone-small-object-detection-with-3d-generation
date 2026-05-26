#!/usr/bin/env bash
set -euo pipefail
cd /home/oem/projects/multi-uav-marine-city
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export CONDA_ENV=com3d-ace
export MPLCONFIGDIR=/home/oem/projects/multi-uav-marine-city/.cache/matplotlib
export YOLO_CONFIG_DIR=/home/oem/projects/multi-uav-marine-city/.cache/ultralytics
mkdir -p "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR"
echo "START model=yolov8s.pt seed=3407 physical_gpu=1 at $(date -Is)"
conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov8s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 3407 --project outputs/detectors/server_baselines --name yolov8s_visdrone_seed3407 2>&1 | tee outputs/logs/server_baselines/yolov8s_visdrone_seed3407.log
if [[ 1 == 1 ]]; then
  run_dir=$(find outputs/detectors/server_baselines -maxdepth 1 -type d -name "*_yolov8s_visdrone_seed3407" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_baselines --name eval_yolov8s_visdrone_seed3407)
    if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
    conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_baselines/yolov8s_visdrone_seed3407.log
  fi
fi
echo "DONE model=yolov8s.pt seed=3407 physical_gpu=1 at $(date -Is)"
echo "START model=yolo12s.pt seed=3407 physical_gpu=1 at $(date -Is)"
conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo12s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 3407 --project outputs/detectors/server_baselines --name yolo12s_visdrone_seed3407 2>&1 | tee outputs/logs/server_baselines/yolo12s_visdrone_seed3407.log
if [[ 1 == 1 ]]; then
  run_dir=$(find outputs/detectors/server_baselines -maxdepth 1 -type d -name "*_yolo12s_visdrone_seed3407" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_baselines --name eval_yolo12s_visdrone_seed3407)
    if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
    conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_baselines/yolo12s_visdrone_seed3407.log
  fi
fi
echo "DONE model=yolo12s.pt seed=3407 physical_gpu=1 at $(date -Is)"
echo "START model=yolo11s.pt seed=3407 physical_gpu=1 at $(date -Is)"
conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo11s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 3407 --project outputs/detectors/server_baselines --name yolo11s_visdrone_seed3407 2>&1 | tee outputs/logs/server_baselines/yolo11s_visdrone_seed3407.log
if [[ 1 == 1 ]]; then
  run_dir=$(find outputs/detectors/server_baselines -maxdepth 1 -type d -name "*_yolo11s_visdrone_seed3407" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_baselines --name eval_yolo11s_visdrone_seed3407)
    if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
    conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_baselines/yolo11s_visdrone_seed3407.log
  fi
fi
echo "DONE model=yolo11s.pt seed=3407 physical_gpu=1 at $(date -Is)"
