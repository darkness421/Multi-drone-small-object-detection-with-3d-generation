#!/usr/bin/env python3
"""Build a measured TinyFReLU response panel from a trained SAFR-YOLO checkpoint.

The figure is intentionally small and paper-facing: it probes the first
TinySpatialFReLU block in the selected VisDrone checkpoint, records the input
feature, high-frequency residual, spatial condition, and output, then produces a
supplementary panel that can replace purely illustrative response sketches.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplconfig"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import torch
from PIL import Image, ImageDraw


CHECKPOINT = ROOT / (
    "outputs/detectors/server_yolov11_p2p4_balanced/"
    "20260610_073629_proposed_p2p4_balanced_selfattn_tiny_frelu_yolo11l_"
    "visdrone_yolov11_p2_balanced_seed123/ultralytics/weights/best.pt"
)
IMAGE = ROOT / "data/processed/visdrone_yolo/images/val/0000295_02400_d_0000033.jpg"
LABEL = ROOT / "data/processed/visdrone_yolo/labels/val/0000295_02400_d_0000033.txt"
PAPER_FIG = ROOT / "paper/figures/figS2b_tinyfrelu_measured_response.png"
LIVE_DIR = ROOT / "outputs/reports/live/tinyfrelu_measured_response"
LIVE_FIG = LIVE_DIR / "figS2b_tinyfrelu_measured_response.png"
SUMMARY = LIVE_DIR / "summary.json"


def normalize_map(x: np.ndarray, lo_pct: float = 1.0, hi_pct: float = 99.0) -> np.ndarray:
    lo, hi = np.percentile(x, [lo_pct, hi_pct])
    if hi <= lo:
        return np.zeros_like(x, dtype=np.float32)
    y = (x - lo) / (hi - lo)
    return np.clip(y, 0.0, 1.0).astype(np.float32)


def load_visdrone_image_with_boxes(size: tuple[int, int]) -> Image.Image:
    image = Image.open(IMAGE).convert("RGB")
    native_w, native_h = image.size
    draw = ImageDraw.Draw(image)
    if LABEL.exists():
        for line in LABEL.read_text().splitlines():
            parts = line.split()
            if len(parts) < 5:
                continue
            cls, xc, yc, bw, bh = map(float, parts[:5])
            x0 = (xc - bw / 2.0) * native_w
            y0 = (yc - bh / 2.0) * native_h
            x1 = (xc + bw / 2.0) * native_w
            y1 = (yc + bh / 2.0) * native_h
            area = bw * bh
            color = (255, 108, 31) if area < 0.0025 else (39, 113, 216)
            width = 2 if area < 0.0025 else 1
            draw.rectangle([x0, y0, x1, y1], outline=color, width=width)
    return image.resize(size, Image.Resampling.BILINEAR)


def make_input_tensor(image_size: tuple[int, int]) -> torch.Tensor:
    image = Image.open(IMAGE).convert("RGB").resize(image_size, Image.Resampling.BILINEAR)
    arr = np.asarray(image).astype(np.float32) / 255.0
    return torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)


def bin_response(x: np.ndarray, condition: np.ndarray, output: np.ndarray, bins: int = 36) -> dict[str, np.ndarray]:
    rng = np.linspace(np.percentile(x, 1), np.percentile(x, 99), bins + 1)
    centers = (rng[:-1] + rng[1:]) / 2.0
    cond_mean = np.full(bins, np.nan, dtype=np.float32)
    out_mean = np.full(bins, np.nan, dtype=np.float32)
    counts = np.zeros(bins, dtype=np.int64)
    ids = np.digitize(x, rng) - 1
    for idx in range(bins):
        mask = ids == idx
        counts[idx] = int(mask.sum())
        if counts[idx] > 0:
            cond_mean[idx] = float(np.mean(condition[mask]))
            out_mean[idx] = float(np.mean(output[mask]))
    valid = counts > 0
    return {
        "centers": centers[valid],
        "condition": cond_mean[valid],
        "output": out_mean[valid],
        "counts": counts[valid],
    }


def main() -> int:
    sys.path.insert(0, str(ROOT))
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    PAPER_FIG.parent.mkdir(parents=True, exist_ok=True)

    if not CHECKPOINT.exists():
        raise FileNotFoundError(CHECKPOINT)
    if not IMAGE.exists():
        raise FileNotFoundError(IMAGE)

    ckpt = torch.load(CHECKPOINT, map_location="cpu", weights_only=False)
    model = ckpt["model"].float().eval()

    records: dict[str, dict[str, torch.Tensor | float | tuple[int, ...]]] = {}
    handles = []
    for name, module in model.named_modules():
        if module.__class__.__name__ != "TinySpatialFReLU":
            continue

        def make_hook(module_name: str):
            def hook(mod, inp, out):
                x = inp[0].detach().float().cpu()
                with torch.no_grad():
                    edge = x - mod.blur(x).detach().float().cpu()
                    condition = (
                        mod.condition(x.to(next(mod.parameters()).device)).detach().float().cpu()
                        + torch.tanh(mod.edge_gain.detach().float().cpu()) * edge
                    )
                y = out.detach().float().cpu()
                records[module_name] = {
                    "x": x,
                    "edge": edge,
                    "condition": condition,
                    "y": y,
                    "edge_gain": float(mod.edge_gain.detach().float().cpu()),
                    "shape": tuple(x.shape),
                }

            return hook

        handles.append(module.register_forward_hook(make_hook(name)))

    image_size = (1280, 736)
    x_in = make_input_tensor(image_size)
    with torch.no_grad():
        _ = model(x_in)
    for handle in handles:
        handle.remove()

    if not records:
        raise RuntimeError("No TinySpatialFReLU module was recorded.")

    # The first TinySpatialFReLU has the highest spatial resolution and is the
    # most relevant probe for tiny-object boundary preservation.
    module_name = sorted(records.keys(), key=lambda k: records[k]["shape"][2], reverse=True)[0]
    rec = records[module_name]
    feature = rec["x"].numpy()[0]
    edge = rec["edge"].numpy()[0]
    condition = rec["condition"].numpy()[0]
    output = rec["y"].numpy()[0]

    feature_energy = normalize_map(np.mean(np.abs(feature), axis=0))
    residual_energy = normalize_map(np.mean(np.abs(edge), axis=0))
    condition_energy = normalize_map(np.mean(np.abs(condition), axis=0))
    delta = output - feature
    positive_delta = normalize_map(np.mean(np.maximum(delta, 0.0), axis=0), 0.5, 99.5)
    gate_fraction = np.mean(condition > feature, axis=0)

    flat_feature = feature.reshape(-1)
    flat_condition = condition.reshape(-1)
    flat_output = output.reshape(-1)
    response = bin_response(flat_feature, flat_condition, flat_output)

    changed = np.abs(delta) > 1e-5
    summary = {
        "checkpoint": str(CHECKPOINT.relative_to(ROOT)),
        "image": str(IMAGE.relative_to(ROOT)),
        "label": str(LABEL.relative_to(ROOT)),
        "module": module_name,
        "feature_shape": list(rec["shape"]),
        "edge_gain": rec["edge_gain"],
        "mean_abs_edge": float(np.mean(np.abs(edge))),
        "mean_positive_delta": float(np.mean(np.maximum(delta, 0.0))),
        "changed_fraction": float(np.mean(changed)),
        "gate_fraction_mean": float(np.mean(gate_fraction)),
    }

    plt.rcParams.update(
        {
            "font.size": 8,
            "axes.titlesize": 9,
            "axes.labelsize": 8,
            "legend.fontsize": 7,
        }
    )
    fig = plt.figure(figsize=(13.2, 3.7), dpi=240)
    gs = fig.add_gridspec(
        1,
        5,
        width_ratios=[1.12, 1.0, 1.0, 1.45, 1.45],
        left=0.035,
        right=0.985,
        bottom=0.18,
        top=0.86,
        wspace=0.34,
    )

    ax0 = fig.add_subplot(gs[0])
    ax0.imshow(load_visdrone_image_with_boxes((360, 207)))
    ax0.set_title("(a) VisDrone crop used for probing")
    ax0.text(
        0.02,
        0.02,
        "orange: tiny boxes\nblue: larger boxes",
        transform=ax0.transAxes,
        va="bottom",
        ha="left",
        color="white",
        fontsize=7,
        bbox={"facecolor": "black", "alpha": 0.45, "pad": 3, "edgecolor": "none"},
    )
    ax0.axis("off")

    maps = [
        ("high-frequency residual |h(x)|", residual_energy, "magma"),
        ("positive output delta", positive_delta, "inferno"),
    ]
    for i, (title, data, cmap) in enumerate(maps):
        ax = fig.add_subplot(gs[i + 1])
        ax.imshow(data, cmap=cmap)
        ax.set_title(f"(b{i + 1}) {title}")
        ax.axis("off")

    ax_curve = fig.add_subplot(gs[3:5])
    centers = response["centers"]
    ax_curve.plot(centers, centers, color="0.45", linestyle="--", linewidth=1.2, label="identity")
    ax_curve.plot(centers, response["condition"], color="#f97316", linewidth=1.7, label="mean c(x)")
    ax_curve.plot(centers, response["output"], color="#2563eb", linewidth=1.9, label="mean y=max(x,c(x))")
    ax_curve.fill_between(
        centers,
        np.minimum(centers, response["output"]),
        np.maximum(centers, response["output"]),
        color="#2563eb",
        alpha=0.12,
        linewidth=0,
    )
    ax_curve.set_title("(c) measured feature-response curve")
    ax_curve.set_xlabel("TinyFReLU input feature value")
    ax_curve.set_ylabel("response", labelpad=2)
    ax_curve.grid(True, linewidth=0.35, alpha=0.35)
    ax_curve.legend(loc="upper left", frameon=False)

    fig.savefig(PAPER_FIG, bbox_inches="tight", facecolor="white")
    fig.savefig(LIVE_FIG, bbox_inches="tight", facecolor="white")
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(PAPER_FIG)
    print(LIVE_FIG)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
