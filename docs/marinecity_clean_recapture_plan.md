# MarineCity Clean Full-Frame Recapture Plan

Updated: `2026-06-27 20:53:16 KST`
Status: `main_full_frame_ready`
Source gate: `outputs/reports/live/marinecity_qualitative_gate.json`
Source gate status: `marinecity_qualitative_gate_main_ready`

## Why This Is Needed

The real-Cesium MarineCity pipeline and 49 token-level smoke tests are present. The current best full-frame capture now satisfies the main-paper qualitative gate; keep this runbook as the reproducible recapture and QA recipe.

| Metric | Current | Target | Gap |
| --- | ---: | ---: | ---: |
| Best full-frame black/void | `0.017828` | `0.100000` | `0.000000` |
| Mean top-3 full-frame black/void | `0.087552` | `0.150000` | `0.000000` |
| Best crop black/void | `0.003577` | `0.020000` | supplementary-only |

## Height And Camera Policy

- User-visible MarineCity review height: `160 m`.
- UAV/camera observation band: `140-160 m`.
- Default S0 UAV schedule: `uav_01=140 m`, `uav_02=150 m`, `uav_03=160 m`.
- Keep this separate from CesiumGeoreference readback.

## Hard Constraints

- Open the real Cesium MarineCity USD only.
- Use actor-only session overlays for S0/S1/S2.
- Do not create fake, proxy, placeholder, block, or fallback city geometry.
- Do not overwrite or save the base uavmarine.usd during capture.
- If Cesium tiles fail to render, fail with diagnostics rather than substituting geometry.

## Scenario Targets

| Scenario | Overlay | Output | Purpose |
| --- | --- | --- | --- |
| S0 | `uavmarine_multiuav_actor_overlay_s0_locked_roi.usda` | `uavmarine_s0_viewer160_session_recapture` | locked MarineCity ROI smoke/full-frame candidate |
| S1 | `uavmarine_multiuav_actor_overlay_s1_adjacent_overlap.usda` | `uavmarine_s1_viewer160_session_recapture` | adjacent-overlap ambiguity candidate |
| S2 | `uavmarine_multiuav_actor_overlay_s2_coastline_multiview.usda` | `uavmarine_s2_viewer160_session_recapture` | coastline multi-view candidate |

## Commands

Start or reopen the real-Cesium GUI at the 160 m review profile if the current GUI is not stable:

```bash
COM3D_KEEP_USER_CAMERA=1 COM3D_VIEWER_PROFILE=viewer160 COM3D_GEOREF_HEIGHT=160.0 SESSION=uav-marinecity-s0-viewer160-gui bash scripts/ubuntu/start_uavmarine_overlay_gui.sh s0
```

Run or reproduce the clean recapture + detector + rule-based reasoner queue:

```bash
FORCE_RECAPTURE=1 FORCE_DETECTOR=1 FORCE_REASONER=1 CAPTURE_USE_ACTOR_SESSION=1 CAPTURE_HEADLESS=1 CAPTURE_CAMERA_PROFILE=viewer160-clean CAPTURE_OPEN_WARMUP=900 CAPTURE_RENDER_WARMUP=240 CAPTURE_WIDTH=1280 CAPTURE_HEIGHT=720 DETECTOR_DEVICE=cpu DETECTOR_IMGSZ=1280 DETECTOR_CONF=0.01 REASONER_PROVIDER=mock bash scripts/ubuntu/start_marinecity_viewer160_pipeline_queue.sh
```

Monitor while it runs:

```bash
tmux attach -t marinecity-viewer160-pipeline
tail -f outputs/logs/marinecity_viewer160_pipeline/queue.log
```

After the queue finishes, regenerate visual QA, gates, and dashboards:

```bash
python scripts/select_marinecity_capture_quality.py
python scripts/build_marinecity_real_capture_crop_candidates.py
python scripts/build_marinecity_qualitative_selection.py
python scripts/check_marinecity_qualitative_gate.py
python scripts/build_marinecity_simulation_dashboard.py
PYTHONPATH=. python scripts/build_live_training_dashboard.py --out outputs/reports/live/training_dashboard.png
python scripts/check_paper_artifact_readiness.py
python scripts/build_accv_status_snapshot.py
```

## Acceptance

Main full-frame qualitative figure is ready only when all of these are true:

- `real_cesium_ok == true`
- `system_smoke_ok == true`
- `best_full_capture.best_black_ratio <= 0.1`
- `best_full_capture.mean_top3_black_ratio <= 0.15`

Crop candidates remain supplementary-only unless explicitly captioned as crop-only framing evidence.

## Outputs To Watch

- `pipeline_status`: `outputs/experiments/marinecity_viewer160_pipeline_status.md`
- `queue_log`: `outputs/logs/marinecity_viewer160_pipeline/queue.log`
- `capture_quality_csv`: `outputs/reports/live/marinecity_capture_quality/marinecity_capture_quality_rank.csv`
- `capture_quality_sheet`: `outputs/reports/live/marinecity_capture_quality/marinecity_capture_quality_top8.png`
- `qualitative_gate`: `outputs/reports/live/marinecity_qualitative_gate.json`
- `simulation_dashboard`: `outputs/reports/live/marinecity_simulation_dashboard.png`

## Next After Pass

- Promote the passing full-frame image into paper/figures/results/marinecity_system.
- Update paper/sections/07_marinecity_qualitative_figure_slots.tex from the regenerated selection manifest.
- Keep crop-only figures in supplementary unless the main caption clearly states crop-only framing.
- Use the reviewed 49-prompt AeroGraph candidate with a caveat; run external-provider replication before claiming final reasoner performance.
