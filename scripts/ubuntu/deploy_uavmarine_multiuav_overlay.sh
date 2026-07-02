#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

DEPLOY_ROOT=${DEPLOY_ROOT:-/home/oem/UAV/uav_marinecity}
TEXTURE_SRC=${TEXTURE_SRC:-sim/isaac/assets/visdrone_objects}

mkdir -p "$DEPLOY_ROOT/scripts" "$DEPLOY_ROOT/outputs"

python3 scripts/build_uavmarine_multiuav_overlay.py \
  --deploy-root "$DEPLOY_ROOT" \
  --copy-textures \
  --texture-src "$TEXTURE_SRC"

python3 scripts/build_uavmarine_multiuav_overlay.py \
  --deploy-root "$DEPLOY_ROOT" \
  --all-scenarios \
  --copy-textures \
  --texture-src "$TEXTURE_SRC"

python3 scripts/build_uavmarine_multiuav_overlay.py \
  --deploy-root "$DEPLOY_ROOT" \
  --all-scenarios \
  --actor-only \
  --out uavmarine_multiuav_actor_overlay.usda \
  --copy-textures \
  --texture-src "$TEXTURE_SRC"

cp simulation/isaac/open_uavmarine_multiuav_gui.py \
  "$DEPLOY_ROOT/scripts/open_uavmarine_multiuav_gui.py"
cp simulation/isaac/capture_realcities_multiuav.py \
  "$DEPLOY_ROOT/scripts/capture_realcities_multiuav.py"

cat <<EOF
UAVMarine multi-UAV overlay deployed.

Base USD:
  $DEPLOY_ROOT/uavmarine.usd

Overlay USD to open in Isaac:
  $DEPLOY_ROOT/uavmarine_multiuav_overlay.usda

Scenario overlays:
  $DEPLOY_ROOT/uavmarine_multiuav_overlay_s0_locked_roi.usda
  $DEPLOY_ROOT/uavmarine_multiuav_overlay_s1_adjacent_overlap.usda
  $DEPLOY_ROOT/uavmarine_multiuav_overlay_s2_coastline_multiview.usda

Actor-only session overlays:
  $DEPLOY_ROOT/uavmarine_multiuav_actor_overlay_s0_locked_roi.usda
  $DEPLOY_ROOT/uavmarine_multiuav_actor_overlay_s1_adjacent_overlap.usda
  $DEPLOY_ROOT/uavmarine_multiuav_actor_overlay_s2_coastline_multiview.usda

Runtime GUI helper copied to:
  $DEPLOY_ROOT/scripts/open_uavmarine_multiuav_gui.py

Runtime capture helper copied to:
  $DEPLOY_ROOT/scripts/capture_realcities_multiuav.py

This overlay does not modify uavmarine.usd. Open the overlay to turn the
ROI/object/UAV layer on; reopen uavmarine.usd to turn it off.
EOF
