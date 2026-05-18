# CoM3D-ACE

`CoM3D-ACE`는 cooperative multi-UAV small object detection 연구를 위한 작업 저장소입니다.

현재 단계는 Ubuntu 서버 detector baseline 재정비와 proposed perception module 준비입니다. 긴 학습은 tmux 스크립트로 수동 실행하고, repo에는 코드/config/docs/요약 CSV/보고서 PNG만 관리합니다.

## 지금 남겨둘 것

- `docs/survey_workspace.md`: 서베이 결과, 아이디어, dataset 후보, 최종 시스템 후보를 임시 정리
- `notion_exports/`: Notion에 붙여넣을 최소 Markdown export
- `docs/server_training_plan.md`: Ubuntu 서버 baseline 학습 계획
- `docs/server_progress.md`: 서버 실험 준비 진행 기록
- 코드 scaffold: baseline 후 proposed module로 확장할 초기 구현 뼈대

## 현재 코드 모듈

```text
data/converters/     VisDrone, UAVDT, AI-TOD, CoM3D JSON conversion
detectors/           YOLO/RT-DETR/D-FINE wrapper interfaces
evidence/            EvidenceToken, uncertainty, 2D-to-3D lifting
alignment/           cross-view / cross-resolution cost and matching
graph/               3D evidence graph construction
ambiguity/           ambiguity score and reason diagnosis
policy/              re-observation candidate selection
vlm/                 SAGE prompt builder and JSON parser
simulation/          Isaac/Cesium episode manifest helpers
evaluation/          metrics and statistical utilities
scripts/             experiment entrypoint shell scripts
```

## Windows Quick Start

```bat
conda env create -f environment.yml
conda activate com3d-ace
scripts\00_check_env.bat
scripts\00_check_datasets.bat
scripts\21_stage_visdrone_from_downloads.bat
scripts\01_convert_datasets.bat
scripts\10_check_training_readiness.bat
scripts\04_train_detector_baselines.bat
```

Dataset 경로는 `configs/dataset_roots.yaml`에서 수정합니다.
`scripts\00_check_datasets.bat`를 먼저 실행하면 `VisDrone`, `UAVDT`, `AI-TOD` raw path 중 무엇이 아직 비어 있는지 바로 확인할 수 있습니다.
`scripts\21_stage_visdrone_from_downloads.bat`는 `Downloads`에 있는 VisDrone zip 또는 폴더를 repo raw 구조에 맞게 배치할 수 있는 dry-run 도구입니다. 실제 복사/압축해제는 `scripts\21_stage_visdrone_from_downloads.bat apply`로 실행합니다.
VisDrone 원본이 PC에 없으면 `scripts\23_prepare_visdrone_visible_terminal.bat`로 다운로드, 변환, readiness check, preview까지 새 터미널에서 진행할 수 있습니다.
`scripts\10_check_training_readiness.bat`는 YOLO용 `data.yaml`, image/label 폴더, placeholder 이미지 여부, active Python 환경의 `ultralytics` 설치 여부를 확인합니다.

VisDrone YOLO baseline 학습:

```bat
scripts\11_train_yolo11n_visdrone.bat 100
scripts\12_train_yolov8n_visdrone.bat 100
```

Scratch 학습을 5개 seed로 반복하고, 나중에 p-value 계산이 가능하도록 seed별 metric CSV를 남길 때:

```bat
scripts\24_train_yolo11n_visdrone_5seed_scratch.bat 100 0
```

결과는 `outputs\experiments\multiseed\*_seed_metrics.csv`와 `*_summary.json`에 저장됩니다. 각 seed의 `best.pt`는 validation 후 image-level class-presence `ROC-AUC`도 함께 기록합니다.

두 방법의 seed별 CSV가 준비된 뒤 p-value를 계산할 때:

