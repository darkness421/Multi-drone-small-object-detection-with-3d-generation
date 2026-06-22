#!/usr/bin/env bash
set -uo pipefail
cd /home/oem/projects/multi-uav-marine-city
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export RESOURCE_GUARD=1
export MIN_FREE_GB=100
export MAX_DISK_USE_PERCENT=92
export MIN_RAM_GB=16
export MIN_GPU_FREE_GB=8
export GUARD_WAIT_SECONDS=120
export MPLCONFIGDIR=/home/oem/projects/multi-uav-marine-city/.cache/matplotlib
export YOLO_CONFIG_DIR=/home/oem/projects/multi-uav-marine-city/.cache/ultralytics
export XDG_CACHE_HOME=/home/oem/projects/multi-uav-marine-city/.cache
mkdir -p "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR" "$XDG_CACHE_HOME"
echo "GPU worker 0 started at $(date -Is)"

echo "START model=yolov8l.pt seed=42 gpu=0 batch=2 at $(date -Is)"
if [[ "${RESOURCE_GUARD:-1}" == "1" ]]; then bash scripts/ubuntu/check_resource_margin.sh --path /home/oem/projects/multi-uav-marine-city --gpu 0 --min-free-gb "$MIN_FREE_GB" --max-disk-use-percent "$MAX_DISK_USE_PERCENT" --min-ram-gb "$MIN_RAM_GB" --min-gpu-free-gb "$MIN_GPU_FREE_GB" --wait-seconds "$GUARD_WAIT_SECONDS" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed42.log; fi
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov8l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 2 --workers 4 --device 0 --seed 42 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name yolov8l_visdrone_large_fresh_large_20260524_140922_seed42 2>&1 | tee outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed42.log; then
  echo "TRAIN_OK model=yolov8l.pt seed=42 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed42.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/large_20260524_140922 -maxdepth 1 -type d \( -name yolov8l_visdrone_large_fresh_large_20260524_140922_seed42 -o -name \*_yolov8l_visdrone_large_fresh_large_20260524_140922_seed42 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --workers 4 --device 0 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name eval_yolov8l_visdrone_large_fresh_large_20260524_140922_seed42)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed42.log || echo "EVAL_FAILED model=yolov8l.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed42.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolov8l.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed42.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolov8l.pt seed=42 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed42.log
fi
echo "DONE model=yolov8l.pt seed=42 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed42.log

echo "START model=yolov8l.pt seed=123 gpu=0 batch=2 at $(date -Is)"
if [[ "${RESOURCE_GUARD:-1}" == "1" ]]; then bash scripts/ubuntu/check_resource_margin.sh --path /home/oem/projects/multi-uav-marine-city --gpu 0 --min-free-gb "$MIN_FREE_GB" --max-disk-use-percent "$MAX_DISK_USE_PERCENT" --min-ram-gb "$MIN_RAM_GB" --min-gpu-free-gb "$MIN_GPU_FREE_GB" --wait-seconds "$GUARD_WAIT_SECONDS" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed123.log; fi
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov8l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 2 --workers 4 --device 0 --seed 123 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name yolov8l_visdrone_large_fresh_large_20260524_140922_seed123 2>&1 | tee outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed123.log; then
  echo "TRAIN_OK model=yolov8l.pt seed=123 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed123.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/large_20260524_140922 -maxdepth 1 -type d \( -name yolov8l_visdrone_large_fresh_large_20260524_140922_seed123 -o -name \*_yolov8l_visdrone_large_fresh_large_20260524_140922_seed123 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --workers 4 --device 0 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name eval_yolov8l_visdrone_large_fresh_large_20260524_140922_seed123)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed123.log || echo "EVAL_FAILED model=yolov8l.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed123.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolov8l.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed123.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolov8l.pt seed=123 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed123.log
fi
echo "DONE model=yolov8l.pt seed=123 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed123.log

