# Dataset 저장 규칙

이 폴더는 학습/평가 dataset을 관리하는 위치입니다. 원본 dataset과 변환된 dataset은 용량이 크기 때문에 GitHub에 올리지 않습니다.

## 폴더 구조

```text
data/
  raw/
    VisDrone/
      VisDrone2019-DET-train/
      VisDrone2019-DET-val/
      VisDrone2019-DET-test-dev/
  processed/
    visdrone_yolo/
      images/
        train/
        val/
      labels/
        train/
        val/
  external/
```

## Git 관리 원칙

- `data/raw/`: 원본 dataset 저장. Git에 올리지 않습니다.
- `data/processed/`: YOLO format 등 변환 결과 저장. Git에 올리지 않습니다.
- `data/external/`: 외부 참조 파일 또는 임시 다운로드 저장. Git에 올리지 않습니다.
- dataset 설명, 변환 규칙, config만 Git에 기록합니다.

## 첫 Baseline Dataset

첫 baseline은 `VisDrone`의 DET task를 사용합니다.

목표:

- UAV 시점의 도시 장면에서 small object detection baseline을 확보합니다.
- `Ultralytics YOLO`로 학습 가능한 `YOLO format`으로 변환합니다.
- 결과 metric은 `mAP`, `AP_small`, `precision`, `recall`, `FPS` 중심으로 기록합니다.

## VisDrone DET Annotation

VisDrone DET annotation은 이미지별 `.txt` 파일에 저장됩니다.

한 줄 형식:

```text
bbox_left,bbox_top,bbox_width,bbox_height,score,object_category,truncation,occlusion
```

변환 시 주의:

- `score`가 `0`이면 ignored box로 보고 제외합니다.
- `object_category`가 `0`이면 ignored region으로 보고 제외합니다.
- bounding box는 `(left, top, width, height)`에서 YOLO의 `(x_center, y_center, width, height)` normalized format으로 변환합니다.
- label id는 YOLO 형식에 맞춰 `0`부터 시작하도록 변환합니다.

## 참고 출처

- VisDrone DET toolkit: https://github.com/VisDrone/VisDrone2018-DET-toolkit

