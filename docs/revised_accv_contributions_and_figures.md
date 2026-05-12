# ACCV 멀티드론 논문 수정 방향 정리

작성일: 2026-05-12

## 1. 수정된 논문 방향

기존 방향은 cooperative multi-UAV small object detection pipeline 중심이었음.  
수정 방향은 아래 3개 contribution을 중심으로 재구성함.

1. SOTA detector 기반 small object detection 성능 개선 모듈 제안
2. Multi-angle UAV image 기반 3D 생성형 재구성 모델 제안 및 비교
3. MarineCity 특정 환경에서 multi-angle / 3D reconstruction benchmark dataset 생성

즉, 논문은 단순히 detector 하나를 제안하는 것이 아니라,  
`2D detection improvement + 3D generative reconstruction + benchmark dataset`을 함께 제안하는 형태로 구성함.

---

## 2. Contribution 1: SOTA Detector + 2개 모듈

### 목표

VisDrone, UAVDT 등 public UAV dataset에서 기존 SOTA detector를 기반으로 small object detection 성능을 개선함.

### 기본 방향

YOLOv11, YOLOv8, RT-DETR, D-FINE 등 detector를 baseline으로 두고, 여기에 UAV small object detection에 특화된 plug-in module 2개를 추가함.

### 제안 모듈 후보

#### Module A. Tiny Evidence Enhancement Module

역할:

- 고고도 UAV 영상에서 작은 객체의 local detail을 보존함
- P2 / high-resolution feature를 활용함
- patch-level feature 또는 wavelet / frequency 정보를 활용 가능함
- small object의 edge, texture, local contrast를 강화함

그림 표현:

```text
Input UAV image
   ↓
Backbone / Neck
   ↓
Tiny Evidence Enhancement Module
   ↓
Enhanced small-object feature
```

실험:

- Baseline detector
- Baseline + Module A
- Baseline + Module B
- Baseline + Module A + Module B

평가:

- AP
- AP50
- APsmall
- Recall
- FPS
- Params

#### Module B. Ambiguity-aware Evidence Token Module

역할:

- detector output을 단순 bbox가 아니라 evidence token 형태로 변환함
- confidence, class entropy, resolution level, crop feature를 함께 저장함
- ambiguous object를 이후 3D reconstruction / multi-view reasoning으로 넘길 수 있게 함

Evidence token 예시:

```text
EvidenceToken =
  bbox
  class logits
  confidence
  uncertainty
  crop feature
  resolution score
  image id
  view id
```

그림 표현:

```text
Detector output
   ↓
Ambiguity-aware Evidence Token Module
   ↓
EvidenceToken set
   ↓
3D / multi-view stage
```

핵심 주장:

- Module A는 intra-image small object feature를 강화함
- Module B는 detection result를 multi-view / 3D reasoning으로 연결함
- 두 모듈을 통해 detector 성능과 downstream 3D reasoning 입력 품질을 동시에 개선함

---

## 3. Contribution 2: 3D 생성형 모델 제안 및 비교 실험

### 목표

다양한 UAV angle image를 활용하여 특정 도시 환경을 3D로 재구성하고, 재구성된 3D representation이 small object detection 및 ambiguous object reasoning에 도움이 되는지 검증함.

### 비교 대상 모델

비교군:

- NeRF
- instant-ngp
- 3D Gaussian Splatting
- 제안 모델

### 제안 모델 방향

임시 이름:

```text
CoM3D-Gen
```

또는:

```text
MarineCity-ACE-3DGS
```

기본 아이디어:

- Multi-UAV / multi-angle image를 입력으로 사용함
- Camera pose를 함께 사용함
- 3D scene representation을 생성함
- 객체 detection evidence를 3D representation에 결합함
- ambiguous object에 대해 novel view 또는 reconstructed view evidence를 제공함

일반 3D reconstruction과의 차별점:

| 기존 3D 생성형 모델 | 제안 방향 |
| --- | --- |
| scene appearance reconstruction 중심 | object evidence-aware reconstruction 중심 |
| 이미지 품질 중심 평가 | detection / ambiguity resolution 성능까지 평가 |
| 전체 장면 재구성 중심 | small object와 multi-angle evidence를 함께 고려 |

### 그림 표현

```text
Multi-angle UAV images + camera poses
        ↓
3D generative reconstruction model
        ↓
3D scene representation
        ↓
Novel / missing view synthesis
        ↓
Object evidence completion
        ↓
Improved fine-grained detection
```

### 평가 지표

3D reconstruction:

- PSNR
- SSIM
- LPIPS
- Rendering FPS
- Training / reconstruction time

Detection-aware evaluation:

- detection AP on rendered views
- ambiguous object resolution rate
- class correction rate
- multi-view consistency
- 3D object localization error, 가능 시

---

## 4. Contribution 3: MarineCity Multi-Angle Benchmark Dataset

### 목표

해운대 마린시티 특정 환경에서 다양한 angle image와 3D reconstruction 결과를 포함하는 benchmark dataset을 생성함.

### Dataset 이름 후보

```text
MarineCity-MultiUAV
```

또는:

```text
CoM3D-MarineCity Benchmark
```

### Dataset 구성

데이터 구성:

- RGB image
- UAV viewpoint / angle
- Camera intrinsic
- Camera extrinsic
- UAV pose
- 2D bbox
- Object class
- Object ID
- Depth map, 가능 시
- 3D reconstruction result
- Novel view image
- Ambiguity label, 가능 시

### Angle 구성

예시:

- nadir view
- front-oblique view
- side-oblique view
- rear-oblique view
- low-altitude close view
- high-altitude wide view

### Dataset의 역할

이 dataset은 단순 detector 학습용 dataset이 아니라, 아래 실험을 가능하게 하는 benchmark임.

