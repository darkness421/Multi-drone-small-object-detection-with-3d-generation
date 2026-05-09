"""Prototype re-observation policy simulator."""

from __future__ import annotations

import argparse
import csv
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any


METHODS = [
    "no-reobserve",
    "random",
    "uncertainty-only",
    "information-gain-only",
    "com3d-policy",
]


@dataclass(slots=True)
class CandidateView:
    view_id: str
    information_gain: float
    cost: float
    safety_risk: float = 0.0


def default_candidate_views() -> list[CandidateView]:
    return [
        CandidateView("side", 0.24, 0.18, 0.04),
        CandidateView("front", 0.18, 0.12, 0.03),
        CandidateView("rear", 0.14, 0.11, 0.03),
        CandidateView("closer", 0.30, 0.28, 0.08),
        CandidateView("top_down", 0.08, 0.05, 0.02),
    ]


def choose_view(method: str, ambiguity: float, candidate_views: list[CandidateView], rng: random.Random) -> CandidateView | None:
    if method == "no-reobserve":
        return None
    if method == "random":
        return rng.choice(candidate_views)
    if method == "uncertainty-only":
        return max(candidate_views, key=lambda view: ambiguity)
    if method == "information-gain-only":
        return max(candidate_views, key=lambda view: view.information_gain)
    return max(candidate_views, key=lambda view: ambiguity + view.information_gain - 0.5 * view.cost - view.safety_risk)


def simulate_policy(
    hypotheses: list[dict[str, Any]],
    ambiguity_scores: list[dict[str, Any]],
    *,
    seed: int = 0,
) -> list[dict[str, float | str]]:
    rng = random.Random(seed)
    score_by_id = {row["object_id"]: float(row["ambiguity_score"]) for row in ambiguity_scores}
    candidate_views = default_candidate_views()
    rows = []
    for method in METHODS:
        total_gain = 0.0
        resolved = 0
        reobs_count = 0
        total_cost = 0.0
        for hypothesis in hypotheses:
            object_id = hypothesis.get("object_id")
            ambiguity = score_by_id.get(object_id, float(hypothesis.get("mean_uncertainty", 0.0)))
            view = choose_view(method, ambiguity, candidate_views, rng)
            if view is None:
                continue
            reobs_count += 1
            total_cost += view.cost
            gain = max(0.0, view.information_gain * ambiguity - view.safety_risk)
            total_gain += gain
            if gain > 0.05:
                resolved += 1
        n = max(len(hypotheses), 1)
        rows.append(
            {
                "method": method,
                "final_acc": min(1.0, 0.50 + total_gain / n),
                "ambiguity_resolution_rate": resolved / n,
                "reobs_count": reobs_count,
                "cost": total_cost,
            }
        )
    return rows


def write_csv(rows: list[dict[str, float | str]], out_path: str | Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["method", "final_acc", "ambiguity_resolution_rate", "reobs_count", "cost"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate re-observation policy ablations.")
    parser.add_argument("--hypotheses", required=True)
    parser.add_argument("--ambiguity", required=True)
    parser.add_argument("--out", default="outputs/policy/reobservation_policy_metrics.csv")
    args = parser.parse_args()

    hypotheses = json.loads(Path(args.hypotheses).read_text(encoding="utf-8"))
    ambiguity = json.loads(Path(args.ambiguity).read_text(encoding="utf-8"))
    rows = simulate_policy(hypotheses, ambiguity)
    write_csv(rows, args.out)
    print(f"Wrote policy metrics to {args.out}")


if __name__ == "__main__":
    main()

