# Proposed Model: Perception & Prediction

작성일: 2026-05-13

## 1. 역할

본 모듈은 ACCV 멀티드론 논문의 Contribution 1에 해당함.

기존 YOLOv8n, YOLOv11n, RT-DETR-R18 등 SOTA detector baseline 학습이 끝난 뒤, YOLO11n 계열을 기반으로 small-object perception 성능을 개선하는 제안 모델로 설계함.

핵심 목표는 아래와 같음.

```text
고고도 관측에서 작은 목표 후보를 탐지하고,
짧은 시간 동안 안정적으로 추적·예측하는 perception module 구성
```

즉, 최종 시스템에서 이 모듈은 다음 역할을 담당함.

- 작은 객체 후보를 놓치지 않도록 recall을 높임
- 고도와 angle 변화로 인한 해상도 저하를 보완함
- 짧은 시간 동안 object candidate를 안정적으로 유지함
- 이후 EvidenceToken, 3D reconstruction, ambiguity reasoning으로 넘길 입력을 생성함

---

## 2. 제안 모델 이름 후보

임시 이름:

```text
PP-YOLO11n
```

또는 논문식 이름:

```text
ACE-Perception
```

전체 시스템 이름과 맞추면:

```text
CoM3D-ACE Perception Module
```

추천 표현:

```text
CoM3D-ACE-P: Perception and Prediction Module
```

---

## 3. 전체 구조

제안 모델은 YOLO11n을 기반 detector로 사용하고, small-object perception을 위해 3개 구성요소를 추가함.

```text
Input UAV image
    ↓
Patch / Tiling Inference
    ↓
YOLO11n Backbone
    ↓
Wavelet Stem
    ↓
Partial Deformable Neck
    ↓
Small-object Detection Head
    ↓
Evidence Candidate Queue
    ↓
Short-term Prediction
```

보고용 간단 그림에서는 아래처럼 표현함.

```text
High-altitude UAV Image
        ↓
[1] Patch / Tiling Inference
        ↓
[2] YOLO11n-based Small-object Perception FM
        ↓
[3] Wavelet Stem + Partial Deformable Neck
        ↓
Small Target Candidates
        ↓
Short-term Tracking / Prediction
```

---

## 4. 구성요소 1: YOLO11n 기반 Small-object Perception FM

### 목적

YOLO11n을 lightweight detector backbone으로 사용하되, 고고도 UAV small object에 맞게 feature map을 보강함.

### 핵심 아이디어

- YOLO11n의 빠른 추론 속도를 유지함
- 작은 객체를 위한 high-resolution feature를 강화함
- P2 또는 shallow feature를 활용하는 small-object branch를 추가 가능함
- detector output을 EvidenceToken으로 변환할 수 있게 설계함

### 기대 효과

- 작은 객체 recall 개선
- VisDrone / UAVDT에서 APsmall 개선
- 이후 3D evidence graph로 넘길 후보 품질 개선

---

## 5. 구성요소 2: Wavelet Stem / Partial Deformable Neck

### 5.1 Wavelet Stem

목적:

- 작은 객체의 edge, texture, local contrast 정보를 보존함
- 고도 상승으로 인해 흐려지는 fine detail을 frequency 관점에서 보완함

아이디어:

```text
Input image
   ↓
Wavelet decomposition
   ├─ low-frequency component
   └─ high-frequency component
   ↓
Feature fusion
   ↓
YOLO backbone input feature
```

기대 효과:

- 작은 차량, 보행자, 오토바이, 선박 후보의 local boundary 강화
- dense scene에서 인접 객체 분리 가능성 향상

### 5.2 Partial Deformable Neck

목적:

- UAV angle 변화, perspective distortion, 객체 형태 왜곡에 대응함
- 모든 feature에 deformable convolution을 적용하지 않고 일부 neck stage에만 적용하여 속도 저하를 줄임

아이디어:

```text
YOLO neck feature
   ↓
Partial deformable convolution
   ↓
Geometry-adaptive feature alignment
   ↓
Detection head
```

기대 효과:

- oblique view에서 객체 box alignment 개선
- 작은 객체 위치 오차 감소
- FPS 손실을 제한하면서 성능 개선

---

## 6. 구성요소 3: Patch / Tiling Inference

### 목적

고고도 UAV image에서 작은 객체가 전체 이미지 기준으로 너무 작게 나타나는 문제를 보완함.

### 핵심 아이디어

전체 이미지를 한 번에 넣는 baseline과 달리, image를 overlapping tile로 나누어 작은 객체를 더 크게 보이도록 함.

```text
Full UAV image
   ↓
Overlapping tiles
   ↓
Detector inference per tile
   ↓
Tile-level bbox merge
   ↓
Final detections
```

### 설계 옵션

- fixed-size tiling
- overlap ratio 조절
- scale-aware tiling
- density-aware tiling, 가능 시
- tile 결과에 대해 NMS / Weighted Box Fusion 적용

### 기대 효과

- 작은 객체 recall 증가
- 원거리 객체 누락 감소
- dense region에서 detection sensitivity 증가

---

## 7. Short-term Tracking / Prediction

### 목적

짧은 시간 동안 detection이 불안정하게 깜빡이는 문제를 줄임.

### 초기 구현 방향

처음부터 복잡한 tracker를 넣지 않고, lightweight temporal smoothing부터 시작함.

