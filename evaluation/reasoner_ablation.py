"""Evaluate the final LLM-assisted adjudicator against simpler decision rules."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from reasoning.final_adjudicator import adjudicate_object
from runtime.config import resolve_path


def read_json(path: str | Path) -> Any:
    return json.loads(resolve_path(path).read_text(encoding="utf-8"))


def labels_by_id(labels: list[dict[str, Any]]) -> dict[str, str]:
    return {str(row["object_id"]): str(row.get("class") or row.get("true_class")) for row in labels}


def accuracy(predictions: dict[str, str], labels: dict[str, str]) -> float:
    shared = sorted(set(predictions) & set(labels))
    if not shared:
        return 0.0
    return sum(1 for object_id in shared if predictions[object_id] == labels[object_id]) / len(shared)


def evaluate_reasoner(
    hypotheses: list[dict[str, Any]],
    labels: dict[str, str],
    ambiguity_rows: list[dict[str, Any]] | None = None,
    llm_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    ambiguity = {str(row.get("object_id")): row for row in ambiguity_rows or []}
    llm = {str(row.get("object_id")): row for row in llm_rows or []}
    detector_preds: dict[str, str] = {}
    geometry_preds: dict[str, str] = {}
    llm_assisted_preds: dict[str, str] = {}
    geometry_reobserve_count = 0
    reobserve_count = 0
    for hypothesis in hypotheses:
        object_id = str(hypothesis.get("object_id"))
        detector_decision = adjudicate_object(hypothesis, ambiguity=None, llm_payload=None)
        geometry_decision = adjudicate_object(hypothesis, ambiguity=ambiguity.get(object_id), llm_payload=None)
        full_decision = adjudicate_object(hypothesis, ambiguity=ambiguity.get(object_id), llm_payload=llm.get(object_id))
        detector_preds[object_id] = detector_decision.predicted_class
        geometry_preds[object_id] = geometry_decision.predicted_class
        llm_assisted_preds[object_id] = full_decision.predicted_class
        geometry_reobserve_count += int(geometry_decision.should_reobserve)
        reobserve_count += int(full_decision.should_reobserve)
    n = max(len(hypotheses), 1)
    return [
        {
            "method": "detector_only",
            "final_accuracy": accuracy(detector_preds, labels),
            "reobserve_rate": 0.0,
            "llm_call_rate": 0.0,
            "advantage": "fast, cheap, deterministic",
            "limitation": "weak on ambiguous small or occluded objects",
        },
        {
            "method": "detector_geometry_ambiguity",
            "final_accuracy": accuracy(geometry_preds, labels),
            "reobserve_rate": geometry_reobserve_count / n,
            "llm_call_rate": 0.0,
            "advantage": "uses cross-view geometry and ambiguity without LLM cost",
            "limitation": "cannot use semantic context beyond encoded evidence",
        },
        {
            "method": "llm_final_adjudicator",
            "final_accuracy": accuracy(llm_assisted_preds, labels),
            "reobserve_rate": reobserve_count / n,
            "llm_call_rate": len(llm) / n,
            "advantage": "can use semantic/contextual cues and explain disagreements",
            "limitation": "cost, latency, prompt sensitivity, possible hallucination",
        },
    ]


def write_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    out = resolve_path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["method", "final_accuracy", "reobserve_rate", "llm_call_rate", "advantage", "limitation"]
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate final adjudicator ablation.")
    parser.add_argument("--hypotheses", required=True)
    parser.add_argument("--labels", required=True)
    parser.add_argument("--ambiguity", default=None)
    parser.add_argument("--llm", default=None)
    parser.add_argument("--out", default="outputs/experiments/llm_reasoner_ablation.csv")
    args = parser.parse_args()

    rows = evaluate_reasoner(
        read_json(args.hypotheses),
        labels_by_id(read_json(args.labels)),
        read_json(args.ambiguity) if args.ambiguity else None,
        read_json(args.llm) if args.llm else None,
    )
    write_csv(args.out, rows)
    print(f"Wrote {resolve_path(args.out)}")


if __name__ == "__main__":
    main()
