"""Print environment diagnostics for CoM3D-ACE on Windows or Ubuntu."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import os
import platform
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET_CONFIG = ROOT / "configs" / "dataset_roots.yaml"
UBUNTU_PATHS_CONFIG = ROOT / "configs" / "paths.ubuntu.yaml"


def package_version(package: str, import_name: str | None = None) -> str:
    import_name = import_name or package
    try:
        return importlib.metadata.version(package)
    except Exception:
        try:
            module = importlib.import_module(import_name)
            return str(getattr(module, "__version__", "installed"))
        except Exception:
            return "not installed"


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import yaml
    except ImportError:
        return {"error": "PyYAML is not installed"}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def resolve_config_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (ROOT / path).resolve()


def print_cuda_info() -> None:
    try:
        import torch
    except ImportError:
        print("Torch version: not installed")
        print("CUDA available: torch not installed")
        return

    print(f"Torch version: {getattr(torch, '__version__', 'unknown')}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    print(f"CUDA device count: {torch.cuda.device_count()}")
    if torch.cuda.is_available():
        for idx in range(torch.cuda.device_count()):
            print(f"GPU {idx}: {torch.cuda.get_device_name(idx)}")
    else:
        print("GPU name: none")


def print_dataset_roots(config_path: Path) -> None:
    print("")
    print(f"Dataset roots config: {config_path}")
    roots = load_yaml(config_path)
    for name, cfg in roots.get("datasets", {}).items():
        print(f"  [{name}]")
        for key, value in cfg.items():
            if not isinstance(value, str):
                print(f"    {key}: {value}")
                continue
            path = resolve_config_path(value)
            print(f"    {key}: {path} (exists={path.exists()})")


def print_server_paths(config_path: Path) -> None:
    print("")
    print(f"Ubuntu/server paths config: {config_path}")
    payload = load_yaml(config_path)
    if not payload:
        print("  not configured")
        return
    for section in ("datasets", "outputs", "logs", "cache"):
        values = payload.get(section, {})
        if not values:
            continue
        print(f"  [{section}]")
        for key, value in values.items():
            if isinstance(value, str):
                path = resolve_config_path(value)
                print(f"    {key}: {path} (exists={path.exists()})")
            else:
                print(f"    {key}: {value}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Print CoM3D-ACE environment diagnostics.")
    parser.add_argument("--dataset-config", default=str(DATASET_CONFIG))
    parser.add_argument("--paths-config", default=str(UBUNTU_PATHS_CONFIG))
    args = parser.parse_args()

    print("CoM3D-ACE Environment Check")
    print(f"Project root: {ROOT}")
    print(f"Python: {platform.python_version()}")
    print(f"Python executable: {platform.python_implementation()} / {Path(sys.executable)}")
    print(f"Conda env: {os.environ.get('CONDA_DEFAULT_ENV', '') or 'not active'}")
    print(f"Platform: {platform.platform()}")
    print_cuda_info()
    print("")
    print("Package versions:")
    for package, import_name in [
        ("torch", "torch"),
        ("torchvision", "torchvision"),
        ("ultralytics", "ultralytics"),
        ("opencv-python", "cv2"),
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("scikit-learn", "sklearn"),
        ("matplotlib", "matplotlib"),
        ("PyYAML", "yaml"),
    ]:
        print(f"  {package}: {package_version(package, import_name)}")

    print_dataset_roots(resolve_config_path(args.dataset_config))
    print_server_paths(resolve_config_path(args.paths_config))


if __name__ == "__main__":
    main()