echo "START model=yolov8l.pt seed=2026 gpu=0 batch=2 at $(date -Is)"
if [[ "${RESOURCE_GUARD:-1}" == "1" ]]; then bash scripts/ubuntu/check_resource_margin.sh --path /home/oem/projects/multi-uav-marine-city --gpu 0 --min-free-gb "$MIN_FREE_GB" --max-disk-use-percent "$MAX_DISK_USE_PERCENT" --min-ram-gb "$MIN_RAM_GB" --min-gpu-free-gb "$MIN_GPU_FREE_GB" --wait-seconds "$GUARD_WAIT_SECONDS" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed2026.log; fi
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov8l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 2 --workers 4 --device 0 --seed 2026 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name yolov8l_visdrone_large_fresh_large_20260524_140922_seed2026 2>&1 | tee outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed2026.log; then
  echo "TRAIN_OK model=yolov8l.pt seed=2026 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed2026.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/large_20260524_140922 -maxdepth 1 -type d \( -name yolov8l_visdrone_large_fresh_large_20260524_140922_seed2026 -o -name \*_yolov8l_visdrone_large_fresh_large_20260524_140922_seed2026 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --workers 4 --device 0 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name eval_yolov8l_visdrone_large_fresh_large_20260524_140922_seed2026)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed2026.log || echo "EVAL_FAILED model=yolov8l.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed2026.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolov8l.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed2026.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolov8l.pt seed=2026 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed2026.log
fi
echo "DONE model=yolov8l.pt seed=2026 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov8l_visdrone_large_fresh_large_20260524_140922_seed2026.log

echo "START model=yolov10l.pt seed=42 gpu=0 batch=2 at $(date -Is)"
if [[ "${RESOURCE_GUARD:-1}" == "1" ]]; then bash scripts/ubuntu/check_resource_margin.sh --path /home/oem/projects/multi-uav-marine-city --gpu 0 --min-free-gb "$MIN_FREE_GB" --max-disk-use-percent "$MAX_DISK_USE_PERCENT" --min-ram-gb "$MIN_RAM_GB" --min-gpu-free-gb "$MIN_GPU_FREE_GB" --wait-seconds "$GUARD_WAIT_SECONDS" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed42.log; fi
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov10l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 2 --workers 4 --device 0 --seed 42 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name yolov10l_visdrone_large_fresh_large_20260524_140922_seed42 2>&1 | tee outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed42.log; then
  echo "TRAIN_OK model=yolov10l.pt seed=42 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed42.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/large_20260524_140922 -maxdepth 1 -type d \( -name yolov10l_visdrone_large_fresh_large_20260524_140922_seed42 -o -name \*_yolov10l_visdrone_large_fresh_large_20260524_140922_seed42 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --workers 4 --device 0 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name eval_yolov10l_visdrone_large_fresh_large_20260524_140922_seed42)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed42.log || echo "EVAL_FAILED model=yolov10l.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed42.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolov10l.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed42.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolov10l.pt seed=42 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed42.log
fi
echo "DONE model=yolov10l.pt seed=42 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed42.log

echo "START model=yolov10l.pt seed=123 gpu=0 batch=2 at $(date -Is)"
if [[ "${RESOURCE_GUARD:-1}" == "1" ]]; then bash scripts/ubuntu/check_resource_margin.sh --path /home/oem/projects/multi-uav-marine-city --gpu 0 --min-free-gb "$MIN_FREE_GB" --max-disk-use-percent "$MAX_DISK_USE_PERCENT" --min-ram-gb "$MIN_RAM_GB" --min-gpu-free-gb "$MIN_GPU_FREE_GB" --wait-seconds "$GUARD_WAIT_SECONDS" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed123.log; fi
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov10l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 2 --workers 4 --device 0 --seed 123 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name yolov10l_visdrone_large_fresh_large_20260524_140922_seed123 2>&1 | tee outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed123.log; then
  echo "TRAIN_OK model=yolov10l.pt seed=123 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed123.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/large_20260524_140922 -maxdepth 1 -type d \( -name yolov10l_visdrone_large_fresh_large_20260524_140922_seed123 -o -name \*_yolov10l_visdrone_large_fresh_large_20260524_140922_seed123 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --workers 4 --device 0 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name eval_yolov10l_visdrone_large_fresh_large_20260524_140922_seed123)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed123.log || echo "EVAL_FAILED model=yolov10l.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed123.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolov10l.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed123.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolov10l.pt seed=123 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed123.log
