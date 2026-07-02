"""Check AeroGraph external-provider response readiness for paper-table promotion."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.aerograph_response_validation import validate_response_row


DEFAULT_PROVIDER_MANIFESTS = [
    "outputs/reasoning/aerograph_prompt_pack_eval_manual_web/manifest.json",
    "outputs/reasoning/aerograph_prompt_pack_eval_external_web/manifest.json",
    "outputs/reasoning/aerograph_prompt_pack_eval_openai/manifest.json",
    "outputs/reasoning/aerograph_prompt_pack_eval_command/manifest.json",
    "outputs/reasoning/aerograph_prompt_pack_eval_manual/manifest.json",
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                rows.append({"_invalid_jsonl_line": line_number})
                continue
            rows.append(payload if isinstance(payload, dict) else {"_non_object_line": line_number})
    return rows


def response_present(row: dict[str, Any]) -> bool:
    if row.get("_invalid_jsonl_line") or row.get("_non_object_line"):
        return False
    for key in ("response", "response_text", "raw_text", "raw_response", "model_output", "output"):
        value = row.get(key)
        if value not in (None, ""):
            return True
    return False


def response_valid(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("_invalid_jsonl_line") or row.get("_non_object_line"):
        return {"present": False, "valid": False, "issues": ["invalid_jsonl_row"], "payload": None}
    return validate_response_row(row)


def key_candidates(row: dict[str, Any], index: int) -> list[str]:
    keys: list[str] = []
    scenario_id = row.get("scenario_id")
    object_id = row.get("object_id")
    if scenario_id not in (None, "") and object_id not in (None, ""):
        keys.append(f"scenario_object:{scenario_id}:{object_id}")
    for key_name in ("index", "id"):
        value = row.get(key_name)
        if value not in (None, ""):
            keys.append(f"index:{value}")
    if object_id not in (None, ""):
        keys.append(f"object:{object_id}")
    keys.append(f"index:{index}")
    return list(dict.fromkeys(str(key) for key in keys))


def coverage(prompt_rows: list[dict[str, Any]], response_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_key: dict[str, dict[str, Any]] = {}
    invalid_rows = 0
    present_response_rows = 0
    valid_response_rows = 0
    invalid_response_rows = 0
    invalid_response_row_examples: list[dict[str, Any]] = []
    for index, row in enumerate(response_rows, start=1):
        if row.get("_invalid_jsonl_line") or row.get("_non_object_line"):
            invalid_rows += 1
            continue
        if response_present(row):
            present_response_rows += 1
            validation = response_valid(row)
            if validation["valid"]:
                valid_response_rows += 1
            else:
                invalid_response_rows += 1
                if len(invalid_response_row_examples) < 20:
                    invalid_response_row_examples.append(
                        {
                            "row_index": index,
                            "scenario_id": row.get("scenario_id"),
                            "object_id": row.get("object_id"),
                            "issues": validation["issues"],
                        }
                    )
        for key in key_candidates(row, index):
            by_key[key] = row

    matched = 0
    matched_with_response = 0
    matched_valid_response = 0
    missing: list[str] = []
    missing_indices: list[int] = []
    blank: list[str] = []
    blank_indices: list[int] = []
    invalid: list[str] = []
    invalid_indices: list[int] = []
    invalid_examples: list[dict[str, Any]] = []
    matched_nonblank_indices: list[int] = []
    matched_valid_indices: list[int] = []
    for index, prompt in enumerate(prompt_rows, start=1):
        source = next((by_key[key] for key in key_candidates(prompt, index) if key in by_key), None)
        label = f"{prompt.get('scenario_id')}:{prompt.get('object_id')}"
        if source is None:
            missing.append(label)
            missing_indices.append(index)
            continue
        matched += 1
        if response_present(source):
            matched_with_response += 1
            matched_nonblank_indices.append(index)
            validation = response_valid(source)
            if validation["valid"]:
                matched_valid_response += 1
                matched_valid_indices.append(index)
            else:
                invalid.append(label)
                invalid_indices.append(index)
                if len(invalid_examples) < 20:
                    invalid_examples.append(
                        {
                            "index": index,
                            "label": label,
                            "issues": validation["issues"],
                        }
                    )
        else:
            blank.append(label)
            blank_indices.append(index)

    total = len(prompt_rows)
    return {
        "prompt_count": total,
        "response_row_count": len(response_rows),
        "present_response_row_count": present_response_rows,
        "valid_response_row_count": valid_response_rows,
        "matched_prompt_count": matched,
        "matched_nonblank_response_count": matched_with_response,
        "matched_valid_response_count": matched_valid_response,
        "missing_prompt_count": len(missing),
        "blank_response_count": len(blank),
        "invalid_response_row_count": invalid_rows,
        "invalid_schema_response_row_count": invalid_response_rows,
        "invalid_matched_response_count": len(invalid),
        "missing_examples": missing[:20],
        "blank_examples": blank[:20],
        "invalid_examples": invalid_examples,
        "invalid_response_row_examples": invalid_response_row_examples,
        "missing_indices": missing_indices,
        "blank_indices": blank_indices,
        "invalid_indices": invalid_indices,
        "matched_nonblank_indices": matched_nonblank_indices,
        "matched_valid_indices": matched_valid_indices,
        "next_missing_index": sorted(missing_indices + blank_indices + invalid_indices)[0]
        if (missing_indices or blank_indices or invalid_indices)
        else None,
        "coverage_ratio": round(matched_with_response / total, 6) if total else 0.0,
        "valid_coverage_ratio": round(matched_valid_response / total, 6) if total else 0.0,
        "complete": total > 0 and matched_valid_response == total and invalid_rows == 0 and invalid_response_rows == 0,
    }


def batch_coverage(cov: dict[str, Any], web_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    matched = set(int(value) for value in cov.get("matched_valid_indices", cov.get("matched_nonblank_indices", [])))
    batches = web_manifest.get("batches", []) if isinstance(web_manifest, dict) else []
    rows: list[dict[str, Any]] = []
    for batch in batches:
        start = int(batch.get("start_index", 0) or 0)
        end = int(batch.get("end_index", 0) or 0)
        if start <= 0 or end < start:
            continue
        expected = set(range(start, end + 1))
        complete = len(expected & matched)
        rows.append(
            {
                "path": batch.get("path"),
                "start_index": start,
                "end_index": end,
                "count": len(expected),
                "matched_valid_count": complete,
                "matched_nonblank_count": complete,
                "complete": complete == len(expected),
            }
        )
    return rows


def provider_coverage(manifest_path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    summary = manifest.get("summary", {}) or {}
    prompt_count = int(manifest.get("total_prompt_count", 0) or summary.get("total", 0) or 0)
    nonblank = int(manifest.get("non_mock_output_count", 0) or manifest.get("covered_real_prompt_count", 0) or 0)
    valid = int(manifest.get("valid_non_mock_output_count", 0) or 0)
    provider = str(manifest.get("provider", "") if manifest else "")
    provider_lower = provider.lower()
    reviewed_candidate = "internal reviewed" in provider_lower or "review candidate" in provider_lower
    display_provider = "AeroGraph reviewed candidate" if reviewed_candidate else provider
    complete = (
        bool(manifest.get("non_mock_outputs_ready"))
        and prompt_count > 0
        and valid == prompt_count
        and not reviewed_candidate
    )
    return {
        "path": str(manifest_path),
        "exists": bool(manifest),
        "status": manifest.get("status", "missing") if manifest else "missing",
        "provider": display_provider,
        "openai_model": manifest.get("openai_model", "") if manifest else "",
        "prompt_count": prompt_count,
        "matched_nonblank_response_count": nonblank,
        "matched_valid_response_count": valid,
        "coverage_ratio": round(valid / prompt_count, 6) if prompt_count else 0.0,
        "complete": complete,
        "non_mock_outputs_ready": bool(manifest.get("non_mock_outputs_ready")) if manifest else False,
        "reviewed_candidate": reviewed_candidate,
        "external_provider_replication_ready": complete,
    }


def best_provider_coverage(paths: list[Path]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = [provider_coverage(path, read_json(path)) for path in paths]
    existing = [row for row in rows if row["exists"]]
    if not existing:
        return rows, {
            "source": "provider_manifest",
            "prompt_count": 0,
            "matched_nonblank_response_count": 0,
            "matched_valid_response_count": 0,
            "coverage_ratio": 0.0,
            "complete": False,
            "path": "",
        }
    best = max(
        existing,
        key=lambda row: (
            bool(row.get("complete")),
            int(row.get("matched_valid_response_count", row.get("matched_nonblank_response_count", 0)) or 0),
            float(row.get("coverage_ratio", 0.0) or 0.0),
        ),
    )
    best = dict(best)
    best["source"] = "provider_manifest"
    return rows, best


def effective_coverage(manual: dict[str, Any], provider: dict[str, Any]) -> dict[str, Any]:
    manual_matched = int(manual.get("matched_valid_response_count", manual.get("matched_nonblank_response_count", 0)) or 0)
    provider_matched = int(provider.get("matched_valid_response_count", provider.get("matched_nonblank_response_count", 0)) or 0)
    if provider_matched > manual_matched or provider.get("complete"):
        return provider
    result = {
        "source": "manual_responses",
        "prompt_count": manual.get("prompt_count", 0),
        "matched_nonblank_response_count": manual_matched,
        "matched_valid_response_count": manual_matched,
        "coverage_ratio": manual.get("valid_coverage_ratio", manual.get("coverage_ratio", 0.0)),
        "complete": manual.get("complete", False),
        "path": "",
    }
    return result


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    cov = report["manual_response_coverage"]
    effective = report["effective_response_coverage"]
    lines = [
        "# AeroGraph Non-Mock Readiness Status",
        "",
        f"- Status: `{report['status']}`",
        f"- Prompt pack: `{report['prompt_pack']}`",
        f"- Prompt count: `{cov['prompt_count']}`",
        f"- Manual response file: `{report['manual_responses']}`",
        f"- Response rows: `{cov['response_row_count']}`",
        f"- Matched nonblank responses: `{cov['matched_nonblank_response_count']}/{cov['prompt_count']}`",
        f"- Matched valid schema responses: `{cov['matched_valid_response_count']}/{cov['prompt_count']}`",
        f"- Coverage ratio: `{cov['coverage_ratio']}`",
        f"- Valid coverage ratio: `{cov['valid_coverage_ratio']}`",
        f"- Effective valid response coverage: `{effective.get('matched_valid_response_count', effective.get('matched_nonblank_response_count'))}/{effective.get('prompt_count')}` via `{effective.get('source')}`",
        f"- Reviewed-candidate coverage: `{report.get('reviewed_candidate_valid_count')}/{cov['prompt_count']}`",
        f"- External-provider replication ready: `{report.get('external_provider_replication_ready')}`",
        f"- Invalid JSONL response rows: `{cov['invalid_response_row_count']}`",
        f"- Invalid schema response rows: `{cov['invalid_schema_response_row_count']}`",
        f"- Web batch manifest: `{report['web_batch_manifest']}`",
        f"- Web batch status: `{report['web_batch_status']}`",
        f"- Web batch count: `{report['web_batch_count']}`",
        f"- Full manual template: `{report['full_template']}`",
        f"- Paper table manifest: `{report['paper_table_manifest']}`",
        f"- Paper table status: `{report['paper_table_status']}`",
        "",
        "## Interpretation",
        "",
    ]
    if report.get("external_provider_replication_ready"):
        lines.append("- All prompts have matched valid-schema external-provider responses. Rebuild or verify the final paper table.")
    elif report.get("reviewed_candidate_valid_count") == cov["prompt_count"] and cov["prompt_count"]:
        lines.append("- A reviewed candidate table is available, but final external-provider/local-model replication is still pending.")
    elif cov["matched_valid_response_count"] == 0 and effective.get("matched_valid_response_count", effective.get("matched_nonblank_response_count", 0)) == 0:
        lines.append("- External-provider responses are not collected yet. Use the web batches or full template next.")
    else:
        lines.append("- External-provider responses are partially collected. Fill missing/blank/invalid rows before paper-table promotion.")

    provider_runs = report.get("provider_run_coverage", [])
    if provider_runs:
        lines.extend(
            [
                "",
                "## Provider Manifest Coverage",
                "",
                "| Source | Status | Provider | Valid Responses | Reviewed Candidate | External Complete |",
                "| --- | --- | --- | ---: | --- |",
            ]
        )
        for row in provider_runs:
            if not row.get("exists"):
                continue
            provider = row.get("provider") or row.get("openai_model") or "provider"
            lines.append(
                f"| `{row['path']}` | `{row['status']}` | `{provider}` | "
                f"`{row.get('matched_valid_response_count', row['matched_nonblank_response_count'])}/{row['prompt_count']}` | "
                f"`{row.get('reviewed_candidate')}` | `{row['complete']}` |"
            )

    if report.get("web_batch_progress"):
        lines.extend(
            [
                "",
                "## Batch Progress",
                "",
                "| Batch | Items | Valid Responses | Status | File |",
                "| ---: | --- | ---: | --- | --- |",
            ]
        )
        for index, batch in enumerate(report["web_batch_progress"], start=1):
            status = "done" if batch["complete"] else "pending"
            lines.append(
                f"| {index} | {batch['start_index']}-{batch['end_index']} | "
                f"{batch.get('matched_valid_count', batch['matched_nonblank_count'])}/{batch['count']} | {status} | `{batch['path']}` |"
            )

    if cov["missing_examples"]:
        lines.extend(["", "## Missing Examples", ""])
        if cov.get("next_missing_index") is not None:
            lines.append(f"- Next missing item index: `{cov['next_missing_index']}`")
        for item in cov["missing_examples"]:
            lines.append(f"- `{item}`")
    if cov["blank_examples"]:
        lines.extend(["", "## Blank Response Examples", ""])
        for item in cov["blank_examples"]:
            lines.append(f"- `{item}`")
    if cov.get("invalid_examples"):
        lines.extend(["", "## Invalid Schema Examples", ""])
        for item in cov["invalid_examples"]:
            lines.append(f"- `{item}`")
    if cov.get("invalid_response_row_examples"):
        lines.extend(["", "## Invalid Response Row Examples", ""])
        for item in cov["invalid_response_row_examples"]:
            lines.append(f"- `{item}`")

    lines.extend(
        [
            "",
            "## Promotion Commands",
            "",
            "```bash",
            "python scripts/check_aerograph_prompt_pack_integrity.py",
            "python scripts/import_aerograph_manual_responses.py \\",
            "  --responses outputs/reasoning/aerograph_manual_responses.jsonl \\",
            "  --provider-label \"External web LLM\" \\",
            "  --out-dir outputs/reasoning/aerograph_prompt_pack_eval_manual_web",
            "python scripts/build_aerograph_reasoner_table.py",
            "python scripts/check_aerograph_nonmock_readiness.py",
            "python scripts/check_paper_artifact_readiness.py",
            "python scripts/check_latex_patch_integrity.py",
            "PYTHONPATH=. python scripts/build_live_training_dashboard.py --out outputs/reports/live/training_dashboard.png",
            "python scripts/build_accv_status_snapshot.py",
            "```",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build(args: argparse.Namespace) -> dict[str, Any]:
    prompt_pack = Path(args.prompt_pack)
    manual_responses = Path(args.manual_responses)
    web_manifest_path = Path(args.web_batch_manifest)
    table_manifest_path = Path(args.paper_table_manifest)
    full_template = Path(args.full_template)

    prompt_rows = read_jsonl(prompt_pack)
    response_rows = read_jsonl(manual_responses)
    cov = coverage(prompt_rows, response_rows)
    web_manifest = read_json(web_manifest_path)
    table_manifest = read_json(table_manifest_path)
    provider_paths = [Path(item) for item in args.provider_manifests]
    provider_rows, best_provider = best_provider_coverage(provider_paths)
    effective = effective_coverage(cov, best_provider)
    reviewed_valid = max(
        (
            int(row.get("matched_valid_response_count", 0) or 0)
            for row in provider_rows
            if row.get("reviewed_candidate")
        ),
        default=0,
    )
    external_ready = bool(best_provider.get("complete")) and bool(table_manifest.get("non_mock_outputs_ready"))
    status = (
        "aerograph_external_provider_table_ready"
        if external_ready
        else "aerograph_reviewed_candidate_ready_external_pending"
        if reviewed_valid == len(prompt_rows) and prompt_rows
        else "aerograph_external_provider_pending_responses"
    )

    report = {
        "status": status,
        "prompt_pack": str(prompt_pack),
        "manual_responses": str(manual_responses),
        "full_template": str(full_template),
        "full_template_exists": full_template.exists(),
        "web_batch_manifest": str(web_manifest_path),
        "web_batch_status": web_manifest.get("status", "missing"),
        "web_batch_count": web_manifest.get("batch_count", 0),
        "paper_table_manifest": str(table_manifest_path),
        "paper_table_status": table_manifest.get("status", "missing"),
        "paper_table_non_mock_outputs_ready": bool(table_manifest.get("non_mock_outputs_ready")),
        "external_provider_replication_ready": external_ready,
        "reviewed_candidate_valid_count": reviewed_valid,
        "manual_response_coverage": cov,
        "provider_run_coverage": provider_rows,
        "best_provider_coverage": best_provider,
        "effective_response_coverage": effective,
        "web_batch_progress": batch_coverage(cov, web_manifest),
    }

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(Path(args.out_md), report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt-pack", default="outputs/reports/live/aerograph_prompt_pack/aerograph_prompts_all.jsonl")
    parser.add_argument("--manual-responses", default="outputs/reasoning/aerograph_manual_responses.jsonl")
    parser.add_argument("--full-template", default="outputs/reports/live/aerograph_prompt_pack/aerograph_manual_response_template_all.jsonl")
    parser.add_argument("--web-batch-manifest", default="outputs/reports/live/aerograph_prompt_pack/web_batches/manifest.json")
    parser.add_argument("--paper-table-manifest", default="outputs/reports/live/aerograph_reasoner_table_manifest.json")
    parser.add_argument("--provider-manifests", nargs="*", default=DEFAULT_PROVIDER_MANIFESTS)
    parser.add_argument("--out-json", default="outputs/reports/live/aerograph_nonmock_readiness_status.json")
    parser.add_argument("--out-md", default="outputs/reports/live/aerograph_nonmock_readiness_status.md")
    args = parser.parse_args()
    print(json.dumps(build(args), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
