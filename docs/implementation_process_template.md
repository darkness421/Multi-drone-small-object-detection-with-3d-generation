# 환경 및 구현 과정 기록 템플릿

## 목적

구현이 진행될 때 Notion의 `05 환경 및 구현 과정` 열에 붙여넣기 위한 기록 템플릿입니다.

## 기록 단위

작업 하나가 끝날 때마다 아래 형식으로 기록합니다.

```text
날짜:
작업명:
관련 모듈:
관련 commit:
실행 명령:
생성 파일:
검증 결과:
막힌 점:
다음 작업:
```

## Example

### 2026-05-07: Dummy evidence pipeline 연결

| 항목 | 내용 |
| --- | --- |
| 관련 모듈 | `pipelines`, `datasets`, `lifting3d`, `evidence_graph` |
| 관련 commit | `df896c7` |
| 실행 명령 | `python pipelines\run_dummy_evidence_pipeline.py` |
| 생성 파일 | `outputs/pipeline_dummy/*.json` |
| 검증 결과 | `python -m unittest discover tests` 통과 |
| 막힌 점 | 실제 Isaac depth/pose가 없어서 synthetic placeholder 사용 |
| 다음 작업 | graph summary/visualization 생성 |

## 구현 과정에서 계속 기록할 항목

- 환경 세팅
- dataset 준비
- Isaac Sim/Cesium 설정
- scenario generation
- annotation conversion
- 2D-to-3D lifting
- evidence graph
- reasoning/prompt
- experiment runner
- paper figure 생성

## 나중에 채울 TODO

- [ ] Isaac Sim 설치/실행 로그 추가
- [ ] Cesium tileset 설정 로그 추가
- [ ] 첫 Marine City screenshot 경로 추가
- [ ] 첫 UAV capture 결과 추가
- [ ] 첫 실험 결과 commit 연결

