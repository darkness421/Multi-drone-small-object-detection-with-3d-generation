# MarineCity Viewer160 Pipeline Status

- Updated: 2026-06-27T13:11:14+09:00
- Phase: finished completed=3 failed=0
- Isaac container: `isaac-sim-gui-uav-marinecity`
- Capture profile: `viewer160`
- Detector: `P2P4-SelfAttnFR` checkpoint `outputs/detectors/server_yolov11_p2p4_balanced/20260610_073629_proposed_p2p4_balanced_selfattn_tiny_frelu_yolo11l_visdrone_yolov11_p2_balanced_seed123/ultralytics/weights/best.pt`
- Detector device: `0`
- Reasoner provider: `mock`
- ChatGPT/OpenAI reasoner: not configured; using mock reasoner until `OPENAI_API_KEY` or `AEROGRAPH_COMMAND` is set

## Scenario Queue

| Scenario | Overlay USD | Capture | Detector | Reasoner |
| --- | --- | --- | --- | --- |
| S0 | `uavmarine_multiuav_actor_overlay_s0_locked_roi.usda` | done | done | done |
| S1 | `uavmarine_multiuav_actor_overlay_s1_adjacent_overlap.usda` | done | done | done |
| S2 | `uavmarine_multiuav_actor_overlay_s2_coastline_multiview.usda` | done | done | done |

## Latest Queue Log

```text
  "uav_count": 3,
  "token_count": 39,
  "tokens_by_uav": {
    "uav_01": 17,
    "uav_02": 15,
    "uav_03": 7
  },
  "tokens_by_class": {
    "car": 24,
    "bus": 4,
    "van": 4,
    "pedestrian": 6,
    "truck": 1
  }
}
[2026-06-27T13:10:58+09:00] DETECTOR_OK scenario=S2 out=outputs/evidence/uavmarine_s2_viewer160_session_recapture_detector_smoke_conf001
/home/oem/projects/multi-uav-marine-city/outputs/reports/live/marinecity_simulation_dashboard.png
/home/oem/projects/multi-uav-marine-city/outputs/reports/live/training_dashboard.png
[2026-06-27T13:11:05+09:00] START reasoner scenario=S2 provider=mock out=outputs/reasoning/uavmarine_s2_viewer160_session_recapture_from_detector_conf001_mock
{
  "status": "marinecity_3d_reasoner_smoke_complete",
  "scenario": "s2_coastline_multiview",
  "source": "detector_tokens",
  "provider": "mock_symbolic_aerograph",
  "runner_provider": "mock",
  "hypothesis_count": 27,
  "llm_call_count": 27,
  "reobserve_count": 27,
  "output_dir": "outputs/reasoning/uavmarine_s2_viewer160_session_recapture_from_detector_conf001_mock"
}
[2026-06-27T13:11:07+09:00] REASONER_OK scenario=S2 out=outputs/reasoning/uavmarine_s2_viewer160_session_recapture_from_detector_conf001_mock
/home/oem/projects/multi-uav-marine-city/outputs/reports/live/marinecity_simulation_dashboard.png
/home/oem/projects/multi-uav-marine-city/outputs/reports/live/training_dashboard.png
[2026-06-27T13:11:14+09:00] SCENARIO_DONE S2
[2026-06-27T13:11:14+09:00] QUEUE_FINISHED marinecity_viewer160 completed=3 failed=0
```
