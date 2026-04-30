# Timeline to ACCV

- Notion Section: `환경 및 구현 과정`
- Status: `Not Started`
- Source: `docs/timeline_to_accv.md`
- Export Date: `2026-04-30`

---

# ACCV 요약 제출까지 일정

기준일: 2026-05-01  
목표일: 2026-07-05  
목표: ACCV 요약 제출용 연구 방향, baseline 결과, 방법론 개요, 실험 계획을 제출 가능한 형태로 정리합니다.

## 전체 전략

5월은 dataset과 baseline을 확정하고, 6월은 제안 방법과 실험 결과를 만드는 기간으로 둡니다. 7월 초에는 새 기능을 크게 추가하지 않고, 요약문과 그림, 핵심 결과 정리에 집중합니다.

## 주요 마일스톤

| 기간 | 목표 | 산출물 |
| --- | --- | --- |
| 2026-05-01 ~ 2026-05-10 | Dataset 확정 및 `YOLO baseline` 준비 | `VisDrone` 준비 계획, class mapping, baseline config |
| 2026-05-11 ~ 2026-05-24 | 첫 baseline 학습/평가 | `mAP`, `AP_small`, `precision`, `recall`, `FPS` 초도 결과 |
| 2026-05-25 ~ 2026-06-07 | small object 개선 모듈 설계 | patch-level feature, wavelet stem, ablation 계획 |
| 2026-06-08 ~ 2026-06-21 | Multi-UAV fusion 및 3D reasoning 구조 정리 | fusion diagram, 3D grounding 흐름, re-observation logic |
| 2026-06-22 ~ 2026-06-30 | 실험 결과 정리 및 figure 제작 | 결과표, method figure, failure case, demo screenshot 계획 |
| 2026-07-01 ~ 2026-07-05 | ACCV 요약 제출 준비 | 최종 요약문, 핵심 그림, contribution bullet, 제출 체크 |

## 주차별 계획

### Week 1: 2026-05-01 ~ 2026-05-03

- `VisDrone`을 첫 baseline dataset으로 확정합니다.
- dataset 다운로드 위치, annotation 구조, license/사용 조건을 확인합니다.
- `data/README.md`, `config/datasets/visdrone.yaml`, `scripts/prepare_visdrone.py` 구조를 준비합니다.
- Notion에는 `Experiment Plan` 카드로 dataset 선정 이유를 옮깁니다.

### Week 2: 2026-05-04 ~ 2026-05-10

- `VisDrone` annotation을 `YOLO format`으로 변환하는 스크립트를 준비합니다.
- `Ultralytics YOLO` baseline 학습 환경을 설정합니다.
- 첫 dry-run 학습 또는 작은 subset 학습을 실행합니다.
- 실패 로그와 환경 문제는 `docs/dev_log.md`에 기록합니다.

### Week 3: 2026-05-11 ~ 2026-05-17

- `YOLO baseline` 전체 학습 1차를 실행합니다.
- `mAP`, `AP_small`, `precision`, `recall`, `FPS`를 기록합니다.
- 결과는 `docs/experiment_results.md`에 `EXP-202605xx-001` 형식으로 남깁니다.

### Week 4: 2026-05-18 ~ 2026-05-24

- baseline 결과를 분석합니다.
- small object 실패 사례를 수집합니다.
- `AI-TOD`를 추가 평가 dataset으로 쓸지 확정합니다.
- 논문 contribution 후보를 3개로 압축합니다.

### Week 5: 2026-05-25 ~ 2026-05-31

- patch-level feature 또는 wavelet stem 개선 방향을 하나 선택합니다.
- baseline 대비 개선 실험 설계를 만듭니다.
- ablation 항목을 정리합니다.

### Week 6: 2026-06-01 ~ 2026-06-07

- small object 개선 모듈 1차 구현 또는 pseudo-code를 준비합니다.
- baseline과 비교 가능한 실험 설정을 맞춥니다.
- 결과가 부족하면 최소한 method figure와 실험 계획을 강하게 정리합니다.

### Week 7: 2026-06-08 ~ 2026-06-14

- Multi-UAV fusion 구조를 구체화합니다.
- UAV별 detection, camera pose, projected 3D consistency를 연결하는 pipeline diagram을 만듭니다.
- `Isaac Sim` 데모는 full implementation보다 figure/demo plan 중심으로 준비합니다.

### Week 8: 2026-06-15 ~ 2026-06-21

- 3D grounding, confidence reasoning, re-observation logic을 정리합니다.
- 제안 방법의 전체 흐름을 1장짜리 figure로 만듭니다.
- summary submission에 들어갈 contribution 문장을 다듬습니다.

### Week 9: 2026-06-22 ~ 2026-06-30

- 실험 결과표와 figure를 정리합니다.
- 실패 사례와 한계를 정리합니다.
- 요약문 초안을 작성합니다.
- 관련 연구 문단을 정리합니다.

### Final Week: 2026-07-01 ~ 2026-07-05

- 새 실험 추가를 멈추고 제출물 완성에 집중합니다.
- 제목, abstract, contribution, method summary, experiment summary를 점검합니다.
- 그림 해상도와 캡션을 확인합니다.
- 2026-07-05 제출 전 최종 체크리스트를 완료합니다.

## 제출 전 체크리스트

- [ ] 연구 제목 확정
- [ ] 핵심 contribution 3개 정리
- [ ] `YOLO baseline` 결과 최소 1개 확보
- [ ] small object 개선 방향 명확화
- [ ] Multi-UAV fusion / 3D reasoning figure 준비
- [ ] dataset 사용 근거 정리
- [ ] 한계와 다음 계획 정리
- [ ] ACCV 요약 제출 양식 확인
- [ ] 최종 제출 파일 백업
