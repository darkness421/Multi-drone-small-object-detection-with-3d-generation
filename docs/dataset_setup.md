# Dataset Setup

오늘 목표는 public UAV dataset을 학습 가능한 구조로 넣고, 학습 전에 bbox preview로 확인하는 것이다.

## VisDrone

Repo가 기대하는 raw 구조:

```text
data/raw/VisDrone2019-DET/
  VisDrone2019-DET-train/
    images/
    annotations/
  VisDrone2019-DET-val/
    images/
    annotations/
  VisDrone2019-DET-test-dev/
    images/
    annotations/
```

다운로드한 zip 또는 압축 해제된 폴더가 `Downloads`에 있으면 먼저 dry-run으로 확인한다.

```bat
scripts\21_stage_visdrone_from_downloads.bat
```

출력에 `copy-dir` 또는 `extract-zip`이 보이면 실제 반영한다.

```bat
scripts\21_stage_visdrone_from_downloads.bat apply
```

그다음 변환과 preview를 실행한다.

```bat
scripts\00_check_datasets.bat
scripts\01_convert_datasets.bat
scripts\10_check_training_readiness.bat
scripts\19_preview_yolo_dataset.bat configs\detector\visdrone_yolo_data.yaml train
```

preview HTML에서 image와 bbox가 맞으면 YOLOv11n 학습으로 넘어간다.

```bat
scripts\17_train_yolo_visible_terminal.bat 100 yolo11n
```

원본 파일이 PC에 아직 없으면 아래 명령으로 다운로드부터 변환, readiness check, preview까지 한 번에 진행할 수 있다. 다운로드 용량은 train/val/test-dev 합쳐서 약 1.9GB이며, 새 터미널에서 진행률을 볼 수 있다.

```bat
scripts\23_prepare_visdrone_visible_terminal.bat
```

다운로드 source:

- Official dataset index: `https://github.com/VisDrone/VisDrone-Dataset`
- Mirror used by the setup script: `https://github.com/ultralytics/yolov5/releases/tag/v1.0`

## 현재 우선순위

1. `VisDrone2019-DET-train`
2. `VisDrone2019-DET-val`
3. `UAVDT`
4. `AI-TOD`

VisDrone train/val이 준비되면 detector baseline 학습을 시작할 수 있다.

## UAVDT

UAVDT는 VisDrone baseline이 안정화된 뒤 cross-dataset validation으로 쓴다.
서버에서는 아래 구조를 우선 기대한다.

```text
data/raw/UAVDT/
  images/<sequence>/*.jpg
  annotations/<sequence>.txt
```

로컬 폴더나 zip이 있으면 `SOURCE`로 넘겨 staged raw data, COCO JSON, YOLO
labels를 한 번에 준비한다.

```bash
SOURCE=/path/to/UAVDT bash scripts/ubuntu/prepare_uavdt_dataset.sh
```

서버에서 공식 Google Drive 원본 zip을 받을 때는 tmux 다운로드를 사용한다.
기본값은 먼저 zip만 받고, 완료 후 구조 확인/압축 해제/변환을 이어서 한다.

```bash
bash scripts/ubuntu/download_uavdt_dataset_tmux.sh
tmux attach -t server-uavdt-download
```

준비가 끝나면 VisDrone queue 뒤에 UAVDT 비교 baseline을 붙인다.

```bash
bash scripts/ubuntu/train_uavdt_comparisons_after_session.sh
bash scripts/ubuntu/collect_cross_dataset_results.sh
```

UAVDT raw 파일이 비어 있으면 readiness check가 실패하고 학습은 시작하지
않는다.
