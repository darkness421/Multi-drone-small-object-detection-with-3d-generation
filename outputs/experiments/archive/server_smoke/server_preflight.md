# Server Baseline Preflight

- Can start training: True

## Blockers

- None

## CUDA

- Torch: 2.11.0+cu128
- CUDA version: 12.8
- CUDA available: True
- Device count: 2

## Next Commands

```bash
nvidia-smi
```
```bash
find data/raw/VisDrone2019-DET -type f | head
```
```bash
conda run --no-capture-output -n com3d-ace python -m scripts.convert_datasets
```
```bash
bash scripts/ubuntu/preflight_baseline.sh --strict
```
```bash
bash scripts/ubuntu/train_visdrone_pair_tmux.sh visdrone-pair yolov8n.pt yolo11n.pt 42 100 8 1280
```
