"""Output directory and logging helpers."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from .config import PROJECT_ROOT, resolve_path


def prepare_run_dir(run_name: str, *, output_root: str | Path = "outputs/runs") -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in run_name)
    run_dir = resolve_path(output_root) / f"{timestamp}_{safe_name}"
    for subdir in ("logs", "metrics", "artifacts"):
        (run_dir / subdir).mkdir(parents=True, exist_ok=True)
    return run_dir


def setup_logging(log_path: str | Path | None = None, *, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("com3d_ace")
    logger.setLevel(level)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_path is not None:
        log_path = resolve_path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger

