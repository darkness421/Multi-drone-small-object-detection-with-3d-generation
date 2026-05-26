#!/usr/bin/env bash
set -uo pipefail
cd /home/oem/projects/multi-uav-marine-city
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export MPLCONFIGDIR=/home/oem/projects/multi-uav-marine-city/.cache/matplotlib
export YOLO_CONFIG_DIR=/home/oem/projects/multi-uav-marine-city/.cache/ultralytics
export XDG_CACHE_HOME=/home/oem/projects/multi-uav-marine-city/.cache
mkdir -p "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR" "$XDG_CACHE_HOME"
echo "GPU worker 1 started at $(date -Is)"

echo "START model=yolov10s.pt seed=123 gpu=1 batch=8 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov10s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 123 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name yolov10s_visdrone_fresh_fresh_20260519_131008_seed123 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10s_visdrone_fresh_fresh_20260519_131008_seed123.log; then
  echo "TRAIN_OK model=yolov10s.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10s_visdrone_fresh_fresh_20260519_131008_seed123.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131008 -maxdepth 1 -type d \( -name yolov10s_visdrone_fresh_fresh_20260519_131008_seed123 -o -name \*_yolov10s_visdrone_fresh_fresh_20260519_131008_seed123 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name eval_yolov10s_visdrone_fresh_fresh_20260519_131008_seed123)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10s_visdrone_fresh_fresh_20260519_131008_seed123.log || echo "EVAL_FAILED model=yolov10s.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10s_visdrone_fresh_fresh_20260519_131008_seed123.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolov10s.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10s_visdrone_fresh_fresh_20260519_131008_seed123.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolov10s.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10s_visdrone_fresh_fresh_20260519_131008_seed123.log
fi
echo "DONE model=yolov10s.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10s_visdrone_fresh_fresh_20260519_131008_seed123.log

echo "START model=yolov10n.pt seed=42 gpu=1 batch=8 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov10n.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 42 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name yolov10n_visdrone_fresh_fresh_20260519_131008_seed42 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10n_visdrone_fresh_fresh_20260519_131008_seed42.log; then
  echo "TRAIN_OK model=yolov10n.pt seed=42 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10n_visdrone_fresh_fresh_20260519_131008_seed42.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131008 -maxdepth 1 -type d \( -name yolov10n_visdrone_fresh_fresh_20260519_131008_seed42 -o -name \*_yolov10n_visdrone_fresh_fresh_20260519_131008_seed42 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name eval_yolov10n_visdrone_fresh_fresh_20260519_131008_seed42)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10n_visdrone_fresh_fresh_20260519_131008_seed42.log || echo "EVAL_FAILED model=yolov10n.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10n_visdrone_fresh_fresh_20260519_131008_seed42.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolov10n.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10n_visdrone_fresh_fresh_20260519_131008_seed42.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolov10n.pt seed=42 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10n_visdrone_fresh_fresh_20260519_131008_seed42.log
fi
echo "DONE model=yolov10n.pt seed=42 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10n_visdrone_fresh_fresh_20260519_131008_seed42.log

echo "START model=yolov10n.pt seed=2026 gpu=1 batch=8 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov10n.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 2026 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name yolov10n_visdrone_fresh_fresh_20260519_131008_seed2026 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10n_visdrone_fresh_fresh_20260519_131008_seed2026.log; then
  echo "TRAIN_OK model=yolov10n.pt seed=2026 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10n_visdrone_fresh_fresh_20260519_131008_seed2026.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131008 -maxdepth 1 -type d \( -name yolov10n_visdrone_fresh_fresh_20260519_131008_seed2026 -o -name \*_yolov10n_visdrone_fresh_fresh_20260519_131008_seed2026 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name eval_yolov10n_visdrone_fresh_fresh_20260519_131008_seed2026)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10n_visdrone_fresh_fresh_20260519_131008_seed2026.log || echo "EVAL_FAILED model=yolov10n.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10n_visdrone_fresh_fresh_20260519_131008_seed2026.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolov10n.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10n_visdrone_fresh_fresh_20260519_131008_seed2026.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolov10n.pt seed=2026 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10n_visdrone_fresh_fresh_20260519_131008_seed2026.log
