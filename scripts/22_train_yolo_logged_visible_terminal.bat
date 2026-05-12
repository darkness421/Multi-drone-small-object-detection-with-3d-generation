@echo off
setlocal

set "ROOT=%~dp0\.."
set "EPOCHS=%1"
if "%EPOCHS%"=="" set EPOCHS=100

set "MODEL=%2"
if "%MODEL%"=="" set MODEL=yolo11n

set "MODEL_WEIGHTS=yolo11n.pt"
set "TRAIN_SCRIPT=scripts\11_train_yolo11n_visdrone.bat"
if /I "%MODEL%"=="yolov8n" (
    set "MODEL_WEIGHTS=yolov8n.pt"
    set "TRAIN_SCRIPT=scripts\12_train_yolov8n_visdrone.bat"
)

set "CONDA_ACTIVATE=%USERPROFILE%\anaconda3\Scripts\activate.bat"
if not exist "%CONDA_ACTIVATE%" (
    echo Conda activate script was not found:
    echo   %CONDA_ACTIVATE%
    exit /b 1
)

set "LAUNCHER=%TEMP%\com3d_ace_logged_visible_train.cmd"
> "%LAUNCHER%" echo @echo off
>> "%LAUNCHER%" echo setlocal
>> "%LAUNCHER%" echo cd /d "%ROOT%"
>> "%LAUNCHER%" echo call "%CONDA_ACTIVATE%" com3d-ace
>> "%LAUNCHER%" echo echo Starting tracked visible training for %MODEL%...
>> "%LAUNCHER%" echo for /f "delims=" %%%%R in ('python -m scripts.track_training_experiment start --model %MODEL_WEIGHTS% --dataset VisDrone2019-DET --epochs %EPOCHS% --imgsz 1280 --batch 8 --data-yaml configs\detector\visdrone_yolo_data.yaml --command "%TRAIN_SCRIPT% %EPOCHS%" --notes "Visible training terminal launched from scripts\22_train_yolo_logged_visible_terminal.bat" --print-run-id') do set "RUN_ID=%%%%R"
>> "%LAUNCHER%" echo echo Experiment run id: %%RUN_ID%%
>> "%LAUNCHER%" echo %TRAIN_SCRIPT% %EPOCHS%
>> "%LAUNCHER%" echo if errorlevel 1 ^(
>> "%LAUNCHER%" echo     set "RUN_STATUS=failed"
>> "%LAUNCHER%" echo ^) else ^(
>> "%LAUNCHER%" echo     set "RUN_STATUS=completed"
>> "%LAUNCHER%" echo ^)
>> "%LAUNCHER%" echo python -m scripts.track_training_experiment finish --run-id %%RUN_ID%% --status %%RUN_STATUS%% --detector-root outputs\detectors
>> "%LAUNCHER%" echo echo.
>> "%LAUNCHER%" echo echo Training finished with status %%RUN_STATUS%%.
>> "%LAUNCHER%" echo echo Experiment record: outputs\experiments\%%RUN_ID%%\experiment.md
>> "%LAUNCHER%" echo echo Index CSV: outputs\experiments\training_experiment_index.csv
>> "%LAUNCHER%" echo echo.
>> "%LAUNCHER%" echo echo Press any key to close.
>> "%LAUNCHER%" echo pause

echo Opening tracked visible training terminal for %MODEL% with %EPOCHS% epochs.
start "CoM3D-ACE tracked training" cmd.exe /k "%LAUNCHER%"
endlocal
