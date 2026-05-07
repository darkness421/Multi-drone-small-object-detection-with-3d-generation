"""SAGE prompt builder and robust JSON parser."""

from __future__ import annotations

import json
import re
from typing import Any


SAGE_SCHEMA = {
    "decision": "verified|rejected|uncertain",
    "predicted_class": "string",
    "confidence": 0.0,
    "evidence_clues": [],
    "missing_evidence": "string",
    "recommended_action": "string",
}


def build_sage_prompt(
    *,
    scene_summary: str,
    graph_summary: dict[str, Any],
    ambiguity_reasons: list[str],
    candidate_classes: list[str],
    roi_hints: list[str] | None = None,
) -> str:
    roi_hints = roi_hints or []
    return "\n".join(
        [
            "You are SAGE: Scene-aware Ambiguity-guided Graph Evidence verifier.",
            "Use the structured graph metadata and multi-view crop descriptions to verify the object class.",
            "Return only valid JSON following this schema:",
            json.dumps(SAGE_SCHEMA, indent=2),
            "",
            f"Scene: {scene_summary}",
            f"Candidate classes: {candidate_classes}",
            f"Ambiguity reasons: {ambiguity_reasons}",
            f"ROI hints: {roi_hints}",
            "Graph summary:",
            json.dumps(graph_summary, indent=2),
        ]
    )


def parse_sage_response(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return {
                "decision": "uncertain",
                "predicted_class": None,
                "confidence": 0.0,
                "evidence_clues": [],
                "missing_evidence": "json_parse_failed",
                "recommended_action": "active re-observe",
                "raw_response": text,
            }
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError:
            return {
                "decision": "uncertain",
                "predicted_class": None,
                "confidence": 0.0,
                "evidence_clues": [],
                "missing_evidence": "json_parse_failed",
                "recommended_action": "active re-observe",
                "raw_response": text,
            }

    payload.setdefault("decision", "uncertain")
    payload.setdefault("predicted_class", None)
    payload.setdefault("confidence", 0.0)
    payload.setdefault("evidence_clues", [])
    payload.setdefault("missing_evidence", "")
    payload.setdefault("recommended_action", "VLM verify")
    return payload

