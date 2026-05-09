# Visible Execution Workflow

이 프로젝트에서 실제 학습, 테스트, Isaac Sim 실행은 사용자가 눈으로 확인할 수 있는 형태를 기본으로 한다.

## Detector Training

1. `scripts\00_check_env.bat`
2. `scripts\00_check_datasets.bat`
3. `scripts\01_convert_datasets.bat`
4. `scripts\10_check_training_readiness.bat`
5. `scripts\11_train_yolo11n_visdrone.bat 100`

YOLO 학습 로그는 VS Code 터미널에서 그대로 확인한다. 학습 결과는 `outputs/detectors/` 아래에 저장한다.
사용자가 실시간으로 보기 쉽게 별도 터미널을 띄울 때는 아래 launcher를 사용한다.

```bat
scripts\17_train_yolo_visible_terminal.bat 100 yolo11n
scripts\17_train_yolo_visible_terminal.bat 100 yolov8n
```

평가도 터미널이 닫히지 않게 보면서 실행할 수 있다.

```bat
scripts\18_eval_yolo_visible_terminal.bat outputs\detectors\...\best.pt
```

## Detector Test Preview

추론 결과를 사람이 볼 수 있게 HTML preview로 만든다.

```bat
scripts\16_make_visible_smoke_sample.bat
scripts\15_run_visible_yolo_preview.bat data\sample_images yolo11n.pt
```

출력:

- `outputs\smoke\visible_sample\preview\index.html`
- `outputs\evidence\tokens.jsonl`
- `outputs\crops\`
- `outputs\preview\evidence_tokens\index.html`
- `outputs\preview\evidence_tokens\summary.csv`

이미 생성된 EvidenceToken만 확인할 때:

```bat
scripts\14_preview_evidence_tokens.bat outputs\evidence\tokens.jsonl
```

## Isaac Sim

Isaac Sim은 headless 실행보다 GUI 실행을 기본으로 한다.

```bat
scripts\20_launch_isaac_visible.bat
```

Isaac 설치 경로가 `C:\isaacsim`이 아니면 먼저 환경변수를 설정한다.

```bat
set ISAAC_ROOT=C:\path\to\isaacsim
scripts\20_launch_isaac_visible.bat
```

나중에 실제 export runner는 Isaac GUI에서 장면, UAV camera, bbox, re-observation viewpoint가 보이는 상태로 실행한다.
