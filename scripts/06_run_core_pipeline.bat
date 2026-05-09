@echo off
setlocal
cd /d "%~dp0\.."
python -m scripts.run_core_pipeline --make-dummy --tokens outputs\evidence\dummy_tokens.jsonl --out-dir outputs\core_pipeline
endlocal
