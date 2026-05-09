@echo off
setlocal
cd /d "%~dp0\.."

set WEIGHTS=%1
if "%WEIGHTS%"=="" (
    echo Usage: scripts\13_eval_yolo_visdrone.bat path\to\best.pt
    exit /b 1
)

python -m scripts.check_training_readiness --data-yaml configs\detector\visdrone_yolo_data.yaml --strict
if errorlevel 1 exit /b 1

python -m detectors.train_yolo eval --model "%WEIGHTS%" --data-yaml configs\detector\visdrone_yolo_data.yaml --imgsz 1280 --name eval_visdrone
endlocal
