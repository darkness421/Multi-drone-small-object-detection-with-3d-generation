# 최종 제안 시스템 그림 수정 템플릿

- Notion Section: `Proposed Method`
- Status: `Not Started`
- Source: `docs/final_system_figure_template.md`
- Export Date: `2026-05-07`

---

# 최종 제안 시스템 그림 수정 템플릿

## 목적

Survey가 끝난 뒤 최종 제안 시스템 그림을 다시 그릴 때 사용할 정리 카드입니다.  
이 카드는 Notion의 `Proposed Method` 열에 넣습니다.

## 최종 시스템 그림 후보 제목

```text
CoM3D-ACE Overall Architecture
```

또는 방향이 바뀌면:

```text
Cooperative Multi-UAV 3D Evidence Reasoning Framework
Ambiguity-Aware Multi-UAV Object Detection System
Digital Twin Guided Multi-UAV Evidence Completion
```

## 그림에 들어갈 핵심 흐름

```text
MarineCity Digital Twin
→ Controlled Multi-UAV Scenario
→ RGB / Depth / Pose Capture
→ Per-UAV 2D Detector
→ 2D-to-3D Lifting
→ Object Evidence Graph
→ Ambiguity Diagnosis
→ Evidence Completion / Next View
→ Fine-Grained Decision
```

## 그림 수정 시 결정해야 할 것

| 결정 항목 | 후보 | 선택 |
| --- | --- | --- |
| 핵심 contribution | detection / evidence graph / re-observation / scenario generation | TBD |
| VLM/LLM 위치 | ambiguity diagnosis / explanation / policy selection | TBD |
| Isaac Sim 역할 | dataset generation / demo / controlled hard case generation | TBD |
| Cesium 역할 | geospatial background / urban digital twin / camera pose context | TBD |
| 최종 출력 | class / 3D location / confidence / explanation / next view | TBD |

## Figure Panel 구성안

### Panel A. Digital Twin + Multi-UAV Observation

- Marine City digital twin
- UAV 1, UAV 2, UAV 3
- 각 UAV camera view
- RGB/depth/pose 동기화

### Panel B. 2D Detection to 3D Evidence

- Per-view bbox
- depth 기반 3D lifting
- object hypothesis
- multi-view association

### Panel C. 3D Object Evidence Graph

- object node
- view evidence
- class logits
- occlusion/context/uncertainty
- missing evidence

### Panel D. Ambiguity-Centric Decision

- ambiguity type
- recommended next view
- final fine-grained class
- explanation

## 최종 그림에 반드시 들어갈 키워드

- `Multi-UAV`
- `Urban Digital Twin`
- `2D-to-3D Lifting`
- `3D Object Evidence Graph`
- `Ambiguity Diagnosis`
- `Evidence Completion`
- `Recommended Next View`

## 나중에 채울 TODO

- [ ] Survey 결과 기반으로 핵심 contribution 1개를 확정
- [ ] 전체 pipeline block 순서 확정
- [ ] VLM/LLM 사용 위치 확정
- [ ] Method figure rough sketch 생성
- [ ] Figure caption 초안 작성
- [ ] Notion에 최종 그림 버전 붙여넣기
