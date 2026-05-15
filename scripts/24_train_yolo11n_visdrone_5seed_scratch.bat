@echo off
setlocal
cd /d "%~dp0\.."

set EPOCHS=%1
if "%EPOCHS%"=="" set EPOCHS=100

set DEVICE=%2

python -m scripts.check_training_readiness --data-yaml configs\detector\visdrone_yolo_data.yaml --strict
if errorlevel 1 exit /b 1

python -m detectors.train_yolo_multiseed ^
  --model yolo11n.pt ^
  --method YOLOv11n ^
  --dataset VisDrone2019-DET ^
  --dataset-slug visdrone ^
  --data-yaml configs\detector\visdrone_yolo_data.yaml ^
  --epochs %EPOCHS% ^
  --imgsz 1280 ^
  --batch 8 ^
  --seeds 0,1,2,3,4 ^
  --roc-auc ^
  --project outputs\detectors ^
  --out-dir outputs\experiments\multiseed ^
  --device "%DEVICE%"

endlocal
