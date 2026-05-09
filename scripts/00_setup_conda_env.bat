@echo off
setlocal
cd /d "%~dp0\.."

where conda >nul 2>nul
if errorlevel 1 (
    echo Conda was not found in PATH.
    echo Open Anaconda Prompt and run this script again, or create the env manually:
    echo conda env create -f environment.yml
    exit /b 1
)

conda env list | findstr /C:"com3d-ace" >nul 2>nul
if errorlevel 1 (
    echo Creating conda environment: com3d-ace
    conda env create -f environment.yml
) else (
    echo Updating conda environment: com3d-ace
    conda env update -n com3d-ace -f environment.yml --prune
)

echo.
echo Activate with:
echo conda activate com3d-ace
echo.
echo Then verify with:
echo python -m scripts.check_env
endlocal