1. multi-angle object detection
2. 3D reconstruction comparison
3. novel view generation
4. ambiguity resolution
5. re-observation policy simulation
6. MarineCity-specific urban digital twin evaluation

---

## 5. 수정된 전체 시스템 그림 구성안

기존 그림은 detection pipeline 중심이었음.  
수정 그림은 3개 contribution이 한눈에 보이도록 구성함.

### Figure 1. Overall Framework

그림 흐름:

```text
MarineCity Multi-UAV Environment
        ↓
Multi-angle UAV Image Collection
        ↓
SOTA Detector + Proposed Modules
        ↓
EvidenceToken Generation
        ↓
3D Generative Reconstruction
        ↓
Object-aware 3D Evidence Completion
        ↓
Final Detection / Ambiguity Resolution
```

그림에서 3개 contribution 표시:

```text
[C1] Detector + 2 Modules
[C2] 3D Generative Reconstruction Model
[C3] MarineCity Multi-angle Benchmark Dataset
```

### Figure 2. Detector Module Figure

목적:

- Contribution 1 설명용
- detector에 어떤 모듈이 붙는지 보여줌

구성:

```text
UAV image
  ↓
SOTA detector backbone
  ↓
Tiny Evidence Enhancement Module
  ↓
Detection head
  ↓
Ambiguity-aware Evidence Token Module
  ↓
Evidence tokens
```

비교 표시:

```text
Baseline
Baseline + Module A
Baseline + Module B
Baseline + Module A + B
```

### Figure 3. 3D Generative Reconstruction Figure

목적:

- Contribution 2 설명용
- NeRF / instant-ngp / 3DGS와 제안 모델 비교 구조를 보여줌

구성:

```text
Multi-angle images + camera poses
      ↓
3D generator
      ↓
3D representation
      ↓
Novel view / missing view synthesis
      ↓
Object evidence completion
```

### Figure 4. Benchmark Dataset Figure

목적:

- Contribution 3 설명용
- MarineCity dataset이 무엇을 포함하는지 보여줌

구성:

```text
MarineCity scene
  ├─ UAV angle A image
  ├─ UAV angle B image
  ├─ UAV angle C image
  ├─ 2D bbox / object ID
  ├─ camera pose
  ├─ depth / 3D reconstruction
  └─ ambiguity / missing-view label
```

---

## 6. 수정된 실험 설계

### Experiment 1. Detector baseline and module ablation

목적:

- SOTA detector에 제안 모듈 2개를 붙였을 때 성능 개선을 보임.

비교:

| Method | 설명 |
| --- | --- |
| YOLOv8n | baseline |
| YOLOv11n | baseline |
| RT-DETR-R18 | transformer detector baseline |
| D-FINE-S | optional baseline |
| Detector + Module A | tiny evidence enhancement |
| Detector + Module B | ambiguity-aware evidence token |
| Detector + Module A + B | full detector-side proposal |

### Experiment 2. 3D generative reconstruction comparison

목적:

- 다양한 angle image를 이용한 3D reconstruction / novel view generation 성능 비교.

비교:

| Method | 설명 |
| --- | --- |
| NeRF | classic neural radiance field |
| instant-ngp | fast NeRF baseline |
| 3D Gaussian Splatting | real-time radiance field rendering baseline |
| Ours | object evidence-aware 3D generative model |

### Experiment 3. Detection-aware 3D evidence completion

목적:

- 단순 3D reconstruction이 아니라, detection 성능과 ambiguity resolution에 실제로 도움이 되는지 검증함.

비교:

| Method | 설명 |
| --- | --- |
| single-view detection | 1개 angle만 사용 |
| multi-view voting | 여러 angle 결과 평균 |
| 3D reconstruction only | 3D 생성 결과만 사용 |
| 3D reconstruction + evidence token | detection evidence 결합 |
| full CoM3D-ACE | detector modules + 3D generation + evidence completion |

### Experiment 4. MarineCity benchmark dataset validation

목적:

- 새 dataset이 다양한 angle, 3D reconstruction, ambiguity case를 포함한다는 것을 보임.

제시할 내용:

- dataset statistics
- angle distribution
- object class distribution
- altitude / distance distribution
- example images
- 3D reconstruction examples
- ambiguous object examples

---

## 7. 논문 Contribution 문장 초안

논문 introduction 마지막에 들어갈 수 있는 형태:

```text
Our contributions are threefold.

First, we propose two plug-in modules for SOTA UAV small-object detectors:
a tiny evidence enhancement module and an ambiguity-aware evidence token module.
These modules improve intra-image small-object representation and provide structured evidence for downstream multi-view reasoning.

Second, we propose an object evidence-aware 3D generative reconstruction framework
that leverages multi-angle UAV images to synthesize missing views and support ambiguity resolution.
We compare the proposed framework with NeRF, instant-ngp, and 3D Gaussian Splatting.

Third, we construct a MarineCity multi-angle UAV benchmark dataset
containing diverse viewpoint images, camera poses, object annotations, and 3D reconstruction outputs.
The dataset enables evaluation of detection, 3D reconstruction, and ambiguity-centric evidence completion in a realistic urban coastal environment.
```

---

## 8. 한 줄 요약

수정된 논문은 아래 구조로 가는 것이 가장 명확함.

```text
SOTA detector를 개선하는 2개 모듈 제안
+ multi-angle UAV image 기반 3D 생성형 모델 제안
+ MarineCity multi-angle / 3D reconstruction benchmark dataset 생성
```

이렇게 구성하면 detection 성능 개선, 3D 생성형 모델 비교, dataset contribution이 각각 분리되면서도 CoM3D-ACE라는 하나의 시스템으로 연결됨.
