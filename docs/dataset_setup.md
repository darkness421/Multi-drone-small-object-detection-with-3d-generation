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
4. `TinyPerson`
5. `AI-TOD`

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

변환 스크립트는 서버에서 기본적으로 YOLO image tree를 hardlink로 만든다.
따라서 raw/extracted image를 다시 복사하지 않아 디스크 사용량을 줄인다.
공식 UAVDT zip을 그대로 푼 경우에는 `data/raw/UAVDT/_official_extract`를
`RAW_ROOT`로 넘기면 된다. 변환기는 `M####` 형식의 공식 sequence directory만
사용하고, annotation은 `*_gt.txt`를 `*_gt_whole.txt`나 `*_gt_ignore.txt`보다
우선한다.

```bash
RAW_ROOT=data/raw/UAVDT/_official_extract bash scripts/ubuntu/prepare_uavdt_dataset.sh
```

준비가 끝나면 VisDrone queue 뒤에 UAVDT 비교 baseline을 붙인다.

```bash
bash scripts/ubuntu/start_uavdt_comparisons_pending.sh
bash scripts/ubuntu/collect_cross_dataset_results.sh
```

UAVDT raw 파일이 비어 있으면 readiness check가 실패하고 학습은 시작하지
않는다.

## TinyPerson

TinyPerson은 final detector가 정해진 뒤 detector-only supplementary stress
test로 추가한다. VisDrone이 multi-class UAV dense detection의 primary
benchmark라면, TinyPerson은 4x/8x/16x head와 overlap-aware decision module이
극소 사람 객체에도 도움이 되는지 보여주는 보조 근거다.

공식 다운로드:

- Official benchmark repo: `https://github.com/ucas-vg/PointTinyBenchmark/tree/TinyBenchmark`
- Official Google Drive id listed in the repo README:
  `1KrH9uEC9q4RdKJz-k34Q6v5hRewU5HOw`

서버에서 다운로드를 먼저 시작한다.

```bash
bash scripts/ubuntu/download_tinyperson_dataset_tmux.sh
tmux attach -t server-tinyperson-download
```

다운로드와 압축 해제가 끝나면 COCO-style annotation을 YOLO tree로 변환한다.
watcher가 raw JSON을 발견하면 자동 변환도 시도하지만, 수동으로 확인할 때는
아래 명령을 쓴다.

```bash
bash scripts/ubuntu/prepare_tinyperson_dataset.sh
```

기대하는 변환 결과:

```text
data/processed/tinyperson_yolo/
  images/train/
  images/val/
  labels/train/
  labels/val/
  data.yaml
```

권장 범위:

- YOLOv11l baseline
- final proposed detector
- 가능하면 Core 1 + Core 2 architecture-only variant
- input size `1280` under the corrected TinyPerson corner/original-window
  protocol
- 먼저 seed `42`만 GPU0에서 실행하고, 결과가 좋으면 `42, 123, 2026`으로 확장
- GPU1은 TinyPerson에 쓰지 않고 Isaac/3D/reasoner lane에 남겨둔다.

TinyPerson은 main detector gate가 아니라 supplementary validation으로 둔다.
즉, VisDrone 결과를 튜닝한 뒤 TinyPerson으로 generalization/stress-test를
보여주는 방식이 안전하다.

자동 큐:

```bash
bash scripts/ubuntu/start_tinyperson_corner_original_queue.sh
```

이 큐는 TinyPerson corner annotation window를 실제 crop image로 materialize하고,
모든 person category를 단일 `person` class로 collapse한 뒤 GPU0에서 corrected
TinyPerson check를 시작한다. 기존 640 변환 결과는 full image와 corner annotation
좌표계가 섞였기 때문에 supplementary diagnostic으로만 유지한다.