fi
echo "DONE model=yolov10n.pt seed=2026 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10n_visdrone_fresh_fresh_20260519_131008_seed2026.log

echo "START model=yolov9s.pt seed=123 gpu=1 batch=8 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov9s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 123 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name yolov9s_visdrone_fresh_fresh_20260519_131008_seed123 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov9s_visdrone_fresh_fresh_20260519_131008_seed123.log; then
  echo "TRAIN_OK model=yolov9s.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov9s_visdrone_fresh_fresh_20260519_131008_seed123.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131008 -maxdepth 1 -type d \( -name yolov9s_visdrone_fresh_fresh_20260519_131008_seed123 -o -name \*_yolov9s_visdrone_fresh_fresh_20260519_131008_seed123 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name eval_yolov9s_visdrone_fresh_fresh_20260519_131008_seed123)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov9s_visdrone_fresh_fresh_20260519_131008_seed123.log || echo "EVAL_FAILED model=yolov9s.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov9s_visdrone_fresh_fresh_20260519_131008_seed123.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolov9s.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov9s_visdrone_fresh_fresh_20260519_131008_seed123.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolov9s.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov9s_visdrone_fresh_fresh_20260519_131008_seed123.log
fi
echo "DONE model=yolov9s.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov9s_visdrone_fresh_fresh_20260519_131008_seed123.log

echo "START model=yolov5su.pt seed=42 gpu=1 batch=8 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov5su.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 42 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name yolov5su_visdrone_fresh_fresh_20260519_131008_seed42 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov5su_visdrone_fresh_fresh_20260519_131008_seed42.log; then
  echo "TRAIN_OK model=yolov5su.pt seed=42 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov5su_visdrone_fresh_fresh_20260519_131008_seed42.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131008 -maxdepth 1 -type d \( -name yolov5su_visdrone_fresh_fresh_20260519_131008_seed42 -o -name \*_yolov5su_visdrone_fresh_fresh_20260519_131008_seed42 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name eval_yolov5su_visdrone_fresh_fresh_20260519_131008_seed42)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov5su_visdrone_fresh_fresh_20260519_131008_seed42.log || echo "EVAL_FAILED model=yolov5su.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov5su_visdrone_fresh_fresh_20260519_131008_seed42.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolov5su.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov5su_visdrone_fresh_fresh_20260519_131008_seed42.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolov5su.pt seed=42 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov5su_visdrone_fresh_fresh_20260519_131008_seed42.log
fi
echo "DONE model=yolov5su.pt seed=42 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov5su_visdrone_fresh_fresh_20260519_131008_seed42.log

echo "START model=yolov5su.pt seed=2026 gpu=1 batch=8 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov5su.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 2026 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name yolov5su_visdrone_fresh_fresh_20260519_131008_seed2026 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov5su_visdrone_fresh_fresh_20260519_131008_seed2026.log; then
  echo "TRAIN_OK model=yolov5su.pt seed=2026 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov5su_visdrone_fresh_fresh_20260519_131008_seed2026.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131008 -maxdepth 1 -type d \( -name yolov5su_visdrone_fresh_fresh_20260519_131008_seed2026 -o -name \*_yolov5su_visdrone_fresh_fresh_20260519_131008_seed2026 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name eval_yolov5su_visdrone_fresh_fresh_20260519_131008_seed2026)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov5su_visdrone_fresh_fresh_20260519_131008_seed2026.log || echo "EVAL_FAILED model=yolov5su.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov5su_visdrone_fresh_fresh_20260519_131008_seed2026.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolov5su.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov5su_visdrone_fresh_fresh_20260519_131008_seed2026.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolov5su.pt seed=2026 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov5su_visdrone_fresh_fresh_20260519_131008_seed2026.log
fi
echo "DONE model=yolov5su.pt seed=2026 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov5su_visdrone_fresh_fresh_20260519_131008_seed2026.log

