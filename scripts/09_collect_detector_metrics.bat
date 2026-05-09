@echo off
setlocal
cd /d "%~dp0\.."
python -m evaluation.detector_metrics_collector --metrics-dir outputs\detectors\metrics --out paper\tables\detector_frontend_comparison_filled.csv
endlocal
