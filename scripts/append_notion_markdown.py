"""Append a small Markdown plan to a Notion page.

The Notion token can be read from stdin with --token-stdin. Avoid passing tokens
as command-line arguments because process listings can expose them.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from scripts.update_notion_status import append_blocks, bullet, extract_page_id, heading, paragraph, table_block


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_separator_row(line: str) -> bool:
    cells = split_table_row(line)
    return bool(cells) and all(set(cell.replace(" ", "")) <= {"-", ":"} for cell in cells)


def markdown_blocks(markdown: str) -> list[dict]:
    blocks: list[dict] = []
    lines = markdown.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()
        if not stripped:
            index += 1
            continue

        if stripped.startswith("|"):
            table_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index].strip())
                index += 1
            if len(table_lines) >= 2 and is_separator_row(table_lines[1]):
                headers = split_table_row(table_lines[0])
                rows = [split_table_row(row) for row in table_lines[2:]]
                blocks.append(table_block(headers, rows))
            else:
                blocks.extend(paragraph(row) for row in table_lines)
            continue

        if stripped.startswith("### "):
            blocks.append(heading(stripped[4:], 3))
        elif stripped.startswith("## "):
            blocks.append(heading(stripped[3:], 2))
        elif stripped.startswith("# "):
            blocks.append(heading(stripped[2:], 1))
        elif stripped.startswith("- "):
            blocks.append(bullet(stripped[2:]))
        else:
            blocks.append(paragraph(stripped))
        index += 1
    return blocks


def main() -> None:
    parser = argparse.ArgumentParser(description="Append a Markdown file to a Notion page.")
    parser.add_argument("--page", required=True, help="Notion page id or URL.")
    parser.add_argument("--markdown", required=True, help="Markdown file to append.")
    parser.add_argument("--token-stdin", action="store_true", help="Read the Notion token from stdin.")
    parser.add_argument("--notion-version", default="2026-03-11")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    page_id = extract_page_id(args.page)
    markdown_path = Path(args.markdown)
    blocks = markdown_blocks(markdown_path.read_text(encoding="utf-8"))
    if args.dry_run:
        print(f"Would append {len(blocks)} blocks to {page_id}.")
        return

    token = sys.stdin.readline().strip() if args.token_stdin else os.environ.get("NOTION_TOKEN", "").strip()
    if not token:
        raise SystemExit("NOTION_TOKEN is not set.")
    append_blocks(page_id, token, blocks, args.notion_version)
    print(f"Appended {len(blocks)} blocks to Notion page {page_id}.")


if __name__ == "__main__":
    main()
