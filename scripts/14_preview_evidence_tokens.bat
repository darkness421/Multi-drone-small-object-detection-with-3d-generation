@echo off
setlocal
cd /d "%~dp0\.."

set TOKENS=%1
if "%TOKENS%"=="" set TOKENS=outputs\evidence\tokens.jsonl

set OUT_DIR=%2
if "%OUT_DIR%"=="" set OUT_DIR=outputs\preview\evidence_tokens

python -m scripts.preview_evidence_tokens --tokens "%TOKENS%" --out-dir "%OUT_DIR%"
if errorlevel 1 exit /b 1

start "" "%CD%\%OUT_DIR%\index.html"
endlocal
