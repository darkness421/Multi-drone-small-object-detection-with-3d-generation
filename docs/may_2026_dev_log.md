# 5월 개발 로그

## 2026-05-07

### 저장 확인

- 이전 작업은 `docs/dev_log.md`와 `notion_exports/환경_및_구현_과정_Development_Log.md`에 저장되어 있습니다.
- 오늘부터의 작업은 `2026-05-07` 섹션에 분리해서 기록하기 시작했습니다.

### 완료한 작업

- `generate_scenarios.py`를 ambiguity-centric controlled scenario generator로 확장했습니다.
- `datasets/marinecity/annotation_schema.json`을 추가했습니다.
- `marinecity_to_coco.py`에 validation과 `--validate-only` 옵션을 추가했습니다.
- core scaffold 검증용 `unittest` 테스트를 추가했습니다.
- `pipelines/run_dummy_evidence_pipeline.py`를 추가했습니다.

### 오늘 기준 핵심 산출물

- controlled scenario sample: `sim/scenarios/sample_scenarios.json`
- annotation schema: `datasets/marinecity/annotation_schema.json`
- dummy pipeline: `pipelines/run_dummy_evidence_pipeline.py`
- pipeline test: `tests/test_dummy_pipeline.py`

### 다음 작업 후보

- evidence graph 시각화/summary 생성
- camera pose 기반 실제 extrinsics 연결
- ambiguity diagnosis prompt 입력 JSON 생성

