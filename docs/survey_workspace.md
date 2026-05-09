# Survey Workspace

이 문서는 서베이 단계에서만 사용하는 임시 정리 공간입니다.

서베이가 끝나면 여기서 확정된 내용만 골라서 다음 문서를 새로 만듭니다.

- 최종 제안 시스템
- 세부 모듈 구조
- 수식
- dataset plan
- experiment plan
- 구현 및 환경 문서
- paper draft

## 1. Related Research

| 번호 | 논문 / 자료 | 핵심 아이디어 | 우리 연구에 주는 힌트 | 상태 |
| --- | --- | --- | --- | --- |
| 1 |  |  |  | Reading |

## 2. System Ideas

- 아직 확정하지 않습니다.
- 서베이 중 나온 아이디어를 짧게 적고, 나중에 합칠 것만 남깁니다.

## 3. Dataset Candidates

결론: public UAV small-object dataset만으로는 논문이 성립하기 어렵다. 대부분 단일 이미지 2D bbox 중심이라 `multi-UAV`, `multi-view`, `3D location`, `pose/depth`, `re-observation`, `ambiguity resolution`을 평가할 수 없다.

따라서 데이터셋은 2단 구조로 간다.

### 3.1 Public Dataset: Front-End Detector 검증용

목적은 "always-on evidence generator가 2D UAV small-object detection에서 기본기가 있다"를 보이는 것이다.

| Dataset | 용도 | 우선순위 |
| --- | --- | --- |
| `VisDrone2019-DET` | UAV small/dense object detection main benchmark | 필수 |
| `UAVDT` | UAV vehicle detection / video-domain generalization | 필수 또는 강력 추천 |
| `AI-TOD` | high tiny-object ratio, `APtiny` / `APsmall` stress test | 추천 |
| `TinyPerson` | extreme tiny person detection | 선택 |
| `HIT-UAV` | infrared / low-light UAV object detection | 선택, 좋음 |
| `DroneVehicle` | RGB-IR vehicle dataset, modality extension 논의 | 선택 |

현실적인 ACCV 조합:

```text
Minimum: VisDrone2019-DET + UAVDT
Strong:  VisDrone2019-DET + UAVDT + AI-TOD
Extend:  VisDrone2019-DET + UAVDT + AI-TOD + HIT-UAV
```

`HIT-UAV`는 low-light / thermal ambiguity 주장을 만들 수 있지만, 시간이 부족하면 supplementary 또는 future extension으로 둔다.

### 3.2 CoM3D-UAV-Sim: 핵심 시스템 평가용 Synthetic Benchmark

임시 이름:

```text
CoM3D-UAV-Sim
```

논문식 이름 후보:

```text
CoM3D-ACE-Sim Benchmark
```

필요한 이유:

| 필요한 정보 | Public dataset 여부 | Synthetic 필요성 |
| --- | --- | --- |
| synchronized multi-UAV view | 거의 없음 | 필요 |
| camera pose / UAV pose | 제한적 | 필요 |
| depth map | 없음 또는 제한적 | 필요 |
| 3D object location GT | 없음 | 필요 |
| same-object multi-view ID | 없음 | 필요 |
| viewpoint / altitude variation | 제한적 | 필요 |
| active re-observation evaluation | 없음 | 필수 |
| ambiguity reason GT | 없음 | 생성 가능 |
| occlusion / low-res / side-view conflict 제어 | 어려움 | 필요 |

정리하면 `Isaac Sim`은 필요하다. `Cesium`은 있으면 도시 realism과 figure quality가 좋아지는 옵션이다.

### 3.3 Synthetic Benchmark 구성

| 항목 | 설정 |
| --- | --- |
| Simulator | `Isaac Sim` |
| Urban map | Haeundae-like coastal urban scene 또는 generic urban digital twin |
| Optional map source | `Cesium`, `OSM`, custom USD city assets |
| Sensors | RGB, depth, semantic/instance mask, camera pose, UAV pose |
| UAV 수 | 2, 3, 4대 |
| View types | nadir, oblique, side-view, rear-view, close-up |
| Altitude | 30m, 60m, 100m, 150m |
| Weather / lighting | clear, shadow, sunset, night, fog-like degradation |
| Object density | sparse, medium, dense |
| Occlusion | none, partial, heavy |

