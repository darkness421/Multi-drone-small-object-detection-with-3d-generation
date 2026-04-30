# Dataset Plan

Dataset choices should support UAV-based small object detection, multi-view reasoning, and the final Isaac Sim/Cesium Marine City demo.

## Candidate Datasets

| Dataset | Role | Why It Matters | Status |
| --- | --- | --- | --- |
| VisDrone | Main training baseline | UAV viewpoint, urban scenes, small pedestrians and vehicles | Candidate |
| AI-TOD | Tiny-object evaluation | Strong benchmark for very small aerial objects | Candidate |
| SeaDronesSee | Coastal/marine auxiliary data | Useful for sea/coastal object cases near Marine City | Candidate |
| Isaac Sim synthetic data | Domain adaptation and demo data | Can match Marine City geometry, UAV camera angles, and target scenarios | Planned |

## Initial Recommendation

Start with VisDrone as the first baseline dataset, then add AI-TOD for small-object stress testing. Use SeaDronesSee if the scenario includes sea/coastal targets. Generate Isaac Sim synthetic data later for Marine City-specific adaptation and visualization.

## Class Mapping Draft

| Project Class | Possible Source Classes |
| --- | --- |
| person | pedestrian, people, person |
| vehicle | car, van, truck, bus |
| small_boat | boat, vessel |
| debris | custom synthetic labels |

