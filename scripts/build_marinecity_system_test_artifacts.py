"""Build paper-facing MarineCity multi-UAV system test artifacts.

This script does not create or modify Isaac/Cesium stages. It only reads
already captured real-Cesium MarineCity RGB/depth images, detector EvidenceTokens,
and reasoner smoke outputs, then builds compact result panels and tables.
"""

from __future__ import annotations

import csv
import json
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "outputs/reports/live/marinecity_system_test_10plus"
PAPER_TABLE_DIR = REPO_ROOT / "paper/tables"
TOKEN_RESULTS_CSV = "system_test_token_results.csv"
TOKEN_CONTACT_SHEET = "contact_sheet_token_tests.png"
REASONER_ANSWERS_MD = "reasoner_answers_token_tests.md"


@dataclass(frozen=True)
class Scenario:
    key: str
    label: str
    focus: str
    capture_root: Path
    evidence_dir: Path
    reasoning_dir: Path


SCENARIOS = [
    Scenario(
        key="s0",
        label="S0 locked MarineCity ROI",
        focus="baseline multi-UAV evidence confirmation",
        capture_root=Path("/home/oem/UAV/uav_marinecity/outputs/isaac_exports/uavmarine_s0_viewer160_session_recapture"),
        evidence_dir=REPO_ROOT / "outputs/evidence/uavmarine_s0_viewer160_session_recapture_detector_smoke_conf001",
        reasoning_dir=REPO_ROOT / "outputs/reasoning/uavmarine_s0_viewer160_session_recapture_from_detector_conf001_rule_based",
    ),
    Scenario(
        key="s1",
        label="S1 adjacent/overlapping objects",
        focus="small-object overlap and re-observation decision",
        capture_root=Path("/home/oem/UAV/uav_marinecity/outputs/isaac_exports/uavmarine_s1_viewer160_session_recapture"),
        evidence_dir=REPO_ROOT / "outputs/evidence/uavmarine_s1_viewer160_session_recapture_detector_smoke_conf001",
        reasoning_dir=REPO_ROOT / "outputs/reasoning/uavmarine_s1_viewer160_session_recapture_from_detector_conf001_rule_based",
    ),
    Scenario(
        key="s2",
        label="S2 coastline multi-view ambiguity",
        focus="coastline/reflection ambiguity and missing-view handling",
        capture_root=Path("/home/oem/UAV/uav_marinecity/outputs/isaac_exports/uavmarine_s2_viewer160_session_recapture"),
        evidence_dir=REPO_ROOT / "outputs/evidence/uavmarine_s2_viewer160_session_recapture_detector_smoke_conf001",
        reasoning_dir=REPO_ROOT / "outputs/reasoning/uavmarine_s2_viewer160_session_recapture_from_detector_conf001_rule_based",
    ),
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = ["DejaVuSans-Bold.ttf", "DejaVuSans.ttf"] if bold else ["DejaVuSans.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


FONT_H1 = font(34, bold=True)
FONT_H2 = font(24, bold=True)
FONT_BODY = font(20)
FONT_SMALL = font(16)
FONT_MONO = font(16)


def display_provider(provider: Any) -> str:
    value = str(provider or "unknown")
    if value.endswith("_symbolic_aerograph"):
        return "rule_based_aerograph"
    return value


def fit_image(path: Path, size: tuple[int, int]) -> Image.Image:
    if not path.exists():
        image = Image.new("RGB", size, "#f8fafc")
        draw = ImageDraw.Draw(image)
        draw.rectangle([0, 0, size[0] - 1, size[1] - 1], outline="#cbd5e1", width=2)
        draw.text((20, size[1] // 2 - 10), f"missing: {path.name}", fill="#b91c1c", font=FONT_SMALL)
        return image
    image = Image.open(path).convert("RGB")
    image.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "#ffffff")
    x = (size[0] - image.width) // 2
    y = (size[1] - image.height) // 2
    canvas.paste(image, (x, y))
    return canvas


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    width: int,
    line_height: int,
    fill: str = "#0f172a",
    font_obj: ImageFont.ImageFont = FONT_BODY,
) -> int:
    x, y = xy
    lines: list[str] = []
    for para in text.splitlines():
        if not para.strip():
            lines.append("")
            continue
        lines.extend(textwrap.wrap(para, width=width))
    for line in lines:
        draw.text((x, y), line, fill=fill, font=font_obj)
        y += line_height
    return y


def text_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str, body: str, accent: str) -> None:
    draw.rounded_rectangle(box, radius=10, fill="#ffffff", outline=accent, width=3)
    x0, y0, x1, _ = box
    draw.rectangle([x0, y0, x1, y0 + 46], fill=accent)
    draw.text((x0 + 18, y0 + 9), title, fill="white", font=FONT_H2)
    draw_wrapped(draw, body, (x0 + 18, y0 + 64), 52, 28, font_obj=FONT_BODY)


def find_token(tokens: list[dict[str, Any]], image_id: str, bbox: list[float]) -> dict[str, Any] | None:
    candidates = [row for row in tokens if row.get("image_id") == image_id]
    if not candidates:
        return None

    def diff(row: dict[str, Any]) -> float:
        candidate_bbox = row.get("bbox_2d", [0, 0, 0, 0])
        return sum(abs(float(a) - float(b)) for a, b in zip(candidate_bbox, bbox))

    return min(candidates, key=diff)


def crop_path_for_token(evidence_dir: Path, token: dict[str, Any] | None) -> Path | None:
    if not token:
        return None
    token_id = str(token.get("token_id", ""))
    parts = token_id.split(":")
    if len(parts) != 3:
        return None
    image_id, batch_id, det_id = parts
    return evidence_dir / "crops" / str(token.get("uav_id", "")) / f"{image_id}_{batch_id}_{det_id}.jpg"


def first_view_image_path(scenario: Scenario, image_id: str) -> Path:
    return scenario.capture_root / "real_cesium_capture" / f"{image_id}.png"


def preview_path(scenario: Scenario, image_id: str) -> Path:
    return scenario.evidence_dir / "previews" / f"{image_id}_pred.png"


def response_for_object(rows: list[dict[str, Any]], object_id: str) -> dict[str, Any]:
    for row in rows:
        if row.get("object_id") == object_id:
            return row
    return {}


def scenario_rows(scenario: Scenario) -> dict[str, Any]:
    return {
        "capture": read_json(scenario.capture_root / "real_cesium_capture_summary.json"),
        "capture_plan": read_json(scenario.capture_root / "capture_plan.json"),
        "detector": read_json(scenario.evidence_dir / "detector_smoke_summary.json"),
        "tokens": read_jsonl(scenario.evidence_dir / "evidence_tokens.jsonl"),
        "reasoner": read_json(scenario.reasoning_dir / "summary.json"),
        "hypotheses": read_json(scenario.reasoning_dir / "hypotheses.json"),
        "llm": read_json(scenario.reasoning_dir / "llm_responses.json"),
        "decisions": read_json(scenario.reasoning_dir / "final_decisions.json"),
    }


def build_token_panel(
    test_id: int,
    scenario: Scenario,
    hypothesis: dict[str, Any],
    llm: dict[str, Any],
    decision: dict[str, Any],
    token: dict[str, Any] | None,
    out_path: Path,
) -> dict[str, Any]:
    view = (hypothesis.get("views") or [{}])[0]
    image_id = str(view.get("image_id", "unknown"))
    uav_id = str(view.get("uav_id", token.get("uav_id") if token else "unknown"))
    input_path = first_view_image_path(scenario, image_id)
    pred_path = preview_path(scenario, image_id)
    crop_path = crop_path_for_token(scenario.evidence_dir, token)

    canvas = Image.new("RGB", (2200, 1280), "#f8fafc")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, 2200, 94], fill="#0f172a")
    draw.text((36, 24), f"MarineCity System Test {test_id:02d}: {scenario.label}", fill="white", font=FONT_H1)
    draw.text((36, 64), f"{scenario.focus} | UAV={uav_id} | image={image_id}", fill="#cbd5e1", font=FONT_SMALL)

    input_img = fit_image(input_path, (650, 366))
    pred_img = fit_image(pred_path, (650, 366))
    crop_img = fit_image(crop_path, (360, 360)) if crop_path else fit_image(Path("__missing_crop__"), (360, 360))
    canvas.paste(input_img, (40, 140))
    canvas.paste(pred_img, (760, 140))
    canvas.paste(crop_img, (1480, 140))
    draw.text((40, 112), "Input UAV camera view", fill="#1e3a8a", font=FONT_H2)
    draw.text((760, 112), "P2P4-SelfAttnFR detector preview", fill="#1e3a8a", font=FONT_H2)
    draw.text((1480, 112), "Detected crop", fill="#1e3a8a", font=FONT_H2)

    posterior = hypothesis.get("class_posterior", {})
    top_class = max(posterior, key=posterior.get) if posterior else "unknown"
    det_conf = float(token.get("confidence", hypothesis.get("confidence", 0.0))) if token else float(hypothesis.get("confidence", 0.0))
    det_unc = float(token.get("uncertainty", 0.0)) if token else 0.0
    bbox = token.get("bbox_2d", view.get("bbox_2d", [])) if token else view.get("bbox_2d", [])
    bbox_text = ", ".join(f"{float(v):.1f}" for v in bbox[:4]) if bbox else "n/a"
    llm_class = llm.get("predicted_class", "unknown")
    llm_conf = float(llm.get("confidence", 0.0) or 0.0)
    action = llm.get("recommended_action", decision.get("recommended_action", "n/a"))
    reobserve = bool(decision.get("should_reobserve", False))
    reasons = llm.get("reasons") or decision.get("reason_tags") or []

    det_body = (
        f"Detector class: {top_class}\n"
        f"Detector confidence: {det_conf:.3f}\n"
        f"Uncertainty: {det_unc:.3f}\n"
        f"2D bbox [x,y,w,h]: {bbox_text}\n"
        f"UAV camera pose: {token.get('uav_pose', []) if token else 'n/a'}"
    )
    text_card(draw, (40, 560, 700, 900), "2D EvidenceToken", det_body, "#2563eb")

    graph_body = (
        f"3D hypothesis id: {hypothesis.get('object_id', 'unknown')}\n"
        f"View count: {hypothesis.get('view_count', 0)}\n"
        f"Geometry residual: {float(hypothesis.get('geometry_residual', 0.0)):.3f}\n"
        f"Ambiguity score: {float(hypothesis.get('ambiguity_score', 0.0)):.3f}\n"
        "3D output type: evidence-graph smoke, not final NeRF/3DGS generation"
    )
    text_card(draw, (760, 560, 1420, 900), "3D Evidence Package", graph_body, "#7c3aed")

    provider = display_provider(llm.get("provider", "unknown"))
    answer_body = (
        f"Reasoner provider: {provider}\n"
        f"Predicted class: {llm_class}\n"
        f"Reasoner confidence: {llm_conf:.3f}\n"
        f"Action: {action}\n"
        f"Re-observe: {str(reobserve)}\n"
        f"Reasons: {', '.join(str(r) for r in reasons[:5])}"
    )
    text_card(draw, (1480, 560, 2140, 900), "Reasoner Answer", answer_body, "#16a34a" if not reobserve else "#f97316")

    note = (
        "Use this panel as a system smoke-test artifact. For final paper results, replace the rule-based "
        "verifier with the selected LLM/VLM provider and improve object placement/scale where small objects are weak."
    )
    draw_wrapped(draw, note, (40, 960), 150, 28, fill="#334155", font_obj=FONT_BODY)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)

    return {
        "test_id": f"T{test_id:02d}",
        "scenario": scenario.key,
        "scenario_label": scenario.label,
        "uav_id": uav_id,
        "image_id": image_id,
        "object_id": hypothesis.get("object_id", ""),
        "detector_class": top_class,
        "detector_confidence": f"{det_conf:.4f}",
        "detector_uncertainty": f"{det_unc:.4f}",
        "ambiguity_score": f"{float(hypothesis.get('ambiguity_score', 0.0)):.4f}",
        "geometry_residual": f"{float(hypothesis.get('geometry_residual', 0.0)):.4f}",
        "reasoner_provider": provider,
        "reasoner_class": llm_class,
        "reasoner_confidence": f"{llm_conf:.4f}",
        "recommended_action": action,
        "should_reobserve": str(reobserve),
        "input_image": str(input_path),
        "detector_preview": str(pred_path),
        "panel": str(out_path),
    }