echo "START model=yolov8n.pt seed=123 gpu=1 batch=8 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov8n.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 123 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name yolov8n_visdrone_fresh_fresh_20260519_131008_seed123 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov8n_visdrone_fresh_fresh_20260519_131008_seed123.log; then
  echo "TRAIN_OK model=yolov8n.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov8n_visdrone_fresh_fresh_20260519_131008_seed123.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131008 -maxdepth 1 -type d \( -name yolov8n_visdrone_fresh_fresh_20260519_131008_seed123 -o -name \*_yolov8n_visdrone_fresh_fresh_20260519_131008_seed123 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name eval_yolov8n_visdrone_fresh_fresh_20260519_131008_seed123)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov8n_visdrone_fresh_fresh_20260519_131008_seed123.log || echo "EVAL_FAILED model=yolov8n.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov8n_visdrone_fresh_fresh_20260519_131008_seed123.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolov8n.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov8n_visdrone_fresh_fresh_20260519_131008_seed123.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolov8n.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov8n_visdrone_fresh_fresh_20260519_131008_seed123.log
fi
echo "DONE model=yolov8n.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov8n_visdrone_fresh_fresh_20260519_131008_seed123.log

echo "START model=yolov8s.pt seed=42 gpu=1 batch=8 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov8s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 42 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name yolov8s_visdrone_fresh_fresh_20260519_131008_seed42 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov8s_visdrone_fresh_fresh_20260519_131008_seed42.log; then
  echo "TRAIN_OK model=yolov8s.pt seed=42 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov8s_visdrone_fresh_fresh_20260519_131008_seed42.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131008 -maxdepth 1 -type d \( -name yolov8s_visdrone_fresh_fresh_20260519_131008_seed42 -o -name \*_yolov8s_visdrone_fresh_fresh_20260519_131008_seed42 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name eval_yolov8s_visdrone_fresh_fresh_20260519_131008_seed42)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov8s_visdrone_fresh_fresh_20260519_131008_seed42.log || echo "EVAL_FAILED model=yolov8s.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov8s_visdrone_fresh_fresh_20260519_131008_seed42.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolov8s.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov8s_visdrone_fresh_fresh_20260519_131008_seed42.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolov8s.pt seed=42 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov8s_visdrone_fresh_fresh_20260519_131008_seed42.log
fi
echo "DONE model=yolov8s.pt seed=42 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov8s_visdrone_fresh_fresh_20260519_131008_seed42.log

echo "START model=yolov8s.pt seed=2026 gpu=1 batch=8 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov8s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 2026 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name yolov8s_visdrone_fresh_fresh_20260519_131008_seed2026 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov8s_visdrone_fresh_fresh_20260519_131008_seed2026.log; then
  echo "TRAIN_OK model=yolov8s.pt seed=2026 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov8s_visdrone_fresh_fresh_20260519_131008_seed2026.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131008 -maxdepth 1 -type d \( -name yolov8s_visdrone_fresh_fresh_20260519_131008_seed2026 -o -name \*_yolov8s_visdrone_fresh_fresh_20260519_131008_seed2026 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name eval_yolov8s_visdrone_fresh_fresh_20260519_131008_seed2026)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov8s_visdrone_fresh_fresh_20260519_131008_seed2026.log || echo "EVAL_FAILED model=yolov8s.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov8s_visdrone_fresh_fresh_20260519_131008_seed2026.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolov8s.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov8s_visdrone_fresh_fresh_20260519_131008_seed2026.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolov8s.pt seed=2026 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov8s_visdrone_fresh_fresh_20260519_131008_seed2026.log
fi
echo "DONE model=yolov8s.pt seed=2026 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov8s_visdrone_fresh_fresh_20260519_131008_seed2026.log

