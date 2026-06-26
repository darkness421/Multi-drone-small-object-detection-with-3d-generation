# MarineCity System Integration Check

Updated: `2026-06-26 13:13:10 KST`
Status: `marinecity_system_integration_smoke_ready_with_pending_final_gates`

## Gate Summary

| Gate | Status | Evidence |
|---|---|---|
| real_cesium_stage | PASS | google_tiles=True, terrain=True, fake_city=False |
| visdrone_actor_overlay | PASS | objects=6, classes=bus,car,pedestrian,person,truck,van |
| multi_uav_markers_and_cameras | PASS | uav_markers=3, capture_cameras=3 |
| real_capture_rgb_depth_pose | PASS | scenarios=3, frames=9, altitude_range=140.0-160.0m |
| safr_yolo_from_uav_views | PASS | tokens=23, device=1, classes={'car': 15, 'bus': 8} |
| pedestrian_detection_from_current_views | WARN | pedestrian/person actors=True, main_conf015_person_tokens=0, supp_conf005_person_tokens=1. Use the low-confidence run only as a diagnostic/qualitative candidate unless promoted by a fixed protocol. |
| crossview_evidence_graph | PASS | hypotheses=13, multi_view=5 |
| neural_3d_completion_benchmark | PENDING | Current real-Cesium RGB/depth/pose captures are valid source evidence. Do not claim NeRF/Instant-NGP/Mip-NeRF/3DGS completion until metric rows exist. |
| external_llm_reasoner | PENDING | 49-prompt external_ready=False, 23-prompt status=aerograph_real_capture_nonmock_smoke_pending |
| tinyperson_640_supplement | PASS | Use TinyPerson as supplementary domain-shift evidence only. The current sparse converted 640 split does not support a headline SAFR-YOLO improvement claim. |

## Real-Cesium Stage

- Stage path: `/workspace/uav_marinecity/uavmarine.usd`
- Root layer: `/workspace/uav_marinecity/uavmarine.usd`
- Georeference readback: `{'valid': True, 'path': '/CesiumGeoreference', 'latitude': 35.1569, 'latitude_attr': 'cesium:georeferenceOrigin:latitude', 'longitude': 129.1439, 'longitude_attr': 'cesium:georeferenceOrigin:longitude', 'height': 200.0, 'height_attr': 'cesium:georeferenceOrigin:height'}`
- Google Photorealistic 3D Tiles: `True`
- Cesium terrain: `True`
- Fake/substitute city geometry: `False`

## Actors, UAVs, And Captures

- Actor layer: `/home/oem/UAV/uav_marinecity/uavmarine_multiuav_actor_overlay_s0_locked_roi.usda`
- Actor classes: `['bus', 'car', 'pedestrian', 'person', 'truck', 'van']`
- Object count: `6`
- UAV marker count: `3`
- Camera prim count in captured frames: `3`
- Capture scenarios/frames: `3` / `9`
- UAV camera altitude range: `[140.0, 160.0]` m
- Mean RGB black ratio / depth finite ratio: `0.0913768325617284` / `0.908344425154321`

## SAFR-YOLO Smoke

- Detector status: `marinecity_real_capture_detector_smoke_complete`
- Device/img/conf: `1` / `1280` / `0.15`
- Frame/token count: `9` / `23`
- Tokens by class: `{'car': 15, 'bus': 8}`
- Preview sheet: `/home/oem/projects/multi-uav-marine-city/outputs/evidence/marinecity_real_capture_detector_smoke/marinecity_detector_preview_contact_sheet.png`

## Pending Final Gates

- 3D completion: `pending_upstream_runner_connection`; Current real-Cesium RGB/depth/pose captures are valid source evidence. Do not claim NeRF/Instant-NGP/Mip-NeRF/3DGS completion until metric rows exist.
- LLM reasoner: `aerograph_reviewed_candidate_ready_external_pending`; external provider ready `False`
- TinyPerson: `complete_supplementary_stress_test`; best `YOLOv9m-TinyPerson640` AP `0.00019666666666666666`; ours AP `1e-05`

Claiming rule: report the current MarineCity results as a real-Cesium system smoke/protocol validation. Do not claim completed neural 3D generation or external LLM validation until the pending gates pass.
