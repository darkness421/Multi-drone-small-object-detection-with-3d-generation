@echo off
setlocal
cd /d "%~dp0\.."
python scripts\convert_datasets.py --config configs\dataset_roots.yaml
endlocal