fi
echo "DONE model=yolov10l.pt seed=123 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed123.log

echo "START model=yolov10l.pt seed=2026 gpu=0 batch=2 at $(date -Is)"
if [[ "${RESOURCE_GUARD:-1}" == "1" ]]; then bash scripts/ubuntu/check_resource_margin.sh --path /home/oem/projects/multi-uav-marine-city --gpu 0 --min-free-gb "$MIN_FREE_GB" --max-disk-use-percent "$MAX_DISK_USE_PERCENT" --min-ram-gb "$MIN_RAM_GB" --min-gpu-free-gb "$MIN_GPU_FREE_GB" --wait-seconds "$GUARD_WAIT_SECONDS" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed2026.log; fi
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov10l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 2 --workers 4 --device 0 --seed 2026 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name yolov10l_visdrone_large_fresh_large_20260524_140922_seed2026 2>&1 | tee outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed2026.log; then
  echo "TRAIN_OK model=yolov10l.pt seed=2026 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed2026.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/large_20260524_140922 -maxdepth 1 -type d \( -name yolov10l_visdrone_large_fresh_large_20260524_140922_seed2026 -o -name \*_yolov10l_visdrone_large_fresh_large_20260524_140922_seed2026 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --workers 4 --device 0 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name eval_yolov10l_visdrone_large_fresh_large_20260524_140922_seed2026)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed2026.log || echo "EVAL_FAILED model=yolov10l.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed2026.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolov10l.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed2026.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolov10l.pt seed=2026 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed2026.log
fi
echo "DONE model=yolov10l.pt seed=2026 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolov10l_visdrone_large_fresh_large_20260524_140922_seed2026.log

echo "START model=yolo11l.pt seed=42 gpu=0 batch=2 at $(date -Is)"
if [[ "${RESOURCE_GUARD:-1}" == "1" ]]; then bash scripts/ubuntu/check_resource_margin.sh --path /home/oem/projects/multi-uav-marine-city --gpu 0 --min-free-gb "$MIN_FREE_GB" --max-disk-use-percent "$MAX_DISK_USE_PERCENT" --min-ram-gb "$MIN_RAM_GB" --min-gpu-free-gb "$MIN_GPU_FREE_GB" --wait-seconds "$GUARD_WAIT_SECONDS" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed42.log; fi
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo11l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 2 --workers 4 --device 0 --seed 42 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name yolo11l_visdrone_large_fresh_large_20260524_140922_seed42 2>&1 | tee outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed42.log; then
  echo "TRAIN_OK model=yolo11l.pt seed=42 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed42.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/large_20260524_140922 -maxdepth 1 -type d \( -name yolo11l_visdrone_large_fresh_large_20260524_140922_seed42 -o -name \*_yolo11l_visdrone_large_fresh_large_20260524_140922_seed42 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --workers 4 --device 0 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name eval_yolo11l_visdrone_large_fresh_large_20260524_140922_seed42)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed42.log || echo "EVAL_FAILED model=yolo11l.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed42.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolo11l.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed42.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolo11l.pt seed=42 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed42.log
fi
echo "DONE model=yolo11l.pt seed=42 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed42.log

