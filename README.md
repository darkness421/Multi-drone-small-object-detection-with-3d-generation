# CoM3D-ACE

`CoM3D-ACE`는 cooperative multi-UAV small object detection 연구를 위한 작업 저장소입니다.

현재 단계는 `Survey phase`입니다. 관련 연구 조사가 끝나기 전까지 전체 시스템 구조, 세부 모듈, dataset plan, experiment plan은 확정하지 않습니다.

## 지금 남겨둘 것

- `docs/survey_workspace.md`: 서베이 결과, 아이디어, dataset 후보, 최종 시스템 후보를 임시 정리
- `notion_exports/`: Notion에 붙여넣을 최소 Markdown export
- 코드 scaffold: 나중에 확정된 시스템에 맞춰 수정할 초기 구현 뼈대

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
python scripts\check_env.py
scripts\01_convert_datasets.bat
scripts\04_train_detector_baselines.bat
```

Dataset 경로는 `configs/dataset_roots.yaml`에서 수정합니다.

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
