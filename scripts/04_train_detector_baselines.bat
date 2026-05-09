@echo off
setlocal
cd /d "%~dp0\.."

python -m scripts.run_detector_baselines --data-yaml configs\detector\visdrone_yolo_data.yaml --out outputs\detectors\detector_baseline_plan.csv
endlocal
