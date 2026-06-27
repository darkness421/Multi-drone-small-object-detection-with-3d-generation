"""Build paste-ready AeroGraph prompt batches for web LLM providers."""

from __future__ import annotations

import argparse
import json
from math import ceil
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def batch_rows(rows: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [rows[index : index + size] for index in range(0, len(rows), size)]


def prompt_block(row: dict[str, Any], index: int) -> str:
    metadata = {
        "index": index,
        "scenario_id": row.get("scenario_id"),
        "scenario": row.get("scenario"),
        "object_id": row.get("object_id"),
        "candidate_class": row.get("candidate_class"),
    }
    return "\n".join(
        [
            f"### Item {index}",
            "",
            "Metadata:",
            "```json",
            json.dumps(metadata, ensure_ascii=False),
            "```",
            "",
            "Prompt:",
            "```text",
            str(row.get("prompt", "")),
            "```",
            "",
        ]
    )


def write_batch(path: Path, rows: list[dict[str, Any]], start_index: int, total: int) -> dict[str, Any]:
    end_index = start_index + len(rows) - 1
    lines = [
        "# AeroGraph Manual Non-Mock Batch",
        "",
        f"Items: {start_index}-{end_index} of {total}",
        "",
        "Instructions for the web LLM/provider:",
        "",
        "Return JSONL only. Do not add prose, markdown fences, explanations, or extra keys.",
        "Each output line must correspond to one item and must use this shape:",
        "",
        "```json",
        json.dumps(
            {
                "index": start_index,
                "scenario_id": "S0",
                "object_id": "example_object",
                "response_text": {
                    "decision": "verified|rejected|uncertain",
                    "predicted_class": "string",
                    "confidence": 0.0,
                    "evidence_clues": [],
                    "missing_evidence": "string",
                    "recommended_action": "string",
                },
            },
            indent=2,
            ensure_ascii=False,
        ),
        "```",
        "",
        "Use only `verified`, `rejected`, or `uncertain` for `decision`.",
        "Set `confidence` between 0 and 1.",
        "If evidence is weak, choose `uncertain` and set `recommended_action` to a re-observation or verification action.",
        "",
    ]
    for offset, row in enumerate(rows):
        lines.append(prompt_block(row, start_index + offset))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "path": str(path),
        "start_index": start_index,
        "end_index": end_index,
        "count": len(rows),
        "scenario_counts": scenario_counts(rows),
    }


