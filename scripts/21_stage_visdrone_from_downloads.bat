@echo off
setlocal
cd /d "%~dp0\.."

set MODE=%1
if /I "%MODE%"=="apply" (
    python -m scripts.stage_visdrone_dataset --source "%USERPROFILE%\Downloads" --raw-root data\raw\VisDrone2019-DET --apply
) else (
    python -m scripts.stage_visdrone_dataset --source "%USERPROFILE%\Downloads" --raw-root data\raw\VisDrone2019-DET
)

echo.
python -m scripts.check_dataset_readiness
endlocal
