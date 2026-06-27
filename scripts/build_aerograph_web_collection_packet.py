"""Build a human-facing AeroGraph web collection packet and checklist."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.aerograph_response_validation import validate_response_row
from scripts.normalize_aerograph_web_responses import row_key


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def batch_number(index: int, manifest: dict[str, Any]) -> int:
    for batch_index, batch in enumerate(manifest.get("batches", []), start=1):
        start = int(batch.get("start_index", 0) or 0)
        end = int(batch.get("end_index", 0) or 0)
        if start <= index <= end:
            return batch_index
    size = int(manifest.get("batch_size", 10) or 10)
    return (index - 1) // size + 1


def response_lookup(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows, start=1):
        lookup[row_key(row, index)] = row
    return lookup


def prompt_keys(row: dict[str, Any], index: int) -> list[str]:
    keys = [row_key(row, index)]
    object_id = row.get("object_id")
    if object_id not in (None, ""):
        keys.append(f"object:{object_id}")
    if row.get("index") not in (None, ""):
        keys.append(f"index:{row.get('index')}")
    keys.append(f"index:{index}")
    return list(dict.fromkeys(keys))


def build_rows(
    prompts: list[dict[str, Any]],
    manifest: dict[str, Any],
    responses: list[dict[str, Any]],
    raw_output_dir: str,
) -> list[dict[str, Any]]:
    by_key = response_lookup(responses)
    rows: list[dict[str, Any]] = []
    for index, prompt in enumerate(prompts, start=1):
        response = next((by_key[key] for key in prompt_keys(prompt, index) if key in by_key), None)
        valid = False
        issues = ""
        if response is not None:
            result = validate_response_row(response)
            valid = bool(result["valid"])
            issues = ";".join(str(item) for item in result["issues"])
        batch = batch_number(index, manifest)
        rows.append(
            {
                "index": index,
                "batch": batch,
                "scenario_id": prompt.get("scenario_id", ""),
                "scenario": prompt.get("scenario", ""),
                "object_id": prompt.get("object_id", ""),
                "candidate_class": prompt.get("candidate_class", ""),
                "should_reobserve": prompt.get("should_reobserve", ""),
                "status": "valid" if valid else ("invalid" if response else "pending"),
                "valid_schema": valid,
                "schema_issues": issues,
                "web_batch_file": batch_file(batch, manifest),
                "suggested_raw_output": f"{raw_output_dir}/batch_{batch:02d}.md",
            }
        )
    return rows


def batch_file(batch_index: int, manifest: dict[str, Any]) -> str:
    batches = manifest.get("batches", [])
    if 1 <= batch_index <= len(batches):
        return str(batches[batch_index - 1].get("path", ""))
    return ""


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "index",
        "batch",
        "scenario_id",
        "scenario",
        "object_id",
        "candidate_class",
        "should_reobserve",
        "status",
        "valid_schema",
        "schema_issues",
        "web_batch_file",
        "suggested_raw_output",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, Any]], manifest: dict[str, Any], checklist_path: Path, args: argparse.Namespace) -> None:
    total = len(rows)
    valid = sum(1 for row in rows if row["status"] == "valid")
    invalid = sum(1 for row in rows if row["status"] == "invalid")
    pending = sum(1 for row in rows if row["status"] == "pending")
    gate_label = args.gate_label or f"{total}-Prompt"
    lines = [
        f"# AeroGraph {gate_label} Web Collection Packet",
        "",
        args.purpose,
        "",
        "## Current Coverage",
        "",
        f"- Total prompts: `{total}`",
        f"- Valid schema responses: `{valid}/{total}`",
        f"- Invalid responses: `{invalid}`",
        f"- Pending responses: `{pending}`",
        f"- Checklist CSV: `{checklist_path}`",
        "",
        "## Batch Files",
        "",
        "| Batch | Items | Count | Raw output target | Prompt file |",
        "| ---: | --- | ---: | --- | --- |",
    ]
    for index, batch in enumerate(manifest.get("batches", []), start=1):
        lines.append(
            f"| {index} | {batch.get('start_index')}-{batch.get('end_index')} | {batch.get('count')} | "
            f"`{args.raw_output_dir}/batch_{index:02d}.md` | `{batch.get('path')}` |"
        )
    lines.extend(
        [
            "",
            "## Workflow",
            "",
            "1. Paste each batch prompt file into the selected web LLM.",
            "2. Save each raw answer into the matching raw output target above.",
            "3. Normalize and merge all raw outputs:",
            "",
            "```bash",
            "python scripts/normalize_aerograph_web_responses.py \\",
            f"  --input {args.raw_output_dir}/ \\",
            f"  --out {args.normalized_responses} \\",
            f"  --append-to {args.manual_responses}",
            "```",
            "",
            "4. Import responses:",
            "",
            "```bash",
            "python scripts/check_aerograph_prompt_pack_integrity.py",
            "python scripts/import_aerograph_manual_responses.py \\",
            f"  --prompt-pack {args.prompt_pack} \\",
            f"  --responses {args.manual_responses} \\",
            f"  --provider-label \"{args.provider_label}\" \\",
            f"  --out-dir {args.import_out_dir}",
        ]
    )
    if args.promotion_mode == "full":
        lines.extend(
            [
                "python scripts/build_aerograph_reasoner_table.py",
                "python scripts/check_aerograph_nonmock_readiness.py",
                "python scripts/check_paper_artifact_readiness.py",
                "python scripts/check_latex_patch_integrity.py",
                "PYTHONPATH=. python scripts/build_live_training_dashboard.py --out outputs/reports/live/training_dashboard.png",
                "python scripts/build_accv_status_snapshot.py",
            ]
        )
    else:
        lines.extend(
            [
                "# Compact smoke only: inspect the manifest before any paper-table promotion.",
                f"cat {args.import_out_dir}/manifest.json",
            ]
        )
    lines.extend(
        [
            "```",
            "",
            "## Pending Items",
            "",
            "| Index | Batch | Scenario | Object | Candidate | Status |",
            "| ---: | ---: | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        if row["status"] == "valid":
            continue
        lines.append(
            f"| {row['index']} | {row['batch']} | {row['scenario_id']} | "
            f"`{row['object_id']}` | {row['candidate_class']} | {row['status']} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(args: argparse.Namespace) -> dict[str, Any]:
    defaults = {
        "raw_output_dir": "outputs/reasoning/aerograph_web_raw_batches",
        "normalized_responses": "outputs/reasoning/aerograph_manual_responses.normalized.jsonl",
        "provider_label": "External web LLM",
        "import_out_dir": "outputs/reasoning/aerograph_prompt_pack_eval_manual_web",
        "gate_label": "49-Prompt",
        "promotion_mode": "full",
        "purpose": (
            "Purpose: collect non-mock AeroGraph reasoner responses from a web LLM "
            "for the final ACCV paper-table gate."
        ),
    }
    for key, value in defaults.items():
        if not hasattr(args, key):
            setattr(args, key, value)

    repo_root = Path(args.repo_root).resolve()
    prompts = read_jsonl(repo_root / args.prompt_pack)
    manifest = read_json(repo_root / args.web_batch_manifest)
    responses = read_jsonl(repo_root / args.manual_responses)
    rows = build_rows(prompts, manifest, responses, args.raw_output_dir)
    checklist_path = repo_root / args.out_csv
    packet_path = repo_root / args.out_md
    write_csv(checklist_path, rows)
    write_markdown(packet_path, rows, manifest, checklist_path.relative_to(repo_root), args)
    report = {
        "status": "aerograph_web_collection_packet_ready",
        "prompt_count": len(prompts),
        "valid_schema_responses": sum(1 for row in rows if row["status"] == "valid"),
        "invalid_responses": sum(1 for row in rows if row["status"] == "invalid"),
        "pending_responses": sum(1 for row in rows if row["status"] == "pending"),
        "packet": str(packet_path.relative_to(repo_root)),
        "checklist": str(checklist_path.relative_to(repo_root)),
    }
    (repo_root / args.out_json).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--prompt-pack", default="outputs/reports/live/aerograph_prompt_pack/aerograph_prompts_all.jsonl")
    parser.add_argument("--web-batch-manifest", default="outputs/reports/live/aerograph_prompt_pack/web_batches/manifest.json")
    parser.add_argument("--manual-responses", default="outputs/reasoning/aerograph_manual_responses.jsonl")
    parser.add_argument("--raw-output-dir", default="outputs/reasoning/aerograph_web_raw_batches")
    parser.add_argument("--normalized-responses", default="outputs/reasoning/aerograph_manual_responses.normalized.jsonl")
    parser.add_argument("--provider-label", default="External web LLM")
    parser.add_argument("--import-out-dir", default="outputs/reasoning/aerograph_prompt_pack_eval_manual_web")
    parser.add_argument("--gate-label", default="49-Prompt")
    parser.add_argument("--promotion-mode", choices=["full", "smoke"], default="full")
    parser.add_argument(
        "--purpose",
        default=(
            "Purpose: collect final non-mock AeroGraph Reasoner responses from a web "
            "LLM provider, then promote them to the paper table "
            "only after all rows pass schema validation."
        ),
    )
    parser.add_argument("--out-md", default="outputs/reports/live/aerograph_prompt_pack/aerograph_web_collection_packet.md")
    parser.add_argument("--out-csv", default="outputs/reports/live/aerograph_prompt_pack/aerograph_web_collection_checklist.csv")
    parser.add_argument("--out-json", default="outputs/reports/live/aerograph_prompt_pack/aerograph_web_collection_packet.json")
    args = parser.parse_args()
    print(json.dumps(build(args), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
