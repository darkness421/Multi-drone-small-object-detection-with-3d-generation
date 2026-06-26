"""Normalize raw web LLM AeroGraph responses into importable JSONL.

Factory/ChatGPT web UIs often return JSONL inside markdown fences, a JSON array,
or a short prose wrapper. This helper extracts JSON objects, validates the
AeroGraph response schema, and optionally merges them into the manual response
file used by ``scripts/import_aerograph_manual_responses.py``.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.aerograph_response_validation import REQUIRED_KEYS
from scripts.aerograph_response_validation import validate_response_row

SUPPORTED_EXTENSIONS = {".txt", ".md", ".json", ".jsonl"}


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
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSONL row") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_number}: row must be a JSON object")
            rows.append(payload)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_json_text(text: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def parse_jsonl_text(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("```"):
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
        elif isinstance(payload, list):
            rows.extend(item for item in payload if isinstance(item, dict))
    return rows


def fenced_blocks(text: str) -> list[str]:
    pattern = re.compile(r"```(?:json|jsonl)?\s*(.*?)```", flags=re.IGNORECASE | re.DOTALL)
    return [match.group(1).strip() for match in pattern.finditer(text)]


def scan_json_objects(text: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    rows: list[dict[str, Any]] = []
    index = 0
    while index < len(text):
        brace = text.find("{", index)
        bracket = text.find("[", index)
        candidates = [pos for pos in (brace, bracket) if pos != -1]
        if not candidates:
            break
        index = min(candidates)
        try:
            payload, end = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            index += 1
            continue
        if isinstance(payload, dict):
            rows.append(payload)
        elif isinstance(payload, list):
            rows.extend(item for item in payload if isinstance(item, dict))
        index += max(end, 1)
    return rows


def extract_rows(text: str) -> list[dict[str, Any]]:
    sources: list[list[dict[str, Any]]] = []
    sources.append(parse_json_text(text))
    sources.append(parse_jsonl_text(text))
    for block in fenced_blocks(text):
        sources.append(parse_json_text(block))
        sources.append(parse_jsonl_text(block))
    sources.append(scan_json_objects(text))

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in sources:
        for row in source:
            key = json.dumps(row, sort_keys=True, ensure_ascii=False)
            if key not in seen:
                rows.append(row)
                seen.add(key)
    return rows


def row_key(row: dict[str, Any], fallback_index: int) -> str:
    scenario_id = row.get("scenario_id")
    object_id = row.get("object_id")
    if scenario_id not in (None, "") and object_id not in (None, ""):
        return f"scenario_object:{scenario_id}:{object_id}"
    if row.get("index") not in (None, ""):
        return f"index:{row.get('index')}"
    if row.get("id") not in (None, ""):
        return f"index:{row.get('id')}"
    return f"fallback:{fallback_index}"


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    """Keep wrapper rows, and wrap bare AeroGraph payloads when possible."""

    if "response_text" in row or "response" in row or "model_output" in row or "output" in row:
        return row
    if any(key in row for key in REQUIRED_KEYS):
        metadata = {key: value for key, value in row.items() if key not in REQUIRED_KEYS}
        payload = {key: row.get(key) for key in REQUIRED_KEYS}
        metadata["response_text"] = payload
        return metadata
    return row


def merge_rows(existing: list[dict[str, Any]], new_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for index, row in enumerate(existing, start=1):
        key = row_key(row, index)
        if key not in merged:
            order.append(key)
        merged[key] = row
    for index, row in enumerate(new_rows, start=1):
        key = row_key(row, index)
        if key not in merged:
            order.append(key)
        merged[key] = row
    return [merged[key] for key in order]


def resolve_input_paths(repo_root: Path, inputs: list[str]) -> list[Path]:
    paths: list[Path] = []
    for item in inputs:
        raw_path = Path(item)
        path = raw_path if raw_path.is_absolute() else repo_root / raw_path
        if any(char in item for char in "*?[]"):
            matches = [Path(match) for match in glob.glob(str(path))]
        elif path.is_dir():
            matches = [candidate for candidate in sorted(path.iterdir()) if candidate.suffix.lower() in SUPPORTED_EXTENSIONS]
        else:
            matches = [path]
        for match in matches:
            if match.exists() and match.is_file():
                paths.append(match.resolve())
    seen: set[Path] = set()
    unique_paths: list[Path] = []
    for path in paths:
        if path not in seen:
            unique_paths.append(path)
            seen.add(path)
    return unique_paths


def build_report(
    rows: list[dict[str, Any]],
    input_paths: list[Path],
    out_path: Path,
    append_to: Path | None,
    report_json: Path,
    report_md: Path,
) -> dict[str, Any]:
    invalid_examples = []
    valid_count = 0
    for index, row in enumerate(rows, start=1):
        result = validate_response_row(row)
        if result["valid"]:
            valid_count += 1
        elif len(invalid_examples) < 20:
            invalid_examples.append(
                {
                    "line": index,
                    "index": row.get("index"),
                    "scenario_id": row.get("scenario_id"),
                    "object_id": row.get("object_id"),
                    "issues": result["issues"],
                }
            )
    report = {
        "status": "aerograph_web_response_normalized",
        "normalized_rows": len(rows),
        "valid_schema_rows": valid_count,
        "invalid_schema_rows": len(rows) - valid_count,
        "input_files": [str(path) for path in input_paths],
        "normalized_output": str(out_path),
        "append_target": str(append_to) if append_to else "",
        "invalid_examples": invalid_examples,
    }
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# AeroGraph Web Response Normalization",
        "",
        f"- Status: `{report['status']}`",
        f"- Normalized rows: `{report['normalized_rows']}`",
        f"- Valid schema rows: `{report['valid_schema_rows']}`",
        f"- Invalid schema rows: `{report['invalid_schema_rows']}`",
        f"- Input files: `{len(input_paths)}`",
        f"- Normalized output: `{report['normalized_output']}`",
        f"- Append target: `{report['append_target']}`",
    ]
    if invalid_examples:
        lines.extend(["", "## Invalid Examples", ""])
        for item in invalid_examples:
            lines.append(
                f"- line `{item['line']}` index `{item.get('index')}` "
                f"object `{item.get('scenario_id')}:{item.get('object_id')}` issues `{item['issues']}`"
            )
    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def run(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(args.repo_root).resolve()
    out_path = repo_root / args.out
    append_to = repo_root / args.append_to if args.append_to else None
    input_paths = resolve_input_paths(repo_root, args.input)
    if not input_paths:
        raise SystemExit("No input files found for AeroGraph web response normalization.")
    text = "\n".join(
        f"\n\n# Source: {path}\n{path.read_text(encoding='utf-8')}" for path in input_paths
    )
    rows = [normalize_row(row) for row in extract_rows(text)]
    if args.require_valid:
        invalid = [validate_response_row(row) for row in rows if not validate_response_row(row)["valid"]]
        if invalid:
            raise SystemExit(f"Found {len(invalid)} invalid AeroGraph response rows; run without --require-valid to inspect report.")
    if append_to:
        rows = merge_rows(read_jsonl(append_to), rows)
        write_jsonl(append_to, rows)
    write_jsonl(out_path, rows)
    return build_report(
        rows,
        input_paths,
        out_path,
        append_to,
        repo_root / args.report_json,
        repo_root / args.report_md,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--input",
        nargs="+",
        required=True,
        help="Raw web output file(s), directory, or glob: .txt, .md, .json, or .jsonl.",
    )
    parser.add_argument("--out", default="outputs/reasoning/aerograph_manual_responses.normalized.jsonl")
    parser.add_argument("--append-to", default="", help="Optional JSONL file to merge/update, usually outputs/reasoning/aerograph_manual_responses.jsonl.")
    parser.add_argument("--require-valid", action="store_true", help="Fail if any normalized row fails AeroGraph schema validation.")
    parser.add_argument("--report-json", default="outputs/reports/live/aerograph_web_response_normalization_report.json")
    parser.add_argument("--report-md", default="outputs/reports/live/aerograph_web_response_normalization_report.md")
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
