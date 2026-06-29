"""Build the viewer160 78-token cross-view routing graph.

This helper combines the three validated MarineCity viewer160 detector-token
files, prefixes token ids to avoid collisions, adds scenario metadata, and then
reuses the cross-view graph builder. The output backs the paper routing table
that reports ambiguity, support/conflict/missing edges, and action counts.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUTS = [
    (
        "S0",
        "uavmarine_s0_viewer160_session_recapture",
        ROOT / "outputs/evidence/uavmarine_s0_viewer160_session_recapture_detector_smoke_conf001/evidence_tokens.jsonl",
    ),
    (
        "S1",
        "uavmarine_s1_viewer160_session_recapture",
        ROOT / "outputs/evidence/uavmarine_s1_viewer160_session_recapture_detector_smoke_conf001/evidence_tokens.jsonl",
    ),
    (
        "S2",
        "uavmarine_s2_viewer160_session_recapture",
        ROOT / "outputs/evidence/uavmarine_s2_viewer160_session_recapture_detector_smoke_conf001/evidence_tokens.jsonl",
    ),
]
DEFAULT_OUT_TOKENS = ROOT / "outputs/evidence/marinecity_viewer160_combined_detector_smoke/evidence_tokens.jsonl"
DEFAULT_GRAPH_DIR = ROOT / "outputs/graphs/marinecity_viewer160_crossview_evidence_graph"
DEFAULT_PAPER_TABLE = ROOT / "paper/tables/marinecity_crossview_evidence_graph_table.tex"


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


def build_combined_tokens(out_tokens: Path) -> dict[str, Any]:
    combined: list[dict[str, Any]] = []
    scenario_counts: dict[str, int] = {}
    for scenario_short, scenario_id, path in DEFAULT_INPUTS:
        rows = read_jsonl(path)
        scenario_counts[scenario_short] = len(rows)
        for row in rows:
            metadata = dict(row.get("metadata") or {})
            metadata["scenario_short"] = scenario_short
            metadata["scenario_id"] = scenario_id
            metadata["source_evidence_tokens"] = str(path.relative_to(ROOT))
            row["metadata"] = metadata
            row["token_id"] = f"{scenario_short}:{row.get('token_id')}"
            row["image_id"] = f"{scenario_short}:{row.get('image_id')}"
            if row.get("object_id"):
                row["object_id"] = f"{scenario_short}:{row['object_id']}"
            combined.append(row)
    write_jsonl(out_tokens, combined)
    manifest = {
        "status": "viewer160_combined_evidence_tokens_ready",
        "token_count": len(combined),
        "scenario_counts": scenario_counts,
        "out_tokens": str(out_tokens.relative_to(ROOT)),
    }
    (out_tokens.parent / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_tokens = (ROOT / args.out_tokens).resolve() if not Path(args.out_tokens).is_absolute() else Path(args.out_tokens)
    graph_dir = (ROOT / args.graph_dir).resolve() if not Path(args.graph_dir).is_absolute() else Path(args.graph_dir)
    paper_table = (ROOT / args.paper_table).resolve() if not Path(args.paper_table).is_absolute() else Path(args.paper_table)
    manifest = build_combined_tokens(out_tokens)
    command = [
        sys.executable,
        "scripts/build_marinecity_crossview_evidence_graph.py",
        "--tokens",
        str(out_tokens),
        "--out-dir",
        str(graph_dir),
        "--paper-table",
        str(paper_table),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    return {
        **manifest,
        "graph_dir": str(graph_dir.relative_to(ROOT)),
        "paper_table": str(paper_table.relative_to(ROOT)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build combined viewer160 MarineCity evidence graph.")
    parser.add_argument("--out-tokens", default=str(DEFAULT_OUT_TOKENS.relative_to(ROOT)))
    parser.add_argument("--graph-dir", default=str(DEFAULT_GRAPH_DIR.relative_to(ROOT)))
    parser.add_argument("--paper-table", default=str(DEFAULT_PAPER_TABLE.relative_to(ROOT)))
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
