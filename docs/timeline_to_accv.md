# ACCV 요약 제출까지 일정

기준일: 2026-05-01  
목표일: 2026-07-05  
목표: ACCV 요약 제출용 연구 방향, baseline 결과, 방법론 개요, 실험 계획을 제출 가능한 형태로 정리합니다.

## 전체 전략

5월은 dataset과 baseline을 확정하고, 6월은 제안 방법과 실험 결과를 만드는 기간으로 둡니다. 7월 초에는 새 기능을 크게 추가하지 않고, 요약문과 그림, 핵심 결과 정리에 집중합니다.

개발과 논문 작성은 병행합니다. 매주 개발 산출물, 실험 산출물, 논문 산출물을 하나씩 남기는 방식으로 진행합니다. 코드가 늦어져도 논문 구조와 그림은 먼저 만들고, 실험 결과는 확보되는 즉시 표와 문장에 반영합니다.

중요 기준: 2026-06-15 전후에는 서론, 관련 연구, 제안하는 방법이 최소 1차 완성되어 있어야 합니다. 6월 중순 이후에는 큰 구조를 새로 만들기보다 실험 결과, ablation, figure, abstract 압축에 집중합니다.

## 주요 마일스톤

| 기간 | 목표 | 산출물 |
| --- | --- | --- |
| 2026-05-01 ~ 2026-05-10 | Dataset 확정 및 `YOLO baseline` 준비 | `VisDrone` 준비 계획, class mapping, baseline config |
| 2026-05-11 ~ 2026-05-24 | 첫 baseline 학습/평가 | `mAP`, `AP_small`, `precision`, `recall`, `FPS` 초도 결과 |
| 2026-05-25 ~ 2026-06-07 | small object 개선 모듈 설계 및 논문 본문 1차 작성 | patch-level feature, wavelet stem, ablation 계획, Introduction/Related Work 초안 |
| 2026-06-08 ~ 2026-06-15 | 제안 방법과 핵심 본문 1차 완성 | Proposed Method 1차, fusion diagram, 3D grounding 흐름, re-observation logic |
| 2026-06-16 ~ 2026-06-21 | 본문 구조 고정 및 실험/그림 보강 | Introduction/Related Work/Method freeze, 결과표와 figure 보강 |
| 2026-06-22 ~ 2026-06-30 | 실험 결과 정리 및 figure 제작 | 결과표, method figure, failure case, demo screenshot 계획 |
| 2026-07-01 ~ 2026-07-05 | ACCV 요약 제출 준비 | 최종 요약문, 핵심 그림, contribution bullet, 제출 체크 |

## 주차별 계획

### Week 1: 2026-05-01 ~ 2026-05-03

- `VisDrone`을 첫 baseline dataset으로 확정합니다.
- dataset 다운로드 위치, annotation 구조, license/사용 조건을 확인합니다.
- `data/README.md`, `config/datasets/visdrone.yaml`, `scripts/prepare_visdrone.py` 구조를 준비합니다.
- Notion에는 `Experiment Plan` 카드로 dataset 선정 이유를 옮깁니다.

개발 산출물:

- `data/README.md`
- `config/datasets/visdrone.yaml`
- `scripts/prepare_visdrone.py` 초안

논문 산출물:

- 논문 working title 2~3개 후보
- 문제 정의 초안: 왜 UAV small object detection이 어려운지
- dataset 선정 근거 문단 초안

일일 계획:

| 날짜 | 개발 | 논문/문서 |
| --- | --- | --- |
| 2026-05-01 | dataset 폴더 구조와 VisDrone config 생성 | 문제 정의 1문단 작성 |
| 2026-05-02 | VisDrone annotation 구조 분석 | Dataset 섹션 초안 작성 |
| 2026-05-03 | YOLO format 변환 설계 | contribution 후보 3개 작성 |

### Week 2: 2026-05-04 ~ 2026-05-10

- `VisDrone` annotation을 `YOLO format`으로 변환하는 스크립트를 준비합니다.
- `Ultralytics YOLO` baseline 학습 환경을 설정합니다.
- 첫 dry-run 학습 또는 작은 subset 학습을 실행합니다.
- 실패 로그와 환경 문제는 `docs/implementation_process_template.md` 형식으로 기록합니다.

개발 산출물:

- VisDrone to YOLO 변환 스크립트 1차
- subset 학습용 dataset config
- baseline train command 기록

실험 산출물:

