# UAVMarine Multi-UAV Scenario Plan

Date: 2026-06-25

This setup uses the user-verified real Cesium Marine City stage as the base map.
Do not overwrite the base USD during object, UAV, camera, or detector testing.

## Locked Base

- Base USD: `/home/oem/UAV/uav_marinecity/uavmarine.usd`
- Locked backup: `/home/oem/UAV/uav_marinecity/backups/uavmarine_locked_20260624_2105.usd`
- Rule: preserve this base coordinate/altitude state. Scenario files must sublayer
  this base USD and add only non-destructive overlays.

## Scenario Overlays

Use the actor-only session overlays for live Isaac work. The base stage remains
`uavmarine.usd`; the scenario layer is added only to the session layer, so the
base USD is not saved or overwritten.

- Scenario 0: `/home/oem/UAV/uav_marinecity/uavmarine_multiuav_actor_overlay_s0_locked_roi.usda`
  - Balanced Marine City ROI smoke test.
  - Use first to verify that the real Cesium map, ROI markers, objects, and UAVs
    all appear together.

- Scenario 1: `/home/oem/UAV/uav_marinecity/uavmarine_multiuav_actor_overlay_s1_adjacent_overlap.usda`
  - Adjacent/overlapping small objects.
  - Intended for overlap-aware NMS and small-object ambiguity tests.

- Scenario 2: `/home/oem/UAV/uav_marinecity/uavmarine_multiuav_actor_overlay_s2_coastline_multiview.usda`
  - Coastline multi-view ambiguity.
  - Intended for 3D evidence completion and graph-grounded reasoner tests.

Legacy full-stage overlays named `uavmarine_multiuav_overlay_*.usda` are kept
only for older automated captures. For live visual verification, prefer the
actor-only session overlays above.

If the current Isaac GUI can be closed/restarted, use the dedicated launcher
from the repository so the real Cesium overlay and review-camera script are
loaded at startup:

```bash
bash scripts/ubuntu/start_uavmarine_overlay_gui.sh s0
```

Use `s1` or `s2` instead of `s0` for the adjacent-overlap and coastline
multi-view scenarios. This launcher restarts the
`isaac-sim-gui-uav-marinecity` container, but it does not overwrite
`uavmarine.usd`; it opens the real Cesium base stage, adds the selected
actor-only overlay as a session layer, and writes status under
`/home/oem/UAV/uav_marinecity/outputs/uavmarine_session_overlay_status_*.json`.

## UAV Camera Views

Each scenario contains three UAV markers:

- `uav_01`: low-altitude detector view
- `uav_02`: cross-view confirmation
- `uav_03`: wide-area context

Current UAV camera/marker altitude policy is locked to the UAV-style
`140--160 m` band so the simulated views stay closer to the VisDrone-like
training imagery:

| Scenario | uav_01 | uav_02 | uav_03 |
| --- | ---: | ---: | ---: |
| S0 locked ROI | 140 m | 150 m | 160 m |
| S1 adjacent overlap | 145 m | 150 m | 155 m |
| S2 coastline multiview | 160 m | 150 m | 140 m |

Operational decision as of 2026-06-25: use about `160 m` as the user-visible
MarineCity review height, and keep all UAV observation cameras inside the
`140--160 m` range. This replaces the older `80 m`/`900 m` debug profiles for
paper-facing experiments.

Keep CesiumGeoreference height separate from these UAV camera altitudes. The
latest status file may report an older georeference readback, but paper-facing
simulation metadata should use the UAV altitude policy above.

The runtime helper creates camera paths under:

- `/World/CoM3D_ACE_UAVMarine/RuntimeCameras/overview_Camera`
- `/World/CoM3D_ACE_UAVMarine/RuntimeCameras/uav_01_Camera`
- `/World/CoM3D_ACE_UAVMarine/RuntimeCameras/uav_02_Camera`
- `/World/CoM3D_ACE_UAVMarine/RuntimeCameras/uav_03_Camera`

This means each drone can have its own visible camera composition. The intended
pipeline is:

1. Open the scenario overlay in Isaac Sim.
2. Verify real Marine City is visible, not a proxy/debug city.
3. Run or execute `open_uavmarine_session_overlay_gui.py` to add the actor-only
   session layer while preserving the user's live viewport camera.
4. Export RGB/depth/pose from each UAV camera.
5. Run the selected YOLO/P2P4-SelfAttnFR detector on each UAV RGB frame.
6. Convert detections to EvidenceTokens for 3D evidence graph and AeroGraph
   reasoner testing.

## Capture And Reasoner Commands

After a scenario overlay is visually verified in Isaac, capture RGB/depth/pose
from the real base stage plus an actor-only session layer:

Inside the Isaac container, the single mounted GPU is visible as index `0` even
when the host allocated physical GPU1 to the container.

```bash
docker exec isaac-sim-gui-uav-marinecity bash -lc '
cd /isaac-sim &&
/isaac-sim/python.sh /workspace/uav_marinecity/scripts/capture_realcities_multiuav.py \
  --base-stage /workspace/uav_marinecity/uavmarine.usd \
  --actor-layer /workspace/uav_marinecity/uavmarine_multiuav_actor_overlay_s0_locked_roi.usda \
  --root /World/CoM3D_ACE_UAVMarine \
  --out-dir /workspace/uav_marinecity/outputs/isaac_exports/uavmarine_s0_viewer160_session_recapture \
  --width 1280 \
  --height 720 \
  --camera-profile viewer160 \
  --active-gpu 0 \
  --headless
'
```

For the other scenario overlays, replace the stage/out-dir pair:

- `uavmarine_multiuav_actor_overlay_s1_adjacent_overlap.usda` ->
  `outputs/isaac_exports/uavmarine_s1_viewer160_session_recapture`
- `uavmarine_multiuav_actor_overlay_s2_coastline_multiview.usda` ->
  `outputs/isaac_exports/uavmarine_s2_viewer160_session_recapture`

Run the selected detector on exported frames:

```bash
python scripts/run_marinecity_detector_smoke.py \
  --summary outputs/isaac_exports/uavmarine_s0_locked_roi/real_cesium_capture_summary.json \
  --capture-plan outputs/isaac_exports/uavmarine_s0_locked_roi/capture_plan.json \
  --weights outputs/detectors/server_yolov11_p2p4_balanced/20260610_073629_proposed_p2p4_balanced_selfattn_tiny_frelu_yolo11l_visdrone_yolov11_p2_balanced_seed123/ultralytics/weights/best.pt \
  --out-dir outputs/evidence/uavmarine_s0_detector_smoke \
  --device 1 \
  --imgsz 1280
```

Run the 3D evidence and AeroGraph Reasoner smoke test:

```bash
python scripts/run_marinecity_3d_reasoner_smoke.py \
  --scenario s0_locked_roi \
  --tokens outputs/evidence/uavmarine_s0_detector_smoke/evidence_tokens.jsonl \
  --provider rule_based \
  --out-dir outputs/reasoning/uavmarine_s0_reasoner
```

The `rule_based` provider is deterministic and good for debugging the pipeline. To use
an external web or local LLM later, install/login in the user environment and pass a CLI command
that reads the prompt from stdin and emits JSON:

```bash
python scripts/run_marinecity_3d_reasoner_smoke.py \
  --scenario s1_adjacent_overlap \
  --tokens outputs/evidence/uavmarine_s1_detector_smoke/evidence_tokens.jsonl \
  --provider command \
  --command "AEROGRAPH_COMMAND_THAT_READS_STDIN_AND_RETURNS_JSON" \
  --out-dir outputs/reasoning/uavmarine_s1_reasoner_command
```

The same runner also accepts `--provider openai` when `OPENAI_API_KEY` is set.

## Regenerate

From the repository:

```bash
bash scripts/ubuntu/deploy_uavmarine_multiuav_overlay.sh
```

This regenerates scenario overlays and copies VisDrone object textures. It does
not modify `uavmarine.usd`.