```bat
python -m evaluation.seed_statistics --baseline-csv outputs\experiments\multiseed\baseline_seed_metrics.csv --candidate-csv outputs\experiments\multiseed\ours_seed_metrics.csv --metric AP --out outputs\experiments\multiseed\ap_pvalue.json
python -m evaluation.seed_statistics --baseline-csv outputs\experiments\multiseed\baseline_seed_metrics.csv --candidate-csv outputs\experiments\multiseed\ours_seed_metrics.csv --metric ROC-AUC --out outputs\experiments\multiseed\roc_auc_pvalue.json
```

학습 로그를 새 터미널 창에서 실시간으로 보면서 실행:

```bat
scripts\17_train_yolo_visible_terminal.bat 100 yolo11n
scripts\17_train_yolo_visible_terminal.bat 100 yolov8n
```

학습 결과 기록까지 자동으로 남기려면 아래 launcher를 우선 사용합니다.

```bat
scripts\22_train_yolo_logged_visible_terminal.bat 100 yolo11n
scripts\22_train_yolo_logged_visible_terminal.bat 100 yolov8n
```

결과는 `outputs\experiments\<run_id>\experiment.md`와 `outputs\experiments\training_experiment_index.csv`에 저장됩니다.

학습이 끝난 뒤 best weight를 평가할 때:

```bat
scripts\13_eval_yolo_visdrone.bat outputs\detectors\...\best.pt
scripts\18_eval_yolo_visible_terminal.bat outputs\detectors\...\best.pt
```

Detector 테스트 결과를 눈으로 확인할 때:

```bat
scripts\16_make_visible_smoke_sample.bat
scripts\19_preview_yolo_dataset.bat configs\detector\visdrone_yolo_data.yaml train
scripts\15_run_visible_yolo_preview.bat data\sample_images yolo11n.pt
```

이미 생성된 EvidenceToken JSONL만 확인할 때:

```bat
scripts\14_preview_evidence_tokens.bat outputs\evidence\tokens.jsonl
```

Isaac Sim은 GUI에서 장면을 보면서 실행하는 흐름을 기본으로 합니다.

```bat
scripts\20_launch_isaac_visible.bat
```

상세한 visible 실행 원칙은 `docs/visible_execution_workflow.md`에 정리합니다.

## Ubuntu Server Quick Start

서버 전용 경로는 `configs/paths.ubuntu.yaml`, 실행 스크립트는 `scripts/ubuntu/`에 둡니다.

```bash
cd /home/oem/projects/multi-uav-marine-city
bash scripts/ubuntu/check_env.sh
bash scripts/ubuntu/check_dataset_ready.sh
```

데이터셋 readiness가 통과한 뒤에만 긴 학습을 tmux에서 시작합니다.

```bash
bash scripts/ubuntu/preflight_baseline.sh
bash scripts/ubuntu/prepare_visdrone_dataset_tmux.sh
bash scripts/ubuntu/train_visdrone_pair_tmux.sh visdrone-pair yolov8n.pt yolo11n.pt 42 100 8 1280
bash scripts/ubuntu/watch_training.sh visdrone-pair
```

전체 preliminary baseline queue는 기본 3 seeds `42,123,2026`으로 준비됩니다.

```bash
bash scripts/ubuntu/train_visdrone_baselines_tmux.sh server-visdrone-baselines 100 8 1280
```

학습이 끝난 뒤 결과를 수집합니다.

```bash
bash scripts/ubuntu/collect_server_results.sh
bash scripts/ubuntu/check_detector_stage_gate.sh
```

결과 CSV는 YOLO 세대, non-YOLO detector family, checkpoint scale, measured
parameter-size group을 별도 컬럼으로 분리합니다. 예를 들어 YOLOv12s는
`detector_family=YOLO`, `yolo_version=v12`, `model_scale=small`로 기록되고,
RT-DETR 계열은 `architecture_group=non_yolo`로 분리됩니다.