echo "START model=yolo11n.pt seed=123 gpu=1 batch=8 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo11n.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 123 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name yolo11n_visdrone_fresh_fresh_20260519_131008_seed123 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo11n_visdrone_fresh_fresh_20260519_131008_seed123.log; then
  echo "TRAIN_OK model=yolo11n.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo11n_visdrone_fresh_fresh_20260519_131008_seed123.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131008 -maxdepth 1 -type d \( -name yolo11n_visdrone_fresh_fresh_20260519_131008_seed123 -o -name \*_yolo11n_visdrone_fresh_fresh_20260519_131008_seed123 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name eval_yolo11n_visdrone_fresh_fresh_20260519_131008_seed123)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo11n_visdrone_fresh_fresh_20260519_131008_seed123.log || echo "EVAL_FAILED model=yolo11n.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo11n_visdrone_fresh_fresh_20260519_131008_seed123.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolo11n.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo11n_visdrone_fresh_fresh_20260519_131008_seed123.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolo11n.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo11n_visdrone_fresh_fresh_20260519_131008_seed123.log
fi
echo "DONE model=yolo11n.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo11n_visdrone_fresh_fresh_20260519_131008_seed123.log

echo "START model=yolo11s.pt seed=42 gpu=1 batch=8 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo11s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 42 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name yolo11s_visdrone_fresh_fresh_20260519_131008_seed42 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo11s_visdrone_fresh_fresh_20260519_131008_seed42.log; then
  echo "TRAIN_OK model=yolo11s.pt seed=42 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo11s_visdrone_fresh_fresh_20260519_131008_seed42.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131008 -maxdepth 1 -type d \( -name yolo11s_visdrone_fresh_fresh_20260519_131008_seed42 -o -name \*_yolo11s_visdrone_fresh_fresh_20260519_131008_seed42 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name eval_yolo11s_visdrone_fresh_fresh_20260519_131008_seed42)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo11s_visdrone_fresh_fresh_20260519_131008_seed42.log || echo "EVAL_FAILED model=yolo11s.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo11s_visdrone_fresh_fresh_20260519_131008_seed42.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolo11s.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo11s_visdrone_fresh_fresh_20260519_131008_seed42.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolo11s.pt seed=42 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo11s_visdrone_fresh_fresh_20260519_131008_seed42.log
fi
echo "DONE model=yolo11s.pt seed=42 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo11s_visdrone_fresh_fresh_20260519_131008_seed42.log

echo "START model=yolo11s.pt seed=2026 gpu=1 batch=8 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo11s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 2026 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name yolo11s_visdrone_fresh_fresh_20260519_131008_seed2026 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo11s_visdrone_fresh_fresh_20260519_131008_seed2026.log; then
  echo "TRAIN_OK model=yolo11s.pt seed=2026 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo11s_visdrone_fresh_fresh_20260519_131008_seed2026.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131008 -maxdepth 1 -type d \( -name yolo11s_visdrone_fresh_fresh_20260519_131008_seed2026 -o -name \*_yolo11s_visdrone_fresh_fresh_20260519_131008_seed2026 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name eval_yolo11s_visdrone_fresh_fresh_20260519_131008_seed2026)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo11s_visdrone_fresh_fresh_20260519_131008_seed2026.log || echo "EVAL_FAILED model=yolo11s.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo11s_visdrone_fresh_fresh_20260519_131008_seed2026.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolo11s.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo11s_visdrone_fresh_fresh_20260519_131008_seed2026.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolo11s.pt seed=2026 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo11s_visdrone_fresh_fresh_20260519_131008_seed2026.log
fi
echo "DONE model=yolo11s.pt seed=2026 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo11s_visdrone_fresh_fresh_20260519_131008_seed2026.log

echo "START model=yolo12n.pt seed=123 gpu=1 batch=8 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo12n.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 123 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name yolo12n_visdrone_fresh_fresh_20260519_131008_seed123 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12n_visdrone_fresh_fresh_20260519_131008_seed123.log; then
  echo "TRAIN_OK model=yolo12n.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12n_visdrone_fresh_fresh_20260519_131008_seed123.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131008 -maxdepth 1 -type d \( -name yolo12n_visdrone_fresh_fresh_20260519_131008_seed123 -o -name \*_yolo12n_visdrone_fresh_fresh_20260519_131008_seed123 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name eval_yolo12n_visdrone_fresh_fresh_20260519_131008_seed123)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12n_visdrone_fresh_fresh_20260519_131008_seed123.log || echo "EVAL_FAILED model=yolo12n.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12n_visdrone_fresh_fresh_20260519_131008_seed123.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolo12n.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12n_visdrone_fresh_fresh_20260519_131008_seed123.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolo12n.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12n_visdrone_fresh_fresh_20260519_131008_seed123.log
