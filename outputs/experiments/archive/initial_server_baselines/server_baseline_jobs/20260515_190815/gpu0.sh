#!/usr/bin/env bash
set -euo pipefail
cd /home/oem/projects/multi-uav-marine-city
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CONDA_ENV=com3d-ace
export MPLCONFIGDIR=/home/oem/projects/multi-uav-marine-city/.cache/matplotlib
export YOLO_CONFIG_DIR=/home/oem/projects/multi-uav-marine-city/.cache/ultralytics
mkdir -p "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR"
echo "START model=yolov8n.pt seed=42 physical_gpu=0 at $(date -Is)"
conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov8n.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 42 --project outputs/detectors/server_baselines --name yolov8n_visdrone_seed42 2>&1 | tee outputs/logs/server_baselines/yolov8n_visdrone_seed42.log
if [[ 1 == 1 ]]; then
  run_dir=$(find outputs/detectors/server_baselines -maxdepth 1 -type d -name "*_yolov8n_visdrone_seed42" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_baselines --name eval_yolov8n_visdrone_seed42)
    if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
    conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_baselines/yolov8n_visdrone_seed42.log
  fi
fi
echo "DONE model=yolov8n.pt seed=42 physical_gpu=0 at $(date -Is)"
echo "START model=yolov8n.pt seed=2026 physical_gpu=0 at $(date -Is)"
conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov8n.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 2026 --project outputs/detectors/server_baselines --name yolov8n_visdrone_seed2026 2>&1 | tee outputs/logs/server_baselines/yolov8n_visdrone_seed2026.log
if [[ 1 == 1 ]]; then
  run_dir=$(find outputs/detectors/server_baselines -maxdepth 1 -type d -name "*_yolov8n_visdrone_seed2026" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_baselines --name eval_yolov8n_visdrone_seed2026)
    if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
    conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_baselines/yolov8n_visdrone_seed2026.log
  fi
fi
echo "DONE model=yolov8n.pt seed=2026 physical_gpu=0 at $(date -Is)"
echo "START model=yolov8s.pt seed=123 physical_gpu=0 at $(date -Is)"
conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov8s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 123 --project outputs/detectors/server_baselines --name yolov8s_visdrone_seed123 2>&1 | tee outputs/logs/server_baselines/yolov8s_visdrone_seed123.log
if [[ 1 == 1 ]]; then
  run_dir=$(find outputs/detectors/server_baselines -maxdepth 1 -type d -name "*_yolov8s_visdrone_seed123" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_baselines --name eval_yolov8s_visdrone_seed123)
    if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
    conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_baselines/yolov8s_visdrone_seed123.log
  fi
fi
echo "DONE model=yolov8s.pt seed=123 physical_gpu=0 at $(date -Is)"
echo "START model=yolo11n.pt seed=42 physical_gpu=0 at $(date -Is)"
conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo11n.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 42 --project outputs/detectors/server_baselines --name yolo11n_visdrone_seed42 2>&1 | tee outputs/logs/server_baselines/yolo11n_visdrone_seed42.log
if [[ 1 == 1 ]]; then
  run_dir=$(find outputs/detectors/server_baselines -maxdepth 1 -type d -name "*_yolo11n_visdrone_seed42" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_baselines --name eval_yolo11n_visdrone_seed42)
    if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
    conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_baselines/yolo11n_visdrone_seed42.log
  fi
fi
echo "DONE model=yolo11n.pt seed=42 physical_gpu=0 at $(date -Is)"
echo "START model=yolo11n.pt seed=2026 physical_gpu=0 at $(date -Is)"
conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo11n.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 2026 --project outputs/detectors/server_baselines --name yolo11n_visdrone_seed2026 2>&1 | tee outputs/logs/server_baselines/yolo11n_visdrone_seed2026.log
if [[ 1 == 1 ]]; then
  run_dir=$(find outputs/detectors/server_baselines -maxdepth 1 -type d -name "*_yolo11n_visdrone_seed2026" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_baselines --name eval_yolo11n_visdrone_seed2026)
    if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
    conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_baselines/yolo11n_visdrone_seed2026.log
  fi
