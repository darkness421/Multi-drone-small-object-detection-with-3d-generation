"""Evidence data structures and always-on evidence generation."""

from .token import EvidenceToken
from .io import load_tokens_jsonl, save_tokens_jsonl
from .crops import extract_crop
from .visualization import render_preview_from_jsonl, render_preview_html

__all__ = [
    "EvidenceToken",
    "load_tokens_jsonl",
    "save_tokens_jsonl",
    "extract_crop",
    "render_preview_from_jsonl",
    "render_preview_html",
]
