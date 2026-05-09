@echo off
setlocal

set "ROOT=%~dp0\.."
set "WEIGHTS=%1"
if "%WEIGHTS%"=="" (
    echo Usage: scripts\18_eval_yolo_visible_terminal.bat path\to\best.pt
    exit /b 1
)

set "CONDA_ACTIVATE=%USERPROFILE%\anaconda3\Scripts\activate.bat"
if not exist "%CONDA_ACTIVATE%" (
    echo Conda activate script was not found:
    echo   %CONDA_ACTIVATE%
    exit /b 1
)

set "LAUNCHER=%TEMP%\com3d_ace_visible_eval.cmd"
> "%LAUNCHER%" echo @echo off
>> "%LAUNCHER%" echo cd /d "%ROOT%"
>> "%LAUNCHER%" echo call "%CONDA_ACTIVATE%" com3d-ace
>> "%LAUNCHER%" echo scripts\13_eval_yolo_visdrone.bat "%WEIGHTS%"
>> "%LAUNCHER%" echo echo.
>> "%LAUNCHER%" echo echo Evaluation command finished. Press any key to close.
>> "%LAUNCHER%" echo pause

echo Opening visible evaluation terminal for %WEIGHTS%.
start "CoM3D-ACE visible eval" cmd.exe /k "%LAUNCHER%"
endlocal
