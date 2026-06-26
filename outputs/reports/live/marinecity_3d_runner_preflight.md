# MarineCity 3D Runner Preflight

Updated: `2026-06-26 13:42:09 KST`
Status: `marinecity_3d_runner_preflight_ready`
Neural runner available: `False`
Geometry smoke available: `True`

## Current Python

- Executable: `/home/oem/anaconda3/bin/python`

| Command | Path |
|---|---|
| ns-train | `None` |
| ns-process-data | `None` |
| colmap | `None` |
| instant-ngp | `None` |

| Module | Available | Error |
|---|---|---|
| nerfstudio | `False` | `ModuleNotFoundError: No module named 'nerfstudio'` |
| open3d | `False` | `ModuleNotFoundError: No module named 'open3d'` |
| plyfile | `False` | `ModuleNotFoundError: No module named 'plyfile'` |
| trimesh | `False` | `ModuleNotFoundError: No module named 'trimesh'` |
| cv2 | `False` | `ModuleNotFoundError: No module named 'cv2'` |
| numpy | `True` | `` |
| PIL | `True` | `` |

## Conda Env `com3d-ace`


| Command | Path |
|---|---|
| ns-train | `None` |
| ns-process-data | `None` |
| colmap | `None` |
| instant-ngp | `None` |

| Module | Available | Error |
|---|---|---|
| nerfstudio | `False` | `ModuleNotFoundError: No module named 'nerfstudio'` |
| open3d | `False` | `ModuleNotFoundError: No module named 'open3d'` |
| plyfile | `False` | `ModuleNotFoundError: No module named 'plyfile'` |
| trimesh | `False` | `ModuleNotFoundError: No module named 'trimesh'` |
| cv2 | `True` | `` |
| numpy | `True` | `` |
| PIL | `True` | `` |

Claiming rule: No local neural 3D runner is considered available unless ns-train, instant-ngp, or an equivalent upstream command is found. The depth point-cloud smoke only verifies geometry handoff.
