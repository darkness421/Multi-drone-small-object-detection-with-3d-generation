# REGR: Reciprocal Evidence-Graph Refinement for Aerial Multi-Object Tracking

The current manuscript studies deterministic temporal identity refinement of frozen aerial tracklets. The paper code and experiment records are on the **[`regr-paper` branch](https://github.com/darkness421/Multi-drone-small-object-detection-with-3d-generation/tree/regr-paper)**.

- [Paper overview and scope](https://github.com/darkness421/Multi-drone-small-object-detection-with-3d-generation/tree/regr-paper#readme)
- [Implementation and reproducibility guide](https://github.com/darkness421/Multi-drone-small-object-detection-with-3d-generation/blob/regr-paper/docs/REGR_REPRODUCIBILITY.md)
- [Complete MMOT comparison](https://github.com/darkness421/Multi-drone-small-object-detection-with-3d-generation/blob/regr-paper/reproducibility/ivc_professor_review_20260914/main_comparison.csv)
- [Qualitative examples and provenance](https://github.com/darkness421/Multi-drone-small-object-detection-with-3d-generation/tree/regr-paper/reproducibility/ivc_professor_review_20260914/evidence/detector_temporal_cases)

REGR links compatible tracklets through reciprocal predecessor-successor selection while preserving boxes, classes, scores, and observation counts. The study evaluates all 50 MMOT test sequences with three upstream trackers under oracle and detector inputs. Historical result keys retain the name `com3d_reciprocal_guard`; the guide explains their correspondence to REGR.

The repository name reflects earlier multi-UAV and 3D project work. The default `main` branch retains that older scaffold; use `regr-paper` for the current manuscript. Its experiment baseline is commit `2a033849f1746604db774c95537f0400b5e513a2` on `server-baseline-pipeline`.

As of 2026-09-17 this repository is private. Anonymous reviewer access requires a public release. Raw datasets, full caches, checkpoints, and external source workspaces are not bundled.

---

<details>
<summary>Earlier project setup (legacy main-branch scaffold)</summary>

# Multi-UAV Small Object Detection

This repository contains code and configuration files for a multi-UAV small
object detection pipeline in an urban coastal scene. The project combines
geospatial scene setup, synchronized UAV camera configurations, detector-side
small-object evidence, multi-view fusion, and re-observation planning.

## Overview

The codebase is organized around the following components:

- Geospatial scene configuration for a WGS84 origin and local ENU coordinates.
- Multi-UAV mission definitions with synchronized camera viewpoints.
- Lightweight data structures for scene, pose, camera, and mission metadata.
- Configuration hooks for detector weights, multi-view fusion, and uncertainty
  handling.
- Isaac Sim notes for generating synchronized image and pose exports.

## Repository Layout

```text
config/
  marine_city_scene.yaml   # Geospatial scene and simulation settings
  uav_mission.yaml         # UAV poses, cameras, detector, and fusion settings
isaac/
  README.md                # Isaac Sim scene-generation notes
src/
  multi_uav_pipeline/
    geo.py                 # WGS84 origin and local ENU pose structures
    mission.py             # Mission, UAV, and camera configuration structures
tools/
  check_environment.ps1    # Optional local environment check script
```

## Configuration

Scene-level settings are defined in `config/marine_city_scene.yaml`. The Cesium
ion token is read from the `CESIUM_ION_TOKEN` environment variable when a Cesium
ion tileset is used.

Mission-level settings are defined in `config/uav_mission.yaml`, including UAV
starting poses, camera intrinsics, detector weight path, confidence threshold,
multi-view fusion mode, and uncertainty-driven re-observation options.

## Basic Usage

1. Review or update the scene origin and 3D Tiles source in
   `config/marine_city_scene.yaml`.
2. Review the UAV viewpoints, camera settings, and detector configuration in
   `config/uav_mission.yaml`.
3. Use the Isaac Sim workflow in `isaac/README.md` to create the scene, attach
   UAV camera rigs, and export synchronized frames with camera poses.
4. Use the structures in `src/multi_uav_pipeline/` to load mission metadata and
   pass it to downstream detection, fusion, and re-observation modules.

</details>
