# Notion 동기화 계획

이 프로젝트는 나중에 `Notion API`를 이용해 GitHub/local 개발 기록을 기존 Notion 보드와 동기화할 수 있습니다.

## Notion 보드

- Database URL: https://www.notion.so/377a56f7685383748586011fd1983a90
- Data source URL: `collection://013a56f7-6853-834a-a96b-072eb1805f4f`
- 기본 Board view: `view://54ba56f7-6853-83b8-86a2-8824de7950de`

주의: 위 값은 현재 Notion workspace에서 확인한 보드/데이터 소스/뷰 URL입니다. `Notion Public API`에서 요구하는 `database_id`는 integration 설정 화면 또는 `Copy link`에서 요구하는 형식에 맞춰 별도로 확정합니다.

## Notion View 목록

| View | URL |
| --- | --- |
| Board (By Category) | `view://54ba56f7-6853-83b8-86a2-8824de7950de` |
| Calendar | `view://307a56f7-6853-8373-9c2f-0862d48db107` |
| Table (Upcoming) | `view://f8fa56f7-6853-839d-9bdc-8815af03d4d9` |
| Table (Overdue) | `view://cf5a56f7-6853-824d-8fad-88a51af2e850` |

## 현재 Notion 보드 매핑

| Notion Section | Local File | 목적 |
| --- | --- | --- |
| Related Research | `docs/paper_plan.md` | paper target, related research note, survey link |
| Proposed Method | `docs/idea_bank.md` | method idea와 architecture note |
| Experiment Plan | `docs/dataset_plan.md` | dataset 선정, class mapping, experiment design |
| Experiment Result | `docs/experiment_results.md` | 실험 설정, metric, output, 결과 해석 |
| 환경 및 구현 과정 | `docs/dev_log.md` | setup history, implementation note, environment decision |

## 추천 자동화 흐름

1. 중요한 project note는 먼저 `docs/` 안의 Markdown 파일에 기록합니다.
2. 해당 문서를 commit/push해서 GitHub에 저장합니다.
3. 이후 Markdown 파일을 읽어 Notion database item을 업데이트하는 sync script를 추가합니다.

Sync script는 `scripts/sync_notion.py`에 있습니다. 현재 지원하는 실행 모드는 아래와 같습니다.

```powershell
python scripts\sync_notion.py --dry-run
python scripts\sync_notion.py --api-dry-run
python scripts\sync_notion.py --sync
```

`--dry-run`은 token 없이 로컬 문서 매핑만 확인합니다. `--api-dry-run`과 `--sync`는 `.env`의 `NOTION_TOKEN`이 필요합니다.

## 추후 API Sync에 필요한 것

- `Notion integration token`
- 연동 도구가 요구하는 정확한 식별자 입력값
  - 예: `database_id`, `notion_database_id`, `view_id`, `page_id`
- Notion page/database를 integration에 공유하는 권한 설정
- secret을 저장할 `.env` 파일

로컬 secret 예시:

```text
NOTION_TOKEN=...
NOTION_DATA_SOURCE_ID=013a56f7-6853-834a-a96b-072eb1805f4f
```

Notion token은 절대 GitHub에 commit하면 안 됩니다.
