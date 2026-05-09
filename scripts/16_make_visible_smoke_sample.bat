@echo off
setlocal
cd /d "%~dp0\.."

set OUT_DIR=%1
if "%OUT_DIR%"=="" set OUT_DIR=outputs\smoke\visible_sample

python -m scripts.make_visible_smoke_sample --out-dir "%OUT_DIR%"
if errorlevel 1 exit /b 1

start "" "%CD%\%OUT_DIR%\preview\index.html"
endlocal