echo "START model=yolo11l.pt seed=123 gpu=0 batch=2 at $(date -Is)"
if [[ "${RESOURCE_GUARD:-1}" == "1" ]]; then bash scripts/ubuntu/check_resource_margin.sh --path /home/oem/projects/multi-uav-marine-city --gpu 0 --min-free-gb "$MIN_FREE_GB" --max-disk-use-percent "$MAX_DISK_USE_PERCENT" --min-ram-gb "$MIN_RAM_GB" --min-gpu-free-gb "$MIN_GPU_FREE_GB" --wait-seconds "$GUARD_WAIT_SECONDS" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed123.log; fi
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo11l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 2 --workers 4 --device 0 --seed 123 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name yolo11l_visdrone_large_fresh_large_20260524_140922_seed123 2>&1 | tee outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed123.log; then
  echo "TRAIN_OK model=yolo11l.pt seed=123 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed123.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/large_20260524_140922 -maxdepth 1 -type d \( -name yolo11l_visdrone_large_fresh_large_20260524_140922_seed123 -o -name \*_yolo11l_visdrone_large_fresh_large_20260524_140922_seed123 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --workers 4 --device 0 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name eval_yolo11l_visdrone_large_fresh_large_20260524_140922_seed123)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed123.log || echo "EVAL_FAILED model=yolo11l.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed123.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolo11l.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed123.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolo11l.pt seed=123 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed123.log
fi
echo "DONE model=yolo11l.pt seed=123 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed123.log

echo "START model=yolo11l.pt seed=2026 gpu=0 batch=2 at $(date -Is)"
if [[ "${RESOURCE_GUARD:-1}" == "1" ]]; then bash scripts/ubuntu/check_resource_margin.sh --path /home/oem/projects/multi-uav-marine-city --gpu 0 --min-free-gb "$MIN_FREE_GB" --max-disk-use-percent "$MAX_DISK_USE_PERCENT" --min-ram-gb "$MIN_RAM_GB" --min-gpu-free-gb "$MIN_GPU_FREE_GB" --wait-seconds "$GUARD_WAIT_SECONDS" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed2026.log; fi
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo11l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 2 --workers 4 --device 0 --seed 2026 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name yolo11l_visdrone_large_fresh_large_20260524_140922_seed2026 2>&1 | tee outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed2026.log; then
  echo "TRAIN_OK model=yolo11l.pt seed=2026 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed2026.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/large_20260524_140922 -maxdepth 1 -type d \( -name yolo11l_visdrone_large_fresh_large_20260524_140922_seed2026 -o -name \*_yolo11l_visdrone_large_fresh_large_20260524_140922_seed2026 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --workers 4 --device 0 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name eval_yolo11l_visdrone_large_fresh_large_20260524_140922_seed2026)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed2026.log || echo "EVAL_FAILED model=yolo11l.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed2026.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolo11l.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed2026.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolo11l.pt seed=2026 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed2026.log
fi
echo "DONE model=yolo11l.pt seed=2026 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo11l_visdrone_large_fresh_large_20260524_140922_seed2026.log

echo "START model=yolo12l.pt seed=42 gpu=0 batch=2 at $(date -Is)"
if [[ "${RESOURCE_GUARD:-1}" == "1" ]]; then bash scripts/ubuntu/check_resource_margin.sh --path /home/oem/projects/multi-uav-marine-city --gpu 0 --min-free-gb "$MIN_FREE_GB" --max-disk-use-percent "$MAX_DISK_USE_PERCENT" --min-ram-gb "$MIN_RAM_GB" --min-gpu-free-gb "$MIN_GPU_FREE_GB" --wait-seconds "$GUARD_WAIT_SECONDS" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed42.log; fi
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo12l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 2 --workers 4 --device 0 --seed 42 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name yolo12l_visdrone_large_fresh_large_20260524_140922_seed42 2>&1 | tee outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed42.log; then
  echo "TRAIN_OK model=yolo12l.pt seed=42 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed42.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/large_20260524_140922 -maxdepth 1 -type d \( -name yolo12l_visdrone_large_fresh_large_20260524_140922_seed42 -o -name \*_yolo12l_visdrone_large_fresh_large_20260524_140922_seed42 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --workers 4 --device 0 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name eval_yolo12l_visdrone_large_fresh_large_20260524_140922_seed42)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed42.log || echo "EVAL_FAILED model=yolo12l.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed42.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolo12l.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed42.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolo12l.pt seed=42 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed42.log
fi
echo "DONE model=yolo12l.pt seed=42 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed42.log

