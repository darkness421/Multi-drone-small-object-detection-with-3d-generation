# MarineCity Cesium/Isaac Scene Plan

- Status: `ready_for_gpu_smoke_test`
- Scene: CoM3D-MarineCity (Busan Haeundae Marine City)
- USD stage: `assets/marinecity/marinecity_base.usd`
- Origin: `{'latitude_deg': 35.1569, 'longitude_deg': 129.1456, 'height_m': 160.0}`
- Objects: 10 placeholders
- UAV views: 36

## Next Smoke Test

- Load Cesium georeferenced MarineCity stage.
- Place placeholder vehicle/person/marine objects at ENU offsets.
- Spawn 2-4 UAV cameras using planned altitudes and view angles.
- Verify object ground height, camera pitch/yaw, RGB/depth/mask export paths.
- Export one short multi-view clip before full dataset generation.

## Object Placement Preview

- `mc_obj_001` sedan: E=0.0m, N=0.0m, height=160.0m
- `mc_obj_002` pickup: E=8.0m, N=2.5m, height=160.0m
- `mc_obj_003` van: E=-7.5m, N=-3.0m, height=160.0m
- `mc_obj_004` ambulance: E=14.0m, N=-2.0m, height=160.0m
- `mc_obj_005` police_car: E=-13.0m, N=4.0m, height=160.0m
- `mc_obj_006` truck: E=22.0m, N=1.5m, height=160.0m
- `mc_obj_007` pedestrian: E=-21.0m, N=-2.5m, height=160.0m
- `mc_obj_008` worker: E=3.5m, N=9.0m, height=160.0m
- `mc_obj_009` small_boat: E=-4.0m, N=-10.5m, height=160.0m
- `mc_obj_010` debris: E=18.0m, N=11.0m, height=160.0m