fi
echo "DONE model=yolo12n.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12n_visdrone_fresh_fresh_20260519_131008_seed123.log

echo "START model=yolo12s.pt seed=42 gpu=1 batch=8 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo12s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 42 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name yolo12s_visdrone_fresh_fresh_20260519_131008_seed42 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12s_visdrone_fresh_fresh_20260519_131008_seed42.log; then
  echo "TRAIN_OK model=yolo12s.pt seed=42 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12s_visdrone_fresh_fresh_20260519_131008_seed42.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131008 -maxdepth 1 -type d \( -name yolo12s_visdrone_fresh_fresh_20260519_131008_seed42 -o -name \*_yolo12s_visdrone_fresh_fresh_20260519_131008_seed42 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name eval_yolo12s_visdrone_fresh_fresh_20260519_131008_seed42)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12s_visdrone_fresh_fresh_20260519_131008_seed42.log || echo "EVAL_FAILED model=yolo12s.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12s_visdrone_fresh_fresh_20260519_131008_seed42.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolo12s.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12s_visdrone_fresh_fresh_20260519_131008_seed42.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolo12s.pt seed=42 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12s_visdrone_fresh_fresh_20260519_131008_seed42.log
fi
echo "DONE model=yolo12s.pt seed=42 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12s_visdrone_fresh_fresh_20260519_131008_seed42.log

echo "START model=yolo12s.pt seed=2026 gpu=1 batch=8 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo12s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 2026 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name yolo12s_visdrone_fresh_fresh_20260519_131008_seed2026 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12s_visdrone_fresh_fresh_20260519_131008_seed2026.log; then
  echo "TRAIN_OK model=yolo12s.pt seed=2026 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12s_visdrone_fresh_fresh_20260519_131008_seed2026.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131008 -maxdepth 1 -type d \( -name yolo12s_visdrone_fresh_fresh_20260519_131008_seed2026 -o -name \*_yolo12s_visdrone_fresh_fresh_20260519_131008_seed2026 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name eval_yolo12s_visdrone_fresh_fresh_20260519_131008_seed2026)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12s_visdrone_fresh_fresh_20260519_131008_seed2026.log || echo "EVAL_FAILED model=yolo12s.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12s_visdrone_fresh_fresh_20260519_131008_seed2026.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolo12s.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12s_visdrone_fresh_fresh_20260519_131008_seed2026.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolo12s.pt seed=2026 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12s_visdrone_fresh_fresh_20260519_131008_seed2026.log
fi
echo "DONE model=yolo12s.pt seed=2026 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12s_visdrone_fresh_fresh_20260519_131008_seed2026.log

echo "START model=yolo26n.pt seed=123 gpu=1 batch=8 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo26n.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 123 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name yolo26n_visdrone_fresh_fresh_20260519_131008_seed123 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo26n_visdrone_fresh_fresh_20260519_131008_seed123.log; then
  echo "TRAIN_OK model=yolo26n.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo26n_visdrone_fresh_fresh_20260519_131008_seed123.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131008 -maxdepth 1 -type d \( -name yolo26n_visdrone_fresh_fresh_20260519_131008_seed123 -o -name \*_yolo26n_visdrone_fresh_fresh_20260519_131008_seed123 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name eval_yolo26n_visdrone_fresh_fresh_20260519_131008_seed123)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo26n_visdrone_fresh_fresh_20260519_131008_seed123.log || echo "EVAL_FAILED model=yolo26n.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo26n_visdrone_fresh_fresh_20260519_131008_seed123.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolo26n.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo26n_visdrone_fresh_fresh_20260519_131008_seed123.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolo26n.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo26n_visdrone_fresh_fresh_20260519_131008_seed123.log
