@echo off
setlocal
cd /d "%~dp0\.."

set IMAGE_DIR=%1
if "%IMAGE_DIR%"=="" set IMAGE_DIR=data\sample_images

set WEIGHTS=%2
if "%WEIGHTS%"=="" set WEIGHTS=yolo11n.pt

python -m detectors.infer_yolo --weights "%WEIGHTS%" --images "%IMAGE_DIR%" --out-jsonl outputs\evidence\tokens.jsonl --crop-dir outputs\crops
if errorlevel 1 exit /b 1

python -m scripts.preview_evidence_tokens --tokens outputs\evidence\tokens.jsonl --out-dir outputs\preview\evidence_tokens
if errorlevel 1 exit /b 1

start "" "%CD%\outputs\preview\evidence_tokens\index.html"
endlocal
