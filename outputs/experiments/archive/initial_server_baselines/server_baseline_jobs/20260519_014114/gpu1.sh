#!/usr/bin/env bash
set -euo pipefail
cd /home/oem/projects/multi-uav-marine-city
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export CONDA_ENV=com3d-ace
export MPLCONFIGDIR=/home/oem/projects/multi-uav-marine-city/.cache/matplotlib
export YOLO_CONFIG_DIR=/home/oem/projects/multi-uav-marine-city/.cache/ultralytics
mkdir -p "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR"
echo "START model=yolov5su.pt seed=123 physical_gpu=1 at $(date -Is)"
conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov5su.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 123 --project outputs/detectors/server_baselines --name yolov5su_visdrone_seed123 2>&1 | tee outputs/logs/server_baselines/yolov5su_visdrone_seed123.log
if [[ 0 == 1 ]]; then
  run_dir=$(find outputs/detectors/server_baselines -maxdepth 1 -type d -name "*_yolov5su_visdrone_seed123" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_baselines --name eval_yolov5su_visdrone_seed123)
    if [[ 0 == 1 ]]; then eval_args+=(--roc-auc); fi
    conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_baselines/yolov5su_visdrone_seed123.log
  fi
fi
echo "DONE model=yolov5su.pt seed=123 physical_gpu=1 at $(date -Is)"
echo "START model=yolov9s.pt seed=42 physical_gpu=1 at $(date -Is)"
conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov9s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 42 --project outputs/detectors/server_baselines --name yolov9s_visdrone_seed42 2>&1 | tee outputs/logs/server_baselines/yolov9s_visdrone_seed42.log
if [[ 0 == 1 ]]; then
  run_dir=$(find outputs/detectors/server_baselines -maxdepth 1 -type d -name "*_yolov9s_visdrone_seed42" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_baselines --name eval_yolov9s_visdrone_seed42)
    if [[ 0 == 1 ]]; then eval_args+=(--roc-auc); fi
    conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_baselines/yolov9s_visdrone_seed42.log
  fi
fi
echo "DONE model=yolov9s.pt seed=42 physical_gpu=1 at $(date -Is)"
echo "START model=yolov9s.pt seed=2026 physical_gpu=1 at $(date -Is)"
conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov9s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 2026 --project outputs/detectors/server_baselines --name yolov9s_visdrone_seed2026 2>&1 | tee outputs/logs/server_baselines/yolov9s_visdrone_seed2026.log
if [[ 0 == 1 ]]; then
  run_dir=$(find outputs/detectors/server_baselines -maxdepth 1 -type d -name "*_yolov9s_visdrone_seed2026" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_baselines --name eval_yolov9s_visdrone_seed2026)
    if [[ 0 == 1 ]]; then eval_args+=(--roc-auc); fi
    conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_baselines/yolov9s_visdrone_seed2026.log
  fi
fi
echo "DONE model=yolov9s.pt seed=2026 physical_gpu=1 at $(date -Is)"
echo "START model=yolov10s.pt seed=123 physical_gpu=1 at $(date -Is)"
conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov10s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 123 --project outputs/detectors/server_baselines --name yolov10s_visdrone_seed123 2>&1 | tee outputs/logs/server_baselines/yolov10s_visdrone_seed123.log
if [[ 0 == 1 ]]; then
  run_dir=$(find outputs/detectors/server_baselines -maxdepth 1 -type d -name "*_yolov10s_visdrone_seed123" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_baselines --name eval_yolov10s_visdrone_seed123)
    if [[ 0 == 1 ]]; then eval_args+=(--roc-auc); fi
    conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_baselines/yolov10s_visdrone_seed123.log
  fi
fi
echo "DONE model=yolov10s.pt seed=123 physical_gpu=1 at $(date -Is)"
echo "START model=yolo26n.pt seed=42 physical_gpu=1 at $(date -Is)"
conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo26n.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 42 --project outputs/detectors/server_baselines --name yolo26n_visdrone_seed42 2>&1 | tee outputs/logs/server_baselines/yolo26n_visdrone_seed42.log
if [[ 0 == 1 ]]; then
  run_dir=$(find outputs/detectors/server_baselines -maxdepth 1 -type d -name "*_yolo26n_visdrone_seed42" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_baselines --name eval_yolo26n_visdrone_seed42)
    if [[ 0 == 1 ]]; then eval_args+=(--roc-auc); fi
    conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_baselines/yolo26n_visdrone_seed42.log
  fi
fi
echo "DONE model=yolo26n.pt seed=42 physical_gpu=1 at $(date -Is)"
echo "START model=yolo26n.pt seed=2026 physical_gpu=1 at $(date -Is)"
conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo26n.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 2026 --project outputs/detectors/server_baselines --name yolo26n_visdrone_seed2026 2>&1 | tee outputs/logs/server_baselines/yolo26n_visdrone_seed2026.log
if [[ 0 == 1 ]]; then
  run_dir=$(find outputs/detectors/server_baselines -maxdepth 1 -type d -name "*_yolo26n_visdrone_seed2026" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_baselines --name eval_yolo26n_visdrone_seed2026)
    if [[ 0 == 1 ]]; then eval_args+=(--roc-auc); fi
    conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_baselines/yolo26n_visdrone_seed2026.log
  fi
fi
echo "DONE model=yolo26n.pt seed=2026 physical_gpu=1 at $(date -Is)"
echo "START model=yolo26s.pt seed=123 physical_gpu=1 at $(date -Is)"
conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo26s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 123 --project outputs/detectors/server_baselines --name yolo26s_visdrone_seed123 2>&1 | tee outputs/logs/server_baselines/yolo26s_visdrone_seed123.log
if [[ 0 == 1 ]]; then
  run_dir=$(find outputs/detectors/server_baselines -maxdepth 1 -type d -name "*_yolo26s_visdrone_seed123" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_baselines --name eval_yolo26s_visdrone_seed123)
    if [[ 0 == 1 ]]; then eval_args+=(--roc-auc); fi
    conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_baselines/yolo26s_visdrone_seed123.log
  fi
fi
echo "DONE model=yolo26s.pt seed=123 physical_gpu=1 at $(date -Is)"
