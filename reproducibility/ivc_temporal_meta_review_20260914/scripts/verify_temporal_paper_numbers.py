#!/usr/bin/env python3
"""Verify that the narrowed manuscript reports frozen temporal-audit results."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


TRACKERS = ("bytetrack", "ocsort", "deepocsort")
TABLE_MAP = {
    "table_oracle_full50.tex": "oracle_full50.tex",
    "table_detector_full50.tex": "detector_full50.tex",
    "table_confirmation38.tex": "confirmation38.tex",
    "table_temporal_ablation.tex": "ablation.tex",
    "table_m3ot_transfer.tex": "m3ot_transfer.tex",
    "table_mmot_sizes.tex": "mmot_sizes.tex",
    "table_runtime.tex": "runtime.tex",
    "table_error_coverage_fixed.tex": "error_coverage_fixed.tex",
}
ACTIVE_SOURCES = (
    "main.tex",
    "ivc_sections/00_abstract.tex",
    "ivc_sections/01_introduction.tex",
    "ivc_sections/02_related_work.tex",
    "ivc_sections/03_system_method.tex",
    "ivc_sections/05_experimental_protocol.tex",
    "ivc_sections/06_results.tex",
    "ivc_sections/07_discussion.tex",
    "ivc_sections/08_limitations.tex",
    "ivc_sections/08_conclusion.tex",
    "ivc_sections/09_declarations.tex",
    "ivc_sections/09_appendix.tex",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-root", type=Path, required=True)
    parser.add_argument("--paper-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def row(rows: list[dict], tracker: str, method: str) -> dict:
    matches = [item for item in rows if item["tracker"] == tracker and item["method"] == method]
    if len(matches) != 1:
        raise AssertionError(f"expected one result for {tracker}/{method}, found {len(matches)}")
    return matches[0]


def formatted_deltas(rows: list[dict]) -> tuple[list[str], list[str]]:
    idf1 = []
    idsw = []
    for tracker in TRACKERS:
        base = row(rows, tracker, "no_refinement")
        ours = row(rows, tracker, "com3d_reciprocal_guard")
        idf1.append(f"{ours['IDF1'] - base['IDF1']:.2f}")
        idsw.append(f"{int(base['IDSW'] - ours['IDSW']):,}")
    return idf1, idsw


def require(checks: list[dict], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "PASS" if condition else "FAIL", "detail": detail})


def main() -> int:
    args = parse_args()
    experiment_root = args.experiment_root.resolve()
    paper_root = args.paper_root.resolve()
    ready = experiment_root / "results_raw/paper_ready"
    numbers = json.loads((ready / "key_numbers.json").read_text(encoding="utf-8"))
    checks: list[dict] = []

    for generated, manuscript in TABLE_MAP.items():
        source = (ready / generated).read_bytes()
        target = (paper_root / "ivc_tables/temporal" / manuscript).read_bytes()
        require(checks, f"table:{manuscript}", source == target, "byte-identical to generated frozen-result table")

    active_text = "\n".join((paper_root / path).read_text(encoding="utf-8") for path in ACTIVE_SOURCES)
    abstract = (paper_root / "ivc_sections/00_abstract.tex").read_text(encoding="utf-8")
    abstract_flat = " ".join(abstract.split())
    results = (paper_root / "ivc_sections/06_results.tex").read_text(encoding="utf-8")
    main_tex = (paper_root / "main.tex").read_text(encoding="utf-8")

    oracle_idf1, oracle_idsw = formatted_deltas(numbers["oracle_full50"])
    detector_idf1, detector_idsw = formatted_deltas(numbers["detector_full50"])
    require(
        checks,
        "oracle:abstract-deltas",
        ", ".join(oracle_idf1[:2]) in abstract_flat and oracle_idf1[2] in abstract_flat
        and all(value in abstract_flat for value in oracle_idsw),
        f"IDF1={oracle_idf1}; IDSW reductions={oracle_idsw}",
    )
    require(
        checks,
        "detector:abstract-deltas",
        ", ".join(detector_idf1[:2]) in abstract_flat and detector_idf1[2] in abstract_flat
        and all(value in abstract_flat for value in detector_idsw),
        f"IDF1={detector_idf1}; IDSW reductions={detector_idsw}",
    )
    require(
        checks,
        "oracle:results-deltas",
        all(value in results for value in oracle_idf1 + oracle_idsw),
        f"reported full-precision-derived deltas {oracle_idf1 + oracle_idsw}",
    )
    require(
        checks,
        "detector:results-deltas",
        all(value in results for value in detector_idf1 + detector_idsw),
        f"reported full-precision-derived deltas {detector_idf1 + detector_idsw}",
    )

    m3ot = numbers["m3ot_transfer"]
    held = {item["tracker"]: item for item in m3ot if item["split"] == "held_out"}
    m3ot_deltas = [f"{abs(held[name]['delta_IDF1']):.2f}" for name in ("bytetrack", "ocsort")]
    require(
        checks,
        "m3ot:held-out-deltas",
        all(value in results for value in m3ot_deltas)
        and sum(int(item["accepted_false"]) for item in held.values()) == 10
        and "All ten admitted held-out links" in results,
        f"IDF1 decreases={m3ot_deltas}; known false accepted links=10",
    )

    expected_title = "Reciprocal Evidence-Graph Tracklet Refinement for Aerial Multi-Object Tracking"
    require(checks, "scope:title", expected_title in main_tex, expected_title)
    require(
        checks,
        "metadata:authors",
        all(name in main_tex for name in ("Jong-Chan", "So-Hee", "Sujin", "Sang-Min", "Gun-Woo"))
        and main_tex.count("\\corref{corresponding}") == 2,
        "five named authors and two corresponding-author markers",
    )
    forbidden = re.compile(r"\b(?:TODO|TBD|FIXME|XXX)\b|Anonymous Author|MarineCity|BuckTales|SAFR-YOLO", re.I)
    hits = sorted(set(match.group(0) for match in forbidden.finditer(active_text)))
    require(checks, "scope:no-stale-claims-or-markers", not hits, f"hits={hits}")

    pdf = paper_root / "main.pdf"
    pdf_text = subprocess.run(
        ["pdftotext", "-layout", str(pdf), "-"], check=True, capture_output=True, text=True
    ).stdout
    pdf_hits = sorted(set(match.group(0) for match in forbidden.finditer(pdf_text)))
    require(checks, "pdf:no-stale-claims-or-markers", not pdf_hits, f"hits={pdf_hits}")
    require(checks, "pdf:title", expected_title in " ".join(pdf_text.split()), "title present in rendered PDF")

    failed = [item for item in checks if item["status"] != "PASS"]
    report = {
        "status": "PASS" if not failed else "FAIL",
        "policy": "All manuscript result tables must be generated from frozen CSVs; repeated deltas are recomputed before display rounding.",
        "paper_root": str(paper_root),
        "experiment_root": str(experiment_root),
        "checks": checks,
        "failed_checks": [item["name"] for item in failed],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": len(checks), "failed": len(failed)}))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
