@echo off
setlocal
cd /d "%~dp0\.."

python -m scripts.check_env
endlocal
