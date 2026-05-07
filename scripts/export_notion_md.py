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
        title="Ambiguity-centric 3D object detection pipeline",
        source=ROOT / "docs" / "method_pipeline_card.md",
    ),
    NotionCard(
        section="Proposed Method",
        title="CoM3D-ACE System Specification",
        source=ROOT / "NOTION_SYSTEM_SPEC.md",
    ),
    NotionCard(
        section="Proposed Method",
        title="최종 제안 시스템 그림 수정 템플릿",
        source=ROOT / "docs" / "final_system_figure_template.md",
    ),
    NotionCard(
        section="Proposed Method",
        title="모듈별 그림 및 수식 정리 템플릿",
        source=ROOT / "docs" / "module_figures_formulas_template.md",
    ),
    NotionCard(
        section="Experiment Plan",
        title="Dataset Plan",
        source=ROOT / "docs" / "dataset_plan.md",
    ),
    NotionCard(
        section="Experiment Plan",
        title="Experiment Design Matrix",
        source=ROOT / "docs" / "experiment_design_matrix.md",
    ),
    NotionCard(
        section="Experiment Result",
        title="실험 결과 템플릿",
        source=ROOT / "docs" / "experiment_result_template_card.md",
    ),
    NotionCard(
        section="환경 및 구현 과정",
        title="PROJECT_PLAN",
        source=ROOT / "PROJECT_PLAN.md",
    ),
    NotionCard(
        section="환경 및 구현 과정",
        title="환경 및 구현 과정 기록 템플릿",
        source=ROOT / "docs" / "implementation_process_template.md",
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
    for old_file in EXPORT_DIR.glob("*.md"):
        old_file.unlink()

    index_lines = [
        "# Notion 붙여넣기용 Export",
        "",
        "아래 파일만 Notion 보드에 붙여넣는 것을 추천합니다.",
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