후보:

- IoU-based short-term association
- confidence smoothing
- Kalman filter
- velocity-based short-term prediction

출력:

```text
TrackedCandidate =
  object_candidate_id
  bbox_t
  predicted_bbox_t+1
  class_score
  confidence
  uncertainty
  track_age
```

기대 효과:

- 순간적인 false negative 감소
- 짧은 구간에서 안정적인 object candidate 유지
- multi-UAV / 3D stage에서 같은 객체 후보를 연결하기 쉬워짐

---

## 8. 최종 출력

제안 Perception & Prediction module의 최종 출력은 단순 bbox가 아니라 EvidenceToken 후보 집합으로 둠.

```text
EvidenceCandidate =
  bbox_2d
  class logits
  confidence
  uncertainty
  crop feature
  tile id
  frame id
  short-term track id
  predicted bbox
```

이 출력은 이후 단계로 연결됨.

```text
Perception & Prediction
    ↓
EvidenceToken
    ↓
Multi-angle / 3D Reconstruction
    ↓
Ambiguity Reasoning
    ↓
Re-observation / Evidence Completion
```

---

## 9. 비교 실험 설계

### Experiment 1. Detector baseline comparison

목적:

- 기존 detector baseline 대비 제안 perception module 성능을 비교함.

비교 모델:

| Method | 설명 |
| --- | --- |
| YOLOv8n | baseline |
| YOLOv11n | baseline |
| YOLOv11s | stronger YOLO baseline |
| RT-DETR-R18 | transformer detector baseline |
| D-FINE-S | optional baseline |
| Ours | YOLO11n + proposed modules |

지표:

- AP
- AP50
- AP75
- APsmall
- Recall
- Precision
- FPS
- Params

---

### Experiment 2. Module ablation

목적:

- 제안 구성요소가 각각 성능에 기여하는지 확인함.

비교:

| Method | Wavelet Stem | Partial Deformable Neck | Patch / Tiling | Short-term Prediction |
| --- | --- | --- | --- | --- |
| YOLO11n baseline | - | - | - | - |
| + Wavelet Stem | O | - | - | - |
| + Partial Deformable Neck | - | O | - | - |
| + Patch / Tiling | - | - | O | - |
| + Wavelet + Deformable | O | O | - | - |
| + Wavelet + Deformable + Tiling | O | O | O | - |
| Full Ours | O | O | O | O |

주요 확인 포인트:

- Wavelet Stem이 APsmall에 기여하는지 확인함
- Partial Deformable Neck이 oblique view와 perspective distortion에 기여하는지 확인함
- Patch / Tiling inference가 recall을 개선하는지 확인함
- Short-term Prediction이 temporal stability를 개선하는지 확인함

---

### Experiment 3. Recall and stability evaluation

목적:

- 단순 AP뿐 아니라 작은 목표 후보 유지 능력을 평가함.

지표:

| 지표 | 의미 |
| --- | --- |
| Small-object recall | 작은 객체를 놓치지 않는 정도 |
| False negative rate | 누락 비율 |
| Detection flicker rate | 짧은 시간 동안 detection이 사라지는 비율 |
| Track continuity | 짧은 구간에서 후보가 유지되는 정도 |
| Prediction IoU | 예측 bbox와 다음 frame bbox의 IoU |

---

## 10. 논문 그림 수정안

### Figure: Perception & Prediction Module

그림에 들어갈 텍스트:

```text
Perception & Prediction

Goal:
고고도 관측에서 작은 목표 후보를 탐지하고,
짧은 시간 동안 안정적으로 추적·예측

1. YOLO11n-based small-object perception FM
2. Wavelet stem / partial deformable neck
3. Patch / tiling inference for small-object recall
4. Short-term candidate tracking / prediction
```

시스템 그림 내 위치:

```text
Multi-angle UAV Images
        ↓
[Perception & Prediction]
        ↓
EvidenceToken Candidates
        ↓
3D Generative Reconstruction
        ↓
Object-aware Evidence Completion
```

---

## 11. 구현 순서

비교 모델 학습이 끝난 뒤 아래 순서로 구현함.

1. YOLO11n baseline 결과 고정
2. Patch / tiling inference 먼저 구현
3. Wavelet stem module 추가
4. Partial deformable neck 추가
5. Short-term prediction module 추가
6. Ablation table 생성
7. FPS / Params / latency 측정
8. 최종 detector comparison table 작성

초기 구현 우선순위:

```text
1순위: Patch / tiling inference
2순위: Wavelet stem
3순위: Partial deformable neck
4순위: Short-term prediction
```

이유:

- Patch / tiling은 기존 학습 weight로도 바로 inference 비교 가능함
- Wavelet stem은 학습 구조 수정이 필요하지만 구현 난이도가 비교적 명확함
- Partial deformable neck은 모델 구조 수정과 속도 측정이 필요함
- Short-term prediction은 video dataset 또는 sequential frame 평가가 필요함

---

## 12. 한 줄 정리

제안 Perception & Prediction module은 아래처럼 정의함.

```text
YOLO11n 기반 small-object detector에
Wavelet Stem, Partial Deformable Neck, Patch/Tiling Inference,
Short-term Prediction을 결합하여
고고도 UAV 영상에서 작은 목표 후보의 recall과 안정성을 개선하는 모듈임.
```
