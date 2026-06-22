# Training Experiment Logging

실제 detector 학습은 사용자가 볼 수 있는 터미널에서 실행하고, 각 실행 결과는 자동으로 `outputs/experiments`에 남긴다.

## Recommended Command

```bat
scripts\22_train_yolo_logged_visible_terminal.bat 100 yolo11n
scripts\22_train_yolo_logged_visible_terminal.bat 100 yolov8n
```

이 launcher는 새 터미널을 열고 다음 순서로 실행한다.

1. `com3d-ace` conda env 활성화
2. experiment manifest 생성
3. YOLO 학습 실행
4. 학습 성공/실패 상태 기록
5. Ultralytics `results.csv`, `best.pt`, `last.pt` 위치 기록
6. Notion에 붙여넣기 쉬운 Markdown summary 생성

## Output Files

```text
outputs/experiments/
  training_experiment_index.csv
  <run_id>/
    manifest.json
    experiment.md
```

`manifest.json`은 스크립트가 다시 읽기 좋은 원본 기록이고, `experiment.md`는 Notion에 그대로 붙여넣는 용도다. `training_experiment_index.csv`는 여러 학습 결과를 한 표로 모을 때 사용한다.

## Manual Tracking

학습을 수동으로 실행할 때도 같은 기록기를 사용할 수 있다.

```bat
for /f "delims=" %R in ('python -m scripts.track_training_experiment start --model yolo11n.pt --dataset VisDrone2019-DET --epochs 100 --print-run-id') do set RUN_ID=%R
python -m detectors.train_yolo train --model yolo11n.pt --data-yaml configs\detector\visdrone_yolo_data.yaml --epochs 100 --imgsz 1280 --batch 8 --name yolo11n_visdrone
python -m scripts.track_training_experiment finish --run-id %RUN_ID% --status completed --detector-root outputs\detectors
```
