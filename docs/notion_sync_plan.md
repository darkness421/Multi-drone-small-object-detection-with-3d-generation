# Notion Sync Plan

This project can sync GitHub/local development records into the existing Notion board later through the Notion API.

## Current Notion Board Mapping

| Notion Section | Local File | Purpose |
| --- | --- | --- |
| Related Research | `docs/paper_plan.md` | Paper target, related research notes, survey links |
| Proposed Method | `docs/idea_bank.md` | Method ideas and architecture notes |
| Experiment Plan | `docs/dataset_plan.md` | Dataset choices, class mapping, experiment design |
| 환경 및 구현 과정 | `docs/dev_log.md` | Setup history, implementation notes, environment decisions |

## Recommended Automation

1. Keep important project notes in Markdown inside `docs/`.
2. Commit and push those docs to GitHub.
3. Add a Notion sync script later that reads these Markdown files and updates Notion database items.

## Required For API Sync Later

- Notion integration token
- Notion database ID or page ID
- Shared access from the Notion page/database to the integration
- `.env` file containing secrets, excluded from Git

Example local secret:

```text
NOTION_TOKEN=...
NOTION_PROJECT_DATABASE_ID=...
```

Never commit Notion tokens to GitHub.