echo "START model=yolo12l.pt seed=123 gpu=0 batch=2 at $(date -Is)"
if [[ "${RESOURCE_GUARD:-1}" == "1" ]]; then bash scripts/ubuntu/check_resource_margin.sh --path /home/oem/projects/multi-uav-marine-city --gpu 0 --min-free-gb "$MIN_FREE_GB" --max-disk-use-percent "$MAX_DISK_USE_PERCENT" --min-ram-gb "$MIN_RAM_GB" --min-gpu-free-gb "$MIN_GPU_FREE_GB" --wait-seconds "$GUARD_WAIT_SECONDS" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed123.log; fi
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo12l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 2 --workers 4 --device 0 --seed 123 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name yolo12l_visdrone_large_fresh_large_20260524_140922_seed123 2>&1 | tee outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed123.log; then
  echo "TRAIN_OK model=yolo12l.pt seed=123 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed123.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/large_20260524_140922 -maxdepth 1 -type d \( -name yolo12l_visdrone_large_fresh_large_20260524_140922_seed123 -o -name \*_yolo12l_visdrone_large_fresh_large_20260524_140922_seed123 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --workers 4 --device 0 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name eval_yolo12l_visdrone_large_fresh_large_20260524_140922_seed123)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed123.log || echo "EVAL_FAILED model=yolo12l.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed123.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolo12l.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed123.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolo12l.pt seed=123 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed123.log
fi
echo "DONE model=yolo12l.pt seed=123 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed123.log

echo "START model=yolo12l.pt seed=2026 gpu=0 batch=2 at $(date -Is)"
if [[ "${RESOURCE_GUARD:-1}" == "1" ]]; then bash scripts/ubuntu/check_resource_margin.sh --path /home/oem/projects/multi-uav-marine-city --gpu 0 --min-free-gb "$MIN_FREE_GB" --max-disk-use-percent "$MAX_DISK_USE_PERCENT" --min-ram-gb "$MIN_RAM_GB" --min-gpu-free-gb "$MIN_GPU_FREE_GB" --wait-seconds "$GUARD_WAIT_SECONDS" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed2026.log; fi
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo12l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 2 --workers 4 --device 0 --seed 2026 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name yolo12l_visdrone_large_fresh_large_20260524_140922_seed2026 2>&1 | tee outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed2026.log; then
  echo "TRAIN_OK model=yolo12l.pt seed=2026 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed2026.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/large_20260524_140922 -maxdepth 1 -type d \( -name yolo12l_visdrone_large_fresh_large_20260524_140922_seed2026 -o -name \*_yolo12l_visdrone_large_fresh_large_20260524_140922_seed2026 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --workers 4 --device 0 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name eval_yolo12l_visdrone_large_fresh_large_20260524_140922_seed2026)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed2026.log || echo "EVAL_FAILED model=yolo12l.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed2026.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolo12l.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed2026.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolo12l.pt seed=2026 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed2026.log
fi
echo "DONE model=yolo12l.pt seed=2026 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo12l_visdrone_large_fresh_large_20260524_140922_seed2026.log

echo "START model=yolo26l.pt seed=42 gpu=0 batch=2 at $(date -Is)"
if [[ "${RESOURCE_GUARD:-1}" == "1" ]]; then bash scripts/ubuntu/check_resource_margin.sh --path /home/oem/projects/multi-uav-marine-city --gpu 0 --min-free-gb "$MIN_FREE_GB" --max-disk-use-percent "$MAX_DISK_USE_PERCENT" --min-ram-gb "$MIN_RAM_GB" --min-gpu-free-gb "$MIN_GPU_FREE_GB" --wait-seconds "$GUARD_WAIT_SECONDS" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed42.log; fi
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo26l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 2 --workers 4 --device 0 --seed 42 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name yolo26l_visdrone_large_fresh_large_20260524_140922_seed42 2>&1 | tee outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed42.log; then
  echo "TRAIN_OK model=yolo26l.pt seed=42 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed42.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/large_20260524_140922 -maxdepth 1 -type d \( -name yolo26l_visdrone_large_fresh_large_20260524_140922_seed42 -o -name \*_yolo26l_visdrone_large_fresh_large_20260524_140922_seed42 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --workers 4 --device 0 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name eval_yolo26l_visdrone_large_fresh_large_20260524_140922_seed42)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed42.log || echo "EVAL_FAILED model=yolo26l.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed42.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolo26l.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed42.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolo26l.pt seed=42 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed42.log
