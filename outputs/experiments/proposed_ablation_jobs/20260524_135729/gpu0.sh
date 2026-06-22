#!/usr/bin/env bash
set -euo pipefail
cd /home/oem/projects/multi-uav-marine-city
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export MPLCONFIGDIR=/home/oem/projects/multi-uav-marine-city/.cache/matplotlib
export YOLO_CONFIG_DIR=/home/oem/projects/multi-uav-marine-city/.cache/ultralytics
mkdir -p "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR"
echo "START ablation=control method=Proposed-Control-yolo11s seed=42 gpu=0 at $(date -Is)"
CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0 conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo11s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 42 --project outputs/detectors/server_proposed_ablation --name proposed_control_yolo11s_visdrone_seed42 --method Proposed-Control-yolo11s --ablation control --base-model yolo11s.pt --proposed-module control --implementation-status implemented 2>&1 | tee /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_control_yolo11s_visdrone_seed42.log
run_dir=$(find outputs/detectors/server_proposed_ablation -maxdepth 1 -type d -name "*_proposed_control_yolo11s_visdrone_seed42" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
  eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_proposed_ablation --name eval_proposed_control_yolo11s_visdrone_seed42 --method Proposed-Control-yolo11s --ablation control --base-model yolo11s.pt --proposed-module control --implementation-status implemented)
  if [[ 1 == "1" ]]; then eval_args+=(--roc-auc); fi
  conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_control_yolo11s_visdrone_seed42.log
fi
echo "DONE ablation=control method=Proposed-Control-yolo11s seed=42 gpu=0 at $(date -Is)"
echo "START ablation=control method=Proposed-Control-yolo11s seed=2026 gpu=0 at $(date -Is)"
CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0 conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo11s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 2026 --project outputs/detectors/server_proposed_ablation --name proposed_control_yolo11s_visdrone_seed2026 --method Proposed-Control-yolo11s --ablation control --base-model yolo11s.pt --proposed-module control --implementation-status implemented 2>&1 | tee /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_control_yolo11s_visdrone_seed2026.log
run_dir=$(find outputs/detectors/server_proposed_ablation -maxdepth 1 -type d -name "*_proposed_control_yolo11s_visdrone_seed2026" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
  eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_proposed_ablation --name eval_proposed_control_yolo11s_visdrone_seed2026 --method Proposed-Control-yolo11s --ablation control --base-model yolo11s.pt --proposed-module control --implementation-status implemented)
  if [[ 1 == "1" ]]; then eval_args+=(--roc-auc); fi
  conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_control_yolo11s_visdrone_seed2026.log
fi
echo "DONE ablation=control method=Proposed-Control-yolo11s seed=2026 gpu=0 at $(date -Is)"
echo "START ablation=wavelet_stem method=Proposed-WaveletStem-yolo11s seed=123 gpu=0 at $(date -Is)"
CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0 conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo11s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 123 --project outputs/detectors/server_proposed_ablation --name proposed_wavelet_stem_yolo11s_visdrone_seed123 --method Proposed-WaveletStem-yolo11s --ablation wavelet_stem --base-model yolo11s.pt --proposed-module wavelet_stem --model-patches wavelet_stem --implementation-status implemented 2>&1 | tee /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_wavelet_stem_yolo11s_visdrone_seed123.log
run_dir=$(find outputs/detectors/server_proposed_ablation -maxdepth 1 -type d -name "*_proposed_wavelet_stem_yolo11s_visdrone_seed123" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
  eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_proposed_ablation --name eval_proposed_wavelet_stem_yolo11s_visdrone_seed123 --method Proposed-WaveletStem-yolo11s --ablation wavelet_stem --base-model yolo11s.pt --proposed-module wavelet_stem --implementation-status implemented)
  if [[ 1 == "1" ]]; then eval_args+=(--roc-auc); fi
  conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_wavelet_stem_yolo11s_visdrone_seed123.log
