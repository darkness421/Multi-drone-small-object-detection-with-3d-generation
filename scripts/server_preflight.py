"""Preflight checks before launching long server baseline training."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from runtime.config import resolve_path
from scripts.check_dataset_ready import inspect_paths
from scripts.check_training_readiness import inspect_data_yaml


@dataclass(slots=True)
class CommandStatus:
    available: bool
    returncode: int | None
    output: str


@dataclass(slots=True)
class TorchCudaStatus:
    torch_version: str
    cuda_version: str | None
    cuda_available: bool
    device_count: int
    device_names: list[str]
    error: str = ""


def run_command(args: list[str], timeout: int = 10) -> CommandStatus:
    executable = shutil.which(args[0])
    if executable is None:
        return CommandStatus(False, None, f"{args[0]} not found")
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return CommandStatus(True, None, str(exc))
    output = "\n".join(part.strip() for part in [result.stdout, result.stderr] if part.strip())
    return CommandStatus(True, result.returncode, output)


def torch_cuda_status() -> TorchCudaStatus:
    try:
        import torch
    except ImportError as exc:
        return TorchCudaStatus("", None, False, 0, [], str(exc))
    try:
        available = bool(torch.cuda.is_available())
        count = int(torch.cuda.device_count())
        names = [torch.cuda.get_device_name(idx) for idx in range(count)]
        return TorchCudaStatus(str(torch.__version__), torch.version.cuda, available, count, names)
    except Exception as exc:
        return TorchCudaStatus(str(torch.__version__), torch.version.cuda, False, 0, [], str(exc))


def build_preflight(
    *,
    paths_config: str | Path,
    data_yamls: list[str],
) -> dict[str, Any]:
    nvidia = run_command(["nvidia-smi"])
    tmux = run_command(["tmux", "-V"])
    torch_status = torch_cuda_status()
    path_rows = inspect_paths(paths_config)
    training_rows = [inspect_data_yaml(path) for path in data_yamls]
    blockers: list[str] = []

    if not tmux.available:
        blockers.append("tmux is not installed")
    if not nvidia.available or nvidia.returncode != 0:
        blockers.append("nvidia-smi is not healthy; NVIDIA driver/GPU runtime is not ready")
    if not torch_status.cuda_available or torch_status.device_count == 0:
        blockers.append("PyTorch CUDA is not available in the active environment")
    for row in path_rows:
        if row.required and not row.ready:
            blockers.append(f"required dataset path is not ready: {row.name} ({row.file_count} files)")
    for row in training_rows:
        if not row.ready:
            blockers.append(f"training data YAML is not ready: {row.data_yaml}")

    return {
        "can_start_training": not blockers,
        "blockers": blockers,
        "commands": {
            "nvidia_smi": asdict(nvidia),
            "tmux": asdict(tmux),
        },
        "torch_cuda": asdict(torch_status),
        "dataset_paths": [asdict(row) for row in path_rows],
        "training_readiness": [asdict(row) for row in training_rows],
        "next_commands": [
            "nvidia-smi",
            "find data/raw/VisDrone2019-DET -type f | head",
            "conda run --no-capture-output -n com3d-ace python -m scripts.convert_datasets",
            "bash scripts/ubuntu/preflight_baseline.sh --strict",
            "bash scripts/ubuntu/train_visdrone_pair_tmux.sh visdrone-pair yolov8n.pt yolo11n.pt 42 100 8 1280",
        ],
    }


def write_markdown(payload: dict[str, Any], path: str | Path) -> None:
    out = resolve_path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Server Baseline Preflight",
        "",
        f"- Can start training: {payload['can_start_training']}",
        "",
        "## Blockers",
        "",
    ]
    blockers = payload.get("blockers", [])
    if blockers:
        lines.extend(f"- {blocker}" for blocker in blockers)
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## CUDA",
            "",
            f"- Torch: {payload['torch_cuda'].get('torch_version', '')}",
            f"- CUDA version: {payload['torch_cuda'].get('cuda_version', '')}",
            f"- CUDA available: {payload['torch_cuda'].get('cuda_available', False)}",
            f"- Device count: {payload['torch_cuda'].get('device_count', 0)}",
            "",
            "## Next Commands",
            "",
        ]
    )
    lines.extend(f"```bash\n{command}\n```" for command in payload.get("next_commands", []))
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run server baseline preflight checks.")
    parser.add_argument("--paths-config", default="configs/paths.ubuntu.yaml")
    parser.add_argument(
        "--data-yaml",
        nargs="+",
        default=["configs/detector/visdrone_yolo_data.yaml"],
    )
    parser.add_argument("--out-json", default="outputs/experiments/server_preflight.json")
    parser.add_argument("--out-md", default="outputs/experiments/server_preflight.md")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    payload = build_preflight(paths_config=args.paths_config, data_yamls=args.data_yaml)
    out_json = resolve_path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(payload, args.out_md)
    print(json.dumps({"can_start_training": payload["can_start_training"], "blockers": payload["blockers"]}, indent=2))
    if args.strict and not payload["can_start_training"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
