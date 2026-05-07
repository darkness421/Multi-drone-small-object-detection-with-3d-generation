# Idea Bank

- Notion Section: `Proposed Method`
- Status: `Not Started`
- Source: `docs/idea_bank.md`
- Export Date: `2026-05-07`

---

# 아이디어 뱅크

아직 바로 구현 task로 만들기 전의 아이디어를 기록하는 문서입니다.

## Detection

- 각 UAV 카메라에서 object proposal을 만들기 위한 lightweight `YOLO` baseline을 사용합니다.
- small object 표현을 보존하기 위해 patch-level feature를 추가합니다.
- tiny target 표현력을 높이기 위해 wavelet stem 또는 multi-frequency branch를 검토합니다.

## Multi-UAV Fusion

- timestamp, camera pose, object class, projected 3D consistency를 이용해 여러 UAV view의 detection을 매칭합니다.
- 최종 confidence scoring 전에 여러 UAV의 object evidence를 fusion합니다.
- UAV 간 confidence disagreement가 크면 re-observation trigger로 사용합니다.

## Isaac Sim 데모

- Marine City scene에 UAV camera viewpoint 3개를 배치합니다.
- 각 UAV camera stream에 detection box를 표시합니다.
- fusion된 object position을 top-down 3D marker로 표시합니다.
- object evidence가 불확실하면 re-observation request를 표시합니다.

## Reasoning

- 여러 UAV의 evidence를 요약하기 위해 structured prompt를 사용합니다.
- geometric verification과 language-model explanation은 분리합니다.
- 최종 판단은 class, confidence, 3D position, supporting UAVs, next action까지 추적 가능해야 합니다.
