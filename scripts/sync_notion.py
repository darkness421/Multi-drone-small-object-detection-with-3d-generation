"""Prepare project docs for future Notion sync.

This script currently supports dry-run output only. After the Notion
integration token and API database_id are confirmed, it can be extended to
create or update Notion database items.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_NOTION = {
    "NOTION_DATABASE_URL": "https://www.notion.so/377a56f7685383748586011fd1983a90",
    "NOTION_DATA_SOURCE_URL": "collection://013a56f7-6853-834a-a96b-072eb1805f4f",
    "NOTION_BOARD_VIEW_URL": "view://54ba56f7-6853-83b8-86a2-8824de7950de",
}


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


def dry_run() -> None:
    print("Notion sync dry-run")
    print("===================")
    print(f"Database URL: {os.getenv('NOTION_DATABASE_URL', DEFAULT_NOTION['NOTION_DATABASE_URL'])}")
    print(f"Data source URL: {os.getenv('NOTION_DATA_SOURCE_URL', DEFAULT_NOTION['NOTION_DATA_SOURCE_URL'])}")
    print(f"Board view URL: {os.getenv('NOTION_BOARD_VIEW_URL', DEFAULT_NOTION['NOTION_BOARD_VIEW_URL'])}")
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
    args = parser.parse_args()

    load_env_file(ROOT / ".env")

    if args.dry_run:
        dry_run()
        return

    raise SystemExit(
        "Real Notion API sync is not enabled yet. "
        "Create a Notion integration, fill .env, then extend this script."
    )


if __name__ == "__main__":
    main()