def build_scenario_panel(scenario: Scenario, rows: dict[str, Any], out_path: Path) -> None:
    canvas = Image.new("RGB", (2200, 1450), "#f8fafc")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, 2200, 96], fill="#111827")
    draw.text((36, 20), scenario.label, fill="white", font=FONT_H1)
    draw.text((36, 64), scenario.focus, fill="#d1d5db", font=FONT_SMALL)

    frames = rows["capture"].get("frames", [])
    x_positions = [40, 760, 1480]
    for idx, frame in enumerate(frames[:3]):
        image_id = Path(frame["rgb_path"]).stem
        uav_id = frame.get("uav_id", f"uav_{idx+1:02d}")
        input_path = first_view_image_path(scenario, image_id)
        pred_path = preview_path(scenario, image_id)
        canvas.paste(fit_image(input_path, (650, 366)), (x_positions[idx], 150))
        canvas.paste(fit_image(pred_path, (650, 366)), (x_positions[idx], 570))
        draw.text((x_positions[idx], 116), f"{uav_id} input", fill="#1e3a8a", font=FONT_H2)
        draw.text((x_positions[idx], 536), f"{uav_id} detector", fill="#1e3a8a", font=FONT_H2)

    det = rows["detector"]
    rea = rows["reasoner"]
    decisions = rows["decisions"]
    finalized = sum(1 for d in decisions if not d.get("should_reobserve", False))
    reobserve = sum(1 for d in decisions if d.get("should_reobserve", False))
    class_counts = ", ".join(f"{k}={v}" for k, v in det.get("tokens_by_class", {}).items()) or "none"
    provider = display_provider(rea.get("provider", "unknown"))
    summary = (
        f"Detector tokens: {det.get('token_count', 0)} | classes: {class_counts}\n"
        f"3D hypotheses: {rea.get('hypothesis_count', 0)} | reasoner calls: {rea.get('llm_call_count', 0)} | provider: {provider}\n"
        f"Finalized objects: {finalized} | targeted re-observation: {reobserve}\n"
        "Current status: real-Cesium multi-UAV smoke test complete; final visual-quality and external LLM validation remain."
    )
    text_card(draw, (40, 1010, 2140, 1370), "Scenario-Level System Result", summary, "#0f766e")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def build_contact_sheet(panel_paths: list[Path], out_path: Path, title: str) -> None:
    thumb_w, thumb_h = 520, 300
    cols = 3
    rows = (len(panel_paths) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * thumb_w + 80, rows * thumb_h + 150), "#f8fafc")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, canvas.width, 90], fill="#0f172a")
    draw.text((36, 24), title, fill="white", font=FONT_H1)
    for idx, path in enumerate(panel_paths):
        image = fit_image(path, (thumb_w - 30, thumb_h - 55))
        x = 40 + (idx % cols) * thumb_w
        y = 120 + (idx // cols) * thumb_h
        draw.rounded_rectangle([x, y, x + thumb_w - 20, y + thumb_h - 30], radius=8, fill="#ffffff", outline="#cbd5e1", width=2)
        canvas.paste(image, (x + 15, y + 15))
        draw.text((x + 15, y + thumb_h - 42), path.stem, fill="#334155", font=FONT_SMALL)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def write_tables(test_rows: list[dict[str, str]], scenario_table: list[dict[str, str]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PAPER_TABLE_DIR.mkdir(parents=True, exist_ok=True)
    test_csv = OUT_DIR / TOKEN_RESULTS_CSV
    with test_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(test_rows[0].keys()))
        writer.writeheader()
        writer.writerows(test_rows)

    scenario_csv = OUT_DIR / "paper_system_scenario_table.csv"
    with scenario_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(scenario_table[0].keys()))
        writer.writeheader()
        writer.writerows(scenario_table)

    def latex_escape(value: str) -> str:
        return (
            str(value)
            .replace("\\", r"\textbackslash{}")
            .replace("&", r"\&")
            .replace("%", r"\%")
            .replace("$", r"\$")
            .replace("#", r"\#")
            .replace("_", r"\_")
            .replace("{", r"\{")
            .replace("}", r"\}")
        )

    tex_lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{MarineCity multi-UAV system smoke-test results. The current reasoner provider is a deterministic rule-based AeroGraph verifier for pipeline validation; external LLM/VLM validation is reported separately in the supplementary validation record.}",
        r"\label{tab:marinecity_system_smoke}",
        r"\resizebox{\linewidth}{!}{%",
        r"\begin{tabular}{lrrrrl}",
        r"\toprule",
        r"Scenario & UAV views & Evidence tokens & 3D hypotheses & Re-observe & Detected classes \\",
        r"\midrule",
    ]
    for row in scenario_table:
        tex_lines.append(
            f"{latex_escape(row['scenario'])} & {row['uav_views']} & {row['evidence_tokens']} & "
            f"{row['hypotheses']} & {row['reobserve']} & {latex_escape(row['detected_classes'])} \\\\"
        )
    tex_lines.extend([r"\bottomrule", r"\end{tabular}%", r"}", r"\end{table}", ""])
    scenario_tex = OUT_DIR / "paper_system_scenario_table.tex"
    scenario_tex.write_text("\n".join(tex_lines), encoding="utf-8")

    (PAPER_TABLE_DIR / "marinecity_system_token_results.csv").write_bytes(test_csv.read_bytes())
    (PAPER_TABLE_DIR / "marinecity_system_scenario_table.csv").write_bytes(scenario_csv.read_bytes())
    (PAPER_TABLE_DIR / "marinecity_system_scenario_table.tex").write_bytes(scenario_tex.read_bytes())


