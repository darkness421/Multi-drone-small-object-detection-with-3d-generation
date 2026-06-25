#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

scenario="${1:-s0}"
case "$scenario" in
  s0|S0|locked|locked_roi)
    scenario_key="s0"
    actor_overlay="uavmarine_multiuav_actor_overlay_s0_locked_roi.usda"
    ;;
  s1|S1|adjacent|overlap)
    scenario_key="s1"
    actor_overlay="uavmarine_multiuav_actor_overlay_s1_adjacent_overlap.usda"
    ;;
  s2|S2|coastline|multiview)
    scenario_key="s2"
    actor_overlay="uavmarine_multiuav_actor_overlay_s2_coastline_multiview.usda"
    ;;
  *)
    echo "Usage: $0 [s0|s1|s2]" >&2
    exit 2
    ;;
esac

cat <<EOF
Starting real-Cesium UAVMarine overlay GUI.

Important:
- This restarts the Isaac container named isaac-sim-gui-uav-marinecity.
- It opens /home/oem/UAV/uav_marinecity/uavmarine.usd as the real Cesium base.
- It adds only this actor layer as a session sublayer: $actor_overlay.
- It does not overwrite or save uavmarine.usd.
EOF

export SESSION="${SESSION:-uav-marinecity-${scenario_key}-overlay-gui}"
export RUN_MODE=runapp
export RUNAPP_STAGE_PATH="${RUNAPP_STAGE_PATH:-}"
export RUNAPP_EXTRA_ARGS="${RUNAPP_EXTRA_ARGS:---ext-folder /isaac-sim/.local/share/ov/data/exts/v2 --enable cesium.usd.plugins --enable cesium.omniverse --/exts/cesium.omniverse/showOnStartup=false --exec /workspace/uav_marinecity/scripts/open_uavmarine_session_overlay_gui.py}"
export CONTAINER_USER="${CONTAINER_USER:-0:0}"
export COM3D_UAVMARINE_BASE_STAGE="${COM3D_UAVMARINE_BASE_STAGE:-/workspace/uav_marinecity/uavmarine.usd}"
export COM3D_UAVMARINE_ACTOR_LAYER="${COM3D_UAVMARINE_ACTOR_LAYER:-/workspace/uav_marinecity/$actor_overlay}"
export COM3D_UAVMARINE_SESSION_STATUS="${COM3D_UAVMARINE_SESSION_STATUS:-/workspace/uav_marinecity/outputs/uavmarine_session_overlay_status_${scenario_key}.json}"
export COM3D_KEEP_USER_CAMERA="${COM3D_KEEP_USER_CAMERA:-1}"
export COM3D_GEOREF_HEIGHT="${COM3D_GEOREF_HEIGHT:-160.0}"

exec bash scripts/ubuntu/start_uav_marinecity_isaac_gui.sh
