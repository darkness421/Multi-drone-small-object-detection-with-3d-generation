# Dataset 계획

Dataset은 UAV 기반 small object detection, multi-view reasoning, 그리고 최종 `Isaac Sim`/`Cesium` Marine City 데모를 모두 지원할 수 있어야 합니다.

## 후보 Dataset

| Dataset | 역할 | 필요한 이유 | 상태 |
| --- | --- | --- | --- |
| VisDrone | 메인 training baseline | UAV 시점, 도시 장면, 작은 pedestrian/vehicle 객체가 많음 | 후보 |
| AI-TOD | tiny-object 평가 | 매우 작은 aerial object 성능을 검증하기 좋음 | 후보 |
| SeaDronesSee | 해안/해상 보조 데이터 | Marine City 주변의 sea/coastal object 상황에 유용함 | 후보 |
| Isaac Sim synthetic data | domain adaptation 및 데모 데이터 | Marine City geometry, UAV camera angle, target scenario를 직접 맞출 수 있음 | 계획 |

## 초기 추천

처음에는 `VisDrone`을 baseline dataset으로 시작하는 것이 좋습니다. 이후 `AI-TOD`를 추가해 small object 성능을 강하게 검증하고, 해안/해상 target이 필요하면 `SeaDronesSee`를 보조 dataset으로 사용합니다. 마지막에는 `Isaac Sim`에서 Marine City 전용 synthetic data를 생성해 domain adaptation과 시각화 데모에 사용합니다.

## Class Mapping 초안

| Project Class | 가능한 Source Class |
| --- | --- |
| person | pedestrian, people, person |
| vehicle | car, van, truck, bus |
| small_boat | boat, vessel |
| debris | custom synthetic labels |
