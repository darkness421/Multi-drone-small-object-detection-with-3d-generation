# CoM3D-ACE System Specification

- Notion Section: `Proposed Method`
- Status: `Not Started`
- Source: `NOTION_SYSTEM_SPEC.md`
- Export Date: `2026-05-07`

---

# CoM3D-ACE System Specification

## 1. Paper Title

CoM3D-ACE: Ambiguity-Centric 3D Evidence Completion for Cooperative Multi-UAV Fine-Grained Object Detection in Urban Digital Twins

## 2. Research Goal

부산 해운대 마린시티 digital twin에서 협력형 다중 UAV가 고고도 미세 객체를 다중 시점으로 관측하고, 3D evidence graph와 ambiguity-centric evidence completion을 통해 fine-grained detection을 수행하는 시스템 개발.

## 3. Core Problem

- Tiny object scale
- Fine-grained ambiguity
- Urban occlusion
- Viewpoint dependency
- Multi-UAV annotation scarcity
- Random synthetic data limitation

## 4. Proposed System

### 4.1 MarineCity Digital Twin Builder
### 4.2 Multi-UAV Scenario Generator
### 4.3 UAV Sensor Simulator
### 4.4 Onboard Edge Detection
### 4.5 2D-to-3D Object Lifting
### 4.6 3D Object Evidence Graph
### 4.7 Ambiguity Diagnosis
### 4.8 Evidence Completion Policy
### 4.9 Final Decision Module

## 5. Dataset Plan

### 5.1 CoM3D-MarineCity
### 5.2 VisDrone-DET
### 5.3 AI-TOD
### 5.4 UAVDT
### 5.5 FAIR1M

## 6. Simulation Environment

- NVIDIA Isaac Sim
- Cesium for Omniverse
- Busan Haeundae Marine City
- Isaac Replicator
- RGB / depth / segmentation / pose

## 7. Model Stack

- YOLO11 / RT-DETR
- DINOv2 / SigLIP
- Isaac depth-based 3D lifting
- 3D Object Evidence Graph
- Qwen2.5-VL / InternVL / LLaVA-OneVision
- Symbolic verifier

## 8. Experiment Plan

### Exp1. Single-UAV vs Multi-UAV
### Exp2. 2D Fusion vs 3D Evidence Graph
### Exp3. Ambiguity Diagnosis
### Exp4. Active Re-Observation
### Exp5. Failure-Conditioned Scenario Generation

## 9. Codex Task Board

- Repo scaffold
- Scenario schema
- MarineCity annotation converter
- 2D-to-3D lifting
- Evidence graph builder
- Ambiguity diagnosis prompt
- Experiment runner skeleton

## 10. Milestone

- Week 1: Isaac + Cesium setup
- Week 2: MarineCity capture
- Week 3: Scenario/annotation schema
- Week 4: Detector baseline
- Week 5: 3D lifting/evidence graph
- Week 6: Ambiguity diagnosis
- Week 7: Re-observation experiment
- Week 8: Paper figures/tables
