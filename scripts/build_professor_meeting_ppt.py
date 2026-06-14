#!/usr/bin/env python3
"""Build a professor meeting status deck from current detector reports.

The deck is intentionally concise: it gives a meeting-ready status snapshot,
then points to the live figures/tables that already exist in outputs/reports.
It uses Pandoc instead of python-pptx so it can run in the current environment.
"""

from __future__ import annotations

import csv
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "outputs" / "reports" / "live"
OUT_MD = LIVE / "professor_meeting_status_20260615.md"
OUT_PPTX = LIVE / "professor_meeting_status_20260615.pptx"
SYSTEM_FIG = LIVE / "prof_meeting_fig01_proposed_system_overview.png"
THREE_D_REASONER_FIG = LIVE / "prof_meeting_fig03_3d_reasoner_flow.png"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def fnum(value: str | float | None, digits: int = 4) -> str:
    if value in (None, ""):
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "-"


def pct(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"


def find_method(rows: list[dict[str, str]], method: str) -> dict[str, str]:
    for row in rows:
        if row.get("method") == method:
            return row
    raise KeyError(method)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def multiline_center(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    fill: str,
    fnt: ImageFont.ImageFont,
    spacing: int = 6,
) -> None:
    x, y = xy
    lines = text.split("\n")
    heights = []
    widths = []
    for line in lines:
        box = draw.textbbox((0, 0), line, font=fnt)
        widths.append(box[2] - box[0])
        heights.append(box[3] - box[1])
    total_h = sum(heights) + spacing * (len(lines) - 1)
    cy = y - total_h // 2
    for line, w, h in zip(lines, widths, heights):
        draw.text((x - w // 2, cy), line, font=fnt, fill=fill)
        cy += h + spacing


def box(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    title: str,
    body: str,
    fill: str,
    outline: str,
) -> None:
    draw.rounded_rectangle(xy, radius=28, fill=fill, outline=outline, width=4)
    x1, y1, x2, y2 = xy
    draw.text((x1 + 28, y1 + 24), title, font=font(34, bold=True), fill="#111827")
    multiline_center(
        draw,
        ((x1 + x2) // 2, (y1 + y2) // 2 + 26),
        body,
        "#374151",
        font(26),
    )


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str = "#374151") -> None:
    draw.line([start, end], fill=color, width=8)
    ex, ey = end
    sx, sy = start
    dx = 1 if ex >= sx else -1
    points = [(ex, ey), (ex - 28 * dx, ey - 18), (ex - 28 * dx, ey + 18)]
    draw.polygon(points, fill=color)


def draw_system_overview(path: Path) -> None:
    img = Image.new("RGB", (2400, 1350), "#F8FAFC")
    draw = ImageDraw.Draw(img)
    draw.text((80, 70), "Proposed Multi-Drone Small Object Understanding System", font=font(54, True), fill="#0F172A")
    draw.text(
        (84, 142),
        "Working architecture for ACCV: 2D detector + 3D benchmark generation + reasoner decision layer",
        font=font(28),
        fill="#475569",
    )

    boxes = [
        ((90, 300, 450, 560), "Multi-Drone Inputs", "UAV frames\nMarine-city scenes\nSmall / dense objects", "#E0F2FE", "#0284C7"),
        ((570, 300, 930, 560), "2D Proposed Detector", "P2/P4 heads\nSelfAttnFR refinement\nSmall-object localization", "#DCFCE7", "#16A34A"),
        ((1050, 300, 1410, 560), "3D Generation", "Reconstruction\nIsaac simulation\nViewpoint expansion", "#FEF3C7", "#D97706"),
        ((1530, 300, 1890, 560), "Restored Benchmark", "Image restoration\nSynthetic-real pairing\nHard-case mining", "#FCE7F3", "#DB2777"),
        ((2010, 300, 2370, 560), "Reasoner LLM", "Evidence fusion\nRe-observation policy\nFinal decision", "#EDE9FE", "#7C3AED"),
    ]
    for args in boxes:
        box(draw, *args)
    for s, e in [((450, 430), (570, 430)), ((930, 430), (1050, 430)), ((1410, 430), (1530, 430)), ((1890, 430), (2010, 430))]:
        arrow(draw, s, e)

    lower_boxes = [
        ((330, 760, 870, 1040), "Contribution 1", "Proposed YOLO-based detector\nfor UAV small-object detection\nwith 3-seed evidence", "#FFFFFF", "#94A3B8"),
        ((930, 760, 1470, 1040), "Contribution 2", "3D marine-city benchmark\nfrom reconstruction + simulation\nwith restoration modules", "#FFFFFF", "#94A3B8"),
        ((1530, 760, 2070, 1040), "Contribution 3", "Reasoner model for final decision,\nexplainable evidence selection,\nand re-observation planning", "#FFFFFF", "#94A3B8"),
    ]
    for args in lower_boxes:
        box(draw, *args)
    draw.text((90, 1190), "Current status: Contribution 1 is near paper-table readiness; Contributions 2-3 start after 2D queue stabilizes.", font=font(30, True), fill="#111827")
    draw.text((90, 1242), "Main paper should show the complete system; supplementary should carry full ablations, heatmaps, extra qualitative results, and implementation details.", font=font(26), fill="#475569")
    img.save(path)


def draw_3d_reasoner_flow(path: Path) -> None:
    img = Image.new("RGB", (2400, 1350), "#FBFBF8")
    draw = ImageDraw.Draw(img)
    draw.text((80, 70), "Planned 3D Benchmark + Reasoner Experiment Flow", font=font(54, True), fill="#111827")
    draw.text((84, 142), "This part starts after the 2D detector queue is stable; the detector becomes the perception front-end.", font=font(28), fill="#4B5563")

    boxes = [
        ((110, 300, 570, 560), "3D Scene Source", "Marine-city map\nMulti-view UAV paths\nWeather / altitude factors", "#E0F2FE", "#0369A1"),
        ((710, 300, 1170, 560), "Data Generation", "Isaac capture\n3D reconstruction\nSynthetic viewpoints", "#FEF3C7", "#B45309"),
        ((1310, 300, 1770, 560), "Restoration Module", "Degradation model\nImage restoration\nDomain bridge", "#FCE7F3", "#BE185D"),
        ((1910, 300, 2370, 560), "Detector + Reasoner", "2D detector evidence\nLLM/SAGE reasoner\nFinal action", "#EDE9FE", "#6D28D9"),
    ]
    for args in boxes:
        box(draw, *args)
    for s, e in [((570, 430), (710, 430)), ((1170, 430), (1310, 430)), ((1770, 430), (1910, 430))]:
        arrow(draw, s, e)

    table_x, table_y = 160, 720
    draw.rounded_rectangle((table_x, table_y, 2240, 1125), radius=24, fill="#FFFFFF", outline="#CBD5E1", width=3)
    draw.text((table_x + 40, table_y + 30), "Evaluation outputs to prepare", font=font(36, True), fill="#111827")
    rows = [
        ("3D benchmark", "coverage, weather/altitude splits, object density, failure cases"),
        ("Restoration", "before/after quality, detection gain, hard-case visualization"),
        ("Reasoner", "decision accuracy, evidence trace, re-observation benefit"),
        ("System-level", "detector-only vs detector+3D vs detector+3D+reasoner"),
    ]
    y = table_y + 110
    for name, desc in rows:
        draw.text((table_x + 55, y), name, font=font(28, True), fill="#0F172A")
        draw.text((table_x + 390, y), desc, font=font(28), fill="#475569")
        y += 68

    draw.text((160, 1215), "Decision needed: whether to use closed/open LLMs only, or add a local SAGE-style reasoner for the final decision module.", font=font(30, True), fill="#111827")
    img.save(path)


def ensure_method_figures() -> None:
    draw_system_overview(SYSTEM_FIG)
    draw_3d_reasoner_flow(THREE_D_REASONER_FIG)


def main() -> None:
    ensure_method_figures()
    table_rows = read_rows(ROOT / "outputs" / "reports" / "final_detector_table_preview.csv")
    pvalue_rows = read_rows(ROOT / "outputs" / "experiments" / "final_detector_pvalues.csv")

    ours = find_method(table_rows, "Ours: P2P4-SelfAttnFR")
    yolo11l = find_method(table_rows, "YOLOv11l")

    ap_delta = float(ours["AP"]) - float(yolo11l["AP"])
    ap50_delta = float(ours["AP50"]) - float(yolo11l["AP50"])
    f1_delta = float(ours["F1"]) - float(yolo11l["F1"])
    param_reduction = 1.0 - float(ours["params_m"]) / float(yolo11l["params_m"])
    gflops_delta = float(ours["gflops"]) / float(yolo11l["gflops"]) - 1.0

    pvalues = {row["metric"]: row for row in pvalue_rows}
    ap_p = pvalues.get("AP", {}).get("paired_t_pvalue", "-")
    ap50_p = pvalues.get("AP50", {}).get("paired_t_pvalue", "-")

    now = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M KST")

    main_rows = [r for r in table_rows if r.get("section") == "main_1280_completed_3seed"]
    top5 = main_rows[:5]
    top5_lines = "\n".join(
        f"- {r['rank']}. {r['method']}: AP {fnum(r['AP'])}, AP50 {fnum(r['AP50'])}, "
        f"F1 {fnum(r['F1'])}, Params {float(r['params_m']):.2f}M"
        for r in top5
    )

    md = f"""% ACCV 2026 Meeting Status
% Jong-Chan Park
% {now}

# Goal of This Meeting

- Report current 2D detector status and strongest evidence so far.
- Decide whether `P2P4-SelfAttnFR` can be treated as the working proposed detector.
- Align remaining comparison, ablation, 3D reconstruction/simulation, and LLM reasoner experiments.
- Confirm what should go into the main paper vs. supplementary material.

# Current One-Line Status

- 2D detector search: strong trade-off candidate found and 3-seed confirmation completed.
- Working proposed detector: `Ours: P2P4-SelfAttnFR`.
- Current main-table rank: #1 among completed 1280-resolution, 3-seed detector results.
- Active queue: YOLO-family comparison reinforcement is still running.
- Important caveat: strict internal AP target is not fully cleared yet, so ablation and related-work comparison still matter.

# Proposed System Overview

![](outputs/reports/live/prof_meeting_fig01_proposed_system_overview.png){{width=12.3in}}

# Proposed Detector / Model Figure

![](paper/figures/fig02_detector_module.png){{width=12.1in}}

- Current working detector: `P2P4-SelfAttnFR`.
- Figure should remain editable later because final module naming may change after ablation.
- For the paper, this figure should highlight only our added parts, not redraw every YOLO block in unnecessary detail.

# Proposed 2D Detector Result

| Method | Protocol | AP | AP50 | F1 | Params | GFLOPs |
|---|---|---:|---:|---:|---:|---:|
| Ours: P2P4-SelfAttnFR | VisDrone val, 1280, 3-seed | {fnum(ours['AP'])} | {fnum(ours['AP50'])} | {fnum(ours['F1'])} | {float(ours['params_m']):.2f}M | {float(ours['gflops']):.1f} |
| YOLOv11l | VisDrone val, 1280, 3-seed | {fnum(yolo11l['AP'])} | {fnum(yolo11l['AP50'])} | {fnum(yolo11l['F1'])} | {float(yolo11l['params_m']):.2f}M | {float(yolo11l['gflops']):.1f} |

- Delta vs YOLOv11l: AP +{ap_delta:.4f}, AP50 +{ap50_delta:.4f}, F1 +{f1_delta:.4f}.
- Params are reduced by {pct(param_reduction)}.
- GFLOPs are increased by {pct(gflops_delta)} because high-resolution P2/P4 paths are computationally heavier.
- Paired t-test: AP p={fnum(ap_p)}, AP50 p={fnum(ap50_p)}.

# Final Detector Table Preview

![](outputs/reports/live/paper_fig01_main_detector_table.png){{width=12.4in}}

# Top Completed Main-Protocol Ranking

{top5_lines}

- All rows above are 1280-resolution, 3-seed protocol.
- Related-work 640-eval snapshots are intentionally separated until 1280/3-seed consistency is finished.
- This keeps the main claim clean for reviewers.

# AP / AP50 Comparison

![](outputs/reports/live/paper_fig04_ap_ap50_bar_chart.png){{width=12.0in}}

# Accuracy vs Model Size Trade-Off

![](outputs/reports/live/paper_fig05_ap_params_scatter.png){{width=11.4in}}

# Trade-Off Interpretation

- Main strength: Ours slightly improves AP/AP50 while using fewer parameters than YOLOv11l.
- Main risk: the absolute AP margin is modest, so we need strong ablation and related-work coverage.
- Complexity story should be honest: params decrease, but GFLOPs increase due to small-object high-resolution heads.
- Best paper framing: small-object-oriented detector with better accuracy/parameter trade-off, not simply a faster detector.

# Current Active Runs

- `yolo12s-s42`: epoch 59/100, best AP 0.3353, AP50 0.5421, F1 0.5775, params 9.26M.
- `yolo12s-s123`: epoch 17/100, best AP 0.3023, AP50 0.4959, F1 0.5358, params 9.26M.
- These are comparison reinforcement runs, not proposed-detector search.
- Live dashboard is updated at `outputs/reports/live/training_dashboard.png`.

# Experiment Readiness Overview

![](outputs/reports/live/paper_fig07_experiment_status_overview.png){{width=12.0in}}

# Proposed 3D / Reasoner Figure

![](outputs/reports/live/prof_meeting_fig03_3d_reasoner_flow.png){{width=12.3in}}

# Remaining 2D Experiments

- Complete remaining YOLO-family n/s/m/l comparison coverage.
- Expand related-work comparisons: prioritize models with usable GitHub code or easy adapters.
- Re-evaluate CSFPR-RTDETR and LEAF-YOLO under 1280-consistent protocol where feasible.
- Build final ablation: P2/P4 only, SelfAttnFR only, combined model, NMS/post-process variants.
- Produce heatmaps/Grad-CAM and per-category performance for supplementary material.

# Main Paper vs Supplementary Split

- Main paper: system motivation, proposed detector, 3D benchmark pipeline, LLM reasoner, key 2D/3D/system results.
- Main detector table: only consistent 1280/3-seed results.
- Supplementary: full YOLO family scale table, related-work protocol details, extra ablation, heatmaps, hyperparameters, failure cases.
- Keep main paper self-contained; supplementary supports rather than replaces core claims.

# Next Milestones

- By Wednesday: freeze current 2D detector table draft and paper experiment section skeleton.
- Next Tuesday/Wednesday: start NVIDIA Isaac / marine-city map / 3D benchmark construction.
- After 3D data path is stable: run restoration and reasoner LLM experiments.
- Before July 5 main submission: finalize main tables, core figures, and method wording.
- Before July 8 supplementary: add detailed ablations, qualitative analysis, implementation details, and extra videos/code if available.

# Decisions Needed from Professor

- Is `P2P4-SelfAttnFR` acceptable as the working proposed detector name/structure?
- Which related-work models are mandatory for comparison?
- Should we prioritize AP margin improvement or model complexity reduction for the final detector?
- Confirm main-paper page allocation for 2D detector vs 3D benchmark vs LLM reasoner.
"""

    OUT_MD.write_text(md, encoding="utf-8")

    subprocess.run(
        [
            "pandoc",
            str(OUT_MD.relative_to(ROOT)),
            "-o",
            str(OUT_PPTX.relative_to(ROOT)),
            "--slide-level=1",
        ],
        cwd=ROOT,
        check=True,
    )

    print(OUT_MD)
    print(OUT_PPTX)


if __name__ == "__main__":
    main()
