# Survey Workspace

- Notion Section: `Related Research`
- Status: `Not Started`
- Source: `docs/survey_workspace.md`
- Export Date: `2026-05-07`

---

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

- 아직 확정하지 않습니다.
- survey가 끝난 뒤 최종 제안 시스템에 맞춰 다시 설계합니다.

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
