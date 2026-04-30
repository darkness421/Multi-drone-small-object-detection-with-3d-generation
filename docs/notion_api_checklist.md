# Notion API 자동 연동 체크리스트

이 문서는 GitHub/local 문서를 Notion 보드에 자동 저장하기 위한 준비 목록입니다.

## 현재 상태

- GitHub와 local docs는 준비됨
- Notion 보드 URL은 기록됨
- 자동 동기화 script 초안은 `scripts/sync_notion.py`에 있음
- 아직 `Notion integration token`은 없음

## 해야 할 일

1. Notion에서 새 integration을 만듭니다.
2. `Internal Integration Token`을 발급합니다.
3. `Cooperative Multi-UAV Small Object Detection` 보드 또는 database를 integration에 공유합니다.
4. `.env.example`을 복사해 `.env`를 만듭니다.
5. `.env`에 `NOTION_TOKEN`을 넣습니다.
6. 연동 도구가 요구하는 정확한 `NOTION_DATABASE_ID`를 확인합니다.
7. `scripts/sync_notion.py --dry-run`으로 먼저 어떤 항목이 생성될지 확인합니다.
8. 문제가 없으면 실제 sync를 실행합니다.

## 동기화 대상

| Notion Section | Local File |
| --- | --- |
| Related Research | `docs/paper_plan.md` |
| Proposed Method | `docs/idea_bank.md` |
| Experiment Plan | `docs/dataset_plan.md` |
| Experiment Result | `docs/experiment_results.md` |
| 환경 및 구현 과정 | `docs/dev_log.md` |

## 주의

- `.env`는 GitHub에 올리지 않습니다.
- Notion token은 화면 공유나 문서에 직접 적지 않습니다.
- 처음에는 `--dry-run`으로 확인한 뒤 실제 sync를 실행합니다.

