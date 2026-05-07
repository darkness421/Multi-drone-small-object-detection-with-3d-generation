# Experiment Results

- Notion Section: `Experiment Result`
- Status: `Not Started`
- Source: `docs/experiment_results.md`
- Export Date: `2026-05-07`

---

# 실험 결과

이 문서는 Notion의 `04 Experiment Result` 열과 연결할 실험 결과 기록용 문서입니다.

## 기록 원칙

- 실험 하나당 하나의 항목으로 기록합니다.
- Dataset, model, config, metric, output path를 함께 남깁니다.
- 성공한 결과뿐 아니라 실패한 결과도 기록합니다.
- 결과 해석에는 왜 성능이 좋아졌거나 나빠졌는지에 대한 가설을 함께 남깁니다.

## 실험 결과 템플릿

### EXP-YYYYMMDD-001: 실험 제목

| 항목 | 내용 |
| --- | --- |
| 상태 | Planned / Running / Completed / Failed |
| 목적 | 이 실험으로 확인하려는 것 |
| Dataset | VisDrone / AI-TOD / SeaDronesSee / Isaac Sim synthetic data |
| Model | YOLO baseline / patch-wavelet model / fusion model |
| Config | 사용한 config 파일 또는 주요 hyperparameter |
| Metric | mAP, AP_small, precision, recall, FPS 등 |
| Output | `outputs/...` |
| Git Commit | 실험 당시 commit hash |
| Notion Card | 연결된 Notion item 이름 |

#### 결과

- 주요 수치:
- 시각화 결과:
- 실패/오류:

#### 해석

- 관찰:
- 원인 가설:
- 다음 실험:

## 결과 요약표

| ID | 날짜 | Dataset | Model | 핵심 Metric | 상태 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD | Planned | 첫 실험 전 |