fi
echo "DONE model=yolo11n.pt seed=2026 physical_gpu=0 at $(date -Is)"
echo "START model=yolo11s.pt seed=123 physical_gpu=0 at $(date -Is)"
conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo11s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 123 --project outputs/detectors/server_baselines --name yolo11s_visdrone_seed123 2>&1 | tee outputs/logs/server_baselines/yolo11s_visdrone_seed123.log
if [[ 1 == 1 ]]; then
  run_dir=$(find outputs/detectors/server_baselines -maxdepth 1 -type d -name "*_yolo11s_visdrone_seed123" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_baselines --name eval_yolo11s_visdrone_seed123)
    if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
    conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_baselines/yolo11s_visdrone_seed123.log
  fi
fi
echo "DONE model=yolo11s.pt seed=123 physical_gpu=0 at $(date -Is)"
echo "START model=yolo12n.pt seed=42 physical_gpu=0 at $(date -Is)"
conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo12n.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 42 --project outputs/detectors/server_baselines --name yolo12n_visdrone_seed42 2>&1 | tee outputs/logs/server_baselines/yolo12n_visdrone_seed42.log
if [[ 1 == 1 ]]; then
  run_dir=$(find outputs/detectors/server_baselines -maxdepth 1 -type d -name "*_yolo12n_visdrone_seed42" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_baselines --name eval_yolo12n_visdrone_seed42)
    if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
    conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_baselines/yolo12n_visdrone_seed42.log
  fi
fi
echo "DONE model=yolo12n.pt seed=42 physical_gpu=0 at $(date -Is)"
echo "START model=yolo12n.pt seed=2026 physical_gpu=0 at $(date -Is)"
conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo12n.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 2026 --project outputs/detectors/server_baselines --name yolo12n_visdrone_seed2026 2>&1 | tee outputs/logs/server_baselines/yolo12n_visdrone_seed2026.log
if [[ 1 == 1 ]]; then
  run_dir=$(find outputs/detectors/server_baselines -maxdepth 1 -type d -name "*_yolo12n_visdrone_seed2026" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_baselines --name eval_yolo12n_visdrone_seed2026)
    if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
    conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_baselines/yolo12n_visdrone_seed2026.log
  fi
fi
echo "DONE model=yolo12n.pt seed=2026 physical_gpu=0 at $(date -Is)"
echo "START model=yolo12s.pt seed=123 physical_gpu=0 at $(date -Is)"
conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo12s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 123 --project outputs/detectors/server_baselines --name yolo12s_visdrone_seed123 2>&1 | tee outputs/logs/server_baselines/yolo12s_visdrone_seed123.log
if [[ 1 == 1 ]]; then
  run_dir=$(find outputs/detectors/server_baselines -maxdepth 1 -type d -name "*_yolo12s_visdrone_seed123" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_baselines --name eval_yolo12s_visdrone_seed123)
    if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
    conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_baselines/yolo12s_visdrone_seed123.log
  fi
fi
echo "DONE model=yolo12s.pt seed=123 physical_gpu=0 at $(date -Is)"
echo "START model=rtdetr-l.pt seed=42 physical_gpu=0 at $(date -Is)"
conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model rtdetr-l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 42 --project outputs/detectors/server_baselines --name rtdetr-l_visdrone_seed42 2>&1 | tee outputs/logs/server_baselines/rtdetr-l_visdrone_seed42.log
if [[ 1 == 1 ]]; then
  run_dir=$(find outputs/detectors/server_baselines -maxdepth 1 -type d -name "*_rtdetr-l_visdrone_seed42" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_baselines --name eval_rtdetr-l_visdrone_seed42)
    if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
    conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_baselines/rtdetr-l_visdrone_seed42.log
  fi
fi
echo "DONE model=rtdetr-l.pt seed=42 physical_gpu=0 at $(date -Is)"
echo "START model=rtdetr-l.pt seed=2026 physical_gpu=0 at $(date -Is)"
conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model rtdetr-l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 2026 --project outputs/detectors/server_baselines --name rtdetr-l_visdrone_seed2026 2>&1 | tee outputs/logs/server_baselines/rtdetr-l_visdrone_seed2026.log
if [[ 1 == 1 ]]; then
  run_dir=$(find outputs/detectors/server_baselines -maxdepth 1 -type d -name "*_rtdetr-l_visdrone_seed2026" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_baselines --name eval_rtdetr-l_visdrone_seed2026)
    if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
    conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_baselines/rtdetr-l_visdrone_seed2026.log
  fi
fi
echo "DONE model=rtdetr-l.pt seed=2026 physical_gpu=0 at $(date -Is)"
