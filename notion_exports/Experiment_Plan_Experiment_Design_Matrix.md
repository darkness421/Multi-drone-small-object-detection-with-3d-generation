# Experiment Design Matrix

- Notion Section: `Experiment Plan`
- Status: `Not Started`
- Source: `docs/experiment_design_matrix.md`
- Export Date: `2026-05-07`

---

# Experiment Design Matrix

## 목적

서베이 후 최종 제안 시스템이 확정되면 바로 실험 계획을 정리하기 위한 카드입니다.  
이 카드는 Notion의 `03 Experiment Plan` 열에 넣습니다.

## 실험에서 보여줘야 할 것

| 질문 | 실험 |
| --- | --- |
| Multi-UAV가 Single-UAV보다 좋은가? | Exp1. Single-UAV vs Multi-UAV |
| 3D evidence graph가 단순 2D fusion보다 좋은가? | Exp2. 2D Fusion vs 3D Evidence Graph |
| Ambiguity diagnosis가 hard case를 잘 찾는가? | Exp3. Ambiguity Diagnosis |
| Recommended next view가 실제로 성능을 올리는가? | Exp4. Active Re-Observation |
| Failure-conditioned scenario가 random synthetic보다 좋은가? | Exp5. Failure-Conditioned Scenario Generation |

## Experiment Matrix

| Exp | 목적 | Dataset | Baseline | Proposed | Metrics | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Exp1 | Multi-UAV 효과 | CoM3D-MarineCity | Single-UAV YOLO | Multi-UAV detection | mAP, AP_small, FGA | Planned |
| Exp2 | 3D graph 효과 | CoM3D-MarineCity | 2D voting / NMS | 3D Evidence Graph | FGA, consistency, graph purity | Planned |
| Exp3 | ambiguity 진단 | hard cases | confidence threshold | Ambiguity Diagnosis | ambiguity accuracy, missing evidence recall | Planned |
| Exp4 | next view 효과 | ambiguous objects | fixed view | recommended next view | Δconfidence, ΔFGA, success rate | Planned |
| Exp5 | scenario generation 효과 | synthetic data | random scenario | failure-conditioned scenario | hard-case coverage, AP_hard | Planned |

## Dataset 후보

| Dataset | 역할 | 우선순위 |
| --- | --- | --- |
| CoM3D-MarineCity | 핵심 synthetic dataset | 1 |
| VisDrone-DET | real UAV detector pretraining | 2 |
| AI-TOD / AI-TOD-v2 | tiny object stress test | 3 |
| UAVDT | vehicle/temporal evidence | 4 |
| FAIR1M | fine-grained remote sensing pretraining | 5 |

## Metrics 후보

### Detection

- `mAP`
- `AP_small`
- `precision`
- `recall`
- `FPS`

### Fine-Grained

- `fine-grained accuracy`
- `class confusion reduction`
- `hard-case accuracy`

### Evidence Graph

- `graph purity`
- `multi-view consistency`
- `3D center error`
- `token completeness`

### Ambiguity / Re-observation

- `ambiguity diagnosis accuracy`
- `missing evidence recall`
- `recommended view success rate`
- `confidence gain`
- `evidence completion success`

## 나중에 채울 TODO

- [ ] 최종 contribution에 맞춰 Exp 수 줄이기
- [ ] baseline 2~3개 확정
- [ ] dataset license 확인
- [ ] 실험별 output path 정리
- [ ] 결과표 template 생성