Detector 흐름은 stage gate로 관리합니다. 모든 baseline/comparison 모델을
먼저 끝내고, best overall 및 best lightweight baseline을 고정한 뒤
proposed perception module을 수정합니다. Proposed model이 두 비교 기준을
넘으면 3D generation과 Marine City multi-angle benchmark 단계로 이동합니다.

주요 산출물:

- `outputs/experiments/server_baseline_results.csv`
- `outputs/experiments/server_baseline_summary.csv`
- `outputs/experiments/server_baseline_pvalues.csv`
- `outputs/reports/server_baseline_dashboard.png`

Raw dataset, weights, raw runs, cache, training logs는 GitHub push 대상이 아닙니다. CSV/JSON summary와 report PNG만 작게 관리합니다.

## 3D Generation And Final Reasoner

Marine City multi-angle benchmark와 3D 생성형 모델 비교 실험은 별도 축으로 관리합니다.

```bash
bash scripts/ubuntu/prepare_marinecity_multiview_benchmark.sh
bash scripts/ubuntu/train_3d_generators_tmux.sh
bash scripts/ubuntu/collect_3d_generation_results.sh
```

비교 대상은 NeRF, Instant-NGP, Mip-NeRF 360, 3D Gaussian Splatting입니다. 계획은 `docs/3d_generation_experiment_plan.md`에 정리되어 있습니다.

LLM/VLM final adjudicator는 detector, geometry, ambiguity score, 선택적 LLM 응답을 합쳐 최종 object class와 re-observation 필요 여부를 결정합니다.

```bash
python -m reasoning.final_adjudicator --hypotheses outputs/graph/hypotheses.json --ambiguity outputs/ambiguity/scores.json --llm outputs/reasoning/llm_responses.json --out outputs/reasoning/final_decisions.json
python -m evaluation.reasoner_ablation --hypotheses outputs/graph/hypotheses.json --labels outputs/reasoning/final_labels.json --ambiguity outputs/ambiguity/scores.json --llm outputs/reasoning/llm_responses.json
```

장단점 및 ablation 계획은 `docs/llm_reasoner_adjudicator_plan.md`에 정리되어 있습니다.

EvidenceToken 생성 예시:

```bat
python -m detectors.yolo_folder_infer --weights yolo11n.pt --images data\sample_images --out-jsonl outputs\evidence\tokens.jsonl --crop-dir outputs\crops
```

Graph / ambiguity / policy prototype:

```bat
scripts\06_run_core_pipeline.bat
scripts\07_eval_association.bat
scripts\08_run_system_comparison.bat
scripts\09_collect_detector_metrics.bat
python -m graph.graph_builder --tokens outputs\evidence\tokens.jsonl --out outputs\graph\hypotheses.json
python -m ambiguity.ambiguity_scorer --hypotheses outputs\graph\hypotheses.json --out outputs\ambiguity\scores.json
python -m policy.policy_simulator --hypotheses outputs\graph\hypotheses.json --ambiguity outputs\ambiguity\scores.json --out outputs\policy\metrics.csv
```

Isaac export dry-run:

```bat
scripts\03_export_isaac_dataset.bat
```

실제 Isaac Sim에서는 아래처럼 Isaac의 `python.bat`로 같은 entrypoint를 실행합니다.

```bat
cd C:\isaacsim
python.bat C:\Users\jc\multi-uav-marine-city\simulation\isaac\export_rgb_depth_pose.py --config C:\Users\jc\multi-uav-marine-city\configs\sim\isaac_export.yaml
```

## 나중에 다시 만들 것

- 최종 제안 시스템 그림
- 세부 모듈 구조와 수식
- dataset selection
- experiment plan
- Isaac Sim / Cesium 구현 과정 문서
- paper section draft

## Quick Checks

```powershell
python -m unittest discover tests
python sim\scenarios\generate_scenarios.py --count 20
python datasets\converters\marinecity_to_coco.py --input datasets\converters\dummy_marinecity_input.json --validate-only
python pipelines\run_dummy_evidence_pipeline.py
python experiments\run_exp01_single_uav.py --dummy
```