def write_index(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# AeroGraph Web Batch Index",
        "",
        "Use these batches when no CLI/API provider is configured. Paste one batch",
        "file into an external web LLM, collect JSONL output, and append it to:",
        "",
        "```text",
        manifest["responses"],
        "```",
        "",
        "The active prompt pack has "
        f"{manifest['total_prompts']} prompts across {manifest['batch_count']} batches.",
        "",
        "| Batch | Items | Count | Scenario Counts | File |",
        "| ---: | --- | ---: | --- | --- |",
    ]
    for index, batch in enumerate(manifest["batches"], start=1):
        scenarios = ", ".join(f"{key}:{value}" for key, value in batch["scenario_counts"].items())
        lines.append(
            f"| {index} | {batch['start_index']}-{batch['end_index']} | {batch['count']} | "
            f"{scenarios} | `{batch['path']}` |"
        )

    lines.extend(
        [
            "",
            "## Required Response Shape",
            "",
            "Return JSONL only, one object per prompt item:",
            "",
            "```json",
            json.dumps(
                {
                    "index": 1,
                    "scenario_id": "S0",
                    "object_id": "example_object",
                    "response_text": {
                        "decision": "verified|rejected|uncertain",
                        "predicted_class": "string",
                        "confidence": 0.0,
                        "evidence_clues": [],
                        "missing_evidence": "string",
                        "recommended_action": "string",
                    },
                },
                indent=2,
                ensure_ascii=False,
            ),
            "```",
            "",
            "The `response_text` value may be either a JSON object as above or a",
            "JSON-encoded string containing the same object. The paper gate counts",
            "only rows that parse successfully and pass the required-key schema.",
            "",
            "Common failure cases rejected by the checker:",
            "",
            "- prose or markdown fences around the JSONL output",
            "- missing `index`, or missing both `scenario_id` and `object_id`",
            "- `decision` outside `verified`, `rejected`, or `uncertain`",
            "- `confidence` outside the `[0, 1]` range",
            "- missing `evidence_clues`, `missing_evidence`, or `recommended_action`",
            "",
            "## Optional Raw Output Normalizer",
            "",
            "If the web model returns markdown fences, a JSON array, or prose around",
            "the JSONL, save that raw text first, then normalize one file, multiple",
            "files, a directory, or a glob:",
            "",
            "```bash",
            "python scripts/normalize_aerograph_web_responses.py \\",
            f"  --input {manifest['raw_output_dir']}/ \\",
            f"  --out {manifest['normalized_responses']} \\",
            f"  --append-to {manifest['responses']}",
            "```",
            "",
            "## Import Commands",
            "",
            "```bash",
            "python scripts/check_aerograph_prompt_pack_integrity.py",
            manifest["collection_packet_command"],
            manifest["import_command"],
        ]
    )
    if manifest.get("promotion_mode") == "full":
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
                f"cat {manifest['import_out_dir']}/manifest.json",
            ]
        )
    lines.extend(["```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def scenario_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        scenario = str(row.get("scenario_id", "unknown"))
        counts[scenario] = counts.get(scenario, 0) + 1
    return dict(sorted(counts.items()))


def archive_stale_batches(out_dir: Path, archive_dir: Path, active_paths: set[Path]) -> list[str]:
    archived: list[str] = []
    active_resolved = {path.resolve() for path in active_paths}
    for path in sorted(out_dir.glob("aerograph_web_batch_*.md")):
        if path.resolve() in active_resolved:
            continue
        archive_dir.mkdir(parents=True, exist_ok=True)
        target = archive_dir / path.name
        if target.exists():
            target = archive_dir / f"{path.stem}_legacy{path.suffix}"
        path.rename(target)
        archived.append(str(target))
    return archived


def build(args: argparse.Namespace) -> dict[str, Any]:
    prompt_pack = Path(args.prompt_pack)
    out_dir = Path(args.out_dir)
    archive_dir = Path(args.archive_dir)
    rows = read_jsonl(prompt_pack)
    batches = batch_rows(rows, args.batch_size)
    records: list[dict[str, Any]] = []
    for batch_index, batch in enumerate(batches, start=1):
        start_index = (batch_index - 1) * args.batch_size + 1
        path = out_dir / f"aerograph_web_batch_{batch_index:02d}_{start_index:03d}-{start_index + len(batch) - 1:03d}.md"
        records.append(write_batch(path, batch, start_index, len(rows)))
    archived_legacy_batches = archive_stale_batches(out_dir, archive_dir, {Path(record["path"]) for record in records})

    manifest = {
        "status": "aerograph_web_batches_ready",
        "prompt_pack": str(prompt_pack),
        "out_dir": str(out_dir),
        "batch_size": args.batch_size,
        "total_prompts": len(rows),
        "batch_count": len(batches),
        "scenario_counts": scenario_counts(rows),
        "batches": records,
        "archived_legacy_batches": archived_legacy_batches,
        "responses": args.responses,
        "raw_output_dir": args.raw_output_dir,
        "normalized_responses": args.normalized_responses,
        "promotion_mode": args.promotion_mode,
        "collection_packet_command": args.collection_packet_command,
        "import_out_dir": args.import_out_dir,
        "import_command": (
            "python scripts/import_aerograph_manual_responses.py "
            f"--prompt-pack {args.prompt_pack} "
            f"--responses {args.responses} "
            f"--provider-label \"{args.provider_label}\" "
            f"--out-dir {args.import_out_dir}"
        ),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    index_path = out_dir / "README.md"
    write_index(index_path, manifest)
    manifest["index"] = str(index_path)
    manifest["manifest"] = str(manifest_path)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build web-paste AeroGraph prompt batches.")
    parser.add_argument("--prompt-pack", default="outputs/reports/live/aerograph_prompt_pack/aerograph_prompts_all.jsonl")
    parser.add_argument("--out-dir", default="outputs/reports/live/aerograph_prompt_pack/web_batches")
    parser.add_argument("--archive-dir", default="outputs/reports/archive/aerograph_prompt_pack/web_batches")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--responses", default="outputs/reasoning/aerograph_manual_responses.jsonl")
    parser.add_argument("--raw-output-dir", default="outputs/reasoning/aerograph_web_raw_batches")
    parser.add_argument("--normalized-responses", default="outputs/reasoning/aerograph_manual_responses.normalized.jsonl")
    parser.add_argument("--provider-label", default="External web LLM")
    parser.add_argument("--import-out-dir", default="outputs/reasoning/aerograph_prompt_pack_eval_manual_web")
    parser.add_argument("--promotion-mode", choices=["full", "smoke"], default="full")
    parser.add_argument("--collection-packet-command", default="python scripts/build_aerograph_web_collection_packet.py")
    args = parser.parse_args()
    print(json.dumps(build(args), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