fi
echo "DONE ablation=wavelet_stem method=Proposed-WaveletStem-yolo11s seed=123 gpu=0 at $(date -Is)"
echo "START ablation=se_neck method=Proposed-SE-yolo11s seed=42 gpu=0 at $(date -Is)"
CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0 conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo11s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 42 --project outputs/detectors/server_proposed_ablation --name proposed_se_neck_yolo11s_visdrone_seed42 --method Proposed-SE-yolo11s --ablation se_neck --base-model yolo11s.pt --proposed-module se_neck --model-patches se_neck --implementation-status implemented 2>&1 | tee /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_se_neck_yolo11s_visdrone_seed42.log
run_dir=$(find outputs/detectors/server_proposed_ablation -maxdepth 1 -type d -name "*_proposed_se_neck_yolo11s_visdrone_seed42" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
  eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_proposed_ablation --name eval_proposed_se_neck_yolo11s_visdrone_seed42 --method Proposed-SE-yolo11s --ablation se_neck --base-model yolo11s.pt --proposed-module se_neck --implementation-status implemented)
  if [[ 1 == "1" ]]; then eval_args+=(--roc-auc); fi
  conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_se_neck_yolo11s_visdrone_seed42.log
fi
echo "DONE ablation=se_neck method=Proposed-SE-yolo11s seed=42 gpu=0 at $(date -Is)"
echo "START ablation=se_neck method=Proposed-SE-yolo11s seed=2026 gpu=0 at $(date -Is)"
CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0 conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo11s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 2026 --project outputs/detectors/server_proposed_ablation --name proposed_se_neck_yolo11s_visdrone_seed2026 --method Proposed-SE-yolo11s --ablation se_neck --base-model yolo11s.pt --proposed-module se_neck --model-patches se_neck --implementation-status implemented 2>&1 | tee /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_se_neck_yolo11s_visdrone_seed2026.log
run_dir=$(find outputs/detectors/server_proposed_ablation -maxdepth 1 -type d -name "*_proposed_se_neck_yolo11s_visdrone_seed2026" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
  eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_proposed_ablation --name eval_proposed_se_neck_yolo11s_visdrone_seed2026 --method Proposed-SE-yolo11s --ablation se_neck --base-model yolo11s.pt --proposed-module se_neck --implementation-status implemented)
  if [[ 1 == "1" ]]; then eval_args+=(--roc-auc); fi
  conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_se_neck_yolo11s_visdrone_seed2026.log
fi
echo "DONE ablation=se_neck method=Proposed-SE-yolo11s seed=2026 gpu=0 at $(date -Is)"
echo "START ablation=cbam_neck method=Proposed-CBAM-yolo11s seed=123 gpu=0 at $(date -Is)"
CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0 conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo11s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 123 --project outputs/detectors/server_proposed_ablation --name proposed_cbam_neck_yolo11s_visdrone_seed123 --method Proposed-CBAM-yolo11s --ablation cbam_neck --base-model yolo11s.pt --proposed-module cbam_neck --model-patches cbam_neck --implementation-status implemented 2>&1 | tee /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_cbam_neck_yolo11s_visdrone_seed123.log
run_dir=$(find outputs/detectors/server_proposed_ablation -maxdepth 1 -type d -name "*_proposed_cbam_neck_yolo11s_visdrone_seed123" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
  eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_proposed_ablation --name eval_proposed_cbam_neck_yolo11s_visdrone_seed123 --method Proposed-CBAM-yolo11s --ablation cbam_neck --base-model yolo11s.pt --proposed-module cbam_neck --implementation-status implemented)
  if [[ 1 == "1" ]]; then eval_args+=(--roc-auc); fi
  conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_cbam_neck_yolo11s_visdrone_seed123.log
