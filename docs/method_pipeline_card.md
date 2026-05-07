# Ambiguity-centric 3D object detection pipeline

## 목적

`CoM3D-ACE`의 핵심 pipeline을 코드와 논문 figure로 동시에 발전시키기 위한 카드입니다.

## 현재 Pipeline

```text
MarineCity annotation
→ COCO 2D annotation
→ evidence JSON
→ synthetic depth 기반 3D lifting
→ 3D object evidence graph
→ summary JSON
```

## 현재 구현

- `pipelines/run_dummy_evidence_pipeline.py`
- `datasets/converters/marinecity_to_coco.py`
- `lifting3d/depth_lifting.py`
- `evidence_graph/graph_schema.py`
- `tests/test_dummy_pipeline.py`

## 2026-05-07 완료

- dummy MarineCity annotation에서 COCO/evidence JSON 생성
- synthetic depth map과 identity-like camera pose를 이용한 placeholder 3D lifting
- lifted multi-view evidence를 object-centered 3D evidence graph로 변환
- summary JSON 생성
- `python -m unittest discover tests` 통과

## 다음 작업

- 실제 `camera_pose` JSON을 읽어 camera extrinsics로 변환
- per-view lifted 3D center를 graph node에 더 자세히 보존
- ambiguity diagnosis prompt 입력 형식과 evidence graph를 연결
- paper figure용 graph summary/visualization 생성

