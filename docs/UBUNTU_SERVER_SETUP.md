# Ubuntu Server Setup

This repo is shared by Windows and Ubuntu, so server-only commands live under
`scripts/ubuntu/` and server paths live in `configs/paths.ubuntu.yaml`.

## Scope

The current stage is baseline reorganization. Do not start long training until
the environment and dataset checks pass.

## Environment Check

```bash
cd /home/oem/projects/multi-uav-marine-city
bash scripts/ubuntu/check_env.sh
```

The check prints Python, active conda env, PyTorch/CUDA status, RTX GPU names,
OpenCV/numpy/scipy/sklearn/ultralytics versions, dataset roots, and output paths.

## Dataset Check

```bash
bash scripts/ubuntu/check_dataset_ready.sh
bash scripts/ubuntu/check_dataset_ready.sh --strict
bash scripts/ubuntu/preflight_baseline.sh
```

Required VisDrone paths:

- `data/raw/VisDrone2019-DET`
- `data/processed/visdrone_yolo/images/{train,val,test}`
- `data/processed/visdrone_yolo/labels/{train,val,test}`

Prepare VisDrone from a local source directory:

```bash
SOURCE=/path/to/downloads bash scripts/ubuntu/prepare_visdrone_dataset_tmux.sh
```

Or let the script use the configured download mirror:

```bash
bash scripts/ubuntu/prepare_visdrone_dataset_tmux.sh
```

The script stages local zips/folders when `SOURCE` is set, downloads missing
splits into `data/raw/downloads`, converts to COCO/YOLO, and reruns preflight.

UAVDT is tracked as the second dataset target, but the first server baseline
sweep is VisDrone2019-DET.

`preflight_baseline.sh` writes `outputs/experiments/server_preflight.json` and
`outputs/experiments/server_preflight.md`. It blocks long training when GPU,
PyTorch CUDA, tmux, raw data, or converted YOLO data are not ready.

## Output Policy

Do not push raw datasets, downloaded weights, raw Ultralytics runs, caches, or
logs. Git may track code/config/docs plus compact CSV/JSON summaries and report
PNGs:

- `outputs/experiments/*.csv`
- `outputs/experiments/*.json`
- `outputs/reports/*.png`
- `outputs/reports/server_baselines/README.md`
- `outputs/reports/server_baselines/tables/*.csv`
- `outputs/reports/server_baselines/figures/*.png`
- `outputs/reports/server_baselines/stage_gate.*`

Large artifacts remain ignored under `data/`, `outputs/detectors/`, `runs/`,
`weights/`, `.cache/`, and model weight extensions.

After collecting server results, the compact report bundle is available at
`outputs/reports/server_baselines/README.md`. It mirrors the dashboard,
summary/results/p-value CSVs, and detector stage gate in one Git-friendly
folder.