처음 class는 6-8개 정도로 제한한다.

```text
car
van
truck
bus
pedestrian
small boat
debris / obstacle
traffic cone / small structure
```

Fine-grained ambiguity 후보:

```text
sedan vs van vs pickup vs delivery truck
small boat vs buoy
pedestrian vs pole/debris
car vs occluded truck
```

### 3.4 Annotation Schema

각 frame은 최소 다음 필드를 저장한다.

```json
{
  "image_id": "scene_0001_uav_01_t0001",
  "uav_id": "uav_01",
  "timestamp": 123.45,
  "camera_intrinsic": [[0, 0, 0], [0, 0, 0], [0, 0, 1]],
  "camera_extrinsic": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
  "uav_pose": {
    "x": 0,
    "y": 0,
    "z": 80,
    "roll": 0,
    "pitch": -45,
    "yaw": 120
  },
  "objects": [
    {
      "object_id": "obj_0001",
      "class": "van",
      "bbox_2d": [0, 0, 32, 24],
      "mask": "optional/path.png",
      "bbox_3d": [0, 0, 0, 4.5, 1.8, 1.7, 0],
      "visibility": 0.62,
      "occlusion_level": "medium",
      "view_angle": "side",
      "pixel_size": 24,
      "distance": 82.3
    }
  ]
}
```

Split은 frame 단위가 아니라 scene 단위로 나눈다.

| Split | 구성 |
| --- | --- |
| Train | 60% scenes |
| Val | 20% scenes |
| Test-seen | 10% scenes, seen-style but unseen positions |
| Test-unseen | 10% scenes, unseen map / weather / altitude |

### 3.5 논문 내 데이터셋 사용 방식

```text
We evaluate CoM3D-ACE in two layers.
First, we validate the always-on small-object evidence generator on public UAV detection benchmarks such as VisDrone and UAVDT.
Second, we build a synchronized multi-UAV simulation benchmark in Isaac Sim to evaluate 3D evidence fusion, cross-view/cross-resolution alignment, ambiguity diagnosis, and active re-observation.
```

| 실험 | 데이터셋 |
| --- | --- |
| 2D detector 성능 | `VisDrone`, `UAVDT`, `AI-TOD` |
| tiny / cross-resolution | `AI-TOD`, synthetic downsampled `CoM3D` |
| multi-view 3D graph | `CoM3D-UAV-Sim` |
| re-observation policy | `CoM3D-UAV-Sim` |
| VLM ambiguity verification | `CoM3D-UAV-Sim` ambiguous subset + selected real crops |
| qualitative | synthetic + `VisDrone` / `UAVDT` examples |

## 4. Experiment Ideas

### 4.1 Re-observation Policy Ablation

목적: 재관측이 실제로 성능을 올리고, 비용 대비 효과가 있는지 보여준다.

비교 방법:

| Method | 설명 |
| --- | --- |
| No re-observation | 재관측 없음 |
| Random re-observation | 랜덤 viewpoint |
| Density-guided crop style | 2D dense region만 다시 crop 처리 |
| Greedy uncertainty | uncertainty 높은 object 재관측 |
| Greedy information gain | expected information gain 기준 |
| CoM3D-ACE policy | ambiguity + gain + cost + safety |

지표:

| 지표 | 의미 |
| --- | --- |
| Final accuracy gain | 재관측 전후 정확도 향상 |
| Ambiguity resolution rate | ambiguity 해결률 |
| Re-observation success rate | 재촬영 후 confidence 개선 |
| ΔEntropy | class entropy 감소 |
| Δ3D error | 3D 위치 오차 감소 |
| Number of re-observations | 요청 횟수 |
| Flight cost | 이동 거리 / 시간 |
| Energy cost | battery proxy |
| Communication cost | crop/frame 전송량 |
| VLM calls | VLM 호출 횟수 |
| End-to-end latency | 전체 시간 |

