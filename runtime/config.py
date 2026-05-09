"""Pathlib-based config loading utilities for Windows-friendly scripts."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def resolve_path(path: str | Path, *, base: Path = PROJECT_ROOT) -> Path:
    path = Path(path)
    return path if path.is_absolute() else (base / path).resolve()


def _deep_update(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_update(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def read_yaml(path: str | Path) -> dict[str, Any]:
    path = resolve_path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return payload


def load_config(paths: str | Path | Iterable[str | Path]) -> dict[str, Any]:
    if isinstance(paths, (str, Path)):
        paths = [paths]
    merged: dict[str, Any] = {}
    for path in paths:
        merged = _deep_update(merged, read_yaml(path))
    return merged


def configured_dataset_roots(config_path: str | Path = "configs/dataset_roots.yaml") -> dict[str, dict[str, Path]]:
    payload = load_config(config_path)
    roots: dict[str, dict[str, Path]] = {}
    for name, fields in payload.get("datasets", {}).items():
        roots[name] = {key: resolve_path(value) for key, value in fields.items() if isinstance(value, str)}
    return roots