fi
echo "DONE ablation=cbam_neck method=Proposed-CBAM-yolo11s seed=123 gpu=0 at $(date -Is)"
echo "START ablation=partial_deformable_neck method=Proposed-DeformableNeck-yolo11s seed=42 gpu=0 at $(date -Is)"
CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0 conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo11s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 42 --project outputs/detectors/server_proposed_ablation --name proposed_partial_deformable_neck_yolo11s_visdrone_seed42 --method Proposed-DeformableNeck-yolo11s --ablation partial_deformable_neck --base-model yolo11s.pt --proposed-module partial_deformable_neck --model-patches partial_deformable_neck --implementation-status implemented 2>&1 | tee /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_partial_deformable_neck_yolo11s_visdrone_seed42.log
run_dir=$(find outputs/detectors/server_proposed_ablation -maxdepth 1 -type d -name "*_proposed_partial_deformable_neck_yolo11s_visdrone_seed42" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
  eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_proposed_ablation --name eval_proposed_partial_deformable_neck_yolo11s_visdrone_seed42 --method Proposed-DeformableNeck-yolo11s --ablation partial_deformable_neck --base-model yolo11s.pt --proposed-module partial_deformable_neck --implementation-status implemented)
  if [[ 1 == "1" ]]; then eval_args+=(--roc-auc); fi
  conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_partial_deformable_neck_yolo11s_visdrone_seed42.log
fi
echo "DONE ablation=partial_deformable_neck method=Proposed-DeformableNeck-yolo11s seed=42 gpu=0 at $(date -Is)"
echo "START ablation=partial_deformable_neck method=Proposed-DeformableNeck-yolo11s seed=2026 gpu=0 at $(date -Is)"
CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0 conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo11s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 2026 --project outputs/detectors/server_proposed_ablation --name proposed_partial_deformable_neck_yolo11s_visdrone_seed2026 --method Proposed-DeformableNeck-yolo11s --ablation partial_deformable_neck --base-model yolo11s.pt --proposed-module partial_deformable_neck --model-patches partial_deformable_neck --implementation-status implemented 2>&1 | tee /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_partial_deformable_neck_yolo11s_visdrone_seed2026.log
run_dir=$(find outputs/detectors/server_proposed_ablation -maxdepth 1 -type d -name "*_proposed_partial_deformable_neck_yolo11s_visdrone_seed2026" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
  eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_proposed_ablation --name eval_proposed_partial_deformable_neck_yolo11s_visdrone_seed2026 --method Proposed-DeformableNeck-yolo11s --ablation partial_deformable_neck --base-model yolo11s.pt --proposed-module partial_deformable_neck --implementation-status implemented)
  if [[ 1 == "1" ]]; then eval_args+=(--roc-auc); fi
  conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_partial_deformable_neck_yolo11s_visdrone_seed2026.log
fi
echo "DONE ablation=partial_deformable_neck method=Proposed-DeformableNeck-yolo11s seed=2026 gpu=0 at $(date -Is)"
echo "START ablation=wavelet_se method=Proposed-WaveletSE-yolo11s seed=123 gpu=0 at $(date -Is)"
CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0 conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo11s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 123 --project outputs/detectors/server_proposed_ablation --name proposed_wavelet_se_yolo11s_visdrone_seed123 --method Proposed-WaveletSE-yolo11s --ablation wavelet_se --base-model yolo11s.pt --proposed-module wavelet_stem+se_neck --model-patches wavelet_stem,se_neck --implementation-status implemented 2>&1 | tee /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_wavelet_se_yolo11s_visdrone_seed123.log
run_dir=$(find outputs/detectors/server_proposed_ablation -maxdepth 1 -type d -name "*_proposed_wavelet_se_yolo11s_visdrone_seed123" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
  eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_proposed_ablation --name eval_proposed_wavelet_se_yolo11s_visdrone_seed123 --method Proposed-WaveletSE-yolo11s --ablation wavelet_se --base-model yolo11s.pt --proposed-module wavelet_stem+se_neck --implementation-status implemented)
  if [[ 1 == "1" ]]; then eval_args+=(--roc-auc); fi
  conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_wavelet_se_yolo11s_visdrone_seed123.log
