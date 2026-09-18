#!/usr/bin/env python3
"""Audit the REGR release tree for private paths, secrets, and large assets."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path


TEXT_SUFFIXES = {
    "",
    ".cff",
    ".csv",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
BLOCKED_SUFFIXES = {
    ".7z",
    ".avi",
    ".ckpt",
    ".engine",
    ".mkv",
    ".mov",
    ".mp4",
    ".onnx",
    ".p12",
    ".pem",
    ".pfx",
    ".pth",
    ".pt",
    ".safetensors",
    ".tar",
    ".tgz",
    ".zip",
}
BLOCKED_PARTS = {
    ".git",
    ".idea",
    ".pytest_cache",
    ".venv",
    ".vscode",
    "__pycache__",
    "outputs",
    "runs",
    "third_party",
    "weights",
}
MAX_FILE_BYTES = 10 * 1024 * 1024
SELF = Path(__file__).resolve()


@dataclass
class AuditResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    files_checked: int = 0


def audit(root: Path, *, strict_publication: bool = False) -> AuditResult:
    root = root.resolve()
    result = AuditResult()
    required = {
        "CITATION.cff",
        "GITHUB_RELEASE_CHECKLIST.md",
        "LICENSE-STATUS.md",
        "README.md",
        "RELEASE_MANIFEST.json",
        "SHA256SUMS",
        "THIRD_PARTY_NOTICES.md",
        "ci/github-actions.yml",
        "pyproject.toml",
        "regr/core.py",
        "regr/graph.py",
        "reproducibility/paper_table_map.csv",
    }
    for relative in sorted(required):
        if not (root / relative).is_file():
            result.errors.append(f"missing required file: {relative}")

    patterns = (
        ("Linux user home", re.compile(r"/home/[^/\s]+/")),
        ("mounted private path", re.compile(r"/mnt/[^\s'\"]+")),
        ("Windows user home", re.compile(r"[A-Za-z]:\\\\Users\\\\[^\\\s]+\\\\")),
        ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
        ("GitHub token", re.compile(r"\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}\b")),
        ("API key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
        ("credential in URL", re.compile(r"https?://[^\s/:]+:[^\s/@]+@")),
    )
    authoring_trace = re.compile(
        r"\b(?:co" + "dex|chat" + "gpt|response to reviewer|internal work plan)\b",
        re.IGNORECASE,
    )

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if ".git" in relative.parts:
            continue
        blocked_parts = BLOCKED_PARTS.intersection(relative.parts)
        if blocked_parts:
            result.errors.append(
                f"blocked generated/private path: {relative} "
                f"({', '.join(sorted(blocked_parts))})"
            )
            continue
        result.files_checked += 1
        if path.suffix.lower() in BLOCKED_SUFFIXES:
            result.errors.append(f"blocked binary asset: {relative}")
        if path.stat().st_size > MAX_FILE_BYTES:
            result.errors.append(f"file exceeds 10 MiB: {relative}")
        if path.resolve() == SELF or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            result.errors.append(f"non-text content has text extension: {relative}")
            continue
        for label, pattern in patterns:
            if pattern.search(content):
                result.errors.append(f"{label} found in {relative}")
        if authoring_trace.search(content):
            result.errors.append(f"internal authoring trace found in {relative}")
        if path.suffix.lower() == ".json":
            try:
                json.loads(content)
            except json.JSONDecodeError as exc:
                result.errors.append(f"invalid JSON in {relative}: {exc}")

    if not (root / "LICENSE").is_file():
        message = "project license is not selected; public redistribution remains blocked"
        if strict_publication:
            result.errors.append(message)
        else:
            result.warnings.append(message)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--strict-publication", action="store_true")
    args = parser.parse_args(argv)
    result = audit(args.root, strict_publication=args.strict_publication)
    print(f"checked {result.files_checked} files")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}")
    if result.errors:
        print(f"release audit failed with {len(result.errors)} error(s)")
        return 1
    print("release audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
