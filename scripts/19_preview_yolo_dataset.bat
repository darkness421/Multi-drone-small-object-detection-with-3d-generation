@echo off
setlocal
cd /d "%~dp0\.."

set DATA_YAML=%1
if "%DATA_YAML%"=="" set DATA_YAML=configs\detector\visdrone_yolo_data.yaml

set SPLIT=%2
if "%SPLIT%"=="" set SPLIT=train

set OUT_DIR=%3
if "%OUT_DIR%"=="" set OUT_DIR=outputs\preview\yolo_dataset

python -m scripts.preview_yolo_dataset --data-yaml "%DATA_YAML%" --split "%SPLIT%" --out-dir "%OUT_DIR%"
if errorlevel 1 exit /b 1

start "" "%CD%\%OUT_DIR%\index.html"
endlocal