- subset dry-run 결과
- 학습 환경 문제 목록

논문 산출물:

- Related Work 분류표: UAV object detection, small object detection, multi-view fusion, simulation-based data
- Method overview 그림 러프 스케치

일일 계획:

| 날짜 | 개발 | 논문/문서 |
| --- | --- | --- |
| 2026-05-04 | 변환 스크립트 구현 시작 | Related Work 카테고리 정리 |
| 2026-05-05 | label 변환 검증 | VisDrone 사용 이유 정리 |
| 2026-05-06 | subset dataset 생성 | baseline protocol 문장 작성 |
| 2026-05-07 | YOLO 환경 설정 | Method figure 러프 구성 |
| 2026-05-08 | subset 학습 실행 | 실패 사례 관찰 기준 정리 |
| 2026-05-09 | 오류 수정 및 재실행 | Related Work 1차 메모 |
| 2026-05-10 | Week 2 결과 정리 | Notion용 요약 정리 |

### Week 3: 2026-05-11 ~ 2026-05-17

- `YOLO baseline` 전체 학습 1차를 실행합니다.
- `mAP`, `AP_small`, `precision`, `recall`, `FPS`를 기록합니다.
- 결과는 `docs/experiment_results.md`에 `EXP-202605xx-001` 형식으로 남깁니다.

개발 산출물:

- baseline 학습 script 또는 command
- 결과 저장 규칙
- inference sample 저장

실험 산출물:

- `YOLO baseline` 1차 결과
- class별 실패 사례 일부

논문 산출물:

- Baseline 실험 설정 문단
- 첫 결과표 템플릿
- 실패 사례 figure 후보

일일 계획:

| 날짜 | 개발 | 논문/문서 |
| --- | --- | --- |
| 2026-05-11 | 전체 학습 실행 준비 | Experiment Setup 초안 |
| 2026-05-12 | baseline 학습 실행 | 실험 표 템플릿 작성 |
| 2026-05-13 | 학습 로그 점검 | Metric 설명 문장 작성 |
| 2026-05-14 | validation 실행 | 결과 해석 메모 |
| 2026-05-15 | inference sample 생성 | 실패 사례 캡션 초안 |
| 2026-05-16 | 결과 정리 | Abstract 키워드 초안 |
| 2026-05-17 | Week 3 회고 | Notion용 실험 결과 정리 |

### Week 4: 2026-05-18 ~ 2026-05-24

- baseline 결과를 분석합니다.
- small object 실패 사례를 수집합니다.
- `AI-TOD`를 추가 평가 dataset으로 쓸지 확정합니다.
- 논문 contribution 후보를 3개로 압축합니다.

개발 산출물:

- baseline error analysis script 또는 notebook 계획
- small object sample 모음
- `AI-TOD` 도입 여부 결정

실험 산출물:

- 실패 유형 분류: 작은 크기, occlusion, dense object, motion blur, viewpoint ambiguity
- baseline 한계 요약

논문 산출물:

- Introduction 1차 초안
- Contribution 3개 확정
- Related Work 1차 초안

일일 계획:

| 날짜 | 개발 | 논문/문서 |
| --- | --- | --- |
| 2026-05-18 | baseline 결과 분석 | Introduction 구조 작성 |
| 2026-05-19 | 실패 사례 수집 | 문제 정의 보강 |
| 2026-05-20 | small object failure 분류 | Contribution 후보 정리 |
| 2026-05-21 | AI-TOD 조사/도입 판단 | Related Work 초안 |
| 2026-05-22 | 결과표 업데이트 | Contribution 3개 확정 |
| 2026-05-23 | 시각화 샘플 정리 | Abstract 1차 초안 |
| 2026-05-24 | Week 4 회고 | Notion용 요약 정리 |

### Week 5: 2026-05-25 ~ 2026-05-31

- patch-level feature 또는 wavelet stem 개선 방향을 하나 선택합니다.
- baseline 대비 개선 실험 설계를 만듭니다.
- ablation 항목을 정리합니다.
- Introduction과 Related Work를 1차 완성에 가깝게 끌어올립니다.

개발 산출물:

- 개선 모듈 설계 문서
- patch-level feature 또는 wavelet stem 구현 계획
- ablation config 초안

실험 산출물:

- ablation table 설계
- baseline 대비 비교 기준

논문 산출물:

- Introduction 2차 초안
- Related Work 2차 초안
- Proposed Method 섹션 구조
- Method figure 1차
- Ablation plan 문단

