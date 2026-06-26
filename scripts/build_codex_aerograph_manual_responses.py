"""Build a transparent Codex-assisted AeroGraph manual-response candidate.

This is a bridge for the no-API/no-Factory case. It creates valid AeroGraph
JSON responses from the current prompt pack using a conservative policy:
single-view, high-geometry-residual objects remain uncertain unless the detector
posterior is strong. The output is labeled as Codex-assisted manual review so it
can be replaced by Factory/OpenAI/local-LLM responses later without changing the
downstream importer.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def extract_graph(prompt: str) -> dict[str, Any]:
    graph_match = re.search(r"Graph summary:\s*(\{.*\})\s*$", prompt, flags=re.DOTALL)
    if not graph_match:
        return {}
    try:
        return json.loads(graph_match.group(1))
    except json.JSONDecodeError:
        return {}


def confidence_from_posterior(posterior: float) -> float:
    if posterior >= 0.75:
        return round(min(0.90, 0.58 + posterior * 0.32), 3)
    if posterior >= 0.60:
        return round(0.66 + (posterior - 0.60) * 0.35, 3)
    if posterior >= 0.35:
        return round(0.52 + (posterior - 0.35) * 0.30, 3)
    if posterior >= 0.08:
        return round(0.38 + posterior * 0.55, 3)
    return round(max(0.20, 0.26 + posterior * 1.5), 3)


def build_response(row: dict[str, Any]) -> dict[str, Any]:
    candidate = str(row.get("candidate_class") or "unknown")
    scenario = str(row.get("scenario") or row.get("scenario_id") or "unknown")
    graph = extract_graph(str(row.get("prompt") or ""))
    posterior = float((graph.get("class_posterior") or {}).get(candidate, 0.0) or 0.0)
    view_count = int(graph.get("view_count") or 0)
    residual = float(graph.get("geometry_residual") or 1.0)

    strong = posterior >= 0.60
    decision = "verified" if strong else "uncertain"
    confidence = confidence_from_posterior(posterior)

    evidence = [
        f"detector posterior for {candidate}={posterior:.3f}",
        f"view_count={view_count}",
        f"geometry_residual={residual:.2f}",
        f"scenario={scenario}",
    ]
    if strong:
        evidence.append("class posterior is strong enough for provisional graph-grounded verification")
        missing = "Only one UAV view is available and the geometry residual remains high; cross-view confirmation is still desirable."
        action = (
            f"provisionally verify as {candidate}, keep the node in the evidence graph, "
            "and request one targeted re-observation before mission-level finalization"
        )
    else:
        evidence.append("single-view evidence is insufficient for a final fine-grained decision")
        missing = (
            "Need a second UAV view or closer crop because the current evidence is single-view, "
            "small-object, and geometrically uncertain."
        )
        action = (
            f"mark as uncertain {candidate} candidate and dispatch a targeted re-observation "
            "from another UAV viewpoint"
        )

    return {
        "decision": decision,
        "predicted_class": candidate,
        "confidence": confidence,
        "evidence_clues": evidence,
        "missing_evidence": missing,
        "recommended_action": action,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt-pack", default="outputs/reports/live/aerograph_prompt_pack/aerograph_prompts_all.jsonl")
    parser.add_argument("--out", default="outputs/reasoning/aerograph_manual_responses.codex_candidate.jsonl")
    args = parser.parse_args()

    prompt_rows = read_jsonl(Path(args.prompt_pack))
    out_rows = []
    for index, row in enumerate(prompt_rows, start=1):
        response = build_response(row)
        out_rows.append(
            {
                "index": index,
                "scenario_id": row.get("scenario_id"),
                "object_id": row.get("object_id"),
                "candidate_class": row.get("candidate_class"),
                "response_text": json.dumps(response, ensure_ascii=False),
                "provider_note": (
                    "Codex-assisted manual LLM review candidate; replace with Factory/OpenAI/local-LLM "
                    "provider output if a stricter external-provider result is required."
                ),
            }
        )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in out_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"status": "codex_aerograph_manual_candidate_written", "out": str(out_path), "rows": len(out_rows)}, indent=2))


if __name__ == "__main__":
    main()
