# Notion 기록 방식

이 프로젝트는 당분간 `Notion API` 자동 연동을 사용하지 않습니다. 대신 GitHub/local Markdown 문서를 기준 기록으로 관리하고, 필요한 내용만 Notion에 직접 골라 붙여넣습니다.

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
| Proposed Method | `docs/method_pipeline_card.md` | method idea와 architecture note |
| Experiment Plan | `docs/dataset_plan.md` | dataset 선정, class mapping, experiment design |
| Experiment Result | `docs/experiment_results.md` | 실험 설정, metric, output, 결과 해석 |
| 환경 및 구현 과정 | `docs/implementation_process_template.md` | setup history, implementation note, environment decision |

## 추천 기록 흐름

1. 중요한 project note는 먼저 `docs/` 안의 Markdown 파일에 기록합니다.
2. 해당 문서를 commit/push해서 GitHub에 저장합니다.
3. `scripts/export_notion_md.py`로 Notion에 붙여넣기 좋은 Markdown 파일을 생성합니다.
4. 생성된 파일 중 필요한 것만 Notion 카드에 복사합니다.

Export script는 `scripts/export_notion_md.py`에 있습니다.

```powershell
python scripts\export_notion_md.py --export
```

생성 결과는 `notion_exports/` 폴더에 저장됩니다.

## API Sync를 보류하는 이유

- 아직 Notion 보드 속성과 카드 구조가 계속 바뀔 수 있습니다.
- 자동 sync는 중복 카드나 잘못된 section 업데이트를 만들 수 있습니다.
- 지금은 GitHub 문서를 공식 기록으로 두고, Notion에는 선별해서 옮기는 방식이 안전합니다.
