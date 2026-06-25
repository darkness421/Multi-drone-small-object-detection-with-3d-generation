"""Check LaTeX patch bundles for missing inputs, figures, labels, and stale gates."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PAPER_ROOT = REPO_ROOT / "paper"

INPUT_RE = re.compile(r"(?<!%)\\input\{([^}]+)\}")
GRAPHICS_RE = re.compile(r"(?<!%)\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
LABEL_RE = re.compile(r"\\label\{([^}]+)\}")
REF_RE = re.compile(r"\\(?:ref|autoref|cref|Cref)\{([^}]+)\}")
COMMENTED_INPUT_RE = re.compile(r"^\s*%\s*\\input\{([^}]+)\}", re.MULTILINE)

ALLOWED_PENDING_CONTEXT = {
    "paper/tables/aerograph_reasoner_results_placeholder.tex",
    "paper/tables/marinecity_system_scenario_table.tex",
    "paper/sections/06_marinecity_3d_readiness.tex",
    "paper/sections/main_results_patch_bundle.tex",
    "paper/sections/supplementary_patch_bundle.tex",
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def latex_path(raw: str) -> Path:
    path = PAPER_ROOT / raw
    if path.suffix:
        return path
    return path.with_suffix(".tex")


def figure_candidates(raw: str) -> list[Path]:
    path = PAPER_ROOT / raw
    if path.suffix:
        return [path]
    return [path.with_suffix(ext) for ext in [".pdf", ".png", ".jpg", ".jpeg"]]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def collect_latex(root: Path, visited: set[Path] | None = None) -> tuple[set[Path], list[dict[str, str]]]:
    visited = visited or set()
    missing: list[dict[str, str]] = []
    if root in visited:
        return visited, missing
    visited.add(root)
    text = read_text(root)
    for raw in INPUT_RE.findall(text):
        child = latex_path(raw)
        if not child.exists():
            missing.append({"source": rel(root), "input": raw, "expected": rel(child)})
            continue
        _visited, child_missing = collect_latex(child, visited)
        missing.extend(child_missing)
    return visited, missing


def commented_inputs(path: Path) -> list[str]:
    own_stem = rel(path.with_suffix(""))
    raw_items = COMMENTED_INPUT_RE.findall(read_text(path))
    return [item for item in raw_items if item not in {own_stem, own_stem.replace("paper/", "")}]


def check_graphics(files: set[Path]) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    for path in sorted(files):
        for raw in GRAPHICS_RE.findall(read_text(path)):
            candidates = figure_candidates(raw)
            if not any(candidate.exists() for candidate in candidates):
                missing.append(
                    {
                        "source": rel(path),
                        "figure": raw,
                        "expected_any": ", ".join(rel(candidate) for candidate in candidates),
                    }
                )
    return missing


def label_report(files: set[Path]) -> tuple[dict[str, list[str]], list[dict[str, str]], list[dict[str, str]]]:
    labels: dict[str, list[str]] = {}
    refs: list[dict[str, str]] = []
    for path in sorted(files):
        text = read_text(path)
        for label in LABEL_RE.findall(text):
            labels.setdefault(label, []).append(rel(path))
        for reference in REF_RE.findall(text):
            refs.append({"source": rel(path), "ref": reference})
    duplicates = [
        {"label": label, "sources": "; ".join(sources)}
        for label, sources in sorted(labels.items())
        if len(sources) > 1
    ]
    unresolved = [row for row in refs if row["ref"] not in labels]
    return labels, duplicates, unresolved


def pending_rows(files: set[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(files):
        rel_path = rel(path)
        text = read_text(path)
        for line_number, line in enumerate(text.splitlines(), start=1):
            if "PENDING" not in line and "pending" not in line:
                continue
            status = "allowed" if rel_path in ALLOWED_PENDING_CONTEXT else "review"
            rows.append(
                {
                    "source": rel_path,
                    "line": str(line_number),
                    "status": status,
                    "text": line.strip()[:220],
                }
            )
    return rows


def build(args: argparse.Namespace) -> dict[str, Any]:
    bundles = [PAPER_ROOT / item for item in args.bundles]
    bundle_reports: list[dict[str, Any]] = []
    all_files: set[Path] = set()
    all_missing_inputs: list[dict[str, str]] = []
    for bundle in bundles:
        files, missing_inputs = collect_latex(bundle)
        all_files.update(files)
        all_missing_inputs.extend(missing_inputs)
        bundle_reports.append(
            {
                "bundle": rel(bundle),
                "exists": bundle.exists(),
                "included_file_count": len(files),
                "included_files": [rel(path) for path in sorted(files)],
                "commented_optional_inputs": commented_inputs(bundle),
            }
        )

    missing_graphics = check_graphics(all_files)
    _labels, duplicate_labels, unresolved_refs = label_report(all_files)
    pending = pending_rows(all_files)
    pending_review = [row for row in pending if row["status"] != "allowed"]
    status = "latex_patch_integrity_ok"
    if all_missing_inputs or missing_graphics or duplicate_labels or unresolved_refs or pending_review:
        status = "latex_patch_integrity_needs_attention"

    return {
        "updated_at_kst": datetime.now().strftime("%Y-%m-%d %H:%M:%S KST"),
        "status": status,
        "bundles": bundle_reports,
        "checked_file_count": len(all_files),
        "missing_input_count": len(all_missing_inputs),
        "missing_graphics_count": len(missing_graphics),
        "duplicate_label_count": len(duplicate_labels),
        "unresolved_ref_count": len(unresolved_refs),
        "pending_review_count": len(pending_review),
        "missing_inputs": all_missing_inputs,
        "missing_graphics": missing_graphics,
        "duplicate_labels": duplicate_labels,
        "unresolved_refs": unresolved_refs,
        "pending_rows": pending,
    }


def table(rows: list[dict[str, Any]], fields: list[str]) -> list[str]:
    lines = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return lines


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# LaTeX Patch Integrity Check",
        "",
        f"Updated: `{report['updated_at_kst']}`",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
        f"- Checked files: `{report['checked_file_count']}`",
        f"- Missing inputs: `{report['missing_input_count']}`",
        f"- Missing graphics: `{report['missing_graphics_count']}`",
        f"- Duplicate labels: `{report['duplicate_label_count']}`",
        f"- Unresolved refs: `{report['unresolved_ref_count']}`",
        f"- Pending rows needing review: `{report['pending_review_count']}`",
        "",
        "## Bundles",
        "",
    ]
    lines.extend(table(report["bundles"], ["bundle", "exists", "included_file_count", "commented_optional_inputs"]))
    for key, title, fields in [
        ("missing_inputs", "Missing Inputs", ["source", "input", "expected"]),
        ("missing_graphics", "Missing Graphics", ["source", "figure", "expected_any"]),
        ("duplicate_labels", "Duplicate Labels", ["label", "sources"]),
        ("unresolved_refs", "Unresolved Refs", ["source", "ref"]),
        ("pending_rows", "Pending Mentions", ["source", "line", "status", "text"]),
    ]:
        rows = report[key]
        if rows:
            lines.extend(["", f"## {title}", ""])
            lines.extend(table(rows, fields))
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundles",
        nargs="*",
        default=[
            "sections/main_results_patch_bundle.tex",
            "sections/supplementary_patch_bundle.tex",
        ],
    )
    parser.add_argument("--out-json", default="outputs/reports/live/latex_patch_integrity_check.json")
    parser.add_argument("--out-md", default="outputs/reports/live/latex_patch_integrity_check.md")
    args = parser.parse_args()
    report = build(args)
    out_json = REPO_ROOT / args.out_json
    out_md = REPO_ROOT / args.out_md
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(out_md, report)
    print(json.dumps({"json": rel(out_json), "markdown": rel(out_md), "status": report["status"]}, indent=2))


if __name__ == "__main__":
    main()
