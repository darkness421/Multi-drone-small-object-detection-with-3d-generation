@echo off
setlocal
cd /d "%~dp0\.."
python -m simulation.isaac.export_rgb_depth_pose --config configs\sim\isaac_export.yaml --dry-run
endlocal
