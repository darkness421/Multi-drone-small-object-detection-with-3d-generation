"""Summarize the compact real-capture AeroGraph provider smoke gate."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = [
    "outputs/reasoning/aerograph_real_capture_eval_openai/manifest.json",
    "outputs/reasoning/aerograph_real_capture_eval_command/manifest.json",
    "outputs/reasoning/aerograph_real_capture_eval_manual_web/manifest.json",
    "outputs/reasoning/aerograph_real_capture_eval_dryrun/manifest.json",
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def manifest_summary(path: Path) -> dict[str, Any]:
    manifest = read_json(path)
    summary = manifest.get("summary", {}) or {}
    total = int(summary.get("total", manifest.get("total_prompt_count", 0)) or 0)
    nonmock = int(manifest.get("non_mock_output_count", 0) or 0)
    valid = int(manifest.get("valid_non_mock_output_count", 0) or 0)
    provider_runtime = summary.get("by_provider_runtime", {}) or {}
    is_complete = bool(manifest.get("non_mock_outputs_ready")) and total > 0 and nonmock == total and valid == total
    is_dry_run = manifest.get("provider") == "dry-run" or bool(provider_runtime.get("dry_run"))
    provider = str(manifest.get("provider", ""))
    provider_lower = provider.lower()
    if "internal reviewed" in provider_lower or "review candidate" in provider_lower:
        provider = "AeroGraph reviewed candidate"
    return {
        "path": rel(path),
        "exists": path.exists(),
        "status": manifest.get("status", "missing" if not path.exists() else "unknown"),
        "provider": provider,
        "openai_model": manifest.get("openai_model", ""),
        "total": total,
        "non_mock_output_count": nonmock,
        "valid_non_mock_output_count": valid,
        "paper_claim_allowed": bool(manifest.get("paper_claim_allowed")),
        "non_mock_outputs_ready": bool(manifest.get("non_mock_outputs_ready")),
        "complete_nonmock_smoke": is_complete and not is_dry_run,
        "dry_run": is_dry_run,
    }


def build(args: argparse.Namespace) -> dict[str, Any]:
    candidates = [REPO_ROOT / item for item in (args.candidates or DEFAULT_CANDIDATES)]
    rows = [manifest_summary(path) for path in candidates]
    complete = next((row for row in rows if row["complete_nonmock_smoke"]), None)
    partial = next((row for row in rows if row["non_mock_output_count"] and not row["complete_nonmock_smoke"]), None)
    prompt_manifest = read_json(REPO_ROOT / args.prompt_manifest)
    expected = int(prompt_manifest.get("total_prompts", 0) or 0)
    if complete:
        status = "aerograph_real_capture_nonmock_smoke_complete"
    elif partial:
        status = "aerograph_real_capture_nonmock_smoke_partial"
    else:
        status = "aerograph_real_capture_nonmock_smoke_pending"
    report = {
        "updated_at_kst": datetime.now().strftime("%Y-%m-%d %H:%M:%S KST"),
        "status": status,
        "expected_prompt_count": expected,
        "selected_manifest": complete["path"] if complete else "",
        "best_partial_manifest": partial["path"] if partial else "",
        "candidate_manifests": rows,
        "claiming_rule": (
            "This 23-prompt real-capture run is a provider smoke gate only. "
            "It must not replace the 49-prompt final AeroGraph paper-table gate "
            "unless the paper protocol is explicitly changed."
        ),
    }
    return report


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# AeroGraph Real-Capture Non-Mock Smoke Status",
        "",
        f"Updated: `{report['updated_at_kst']}`",
        f"Status: `{report['status']}`",
        f"Expected prompts: `{report['expected_prompt_count']}`",
        f"Selected manifest: `{report['selected_manifest'] or '-'}`",
        f"Best partial manifest: `{report['best_partial_manifest'] or '-'}`",
        "",
        "## Candidate Runs",
        "",
        "| Manifest | Status | Provider | Total | Non-mock | Valid | Complete |",
        "| --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in report["candidate_manifests"]:
        lines.append(
            f"| `{row['path']}` | `{row['status']}` | `{row['provider']}` | "
            f"{row['total']} | {row['non_mock_output_count']} | "
            f"{row['valid_non_mock_output_count']} | `{row['complete_nonmock_smoke']}` |"
        )
    lines.extend(["", "## Claiming Rule", "", report["claiming_rule"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt-manifest", default="outputs/reports/live/aerograph_real_capture_prompt_pack/manifest.json")
    parser.add_argument("--out-json", default="outputs/reports/live/aerograph_real_capture_nonmock_smoke_status.json")
    parser.add_argument("--out-md", default="outputs/reports/live/aerograph_real_capture_nonmock_smoke_status.md")
    parser.add_argument("--candidates", nargs="*", default=[])
    args = parser.parse_args()
    report = build(args)
    out_json = REPO_ROOT / args.out_json
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(REPO_ROOT / args.out_md, report)
    print(json.dumps({"status": report["status"], "json": rel(out_json), "markdown": args.out_md}, indent=2))


if __name__ == "__main__":
    main()
