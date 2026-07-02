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
