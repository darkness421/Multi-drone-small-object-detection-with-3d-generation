"""Run a MarineCity 3D-evidence and reasoner smoke test.

This script can run before the full Isaac capture is available by using the
scenario overlay metadata as planned evidence. When detector EvidenceTokens are
available, pass ``--tokens`` and the same pipeline will summarize real detections
instead. LLM providers are intentionally abstracted so external APIs, a generic
stdin/stdout command, or a deterministic mock can be plugged in without changing
the pipeline.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evidence import EvidenceToken, load_tokens_jsonl
from reasoning.final_adjudicator import adjudicate_object
from vlm.aerograph_prompt import build_aerograph_prompt, parse_aerograph_response


SCENARIO_METADATA = {
    "s0_locked_roi": {
        "title": "Locked MarineCity ROI",
        "ambiguity": ["baseline_multiview_confirmation", "small_object_resolution"],
        "objects": ["car", "van", "truck", "bus", "pedestrian", "person"],
    },
    "s1_adjacent_overlap": {
        "title": "Adjacent/Overlapping Small Objects",
        "ambiguity": ["adjacent_objects", "box_overlap", "nms_false_suppression_risk"],
        "objects": ["car", "van", "truck", "bus", "pedestrian", "person"],
    },
    "s2_coastline_multiview": {
        "title": "Coastline Multi-View Ambiguity",
        "ambiguity": ["view_disagreement", "coastline_reflection", "missing_side_view"],
        "objects": ["car", "van", "truck", "bus", "pedestrian", "person"],
    },
}


def _read_json(path: str | Path | None) -> Any:
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _object_class_from_token(token: EvidenceToken) -> str:
    value = token.metadata.get("class_name") if token.metadata else None
    if value:
        return str(value)
    if token.class_id is not None:
        return str(token.class_id)
    return "unknown"


def _hypotheses_from_tokens(tokens: list[EvidenceToken]) -> list[dict[str, Any]]:
    by_key: dict[str, list[EvidenceToken]] = defaultdict(list)
    for token in tokens:
        key = token.object_id or f"{token.uav_id}_{_object_class_from_token(token)}_{int(token.bbox_center[0] // 80)}_{int(token.bbox_center[1] // 80)}"
        by_key[key].append(token)

    hypotheses = []
    for object_id, group in sorted(by_key.items()):
        class_votes: Counter[str] = Counter()
        confidence_sum: defaultdict[str, float] = defaultdict(float)
        views = []
        uncertainties = []
        for token in group:
            class_name = _object_class_from_token(token)
            class_votes[class_name] += 1
            confidence_sum[class_name] += float(token.confidence)
            uncertainties.append(float(token.uncertainty))
            views.append(
                {
                    "uav_id": token.uav_id,
                    "image_id": token.image_id,
                    "bbox_2d": token.bbox_2d,
                    "confidence": token.confidence,
                    "uncertainty": token.uncertainty,
                    "depth_value": token.depth_value,
                }
            )
        posterior = {
            class_name: confidence_sum[class_name] / max(1, sum(confidence_sum.values()))
            for class_name in confidence_sum
        }
        if not posterior:
            posterior = {"unknown": 1.0}
        view_count = len({token.uav_id for token in group})
        mean_uncertainty = sum(uncertainties) / max(1, len(uncertainties))
        hypotheses.append(
            {
                "object_id": object_id,
                "class_posterior": posterior,
                "confidence": max(posterior.values()),
                "view_count": view_count,
                "views": views,
                "ambiguity_score": min(1.0, mean_uncertainty + (0.18 if view_count < 2 else 0.0)),
                "geometry_residual": 0.35 if view_count >= 2 else 0.65,
                "source": "detector_tokens",
            }
        )
    return hypotheses


def _planned_hypotheses(scenario: str) -> list[dict[str, Any]]:
    meta = SCENARIO_METADATA.get(scenario, SCENARIO_METADATA["s0_locked_roi"])
    hypotheses = []
    for idx, class_name in enumerate(meta["objects"], start=1):
        ambiguous = scenario != "s0_locked_roi" and class_name in {"car", "van", "truck", "pedestrian", "person"}
        if class_name in {"pedestrian", "person"}:
            posterior = {class_name: 0.54 if ambiguous else 0.66, "person": 0.24, "pedestrian": 0.22}
        elif class_name in {"car", "van", "truck"}:
            posterior = {class_name: 0.58 if ambiguous else 0.72, "car": 0.18, "van": 0.14, "truck": 0.10}
        else:
            posterior = {class_name: 0.74, "truck": 0.12, "van": 0.08}
        hypotheses.append(
            {
                "object_id": f"{scenario}_obj_{idx:02d}_{class_name}",
                "class_posterior": posterior,
                "confidence": max(posterior.values()),
                "view_count": 3,
                "ambiguity_score": 0.68 if ambiguous else 0.42,
                "geometry_residual": 0.52 if scenario == "s2_coastline_multiview" and ambiguous else 0.28,
                "source": "scenario_plan",
            }
        )
    return hypotheses


def _ambiguity_rows(hypotheses: list[dict[str, Any]], scenario: str) -> list[dict[str, Any]]:
    meta = SCENARIO_METADATA.get(scenario, SCENARIO_METADATA["s0_locked_roi"])
    rows = []
    for hypothesis in hypotheses:
        score = float(hypothesis.get("ambiguity_score", 0.0))
        tags = list(meta["ambiguity"])
        if score >= 0.62:
            tags.append("high_ambiguity")
        if float(hypothesis.get("geometry_residual", 0.0)) >= 0.5:
            tags.append("geometry_residual")
        rows.append(
            {
                "object_id": hypothesis["object_id"],
                "ambiguity_score": score,
                "reason_tags": sorted(set(tags)),
                "components": {
                    "geometry_residual": float(hypothesis.get("geometry_residual", 0.0)),
                    "view_count": int(hypothesis.get("view_count", 0)),
                },
            }
        )
    return rows


def _rule_based_reason(prompt: str, hypothesis: dict[str, Any], ambiguity: dict[str, Any]) -> dict[str, Any]:
    posterior = hypothesis.get("class_posterior", {})
    predicted = max(posterior, key=posterior.get) if posterior else "unknown"
    score = float(ambiguity.get("ambiguity_score", 0.0))
    decision = "uncertain" if score >= 0.62 else "verified"
    return {
        "decision": decision,
        "predicted_class": predicted,
        "confidence": max(0.35, min(0.88, float(posterior.get(predicted, 0.5)) + (0.08 if decision == "verified" else -0.03))),
        "evidence_clues": ambiguity.get("reason_tags", [])[:4],
        "missing_evidence": "side/oblique confirmation" if decision == "uncertain" else "",
        "recommended_action": "targeted re-observation" if decision == "uncertain" else "finalize",
        "provider": "rule_based_aerograph",
        "raw_prompt_chars": len(prompt),
    }


def _command_reason(prompt: str, command: str) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        input=prompt,
        text=True,
        shell=True,
        check=False,
        capture_output=True,
        timeout=180,
    )
    text = completed.stdout.strip() or completed.stderr.strip()
    payload = parse_aerograph_response(text)
    payload["provider"] = "command"
    payload["returncode"] = completed.returncode
    return payload


def _openai_reason(prompt: str, model: str) -> dict[str, Any]:
    try:
        from openai import OpenAI  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on local env
        return {
            "decision": "uncertain",
            "predicted_class": None,
            "confidence": 0.0,
            "evidence_clues": [],
            "missing_evidence": f"openai_sdk_unavailable:{type(exc).__name__}",
            "recommended_action": "use rule-based verifier or install provider",
            "provider": "openai_unavailable",
        }
    client = OpenAI()
    response = client.responses.create(
        model=model,
        input=prompt,
        temperature=0.0,
    )
    text = getattr(response, "output_text", "")
    payload = parse_aerograph_response(text)
    payload["provider"] = "openai"
    payload["model"] = model
    return payload


def _run_reasoner(provider: str, prompt: str, hypothesis: dict[str, Any], ambiguity: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    if provider == "rule_based":
        return _rule_based_reason(prompt, hypothesis, ambiguity)
    if provider == "command":
        if not args.command:
            return {
                "decision": "uncertain",
                "predicted_class": None,
                "confidence": 0.0,
                "evidence_clues": [],
                "missing_evidence": "command_missing",
                "recommended_action": "set --command or use --provider openai",
                "provider": "command_unconfigured",
            }
        return _command_reason(prompt, args.command)
    if provider == "openai":
        if not os.environ.get("OPENAI_API_KEY"):
            return {
                "decision": "uncertain",
                "predicted_class": None,
                "confidence": 0.0,
                "evidence_clues": [],
                "missing_evidence": "OPENAI_API_KEY_missing",
                "recommended_action": "set API key or use rule-based verifier",
                "provider": "openai_unconfigured",
            }
        return _openai_reason(prompt, args.openai_model)
    raise ValueError(f"Unsupported provider: {provider}")


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.tokens:
        tokens = load_tokens_jsonl(args.tokens)
        hypotheses = _hypotheses_from_tokens(tokens)
        source = "detector_tokens"
    else:
        hypotheses = _planned_hypotheses(args.scenario)
        source = "scenario_plan"
    ambiguity = _ambiguity_rows(hypotheses, args.scenario)
    ambiguity_by_id = {row["object_id"]: row for row in ambiguity}

    llm_rows = []
    prompts = {}
    for hypothesis in hypotheses:
        object_id = hypothesis["object_id"]
        row = ambiguity_by_id[object_id]
        prompt = build_aerograph_prompt(
            scene_summary=f"Real Cesium Haeundae Marine City multi-UAV scenario: {args.scenario}.",
            graph_summary={
                "object_id": object_id,
                "class_posterior": hypothesis.get("class_posterior", {}),
                "view_count": hypothesis.get("view_count", 0),
                "geometry_residual": hypothesis.get("geometry_residual", 0.0),
                "source": hypothesis.get("source", source),
            },
            ambiguity_reasons=row.get("reason_tags", []),
            candidate_classes=list((hypothesis.get("class_posterior") or {}).keys()),
            roi_hints=["Marine City road/coast ROI", "multi-UAV views", args.scenario],
        )
        prompts[object_id] = prompt
        llm_payload = _run_reasoner(args.provider, prompt, hypothesis, row, args)
        llm_rows.append(
            {
                "object_id": object_id,
                "predicted_class": llm_payload.get("predicted_class"),
                "confidence": float(llm_payload.get("confidence") or 0.0),
                "reasons": llm_payload.get("evidence_clues", []),
                "recommended_action": llm_payload.get("recommended_action"),
                "provider": llm_payload.get("provider", args.provider),
                "raw": llm_payload,
            }
        )

    decisions = [
        adjudicate_object(hypothesis, ambiguity=ambiguity_by_id[hypothesis["object_id"]], llm_payload=llm_rows[idx]).to_dict()
        for idx, hypothesis in enumerate(hypotheses)
    ]
    reasoner_providers = sorted({str(row.get("provider", args.provider)) for row in llm_rows})
    summary_provider = reasoner_providers[0] if len(reasoner_providers) == 1 else ",".join(reasoner_providers)
    summary = {
        "status": "marinecity_3d_reasoner_smoke_complete",
        "scenario": args.scenario,
        "source": source,
        "provider": summary_provider,
        "runner_provider": args.provider,
        "hypothesis_count": len(hypotheses),
        "llm_call_count": len(llm_rows),
        "reobserve_count": sum(1 for row in decisions if row["should_reobserve"]),
        "output_dir": str(out_dir),
    }

    (out_dir / "hypotheses.json").write_text(json.dumps(hypotheses, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "ambiguity.json").write_text(json.dumps(ambiguity, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "llm_responses.json").write_text(json.dumps(llm_rows, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "final_decisions.json").write_text(json.dumps(decisions, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "prompts.json").write_text(json.dumps(prompts, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="MarineCity 3D evidence + AeroGraph Reasoner smoke runner.")
    parser.add_argument("--scenario", choices=sorted(SCENARIO_METADATA), default="s0_locked_roi")
    parser.add_argument("--tokens", default=None, help="Optional detector EvidenceToken JSONL from YOLO smoke test.")
    parser.add_argument("--provider", choices=["rule_based", "command", "openai"], default="rule_based")
    parser.add_argument("--command", default=None, help="Generic command that reads prompt from stdin and writes JSON.")
    parser.add_argument("--openai-model", default="gpt-5.1")
    parser.add_argument("--out-dir", default="outputs/reasoning/marinecity_3d_reasoner_smoke")
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
