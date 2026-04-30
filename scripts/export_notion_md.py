"""Export project docs into Notion-friendly Markdown cards."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "notion_exports"


@dataclass(frozen=True)
class NotionCard:
    section: str
    title: str
    source: Path
    status: str = "Not Started"


CARDS = (
    NotionCard(
        section="Related Research",
        title="Paper Plan",
        source=ROOT / "docs" / "paper_plan.md",
    ),
    NotionCard(
        section="Proposed Method",
        title="Idea Bank",
        source=ROOT / "docs" / "idea_bank.md",
    ),
    NotionCard(
        section="Experiment Plan",
        title="Dataset Plan",
        source=ROOT / "docs" / "dataset_plan.md",
    ),
    NotionCard(
        section="Experiment Result",
        title="Experiment Results",
        source=ROOT / "docs" / "experiment_results.md",
    ),
    NotionCard(
        section="환경 및 구현 과정",
        title="Development Log",
        source=ROOT / "docs" / "dev_log.md",
    ),
    NotionCard(
        section="환경 및 구현 과정",
        title="Timeline to ACCV",
        source=ROOT / "docs" / "timeline_to_accv.md",
    ),
)


def read_markdown(path: Path) -> str:
    if not path.exists():
        return "_source file missing_"
    return path.read_text(encoding="utf-8-sig").strip()


def card_markdown(card: NotionCard) -> str:
    source_rel = card.source.relative_to(ROOT).as_posix()
    body = read_markdown(card.source)
    return "\n".join(
        [
            f"# {card.title}",
            "",
            f"- Notion Section: `{card.section}`",
            f"- Status: `{card.status}`",
            f"- Source: `{source_rel}`",
            f"- Export Date: `{date.today().isoformat()}`",
            "",
            "---",
            "",
            body,
            "",
        ]
    )


def export_cards() -> None:
    EXPORT_DIR.mkdir(exist_ok=True)
    index_lines = [
        "# Notion 붙여넣기용 Export",
        "",
        "아래 파일들은 Notion 카드에 그대로 붙여넣기 좋게 정리된 Markdown입니다.",
        "",
    ]

    for card in CARDS:
        filename = f"{card.section.replace(' ', '_')}_{card.title.replace(' ', '_')}.md"
        path = EXPORT_DIR / filename
        path.write_text(card_markdown(card), encoding="utf-8")
        index_lines.append(f"- `{card.section}`: [{card.title}]({filename})")

    (EXPORT_DIR / "README.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"Exported {len(CARDS)} Notion Markdown files to {EXPORT_DIR}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Export Notion-friendly Markdown files.")
    parser.add_argument("--export", action="store_true", help="Generate files under notion_exports/.")
    args = parser.parse_args()

    if args.export:
        export_cards()
        return

    raise SystemExit("Use --export.")


if __name__ == "__main__":
    main()
