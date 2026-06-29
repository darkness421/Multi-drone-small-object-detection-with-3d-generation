"""Build a paper-safe MarineCity re-observation policy ablation.

The ablation uses the validated viewer160 cross-view evidence graph. It does
not invent new detector accuracy labels; it reports how different decision
policies allocate graph hypotheses to finalize/monitor/reject/re-observe.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GRAPH_DIR = ROOT / "outputs/graphs/marinecity_viewer160_crossview_evidence_graph"
LIVE_DIR = ROOT / "outputs/reports/live"
OUT_CSV = LIVE_DIR / "marinecity_reobservation_policy_ablation.csv"
OUT_MD = LIVE_DIR / "marinecity_reobservation_policy_ablation.md"
OUT_TEX = ROOT / "paper/tables/marinecity_reobservation_policy_ablation_table.tex"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k): str(v) for k, v in row.items()} for row in csv.DictReader(handle)]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def scenario_from_node(value: str) -> str:
    for scenario in ("S0", "S1", "S2"):
        if scenario in value:
            return scenario
    return "UNK"


def edge_counts_by_scenario() -> dict[str, Counter[str]]:
    counts: dict[str, Counter[str]] = {"S0": Counter(), "S1": Counter(), "S2": Counter()}
    edges = read_json(GRAPH_DIR / "edges.json") if (GRAPH_DIR / "edges.json").exists() else []
    for edge in edges:
        scenario = scenario_from_node(f"{edge.get('source', '')} {edge.get('target', '')}")
        if scenario not in counts:
            continue
        edge_type = str(edge.get("edge_type", ""))
        if edge_type == "support":
            counts[scenario]["support"] += 1
        elif "conflict" in edge_type:
            counts[scenario]["conflict"] += 1
        elif edge_type == "missing_evidence":
            counts[scenario]["missing"] += 1
    return counts


def action_bucket(value: str) -> str:
    lowered = value.lower().replace("-", "_").replace(" ", "_")
    if "finalize" in lowered:
        return "finalize"
    if "monitor" in lowered:
        return "monitor"
    if "reject" in lowered:
        return "reject"
    if "reobserve" in lowered or "re_observe" in lowered:
        return "reobserve"
    return "monitor"


def scenario_stats(rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    edge_counts = edge_counts_by_scenario()
    stats: dict[str, dict[str, Any]] = {}
    for scenario in ("S0", "S1", "S2"):
        subset = [row for row in rows if row.get("scenario_short") == scenario]
        amb = [float(row.get("ambiguity_score", 0.0) or 0.0) for row in subset]
        high = [row for row in subset if float(row.get("ambiguity_score", 0.0) or 0.0) >= 0.85]
        stats[scenario] = {
            "n": len(subset),
            "mean_ambiguity": sum(amb) / max(1, len(amb)),
            "high_count": len(high),
            "edges": edge_counts.get(scenario, Counter()),
        }
    return stats


def summarize_policy(name: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    actions = Counter({"finalize": 0, "monitor": 0, "reject": 0, "reobserve": 0})
    high_total = 0
    high_covered = 0
    for row in rows:
        ambiguity = float(row.get("ambiguity_score", 0.0) or 0.0)
        view_count = int(float(row.get("view_count", 0) or 0))
        token_count = int(float(row.get("token_count", 0) or 0))
        quality = row.get("association_quality", "")
        if ambiguity >= 0.85:
            high_total += 1

        if name == "No active re-observation":
            action = "monitor"
        elif name == "Uncertainty only":
            action = "reobserve" if ambiguity >= 0.90 else "monitor"
        elif name == "Support only":
            action = "monitor" if view_count >= 2 else "reobserve"
        elif name == "Conflict/missing aware":
            action = "reobserve" if view_count < 2 or token_count <= 1 or ambiguity >= 0.90 else "monitor"
        elif name == "Ours":
            action = action_bucket(row.get("recommended_action", ""))
        else:
            action = "monitor"

        if quality == "single_view_candidate" and name == "Ours" and action != "reobserve":
            action = "reject"

        actions[action] += 1
        if ambiguity >= 0.85 and action in {"reobserve", "reject"}:
            high_covered += 1

    n = max(1, len(rows))
    return {
        "policy": name,
        "graph_units": len(rows),
        "mean_ambiguity": sum(float(row.get("ambiguity_score", 0.0) or 0.0) for row in rows) / n,
        "finalize": actions["finalize"],
        "monitor": actions["monitor"],
        "reject": actions["reject"],
        "reobserve": actions["reobserve"],
        "high_ambiguity_handled_pct": 100.0 * high_covered / max(1, high_total),
        "action_load": actions["monitor"] + actions["reobserve"],
    }


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    hypotheses = read_rows(GRAPH_DIR / "hypothesis_table.csv")
    policies = [
        "No active re-observation",
        "Support only",
        "Uncertainty only",
        "Conflict/missing aware",
        "Ours",
    ]
    rows = [summarize_policy(policy, hypotheses) for policy in policies]
    scenario = scenario_stats(hypotheses)
    return rows, scenario


def write_csv(rows: list[dict[str, Any]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_tex(rows: list[dict[str, Any]]) -> None:
    OUT_TEX.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        r"\begin{tabular}{lrrrrrr}",
        r"\toprule",
        r"Policy & Units & $\bar{A}$ & F/M/R/O & High handled & Action load \\",
        r"\midrule",
    ]
    for row in rows:
        label = str(row["policy"]).replace("&", r"\&")
        f_m_r_o = f"{row['finalize']}/{row['monitor']}/{row['reject']}/{row['reobserve']}"
        lines.append(
            f"{label} & {row['graph_units']} & {row['mean_ambiguity']:.2f} & "
            f"{f_m_r_o} & {row['high_ambiguity_handled_pct']:.1f}\\% & {row['action_load']} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    OUT_TEX.write_text("\n".join(lines), encoding="utf-8")


def write_md(rows: list[dict[str, Any]], scenario: dict[str, Any]) -> None:
    lines = [
        "# MarineCity Re-observation Policy Ablation",
        "",
        f"Updated: `{datetime.now().astimezone().isoformat(timespec='seconds')}`",
        "",
        "The ablation is computed from the viewer160 real-Cesium cross-view",
        "evidence graph. It compares action allocation policies over the same",
        "17 graph hypotheses and reports action load rather than external LLM",
        "latency.",
        "",
        "| Policy | Units | Avg. ambiguity | F/M/R/O | High-ambiguity handled | Action load |",
        "| --- | ---: | ---: | --- | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['policy']} | {row['graph_units']} | {row['mean_ambiguity']:.2f} | "
            f"{row['finalize']}/{row['monitor']}/{row['reject']}/{row['reobserve']} | "
            f"{row['high_ambiguity_handled_pct']:.1f}% | {row['action_load']} |"
        )
    lines.extend(["", "## Scenario evidence", ""])
    for key in ("S0", "S1", "S2"):
        item = scenario[key]
        edges = item["edges"]
        lines.append(
            f"- {key}: hypotheses={item['n']}, avg_ambiguity={item['mean_ambiguity']:.2f}, "
            f"high={item['high_count']}, edges S/C/M="
            f"{edges.get('support', 0)}/{edges.get('conflict', 0)}/{edges.get('missing', 0)}"
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows, scenario = build_rows()
    write_csv(rows)
    write_tex(rows)
    write_md(rows, scenario)
    print(
        json.dumps(
            {
                "csv": str(OUT_CSV.relative_to(ROOT)),
                "tex": str(OUT_TEX.relative_to(ROOT)),
                "markdown": str(OUT_MD.relative_to(ROOT)),
                "rows": rows,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
