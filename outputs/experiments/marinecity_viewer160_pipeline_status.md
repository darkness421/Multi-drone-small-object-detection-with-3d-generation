# MarineCity Viewer160 Pipeline Status

- Updated: 2026-06-28T21:58:34+09:00
- Phase: finished completed=3 failed=0
- Isaac container: `isaac-sim-gui-uav-marinecity`
- Capture profile: `viewer160-clean`
- Detector: `P2P4-SelfAttnFR` checkpoint `outputs/detectors/server_yolov11_p2p4_balanced/20260610_073629_proposed_p2p4_balanced_selfattn_tiny_frelu_yolo11l_visdrone_yolov11_p2_balanced_seed123/ultralytics/weights/best.pt`
- Detector device: `cpu`
- Reasoner provider: `rule_based`
- External/local reasoner: not configured; using rule-based verifier until `OPENAI_API_KEY` or `AEROGRAPH_COMMAND` is set

## Scenario Queue

| Scenario | Overlay USD | Capture | Detector | Reasoner |
| --- | --- | --- | --- | --- |
| S0 | `uavmarine_multiuav_actor_overlay_s0_locked_roi.usda` | done | done | done |
| S1 | `uavmarine_multiuav_actor_overlay_s1_adjacent_overlap.usda` | done | done | done |
| S2 | `uavmarine_multiuav_actor_overlay_s2_coastline_multiview.usda` | done | done | done |

## Latest Queue Log

```text
  "conf": 0.01,
  "uav_count": 3,
  "token_count": 30,
  "tokens_by_uav": {
    "uav_01": 4,
    "uav_02": 23,
    "uav_03": 3
  },
  "tokens_by_class": {
    "bus": 6,
    "car": 20,
    "pedestrian": 3,
    "van": 1
  }
}
[2026-06-28T21:58:24+09:00] DETECTOR_OK scenario=S2 out=outputs/evidence/uavmarine_s2_viewer160_session_recapture_detector_smoke_conf001
/home/oem/projects/multi-uav-marine-city/outputs/reports/live/marinecity_simulation_dashboard.png
/home/oem/projects/multi-uav-marine-city/outputs/reports/live/training_dashboard.png
[2026-06-28T21:58:28+09:00] START reasoner scenario=S2 provider=rule_based out=outputs/reasoning/uavmarine_s2_viewer160_session_recapture_from_detector_conf001_rule_based
{
  "status": "marinecity_3d_reasoner_smoke_complete",
  "scenario": "s2_coastline_multiview",
  "source": "detector_tokens",
  "provider": "rule_based_aerograph",
  "runner_provider": "rule_based",
  "hypothesis_count": 21,
  "llm_call_count": 21,
  "reobserve_count": 21,
  "output_dir": "outputs/reasoning/uavmarine_s2_viewer160_session_recapture_from_detector_conf001_rule_based"
}
[2026-06-28T21:58:30+09:00] REASONER_OK scenario=S2 out=outputs/reasoning/uavmarine_s2_viewer160_session_recapture_from_detector_conf001_rule_based
/home/oem/projects/multi-uav-marine-city/outputs/reports/live/marinecity_simulation_dashboard.png
/home/oem/projects/multi-uav-marine-city/outputs/reports/live/training_dashboard.png
[2026-06-28T21:58:34+09:00] SCENARIO_DONE S2
[2026-06-28T21:58:34+09:00] QUEUE_FINISHED marinecity_viewer160 completed=3 failed=0
```