핵심 표:

| Method | Final Acc ↑ | Ambiguity Res. ↑ | 3D Error ↓ | Reobs ↓ | Cost ↓ | VLM Calls ↓ |
| --- | --- | --- | --- | --- | --- | --- |
| No reobs |  |  |  | 0 | 0 | 0 |
| Random |  |  |  |  |  |  |
| Density crop |  |  |  |  |  |  |
| Uncertainty only |  |  |  |  |  |  |
| Info gain only |  |  |  |  |  |  |
| Ours |  |  |  |  |  |  |

### 4.2 Selective VLM Verification Ablation

목적: 모든 객체에 VLM을 쓰는 것이 아니라, ambiguity가 높은 경우에만 쓰는 것이 성능/비용 균형이 좋다는 점을 보여준다.

비교 방법:

| Method | 설명 |
| --- | --- |
| No VLM | detector + graph만 |
| Always-on VLM | 모든 object crop에 VLM |
| Random VLM | random subset |
| Uncertainty-triggered VLM | uncertainty threshold |
| SAGE-triggered VLM | ambiguity + graph summary + SAGE prompt |

지표:

| 지표 | 의미 |
| --- | --- |
| Ambiguous subset accuracy | 어려운 객체 정확도 |
| Correction rate | 틀린 예측을 고친 비율 |
| Over-correction rate | 맞는 예측을 틀리게 바꾼 비율 |
| VLM call count | 비용 |
| Average tokens / latency | 추론 비용 |
| Explanation usefulness | 정성 평가 |
| JSON parse success rate | 시스템 안정성 |

핵심 표:

| Method | Ambiguous Acc ↑ | Correction ↑ | Over-correction ↓ | VLM Calls ↓ | Tokens ↓ | Latency ↓ | JSON Parse ↑ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| No VLM |  |  |  | 0 | 0 |  |  |
| Always-on VLM |  |  |  |  |  |  |  |
| Random VLM |  |  |  |  |  |  |  |
| Uncertainty-triggered VLM |  |  |  |  |  |  |  |
| SAGE-triggered VLM |  |  |  |  |  |  |  |

## 5. Decisions To Make Later

- 최종 task 정의
- main dataset / auxiliary dataset
- baseline model
- multi-UAV fusion 방식
- 3D reasoning 사용 범위
- active re-observation 실험 여부

## 6. Current Implementation Direction

- Main codebase direction: `3D evidence graph + ambiguity diagnosis + re-observation + selective SAGE VLM`
- Detector role: always-on front-end baseline, not the main novelty
- Public datasets: `VisDrone`, `UAVDT`, `AI-TOD`
- Full system validation: `Isaac Sim + Cesium` synthetic multi-UAV episodes
- Core modules now scaffolded: `evidence`, `alignment`, `graph`, `ambiguity`, `policy`, `vlm`, `evaluation`, `simulation`
- Windows bootstrap priority: `pathlib`, `environment.yml`, `scripts/check_env.py`, `scripts/01_convert_datasets.bat`, EvidenceToken JSONL pipeline
- Isaac export entrypoint: `simulation/isaac/export_rgb_depth_pose.py`
- Isaac dry-run check: `scripts/03_export_isaac_dataset.bat`

## 7. Windows 기준 구현 순서

### Phase 0. 프로젝트 초기화

목표: Windows에서 repo와 환경이 안정적으로 돌아가게 만든다.

작업:

```text
1. Git repo 생성
2. conda env 생성
3. dataset root 경로 설정
4. config loader 구현
5. logging / output directory 규칙 설정
```

완료 기준:

```powershell
python -m scripts.check_env
```

출력에서 GPU, PyTorch, OpenCV, dataset path가 정상 확인되어야 한다.

### Phase 1. Public Dataset 변환 및 Detector Baseline

목표: `VisDrone` / `UAVDT`에서 detector baseline을 확보한다.

순서:

