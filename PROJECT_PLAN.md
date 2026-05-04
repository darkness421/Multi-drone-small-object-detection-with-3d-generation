# PROJECT PLAN

## Title

CoM3D-ACE: Ambiguity-Centric 3D Evidence Completion for Cooperative Multi-UAV Fine-Grained Object Detection in Urban Digital Twins

## Research Goal

부산 해운대 마린시티 digital twin 환경에서 협력형 Multi-UAV가 고고도 fine-grained object를 다중 시점으로 관측하고, 3D evidence graph와 ambiguity-centric evidence completion을 통해 더 정확한 object decision과 recommended next view를 만드는 시스템을 개발합니다.

## System Modules

| Module | 역할 |
| --- | --- |
| MarineCity Digital Twin Builder | `Cesium` + `Isaac Sim`으로 해운대 마린시티 환경 구성 |
| Multi-UAV Scenario Generator | UAV 수, 고도, 각도, 객체 배치 제어 |
| UAV Sensor Simulator | RGB, depth, segmentation, bbox, pose 생성 |
| Onboard Edge Detector | UAV별 small object 후보 검출 |
| 2D-to-3D Object Lifting | 2D bbox를 depth/pose 기반 3D object hypothesis로 변환 |
| 3D Object Evidence Graph | multi-view crop, geometry, context, uncertainty 통합 |
| Ambiguity Diagnosis | 객체가 왜 애매한지, 어떤 증거가 부족한지 판단 |
| Evidence Completion Policy | active re-observation 또는 failure-conditioned scenario generation 수행 |
| Final Decision Module | fine-grained class, 3D location, confidence, explanation 출력 |

## Dataset Plan

| Dataset | 용도 |
| --- | --- |
| CoM3D-MarineCity | 직접 생성할 핵심 synthetic Multi-UAV + 3D annotation dataset |
| VisDrone-DET | 실제 UAV small object detector pretraining |
| AI-TOD / AI-TOD-v2 | tiny object stress test |
| UAVDT | vehicle detection/tracking, temporal evidence |
| FAIR1M | fine-grained remote sensing representation pretraining |

## Initial Task Board

1. Repo scaffold
2. Scenario schema
3. MarineCity annotation converter
4. 2D-to-3D lifting prototype
5. Evidence graph builder
6. Ambiguity diagnosis prompt
7. Experiment runner skeleton

## ACCV Summary Direction

6월 중순까지 Introduction, Related Work, Proposed Method 1차 완성을 목표로 합니다. 6월 말에는 결과표와 figure를 정리하고, 7월 5일 ACCV 요약 제출 전에는 새 기능을 추가하지 않습니다.

