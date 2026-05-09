@echo off
setlocal
cd /d "%~dp0\.."

set IMAGE_DIR=%1
if "%IMAGE_DIR%"=="" set IMAGE_DIR=data\sample_images

python -m detectors.yolo_folder_infer --weights yolo11n.pt --images "%IMAGE_DIR%" --out-jsonl outputs\evidence\tokens.jsonl --crop-dir outputs\crops
endlocal