일일 계획:

| 날짜 | 개발 | 논문/문서 |
| --- | --- | --- |
| 2026-05-25 | 개선 방향 후보 비교 | Introduction 2차 작성 |
| 2026-05-26 | patch/wavelet 중 1차 선택 | Related Work 2차 작성 |
| 2026-05-27 | 구현 범위 확정 | Proposed Method outline |
| 2026-05-28 | ablation config 작성 | Method figure 구성 |
| 2026-05-29 | 실험 실행 준비 | 수식/알고리즘 표현 초안 |
| 2026-05-30 | 소규모 테스트 | Ablation plan 작성 |
| 2026-05-31 | Week 5 회고 | Introduction/Related Work 점검 |

### Week 6: 2026-06-01 ~ 2026-06-07

- small object 개선 모듈 1차 구현 또는 pseudo-code를 준비합니다.
- baseline과 비교 가능한 실험 설정을 맞춥니다.
- 결과가 부족하면 최소한 method figure와 실험 계획을 강하게 정리합니다.
- Introduction과 Related Work는 이 주 안에 1차 완성 상태로 둡니다.

개발 산출물:

- 개선 모듈 1차 구현 또는 pseudo-code
- 학습/평가 config
- baseline과 동일 조건 비교 설정

실험 산출물:

- 개선 모듈 1차 결과 또는 partial result
- 실패 시 원인 분석

논문 산출물:

- Proposed Method 1차 초안
- 방법론 그림 2차
- Introduction 1차 완성
- Related Work 1차 완성
- 실험 결과가 부족할 경우 대체 presentation strategy 정리

일일 계획:

| 날짜 | 개발 | 논문/문서 |
| --- | --- | --- |
| 2026-06-01 | 개선 모듈 구현 시작 | Proposed Method 초안 |
| 2026-06-02 | 학습 config 연결 | Introduction 완성도 점검 |
| 2026-06-03 | 작은 subset 실험 | Related Work 완성도 점검 |
| 2026-06-04 | 오류 수정 | Method 세부 설명 |
| 2026-06-05 | 비교 실험 실행 | figure 보강 |
| 2026-06-06 | 결과 정리 | 결과 해석 문장 준비 |
| 2026-06-07 | Week 6 회고 | Introduction/Related Work 1차 freeze |

### Week 7: 2026-06-08 ~ 2026-06-14

- Multi-UAV fusion 구조를 구체화합니다.
- UAV별 detection, camera pose, projected 3D consistency를 연결하는 pipeline diagram을 만듭니다.
- `Isaac Sim` 데모는 full implementation보다 figure/demo plan 중심으로 준비합니다.
- Proposed Method를 이 주 안에 1차 완성합니다.

개발 산출물:

- Multi-UAV fusion pseudo-code
- 3D grounding 입력/출력 schema
- `Isaac Sim` demo requirement 목록

실험 산출물:

- fusion logic toy example 또는 synthetic example
- 3D consistency 검증 계획

논문 산출물:

- Proposed Method 1차 완성
- Multi-UAV fusion 섹션 완성 후보
- 3D reasoning figure
- demo scenario 설명 문단

일일 계획:

| 날짜 | 개발 | 논문/문서 |
| --- | --- | --- |
| 2026-06-08 | fusion 입력/출력 정의 | Fusion section outline |
| 2026-06-09 | camera pose schema 정리 | 3D grounding 설명 |
| 2026-06-10 | toy fusion 예제 작성 | pipeline figure 수정 |
| 2026-06-11 | re-observation 조건 설계 | re-observation 문단 |
| 2026-06-12 | Isaac demo 요구사항 정리 | demo scenario 작성 |
| 2026-06-13 | pseudo-code 정리 | Method 통합 |
| 2026-06-14 | Week 7 회고 | Proposed Method 1차 freeze |

### Week 8: 2026-06-15 ~ 2026-06-21

- Introduction, Related Work, Proposed Method의 큰 구조를 고정합니다.
- 3D grounding, confidence reasoning, re-observation logic을 문장과 figure 수준에서 보강합니다.
- 제안 방법의 전체 흐름을 1장짜리 figure로 확정합니다.
- summary submission에 들어갈 contribution 문장을 다듬습니다.

개발 산출물:

- confidence reasoning 규칙 초안
- re-observation decision flow
- 최종 method pipeline 정리

실험 산출물:

