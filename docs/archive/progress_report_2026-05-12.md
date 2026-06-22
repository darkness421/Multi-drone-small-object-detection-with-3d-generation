# CoM3D-ACE 진행 보고 요약

보고일: 2026-05-12

## 1. 현재 목표

본 연구는 Cooperative Multi-UAV Small Object Detection을 목표로 하며, 최종적으로는 다중 UAV 관측 결과를 EvidenceToken, cross-view alignment, 3D evidence graph, ambiguity diagnosis, re-observation policy, selective VLM verification으로 연결하는 CoM3D-ACE 시스템을 구현하는 방향으로 진행 중이다.

현재 단계는 최종 시스템 구현 전, public UAV dataset 기반의 front-end detector baseline을 확보하는 단계이다.

## 2. 현재까지 완료한 작업

### Repository 및 실행 환경

- Windows 기준 CoM3D-ACE repo 구조를 정리했다.
- Python 3.10 기반 `com3d-ace` conda environment를 구성했다.
- PyTorch, CUDA, Ultralytics, OpenCV, NumPy 등 학습 환경을 확인했다.
- GPU는 NVIDIA GeForce RTX 4080 환경에서 사용 가능하다.

### Dataset 준비

- VisDrone2019-DET train / val / test-dev dataset을 다운로드하고 압축 해제했다.
- VisDrone annotation을 COCO 형식으로 변환했다.
- COCO 형식을 YOLO 학습 형식으로 변환했다.
- 학습 readiness check를 통과했다.

Dataset 구성:

| Split | Images | Labels |
| --- | ---: | ---: |
| Train | 6,471 | 6,471 |
| Val | 548 | 548 |
| Test-dev | 1,610 | 1,610 |

### Dataset Preview

변환된 YOLO dataset의 bbox가 정상적으로 표시되는지 HTML preview를 생성했다.

- Preview: `file:///C:/Users/jc/multi-uav-marine-city/outputs/preview/yolo_dataset/index.html`
- Preview sample: 60 images
- Preview boxes: 5,810 boxes

## 3. 현재 학습 진행 상황

현재 학습 중인 모델은 기본 Ultralytics YOLOv11n baseline이다.

| 항목 | 내용 |
| --- | --- |
| Model | YOLOv11n |
| Weight | `yolo11n.pt` |
| Dataset | VisDrone2019-DET |
| Epochs | 100 |
| Image size | 1280 |
| Batch size | 8 |
| Run ID | `20260512_123448_yolo11n_VisDrone2019-DET` |

현재 중간 결과:

| Metric | Value |
| --- | ---: |
| Current epoch | 69 / 100 |
| Precision | 0.57093 |
| Recall | 0.47109 |
| mAP50 | 0.47365 |
| mAP50-95 | 0.28771 |
| Train box loss | 1.26535 |
| Val box loss | 1.28192 |

주의: 위 수치는 학습이 완료되기 전 중간 결과이며, 최종 결과는 100 epoch 완료 후 `best.pt` 기준으로 다시 평가할 예정이다.

학습 결과 저장 위치:

- `outputs/detectors/20260512_123453_yolo11n_visdrone/ultralytics/`
- `outputs/detectors/20260512_123453_yolo11n_visdrone/ultralytics/results.csv`
- `outputs/detectors/20260512_123453_yolo11n_visdrone/ultralytics/weights/best.pt`
- `outputs/detectors/20260512_123453_yolo11n_visdrone/ultralytics/weights/last.pt`

실험 기록 저장 위치:

- `outputs/experiments/20260512_123448_yolo11n_VisDrone2019-DET/manifest.json`
- `outputs/experiments/20260512_123448_yolo11n_VisDrone2019-DET/experiment.md`
- `outputs/experiments/training_experiment_index.csv`

## 4. 이번 단계의 의미

현재 YOLOv11n 학습은 최종 제안 방법 자체가 아니라, CoM3D-ACE 시스템의 front-end detector baseline이다. 이후 이 detector의 출력 bbox, class confidence, crop 등을 EvidenceToken으로 변환하여 multi-view graph와 ambiguity reasoning의 입력으로 사용할 예정이다.

즉 현재 단계의 목적은 다음과 같다.

- VisDrone에서 small object detector baseline 확보
- 이후 EvidenceToken 생성 pipeline의 detector 입력 확보
- YOLO 계열 baseline 결과표의 첫 번째 기준선 확보

## 5. 앞으로 해야 할 작업

### Short-term

1. YOLOv11n 학습 완료 후 final validation 결과 정리
2. YOLOv8n 학습 진행
3. YOLOv11s 또는 YOLOv8s 학습 진행
4. RT-DETR-R18 baseline 학습 준비
5. 학습 결과를 detector comparison table로 정리

### Mid-term

1. YOLO inference 결과를 EvidenceToken JSONL로 변환
2. EvidenceToken preview 생성
3. cross-view / cross-resolution alignment module 테스트
4. 3D evidence graph prototype과 연결
5. ambiguity score 계산 및 hard-case detection 평가 준비

### System-level

1. Isaac Sim에서 CoM3D-Sim synthetic multi-UAV dataset export 준비
2. 작은 block scene 3개부터 구성
   - sparse vehicles
   - dense vehicles + pedestrians
   - occlusion / side-view ambiguity
3. RGB, depth, camera pose, UAV pose, bbox, object ID, visibility를 저장
4. multi-view association, 2D-to-3D lifting, re-observation simulation으로 확장

## 6. 예정 비교 실험

Detector-level baseline:

- YOLOv8n
- YOLOv11n
- YOLOv11s 또는 YOLOv8s
- YOLOv8n+P2
- RT-DETR-R18
- D-FINE-S, 가능 시
- Ours AEG

System-level baseline:

- Single-view detector
- Multi-view average pooling
- Naive 3D fusion
- Graph-only
- Graph + alignment
- Graph + ambiguity diagnosis
- Graph + uncertainty re-observation
- Full CoM3D-ACE

## 7. 다음 보고 전 목표

- YOLOv11n 최종 학습 결과 확보
- YOLOv8n baseline 추가 학습
- detector result table 초안 작성
- EvidenceToken generation pipeline에 YOLO output 연결
- Isaac Sim dataset export 계획 구체화
