@echo off
setlocal
cd /d "%~dp0\.."
if not exist "outputs\evaluation\association_metrics.json" (
  call scripts\07_eval_association.bat
)
python -m evaluation.system_level_runner --association outputs\evaluation\association_metrics.json --policy outputs\core_pipeline\policy_metrics.csv --out paper\tables\system_level_comparison_filled.csv
endlocal
