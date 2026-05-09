@echo off
setlocal

if "%ISAAC_ROOT%"=="" set ISAAC_ROOT=C:\isaacsim

if not exist "%ISAAC_ROOT%\isaac-sim.bat" (
    echo Isaac Sim launcher was not found:
    echo   %ISAAC_ROOT%\isaac-sim.bat
    echo.
    echo Set ISAAC_ROOT to your Isaac Sim install folder, for example:
    echo   set ISAAC_ROOT=C:\Users\jc\AppData\Local\ov\pkg\isaac_sim-*
    exit /b 1
)

echo Launching Isaac Sim GUI from %ISAAC_ROOT%
start "CoM3D-ACE Isaac Sim" /D "%ISAAC_ROOT%" isaac-sim.bat
endlocal
