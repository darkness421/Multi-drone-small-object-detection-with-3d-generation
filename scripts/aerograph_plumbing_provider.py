"""Deterministic AeroGraph provider used only for runner plumbing tests.

This script reads a prompt from stdin and returns a syntactically valid
AeroGraph JSON object. It is deliberately not an LLM and must never be used as
paper evidence.
"""

from __future__ import annotations

import json
import sys


def main() -> None:
    prompt = sys.stdin.read()
    response = {
        "decision": "uncertain",
        "predicted_class": "unknown",
        "confidence": 0.01,
        "evidence_clues": ["plumbing_test_only"],
        "missing_evidence": "non_mock_llm_not_executed",
        "recommended_action": "run_real_openai_factory_or_local_llm_provider",
        "prompt_chars": len(prompt),
    }
    print(json.dumps(response, ensure_ascii=False))


if __name__ == "__main__":
    main()