```text
1. VisDrone -> COCO 변환
2. UAVDT -> COCO 변환
3. YOLOv8n / YOLOv11n 학습
4. RT-DETR-R18 학습
5. D-FINE-S 가능하면 추가
6. AP, AP50, AP75, APsmall, FPS 기록
```

초기 baseline:

```text
YOLOv8n
YOLOv11n
YOLOv8n+P2
RT-DETR-R18
Ours AEG
```

### Phase 2. EvidenceToken 생성

목표: detector 결과를 CoM3D-ACE 시스템 입력으로 바꾼다.

초기 운영:

```text
VisDrone / UAVDT:
  bbox, logits, confidence, crop_feature, uncertainty

CoM3D-Sim:
  bbox, logits, confidence, crop_feature, uncertainty, depth, pose
```

### Phase 3. Isaac Sim Dataset Export

목표: `CoM3D-Sim` 생성.

Windows에서는 Isaac을 별도로 실행해서 export한다.

```powershell
cd C:\isaacsim
python.bat C:\Users\<USER>\CoM3D-ACE\simulation\isaac\export_rgb_depth_pose.py
```

초기에는 도시 전체가 아니라 작은 block scene 3개부터 시작한다.

```text
scene_001: sparse vehicles
scene_002: dense vehicles + pedestrians
scene_003: occlusion / side-view ambiguity
```

Export 항목:

```text
RGB image
depth map
semantic / instance mask
camera intrinsic
camera extrinsic
UAV pose
object 2D bbox
object 3D bbox
object ID
visibility
occlusion level
view angle
distance
pixel size
```

### Phase 4. Cross-View Association + 2D-to-3D Lifting

목표: 같은 객체를 여러 view에서 연결하고 3D 위치를 추정한다.

처음에는 복잡한 GNN 대신 deterministic matching으로 시작한다.

```text
C(e_i, e_j)
= lambda_app d_app
+ lambda_geo d_geo
+ lambda_cls d_cls
+ lambda_res d_res
+ lambda_time d_time
+ lambda_unc d_unc
```

Reliability:

```text
r_i = sigmoid(a * resolution_i + b * visibility_i - c * uncertainty_i - d * geometry_residual_i)
```

완료 기준:

```text
Association F1
False merge rate
False split rate
3D center error
```

### Phase 5. 3D Evidence Graph

목표: object hypothesis node 생성.

처음에는 `PyG`가 아니라 custom graph로 간다.

```json
{
  "observation_nodes": [],
  "object_nodes": [],
  "edges": []
}
```

Edge type:

```text
visual similarity
geometry consistency
temporal consistency
uncertainty relation
```

Object output:

```text
fine-grained class distribution
3D position
confidence
support views
graph consistency score
```

### Phase 6. Ambiguity Diagnosis

목표: 어떤 object node가 틀릴 가능성이 높은지 예측한다.

```text
S(o)
= w_H H_class
+ w_D D_view
+ w_M M_missing
+ w_O O_occ
+ w_R R_lowres
+ w_G G_geo
```

이 실험에서 ROC-AUC를 뽑는다.

```text
positive label = 최종 예측이 틀렸거나 insufficient evidence인 object
score = S(o)
metric = ROC-AUC, AUPRC, FPR@95TPR
```

### Phase 7. Evidence Completion Policy

목표: `finalize` / `VLM verify` / `re-observe` 중 선택.

```text
a* = argmax_a EIG(a, o) - lambda_cost Cost(a) - lambda_risk Risk(a)
```

Candidate action:

```text
front view
side view
rear view
top-down view
closer view
same position high-res crop
```

처음에는 실제 Isaac 재비행 없이, pre-generated candidate views 중 policy가 하나를 선택하게 만든다.

### Phase 8. Selective VLM Verification

목표: ambiguity가 높은 object node만 VLM에 보낸다.

순서:

```text
1. SAGE prompt package 생성
2. open-source VLM 또는 API로 subset만 테스트
3. output JSON parser 구현
4. graph confidence update
5. always-on VLM 대비 call 수 / latency 비교
```

이름:

