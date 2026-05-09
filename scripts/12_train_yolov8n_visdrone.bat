@echo off
setlocal
cd /d "%~dp0\.."

set EPOCHS=%1
if "%EPOCHS%"=="" set EPOCHS=100

python -m scripts.check_training_readiness --data-yaml configs\detector\visdrone_yolo_data.yaml --strict
if errorlevel 1 exit /b 1

python -m detectors.train_yolo train --model yolov8n.pt --data-yaml configs\detector\visdrone_yolo_data.yaml --epochs %EPOCHS% --imgsz 1280 --batch 8 --name yolov8n_visdrone
endlocal
