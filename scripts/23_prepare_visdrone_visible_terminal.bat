@echo off
setlocal

set "ROOT=%~dp0\.."
set "CONDA_ACTIVATE=%USERPROFILE%\anaconda3\Scripts\activate.bat"
if not exist "%CONDA_ACTIVATE%" (
    echo Conda activate script was not found:
    echo   %CONDA_ACTIVATE%
    exit /b 1
)

set "LAUNCHER=%TEMP%\com3d_ace_prepare_visdrone.cmd"
> "%LAUNCHER%" echo @echo off
>> "%LAUNCHER%" echo cd /d "%ROOT%"
>> "%LAUNCHER%" echo call "%CONDA_ACTIVATE%" com3d-ace
>> "%LAUNCHER%" echo echo Preparing VisDrone2019-DET for CoM3D-ACE...
>> "%LAUNCHER%" echo python -m scripts.download_visdrone
>> "%LAUNCHER%" echo if errorlevel 1 goto failed
>> "%LAUNCHER%" echo scripts\01_convert_datasets.bat
>> "%LAUNCHER%" echo if errorlevel 1 goto failed
>> "%LAUNCHER%" echo scripts\10_check_training_readiness.bat
>> "%LAUNCHER%" echo if errorlevel 1 goto failed
>> "%LAUNCHER%" echo scripts\19_preview_yolo_dataset.bat configs\detector\visdrone_yolo_data.yaml train
>> "%LAUNCHER%" echo echo.
>> "%LAUNCHER%" echo echo VisDrone is ready for visible logged training:
>> "%LAUNCHER%" echo echo scripts\22_train_yolo_logged_visible_terminal.bat 100 yolo11n
>> "%LAUNCHER%" echo goto end
>> "%LAUNCHER%" echo :failed
>> "%LAUNCHER%" echo echo.
>> "%LAUNCHER%" echo echo VisDrone preparation failed. Check the messages above.
>> "%LAUNCHER%" echo :end
>> "%LAUNCHER%" echo echo.
>> "%LAUNCHER%" echo echo Press any key to close.
>> "%LAUNCHER%" echo pause

echo Opening visible VisDrone preparation terminal.
start "CoM3D-ACE VisDrone preparation" cmd.exe /k "%LAUNCHER%"
endlocal