def write_reasoner_markdown(test_rows: list[dict[str, str]], scenario_table: list[dict[str, str]]) -> None:
    lines = [
        "# MarineCity System Test Results",
        "",
        "This artifact summarizes the real-Cesium MarineCity multi-UAV smoke test.",
        "The detector is the proposed P2P4-SelfAttnFR checkpoint. The current reasoner provider is a deterministic rule-based AeroGraph verifier, so these are pipeline-validation answers rather than final LLM/VLM claims.",
        "",
        "## Scenario Summary",
        "",
        "| Scenario | UAV views | Evidence tokens | 3D hypotheses | Re-observe | Classes | Provider |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for row in scenario_table:
        lines.append(
            f"| {row['scenario']} | {row['uav_views']} | {row['evidence_tokens']} | {row['hypotheses']} | "
            f"{row['reobserve']} | {row['detected_classes']} | {row['provider']} |"
        )
    lines.extend(["", "## Token-Level Reasoner Answers", ""])
    for row in test_rows:
        lines.extend(
            [
                f"### {row['test_id']} - {row['scenario_label']} - {row['uav_id']}",
                "",
                f"- Input image: `{row['input_image']}`",
                f"- Detector preview: `{row['detector_preview']}`",
                f"- Result panel: `{row['panel']}`",
                f"- Detector: `{row['detector_class']}` conf={row['detector_confidence']} uncertainty={row['detector_uncertainty']}",
                f"- 3D evidence: ambiguity={row['ambiguity_score']} geometry_residual={row['geometry_residual']}",
                f"- Reasoner answer: `{row['reasoner_class']}` conf={row['reasoner_confidence']} action=`{row['recommended_action']}` reobserve={row['should_reobserve']}",
                "",
            ]
        )
    (OUT_DIR / REASONER_ANSWERS_MD).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    token_rows: list[dict[str, str]] = []
    scenario_table: list[dict[str, str]] = []
    token_panels: list[Path] = []
    scenario_panels: list[Path] = []
    test_id = 1

    for scenario in SCENARIOS:
        rows = scenario_rows(scenario)
        scenario_panel = OUT_DIR / f"{scenario.key}_scenario_panel.png"
        build_scenario_panel(scenario, rows, scenario_panel)
        scenario_panels.append(scenario_panel)

        det = rows["detector"]
        rea = rows["reasoner"]
        detected_classes = ", ".join(f"{k}={v}" for k, v in det.get("tokens_by_class", {}).items()) or "none"
        scenario_table.append(
            {
                "scenario": scenario.label,
                "uav_views": str(len(rows["capture"].get("frames", []))),
                "evidence_tokens": str(det.get("token_count", 0)),
                "hypotheses": str(rea.get("hypothesis_count", 0)),
                "reasoner_calls": str(rea.get("llm_call_count", 0)),
                "reobserve": str(rea.get("reobserve_count", 0)),
                "detected_classes": detected_classes,
                "provider": display_provider(rea.get("provider", "")),
                "capture_root": str(scenario.capture_root),
                "evidence_dir": str(scenario.evidence_dir),
                "reasoning_dir": str(scenario.reasoning_dir),
            }
        )

        llm_by_id = {row.get("object_id"): row for row in rows["llm"]}
        decision_by_id = {row.get("object_id"): row for row in rows["decisions"]}
        for hypothesis in rows["hypotheses"]:
            view = (hypothesis.get("views") or [{}])[0]
            token = find_token(rows["tokens"], str(view.get("image_id", "")), view.get("bbox_2d", []))
            object_id = str(hypothesis.get("object_id", ""))
            panel_path = OUT_DIR / "token_panels" / f"test_{test_id:02d}_{scenario.key}_{object_id}.png"
            token_rows.append(
                build_token_panel(
                    test_id=test_id,
                    scenario=scenario,
                    hypothesis=hypothesis,
                    llm=llm_by_id.get(object_id, {}),
                    decision=decision_by_id.get(object_id, {}),
                    token=token,
                    out_path=panel_path,
                )
            )
            token_panels.append(panel_path)
            test_id += 1

    write_tables(token_rows, scenario_table)
    write_reasoner_markdown(token_rows, scenario_table)
    build_contact_sheet(token_panels, OUT_DIR / TOKEN_CONTACT_SHEET, f"MarineCity {len(token_panels)} Token-Level System Tests")
    build_contact_sheet(scenario_panels, OUT_DIR / "contact_sheet_3_scenarios.png", "MarineCity 3 Scenario-Level System Tests")

    manifest = {
        "status": "marinecity_system_test_artifacts_complete",
        "output_dir": str(OUT_DIR),
        "scenario_count": len(SCENARIOS),
        "token_level_test_count": len(token_rows),
        "scenario_panels": [str(p) for p in scenario_panels],
        "token_panels": [str(p) for p in token_panels],
        "contact_sheet_token_tests": str(OUT_DIR / TOKEN_CONTACT_SHEET),
        "contact_sheet_3_scenarios": str(OUT_DIR / "contact_sheet_3_scenarios.png"),
        "system_test_results_csv": str(OUT_DIR / TOKEN_RESULTS_CSV),
        "paper_system_scenario_table_csv": str(OUT_DIR / "paper_system_scenario_table.csv"),
        "paper_system_scenario_table_tex": str(OUT_DIR / "paper_system_scenario_table.tex"),
        "reasoner_answers_md": str(OUT_DIR / REASONER_ANSWERS_MD),
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
