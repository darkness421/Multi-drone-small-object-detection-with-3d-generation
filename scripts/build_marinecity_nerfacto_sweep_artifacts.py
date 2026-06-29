"""Build MarineCity Nerfacto iteration-sweep artifacts.

The main 3D comparison table should keep only representative method rows. This
helper keeps the Nerfacto iteration variants separate so longer training runs
can be inspected without polluting the main claim.
"""

from __future__ import annotations

import csv
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "outputs/experiments/3d_generation/nerfstudio_native_runs"
OUT_CSV = ROOT / "outputs/reports/live/marinecity_nerfacto_iteration_sweep.csv"
OUT_MD = ROOT / "outputs/reports/live/marinecity_nerfacto_iteration_sweep.md"
OUT_PNG = ROOT / "outputs/reports/live/marinecity_nerfacto_iteration_sweep.png"
OUT_TEX = ROOT / "paper/tables/marinecity_nerfacto_iteration_sweep_table.tex"

REPRESENTATIVE_STATUS = "complete_native_marinecity_nerfacto_torch_split067_noapp_fullres_24k"


def numeric(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_iters(text: str) -> int | None:
    match = re.search(r"max_iters=(\d+)", text)
    if match:
        return int(match.group(1))
    match = re.search(r"_(\d+)k(?:_|$)", text)
    if match:
        return int(match.group(1)) * 1000
    return None


def variant_label(path: Path, row: dict[str, Any]) -> str:
    blob = " ".join([path.name, str(row.get("status") or ""), str(row.get("notes") or "")]).lower()
    if "fullres32k" in blob:
        return "full-res 32k"
    if "fullres24k" in blob or "fullres_24k" in blob:
        return "full-res 24k"
    if "fullres12k" in blob or "fullres_12k" in blob:
        return "full-res 12k"
    if "scale075" in blob:
        return "scale 0.75 24k"
    if "latestv2" in blob:
        iters = parse_iters(blob)
        return f"latest capture {iters // 1000}k" if iters else "latest capture"
    iters = parse_iters(blob)
    return f"standard {iters // 1000}k" if iters else "standard"


def paper_use(path: Path, row: dict[str, Any]) -> str:
    status = str(row.get("status") or "")
    if status == REPRESENTATIVE_STATUS:
        return "representative"
    if "fullres32k" in path.name.lower() or "fullres32k" in status.lower():
        return "auxiliary: degraded"
    if "latestv2" in path.name.lower() or "latestv2" in status.lower():
        return "auxiliary: capture variant"
    return "supplementary sweep"


def read_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(RUN_DIR.glob("*metric_row.json")):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if str(row.get("method") or "").lower() != "nerfacto":
            continue
        psnr = numeric(row.get("PSNR"))
        ssim = numeric(row.get("SSIM"))
        lpips = numeric(row.get("LPIPS"))
        if psnr is None or ssim is None or lpips is None:
            continue
        blob = " ".join([path.name, str(row.get("status") or ""), str(row.get("notes") or "")])
        iters = parse_iters(blob)
        if iters is None:
            continue
        rows.append(
            {
                "variant": variant_label(path, row),
                "iters": iters,
                "PSNR": psnr,
                "SSIM": ssim,
                "LPIPS": lpips,
                "FPS": numeric(row.get("FPS")),
                "paper_use": paper_use(path, row),
                "status": row.get("status") or "",
                "source": str(path.relative_to(ROOT)),
            }
        )
    return sorted(rows, key=lambda item: ((item["iters"] or 0), item["variant"]))


def fmt(value: Any, digits: int = 3) -> str:
    number = numeric(value)
    if number is None:
        return "--"
    return f"{number:.{digits}f}"


def write_csv(rows: list[dict[str, Any]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["variant", "iters", "PSNR", "SSIM", "LPIPS", "FPS", "paper_use", "status", "source"],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_md(rows: list[dict[str, Any]]) -> None:
    best = max(rows, key=lambda item: item["PSNR"]) if rows else None
    representative = next((row for row in rows if row["paper_use"] == "representative"), None)
    lines = [
        "# MarineCity Nerfacto Iteration Sweep",
        "",
        f"Updated: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S KST')}`",
        "",
        "This auxiliary sweep separates Nerfacto iteration/capture variants from the main 3D method comparison.",
        "The representative paper row remains the full-resolution 24k run unless a later run improves quality without changing the capture protocol.",
        "",
    ]
    if representative:
        lines.append(
            f"- Representative row: `{representative['variant']}` "
            f"PSNR={fmt(representative['PSNR'], 2)}, SSIM={fmt(representative['SSIM'])}, LPIPS={fmt(representative['LPIPS'])}."
        )
    if best:
        lines.append(
            f"- Highest PSNR in sweep: `{best['variant']}` "
            f"PSNR={fmt(best['PSNR'], 2)}, SSIM={fmt(best['SSIM'])}, LPIPS={fmt(best['LPIPS'])}; use=`{best['paper_use']}`."
        )
    lines.extend(
        [
            "- The 32k reinforcement run is kept as auxiliary evidence because its quality degraded under the tested split/capture setting.",
            "",
            "| Variant | Iters | PSNR | SSIM | LPIPS | FPS | Paper use |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in sorted(rows, key=lambda item: item["PSNR"], reverse=True):
        lines.append(
            f"| {row['variant']} | {row['iters']} | {fmt(row['PSNR'], 2)} | {fmt(row['SSIM'])} | "
            f"{fmt(row['LPIPS'])} | {fmt(row['FPS'], 2)} | {row['paper_use']} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def latex_escape(text: Any) -> str:
    return (
        str(text or "")
        .replace("\\", r"\textbackslash{}")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("_", r"\_")
        .replace("#", r"\#")
    )


def write_tex(rows: list[dict[str, Any]]) -> None:
    OUT_TEX.parent.mkdir(parents=True, exist_ok=True)
    ranked = sorted(rows, key=lambda item: item["PSNR"], reverse=True)
    lines = [
        "% Auto-generated by scripts/build_marinecity_nerfacto_sweep_artifacts.py",
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"Variant & Iters & PSNR$\uparrow$ & SSIM$\uparrow$ & LPIPS$\downarrow$ \\",
        r"\midrule",
    ]
    for row in ranked:
        variant = latex_escape(row["variant"])
        iters = str(row["iters"])
        psnr = fmt(row["PSNR"], 2)
        ssim = fmt(row["SSIM"])
        lpips = fmt(row["LPIPS"])
        if row["paper_use"] == "representative":
            variant = rf"\textbf{{{variant}}}"
            iters = rf"\textbf{{{iters}}}"
            psnr = rf"\textbf{{{psnr}}}"
            ssim = rf"\textbf{{{ssim}}}"
            lpips = rf"\textbf{{{lpips}}}"
        lines.append(
            f"{variant} & {iters} & {psnr} & {ssim} & {lpips} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    OUT_TEX.write_text("\n".join(lines), encoding="utf-8")


def write_png(rows: list[dict[str, Any]]) -> None:
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplconfig"))
    (ROOT / ".mplconfig").mkdir(exist_ok=True)
    import matplotlib.pyplot as plt

    plotted = [row for row in rows if isinstance(row.get("iters"), int) and "latest capture" not in row["variant"]]
    plotted = sorted(plotted, key=lambda row: (row["iters"], row["variant"]))
    if not plotted:
        return

    fig, ax1 = plt.subplots(figsize=(8.8, 4.8), dpi=180)
    variants = [row["variant"] for row in plotted]
    x = list(range(len(plotted)))
    psnr = [row["PSNR"] for row in plotted]
    ssim = [row["SSIM"] for row in plotted]
    lpips = [row["LPIPS"] for row in plotted]

    ax1.plot(x, psnr, marker="o", linewidth=2.0, color="#2563eb", label="PSNR")
    ax1.set_ylabel("PSNR", color="#1d4ed8")
    ax1.tick_params(axis="y", labelcolor="#1d4ed8")
    ax1.grid(axis="y", color="#d4d4d8", linewidth=0.7, alpha=0.65)
    ax1.set_xticks(x)
    ax1.set_xticklabels(variants, rotation=25, ha="right", fontsize=8)

    ax2 = ax1.twinx()
    ax2.plot(x, ssim, marker="s", linewidth=1.7, color="#16a34a", label="SSIM")
    ax2.plot(x, lpips, marker="^", linewidth=1.7, color="#dc2626", label="LPIPS")
    ax2.set_ylabel("SSIM / LPIPS")
    ax2.set_ylim(0.0, 1.0)

    for idx, row in enumerate(plotted):
        if row["paper_use"] == "representative":
            ax1.scatter([idx], [row["PSNR"]], s=110, facecolors="none", edgecolors="#111827", linewidths=1.8)
            ax1.annotate("representative", (idx, row["PSNR"]), xytext=(6, 8), textcoords="offset points", fontsize=8)
        elif "degraded" in row["paper_use"]:
            ax1.annotate("not promoted", (idx, row["PSNR"]), xytext=(6, -16), textcoords="offset points", fontsize=8)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="lower left", fontsize=8)
    fig.tight_layout()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PNG)
    plt.close(fig)


def main() -> None:
    rows = read_rows()
    write_csv(rows)
    write_md(rows)
    write_tex(rows)
    write_png(rows)
    print(
        json.dumps(
            {
                "rows": len(rows),
                "csv": str(OUT_CSV.relative_to(ROOT)),
                "markdown": str(OUT_MD.relative_to(ROOT)),
                "png": str(OUT_PNG.relative_to(ROOT)),
                "tex": str(OUT_TEX.relative_to(ROOT)),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
