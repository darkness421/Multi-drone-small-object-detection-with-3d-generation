"""Strict AeroGraph response validation for paper-promotion gates."""

from __future__ import annotations

import json
import re
from typing import Any


REQUIRED_KEYS = [
    "decision",
    "predicted_class",
    "confidence",
    "evidence_clues",
    "missing_evidence",
    "recommended_action",
]
ALLOWED_DECISIONS = {"verified", "rejected", "uncertain"}
RESPONSE_KEYS = ("response", "response_text", "raw_text", "raw_response", "model_output", "output")


def response_value(row: dict[str, Any]) -> Any:
    for key in RESPONSE_KEYS:
        value = row.get(key)
        if value not in (None, ""):
            return value
    if isinstance(row.get("raw"), dict):
        return row["raw"]
    if any(key in row for key in REQUIRED_KEYS):
        return {key: row.get(key) for key in REQUIRED_KEYS}
    return None


def parse_response_object(value: Any) -> tuple[dict[str, Any] | None, list[str]]:
    if value in (None, ""):
        return None, ["response_missing"]
    if isinstance(value, dict):
        return value, []
    if not isinstance(value, str):
        return None, [f"unsupported_response_type:{type(value).__name__}"]
    text = value.strip()
    if not text:
        return None, ["response_blank"]
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return None, ["json_parse_failed"]
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None, ["json_parse_failed"]
    if not isinstance(parsed, dict):
        return None, ["response_json_not_object"]
    return parsed, []


def validate_aerograph_payload(payload: dict[str, Any] | None) -> list[str]:
    if payload is None:
        return ["response_missing"]
    issues: list[str] = []
    for key in REQUIRED_KEYS:
        if key not in payload:
            issues.append(f"missing_key:{key}")

    decision = payload.get("decision")
    if not isinstance(decision, str) or decision not in ALLOWED_DECISIONS:
        issues.append("invalid_decision")

    predicted_class = payload.get("predicted_class")
    if not isinstance(predicted_class, str) or not predicted_class.strip():
        issues.append("invalid_predicted_class")

    confidence = payload.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        issues.append("invalid_confidence")
    elif not 0.0 <= float(confidence) <= 1.0:
        issues.append("confidence_out_of_range")

    if not isinstance(payload.get("evidence_clues"), list):
        issues.append("invalid_evidence_clues")
    if not isinstance(payload.get("missing_evidence"), str):
        issues.append("invalid_missing_evidence")
    if not isinstance(payload.get("recommended_action"), str) or not payload.get("recommended_action", "").strip():
        issues.append("invalid_recommended_action")
    if payload.get("missing_evidence") == "json_parse_failed":
        issues.append("json_parse_failed_payload")
    return issues


def validate_response_row(row: dict[str, Any]) -> dict[str, Any]:
    value = response_value(row)
    payload, parse_issues = parse_response_object(value)
    schema_issues = validate_aerograph_payload(payload) if payload is not None else []
    issues = parse_issues + schema_issues
    return {
        "present": value not in (None, ""),
        "valid": not issues,
        "issues": issues,
        "payload": payload,
    }
