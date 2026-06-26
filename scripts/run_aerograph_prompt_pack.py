"""Run AeroGraph prompt-pack evaluation with a real or dry-run provider.

The input prompt pack is produced by ``scripts/build_aerograph_prompt_pack.py``.
This runner keeps provider execution separate from prompt construction so
OpenAI/ChatGPT, Ollama, or any local command can be swapped in without changing
the MarineCity detector/3D pipeline.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from vlm.aerograph_prompt import parse_aerograph_response
from scripts.aerograph_response_validation import validate_response_row


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def command_reason(prompt: str, command: str, timeout: int) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        input=prompt,
        text=True,
        shell=True,
        check=False,
        capture_output=True,
        timeout=timeout,
    )
    text = completed.stdout.strip() or completed.stderr.strip()
    payload = parse_aerograph_response(text)
    payload["provider_runtime"] = "command"
    payload["returncode"] = completed.returncode
    payload["raw_text"] = text
    return payload


def openai_reason(prompt: str, model: str, timeout: int) -> dict[str, Any]:
    if not os.environ.get("OPENAI_API_KEY"):
        return {
            "decision": "uncertain",
            "predicted_class": None,
            "confidence": 0.0,
            "evidence_clues": [],
            "missing_evidence": "OPENAI_API_KEY_missing",
            "recommended_action": "configure OpenAI API key or use --provider command",
            "provider_runtime": "openai_unconfigured",
        }
    try:
        from openai import OpenAI  # type: ignore
    except Exception as exc:
        return {
            "decision": "uncertain",
            "predicted_class": None,
            "confidence": 0.0,
            "evidence_clues": [],
            "missing_evidence": f"openai_sdk_unavailable:{type(exc).__name__}",
            "recommended_action": "install openai package or use --provider command",
            "provider_runtime": "openai_sdk_unavailable",
        }
    client = OpenAI(timeout=timeout)
    response = client.responses.create(model=model, input=prompt, temperature=0.0)
    text = getattr(response, "output_text", "")
    payload = parse_aerograph_response(text)
    payload["provider_runtime"] = "openai"
    payload["model"] = model
    payload["raw_text"] = text
    return payload


def dry_run_reason(row: dict[str, Any]) -> dict[str, Any]:
    """Return a pending marker without pretending to be a non-mock result."""

    return {
        "decision": "uncertain",
        "predicted_class": row.get("candidate_class"),
        "confidence": 0.0,
        "evidence_clues": ["dry_run_only"],
        "missing_evidence": "non_mock_provider_not_executed",
        "recommended_action": "run with --provider openai or --provider command",
        "provider_runtime": "dry_run",
    }


def run_one(row: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    prompt = str(row["prompt"])
    started = time.time()
    if args.provider == "dry-run":
        payload = dry_run_reason(row)
    elif args.provider == "openai":
        payload = openai_reason(prompt, args.openai_model, args.timeout)
    elif args.provider == "command":
        if not args.command:
            payload = {
                "decision": "uncertain",
                "predicted_class": None,
                "confidence": 0.0,
                "evidence_clues": [],
                "missing_evidence": "command_missing",
                "recommended_action": "set --command",
                "provider_runtime": "command_unconfigured",
            }
        else:
            payload = command_reason(prompt, args.command, args.timeout)
    else:
        raise ValueError(f"Unsupported provider: {args.provider}")
    elapsed = time.time() - started

    return {
        "scenario_id": row.get("scenario_id"),
        "scenario": row.get("scenario"),
        "object_id": row.get("object_id"),
        "candidate_class": row.get("candidate_class"),
        "graph_reobserve_expected": row.get("should_reobserve"),
        "provider": args.provider,
        "provider_runtime": payload.get("provider_runtime", args.provider),
        "decision": payload.get("decision", "uncertain"),
        "predicted_class": payload.get("predicted_class"),
        "confidence": payload.get("confidence", 0.0),
        "recommended_action": payload.get("recommended_action", ""),
        "missing_evidence": payload.get("missing_evidence", ""),
        "evidence_clues": payload.get("evidence_clues", []),
        "elapsed_sec": round(elapsed, 3),
        "raw": payload,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "scenario_id",
        "object_id",
        "candidate_class",
        "provider_runtime",
        "decision",
        "predicted_class",
        "confidence",
        "recommended_action",
        "missing_evidence",
        "graph_reobserve_expected",
        "elapsed_sec",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    by_decision: dict[str, int] = {}
    by_runtime: dict[str, int] = {}
    mismatches = 0
    reobserve = 0
    valid_schema = 0
    for row in rows:
        by_decision[str(row.get("decision", "unknown"))] = by_decision.get(str(row.get("decision", "unknown")), 0) + 1
        by_runtime[str(row.get("provider_runtime", "unknown"))] = by_runtime.get(str(row.get("provider_runtime", "unknown")), 0) + 1
        if row.get("candidate_class") and row.get("predicted_class") and row.get("candidate_class") != row.get("predicted_class"):
            mismatches += 1
        action = str(row.get("recommended_action", "")).lower()
        if "re-observ" in action or "reobserv" in action or row.get("graph_reobserve_expected") is True:
            reobserve += 1
        if validate_response_row(row)["valid"]:
            valid_schema += 1
    return {
        "total": total,
        "by_decision": dict(sorted(by_decision.items())),
        "by_provider_runtime": dict(sorted(by_runtime.items())),
        "class_mismatch_count": mismatches,
        "reobserve_or_expected_count": reobserve,
        "valid_schema_count": valid_schema,
        "invalid_schema_count": total - valid_schema,
    }


def is_real_provider_output(row: dict[str, Any]) -> bool:
    return str(row.get("provider_runtime", "")) in {"openai", "command"}


def sorted_outputs(rows_by_index: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    return [rows_by_index[index] for index in sorted(rows_by_index)]


def display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def write_run_artifacts(out_dir: Path, rows: list[dict[str, Any]], provider_label: str, manifest: dict[str, Any] | None = None) -> None:
    summary = summarize(rows)
    write_jsonl(out_dir / "responses.jsonl", rows)
    write_csv(out_dir / "responses_table.csv", rows)
    write_latex_table(out_dir / "responses_summary_table.tex", summary, provider_label)
    if manifest is not None:
        (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def write_latex_table(path: Path, summary: dict[str, Any], provider_label: str) -> None:
    decisions = summary.get("by_decision", {})
    verified = int(decisions.get("verified", 0) or 0)
    uncertain = int(decisions.get("uncertain", 0) or 0)
    rejected = int(decisions.get("rejected", 0) or 0)
    total = int(summary.get("total", 0) or 0)
    lines = [
        r"\begin{tabular}{lrrrrr}",
        r"\toprule",
        r"Provider & Prompts & Verified & Uncertain & Rejected & Class mismatches \\",
        r"\midrule",
        f"{provider_label} & {total} & {verified} & {uncertain} & {rejected} & {summary.get('class_mismatch_count', 0)} \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(args.repo_root).resolve()
    prompt_pack = repo_root / args.prompt_pack
    out_dir = repo_root / args.out_dir
    all_prompt_rows = read_jsonl(prompt_pack)
    indexed_rows = list(enumerate(all_prompt_rows, start=1))
    if args.start_index:
        indexed_rows = [(index, row) for index, row in indexed_rows if index >= args.start_index]
    if args.end_index:
        indexed_rows = [(index, row) for index, row in indexed_rows if index <= args.end_index]
    if args.limit:
        indexed_rows = indexed_rows[: args.limit]

    outputs_by_index: dict[int, dict[str, Any]] = {}
    existing_path = out_dir / "responses.jsonl"
    if args.resume and existing_path.exists():
        for existing in read_jsonl(existing_path):
            try:
                existing_index = int(existing.get("index"))
            except (TypeError, ValueError):
                continue
            outputs_by_index[existing_index] = existing

    checkpoint_every = max(1, int(args.checkpoint_every))
    for item_number, (idx, row) in enumerate(indexed_rows, start=1):
        existing = outputs_by_index.get(idx)
        if args.resume and existing and (is_real_provider_output(existing) or not args.retry_unconfigured):
            continue
        result = run_one(row, args)
        result["index"] = idx
        outputs_by_index[idx] = result
        if args.sleep_sec > 0:
            time.sleep(args.sleep_sec)
        if item_number % checkpoint_every == 0:
            write_run_artifacts(out_dir, sorted_outputs(outputs_by_index), args.provider)

    outputs = sorted_outputs(outputs_by_index)
    summary = summarize(outputs)
    real_runtime_count = sum(
        int(count or 0)
        for runtime, count in (summary.get("by_provider_runtime", {}) or {}).items()
        if runtime in {"openai", "command"}
    )
    total_prompt_count = len(all_prompt_rows)
    covered_real_indices = {
        int(row.get("index"))
        for row in outputs
        if is_real_provider_output(row) and str(row.get("index", "")).isdigit()
    }
    valid_real_indices = {
        int(row.get("index"))
        for row in outputs
        if is_real_provider_output(row)
        and str(row.get("index", "")).isdigit()
        and validate_response_row(row)["valid"]
    }
    invalid_real_examples = [
        {
            "index": row.get("index"),
            "scenario_id": row.get("scenario_id"),
            "object_id": row.get("object_id"),
            "issues": validate_response_row(row)["issues"],
        }
        for row in outputs
        if is_real_provider_output(row) and not validate_response_row(row)["valid"]
    ][:20]
    complete_real_run = total_prompt_count > 0 and len(covered_real_indices) == total_prompt_count
    complete_valid_real_run = total_prompt_count > 0 and len(valid_real_indices) == total_prompt_count
    if args.provider == "dry-run":
        status = "aerograph_eval_dry_run_ready"
        note = "Dry-run results are not non-mock LLM evidence."
    elif args.plumbing_test:
        status = "aerograph_eval_plumbing_test_complete" if complete_real_run else "aerograph_eval_plumbing_test_partial"
        note = "Plumbing-test results verify the runner/import path only; they are not paper evidence."
    elif complete_valid_real_run:
        status = "aerograph_eval_complete"
        note = "Use the CSV/LaTeX outputs as candidate paper artifacts after manual review."
    elif complete_real_run:
        status = "aerograph_eval_complete_needs_schema_fix"
        note = "Every prompt has a provider output, but one or more outputs failed strict AeroGraph schema validation."
    elif real_runtime_count:
        status = "aerograph_eval_partial_nonmock"
        note = "Some prompts received real provider outputs; inspect failures before paper use."
    else:
        status = "aerograph_eval_provider_unconfigured"
        note = "No real provider outputs were produced. Configure OpenAI API key or a command provider."
    manifest = {
        "status": status,
        "provider": args.provider,
        "openai_model": args.openai_model if args.provider == "openai" else "",
        "prompt_pack": display_path(prompt_pack, repo_root),
        "out_dir": display_path(out_dir, repo_root),
        "summary": summary,
        "total_prompt_count": total_prompt_count,
        "selected_prompt_count": len(indexed_rows),
        "covered_real_prompt_count": len(covered_real_indices),
        "non_mock_output_count": real_runtime_count,
        "valid_non_mock_output_count": len(valid_real_indices),
        "invalid_non_mock_output_count": max(0, real_runtime_count - len(valid_real_indices)),
        "invalid_non_mock_examples": invalid_real_examples,
        "paper_claim_allowed": complete_valid_real_run and not args.plumbing_test,
        "non_mock_outputs_ready": status == "aerograph_eval_complete",
        "note": note,
    }

    write_run_artifacts(out_dir, outputs, args.provider, manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AeroGraph prompt-pack evaluation.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--prompt-pack", default="outputs/reports/live/aerograph_prompt_pack/aerograph_prompts_all.jsonl")
    parser.add_argument("--out-dir", default="outputs/reasoning/aerograph_prompt_pack_eval")
    parser.add_argument("--provider", choices=["dry-run", "openai", "command"], default="dry-run")
    parser.add_argument("--openai-model", default=os.environ.get("AEROGRAPH_OPENAI_MODEL", "gpt-5.1"))
    parser.add_argument("--command", default=os.environ.get("AEROGRAPH_COMMAND", ""))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--end-index", type=int, default=0)
    parser.add_argument("--resume", action="store_true", help="Reuse existing responses.jsonl rows in the output directory.")
    parser.add_argument("--retry-unconfigured", action="store_true", help="When resuming, rerun rows that only contain unconfigured/provider-failure markers.")
    parser.add_argument("--checkpoint-every", type=int, default=1, help="Write partial responses every N newly evaluated prompts.")
    parser.add_argument("--sleep-sec", type=float, default=0.0, help="Optional pause between provider calls.")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--plumbing-test", action="store_true", help="Mark outputs as non-paper plumbing validation even if a command returns all rows.")
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
