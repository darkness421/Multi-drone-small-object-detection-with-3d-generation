"""Sync project docs to Notion.

The script can run in dry-run mode without a token. Real sync requires a local
.env file with NOTION_TOKEN and NOTION_DATA_SOURCE_ID.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_NOTION = {
    "NOTION_DATABASE_URL": "https://www.notion.so/377a56f7685383748586011fd1983a90",
    "NOTION_DATA_SOURCE_URL": "collection://013a56f7-6853-834a-a96b-072eb1805f4f",
    "NOTION_DATA_SOURCE_ID": "013a56f7-6853-834a-a96b-072eb1805f4f",
    "NOTION_BOARD_VIEW_URL": "view://54ba56f7-6853-83b8-86a2-8824de7950de",
}

NOTION_VERSION = "2026-03-11"


@dataclass(frozen=True)
class NotionSection:
    name: str
    source: Path
    summary: str


SECTIONS = (
    NotionSection(
        name="Related Research",
        source=ROOT / "docs" / "paper_plan.md",
        summary="paper target, related research note, survey link",
    ),
    NotionSection(
        name="Proposed Method",
        source=ROOT / "docs" / "idea_bank.md",
        summary="method idea와 architecture note",
    ),
    NotionSection(
        name="Experiment Plan",
        source=ROOT / "docs" / "dataset_plan.md",
        summary="dataset 선정, class mapping, experiment design",
    ),
    NotionSection(
        name="Experiment Result",
        source=ROOT / "docs" / "experiment_results.md",
        summary="실험 설정, metric, output, 결과 해석",
    ),
    NotionSection(
        name="환경 및 구현 과정",
        source=ROOT / "docs" / "dev_log.md",
        summary="setup history, implementation note, environment decision",
    ),
)


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def read_preview(path: Path, max_chars: int = 500) -> str:
    if not path.exists():
        return "(missing file)"
    text = path.read_text(encoding="utf-8-sig").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n..."


def read_doc(path: Path) -> str:
    if not path.exists():
        return "(missing file)"
    return path.read_text(encoding="utf-8-sig").strip()


def notion_rich_text(text: str, limit: int = 2000) -> list[dict[str, Any]]:
    if not text:
        return []
    return [{"type": "text", "text": {"content": text[:limit]}}]


def paragraph(text: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": notion_rich_text(text)},
    }


def heading(text: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": notion_rich_text(text)},
    }


def code_block(text: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "code",
        "code": {
            "language": "markdown",
            "rich_text": notion_rich_text(text),
        },
    }


def doc_to_blocks(section: NotionSection) -> list[dict[str, Any]]:
    source_rel = section.source.relative_to(ROOT)
    doc = read_doc(section.source)
    return [
        heading("GitHub 문서 동기화"),
        paragraph(f"Section: {section.name}"),
        paragraph(f"Source: {source_rel}"),
        paragraph(f"Summary: {section.summary}"),
        code_block(doc[:1800]),
    ]


def env_value(key: str, default: str | None = None) -> str | None:
    return os.getenv(key) or DEFAULT_NOTION.get(key) or default


def notion_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def notion_request(
    method: str,
    path: str,
    token: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    request = urllib.request.Request(
        f"https://api.notion.com/v1/{path.lstrip('/')}",
        data=data,
        method=method,
        headers=notion_headers(token),
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Notion API error {error.code}: {detail}") from error


def get_data_source(token: str, data_source_id: str) -> dict[str, Any]:
    return notion_request("GET", f"data_sources/{data_source_id}", token)


def find_property_name(schema: dict[str, Any], property_type: str, names: tuple[str, ...]) -> str | None:
    properties = schema.get("properties", {})
    for name, definition in properties.items():
        if definition.get("type") == property_type and name in names:
            return name
    for name, definition in properties.items():
        if definition.get("type") == property_type:
            return name
    return None


def build_properties(schema: dict[str, Any], section: NotionSection) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    title_name = find_property_name(schema, "title", ("Name", "Title", "이름", "작업", "Task"))
    if title_name is None:
        raise RuntimeError("Notion data source에서 title 속성을 찾지 못했습니다.")

    sync_title = f"[Sync] {section.name}: {section.source.name}"
    properties[title_name] = {"title": notion_rich_text(sync_title)}

    category_name = find_property_name(schema, "select", ("Category", "Section", "분류", "카테고리"))
    if category_name is not None:
        properties[category_name] = {"select": {"name": section.name}}

    status_name = find_property_name(schema, "status", ("Status", "상태"))
    if status_name is not None:
        properties[status_name] = {"status": {"name": "Not Started"}}

    return properties


def sync_to_notion(dry_run: bool = False) -> None:
    token = os.getenv("NOTION_TOKEN")
    data_source_id = env_value("NOTION_DATA_SOURCE_ID")

    if not token:
        raise SystemExit(
            "NOTION_TOKEN이 없습니다. .env에 token을 넣은 뒤 다시 실행하세요. "
            "먼저 확인하려면 --dry-run을 사용하세요."
        )
    if not data_source_id:
        raise SystemExit("NOTION_DATA_SOURCE_ID가 없습니다. .env에 data source id를 넣어주세요.")

    schema = get_data_source(token, data_source_id)
    print(f"Connected data source: {schema.get('id', data_source_id)}")

    for section in SECTIONS:
        payload = {
            "parent": {"data_source_id": data_source_id},
            "properties": build_properties(schema, section),
            "children": doc_to_blocks(section),
        }
        if dry_run:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            continue
        response = notion_request("POST", "pages", token, payload)
        print(f"created: {section.name} -> {response.get('url', response.get('id'))}")


def dry_run() -> None:
    print("Notion sync dry-run")
    print("===================")
    print(f"Database URL: {env_value('NOTION_DATABASE_URL')}")
    print(f"Data source URL: {env_value('NOTION_DATA_SOURCE_URL')}")
    print(f"Data source ID: {env_value('NOTION_DATA_SOURCE_ID')}")
    print(f"Board view URL: {env_value('NOTION_BOARD_VIEW_URL')}")
    print(f"Public API database_id: {os.getenv('NOTION_DATABASE_ID', '(not set)')}")
    print()

    for section in SECTIONS:
        print(f"[{section.name}]")
        print(f"source: {section.source.relative_to(ROOT)}")
        print(f"summary: {section.summary}")
        print(read_preview(section.source))
        print()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Sync project docs to Notion.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned Notion updates without calling the Notion API.",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Create Notion pages from local project docs.",
    )
    parser.add_argument(
        "--api-dry-run",
        action="store_true",
        help="Read Notion schema and print create-page payloads without writing pages.",
    )
    args = parser.parse_args()

    load_env_file(ROOT / ".env")

    if args.dry_run:
        dry_run()
        return

    if args.api_dry_run:
        sync_to_notion(dry_run=True)
        return

    if args.sync:
        sync_to_notion(dry_run=False)
        return

    raise SystemExit("Use --dry-run, --api-dry-run, or --sync.")


if __name__ == "__main__":
    main()