fi
echo "DONE model=yolo26l.pt seed=42 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed42.log

echo "START model=yolo26l.pt seed=123 gpu=0 batch=2 at $(date -Is)"
if [[ "${RESOURCE_GUARD:-1}" == "1" ]]; then bash scripts/ubuntu/check_resource_margin.sh --path /home/oem/projects/multi-uav-marine-city --gpu 0 --min-free-gb "$MIN_FREE_GB" --max-disk-use-percent "$MAX_DISK_USE_PERCENT" --min-ram-gb "$MIN_RAM_GB" --min-gpu-free-gb "$MIN_GPU_FREE_GB" --wait-seconds "$GUARD_WAIT_SECONDS" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed123.log; fi
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo26l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 2 --workers 4 --device 0 --seed 123 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name yolo26l_visdrone_large_fresh_large_20260524_140922_seed123 2>&1 | tee outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed123.log; then
  echo "TRAIN_OK model=yolo26l.pt seed=123 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed123.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/large_20260524_140922 -maxdepth 1 -type d \( -name yolo26l_visdrone_large_fresh_large_20260524_140922_seed123 -o -name \*_yolo26l_visdrone_large_fresh_large_20260524_140922_seed123 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --workers 4 --device 0 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name eval_yolo26l_visdrone_large_fresh_large_20260524_140922_seed123)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed123.log || echo "EVAL_FAILED model=yolo26l.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed123.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolo26l.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed123.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolo26l.pt seed=123 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed123.log
fi
echo "DONE model=yolo26l.pt seed=123 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed123.log

echo "START model=yolo26l.pt seed=2026 gpu=0 batch=2 at $(date -Is)"
if [[ "${RESOURCE_GUARD:-1}" == "1" ]]; then bash scripts/ubuntu/check_resource_margin.sh --path /home/oem/projects/multi-uav-marine-city --gpu 0 --min-free-gb "$MIN_FREE_GB" --max-disk-use-percent "$MAX_DISK_USE_PERCENT" --min-ram-gb "$MIN_RAM_GB" --min-gpu-free-gb "$MIN_GPU_FREE_GB" --wait-seconds "$GUARD_WAIT_SECONDS" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed2026.log; fi
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo26l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 2 --workers 4 --device 0 --seed 2026 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name yolo26l_visdrone_large_fresh_large_20260524_140922_seed2026 2>&1 | tee outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed2026.log; then
  echo "TRAIN_OK model=yolo26l.pt seed=2026 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed2026.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/large_20260524_140922 -maxdepth 1 -type d \( -name yolo26l_visdrone_large_fresh_large_20260524_140922_seed2026 -o -name \*_yolo26l_visdrone_large_fresh_large_20260524_140922_seed2026 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --workers 4 --device 0 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name eval_yolo26l_visdrone_large_fresh_large_20260524_140922_seed2026)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed2026.log || echo "EVAL_FAILED model=yolo26l.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed2026.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolo26l.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed2026.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolo26l.pt seed=2026 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed2026.log
fi
echo "DONE model=yolo26l.pt seed=2026 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/yolo26l_visdrone_large_fresh_large_20260524_140922_seed2026.log

