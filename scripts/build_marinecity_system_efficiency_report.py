"""Build a MarineCity system-efficiency report from existing smoke artifacts.

The report is intentionally conservative. It measures routing-unit counts from
real detector/reasoner artifacts rather than inventing latency or token-cost
numbers for an unavailable external LLM provider.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "outputs/reports/live"
OUT_MD = LIVE / "marinecity_system_efficiency_report.md"
OUT_CSV = LIVE / "marinecity_system_efficiency_report.csv"
OUT_TEX = ROOT / "paper/tables/marinecity_system_efficiency_table.tex"
GRAPH_DIR = ROOT / "outputs/graphs/marinecity_viewer160_crossview_evidence_graph"

SCENARIOS = [
    ("S0", "locked MarineCity ROI", "uavmarine_s0_viewer160_session_recapture"),
    ("S1", "adjacent overlap", "uavmarine_s1_viewer160_session_recapture"),
    ("S2", "coastline multi-view", "uavmarine_s2_viewer160_session_recapture"),
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def pct(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return 100.0 * numerator / denominator


def fmt(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k): str(v) for k, v in row.items()} for row in csv.DictReader(handle)]


def short_from_node(value: str) -> str:
    for short in ["S0", "S1", "S2"]:
        if short in value:
            return short
    return "UNK"


def action_bucket(value: str) -> str:
    lowered = value.lower().replace("-", "_").replace(" ", "_")
    if "finalize" in lowered:
        return "finalize"
    if "monitor" in lowered:
        return "monitor"
    if "reject" in lowered:
        return "reject"
    if "reobserve" in lowered or "re_observ" in lowered:
        return "reobserve"
    return "other"


def graph_metrics_by_scenario() -> dict[str, dict[str, Any]]:
    hypotheses = read_csv(GRAPH_DIR / "hypothesis_table.csv")
    edges_path = GRAPH_DIR / "edges.json"
    edges = read_json(edges_path) if edges_path.exists() else []
    metrics: dict[str, dict[str, Any]] = {}
    for short, _label, _stem in SCENARIOS:
        rows = [row for row in hypotheses if row.get("scenario_short") == short]
        ambiguity_values: list[float] = []
        action_counts = {"finalize": 0, "monitor": 0, "reject": 0, "reobserve": 0}
        for row in rows:
            try:
                ambiguity_values.append(float(row.get("ambiguity_score", 0.0)))
            except ValueError:
                pass
            bucket = action_bucket(row.get("recommended_action", ""))
            if bucket in action_counts:
                action_counts[bucket] += 1

        edge_counts = {"support": 0, "conflict": 0, "missing": 0}
        for edge in edges:
            source = str(edge.get("source", ""))
            target = str(edge.get("target", ""))
            if short_from_node(f"{source} {target}") != short:
                continue
            edge_type = str(edge.get("edge_type", ""))
            if edge_type == "support":
                edge_counts["support"] += 1
            elif "conflict" in edge_type:
                edge_counts["conflict"] += 1
            elif edge_type == "missing_evidence":
                edge_counts["missing"] += 1

        metrics[short] = {
            "graph_hypotheses": len(rows),
            "mean_ambiguity": sum(ambiguity_values) / max(1, len(ambiguity_values)),
            "edge_counts": edge_counts,
            "action_counts": action_counts,
        }
    return metrics


def build_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    graph_metrics = graph_metrics_by_scenario()
    for short, label, stem in SCENARIOS:
        detector = read_json(ROOT / f"outputs/evidence/{stem}_detector_smoke_conf001/detector_smoke_summary.json")
        reasoning_dir = ROOT / f"outputs/reasoning/{stem}_from_detector_conf001_rule_based"
        summary = read_json(reasoning_dir / "summary.json")
        raw_tokens = int(detector.get("token_count", 0) or 0)
        grouped = int(summary.get("hypothesis_count", 0) or 0)
        graph = graph_metrics.get(short, {})
        edge_counts = graph.get("edge_counts", {"support": 0, "conflict": 0, "missing": 0})
        action_counts = graph.get("action_counts", {"finalize": 0, "monitor": 0, "reject": 0, "reobserve": 0})
        graph_hypotheses = int(graph.get("graph_hypotheses", grouped) or grouped)
        high_ambiguity = int(action_counts.get("reobserve", 0) or 0)
        low_ambiguity = int(action_counts.get("finalize", 0) or 0) + int(action_counts.get("monitor", 0) or 0)
        reasoner_calls = graph_hypotheses
        rows.append(
            {
                "scenario": short,
                "label": label,
                "uav_views": int(detector.get("uav_count", 3) or 3),
                "raw_detector_tokens": raw_tokens,
                "grouped_hypotheses": graph_hypotheses,
                "high_ambiguity_hypotheses": high_ambiguity,
                "low_ambiguity_hypotheses": low_ambiguity,
                "reasoner_calls": reasoner_calls,
                "token_to_graph_reduction": raw_tokens - graph_hypotheses,
                "token_to_graph_reduction_pct": pct(raw_tokens - graph_hypotheses, raw_tokens),
                "external_call_reduction_vs_per_detection": raw_tokens - reasoner_calls,
                "external_call_reduction_vs_per_detection_pct": pct(raw_tokens - reasoner_calls, raw_tokens),
                "mean_ambiguity": float(graph.get("mean_ambiguity", 0.0) or 0.0),
                "support_edges": int(edge_counts.get("support", 0) or 0),
                "conflict_edges": int(edge_counts.get("conflict", 0) or 0),
                "missing_edges": int(edge_counts.get("missing", 0) or 0),
                "finalize_count": int(action_counts.get("finalize", 0) or 0),
                "monitor_count": int(action_counts.get("monitor", 0) or 0),
                "reject_count": int(action_counts.get("reject", 0) or 0),
                "reobserve_count": int(action_counts.get("reobserve", 0) or 0),
            }
        )
    return rows


def total_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total: dict[str, Any] = {
        "scenario": "Total",
        "label": "all scenarios",
        "uav_views": 3,
    }
    for key in [
        "raw_detector_tokens",
        "grouped_hypotheses",
        "high_ambiguity_hypotheses",
        "low_ambiguity_hypotheses",
        "reasoner_calls",
        "token_to_graph_reduction",
        "external_call_reduction_vs_per_detection",
        "support_edges",
        "conflict_edges",
        "missing_edges",
        "finalize_count",
        "monitor_count",
        "reject_count",
        "reobserve_count",
    ]:
        total[key] = sum(int(row[key]) for row in rows)
    total["mean_ambiguity"] = sum(float(row["mean_ambiguity"]) * int(row["grouped_hypotheses"]) for row in rows) / max(
        1, total["grouped_hypotheses"]
    )
    total["token_to_graph_reduction_pct"] = pct(
        total["token_to_graph_reduction"], total["raw_detector_tokens"]
    )
    total["external_call_reduction_vs_per_detection_pct"] = pct(
        total["external_call_reduction_vs_per_detection"], total["raw_detector_tokens"]
    )
    return total


def write_csv(rows: list[dict[str, Any]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "scenario",
        "label",
        "uav_views",
        "raw_detector_tokens",
        "grouped_hypotheses",
        "high_ambiguity_hypotheses",
        "low_ambiguity_hypotheses",
        "reasoner_calls",
        "token_to_graph_reduction",
        "token_to_graph_reduction_pct",
        "external_call_reduction_vs_per_detection",
        "external_call_reduction_vs_per_detection_pct",
        "mean_ambiguity",
        "support_edges",
        "conflict_edges",
        "missing_edges",
        "finalize_count",
        "monitor_count",
        "reject_count",
        "reobserve_count",
    ]
    with OUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_md(rows: list[dict[str, Any]]) -> None:
    lines = [
        "# MarineCity System Efficiency Report",
        "",
        f"Updated: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S KST')}`",
        "",
        "This report quantifies routing-unit efficiency from the current real-Cesium",
        "MarineCity smoke artifacts. It does not claim measured external-LLM latency",
        "because no external provider is currently configured.",
        "",
        "| Scenario | UAV views | Detector tokens | Graph hyp. | Avg. amb. | Edges S/C/M | Actions F/M/R/O | Saved % |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['scenario']} {row['label']} | {row['uav_views']} | "
            f"{row['raw_detector_tokens']} | {row['grouped_hypotheses']} | "
            f"{fmt(row['mean_ambiguity'], 2)} | "
            f"{row['support_edges']}/{row['conflict_edges']}/{row['missing_edges']} | "
            f"{row['finalize_count']}/{row['monitor_count']}/{row['reject_count']}/{row['reobserve_count']} | "
            f"{fmt(row['external_call_reduction_vs_per_detection_pct'])}% |"
        )
    total = rows[-1]
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"Across the three scenarios, detector-only per-box reasoning would route "
            f"`{total['raw_detector_tokens']}` detector outputs downstream. The current "
            f"CoM3D-ACE graph protocol groups them into `{total['grouped_hypotheses']}` "
            "object hypotheses before action routing.",
            "",
            f"This saves `{total['external_call_reduction_vs_per_detection']}` downstream "
            f"routing units, or `{fmt(total['external_call_reduction_vs_per_detection_pct'])}%`, "
            "relative to reasoning over every raw detection independently. The compact",
            "action code is F/M/R/O = finalize/monitor/reject/re-observe.",
            "",
            "Claiming rule: this supports system-routing efficiency. It should not be",
            "presented as measured external LLM latency or dollar cost until an external",
            "provider run is imported.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def latex_escape(text: Any) -> str:
    return str(text).replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")


def write_tex(rows: list[dict[str, Any]]) -> None:
    OUT_TEX.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "% Auto-generated by scripts/build_marinecity_system_efficiency_report.py",
        r"\begin{tabular}{lrrrrll}",
        r"\toprule",
        r"Scenario & Tokens & Hyp. & $\bar{A}$ & Saved \% & S/C/M & F/M/R/O \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(
            f"{latex_escape(row['scenario'])} & {row['raw_detector_tokens']} & "
            f"{row['grouped_hypotheses']} & {fmt(row['mean_ambiguity'], 2)} & "
            f"{fmt(row['external_call_reduction_vs_per_detection_pct'])} & "
            f"{row['support_edges']}/{row['conflict_edges']}/{row['missing_edges']} & "
            f"{row['finalize_count']}/{row['monitor_count']}/{row['reject_count']}/{row['reobserve_count']} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    OUT_TEX.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_rows()
    rows_with_total = rows + [total_row(rows)]
    write_csv(rows_with_total)
    write_md(rows_with_total)
    write_tex(rows_with_total)
    print(
        json.dumps(
            {
                "markdown": str(OUT_MD.relative_to(ROOT)),
                "csv": str(OUT_CSV.relative_to(ROOT)),
                "tex": str(OUT_TEX.relative_to(ROOT)),
                "total": rows_with_total[-1],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
