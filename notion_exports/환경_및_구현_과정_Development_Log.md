# Development Log

- Notion Section: `환경 및 구현 과정`
- Status: `Not Started`
- Source: `docs/dev_log.md`
- Export Date: `2026-05-07`

---

# 개발 로그

이 문서는 Notion에 동기화하기 전에 중요한 개발 결정과 진행 과정을 기록합니다.

## 2026-04-30

- 로컬 작업 폴더를 `C:\Users\jc\multi-uav-marine-city`로 정리했습니다.
- GitHub 저장소를 연결했습니다: `https://github.com/darkness421/multi-uav-marine-city`.
- 공개 프로젝트 이름과 코드 패키지 이름에서 학회명인 `ACCV`를 제거했습니다.
- 최종 데모 목표를 정했습니다: `Isaac Sim`에서 Marine City 배경, 다중 UAV, 카메라 뷰, detection overlay, 3D fusion, re-observation 로직을 눈으로 확인하는 형태입니다.
- `Isaac Sim` 구현 전에 dataset 선정이 먼저 필요하다고 정리했습니다.
- Notion의 `04 Experiment Result` 열과 연결할 실험 결과 기록 문서 `docs/experiment_results.md`를 추가했습니다.
- 다음 작업 순서를 정리했습니다: `VisDrone`을 첫 baseline dataset으로 잡고, `YOLO baseline` 학습/평가 구조를 준비한 뒤 `AI-TOD`, `SeaDronesSee`, `Isaac Sim synthetic data`로 확장합니다.
- 채팅에서 논의한 내용은 자동으로 Notion에 저장되지 않으므로, 중요한 결정은 `docs/` Markdown 문서에 기록한 뒤 GitHub에 push하는 방식으로 관리하기로 했습니다.
- 2026-07-05 ACCV 요약 제출을 목표로 `docs/timeline_to_accv.md`에 2026-05-01부터 2026-07-05까지의 주차별 일정을 정리했습니다.
- `VisDrone` baseline 준비를 위해 `data/README.md`, `config/datasets/visdrone.yaml`, `scripts/prepare_visdrone.py`를 추가했습니다.
- 프로젝트 스펙을 `CoM3D-ACE`로 갱신하고, scenario schema, MarineCity converter, depth lifting, evidence graph, ambiguity prompt, experiment runner skeleton을 추가했습니다.
- `generate_scenarios.py`를 ambiguity-centric controlled scenario generator로 확장했습니다. `van_vs_ambulance`, `sedan_vs_pickup`, `truck_vs_rescue_vehicle`, `pedestrian_vs_worker`, `small_boat_vs_debris` hard case를 생성합니다.
- `datasets/marinecity/annotation_schema.json`을 추가하고 `marinecity_to_coco.py`에 standard-library 기반 validation과 `--validate-only` 옵션을 추가했습니다.
- scenario generation, MarineCity conversion, depth lifting, dummy experiment metrics를 검증하는 `unittest` 기반 최소 테스트를 추가했습니다.

## 2026-05-07

- 오늘부터의 작업은 이전 scaffold 기록과 분리해서 이 섹션에 누적하기로 했습니다.
- 현재까지의 기록은 `docs/dev_log.md`와 `notion_exports/환경_및_구현_과정_Development_Log.md`에 Notion 붙여넣기용으로 저장되어 있습니다.
- 다음 작업 후보는 `MarineCity annotation → COCO/evidence → 3D lifting placeholder → evidence graph`를 하나의 pipeline script로 연결하는 것입니다.
- `pipelines/run_dummy_evidence_pipeline.py`를 추가해 dummy MarineCity annotation에서 COCO/evidence, synthetic 3D lifting, evidence graph, summary JSON을 한 번에 생성하도록 연결했습니다.
- Notion 보드 구조에 맞춰 `method_pipeline_card.md`, `may_2026_dev_log.md`, `experiment_result_template_card.md`를 추가했습니다.
- Survey 이후 최종 시스템 수정에 대비해 `final_system_figure_template.md`, `module_figures_formulas_template.md`, `experiment_design_matrix.md`, `implementation_process_template.md`를 추가했습니다.
