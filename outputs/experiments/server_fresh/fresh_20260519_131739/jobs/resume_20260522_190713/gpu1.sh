#!/usr/bin/env bash
set -uo pipefail
cd /home/oem/projects/multi-uav-marine-city
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export MPLCONFIGDIR=/home/oem/projects/multi-uav-marine-city/.cache/matplotlib
export YOLO_CONFIG_DIR=/home/oem/projects/multi-uav-marine-city/.cache/ultralytics
export XDG_CACHE_HOME=/home/oem/projects/multi-uav-marine-city/.cache
mkdir -p "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR" "$XDG_CACHE_HOME"
echo "Resume GPU worker 1 started at $(date -Is)"

echo "START resume model=rtdetr-l.pt seed=123 gpu=1 batch=4 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model rtdetr-l.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 4 --device 1 --seed 123 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713 --name rtdetr-l_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/rtdetr-l_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713.log; then
  echo "TRAIN_OK model=rtdetr-l.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/rtdetr-l_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713 -maxdepth 1 -type d \( -name rtdetr-l_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713 -o -name \*_rtdetr-l_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713 --name eval_rtdetr-l_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/rtdetr-l_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713.log || echo "EVAL_FAILED model=rtdetr-l.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/rtdetr-l_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713.log
    else
      echo "EVAL_SKIPPED missing best.pt model=rtdetr-l.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/rtdetr-l_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713.log
    fi
  fi
else
  echo "TRAIN_FAILED model=rtdetr-l.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/rtdetr-l_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713.log
fi
echo "DONE model=rtdetr-l.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/rtdetr-l_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713.log

echo "START resume model=yolov10m.pt seed=123 gpu=1 batch=4 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolov10m.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 4 --device 1 --seed 123 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713 --name yolov10m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/yolov10m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713.log; then
  echo "TRAIN_OK model=yolov10m.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/yolov10m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713 -maxdepth 1 -type d \( -name yolov10m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713 -o -name \*_yolov10m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713 --name eval_yolov10m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/yolov10m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713.log || echo "EVAL_FAILED model=yolov10m.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/yolov10m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolov10m.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/yolov10m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolov10m.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/yolov10m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713.log
fi
echo "DONE model=yolov10m.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/yolov10m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713.log

echo "START resume model=yolo12m.pt seed=123 gpu=1 batch=4 at $(date -Is)"
if conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo12m.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 4 --device 1 --seed 123 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713 --name yolo12m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713 2>&1 | tee outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/yolo12m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713.log; then
  echo "TRAIN_OK model=yolo12m.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/yolo12m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713.log
  if [[ 1 == 1 ]]; then
    run_dir=$(find outputs/detectors/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713 -maxdepth 1 -type d \( -name yolo12m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713 -o -name \*_yolo12m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713 \) -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 1 --project outputs/detectors/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713 --name eval_yolo12m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713)
      if [[ 1 == 1 ]]; then eval_args+=(--roc-auc); fi
      conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/yolo12m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713.log || echo "EVAL_FAILED model=yolo12m.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/yolo12m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713.log
    else
      echo "EVAL_SKIPPED missing best.pt model=yolo12m.pt seed=123 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/yolo12m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713.log
    fi
  fi
else
  echo "TRAIN_FAILED model=yolo12m.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/yolo12m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713.log
fi
echo "DONE model=yolo12m.pt seed=123 gpu=1 at $(date -Is)" | tee -a outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/yolo12m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713.log

echo "Resume GPU worker 1 finished at $(date -Is)"
touch outputs/experiments/server_fresh/fresh_20260519_131739/jobs/resume_20260522_190713/gpu1.done
