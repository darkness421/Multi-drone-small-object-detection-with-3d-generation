@echo off
setlocal
cd /d "%~dp0\.."

if "%ISAAC_ROOT%"=="" set ISAAC_ROOT=C:\isaacsim
if "%MARINECITY_CONFIG%"=="" set MARINECITY_CONFIG=configs\sim\marinecity_windows_export.yaml
if "%MARINECITY_PLAN%"=="" set MARINECITY_PLAN=outputs\experiments\marinecity_isaac_capture_plan.json
if "%MARINECITY_TEMPLATE%"=="" set MARINECITY_TEMPLATE=outputs\experiments\marinecity_isaac_replicator_template.py

if not exist "%ISAAC_ROOT%\isaac-sim.bat" (
    echo Isaac Sim launcher was not found:
    echo   %ISAAC_ROOT%\isaac-sim.bat
    echo.
    echo Set ISAAC_ROOT to your Isaac Sim install folder, for example:
    echo   set ISAAC_ROOT=C:\Users\%USERNAME%\AppData\Local\ov\pkg\isaac_sim-*
    exit /b 1
)

if not exist "%ISAAC_ROOT%\python.bat" (
    echo Isaac Sim python.bat was not found:
    echo   %ISAAC_ROOT%\python.bat
    exit /b 1
)

echo Launching Isaac Sim GUI from %ISAAC_ROOT%
start "CoM3D-ACE Isaac Sim GUI" /D "%ISAAC_ROOT%" isaac-sim.bat

echo.
echo Starting Isaac Python smoke check in a visible terminal.
echo This verifies Isaac Replicator imports and writes the capture plan/template.
start "CoM3D-ACE Isaac Export Smoke" cmd /k ""%ISAAC_ROOT%\python.bat" "%CD%\simulation\isaac\export_rgb_depth_pose.py" --config "%CD%\%MARINECITY_CONFIG%" --plan-out "%CD%\%MARINECITY_PLAN%" --template-out "%CD%\%MARINECITY_TEMPLATE%" --isaac-smoke"

echo.
echo After the GUI loads, open the Script Editor and adapt/run:
echo   %CD%\%MARINECITY_TEMPLATE%
endlocal