fi
echo "DONE ablation=wavelet_se method=Proposed-WaveletSE-yolo11s seed=123 gpu=0 at $(date -Is)"
echo "START ablation=wavelet_cbam method=Proposed-WaveletCBAM-yolo11s seed=42 gpu=0 at $(date -Is)"
CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0 conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo11s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 42 --project outputs/detectors/server_proposed_ablation --name proposed_wavelet_cbam_yolo11s_visdrone_seed42 --method Proposed-WaveletCBAM-yolo11s --ablation wavelet_cbam --base-model yolo11s.pt --proposed-module wavelet_stem+cbam_neck --model-patches wavelet_stem,cbam_neck --implementation-status implemented 2>&1 | tee /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_wavelet_cbam_yolo11s_visdrone_seed42.log
run_dir=$(find outputs/detectors/server_proposed_ablation -maxdepth 1 -type d -name "*_proposed_wavelet_cbam_yolo11s_visdrone_seed42" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
  eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_proposed_ablation --name eval_proposed_wavelet_cbam_yolo11s_visdrone_seed42 --method Proposed-WaveletCBAM-yolo11s --ablation wavelet_cbam --base-model yolo11s.pt --proposed-module wavelet_stem+cbam_neck --implementation-status implemented)
  if [[ 1 == "1" ]]; then eval_args+=(--roc-auc); fi
  conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_wavelet_cbam_yolo11s_visdrone_seed42.log
fi
echo "DONE ablation=wavelet_cbam method=Proposed-WaveletCBAM-yolo11s seed=42 gpu=0 at $(date -Is)"
echo "START ablation=wavelet_cbam method=Proposed-WaveletCBAM-yolo11s seed=2026 gpu=0 at $(date -Is)"
CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0 conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo11s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 2026 --project outputs/detectors/server_proposed_ablation --name proposed_wavelet_cbam_yolo11s_visdrone_seed2026 --method Proposed-WaveletCBAM-yolo11s --ablation wavelet_cbam --base-model yolo11s.pt --proposed-module wavelet_stem+cbam_neck --model-patches wavelet_stem,cbam_neck --implementation-status implemented 2>&1 | tee /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_wavelet_cbam_yolo11s_visdrone_seed2026.log
run_dir=$(find outputs/detectors/server_proposed_ablation -maxdepth 1 -type d -name "*_proposed_wavelet_cbam_yolo11s_visdrone_seed2026" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
  eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_proposed_ablation --name eval_proposed_wavelet_cbam_yolo11s_visdrone_seed2026 --method Proposed-WaveletCBAM-yolo11s --ablation wavelet_cbam --base-model yolo11s.pt --proposed-module wavelet_stem+cbam_neck --implementation-status implemented)
  if [[ 1 == "1" ]]; then eval_args+=(--roc-auc); fi
  conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_wavelet_cbam_yolo11s_visdrone_seed2026.log
fi
echo "DONE ablation=wavelet_cbam method=Proposed-WaveletCBAM-yolo11s seed=2026 gpu=0 at $(date -Is)"
echo "START ablation=full_proposed method=Proposed-Full-yolo11s seed=123 gpu=0 at $(date -Is)"
CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0 conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo train --model yolo11s.pt --data-yaml configs/detector/visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --device 0 --seed 123 --project outputs/detectors/server_proposed_ablation --name proposed_full_proposed_yolo11s_visdrone_seed123 --method Proposed-Full-yolo11s --ablation full_proposed --base-model yolo11s.pt --proposed-module wavelet_stem+cbam_neck+partial_deformable_neck --model-patches wavelet_stem,cbam_neck,partial_deformable_neck --implementation-status implemented 2>&1 | tee /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_full_proposed_yolo11s_visdrone_seed123.log
run_dir=$(find outputs/detectors/server_proposed_ablation -maxdepth 1 -type d -name "*_proposed_full_proposed_yolo11s_visdrone_seed123" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
  eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml configs/detector/visdrone_yolo_data.yaml --imgsz 1280 --device 0 --project outputs/detectors/server_proposed_ablation --name eval_proposed_full_proposed_yolo11s_visdrone_seed123 --method Proposed-Full-yolo11s --ablation full_proposed --base-model yolo11s.pt --proposed-module wavelet_stem+cbam_neck+partial_deformable_neck --implementation-status implemented)
  if [[ 1 == "1" ]]; then eval_args+=(--roc-auc); fi
  conda run --no-capture-output -n com3d-ace python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a /home/oem/projects/multi-uav-marine-city/outputs/logs/server_baselines/proposed_full_proposed_yolo11s_visdrone_seed123.log
fi
echo "DONE ablation=full_proposed method=Proposed-Full-yolo11s seed=123 gpu=0 at $(date -Is)"
