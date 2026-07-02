"""Evaluate the external CSFPR-RTDETR VisDrone checkpoint.

This is intentionally separate from the main Ultralytics runner because
CSFPR-RTDETR ships a forked RT-DETR implementation and checkpoint classes.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def patch_torch_load() -> None:
    """Allow loading the trusted CSFPR checkpoint saved before PyTorch 2.6."""

    import torch

    original_load = torch.load

    def patched_load(*args, **kwargs):  # type: ignore[no-untyped-def]
        kwargs.setdefault("weights_only", False)
        return original_load(*args, **kwargs)

    torch.load = patched_load  # type: ignore[assignment]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="external/CSFPR-RTDETR")
    parser.add_argument("--weights", default="weights/visdrone.pt")
    parser.add_argument("--data", default="dataset/visdrone_local.yaml")
    parser.add_argument("--split", default="val")
    parser.add_argument("--imgsz", type=int, default=1280)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--device", default="0")
    parser.add_argument("--project", default="../../outputs/detectors/related_work_detectors")
    parser.add_argument("--name", default="csfpr_rtdetr_visdrone_eval")
    args = parser.parse_args()

    root = Path.cwd()
    repo = (root / args.repo).resolve()
    if not repo.exists():
        raise SystemExit(f"Missing CSFPR repo: {repo}")

    os.environ.setdefault("MPLCONFIGDIR", str(root / ".cache" / "matplotlib"))
    os.environ.setdefault("YOLO_CONFIG_DIR", str(root / ".cache" / "ultralytics"))
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
    Path(os.environ["YOLO_CONFIG_DIR"]).mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(repo))
    os.chdir(repo)
    patch_torch_load()

    from ultralytics import RTDETR  # noqa: PLC0415

    model = RTDETR(args.weights)
    result = model.val(
        data=args.data,
        split=args.split,
        imgsz=args.imgsz,
        batch=args.batch,
        workers=args.workers,
        device=args.device,
        project=args.project,
        name=args.name,
    )

    payload = {
        "method": "CSFPR-RTDETR",
        "weights": str((repo / args.weights).resolve()),
        "data": str((repo / args.data).resolve()),
        "split": args.split,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "device": args.device,
        "project": args.project,
        "name": args.name,
        "results_dict": getattr(result, "results_dict", None),
        "save_dir": str(getattr(result, "save_dir", "")),
    }
    out_dir = (root / "outputs" / "experiments").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "csfpr_rtdetr_eval_latest.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
