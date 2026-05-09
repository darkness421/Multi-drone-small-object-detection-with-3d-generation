"""JSONL save/load utilities for EvidenceToken objects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .token import EvidenceToken


def save_tokens_jsonl(tokens: Iterable[EvidenceToken], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for token in tokens:
            f.write(json.dumps(token.to_dict(), ensure_ascii=False) + "\n")


def load_tokens_jsonl(path: str | Path) -> list[EvidenceToken]:
    path = Path(path)
    tokens: list[EvidenceToken] = []
    if not path.exists():
        return tokens
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        tokens.append(EvidenceToken.from_dict(json.loads(line)))
    return tokens