- baseline + 개선 모듈 + fusion logic을 비교하는 결과표 초안
- 가능하면 qualitative example 2~3개

논문 산출물:

- Introduction/Related Work/Proposed Method freeze
- Abstract 2차
- Contribution 문장 확정
- Method figure 최종 후보

일일 계획:

| 날짜 | 개발 | 논문/문서 |
| --- | --- | --- |
| 2026-06-15 | confidence rule 정리 | Introduction/Related Work/Method freeze |
| 2026-06-16 | re-observation flow 작성 | Abstract 2차 |
| 2026-06-17 | 결과표 업데이트 | Contribution 문장 다듬기 |
| 2026-06-18 | qualitative sample 정리 | figure 캡션 작성 |
| 2026-06-19 | 남은 실험 실행 | Experiment section 초안 |
| 2026-06-20 | 결과 검토 | 요약 제출 구조 점검 |
| 2026-06-21 | Week 8 회고 | Notion용 제출 준비 요약 |

### Week 9: 2026-06-22 ~ 2026-06-30

- 실험 결과표와 figure를 정리합니다.
- 실패 사례와 한계를 정리합니다.
- 요약문 초안을 작성합니다.
- 관련 연구 문단을 정리합니다.

개발 산출물:

- 더 이상 큰 기능 추가 금지
- 결과 재현 command 정리
- 최종 output 경로 정리

실험 산출물:

- 최종 baseline 결과
- ablation 또는 partial ablation 결과
- qualitative figure 후보

논문 산출물:

- Abstract 3차
- Introduction/Method/Experiment 요약문
- 최종 figure와 table 후보

일일 계획:

| 날짜 | 개발 | 논문/문서 |
| --- | --- | --- |
| 2026-06-22 | 결과 재현 command 정리 | Abstract 3차 |
| 2026-06-23 | 최종 결과표 업데이트 | Introduction 수정 |
| 2026-06-24 | qualitative 결과 정리 | Method 압축 |
| 2026-06-25 | failure case 정리 | Experiment 문장 작성 |
| 2026-06-26 | figure 파일 정리 | Related Work 압축 |
| 2026-06-27 | 리스크 점검 | 전체 초안 연결 |
| 2026-06-28 | 보완 실험 여부 결정 | 초안 1차 리뷰 |
| 2026-06-29 | 최종 로그 정리 | 초안 수정 |
| 2026-06-30 | 제출 자료 freeze | Notion용 제출 패키지 정리 |

### Final Week: 2026-07-01 ~ 2026-07-05

- 새 실험 추가를 멈추고 제출물 완성에 집중합니다.
- 제목, abstract, contribution, method summary, experiment summary를 점검합니다.
- 그림 해상도와 캡션을 확인합니다.
- 2026-07-05 제출 전 최종 체크리스트를 완료합니다.

개발 산출물:

- 코드/결과 백업
- GitHub 최신화
- 제출 당시 commit hash 기록

논문 산출물:

- 최종 abstract
- 제출용 figure/table
- contribution bullet
- limitation 및 future work 한 줄

일일 계획:

| 날짜 | 개발 | 논문/문서 |
| --- | --- | --- |
| 2026-07-01 | 결과/코드 freeze | 최종 초안 작성 |
| 2026-07-02 | figure/table 검토 | 문장 압축 |
| 2026-07-03 | GitHub/backup 정리 | 내부 리뷰 반영 |
| 2026-07-04 | 제출 파일 점검 | 최종 proofreading |
| 2026-07-05 | 제출 commit 기록 | ACCV 요약 제출 |

## 매주 반복 루틴

| 요일 | 루틴 |
| --- | --- |
| 월요일 | 이번 주 개발 목표와 논문 목표를 3개 이하로 확정 |
| 화요일 | 구현 또는 데이터 처리 집중 |
| 수요일 | 실험 실행 및 로그 확인 |
| 목요일 | 결과 분석과 문서 반영 |
| 금요일 | 논문 문장/figure/table 정리 |
| 토요일 | 부족한 실험 보완 |
| 일요일 | GitHub push, Notion export, 다음 주 계획 정리 |

## 매일 최소 기록

매일 끝날 때 아래 4가지를 해당 작업 문서나 `docs/implementation_process_template.md` 형식에 맞춰 짧게 남깁니다.

- 오늘 한 일:
- 막힌 점:
- 내일 할 일:
- 논문에 반영할 문장/그림/결과:

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
