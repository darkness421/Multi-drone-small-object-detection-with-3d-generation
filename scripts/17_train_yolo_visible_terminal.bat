@echo off
setlocal

set "ROOT=%~dp0\.."
set "EPOCHS=%1"
if "%EPOCHS%"=="" set EPOCHS=100

set "MODEL=%2"
if "%MODEL%"=="" set MODEL=yolo11n

set "TRAIN_SCRIPT=scripts\11_train_yolo11n_visdrone.bat"
if /I "%MODEL%"=="yolov8n" set TRAIN_SCRIPT=scripts\12_train_yolov8n_visdrone.bat

set "CONDA_ACTIVATE=%USERPROFILE%\anaconda3\Scripts\activate.bat"
if not exist "%CONDA_ACTIVATE%" (
    echo Conda activate script was not found:
    echo   %CONDA_ACTIVATE%
    exit /b 1
)

set "LAUNCHER=%TEMP%\com3d_ace_visible_train.cmd"
> "%LAUNCHER%" echo @echo off
>> "%LAUNCHER%" echo cd /d "%ROOT%"
>> "%LAUNCHER%" echo call "%CONDA_ACTIVATE%" com3d-ace
>> "%LAUNCHER%" echo %TRAIN_SCRIPT% %EPOCHS%
>> "%LAUNCHER%" echo echo.
>> "%LAUNCHER%" echo echo Training command finished. Press any key to close.
>> "%LAUNCHER%" echo pause

echo Opening visible training terminal for %MODEL% with %EPOCHS% epochs.
start "CoM3D-ACE visible training" cmd.exe /k "%LAUNCHER%"
endlocal
