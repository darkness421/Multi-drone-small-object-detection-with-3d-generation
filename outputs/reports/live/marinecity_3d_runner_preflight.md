# MarineCity 3D Runner Preflight

Updated: `2026-06-28 22:26:25 KST`
Status: `marinecity_3d_runner_preflight_ready`
Neural runner available: `True`
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

## Conda Env `marinecity-nerfstudio`


| Command | Path |
|---|---|
| ns-train | `/home/oem/anaconda3/envs/marinecity-nerfstudio/bin/ns-train` |
| ns-process-data | `/home/oem/anaconda3/envs/marinecity-nerfstudio/bin/ns-process-data` |
| colmap | `None` |
| instant-ngp | `None` |

| Module | Available | Error |
|---|---|---|
| nerfstudio | `True` | `` |
| open3d | `True` | `` |
| plyfile | `True` | `` |
| trimesh | `True` | `` |
| cv2 | `True` | `` |
| numpy | `True` | `` |
| PIL | `True` | `` |

Claiming rule: No local neural 3D runner is considered available unless ns-train, instant-ngp, or an equivalent upstream command is found. The depth point-cloud smoke only verifies geometry handoff.
