"""Build MarineCity qualitative figure selection notes and LaTeX slots."""

from __future__ import annotations

import csv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MARINE_DIR = REPO_ROOT / "paper/figures/results/marinecity_system"
CAPTURE_QA = MARINE_DIR / "marinecity_capture_quality_rank.csv"
CROP_QA = MARINE_DIR / "marinecity_real_capture_crop_candidates.csv"
OUT_MD = MARINE_DIR / "marinecity_qualitative_selection_manifest.md"
OUT_TEX = REPO_ROOT / "paper/sections/07_marinecity_qualitative_figure_slots.tex"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k): str(v) for k, v in row.items()} for row in csv.DictReader(handle)]


def fmt_float(value: str, digits: int = 4) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "-"


def build_markdown(captures: list[dict[str, str]], crops: list[dict[str, str]]) -> str:
    best_capture = captures[0] if captures else {}
    best_crop = crops[0] if crops else {}
    lines = [
        "# MarineCity Qualitative Figure Selection",
        "",
        "Updated: `2026-06-25 KST`",
        "",
        "This manifest selects current MarineCity qualitative assets for the main paper and supplementary material.",
        "All listed images are generated from real-Cesium MarineCity captures or detector-token smoke outputs; no fake/proxy city visual should be used for paper evidence.",
        "",
        "## Recommendation",
        "",
        "- Main paper: use `contact_sheet_3_scenarios.png` only as a clearly labeled real-Cesium system smoke/protocol figure if page budget allows.",
        "- Supplementary: use `contact_sheet_token_tests.png`, `marinecity_capture_quality_top8.png`, and `marinecity_real_capture_crop_top12.png`.",
        "- Final main qualitative figure is still pending a cleaner recapture/selection with low void ratio and visible object/UAV evidence.",
        "",
        "## Current Best Full-Capture Candidate",
        "",
    ]
    if best_capture:
        lines.extend(
            [
                f"- Capture: `{best_capture.get('capture_name', '-')}`",
                f"- Best image: `{best_capture.get('best_image', '-')}`",
                f"- Mean top-3 black/void ratio: `{fmt_float(best_capture.get('mean_top3_black_ratio', ''))}`",
                f"- Best image black/void ratio: `{fmt_float(best_capture.get('best_black_ratio', ''))}`",
                f"- Camera profile: `{best_capture.get('camera_profile', '-')}`",
                "",
            ]
        )
    else:
        lines.append("- No capture QA rows found.\n")

    lines.extend(["## Current Best Crop Candidate", ""])
    if best_crop:
        lines.extend(
            [
                f"- Capture: `{best_crop.get('capture_name', '-')}`",
                f"- Source: `{best_crop.get('source', '-')}`",
                f"- Crop path: `{best_crop.get('crop_path', '-')}`",
                f"- Crop box: `{best_crop.get('crop_box', '-')}`",
                f"- Black/void ratio: `{fmt_float(best_crop.get('black_ratio', ''))}`",
                f"- Area ratio: `{fmt_float(best_crop.get('area_ratio', ''))}`",
                f"- Score: `{fmt_float(best_crop.get('score', ''))}`",
                "",
            ]
        )
    else:
        lines.append("- No crop QA rows found.\n")

    lines.extend(
        [
            "## Paper-Facing Assets",
            "",
            "| Asset | Path | Placement | Status |",
            "|---|---|---|---|",
            "| 3-scenario smoke contact sheet | `paper/figures/results/marinecity_system/contact_sheet_3_scenarios.png` | Main optional / supplementary | Smoke-test ready; not final benchmark |",
            "| Token-level system contact sheet | `paper/figures/results/marinecity_system/contact_sheet_token_tests.png` | Supplementary | Smoke-test ready |",
            "| Visual QA top-8 sheet | `paper/figures/results/marinecity_system/marinecity_capture_quality_top8.png` | Supplementary / internal review | Shows full-capture void ratio issue |",
            "| Crop top-12 sheet | `paper/figures/results/marinecity_system/marinecity_real_capture_crop_top12.png` | Supplementary / final recapture guide | Crop-only; not a replacement for a final full-scene figure |",
            "| S0 scenario panel | `paper/figures/results/marinecity_system/s0_scenario_panel.png` | Supplementary | Scenario detail |",
            "| S1 scenario panel | `paper/figures/results/marinecity_system/s1_scenario_panel.png` | Supplementary | Scenario detail |",
            "| S2 scenario panel | `paper/figures/results/marinecity_system/s2_scenario_panel.png` | Supplementary | Scenario detail |",
            "",
            "## Caption Constraints",
            "",
            "- Say `real-Cesium MarineCity system smoke test`, not final benchmark result.",
            "- Say `deterministic rule-based AeroGraph verifier` when using current reasoner outputs.",
            "- Do not claim NeRF/3DGS/3D completion performance from these figures.",
            "- For main paper, avoid crop-only figures unless captioned as visual framing evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def build_tex(best_capture: dict[str, str], best_crop: dict[str, str]) -> str:
    best_capture_note = (
        f"Current best full-capture candidate: {best_capture.get('capture_name', 'n/a')}, "
        f"mean top-3 void ratio {fmt_float(best_capture.get('mean_top3_black_ratio', ''))}."
        if best_capture
        else "No capture QA candidate found."
    )
    best_crop_note = (
        f"Current best crop candidate: {best_crop.get('capture_name', 'n/a')}, "
        f"void ratio {fmt_float(best_crop.get('black_ratio', ''))}, crop-only area ratio {fmt_float(best_crop.get('area_ratio', ''))}."
        if best_crop
        else "No crop QA candidate found."
    )
    return "\n".join(
        [
            "% Auto-generated by scripts/build_marinecity_qualitative_selection.py.",
            "% These figure slots are safe wording templates; final placement depends on page budget.",
            "",
            "\\begin{figure*}[t]",
            "\\centering",
            "\\includegraphics[width=0.98\\textwidth]{figures/results/marinecity_system/contact_sheet_3_scenarios.png}",
            "\\caption{Real-Cesium MarineCity multi-UAV system smoke-test examples. The panels show three scenario-level detector-to-evidence-token outputs with the current deterministic rule-based AeroGraph verifier. This figure validates the capture and evidence pipeline; final external-provider reasoning and 3D completion results are reported separately when available.}",
            "\\label{fig:marinecity_system_smoke_examples}",
            "\\end{figure*}",
            "",
            "\\begin{figure*}[t]",
            "\\centering",
            "\\includegraphics[width=0.98\\textwidth]{figures/results/marinecity_system/marinecity_real_capture_crop_top12.png}",
            "\\caption{Real-Cesium MarineCity crop candidates used for final qualitative recapture framing. The crops are not synthetic replacements for the full scene. "
            + best_crop_note
            + "}",
            "\\label{fig:supp_marinecity_crop_candidates}",
            "\\end{figure*}",
            "",
            "\\begin{figure*}[t]",
            "\\centering",
            "\\includegraphics[width=0.98\\textwidth]{figures/results/marinecity_system/marinecity_capture_quality_top8.png}",
            "\\caption{Visual quality audit for full real-Cesium MarineCity captures. The sheet is used to select or recapture final qualitative figures by measuring black/void tile regions and brightness. "
            + best_capture_note
            + "}",
            "\\label{fig:supp_marinecity_capture_quality}",
            "\\end{figure*}",
            "",
        ]
    )


def main() -> None:
    captures = read_csv(CAPTURE_QA)
    crops = read_csv(CROP_QA)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_TEX.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(build_markdown(captures, crops), encoding="utf-8")
    OUT_TEX.write_text(build_tex(captures[0] if captures else {}, crops[0] if crops else {}), encoding="utf-8")
    print(str(OUT_MD))
    print(str(OUT_TEX))


if __name__ == "__main__":
    main()
