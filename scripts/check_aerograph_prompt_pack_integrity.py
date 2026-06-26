"""Validate active AeroGraph prompt-pack files for non-mock collection.

This catches the easy-to-miss case where the active prompt pack has been
reduced to 49 prompts but stale 79-row templates or web batches remain in the
live folder.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return -1
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    prompt_dir = REPO_ROOT / args.prompt_dir
    web_dir = REPO_ROOT / args.web_batch_dir
    archive_dir = REPO_ROOT / args.archive_dir
    manifest_path = prompt_dir / "manifest.json"
    web_manifest_path = web_dir / "manifest.json"
    manifest = read_json(manifest_path)
    web_manifest = read_json(web_manifest_path)
    total = int(manifest.get("total_prompts", 0) or 0)
    sample = int(manifest.get("sample_prompts", 0) or 0)

    files = {
        "all_jsonl": REPO_ROOT / str(manifest.get("all_jsonl", "")),
        "counted_jsonl": REPO_ROOT / str(manifest.get("counted_jsonl", "")),
        "sample_jsonl": REPO_ROOT / str(manifest.get("sample_jsonl", "")),
        "manual_template_all": REPO_ROOT / str(manifest.get("manual_response_template_all", "")),
        "manual_template_sample": REPO_ROOT / str(manifest.get("manual_response_template_sample", "")),
    }
    counts = {name: count_jsonl(path) for name, path in files.items()}

    expected_counts = {
        "all_jsonl": total,
        "counted_jsonl": total,
        "sample_jsonl": sample,
        "manual_template_all": total,
        "manual_template_sample": sample,
    }
    count_failures = [
        {
            "name": name,
            "path": rel(files[name]),
            "actual": counts.get(name),
            "expected": expected,
        }
        for name, expected in expected_counts.items()
        if counts.get(name) != expected
    ]

    expected_counted_name = f"aerograph_prompts_{total}.jsonl"
    stale_counted = [
        rel(path)
        for path in sorted(prompt_dir.glob("aerograph_prompts_[0-9]*.jsonl"))
        if path.name != expected_counted_name
    ]

    batches = web_manifest.get("batches", []) if isinstance(web_manifest, dict) else []
    batch_paths = {REPO_ROOT / str(batch.get("path", "")) for batch in batches}
    active_batch_files = set(web_dir.glob("aerograph_web_batch_*.md"))
    unexpected_batches = sorted(active_batch_files - batch_paths)
    missing_batches = sorted(path for path in batch_paths if not path.exists())
    batch_total = sum(int(batch.get("count", 0) or 0) for batch in batches)
    web_failures: list[dict[str, Any]] = []
    if int(web_manifest.get("total_prompts", 0) or 0) != total:
        web_failures.append(
            {
                "name": "web_manifest_total_prompts",
                "actual": web_manifest.get("total_prompts"),
                "expected": total,
            }
        )
    if batch_total != total:
        web_failures.append({"name": "web_batch_sum", "actual": batch_total, "expected": total})
    if missing_batches:
        web_failures.append({"name": "missing_batch_files", "paths": [rel(path) for path in missing_batches]})
    if unexpected_batches:
        web_failures.append({"name": "unexpected_active_batch_files", "paths": [rel(path) for path in unexpected_batches]})

    archived_legacy_files = sorted(rel(path) for path in archive_dir.glob("**/*") if path.is_file())
    failures = count_failures + web_failures
    if stale_counted:
        failures.append({"name": "stale_counted_prompt_packs", "paths": stale_counted})

    status = "aerograph_prompt_pack_integrity_ok" if not failures and total > 0 else "aerograph_prompt_pack_integrity_needs_attention"
    return {
        "updated_at_kst": datetime.now().strftime("%Y-%m-%d %H:%M:%S KST"),
        "status": status,
        "prompt_dir": rel(prompt_dir),
        "web_batch_dir": rel(web_dir),
        "archive_dir": rel(archive_dir),
        "total_prompts": total,
        "sample_prompts": sample,
        "file_counts": counts,
        "expected_counts": expected_counts,
        "web_batch_count": len(batches),
        "web_batch_total": batch_total,
        "failures": failures,
        "archived_legacy_files": archived_legacy_files,
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# AeroGraph Prompt Pack Integrity",
        "",
        f"Updated: `{report['updated_at_kst']}`",
        f"Status: `{report['status']}`",
        f"Prompt count: `{report['total_prompts']}`",
        f"Web batches: `{report['web_batch_count']}` / total rows `{report['web_batch_total']}`",
        "",
        "## File Counts",
        "",
        "| File | Actual | Expected |",
        "| --- | ---: | ---: |",
    ]
    for name, actual in report["file_counts"].items():
        expected = report["expected_counts"].get(name, "")
        lines.append(f"| `{name}` | `{actual}` | `{expected}` |")
    lines.extend(["", "## Failures", ""])
    if report["failures"]:
        for failure in report["failures"]:
            lines.append(f"- `{failure}`")
    else:
        lines.append("- None.")
    lines.extend(["", "## Archived Legacy Files", ""])
    if report["archived_legacy_files"]:
        for item in report["archived_legacy_files"]:
            lines.append(f"- `{item}`")
    else:
        lines.append("- None.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check AeroGraph prompt pack integrity.")
    parser.add_argument("--prompt-dir", default="outputs/reports/live/aerograph_prompt_pack")
    parser.add_argument("--web-batch-dir", default="outputs/reports/live/aerograph_prompt_pack/web_batches")
    parser.add_argument("--archive-dir", default="outputs/reports/archive/aerograph_prompt_pack")
    parser.add_argument("--out-json", default="outputs/reports/live/aerograph_prompt_pack_integrity.json")
    parser.add_argument("--out-md", default="outputs/reports/live/aerograph_prompt_pack_integrity.md")
    args = parser.parse_args()
    report = build_report(args)
    out_json = REPO_ROOT / args.out_json
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(REPO_ROOT / args.out_md, report)
    print(json.dumps({"status": report["status"], "json": rel(out_json), "markdown": args.out_md}, indent=2))


if __name__ == "__main__":
    main()
