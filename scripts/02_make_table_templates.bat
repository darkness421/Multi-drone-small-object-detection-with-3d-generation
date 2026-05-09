@echo off
setlocal
cd /d "%~dp0\.."
python -m evaluation.paper_tables --out-dir paper\tables
python -m evaluation.reobservation_ablation --out paper\tables\reobservation_policy_ablation.csv
python -m evaluation.vlm_ablation --out paper\tables\selective_vlm_ablation.csv
endlocal
