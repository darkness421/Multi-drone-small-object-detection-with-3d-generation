# Notion 동기화 계획

이 프로젝트는 나중에 `Notion API`를 이용해 GitHub/local 개발 기록을 기존 Notion 보드와 동기화할 수 있습니다.

## Notion 보드

- Project board: https://www.notion.so/377a56f7685383748586011fd1983a90?v=54ba56f7685383b886a28824de7950de&source=copy_link
- Database/Page ID: `377a56f7685383748586011fd1983a90`
- View ID: `54ba56f7685383b886a28824de7950de`

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

## 추후 API Sync에 필요한 것

- `Notion integration token`
- `Notion database ID` 또는 `page ID`
- Notion page/database를 integration에 공유하는 권한 설정
- secret을 저장할 `.env` 파일

로컬 secret 예시:

```text
NOTION_TOKEN=...
NOTION_PROJECT_DATABASE_ID=...
```

Notion token은 절대 GitHub에 commit하면 안 됩니다.
