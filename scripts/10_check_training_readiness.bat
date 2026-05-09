@echo off
setlocal
cd /d "%~dp0\.."

python -m scripts.check_training_readiness --data-yaml configs\detector\visdrone_yolo_data.yaml configs\detector\uavdt_yolo_data.yaml
endlocal