fi
echo "DONE model=yolo26n.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo26n_visdrone_fresh_fresh_20260519_131008_seed123.log

echo "START model=yolo26s.pt seed=42 gpu=1 batch=8 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo26s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 42 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name yolo26s_visdrone_fresh_fresh_20260519_131008_seed42 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo26s_visdrone_fresh_fresh_20260519_131008_seed42.log; then
  echo "TRAIN_OK model=yolo26s.pt seed=42 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo26s_visdrone_fresh_fresh_20260519_131008_seed42.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131008 -maxdepth 1 -type d \( -name yolo26s_visdrone_fresh_fresh_20260519_131008_seed42 -o -name \*_yolo26s_visdrone_fresh_fresh_20260519_131008_seed42 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name eval_yolo26s_visdrone_fresh_fresh_20260519_131008_seed42)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo26s_visdrone_fresh_fresh_20260519_131008_seed42.log || echo "EVAL_FAILED model=yolo26s.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo26s_visdrone_fresh_fresh_20260519_131008_seed42.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolo26s.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo26s_visdrone_fresh_fresh_20260519_131008_seed42.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolo26s.pt seed=42 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo26s_visdrone_fresh_fresh_20260519_131008_seed42.log
fi
echo "DONE model=yolo26s.pt seed=42 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo26s_visdrone_fresh_fresh_20260519_131008_seed42.log

echo "START model=yolo26s.pt seed=2026 gpu=1 batch=8 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo26s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 1 --seed 2026 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name yolo26s_visdrone_fresh_fresh_20260519_131008_seed2026 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo26s_visdrone_fresh_fresh_20260519_131008_seed2026.log; then
  echo "TRAIN_OK model=yolo26s.pt seed=2026 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo26s_visdrone_fresh_fresh_20260519_131008_seed2026.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131008 -maxdepth 1 -type d \( -name yolo26s_visdrone_fresh_fresh_20260519_131008_seed2026 -o -name \*_yolo26s_visdrone_fresh_fresh_20260519_131008_seed2026 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name eval_yolo26s_visdrone_fresh_fresh_20260519_131008_seed2026)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo26s_visdrone_fresh_fresh_20260519_131008_seed2026.log || echo "EVAL_FAILED model=yolo26s.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo26s_visdrone_fresh_fresh_20260519_131008_seed2026.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolo26s.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo26s_visdrone_fresh_fresh_20260519_131008_seed2026.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolo26s.pt seed=2026 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo26s_visdrone_fresh_fresh_20260519_131008_seed2026.log
fi
echo "DONE model=yolo26s.pt seed=2026 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo26s_visdrone_fresh_fresh_20260519_131008_seed2026.log

echo "START model=rtdetr-l.pt seed=123 gpu=1 batch=4 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model rtdetr-l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 4 --device 1 --seed 123 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name rtdetr-l_visdrone_fresh_fresh_20260519_131008_seed123 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131008/rtdetr-l_visdrone_fresh_fresh_20260519_131008_seed123.log; then
  echo "TRAIN_OK model=rtdetr-l.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/rtdetr-l_visdrone_fresh_fresh_20260519_131008_seed123.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131008 -maxdepth 1 -type d \( -name rtdetr-l_visdrone_fresh_fresh_20260519_131008_seed123 -o -name \*_rtdetr-l_visdrone_fresh_fresh_20260519_131008_seed123 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name eval_rtdetr-l_visdrone_fresh_fresh_20260519_131008_seed123)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/rtdetr-l_visdrone_fresh_fresh_20260519_131008_seed123.log || echo "EVAL_FAILED model=rtdetr-l.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/rtdetr-l_visdrone_fresh_fresh_20260519_131008_seed123.log
    else
      echo "EVAL_SKIPPED missing best.pt model=rtdetr-l.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/rtdetr-l_visdrone_fresh_fresh_20260519_131008_seed123.log
    fi
  fi
else
  echo "TRAIN_FAILED model=rtdetr-l.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/rtdetr-l_visdrone_fresh_fresh_20260519_131008_seed123.log