```text
SAGE = Scene-aware Ambiguity-guided Graph Evidence Prompt
```

## 8. 비교 실험 구조

비교는 두 층으로 분리한다.

```text
A. 2D front-end detector 비교
B. multi-view / graph / re-observation system 비교
```

이걸 분리하지 않으면 논문이 detector paper인지 system paper인지 흐려진다.

### 8.1 2D Detector 비교 모델

P0:

| 모델 | 이유 |
| --- | --- |
| YOLOv8n/s | 기본 lightweight YOLO baseline |
| YOLOv11n/s | 최신 계열 YOLO baseline |
| YOLOv8n+P2 | small-object head 추가 baseline |
| RT-DETR-R18 | DETR 계열 대표 baseline |
| D-FINE-S | 최신 DETR-style detector baseline 가능 |
| Ours Always-on Evidence Generator | 우리 front-end |

P1:

| 모델 | 이유 |
| --- | --- |
| UAVDet | CNN-Mamba 계열 강한 실시간 baseline |
| LRDS-YOLO | lightweight YOLOv11 small-object 특화 |
| BPD-YOLO / L-FPN | shallow-centric FPN baseline |
| HF-D-FINE | high-resolution D-FINE tiny detector |

P2:

| 모델 | 이유 |
| --- | --- |
| CSFPR-RTDETR | spatial-frequency + position relation |
| DG-TSOD | density-guided two-stage detector |
| CFIA | coarse-fine feature alignment |

최종 추천 detector set:

```text
YOLOv8n
YOLOv11n
YOLOv8n+P2
RT-DETR-R18
D-FINE-S
UAVDet or LRDS-YOLO
Ours AEG
```

### 8.2 System-Level 비교 Baseline

| Baseline | 설명 |
| --- | --- |
| Single-view detector | 가장 confidence 높은 view만 사용 |
| Multi-view average pooling | view별 class score 평균 |
| Multi-view max pooling | 최고 confidence 선택 |
| Naive 3D fusion | pose/depth로 3D 위치만 합침 |
| Graph-only | 3D evidence graph만 사용 |
| Graph + cross-view alignment | alignment 포함 |
| Graph + ambiguity diagnosis | ambiguous object score 사용 |
| Graph + random re-observation | 재관측은 랜덤 |
| Graph + uncertainty re-observation | uncertainty 높은 객체 재관측 |
| Full CoM3D-ACE | alignment + ambiguity + policy + selective VLM |

최종 결과표:

| Method | Final Acc ↑ | 3D Error ↓ | Assoc. F1 ↑ | Ambiguity Res. ↑ | Reobs ↓ | VLM Calls ↓ |
| --- | --- | --- | --- | --- | --- | --- |
| Single-view |  |  | - | - | 0 | 0 |
| Avg multi-view |  |  |  | - | 0 | 0 |
| Naive 3D fusion |  |  |  | - | 0 | 0 |
| Graph-only |  |  |  |  | 0 | 0 |
| Graph + Alignment |  |  |  |  | 0 | 0 |
| Graph + Random Reobs |  |  |  |  |  | 0 |
| Graph + Uncertainty Reobs |  |  |  |  |  |  |
| Full CoM3D-ACE |  |  |  |  |  |  |

반드시 보여줘야 하는 결과:

1. 2D detector 기본 성능: `VisDrone` / `UAVDT`에서 `APsmall`, `FPS`가 경쟁력 있어야 함.
2. Multi-view graph가 single-view보다 좋다: final object accuracy, 3D error, association F1 개선.
3. Cross-view / cross-resolution alignment가 필요하다: 고도/각도/해상도 다른 조건에서 naive fusion보다 우수.
4. Ambiguity score가 실제 오류를 잘 예측한다: AUROC / AUPRC / ECE 제시.
5. Re-observation이 성능을 올린다: random이나 uncertainty-only보다 cost 대비 우수.
6. Selective VLM이 always-on VLM보다 효율적이다: 비슷하거나 더 좋은 ambiguous accuracy를 훨씬 적은 VLM call로 달성.
