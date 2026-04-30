# Development Log

- Notion Section: `환경 및 구현 과정`
- Status: `Not Started`
- Source: `docs/dev_log.md`
- Export Date: `2026-04-30`

---

# 개발 로그

이 문서는 Notion에 동기화하기 전에 중요한 개발 결정과 진행 과정을 기록합니다.

## 2026-04-30

- 로컬 작업 폴더를 `C:\Users\jc\multi-uav-marine-city`로 정리했습니다.
- GitHub 저장소를 연결했습니다: `https://github.com/darkness421/multi-uav-marine-city`.
- 공개 프로젝트 이름과 코드 패키지 이름에서 학회명인 `ACCV`를 제거했습니다.
- 최종 데모 목표를 정했습니다: `Isaac Sim`에서 Marine City 배경, 다중 UAV, 카메라 뷰, detection overlay, 3D fusion, re-observation 로직을 눈으로 확인하는 형태입니다.
- `Isaac Sim` 구현 전에 dataset 선정이 먼저 필요하다고 정리했습니다.
- Notion의 `04 Experiment Result` 열과 연결할 실험 결과 기록 문서 `docs/experiment_results.md`를 추가했습니다.
- 다음 작업 순서를 정리했습니다: `VisDrone`을 첫 baseline dataset으로 잡고, `YOLO baseline` 학습/평가 구조를 준비한 뒤 `AI-TOD`, `SeaDronesSee`, `Isaac Sim synthetic data`로 확장합니다.
- 채팅에서 논의한 내용은 자동으로 Notion에 저장되지 않으므로, 중요한 결정은 `docs/` Markdown 문서에 기록한 뒤 GitHub에 push하는 방식으로 관리하기로 했습니다.
- 2026-07-05 ACCV 요약 제출을 목표로 `docs/timeline_to_accv.md`에 2026-05-01부터 2026-07-05까지의 주차별 일정을 정리했습니다.
- `VisDrone` baseline 준비를 위해 `data/README.md`, `config/datasets/visdrone.yaml`, `scripts/prepare_visdrone.py`를 추가했습니다.