fi
echo "DONE model=rtdetr-l.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/rtdetr-l_visdrone_fresh_fresh_20260519_131008_seed123.log

echo "START model=yolov10m.pt seed=42 gpu=1 batch=4 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov10m.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 4 --device 1 --seed 42 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name yolov10m_visdrone_fresh_fresh_20260519_131008_seed42 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10m_visdrone_fresh_fresh_20260519_131008_seed42.log; then
  echo "TRAIN_OK model=yolov10m.pt seed=42 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10m_visdrone_fresh_fresh_20260519_131008_seed42.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131008 -maxdepth 1 -type d \( -name yolov10m_visdrone_fresh_fresh_20260519_131008_seed42 -o -name \*_yolov10m_visdrone_fresh_fresh_20260519_131008_seed42 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name eval_yolov10m_visdrone_fresh_fresh_20260519_131008_seed42)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10m_visdrone_fresh_fresh_20260519_131008_seed42.log || echo "EVAL_FAILED model=yolov10m.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10m_visdrone_fresh_fresh_20260519_131008_seed42.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolov10m.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10m_visdrone_fresh_fresh_20260519_131008_seed42.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolov10m.pt seed=42 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10m_visdrone_fresh_fresh_20260519_131008_seed42.log
fi
echo "DONE model=yolov10m.pt seed=42 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10m_visdrone_fresh_fresh_20260519_131008_seed42.log

echo "START model=yolov10m.pt seed=2026 gpu=1 batch=4 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov10m.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 4 --device 1 --seed 2026 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name yolov10m_visdrone_fresh_fresh_20260519_131008_seed2026 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10m_visdrone_fresh_fresh_20260519_131008_seed2026.log; then
  echo "TRAIN_OK model=yolov10m.pt seed=2026 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10m_visdrone_fresh_fresh_20260519_131008_seed2026.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131008 -maxdepth 1 -type d \( -name yolov10m_visdrone_fresh_fresh_20260519_131008_seed2026 -o -name \*_yolov10m_visdrone_fresh_fresh_20260519_131008_seed2026 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name eval_yolov10m_visdrone_fresh_fresh_20260519_131008_seed2026)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10m_visdrone_fresh_fresh_20260519_131008_seed2026.log || echo "EVAL_FAILED model=yolov10m.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10m_visdrone_fresh_fresh_20260519_131008_seed2026.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolov10m.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10m_visdrone_fresh_fresh_20260519_131008_seed2026.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolov10m.pt seed=2026 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10m_visdrone_fresh_fresh_20260519_131008_seed2026.log
fi
echo "DONE model=yolov10m.pt seed=2026 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolov10m_visdrone_fresh_fresh_20260519_131008_seed2026.log

echo "START model=yolo12m.pt seed=123 gpu=1 batch=4 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo12m.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 4 --device 1 --seed 123 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name yolo12m_visdrone_fresh_fresh_20260519_131008_seed123 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12m_visdrone_fresh_fresh_20260519_131008_seed123.log; then
  echo "TRAIN_OK model=yolo12m.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12m_visdrone_fresh_fresh_20260519_131008_seed123.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131008 -maxdepth 1 -type d \( -name yolo12m_visdrone_fresh_fresh_20260519_131008_seed123 -o -name \*_yolo12m_visdrone_fresh_fresh_20260519_131008_seed123 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131008 --name eval_yolo12m_visdrone_fresh_fresh_20260519_131008_seed123)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12m_visdrone_fresh_fresh_20260519_131008_seed123.log || echo "EVAL_FAILED model=yolo12m.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12m_visdrone_fresh_fresh_20260519_131008_seed123.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolo12m.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12m_visdrone_fresh_fresh_20260519_131008_seed123.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolo12m.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12m_visdrone_fresh_fresh_20260519_131008_seed123.log
fi
echo "DONE model=yolo12m.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131008/yolo12m_visdrone_fresh_fresh_20260519_131008_seed123.log

echo "GPU worker 1 finished at $(date -Is)"
touch outputs/experiments/server_fresh/fresh_20260519_131008/jobs/gpu1.done
