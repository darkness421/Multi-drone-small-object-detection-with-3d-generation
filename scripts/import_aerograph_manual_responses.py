"""Import manual Factory/ChatGPT AeroGraph responses into paper artifacts.

This is for the no-CLI case: the user can paste prompts into a web UI, collect
JSON responses, and then import them into the same CSV/LaTeX format produced by
``scripts/run_aerograph_prompt_pack.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.run_aerograph_prompt_pack import summarize
from scripts.run_aerograph_prompt_pack import write_csv
from scripts.run_aerograph_prompt_pack import write_jsonl
from scripts.run_aerograph_prompt_pack import write_latex_table
from vlm.aerograph_prompt import parse_aerograph_response
from scripts.aerograph_response_validation import validate_response_row


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSONL row") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_number}: row must be a JSON object")
            rows.append(payload)
    return rows


def response_text(row: dict[str, Any]) -> str:
    for key in ("response", "response_text", "raw_text", "raw_response", "model_output", "output"):
        value = row.get(key)
        if value not in (None, ""):
            return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return json.dumps(row, ensure_ascii=False)


def keys_for(row: dict[str, Any], fallback_index: int, *, object_id_is_unique: bool) -> list[str]:
    keys: list[str] = []
    scenario_id = row.get("scenario_id")
    object_id = row.get("object_id")
    if scenario_id not in (None, "") and object_id not in (None, ""):
        keys.append(f"scenario_object:{scenario_id}:{object_id}")
    for key_name in ("index", "id"):
        value = row.get(key_name)
        if value not in (None, ""):
            keys.append(f"index:{value}")
    if object_id_is_unique and object_id not in (None, ""):
        keys.append(f"object:{object_id}")
    keys.append(f"index:{fallback_index}")
    return list(dict.fromkeys(str(key) for key in keys))


def write_template(prompt_rows: list[dict[str, Any]], path: Path, limit: int = 0) -> None:
    rows = prompt_rows[:limit] if limit else prompt_rows
    template_rows = []
    for index, row in enumerate(rows, start=1):
        template_rows.append(
            {
                "index": index,
                "scenario_id": row.get("scenario_id"),
                "object_id": row.get("object_id"),
                "candidate_class": row.get("candidate_class"),
                "prompt": row.get("prompt"),
                "response_text": "",
            }
        )
    write_jsonl(path, template_rows)


def import_responses(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(args.repo_root).resolve()
    prompt_path = repo_root / args.prompt_pack
    prompt_rows = read_jsonl(prompt_path)

    if args.template_out:
        write_template(prompt_rows, repo_root / args.template_out, args.template_limit)

    if not args.responses:
        return {
            "status": "aerograph_manual_template_ready",
            "prompt_pack": str(prompt_path.relative_to(repo_root)),
            "template_out": args.template_out,
            "template_limit": args.template_limit,
        }

    response_path = repo_root / args.responses
    response_rows = read_jsonl(response_path)
    object_counts: dict[str, int] = {}
    for row in prompt_rows:
        object_id = row.get("object_id")
        if object_id not in (None, ""):
            key = str(object_id)
            object_counts[key] = object_counts.get(key, 0) + 1
    unique_object_ids = {key for key, count in object_counts.items() if count == 1}

    by_key: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(response_rows, start=1):
        object_id = str(row.get("object_id")) if row.get("object_id") not in (None, "") else ""
        for key in keys_for(row, index, object_id_is_unique=object_id in unique_object_ids):
            by_key[key] = row

    outputs: list[dict[str, Any]] = []
    missing: list[str] = []
    for index, prompt_row in enumerate(prompt_rows, start=1):
        object_id = str(prompt_row.get("object_id")) if prompt_row.get("object_id") not in (None, "") else ""
        prompt_keys = keys_for(prompt_row, index, object_id_is_unique=object_id in unique_object_ids)
        key = prompt_keys[0]
        source = next((by_key[item] for item in prompt_keys if item in by_key), None)
        if source is None:
            missing.append(key)
            if not args.allow_partial:
                continue
            payload = {
                "decision": "uncertain",
                "predicted_class": prompt_row.get("candidate_class"),
                "confidence": 0.0,
                "evidence_clues": ["manual_response_missing"],
                "missing_evidence": "manual_response_missing",
                "recommended_action": "collect non-mock response",
                "provider_runtime": "manual_missing",
            }
            raw_text = ""
        else:
            raw_text = response_text(source)
            payload = parse_aerograph_response(raw_text)
            payload["provider_runtime"] = "manual_nonmock"
            payload["raw_text"] = raw_text

        outputs.append(
            {
                "scenario_id": prompt_row.get("scenario_id"),
                "scenario": prompt_row.get("scenario"),
                "object_id": prompt_row.get("object_id"),
                "candidate_class": prompt_row.get("candidate_class"),
                "graph_reobserve_expected": prompt_row.get("should_reobserve"),
                "provider": args.provider_label,
                "provider_runtime": payload.get("provider_runtime", "manual_nonmock"),
                "decision": payload.get("decision", "uncertain"),
                "predicted_class": payload.get("predicted_class"),
                "confidence": payload.get("confidence", 0.0),
                "recommended_action": payload.get("recommended_action", ""),
                "missing_evidence": payload.get("missing_evidence", ""),
                "evidence_clues": payload.get("evidence_clues", []),
                "elapsed_sec": "",
                "raw": payload,
                "index": index,
            }
        )

    if missing and not args.allow_partial:
        raise SystemExit(
            f"Missing {len(missing)} manual responses. Re-run with --allow-partial "
            f"for a partial import. First missing key: {missing[0]}"
        )

    out_dir = repo_root / args.out_dir
    summary = summarize(outputs)
    nonmock_count = int((summary.get("by_provider_runtime", {}) or {}).get("manual_nonmock", 0) or 0)
    valid_nonmock_count = sum(
        1
        for row in outputs
        if row.get("provider_runtime") == "manual_nonmock" and validate_response_row(row)["valid"]
    )
    invalid_nonmock_examples = [
        {
            "index": row.get("index"),
            "scenario_id": row.get("scenario_id"),
            "object_id": row.get("object_id"),
            "issues": validate_response_row(row)["issues"],
        }
        for row in outputs
        if row.get("provider_runtime") == "manual_nonmock" and not validate_response_row(row)["valid"]
    ][:20]
    complete = nonmock_count == len(prompt_rows) and valid_nonmock_count == len(prompt_rows)
    status = "aerograph_manual_import_complete" if complete else "aerograph_manual_import_partial"
    manifest = {
        "status": status,
        "provider": args.provider_label,
        "prompt_pack": str(prompt_path.relative_to(repo_root)),
        "responses": str(response_path.relative_to(repo_root)),
        "out_dir": str(out_dir.relative_to(repo_root)),
        "summary": summary,
        "non_mock_output_count": nonmock_count,
        "valid_non_mock_output_count": valid_nonmock_count,
        "invalid_non_mock_output_count": max(0, nonmock_count - valid_nonmock_count),
        "invalid_non_mock_examples": invalid_nonmock_examples,
        "non_mock_outputs_ready": complete,
        "missing_response_count": len(missing),
        "missing_response_keys": missing[:20],
        "note": "Manual web/provider import. Review response quality before paper use.",
    }

    write_jsonl(out_dir / "responses.jsonl", outputs)
    write_csv(out_dir / "responses_table.csv", outputs)
    write_latex_table(out_dir / "responses_summary_table.tex", summary, args.provider_label)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Import manual AeroGraph web-provider responses.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--prompt-pack", default="outputs/reports/live/aerograph_prompt_pack/aerograph_prompts_all.jsonl")
    parser.add_argument("--responses", default="", help="JSONL with index/object_id and response_text/model_output fields.")
    parser.add_argument("--out-dir", default="outputs/reasoning/aerograph_prompt_pack_eval_manual")
    parser.add_argument("--provider-label", default="Manual non-mock LLM")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--template-out", default="", help="Optional JSONL template to write for manual completion.")
    parser.add_argument("--template-limit", type=int, default=0)
    args = parser.parse_args()
    print(json.dumps(import_responses(args), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
