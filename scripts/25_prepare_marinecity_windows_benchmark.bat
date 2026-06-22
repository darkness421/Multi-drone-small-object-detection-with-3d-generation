@echo off
setlocal
cd /d "%~dp0\.."

if "%PYTHON%"=="" set PYTHON=python
if "%MARINECITY_CONFIG%"=="" set MARINECITY_CONFIG=configs\sim\marinecity_windows_export.yaml
if "%MARINECITY_EXPORT%"=="" set MARINECITY_EXPORT=outputs\experiments\marinecity_isaac_dry_run_manifest.json
if "%MARINECITY_PLAN%"=="" set MARINECITY_PLAN=outputs\experiments\marinecity_isaac_capture_plan.json
if "%MARINECITY_TEMPLATE%"=="" set MARINECITY_TEMPLATE=outputs\experiments\marinecity_isaac_replicator_template.py
if "%MARINECITY_BENCHMARK%"=="" set MARINECITY_BENCHMARK=outputs\experiments\marinecity_multiview_benchmark.json

echo == CoM3D-ACE MarineCity Windows dry-run export ==
echo Config:    %MARINECITY_CONFIG%
echo Manifest:  %MARINECITY_EXPORT%
echo Plan:      %MARINECITY_PLAN%
echo Template:  %MARINECITY_TEMPLATE%
echo Benchmark: %MARINECITY_BENCHMARK%
echo.

%PYTHON% -m simulation.isaac.export_rgb_depth_pose ^
  --config "%MARINECITY_CONFIG%" ^
  --out "%MARINECITY_EXPORT%" ^
  --plan-out "%MARINECITY_PLAN%" ^
  --template-out "%MARINECITY_TEMPLATE%" ^
  --dry-run ^
  --create-placeholders
if errorlevel 1 exit /b %errorlevel%

%PYTHON% -m scripts.build_marinecity_multiview_benchmark ^
  --input "%MARINECITY_EXPORT%" ^
  --out "%MARINECITY_BENCHMARK%" ^
  --val-angles side_view ^
  --test-angles rear_oblique,right_oblique
if errorlevel 1 exit /b %errorlevel%

echo.
echo Dry-run benchmark is ready.
echo   %MARINECITY_EXPORT%
echo   %MARINECITY_PLAN%
echo   %MARINECITY_TEMPLATE%
echo   %MARINECITY_BENCHMARK%
endlocal
