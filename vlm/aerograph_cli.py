"""Build an AeroGraph Reasoner prompt from graph summary and ambiguity reasons."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .aerograph_prompt import build_aerograph_prompt_from_paths, expected_json_schema, parse_aerograph_response
except ImportError:
    from aerograph_prompt import build_aerograph_prompt_from_paths, expected_json_schema, parse_aerograph_response


def main() -> None:
    parser = argparse.ArgumentParser(description="Build AeroGraph prompt text or parse an AeroGraph response.")
    parser.add_argument("--crop", action="append", default=[])
    parser.add_argument("--graph-summary", required=True)
    parser.add_argument("--reason", action="append", default=[])
    parser.add_argument("--out-prompt", default=None)
    parser.add_argument("--parse-response", default=None)
    args = parser.parse_args()

    graph_summary = json.loads(Path(args.graph_summary).read_text(encoding="utf-8"))
    prompt = build_aerograph_prompt_from_paths(crop_paths=args.crop, graph_summary=graph_summary, ambiguity_reasons=args.reason)
    if args.out_prompt:
        Path(args.out_prompt).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_prompt).write_text(prompt, encoding="utf-8")
        print(f"Wrote AeroGraph prompt to {args.out_prompt}")
    else:
        print(prompt)
    print(json.dumps({"expected_json_schema": expected_json_schema()}, indent=2))

    if args.parse_response:
        print(json.dumps(parse_aerograph_response(Path(args.parse_response).read_text(encoding="utf-8")), indent=2))


if __name__ == "__main__":
    main()
