# CoM3D-ACE

**CoM3D-ACE: Ambiguity-Centric 3D Evidence Completion for Cooperative Multi-UAV Fine-Grained Object Detection in Urban Digital Twins**

CoM3D-ACE는 부산 해운대 마린시티 digital twin 환경에서 여러 UAV가 동일 지역을 다중 시점으로 관측하고, 각 UAV의 2D detection 결과를 3D object evidence graph로 통합한 뒤, 모호한 객체에 대해서만 추가 관측 또는 실패 조건 기반 scenario generation을 수행하는 fine-grained UAV object detection 연구 프로젝트입니다.

## 연구 목표

- `NVIDIA Isaac Sim` + `Cesium for Omniverse` 기반 Marine City digital twin 구축
- synchronized Multi-UAV observation dataset인 `CoM3D-MarineCity` 생성
- UAV별 2D detection을 depth/pose 기반 3D hypothesis로 lifting
- multi-view crop, geometry, context, uncertainty를 3D object evidence graph로 통합
- ambiguity type과 missing evidence를 진단하고 recommended next view를 출력
- 최종적으로 fine-grained class, 3D location, confidence, explanation을 제공

## 핵심 문제

| 문제 | 설명 |
| --- | --- |
| Tiny object scale | 고도 100-200m에서 차량, 사람, 선박이 매우 작게 보임 |
| Fine-grained ambiguity | van/ambulance, sedan/pickup, truck/rescue vehicle 구분이 어려움 |
| Urban occlusion | 고층 건물, 그림자, 도로 구조로 객체 일부가 가려짐 |
| Viewpoint dependency | side-view 또는 oblique-view가 있어야 구분 가능한 객체가 있음 |
| Multi-UAV annotation 부족 | synchronized multi-UAV + 3D annotation 데이터가 부족함 |
| Random synthetic data 한계 | 무작위 simulation은 hard case를 충분히 만들지 못함 |

## 전체 Pipeline

```text
Busan Haeundae Marine City Digital Twin
        ↓
Multi-UAV Scenario Generation
        ↓
UAV Sensor Simulation
        ↓
Onboard Edge Detection
        ↓
2D-to-3D Object Lifting
        ↓
3D Object Evidence Graph
        ↓
Ambiguity Diagnosis
        ↓
Evidence Completion Policy
        ↓
Fine-Grained Object Decision
```

## 1차 산출물

- MarineCity digital twin screenshot
- Multi-UAV synchronized observation example
- 3D object evidence graph example
- ambiguous object → recommended next view example

## Repository Structure

```text
configs/              Isaac, detector, experiment config
sim/                  Isaac/Cesium/scenario generation
datasets/             Dataset converters, schemas, splits
detectors/            YOLO/RT-DETR training and inference skeleton
lifting3d/            2D bbox + depth + pose → 3D hypothesis
evidence_graph/       JSON-based 3D object evidence graph
reasoning/            Ambiguity diagnosis prompts and policies
experiments/          Dummy experiment runners and evaluation
notebooks/            Inspection and visualization notebooks
paper/                Figures, tables, draft notes
docs/                 Planning notes and timeline
notion_exports/       Notion에 붙여넣기 좋은 Markdown export
```

## 현재 상태

- GitHub remote: https://github.com/darkness421/multi-uav-marine-city
- 첫 baseline dataset 후보: `CoM3D-MarineCity`, `VisDrone-DET`, `AI-TOD`, `UAVDT`, `FAIR1M`
- 첫 구현 목표: scenario schema, annotation converter, 2D-to-3D lifting, evidence graph, dummy experiment runner

## Quick Checks

```powershell
python -m unittest discover tests
python sim\scenarios\generate_scenarios.py --count 20
python datasets\converters\marinecity_to_coco.py --input datasets\converters\dummy_marinecity_input.json --validate-only
python experiments\run_exp01_single_uav.py --dummy
```
