"""Print Windows-friendly environment diagnostics for CoM3D-ACE."""

from __future__ import annotations

import importlib
import importlib.metadata
import platform
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET_CONFIG = ROOT / "configs" / "dataset_roots.yaml"


def package_version(package: str, import_name: str | None = None) -> str:
    import_name = import_name or package
    try:
        module = importlib.import_module(import_name)
        return str(getattr(module, "__version__", importlib.metadata.version(package)))
    except Exception:
        try:
            return importlib.metadata.version(package)
        except Exception:
            return "not installed"


def load_dataset_roots(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import yaml
    except ImportError:
        return {"error": "PyYAML is not installed"}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def print_cuda_info() -> None:
    try:
        import torch
    except ImportError:
        print("CUDA available: torch not installed")
        return

    print(f"CUDA available: {torch.cuda.is_available()}")
    print(f"CUDA device count: {torch.cuda.device_count()}")
    if torch.cuda.is_available():
        for idx in range(torch.cuda.device_count()):
            print(f"GPU {idx}: {torch.cuda.get_device_name(idx)}")
    else:
        print("GPU name: none")


def main() -> None:
    print("CoM3D-ACE Environment Check")
    print(f"Project root: {ROOT}")
    print(f"Python: {platform.python_version()}")
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

    print("")
    print(f"Dataset roots config: {DATASET_CONFIG}")
    roots = load_dataset_roots(DATASET_CONFIG)
    for name, cfg in roots.get("datasets", {}).items():
        print(f"  [{name}]")
        for key, value in cfg.items():
            path = (ROOT / value).resolve() if isinstance(value, str) and not Path(value).is_absolute() else Path(value)
            exists = path.exists()
            print(f"    {key}: {path} (exists={exists})")


if __name__ == "__main__":
    main()