echo "START model=rtdetr-l.pt seed=42 gpu=0 batch=2 at $(date -Is)"
if [[ "${RESOURCE_GUARD:-1}" == "1" ]]; then bash scripts/ubuntu/check_resource_margin.sh --path /home/oem/projects/multi-uav-marine-city --gpu 0 --min-free-gb "$MIN_FREE_GB" --max-disk-use-percent "$MAX_DISK_USE_PERCENT" --min-ram-gb "$MIN_RAM_GB" --min-gpu-free-gb "$MIN_GPU_FREE_GB" --wait-seconds "$GUARD_WAIT_SECONDS" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed42.log; fi
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model rtdetr-l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 2 --workers 4 --device 0 --seed 42 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed42 2>&1 | tee outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed42.log; then
  echo "TRAIN_OK model=rtdetr-l.pt seed=42 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed42.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/large_20260524_140922 -maxdepth 1 -type d \( -name rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed42 -o -name \*_rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed42 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --workers 4 --device 0 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name eval_rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed42)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed42.log || echo "EVAL_FAILED model=rtdetr-l.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed42.log
    else
      echo "EVAL_SKIPPED missing best.pt model=rtdetr-l.pt seed=42 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed42.log
    fi
  fi
else
  echo "TRAIN_FAILED model=rtdetr-l.pt seed=42 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed42.log
fi
echo "DONE model=rtdetr-l.pt seed=42 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed42.log

echo "START model=rtdetr-l.pt seed=123 gpu=0 batch=2 at $(date -Is)"
if [[ "${RESOURCE_GUARD:-1}" == "1" ]]; then bash scripts/ubuntu/check_resource_margin.sh --path /home/oem/projects/multi-uav-marine-city --gpu 0 --min-free-gb "$MIN_FREE_GB" --max-disk-use-percent "$MAX_DISK_USE_PERCENT" --min-ram-gb "$MIN_RAM_GB" --min-gpu-free-gb "$MIN_GPU_FREE_GB" --wait-seconds "$GUARD_WAIT_SECONDS" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed123.log; fi
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model rtdetr-l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 2 --workers 4 --device 0 --seed 123 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed123 2>&1 | tee outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed123.log; then
  echo "TRAIN_OK model=rtdetr-l.pt seed=123 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed123.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/large_20260524_140922 -maxdepth 1 -type d \( -name rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed123 -o -name \*_rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed123 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --workers 4 --device 0 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name eval_rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed123)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed123.log || echo "EVAL_FAILED model=rtdetr-l.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed123.log
    else
      echo "EVAL_SKIPPED missing best.pt model=rtdetr-l.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed123.log
    fi
  fi
else
  echo "TRAIN_FAILED model=rtdetr-l.pt seed=123 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed123.log
fi
echo "DONE model=rtdetr-l.pt seed=123 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed123.log

echo "START model=rtdetr-l.pt seed=2026 gpu=0 batch=2 at $(date -Is)"
if [[ "${RESOURCE_GUARD:-1}" == "1" ]]; then bash scripts/ubuntu/check_resource_margin.sh --path /home/oem/projects/multi-uav-marine-city --gpu 0 --min-free-gb "$MIN_FREE_GB" --max-disk-use-percent "$MAX_DISK_USE_PERCENT" --min-ram-gb "$MIN_RAM_GB" --min-gpu-free-gb "$MIN_GPU_FREE_GB" --wait-seconds "$GUARD_WAIT_SECONDS" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed2026.log; fi
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model rtdetr-l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 2 --workers 4 --device 0 --seed 2026 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed2026 2>&1 | tee outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed2026.log; then
  echo "TRAIN_OK model=rtdetr-l.pt seed=2026 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed2026.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/large_20260524_140922 -maxdepth 1 -type d \( -name rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed2026 -o -name \*_rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed2026 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --workers 4 --device 0 --project outputs/detectors/server_fresh_baselines/large_20260524_140922 --name eval_rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed2026)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed2026.log || echo "EVAL_FAILED model=rtdetr-l.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed2026.log
    else
      echo "EVAL_SKIPPED missing best.pt model=rtdetr-l.pt seed=2026 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed2026.log
    fi
  fi
else
  echo "TRAIN_FAILED model=rtdetr-l.pt seed=2026 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed2026.log
fi
echo "DONE model=rtdetr-l.pt seed=2026 gpu=0 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/large_20260524_140922/rtdetr-l_visdrone_large_fresh_large_20260524_140922_seed2026.log

echo "GPU worker 0 finished at $(date -Is)"
touch outputs/experiments/server_fresh/large_20260524_140922/jobs/gpu0.done
