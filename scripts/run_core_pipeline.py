"""Run EvidenceToken -> graph -> ambiguity -> policy pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ambiguity.ambiguity_scorer import score_file
from graph.graph_builder import build_object_hypotheses
from policy.policy_simulator import simulate_policy, write_csv
from evidence import load_tokens_jsonl
from scripts.make_dummy_evidence import make_dummy_tokens
from evidence import save_tokens_jsonl


def run_pipeline(tokens_path: Path, output_dir: Path, *, make_dummy: bool = False) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if make_dummy or not tokens_path.exists():
        tokens_path.parent.mkdir(parents=True, exist_ok=True)
        save_tokens_jsonl(make_dummy_tokens(), tokens_path)

    tokens = load_tokens_jsonl(tokens_path)
    hypotheses = build_object_hypotheses(tokens, threshold=2.0)

    hypotheses_path = output_dir / "object_hypotheses.json"
    hypotheses_path.write_text(
        json.dumps([hypothesis.to_dict() for hypothesis in hypotheses], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    ambiguity_path = output_dir / "ambiguity_scores.json"
    scores = score_file(hypotheses_path, ambiguity_path)

    policy_path = output_dir / "policy_metrics.csv"
    write_csv(simulate_policy([hypothesis.to_dict() for hypothesis in hypotheses], scores), policy_path)

    return {"tokens": tokens_path, "hypotheses": hypotheses_path, "ambiguity": ambiguity_path, "policy": policy_path}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the core CoM3D-ACE prototype pipeline.")
    parser.add_argument("--tokens", default="outputs/evidence/dummy_tokens.jsonl")
    parser.add_argument("--out-dir", default="outputs/core_pipeline")
    parser.add_argument("--make-dummy", action="store_true")
    args = parser.parse_args()

    outputs = run_pipeline(Path(args.tokens), Path(args.out_dir), make_dummy=args.make_dummy)
    print(json.dumps({key: str(value) for key, value in outputs.items()}, indent=2))


if __name__ == "__main__":
    main()

