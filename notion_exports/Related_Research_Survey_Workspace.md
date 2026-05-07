# Survey Workspace

- Notion Section: `Related Research`
- Status: `Not Started`
- Source: `docs/survey_workspace.md`
- Export Date: `2026-05-07`

---

# Survey Workspace

이 문서는 서베이 단계에서만 사용하는 임시 정리 공간입니다.

서베이가 끝나면 여기서 확정된 내용만 골라서 다음 문서를 새로 만듭니다.

- 최종 제안 시스템
- 세부 모듈 구조
- 수식
- dataset plan
- experiment plan
- 구현 및 환경 문서
- paper draft

## 1. Related Research

| 번호 | 논문 / 자료 | 핵심 아이디어 | 우리 연구에 주는 힌트 | 상태 |
| --- | --- | --- | --- | --- |
| 1 |  |  |  | Reading |

## 2. System Ideas

- 아직 확정하지 않습니다.
- 서베이 중 나온 아이디어를 짧게 적고, 나중에 합칠 것만 남깁니다.

## 3. Dataset Candidates

| Dataset | Type | 쓸 수 있는 이유 | 한계 | 상태 |
| --- | --- | --- | --- | --- |
| VisDrone | Real UAV | small object baseline | 3D / multi-UAV annotation 없음 | Candidate |
| AI-TOD | Aerial tiny object | tiny object stress test | UAV 시나리오와 직접 연결 약함 | Candidate |
| Isaac Sim synthetic | Synthetic | depth, pose, segmentation 생성 가능 | realism 검증 필요 | Candidate |

## 4. Experiment Ideas

- 아직 확정하지 않습니다.
- survey가 끝난 뒤 최종 제안 시스템에 맞춰 다시 설계합니다.

## 5. Decisions To Make Later

- 최종 task 정의
- main dataset / auxiliary dataset
- baseline model
- multi-UAV fusion 방식
- 3D reasoning 사용 범위
- active re-observation 실험 여부
