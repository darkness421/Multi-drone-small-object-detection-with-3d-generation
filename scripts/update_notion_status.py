"""Append detector experiment status to a Notion page.

The Notion integration token is read from NOTION_TOKEN. Do not pass it on the
command line because command arguments can show up in process listings.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import textwrap
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from mimetypes import guess_type
from pathlib import Path
from typing import Any


DEFAULT_NOTION_VERSION = "2026-03-11"
RICH_TEXT_LIMIT = 1900
DEFAULT_IMAGE_PATHS = ",".join(
    [
        "outputs/reports/server_with_proposed/figures/server_baseline_dashboard.png",
        "outputs/reports/server_with_proposed/figures/ap_ap50_by_model.png",
        "outputs/reports/server_with_proposed/figures/precision_recall_f1_by_model.png",
        "outputs/reports/server_with_proposed/figures/seed_ap_distribution_by_model.png",
        "outputs/reports/server_with_proposed/figures/params_vs_ap.png",
        "outputs/reports/server_with_proposed/figures/gflops_vs_ap.png",
        "outputs/reports/live/large_20260524_140922_server_baseline_dashboard.png",
    ]
)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_csv_list(paths: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in paths.split(","):
        item = item.strip()
        if item:
            rows.extend(read_csv(Path(item)))
    return rows


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt(value: Any, digits: int = 4) -> str:
    parsed = as_float(value)
    if parsed is None:
        return "-"
    return f"{parsed:.{digits}f}"


def fmt_params(value: Any) -> str:
    parsed = as_float(value)
    if parsed is None:
        return "-"
    return f"{parsed / 1_000_000:.2f}M"


def short_path(path: str | Path) -> str:
    return Path(path).as_posix()


def extract_page_id(value: str) -> str:
    """Accept a Notion URL or page id and return a dashed UUID-like id."""

    candidate = value.strip()
    if not candidate:
        raise ValueError("empty Notion page id/url")
    parsed = urllib.parse.urlparse(candidate)
    text = parsed.path if parsed.scheme else candidate
    matches = re.findall(r"([0-9a-fA-F]{32})", text.replace("-", ""))
    if not matches:
        raise ValueError(f"could not find a 32-character Notion page id in: {value}")
    raw = matches[-1].lower()
    return f"{raw[:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:]}"


def best_rows(summary_rows: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
    rows = [row for row in summary_rows if as_float(row.get("best_AP_mean")) is not None]
    rows.sort(key=lambda row: as_float(row.get("best_AP_mean")) or -1, reverse=True)
    return rows[:limit]


def dedupe_summary_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    best: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        key = (row.get("dataset", ""), row.get("method") or row.get("model") or "")
        old = best.get(key)
        old_score = as_float(old.get("best_AP_mean")) if old else None
        new_score = as_float(row.get("best_AP_mean"))
        if old is None or (new_score is not None and (old_score is None or new_score > old_score)):
            best[key] = row
    return list(best.values())


def model_scale(row: dict[str, str]) -> str:
    return row.get("model_scale") or row.get("name_size_tag") or row.get("param_size_group") or "unknown"


def best_by_scale(summary_rows: list[dict[str, str]]) -> list[tuple[str, dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = {}
    for row in summary_rows:
        if as_float(row.get("best_AP_mean")) is None:
            continue
        groups.setdefault(model_scale(row), []).append(row)
    rows: list[tuple[str, dict[str, str]]] = []
    for scale in ["nano", "small", "medium", "large"]:
        candidates = groups.get(scale, [])
        if not candidates:
            continue
        candidates.sort(key=lambda row: as_float(row.get("best_AP_mean")) or -1, reverse=True)
        rows.append((scale, candidates[0]))
    return rows


def large_anchor_rows(summary_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = [
        row
        for row in summary_rows
        if model_scale(row) == "large" or (row.get("method") or "").lower().endswith("l")
    ]
    rows.sort(key=lambda row: as_float(row.get("best_AP_mean")) or -1, reverse=True)
    return rows


def proposed_rows(summary_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = [row for row in summary_rows if row.get("is_proposed") == "true" or (row.get("method") or "").startswith("Proposed-")]
    rows.sort(key=lambda row: as_float(row.get("best_AP_mean")) or -1, reverse=True)
    return rows


def comparison_rows(summary_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = [row for row in summary_rows if row not in proposed_rows(summary_rows)]
    rows.sort(key=lambda row: as_float(row.get("best_AP_mean")) or -1, reverse=True)
    return rows


def top3_command_rows(path: Path) -> list[dict[str, str]]:
    rows = read_csv(path)
    wanted = []
    for row in rows:
        wanted.append(
            {
                "method": row.get("method", "-"),
                "base_model": row.get("base_model", "-"),
                "ablation": row.get("ablation", "-"),
                "seed": row.get("seed", "-"),
                "status": row.get("status", "-"),
            }
        )
    return wanted


def parse_plan(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    rows: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in lines:
        step_match = re.match(r"^## Step (\d+)\.\s+(.+)$", line)
        if step_match:
            current = {"step": step_match.group(1), "title": step_match.group(2), "status": "-"}
            rows.append(current)
            continue
        if current:
            status_match = re.match(r"^Status:\s*(.+)$", line)
            if status_match:
                current["status"] = status_match.group(1).rstrip(".")
    return rows


def latest_incomplete(results_rows: list[dict[str, str]]) -> dict[str, str] | None:
    incomplete = [row for row in results_rows if row.get("status") != "completed"]
    if not incomplete:
        return None
    incomplete.sort(key=lambda row: row.get("run_dir", ""))
    return incomplete[-1]


def bullet(text: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": rich_text(text)},
    }


def heading(text: str, level: int = 2) -> dict[str, Any]:
    block_type = f"heading_{level}"
    return {
        "object": "block",
        "type": block_type,
        block_type: {"rich_text": rich_text(text)},
    }


def paragraph(text: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": rich_text(text)},
    }


def rich_text(text: str) -> list[dict[str, Any]]:
    chunks = textwrap.wrap(
        text,
        width=RICH_TEXT_LIMIT,
        replace_whitespace=False,
        drop_whitespace=False,
        break_long_words=True,
        break_on_hyphens=False,
    )
    if not chunks:
        chunks = [""]
    return [{"type": "text", "text": {"content": chunk}} for chunk in chunks]


def table_cell(text: Any) -> list[dict[str, Any]]:
    return rich_text(str(text))


def table_block(headers: list[str], rows: list[list[Any]]) -> dict[str, Any]:
    all_rows = [headers] + rows
    return {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": len(headers),
            "has_column_header": True,
            "has_row_header": False,
            "children": [
                {
                    "object": "block",
                    "type": "table_row",
                    "table_row": {"cells": [table_cell(cell) for cell in row]},
                }
                for row in all_rows
            ],
        },
    }


def result_tables(summary_rows: list[dict[str, str]], args: argparse.Namespace) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    scale_rows = best_by_scale(summary_rows)
    if scale_rows:
        blocks.append(heading("Best By Model Scale", 3))
        blocks.append(
            table_block(
                ["Scale", "Best Model", "Seeds", "AP", "AP50", "F1", "Params"],
                [
                    [
                        scale,
                        row.get("method") or row.get("model") or "-",
                        row.get("seeds") or row.get("seed_count") or "-",
                        fmt(row.get("best_AP_mean")),
                        fmt(row.get("best_AP50_mean")),
                        fmt(row.get("best_F1_mean")),
                        fmt_params(row.get("Params_mean")),
                    ]
                    for scale, row in scale_rows
                ],
            )
        )

    top_rows = best_rows(summary_rows, args.top_k)
    if top_rows:
        blocks.append(heading("Detector Leaderboard", 3))
        blocks.append(
            table_block(
                ["Rank", "Method", "Scale", "Seeds", "AP", "AP50", "Precision", "Recall", "F1", "Params", "GFLOPs"],
                [
                    [
                        index,
                        row.get("method") or row.get("model") or "-",
                        model_scale(row),
                        row.get("seed_count") or "-",
                        fmt(row.get("best_AP_mean")),
                        fmt(row.get("best_AP50_mean")),
                        fmt(row.get("best_precision_mean")),
                        fmt(row.get("best_recall_mean")),
                        fmt(row.get("best_F1_mean")),
                        fmt_params(row.get("Params_mean")),
                        fmt(row.get("GFLOPs_mean"), 1),
                    ]
                    for index, row in enumerate(top_rows, start=1)
                ],
            )
        )

    anchors = large_anchor_rows(summary_rows)[:8]
    if anchors:
        blocks.append(heading("Large Anchor Status", 3))
        blocks.append(
            table_block(
                ["Method", "Seeds", "AP", "AP50", "F1", "Params", "Notes"],
                [
                    [
                        row.get("method") or row.get("model") or "-",
                        row.get("seeds") or row.get("seed_count") or "-",
                        fmt(row.get("best_AP_mean")),
                        fmt(row.get("best_AP50_mean")),
                        fmt(row.get("best_F1_mean")),
                        fmt_params(row.get("Params_mean")),
                        "complete" if row.get("seed_count") == "3" else "partial/live",
                    ]
                    for row in anchors
                ],
            )
        )

    proposed = proposed_rows(summary_rows)[:6]
    if proposed:
        blocks.append(heading("Proposed Detector Check", 3))
        blocks.append(
            table_block(
                ["Method", "Ablation", "Seeds", "AP", "AP50", "F1", "Gate Note"],
                [
                    [
                        row.get("method") or "-",
                        row.get("ablation") or row.get("proposed_module") or "-",
                        row.get("seed_count") or "-",
                        fmt(row.get("best_AP_mean")),
                        fmt(row.get("best_AP50_mean")),
                        fmt(row.get("best_F1_mean")),
                        "YOLO11s-only candidates did not pass the current baseline gate",
                    ]
                    for row in proposed
                ],
            )
        )
    return blocks


def plan_blocks(args: argparse.Namespace) -> list[dict[str, Any]]:
    rows = parse_plan(Path(args.plan_md))
    if not rows:
        return []
    return [
        heading("Experiment Plan", 3),
        table_block(
            ["Step", "Experiment Stage", "Status"],
            [[row["step"], row["title"], row["status"]] for row in rows],
        ),
    ]


def image_block(file_upload_id: str, caption: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "image",
        "image": {
            "type": "file_upload",
            "file_upload": {"id": file_upload_id},
            "caption": rich_text(caption),
        },
    }


def build_blocks(args: argparse.Namespace) -> list[dict[str, Any]]:
    summary_rows = dedupe_summary_rows(read_csv_list(args.summary_csv))
    results_rows = read_csv(Path(args.results_csv))
    stage_gate = read_json(Path(args.stage_gate_json))
    generated = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")

    blocks: list[dict[str, Any]] = [
        heading(args.title or f"Detector Experiment Result - {generated}", 2),
    ]

    current = latest_incomplete(results_rows)
    if current:
        blocks.extend(
            [
                paragraph("Current live collection shows an incomplete or running detector row."),
                bullet(
                    "Current run: "
                    f"{current.get('method') or current.get('model') or '-'}, "
                    f"seed {current.get('seed') or '-'}, "
                    f"dataset {current.get('dataset') or '-'}, "
                    f"epoch {current.get('final_epoch') or '-'} / {current.get('protocol_epochs') or '-'}, "
                    f"batch {current.get('protocol_batch') or '-'}."
                ),
                bullet(
                    "Best checkpoint so far for that row: "
                    f"AP {fmt(current.get('best_AP'))}, AP50 {fmt(current.get('best_AP50'))}, "
                    f"F1 {fmt(current.get('best_F1'))}."
                ),
            ]
        )
    else:
        blocks.append(paragraph("No incomplete detector rows were found in the selected results CSV."))

    blocks.extend(result_tables(summary_rows, args))

    if stage_gate:
        blocks.append(heading("Stage Gate", 3))
        blocks.append(
            bullet(
                "Recommended next stage: "
                f"{stage_gate.get('recommended_next_stage', 'not generated')} "
                f"({stage_gate.get('dataset', 'all datasets')})."
            )
        )
        rationale = stage_gate.get("rationale")
        if rationale:
            blocks.append(bullet(f"Rationale: {rationale}"))

    blocks.append(heading("Next Actions", 3))
    for item in args.next_action:
        blocks.append(bullet(item))

    blocks.extend(plan_blocks(args))

    return blocks


def build_proposed_blocks(args: argparse.Namespace) -> list[dict[str, Any]]:
    summary_rows = dedupe_summary_rows(read_csv_list(args.summary_csv))
    proposed = proposed_rows(summary_rows)
    comparisons = comparison_rows(summary_rows)
    generated = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    best_proposed = proposed[0] if proposed else None
    best_comparison = comparisons[0] if comparisons else None

    blocks: list[dict[str, Any]] = [
        heading(args.title or f"Proposed Method Update - {generated}", 2),
        paragraph(
            "Gate definition: notify when the best proposed detector has higher AP than every comparison model "
            "and does not lose AP50 against the best AP50 comparison model."
        ),
    ]
    if best_proposed and best_comparison:
        ap_delta = (as_float(best_proposed.get("best_AP_mean")) or 0.0) - (as_float(best_comparison.get("best_AP_mean")) or 0.0)
        blocks.append(
            paragraph(
                f"Current status: not yet. Best proposed is {best_proposed.get('method')} "
                f"with AP {fmt(best_proposed.get('best_AP_mean'))}; best comparison is {best_comparison.get('method')} "
                f"with AP {fmt(best_comparison.get('best_AP_mean'))}. Current AP gap is {ap_delta:.4f}."
            )
        )

    if proposed:
        blocks.append(heading("Completed Proposed Ablations", 3))
        blocks.append(
            table_block(
                ["Method", "Module", "Seeds", "AP", "AP50", "Recall", "F1", "Params"],
                [
                    [
                        row.get("method") or "-",
                        row.get("ablation") or row.get("proposed_module") or "-",
                        row.get("seed_count") or "-",
                        fmt(row.get("best_AP_mean")),
                        fmt(row.get("best_AP50_mean")),
                        fmt(row.get("best_recall_mean")),
                        fmt(row.get("best_F1_mean")),
                        fmt_params(row.get("Params_mean")),
                    ]
                    for row in proposed[:8]
                ],
            )
        )

    if comparisons:
        blocks.append(heading("Current Models To Beat", 3))
        blocks.append(
            table_block(
                ["Rank", "Comparison", "Scale", "Seeds", "AP", "AP50", "F1"],
                [
                    [
                        index,
                        row.get("method") or row.get("model") or "-",
                        model_scale(row),
                        row.get("seed_count") or "-",
                        fmt(row.get("best_AP_mean")),
                        fmt(row.get("best_AP50_mean")),
                        fmt(row.get("best_F1_mean")),
                    ]
                    for index, row in enumerate(comparisons[:8], start=1)
                ],
            )
        )

    queued = top3_command_rows(Path(args.top3_command_csv))
    if queued:
        blocks.append(heading("Next Proposed Screening Queue", 3))
        blocks.append(
            table_block(
                ["Method", "Backbone", "Module", "Seed", "Status"],
                [[row["method"], row["base_model"], row["ablation"], row["seed"], row["status"]] for row in queued],
            )
        )

    blocks.append(heading("Decision", 3))
    blocks.append(bullet("Old YOLO11s proposed variants did not pass the baseline gate."))
    blocks.append(bullet("Run the top-3 proposed screening after the active large-anchor queue finishes."))
    blocks.append(bullet("If a proposed variant overwhelms all comparisons, freeze it and move to detector-to-graph transfer and UAVDT validation."))
    return blocks


def append_blocks(page_id: str, token: str, blocks: list[dict[str, Any]], notion_version: str) -> None:
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    for start in range(0, len(blocks), 100):
        payload = json.dumps({"children": blocks[start : start + 100]}).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=payload,
            method="PATCH",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Notion-Version": notion_version,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                response.read()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Notion API error {exc.code}: {body}") from exc


def create_database_page(
    database_id: str,
    token: str,
    blocks: list[dict[str, Any]],
    properties: dict[str, Any],
    notion_version: str,
) -> str:
    url = "https://api.notion.com/v1/pages"
    payload = json.dumps(
        {
            "parent": {"database_id": database_id},
            "properties": properties,
            "children": blocks[:100],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": notion_version,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data["id"]
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Notion API error {exc.code}: {body}") from exc


def notion_json_request(
    url: str,
    token: str,
    notion_version: str,
    payload: dict[str, Any] | None = None,
    method: str = "POST",
) -> dict[str, Any]:
    data = json.dumps(payload or {}).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": notion_version,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Notion API error {exc.code}: {body}") from exc


def page_title(page: dict[str, Any]) -> str:
    for prop in (page.get("properties") or {}).values():
        if prop.get("type") == "title":
            return "".join(item.get("plain_text", "") for item in prop.get("title", []))
    return ""


def query_database(database_id: str, token: str, notion_version: str, page_size: int = 100) -> list[dict[str, Any]]:
    data = notion_json_request(
        f"https://api.notion.com/v1/databases/{database_id}/query",
        token,
        notion_version,
        {"page_size": page_size},
    )
    return data.get("results", [])


def list_database_pages(database_id: str, token: str, notion_version: str) -> None:
    for page in query_database(database_id, token, notion_version):
        props = page.get("properties") or {}
        category = ((props.get("Category") or {}).get("select") or {}).get("name", "-")
        status = ((props.get("Status") or {}).get("status") or {}).get("name", "-")
        print(f"{page.get('id')} | {page_title(page)} | category={category} | status={status}")


def find_database_page(database_id: str, token: str, notion_version: str, title_query: str) -> str:
    query = title_query.casefold()
    matches = [page for page in query_database(database_id, token, notion_version) if query in page_title(page).casefold()]
    if not matches:
        raise RuntimeError(f"No Notion database page title contains: {title_query}")
    if len(matches) > 1:
        titles = "\n".join(f"- {page.get('id')} | {page_title(page)}" for page in matches)
        raise RuntimeError(f"Multiple Notion pages match {title_query!r}:\n{titles}")
    return str(matches[0]["id"])


def upload_file(path: Path, token: str, notion_version: str) -> str:
    content_type = guess_type(path.name)[0] or "application/octet-stream"
    upload = notion_json_request(
        "https://api.notion.com/v1/file_uploads",
        token,
        notion_version,
        {"mode": "single_part", "filename": path.name, "content_type": content_type},
    )
    upload_url = upload["upload_url"]
    boundary = f"----codexnotion{datetime.now().timestamp():.0f}".replace(".", "")
    file_bytes = path.read_bytes()
    body = b"".join(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'.encode("utf-8"),
            f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
            file_bytes,
            f"\r\n--{boundary}--\r\n".encode("utf-8"),
        ]
    )
    request = urllib.request.Request(
        upload_url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": notion_version,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            response.read()
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Notion file upload error {exc.code}: {body_text}") from exc
    return upload["id"]


def upload_image_blocks(paths: str, token: str, notion_version: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for item in paths.split(","):
        path = Path(item.strip())
        if not path.exists() or path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
            continue
        upload_id = upload_file(path, token, notion_version)
        blocks.append(image_block(upload_id, short_path(path)))
    return blocks


def database_properties(args: argparse.Namespace) -> dict[str, Any]:
    now = datetime.now().astimezone()
    summary_rows = dedupe_summary_rows(read_csv_list(args.summary_csv))
    results_rows = read_csv(Path(args.results_csv))
    current = latest_incomplete(results_rows)
    top = proposed_rows(summary_rows)[:1] if args.focus == "proposed" else best_rows(summary_rows, 1)
    current_text = "No active row found."
    if current:
        current_text = (
            f"{current.get('method') or current.get('model') or '-'} seed {current.get('seed') or '-'} "
            f"epoch {current.get('final_epoch') or '-'} / {current.get('protocol_epochs') or '-'}"
        )
    finding_text = "No completed summary rows found."
    if top:
        row = top[0]
        finding_text = (
            f"{'Best proposed' if args.focus == 'proposed' else 'Top row'}: {row.get('method') or row.get('model') or '-'} "
            f"AP {fmt(row.get('best_AP_mean'))}, AP50 {fmt(row.get('best_AP50_mean'))}."
        )
    scale_rows = best_by_scale(summary_rows)
    if scale_rows:
        finding_text += " Best by scale: " + "; ".join(
            f"{scale}={row.get('method') or row.get('model') or '-'} AP {fmt(row.get('best_AP_mean'))}"
            for scale, row in scale_rows
        )
    return {
        "Title": {"title": [{"type": "text", "text": {"content": args.title or f"{'Proposed Method Update' if args.focus == 'proposed' else 'Detector Experiment Result'} - {now:%Y-%m-%d %H:%M}"}}]},
        "Date": {"date": {"start": now.date().isoformat()}},
        "Status": {"status": {"name": args.status}},
        "Research Type": {"multi_select": [{"name": args.research_type}]},
        "Idea Source": {"select": {"name": args.idea_source}},
        "Category": {"select": {"name": args.category}},
        "Priority": {"select": {"name": args.priority}},
        "Description": {"rich_text": [{"type": "text", "text": {"content": current_text[:1900]}}]},
        "Key Findings": {"rich_text": [{"type": "text", "text": {"content": finding_text[:1900]}}]},
        "Next Steps": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": "; ".join(args.next_action)[:1900]},
                }
            ]
        },
    }


def notion_request(url: str, token: str, notion_version: str) -> tuple[int, str]:
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": notion_version,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def inspect_target(page_id: str, token: str, notion_version: str) -> None:
    for label, url in [
        ("page", f"https://api.notion.com/v1/pages/{page_id}"),
        ("database", f"https://api.notion.com/v1/databases/{page_id}"),
        ("block", f"https://api.notion.com/v1/blocks/{page_id}"),
    ]:
        status, body = notion_request(url, token, notion_version)
        if status >= 400:
            print(f"{label}: HTTP {status} {body[:500]}")
            continue
        data = json.loads(body)
        summary = {
            "object": data.get("object"),
            "id": data.get("id"),
            "type": data.get("type"),
            "parent": data.get("parent"),
            "properties": {
                name: {
                    "type": prop.get("type"),
                    "options": [
                        option.get("name")
                        for option in (prop.get(prop.get("type") or "", {}) or {}).get("options", [])
                    ],
                }
                for name, prop in (data.get("properties") or {}).items()
            },
        }
        print(f"{label}: OK")
        print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Append detector status to a Notion page.")
    parser.add_argument("--page", default=os.environ.get("NOTION_PAGE_ID", ""), help="Notion page id or URL.")
    parser.add_argument("--target", choices=["block", "database"], default="block")
    parser.add_argument("--focus", choices=["experiment", "proposed"], default="experiment")
    parser.add_argument(
        "--summary-csv",
        default=(
            "outputs/experiments/server_with_proposed_summary.csv,"
            "outputs/experiments/server_fresh/large_20260524_140922/live/server_baseline_summary.csv"
        ),
        help="Comma-separated summary CSV paths.",
    )
    parser.add_argument("--results-csv", default="outputs/experiments/server_fresh/large_20260524_140922/live/server_baseline_results.csv")
    parser.add_argument("--stage-gate-json", default="outputs/experiments/server_with_proposed_stage_gate.json")
    parser.add_argument("--top3-command-csv", default="outputs/experiments/top3_proposed_ablation_commands.csv")
    parser.add_argument("--plan-md", default="docs/current_experiment_steps.md")
    parser.add_argument("--image", action="append", default=[], help="Image path to upload and attach. Can be repeated.")
    parser.add_argument("--image-paths", default=DEFAULT_IMAGE_PATHS, help="Comma-separated image paths to upload and attach.")
    parser.add_argument("--no-images", action="store_true")
    parser.add_argument("--title", default="")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--notion-version", default=DEFAULT_NOTION_VERSION)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--inspect", action="store_true", help="Inspect the target object and exit.")
    parser.add_argument("--list-database", action="store_true", help="List page titles in the target database and exit.")
    parser.add_argument("--find-title", default="", help="Find a database page by title substring and append/update that page.")
    parser.add_argument("--token-stdin", action="store_true", help="Read the Notion token from stdin instead of NOTION_TOKEN.")
    parser.add_argument("--status", default="In Progress")
    parser.add_argument("--research-type", default="02 Object Detection")
    parser.add_argument("--idea-source", default="04 Experiment Result")
    parser.add_argument("--category", default="04 Experiment Result")
    parser.add_argument("--priority", default="03 High")
    parser.add_argument(
        "--next-action",
        action="append",
        default=[
            "Let the active large-anchor comparison finish.",
            "Run the top-3 proposed detector screening after the large queue clears.",
            "Run UAVDT validation after the proposed screening.",
        ],
    )
    args = parser.parse_args()

    try:
        page_id = extract_page_id(args.page)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    token = sys.stdin.readline().strip() if args.token_stdin else os.environ.get("NOTION_TOKEN", "").strip()
    if not token and not args.dry_run:
        raise SystemExit("NOTION_TOKEN is not set.")
    if args.inspect:
        if not token:
            raise SystemExit("NOTION_TOKEN is not set.")
        inspect_target(page_id, token, args.notion_version)
        return
    if args.list_database:
        if not token:
            raise SystemExit("NOTION_TOKEN is not set.")
        list_database_pages(page_id, token, args.notion_version)
        return

    blocks = build_proposed_blocks(args) if args.focus == "proposed" else build_blocks(args)
    image_paths = ",".join([args.image_paths, *args.image]).strip(",")
    if args.dry_run:
        print(json.dumps({"page_id": page_id, "image_paths": image_paths, "children": blocks}, indent=2))
        return
    if image_paths and not args.no_images:
        blocks = (
            blocks[:1]
            + [heading("Result Figures", 3)]
            + upload_image_blocks(image_paths, token, args.notion_version)
            + blocks[1:]
        )
    if args.find_title:
        target_page_id = find_database_page(page_id, token, args.notion_version, args.find_title)
        append_blocks(target_page_id, token, blocks, args.notion_version)
        print(f"Appended {len(blocks)} blocks to existing Notion page {target_page_id}.")
    elif args.target == "database":
        created_id = create_database_page(page_id, token, blocks, database_properties(args), args.notion_version)
        print(f"Created a Notion database page {created_id} in {page_id}.")
    else:
        append_blocks(page_id, token, blocks, args.notion_version)
        print(f"Appended {len(blocks)} blocks to Notion page {page_id}.")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1) from exc
