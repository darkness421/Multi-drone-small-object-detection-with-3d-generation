@echo off
setlocal
cd /d "%~dp0\.."
if not exist "outputs\core_pipeline\object_hypotheses.json" (
  python -m scripts.run_core_pipeline --make-dummy --tokens outputs\evidence\dummy_tokens.jsonl --out-dir outputs\core_pipeline
)
python -m evaluation.association_eval --hypotheses outputs\core_pipeline\object_hypotheses.json --tokens outputs\evidence\dummy_tokens.jsonl --out outputs\evaluation\association_metrics.json
endlocal
