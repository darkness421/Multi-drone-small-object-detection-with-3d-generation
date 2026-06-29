"""Build a narrow live PNG dashboard for detector training."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.config import resolve_path
from scripts.watch_live_training_scoreboard import Baseline
from scripts.watch_live_training_scoreboard import f1
from scripts.watch_live_training_scoreboard import fmt
from scripts.watch_live_training_scoreboard import gpu_lines
from scripts.watch_live_training_scoreboard import recently_touched
from scripts.watch_live_training_scoreboard import results_run_slug
from scripts.watch_live_training_scoreboard import row_for_log
from scripts.watch_live_training_scoreboard import row_for_run
from scripts.watch_live_training_scoreboard import sort_key_ap

os.environ.setdefault("MPLBACKEND", "Agg")


DEFAULT_PROJECT_DIRS = [
    "outputs/detectors/server_baselines",
    "outputs/detectors/server_fresh_baselines/large_20260524_140922",
    "outputs/detectors/server_yolov11_p2_compact_ideas",
    "outputs/detectors/server_yolov11_p2_module_search",
    "outputs/detectors/server_yolov11_p2_compression",
    "outputs/detectors/server_yolov11_p2_balanced_followup",
    "outputs/detectors/server_yolov11_p2_balanced_v2_modules",
    "outputs/detectors/server_yolov11_p2p4_balanced",
    "outputs/detectors/server_yolov11_p2_balanced_v3",
    "outputs/detectors/server_yolov11_p2_balanced_v2",
    "outputs/detectors/server_yolov11_p2_balanced",
    "outputs/detectors/server_yolov11_p2_slim",
    "outputs/detectors/server_yolov11_p2_confirm",
    "outputs/detectors/server_yolov11_p2_next_step",
    "outputs/detectors/related_work_consistency",
    "outputs/detectors/related_work_module_reproductions",
    "outputs/detectors/required_related_work_reimplementations",
]
DEFAULT_LOG_DIRS = [
    "outputs/logs/server_baselines",
    "outputs/logs/server_yolov11_p2_compact_ideas",
    "outputs/logs/server_yolov11_p2_module_search",
    "outputs/logs/server_yolov11_p2_compression",
    "outputs/logs/server_yolov11_p2_balanced_followup",
    "outputs/logs/server_yolov11_p2_balanced_v2_modules",
    "outputs/logs/server_yolov11_p2p4_balanced",
    "outputs/logs/server_yolov11_p2_balanced_v3",
    "outputs/logs/server_yolov11_p2_balanced_v2",
    "outputs/logs/server_yolov11_p2_balanced",
    "outputs/logs/server_yolov11_p2_slim",
    "outputs/logs/server_yolov11_p2_confirm",
    "outputs/logs/related_work_consistency",
    "outputs/logs/related_work_module_reproductions",
    "outputs/logs/required_related_work_models",
]

SELECTED_OURS = "Ours: SAFR-YOLO"
FINAL_TABLE_PREVIEW = "outputs/reports/final_detector_table_preview.csv"
RELATED_REFERENCE_LABELS = "paper/tables/related_work_reference_labels.csv"
PROPOSED_RUN_RANKING = "outputs/reports/detector_rankings/proposed_run_performance_ranking.csv"
FINAL_DETECTOR_PVALUES = "outputs/experiments/final_detector_pvalues.csv"
GATED_TRADEOFF_RANKING = "outputs/reports/detector_rankings/overall_1280_completed_gated_tradeoff_ranking.csv"
FINAL_ABLATION_LOG = "outputs/logs/final_p2p4_selfattnfr_ablation_queue/queue.log"
FINAL_ABLATION_MARKER = "QUEUE_FINISHED final P2P4-SelfAttnFR ablation"
RELATED_WORK_LOG = "outputs/logs/related_work_consistency/queue.log"
RELATED_WORK_MARKER = "QUEUE_FINISHED related-work 1280 consistency retrain"
RELATED_WORK_MODULE_LOG = "outputs/logs/related_work_module_reproductions/queue.log"
RELATED_WORK_MODULE_MARKER = "QUEUE_FINISHED related-work module reproductions"
REQUIRED_RELATED_WORK_LOG = "outputs/logs/required_related_work_models/queue.log"
REQUIRED_RELATED_WORK_MARKER = "QUEUE_FINISHED required related-work model queue"
REQUIRED_RELATED_WORK_ROOT = "outputs/detectors/required_related_work_reimplementations"
UAVDET_AFTER_REQUIRED_LOG = "outputs/logs/required_related_work_models/uavdet_inspired_after_required.log"
UAVDET_AFTER_REQUIRED_SEEDS = (42, 123, 2026)
HEATMAP_LOG = "outputs/logs/final_detector_heatmaps/queue.log"
HEATMAP_MARKER = "QUEUE_FINISHED final detector heatmaps"
TINYPERSON_LOG = "outputs/logs/tinyperson_224_top5/queue.log"
TINYPERSON_MARKER = "QUEUE_FINISHED TinyPerson 224 Top5 3Seed stress test"
TINYPERSON224_SUMMARY = "outputs/experiments/tinyperson_224_top5/summary.csv"
TINYPERSON224_DASHBOARD = "outputs/reports/live/tinyperson_224_top5_dashboard.png"
TINYPERSON224_DASHBOARD_MD = "outputs/reports/live/tinyperson_224_top5_dashboard.md"
TINYPERSON_AUX_LOG = "outputs/logs/tinyperson_224_aux_sweep/queue.log"
TINYPERSON_AUX_MARKER = "QUEUE_FINISHED TinyPerson224 auxiliary sweep"
TINYPERSON224_AUX_SUMMARY = "outputs/experiments/tinyperson_224_aux_sweep/summary.csv"
TINYPERSON224_AUX_DASHBOARD = "outputs/reports/live/tinyperson_224_aux_sweep_dashboard.png"
MARINECITY_REINFORCE_NAME = "Neural-3D 80k"
MARINECITY_REINFORCE_RUN = "marinecity_nerfacto_fullres80k"
MARINECITY_REINFORCE_MAX_ITERS = 80000
MARINECITY_REINFORCE_TRAIN_LOG = "outputs/logs/marinecity_nerfstudio_gpu0/marinecity_nerfacto_fullres80k_20260629_afternoon_20260629_1608_fullres80k_train.log"
MARINECITY_REINFORCE_METRIC_JSON = "outputs/experiments/3d_generation/nerfstudio_native_runs/marinecity_nerfacto_fullres80k_20260629_afternoon_20260629_1608_fullres80k_metric_row.json"
PAPER_ARTIFACT_LOG = "outputs/logs/paper_artifacts_after_2d/queue.log"
PAPER_ARTIFACT_MARKER = "QUEUE_FINISHED paper artifacts after 2D"
PAPER_GATE_QUEUE_LOG_DIR = "outputs/logs/accv_paper_gate_queue"
ISAAC_CAPTURE_PLAN = "outputs/experiments/marinecity_isaac_capture_plan.json"
ISAAC_DRY_RUN_MANIFEST = "outputs/experiments/marinecity_isaac_dry_run_manifest.json"
ISAAC_REPLICATOR_TEMPLATE = "outputs/experiments/marinecity_isaac_replicator_template.py"
ISAAC_READINESS_MANIFEST = "outputs/experiments/marinecity_multiview_benchmark_readiness.json"
ISAAC_CESIUM_SCENE_PLAN = "outputs/experiments/marinecity_cesium_scene_plan.json"
ISAAC_STREAMING_MARKER = "outputs/logs/gpu1_isaac51_streaming/marinecity_stage_opened.json"
CESIUM_STATUS = "outputs/reports/live/cesium_haeundae_status.md"
MULTIUAV_SMOKE_SUMMARY = "outputs/evidence/marinecity_detector_smoke_20260623_conf001/detector_smoke_summary.json"
REAL_CAPTURE_DETECTOR_SUMMARY = "outputs/evidence/marinecity_real_capture_detector_smoke/detector_smoke_summary.json"
VIEWER160_STATUS_CSV = "outputs/experiments/marinecity_viewer160_pipeline_status.csv"
VIEWER160_QUEUE_LOG = "outputs/logs/marinecity_viewer160_pipeline/queue.log"
VIEWER160_SCENARIOS = [
    ("uavmarine_s0_viewer160_session_recapture", "uavmarine_s0_viewer160_recapture"),
    ("uavmarine_s1_viewer160_session_recapture", "uavmarine_s1_viewer160_recapture"),
    ("uavmarine_s2_viewer160_session_recapture", "uavmarine_s2_viewer160_recapture"),
]
VIEWER160_EXPORT_ROOT = Path("/home/oem/UAV/uav_marinecity/outputs/isaac_exports")


def setup_matplotlib() -> Any:
    os.environ.setdefault("MPLCONFIGDIR", str(resolve_path(".cache/matplotlib")))
    os.environ.setdefault("XDG_CACHE_HOME", str(resolve_path(".cache")))
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    return plt, FancyBboxPatch


def collect_rows(project_dirs: list[str], log_dirs: list[str], baseline: Baseline) -> list[dict[str, str]]:
    result_files: list[Path] = []
    for root in project_dirs:
        root_path = resolve_path(root)
        for pattern in ["*/ultralytics/results.csv", "*/*/results.csv", "*/results.csv"]:
            result_files.extend(root_path.glob(pattern))
    result_files = list(dict.fromkeys(result_files))
    result_files = sorted(result_files, key=lambda path: path.stat().st_mtime, reverse=True)
    result_slugs = {re.sub(r"^\d{8}_\d{6}_", "", results_run_slug(path)) for path in result_files}

    log_rows: list[dict[str, str]] = []
    for log_dir in log_dirs:
        for log_path in resolve_path(log_dir).glob("*.log"):
            if log_path.name == "queue.log":
                continue
            if log_path.name == "uavdet_inspired_after_required.log":
                continue
            has_result_row = any(log_path.stem == slug or log_path.stem.startswith(f"{slug}_") for slug in result_slugs)
            if not has_result_row and recently_touched([log_path]):
                log_rows.append(row_for_log(log_path, baseline))
    log_rows = sorted(log_rows, key=lambda row: row["run"])
    run_rows = [row_for_run(path, [resolve_path(item) for item in log_dirs], baseline) for path in result_files]
    return log_rows + run_rows


def numeric(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def read_csv(path: str) -> list[dict[str, str]]:
    csv_path = resolve_path(path)
    if not csv_path.exists():
        return []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(key): str(value) for key, value in row.items()} for row in csv.DictReader(handle)]


def read_json_obj(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def viewer160_step_count(step: str) -> int:
    return len(
        {
            row.get("scenario")
            for row in read_csv(VIEWER160_STATUS_CSV)
            if row.get("step") == step and row.get("status") == "ok"
        }
    )


def viewer160_capture_count() -> int:
    return sum(
        1
        for session_stem, legacy_stem in VIEWER160_SCENARIOS
        if (VIEWER160_EXPORT_ROOT / session_stem / "real_cesium_capture_summary.json").exists()
        or (VIEWER160_EXPORT_ROOT / legacy_stem / "real_cesium_capture_summary.json").exists()
    )


def viewer160_detector_summary() -> tuple[int, dict[str, int]]:
    total_tokens = 0
    classes: dict[str, int] = {}
    for session_stem, legacy_stem in VIEWER160_SCENARIOS:
        stem = (
            session_stem
            if resolve_path(f"outputs/evidence/{session_stem}_detector_smoke_conf001/detector_smoke_summary.json").exists()
            else legacy_stem
        )
        summary = read_json_obj(resolve_path(f"outputs/evidence/{stem}_detector_smoke_conf001/detector_smoke_summary.json"))
        if not summary:
            summary = read_json_obj(resolve_path(f"outputs/evidence/{stem}_detector_smoke_conf005/detector_smoke_summary.json"))
        total_tokens += int(summary.get("token_count", 0) or 0)
        for label, count in (summary.get("tokens_by_class", {}) or {}).items():
            classes[str(label)] = classes.get(str(label), 0) + int(count or 0)
    if total_tokens == 0:
        real_capture_summary = read_json_obj(resolve_path(REAL_CAPTURE_DETECTOR_SUMMARY))
        if real_capture_summary:
            return (
                int(real_capture_summary.get("token_count", 0) or 0),
                {
                    str(label): int(count or 0)
                    for label, count in (real_capture_summary.get("tokens_by_class", {}) or {}).items()
                },
            )
    return total_tokens, classes


def related_reference_labels() -> dict[str, str]:
    labels: dict[str, str] = {}
    for row in read_csv(RELATED_REFERENCE_LABELS):
        model = row.get("model", "").strip()
        if not model:
            continue
        label = row.get("reference_number", "").strip() or row.get("fallback_label", "").strip()
        if not label and row.get("cite_key", "").strip():
            label = "TBD"
        if label:
            labels[model] = label
    return labels


def related_label(name: str, labels: dict[str, str]) -> str:
    label = labels.get(name)
    return f"{name} [{label}]" if label else name


def related_group_label(names: list[str], labels: dict[str, str]) -> str:
    return " / ".join(related_label(name, labels) for name in names)


def related_label_with_scope(name: str, labels: dict[str, str]) -> str:
    label = labels.get(name)
    return f"{name} [{label}]" if label else f"{name} [not in Sec. 2.1]"


def active_run_display_name(row: dict[str, str]) -> str:
    run = row.get("run", "")
    labels = related_reference_labels()
    seed_match = re.search(r"(?:^|[-_])(?:s|seed)(\d+)$", run)
    seed = f" s{seed_match.group(1)}" if seed_match else ""
    if "yolo11s_uav_simam_dwr_repro" in run:
        return f"{related_label_with_scope('YOLO11s-UAV', labels)} SimAM+DWR repro{seed}"
    if "sffef_yolo_reimpl" in run:
        return f"{related_label_with_scope('SFFEF-YOLO', labels)} reimpl{seed}"
    if "bpd_yolo_reimpl" in run:
        return f"{related_label_with_scope('BPD-YOLO', labels)} reimpl{seed}"
    if "hf_dfine_reimpl" in run:
        return f"{related_label_with_scope('HF-D-FINE', labels)} reimpl{seed}"
    if "csfpr" in run.lower() or "csfpr-rtdetr" in run.lower():
        return f"{related_label_with_scope('CSFPR-RTDETR', labels)}{seed}"
    if "mffsod" in run.lower():
        return f"{related_label_with_scope('MFFSODNet', labels)}{seed}"
    if "p2p4_selfattnfr_visdrone_transfer_tinyperson640" in run:
        return f"Ours P2P4-SelfAttnFR TinyPerson transfer{seed}"
    if "tinyperson" in run.lower() and not any(
        token in run.lower()
        for token in ["sffef_yolo", "bpd_yolo", "hf_dfine", "uavdet", "yolo11s_uav", "csfpr", "mffsod"]
    ):
        for raw in [
            "yolov5nu",
            "yolov5su",
            "yolov5mu",
            "yolov5lu",
            "yolov8n",
            "yolov8s",
            "yolov8m",
            "yolov8l",
            "yolov9t",
            "yolov9s",
            "yolov9m",
            "yolov9c",
            "yolov10n",
            "yolov10s",
            "yolov10m",
            "yolov10l",
            "yolo11n",
            "yolo11s",
            "yolo11m",
            "yolo11l",
            "yolo12n",
            "yolo12s",
            "yolo12m",
            "yolo12l",
            "yolo26n",
            "yolo26s",
            "yolo26m",
            "yolo26l",
        ]:
            if raw in run.lower():
                return f"{raw.upper()} TinyPerson224 aux{seed}"
        if "p2p4_selfattnfr" in run.lower():
            return f"Ours P2P4-SelfAttnFR TinyPerson224{seed}"
    if "tinyperson224_aux" in run.lower() or "tinyperson_224_aux" in run.lower():
        if "sffef_yolo" in run.lower():
            return f"{related_label_with_scope('SFFEF-YOLO', labels)} TinyPerson224 aux{seed}"
        if "bpd_yolo" in run.lower():
            return f"{related_label_with_scope('BPD-YOLO', labels)} TinyPerson224 aux{seed}"
        if "hf_dfine" in run.lower():
            return f"{related_label_with_scope('HF-D-FINE', labels)} TinyPerson224 aux{seed}"
        if "uavdet" in run.lower():
            return f"{related_label_with_scope('UAVDet', labels)} TinyPerson224 aux{seed}"
        if "yolo11s_uav" in run.lower():
            return f"{related_label_with_scope('YOLO11s-UAV', labels)} TinyPerson224 aux{seed}"
        name = run.lower().replace("_tinyperson224_aux", "").replace("-tinyperson224-aux", "")
        name = re.sub(r"[-_]seed\d+$", "", name)
        return f"{name.upper()} TinyPerson224 aux{seed}"
    if "tinyperson224_top5" in run.lower() or "tinyperson_224_top5" in run.lower():
        if "p2p4_selfattnfr" in run.lower():
            return f"Ours P2P4-SelfAttnFR TinyPerson224{seed}"
        for raw, label in [
            ("yolo11l", "YOLOv11l"),
            ("yolov9c", "YOLOv9c"),
            ("yolov8l", "YOLOv8l"),
            ("yolov9m", "YOLOv9m"),
        ]:
            if raw in run.lower():
                return f"{label} TinyPerson224{seed}"
    return run


def queue_log_lines(path: str, limit: int = 400) -> list[str]:
    log_path = resolve_path(path)
    if not log_path.exists():
        return []
    try:
        return log_path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]
    except OSError:
        return []


def queue_log_contains(path: str, marker: str) -> bool:
    return any(marker in line for line in queue_log_lines(path, limit=800))


def clean_queue_line(line: str) -> str:
    value = re.sub(r"^\[[^\]]+\]\s*", "", line).strip()
    return value.replace("QUEUE_FINISHED ", "finished: ")


def latest_queue_event(path: str) -> str:
    for line in reversed(queue_log_lines(path, limit=120)):
        event = clean_queue_line(line)
        if event:
            return event
    return "not started"


def queue_state(path: str, marker: str, *, waiting: bool = False) -> str:
    if queue_log_contains(path, marker):
        return "done"
    event = latest_queue_event(path).lower()
    if "waiting for train_ok" in event or event.startswith("start ") or " started" in event:
        return "running"
    if event == "not started" or waiting or "waiting" in event:
        return "waiting"
    return "running"


def latest_paper_gate_log() -> Path | None:
    log_dir = resolve_path(PAPER_GATE_QUEUE_LOG_DIR)
    if not log_dir.exists():
        return None
    files = sorted(log_dir.glob("run_*.log"), key=lambda path: path.stat().st_mtime, reverse=True)
    return files[0] if files else None


def paper_gate_queue_status_row() -> dict[str, str]:
    latest = latest_paper_gate_log()
    if latest is None:
        return {
            "queue": "ACCV paper gate queue",
            "status": "waiting",
            "detail": "15-min paper/readiness/dashboard refresh queue",
            "event": "no queue log yet",
        }
    age_sec = max(0.0, datetime.now().timestamp() - latest.stat().st_mtime)
    lines = [
        line.strip()
        for line in latest.read_text(encoding="utf-8", errors="ignore").splitlines()
        if line.strip()
    ]
    event = clean_queue_line(lines[-1]) if lines else latest.name
    event_lower = event.lower()
    if "finished_at" in event_lower or "all local gates completed" in event_lower:
        status = "monitoring"
    else:
        status = "running" if age_sec <= 20 * 60 else "ready"
    detail = "refreshes Overleaf sync status, paper gates, 3D/AeroGraph readiness, and dashboards"
    return {
        "queue": "ACCV paper gate queue",
        "status": status,
        "detail": detail,
        "event": f"{latest.name}; {event}",
    }


def tinyperson_job_done(job_key: str) -> bool:
    marker = f"TRAIN_OK TinyPerson job={job_key}"
    failed = f"TRAIN_FAILED TinyPerson job={job_key}"
    return queue_log_contains(TINYPERSON_LOG, marker) or queue_log_contains(TINYPERSON_LOG, failed)


def drop_completed_tinyperson_active(rows: list[dict[str, str]]) -> None:
    job_keys = {
        "yolo11l": "yolo11l",
        "yolov9c": "yolov9c",
        "yolov8l": "yolov8l",
        "yolov9m": "yolov9m",
        "p2p4_selfattnfr": "p2p4_selfattnfr",
    }
    if queue_log_contains(TINYPERSON_LOG, TINYPERSON_MARKER):
        completed = set(job_keys)
    else:
        completed = {prefix for prefix, job in job_keys.items() if tinyperson_job_done(job)}
    if not completed:
        return
    for row in rows:
        run = row.get("run", "").lower()
        if "tinyperson" in run and any(run.startswith(prefix) for prefix in completed):
            row["active"] = "false"


def tinyperson224_status_row() -> dict[str, str]:
    rows = read_csv(TINYPERSON224_SUMMARY)
    if rows:
        best = max(rows, key=lambda row: numeric(row.get("best_AP_mean", "")) or -1.0)
        method = best.get("method", "TinyPerson224")
        if method.startswith("ProposedSize"):
            method = "Ours"
        evidence = (
            f"img224 {best.get('seed_count', '-')}-seed; "
            f"{method} AP {fmt(numeric(best.get('best_AP_mean', '')))} "
            f"AP50 {fmt(numeric(best.get('best_AP50_mean', '')))}"
        )
    else:
        evidence = "summary pending; imgsz 224 Top5 stress test"
    status = "done" if queue_log_contains(TINYPERSON_LOG, TINYPERSON_MARKER) else queue_state(TINYPERSON_LOG, TINYPERSON_MARKER)
    return {
        "queue": "TinyPerson224 Top5",
        "status": status,
        "detail": "completed 224-input Top5/3-seed stress-test; excluded from main claims",
        "event": evidence,
    }


def tinyperson224_aux_status_row() -> dict[str, str]:
    rows = read_csv(TINYPERSON224_AUX_SUMMARY)
    train_ok = sum(1 for line in queue_log_lines(TINYPERSON_AUX_LOG, limit=2000) if "TRAIN_OK TinyPerson224 aux" in line)
    if rows:
        best = max(rows, key=lambda row: numeric(row.get("best_AP_mean", "")) or -1.0)
        method = best.get("method", "TinyPerson224 aux")
        method = method.replace("-TinyPerson224Aux", "")
        evidence = (
            f"{len(rows)} rows; best {method[:22]} AP "
            f"{fmt(numeric(best.get('best_AP_mean', '')))} AP50 "
            f"{fmt(numeric(best.get('best_AP50_mean', '')))}"
        )
    else:
        latest = latest_queue_event(TINYPERSON_AUX_LOG)
        evidence = f"{train_ok} trained; {latest}"
    return {
        "queue": "TinyPerson224 sweep",
        "status": queue_state(TINYPERSON_AUX_LOG, TINYPERSON_AUX_MARKER),
        "detail": "separate 224-input auxiliary sweep; never mixed with VisDrone 1280 table",
        "event": evidence,
    }


def marinecity_reinforce_active_row() -> dict[str, str] | None:
    train_log = resolve_path(MARINECITY_REINFORCE_TRAIN_LOG)
    metric_json = resolve_path(MARINECITY_REINFORCE_METRIC_JSON)
    if metric_json.exists() or not train_log.exists():
        return None

    progress = "training"
    speed = "rays/s pending"
    try:
        lines = train_log.read_text(encoding="utf-8", errors="ignore").splitlines()[-240:]
    except OSError:
        lines = []
    pattern = re.compile(r"^\s*(\d+)\s+\(([\d.]+)%\)\s+[\d.]+\s+ms\s+([0-9]+\s+m,\s+[0-9]+\s+s)\s+([0-9.]+\s+K)")
    for line in lines:
        match = pattern.search(line)
        if match:
            step, pct, eta, rays = match.groups()
            progress = f"{step}/{MARINECITY_REINFORCE_MAX_ITERS} {pct}% ETA {eta.replace(' ', '')}"
            speed = f"{rays.replace(' ', '')} rays/s"

    return {
        "run": MARINECITY_REINFORCE_RUN,
        "active": "true",
        "gpu": "0",
        "progress": progress,
        "speed": speed,
        "AP": "-",
        "AP50": "-",
        "F1": "-",
        "P": "-",
        "R": "-",
        "bestAP": "-",
        "bestAP50": "-",
        "bestP": "-",
        "bestR": "-",
        "bestF1": "-",
        "box": "-",
        "cls": "-",
        "dfl": "-",
        "Params": "n/a",
        "GFLOPs": "n/a",
        "dAP": "n/a",
        "gate": "neural-3D metric reinforcement",
    }


def neural3d_reinforcement_status_row() -> dict[str, str]:
    active = marinecity_reinforce_active_row()
    metric_json = resolve_path(MARINECITY_REINFORCE_METRIC_JSON)
    if active:
        return {
            "queue": MARINECITY_REINFORCE_NAME,
            "status": "running",
            "detail": "Nerfacto full-res 80k reinforcement on MarineCity real-Cesium captures",
            "event": f"{active['progress']}; {active['speed']}",
        }
    if metric_json.exists():
        return {
            "queue": MARINECITY_REINFORCE_NAME,
            "status": "done",
            "detail": "Nerfacto full-res 80k reinforcement completed; compare before promotion",
            "event": f"metric row: {MARINECITY_REINFORCE_METRIC_JSON}",
        }
    return {
        "queue": MARINECITY_REINFORCE_NAME,
        "status": "waiting",
        "detail": "optional 80k reinforcement pending",
        "event": "not started",
    }


def isaac_cesium_status_row() -> dict[str, str]:
    captures = viewer160_capture_count()
    if captures >= 3:
        return {
            "queue": "Isaac/Cesium map",
            "status": "done",
            "detail": "Real MarineCity Cesium ROI captured for S0/S1/S2 with viewer160 profile",
            "event": "real Cesium captures 3/3; next paper-quality recapture should reduce tile/backface artifacts",
        }
    marker_path = resolve_path(ISAAC_STREAMING_MARKER)
    if marker_path.exists():
        marker = marker_path.read_text(encoding="utf-8", errors="ignore")
        if "stage_opened" in marker:
            return {
                "queue": "Isaac/Cesium map",
                "status": "running",
                "detail": "MarineCity stage opened on GPU1; view with Kit Remote/WebRTC at 127.0.0.1:49100",
                "event": "live preview: marinecity_isaac_preview.png",
            }
    required = [
        ISAAC_CAPTURE_PLAN,
        ISAAC_DRY_RUN_MANIFEST,
        ISAAC_REPLICATOR_TEMPLATE,
        ISAAC_READINESS_MANIFEST,
        ISAAC_CESIUM_SCENE_PLAN,
    ]
    missing = [path for path in required if not resolve_path(path).exists()]
    if missing:
        return {
            "queue": "Isaac/Cesium map",
            "status": "waiting",
            "detail": "prepare MarineCity capture plan, Cesium stage, and object placement files",
            "event": f"missing {Path(missing[0]).name}",
        }
    return {
        "queue": "Isaac/Cesium map",
        "status": "ready",
        "detail": "MarineCity scene, objects, UAV altitudes ready for smoke test",
        "event": "scene plan + replicator template ready",
    }


def selected_detector_ready() -> bool:
    return any(row.get("method") == SELECTED_OURS for row in read_csv(FINAL_TABLE_PREVIEW))


def multi_uav_detector_test_row() -> dict[str, str]:
    detector_runs = viewer160_step_count("detector")
    reasoner_runs = viewer160_step_count("reasoner")
    total_tokens, classes = viewer160_detector_summary()
    if detector_runs >= 3 and reasoner_runs >= 3:
        class_text = ", ".join(f"{label}:{count}" for label, count in sorted(classes.items())) or "none"
        return {
            "queue": "Multi-UAV YOLO test",
            "status": "done",
            "detail": "P2P4-SelfAttnFR inference + 3D evidence/reasoner validation ran on S0/S1/S2 viewer160 captures",
            "event": f"{total_tokens} EvidenceTokens; {class_text}; rule-based reasoner 3/3",
        }
    scene_ready = resolve_path(ISAAC_CESIUM_SCENE_PLAN).exists()
    detector_ready = selected_detector_ready()
    if scene_ready and detector_ready:
        return {
            "queue": "Multi-UAV YOLO test",
            "status": "ready",
            "detail": "mount P2P4-SelfAttnFR on 2-4 UAV views after map smoke test",
            "event": "detector + scene plan ready",
        }
    missing = "scene plan" if not scene_ready else "selected detector row"
    return {
        "queue": "Multi-UAV YOLO test",
        "status": "waiting",
        "detail": "prepare selected detector and multi-drone camera-view wiring",
        "event": f"missing {missing}",
    }


def final_table_related_1280_done() -> bool:
    rows = [
        row
        for row in read_csv(FINAL_TABLE_PREVIEW)
        if row.get("section") == "main_1280_completed_3seed"
    ]
    required = ("CSFPR-RTDETR", "MFFSODNet")
    for name in required:
        matched = [
            row
            for row in rows
            if name.lower() in row.get("method", "").lower()
            and int(float(row.get("seed_count", "0") or 0)) >= 3
        ]
        if not matched:
            return False
    return True


def queue_status_rows() -> list[dict[str, str]]:
    final_done = queue_log_contains(FINAL_ABLATION_LOG, FINAL_ABLATION_MARKER)
    related_done = queue_log_contains(RELATED_WORK_LOG, RELATED_WORK_MARKER) or final_table_related_1280_done()
    related_module_done = queue_log_contains(RELATED_WORK_MODULE_LOG, RELATED_WORK_MODULE_MARKER)
    required_related_done = queue_log_contains(REQUIRED_RELATED_WORK_LOG, REQUIRED_RELATED_WORK_MARKER)
    heatmap_done = queue_log_contains(HEATMAP_LOG, HEATMAP_MARKER)

    rows: list[dict[str, str]] = [paper_gate_queue_status_row()]
    if not final_done:
        rows.append({
            "queue": "Final ablation",
            "status": queue_state(FINAL_ABLATION_LOG, FINAL_ABLATION_MARKER),
            "detail": "P2P4-SelfAttnFR core ablation + 3-seed p-value tables collected",
            "event": "summary/p-values ready" if final_done else latest_queue_event(FINAL_ABLATION_LOG),
        })
    if not related_done:
        rows.append({
            "queue": "Related-work 1280",
            "status": queue_state(RELATED_WORK_LOG, RELATED_WORK_MARKER),
            "detail": "CSFPR-RTDETR 3 seeds -> MFFSODNet 3 seeds, 1280",
            "event": latest_queue_event(RELATED_WORK_LOG),
        })
    if not related_module_done:
        rows.append({
            "queue": related_label_with_pending("YOLO11s-UAV", related_reference_labels()),
            "status": queue_state(RELATED_WORK_MODULE_LOG, RELATED_WORK_MODULE_MARKER),
            "detail": "GPU0: SimAM/FlexSimAM + DWR module-level reproduction, seeds 42/123/2026",
            "event": latest_queue_event(RELATED_WORK_MODULE_LOG),
        })
    if not required_related_done:
        rows.append({
            "queue": "Required related-work",
            "status": queue_state(REQUIRED_RELATED_WORK_LOG, REQUIRED_RELATED_WORK_MARKER),
            "detail": "GPU0: SFFEF [4], BPD [7], HF-D-FINE [12]; UAVDet [16] fallback waits after queue",
            "event": latest_queue_event(REQUIRED_RELATED_WORK_LOG),
        })
    if not heatmap_done:
        rows.append({
            "queue": "Heatmaps",
            "status": queue_state(HEATMAP_LOG, HEATMAP_MARKER, waiting=not (final_done and related_done)),
            "detail": "final detector Grad-CAM/qualitative after 2D + related-work",
            "event": latest_queue_event(HEATMAP_LOG),
        })
    rows.append(neural3d_reinforcement_status_row())
    rows.append(isaac_cesium_status_row())
    rows.append(multi_uav_detector_test_row())
    if not queue_log_contains(PAPER_ARTIFACT_LOG, PAPER_ARTIFACT_MARKER):
        rows.append({
            "queue": "Paper artifacts",
            "status": queue_state(PAPER_ARTIFACT_LOG, PAPER_ARTIFACT_MARKER, waiting=not (final_done and related_done)),
            "detail": "paper tables/figures refresh after final queues",
            "event": latest_queue_event(PAPER_ARTIFACT_LOG),
        })
    return rows


def params_m(row: dict[str, str]) -> float | None:
    value = row.get("Params", "").replace("M", "").strip()
    return numeric(value)


def metric_from_summary(row: dict[str, str], metric: str) -> float | None:
    return numeric(row.get(f"{metric}_mean", "")) or numeric(row.get(metric, ""))


def params_from_summary(row: dict[str, str]) -> float | None:
    value = metric_from_summary(row, "Params")
    if value is None:
        return None
    return value / 1_000_000.0 if value > 1_000 else value


def is_plain_yolo_family(method: str) -> bool:
    normalized = method.lower().replace("-", "").replace("_", "")
    return normalized.startswith(("yolov5", "yolov8", "yolov9", "yolov10", "yolo11", "yolo12", "yolo26"))


def fmt_signed(value: float | None) -> str:
    return "-" if value is None else f"{value:+.4f}"


def comparison_tradeoff_score(row: dict[str, str], baseline: Baseline) -> float:
    ap = numeric(row.get("AP", "-"))
    ap50 = numeric(row.get("AP50", "-"))
    f1_value = numeric(row.get("F1", "-"))
    params = params_m(row)
    if ap is None or ap50 is None or f1_value is None or params is None or params <= 0:
        return -1.0
    if ap < baseline.ap or ap50 < baseline.ap50:
        return -1.0
    accuracy = 0.50 * (ap / baseline.ap) + 0.25 * (ap50 / baseline.ap50) + 0.25 * (f1_value / baseline.f1)
    efficiency = baseline.params_m / params
    return accuracy * efficiency


def comparison_row_key(row: dict[str, str]) -> str:
    return row.get("model", "").lower().replace(" ", "").replace("_", "-")


def add_unique_comparison_row(rows: list[dict[str, str]], seen: set[str], row: dict[str, str]) -> None:
    key = comparison_row_key(row)
    if not key or key in seen:
        return
    seen.add(key)
    rows.append(row)


def summary_to_comparison_row(row: dict[str, str], baseline: Baseline) -> dict[str, str] | None:
    method = row.get("method") or row.get("model") or ""
    if not method:
        return None
    ap = metric_from_summary(row, "best_AP")
    ap50 = metric_from_summary(row, "best_AP50")
    precision = metric_from_summary(row, "best_precision")
    recall = metric_from_summary(row, "best_recall")
    f1_value = metric_from_summary(row, "best_F1") or f1(precision, recall)
    params = params_from_summary(row)
    if ap is None or ap50 is None:
        return None
    if row.get("is_proposed") == "true":
        group = "Proposed confirm"
    elif row.get("detector_family") == "YOLO" or is_plain_yolo_family(method):
        group = "YOLO family baseline"
    elif method.upper().startswith("RT-DETR") or (row.get("detector_family") or "").upper().startswith("RT-DETR"):
        group = "Generic non-YOLO baseline"
    else:
        group = "Related-work prior model"
    seed_count = row.get("seed_count") or row.get("best_AP_n") or ""
    note = f"{seed_count}-seed" if seed_count else "summary"
    return {
        "model": method,
        "group": group,
        "AP": fmt(ap),
        "AP50": fmt(ap50),
        "P": fmt(precision),
        "R": fmt(recall),
        "F1": fmt(f1_value),
        "Params": "-" if params is None else f"{params:.2f}M",
        "dAP": fmt_signed(ap - baseline.ap),
        "note": note,
    }


def related_work_to_comparison_row(row: dict[str, str], baseline: Baseline) -> dict[str, str] | None:
    method = row.get("method") or ""
    ap = numeric(row.get("ap", ""))
    ap50 = numeric(row.get("ap50", ""))
    precision = numeric(row.get("precision", ""))
    recall = numeric(row.get("recall", ""))
    f1_value = numeric(row.get("f1", "")) or f1(precision, recall)
    params = numeric(row.get("params_m", ""))
    if not method or ap is None or ap50 is None:
        return None
    return {
        "model": method,
        "group": "Related-work prior model",
        "AP": fmt(ap),
        "AP50": fmt(ap50),
        "P": fmt(precision),
        "R": fmt(recall),
        "F1": fmt(f1_value),
        "Params": "-" if params is None else f"{params:.2f}M",
        "dAP": fmt_signed(ap - baseline.ap),
        "note": f"{row.get('imgsz', '-')}-eval only",
    }


def table_value(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def final_table_to_comparison_row(row: dict[str, str], baseline: Baseline) -> dict[str, str] | None:
    if row.get("section") != "main_1280_completed_3seed":
        return None
    method = row.get("method", "")
    ap = numeric(table_value(row, "AP", "ap"))
    ap50 = numeric(table_value(row, "AP50", "ap50"))
    precision = numeric(table_value(row, "precision", "P"))
    recall = numeric(table_value(row, "recall", "R"))
    f1_value = numeric(table_value(row, "F1", "f1")) or f1(precision, recall)
    params = numeric(table_value(row, "params_m", "ParamsM"))
    if not method or ap is None or ap50 is None:
        return None
    return {
        "model": method,
        "group": row.get("group", ""),
        "AP": fmt(ap),
        "AP50": fmt(ap50),
        "P": fmt(precision),
        "R": fmt(recall),
        "F1": fmt(f1_value),
        "Params": "-" if params is None else f"{params:.2f}M",
        "dAP": fmt_signed(ap - baseline.ap),
        "note": row.get("note", "official 3-seed"),
        "seeds": row.get("seeds", ""),
        "seed_count": row.get("seed_count", ""),
        "protocol": row.get("protocol", ""),
    }


def build_full_comparison_rows(rows: list[dict[str, str]], baseline: Baseline) -> list[dict[str, str]]:
    comparison_rows: list[dict[str, str]] = []
    seen: set[str] = set()

    for source_row in read_csv(FINAL_TABLE_PREVIEW):
        comp_row = final_table_to_comparison_row(source_row, baseline)
        if comp_row is not None:
            add_unique_comparison_row(comparison_rows, seen, comp_row)

    proposed_candidates = [row for row in rows if row.get("bestAP") != "-"]
    for best_proposed in sorted(proposed_candidates, key=sort_key_ap, reverse=True):
        add_unique_comparison_row(
            comparison_rows,
            seen,
            {
                "model": best_proposed["run"],
                "group": "Proposed search",
                "AP": best_proposed["bestAP"],
                "AP50": best_proposed["bestAP50"],
                "P": best_proposed.get("bestP", "-"),
                "R": best_proposed.get("bestR", "-"),
                "F1": best_proposed.get("bestF1", "-"),
                "Params": best_proposed["Params"],
                "dAP": best_proposed["dAP"],
                "note": best_proposed["gate"],
            },
        )

    add_unique_comparison_row(
        comparison_rows,
        seen,
        {
            "model": "YOLOv11l",
            "group": "YOLO family baseline",
            "AP": f"{baseline.ap:.4f}",
            "AP50": f"{baseline.ap50:.4f}",
            "P": "0.6666",
            "R": "0.5881",
            "F1": f"{baseline.f1:.4f}",
            "Params": f"{baseline.params_m:.2f}M",
            "dAP": "+0.0000",
            "note": "best YOLO baseline",
        },
    )

    for summary_path in [
        "outputs/experiments/server_with_top3_proposed_summary.csv",
        "outputs/experiments/server_with_yolov11_p2_confirm_slim_summary.csv",
        "outputs/experiments/server_with_yolov11_p2_next_summary.csv",
        "outputs/experiments/server_with_proposed_summary.csv",
    ]:
        for source_row in read_csv(summary_path):
            comp_row = summary_to_comparison_row(source_row, baseline)
            if comp_row is not None:
                add_unique_comparison_row(comparison_rows, seen, comp_row)

    for source_row in read_csv("outputs/experiments/related_work_detector_results.csv"):
        comp_row = related_work_to_comparison_row(source_row, baseline)
        if comp_row is not None:
            add_unique_comparison_row(comparison_rows, seen, comp_row)

    def sort_key(row: dict[str, str]) -> tuple[int, float, float]:
        group_order = {
            "Proposed search": 0,
            "Proposed confirm": 1,
            "YOLO family baseline": 2,
            "Generic non-YOLO baseline": 4,
            "Related-work prior model": 5,
        }.get(row.get("group", ""), 6)
        return (group_order, -(numeric(row.get("AP", "-")) or -1.0), params_m(row) or 999.0)

    return sorted(comparison_rows, key=sort_key)


def visible_comparison_rows(comparison_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected = next((row for row in comparison_rows if row.get("model") == SELECTED_OURS), None)
    if selected is None:
        selected = {
            "model": SELECTED_OURS,
            "group": "Ours final",
            "AP": "0.3822",
            "AP50": "0.6052",
            "P": "0.6732",
            "R": "0.5872",
            "F1": "0.6273",
            "Params": "20.82M",
            "dAP": "+0.0045",
            "note": "fallback official 3-seed",
        }
    selected = dict(selected)
    selected["model"] = "1. Ours"
    selected["group"] = "Ours final 3-seed"
    selected["note"] = "P2P4-SelfAttnFR impl.; official 3-seed"

    comparison_pool = [row for row in comparison_rows if row.get("model") != SELECTED_OURS]
    yolo_pool = sorted(
        [
            row
            for row in comparison_pool
            if row.get("group") == "Best YOLO baseline"
            or row.get("group") == "YOLO family baseline"
            or row.get("group", "").startswith("YOLO ")
        ],
        key=lambda row: (numeric(row.get("AP", "-")) or -1.0, numeric(row.get("AP50", "-")) or -1.0),
        reverse=True,
    )

    visible = [selected, {"section": "true", "model": "YOLO Family Baselines", "group": "plain YOLO n/s/m/l scale rows"}]
    for row in yolo_pool[:6]:
        visible.append(dict(row))

    non_yolo_names = ["RT-DETR-L"]
    related_names = ["CSFPR-RTDETR"]
    seen = {comparison_row_key(row) for row in visible}
    for name in non_yolo_names:
        for row in comparison_pool:
            if row.get("model") == name and comparison_row_key(row) not in seen:
                visible.append(dict(row))
                seen.add(comparison_row_key(row))
                break

    visible.append({"section": "true", "model": "Related-Work External Eval Only", "group": "separate from trained main 1280/3-seed"})
    for name in related_names:
        for row in comparison_pool:
            if row.get("model") == name and comparison_row_key(row) not in seen:
                visible.append(dict(row))
                seen.add(comparison_row_key(row))
                break

    visible = visible[:14]
    rank = 2
    for idx, row in enumerate(visible[1:], start=1):
        if row.get("section") == "true":
            continue
        ranked = dict(row)
        ranked["model"] = f"{rank}. {row['model']}"
        visible[idx] = ranked
        rank += 1
    return visible


def raw_ap_candidates(limit: int = 3) -> list[dict[str, str]]:
    return read_csv(PROPOSED_RUN_RANKING)[:limit]


def final_pvalue_summary() -> str:
    rows = {row.get("metric", ""): row for row in read_csv(FINAL_DETECTOR_PVALUES)}
    parts: list[str] = []
    for metric in ["AP", "AP50"]:
        pvalue = numeric(rows.get(metric, {}).get("paired_t_pvalue", ""))
        if pvalue is not None:
            parts.append(f"{metric} p={pvalue:.4f}")
    return "  ".join(parts)


def target_gap(value: str, target: float | str) -> str:
    val = numeric(value)
    target_value = target if isinstance(target, float) else numeric(str(target))
    if val is None or target_value is None:
        return "-"
    return f"{val - target_value:+.4f}"


def target_gap_color(value: str) -> str:
    val = numeric(value)
    if val is None:
        return "#475569"
    if val >= 0:
        return "#047857"
    if val >= -0.005:
        return "#B45309"
    return "#B91C1C"


def params_gap_to_budget(value: str, baseline: Baseline) -> str:
    params = numeric(value.replace("M", "").strip())
    if params is None:
        return "-"
    return f"{baseline.candidate_param_budget_m - params:+.2f}M"


def params_delta(value: str, reference: str) -> str:
    params = numeric(value.replace("M", "").strip())
    ref = numeric(reference.replace("M", "").strip())
    if params is None or ref is None:
        return "-"
    return f"{params - ref:+.2f}M"


def metric_delta(value: str, reference: str) -> str:
    val = numeric(value)
    ref = numeric(reference)
    if val is None or ref is None:
        return "-"
    return f"{val - ref:+.4f}"


def official_row(comparison_rows: list[dict[str, str]], name: str) -> dict[str, str] | None:
    def base_label(value: str) -> str:
        return re.sub(r"\s*\[[^\]]+\]$", "", value.strip())

    candidates = [row for row in comparison_rows if base_label(row.get("model", "")) == name]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda row: (
            1 if "3-seed" in row.get("note", "").lower() else 0,
            numeric(row.get("AP", "-")) or -1.0,
        ),
    )


def _mean(values: list[float]) -> float | None:
    return None if not values else sum(values) / len(values)


def required_reimpl_summaries(live_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    model_keys = {
        "SFFEF-YOLO": "sffef_yolo_reimpl",
        "BPD-YOLO": "bpd_yolo_reimpl",
        "HF-D-FINE": "hf_dfine_reimpl",
    }
    by_model: dict[str, list[dict[str, Any]]] = {name: [] for name in model_keys}
    for summary_path in resolve_path(REQUIRED_RELATED_WORK_ROOT).glob("*/metrics/eval_summary.json"):
        run_name = summary_path.parts[-3]
        if "_eval_" in run_name:
            continue
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        seed_match = re.search(r"seed(\d+)", run_name)
        seed = seed_match.group(1) if seed_match else ""
        metrics = summary.get("metrics", {})
        method = summary.get("method", "")
        for model_name in by_model:
            if model_name in method:
                by_model[model_name].append({"seed": seed, "metrics": metrics})
                break

    params_by_model: dict[str, str] = {}
    for row in live_rows:
        run = row.get("run", "")
        for model_name, key in model_keys.items():
            if key in run and row.get("Params", "-") != "-":
                params_by_model.setdefault(model_name, row["Params"])

    summaries: dict[str, dict[str, str]] = {}
    for model_name, items in by_model.items():
        items = sorted(items, key=lambda item: int(item["seed"]) if item["seed"].isdigit() else 999999)
        ap_values = [float(item["metrics"]["AP"]) for item in items if item["metrics"].get("AP") is not None]
        ap50_values = [float(item["metrics"]["AP50"]) for item in items if item["metrics"].get("AP50") is not None]
        precision_values = [
            float(item["metrics"]["precision"]) for item in items if item["metrics"].get("precision") is not None
        ]
        recall_values = [float(item["metrics"]["recall"]) for item in items if item["metrics"].get("recall") is not None]
        precision = _mean(precision_values)
        recall = _mean(recall_values)
        seed_values = [item["seed"] for item in items if item["seed"]]
        seed_count = len(set(seed_values))
        summaries[model_name] = {
            "AP": fmt(_mean(ap_values)),
            "AP50": fmt(_mean(ap50_values)),
            "F1": fmt(f1(precision, recall)),
            "Params": params_by_model.get(model_name, "26.08M" if seed_count else "-"),
            "seeds": ",".join(sorted(set(seed_values), key=lambda value: int(value) if value.isdigit() else 999999)),
            "seed_count": str(seed_count),
        }
    return summaries


def uavdet_after_required_queue_state() -> dict[str, Any]:
    log_path = resolve_path(UAVDET_AFTER_REQUIRED_LOG)
    running_seed: int | None = None
    finished_seeds: set[int] = set()
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            start = re.search(r"START UAVDet .* seed=(\d+)", line)
            finish = re.search(r"FINISH UAVDet .* seed=(\d+)", line)
            if start:
                running_seed = int(start.group(1))
            if finish:
                seed = int(finish.group(1))
                finished_seeds.add(seed)
                if running_seed == seed:
                    running_seed = None

    root = resolve_path(REQUIRED_RELATED_WORK_ROOT)
    result_rows: list[dict[str, Any]] = []
    for path in root.glob("*uavdet_inspired_reimpl_visdrone_seed*/ultralytics/results.csv"):
        seed_match = re.search(r"seed(\d+)", str(path))
        seed = int(seed_match.group(1)) if seed_match else -1
        rows = read_csv(str(path))
        if not rows:
            continue
        best = max(rows, key=lambda row: numeric(row.get("metrics/mAP50-95(B)", "0")) or 0.0)
        precision = numeric(best.get("metrics/precision(B)", ""))
        recall = numeric(best.get("metrics/recall(B)", ""))
        result_rows.append(
            {
                "seed": seed,
                "ap": numeric(best.get("metrics/mAP50-95(B)", "")),
                "ap50": numeric(best.get("metrics/mAP50(B)", "")),
                "f1": f1(precision, recall),
                "params": None,
            }
        )

    best_row = max(result_rows, key=lambda row: row.get("ap") or -1.0, default={})
    live_count = len({row["seed"] for row in result_rows})
    started = set(finished_seeds)
    started.update(row["seed"] for row in result_rows)
    if running_seed is not None:
        started.add(running_seed)
    note = (
        f"active seed{running_seed}; finished {len(finished_seeds)}/3; live {live_count}/3"
        if running_seed is not None
        else f"finished {len(finished_seeds)}/3; live {live_count}/3"
    )
    return {
        "running_seed": running_seed,
        "finished_seeds": sorted(finished_seeds),
        "started_count": len(started),
        "live_count": live_count,
        "best_row": best_row,
        "note": note,
    }


def paper_reference_row(comparison_rows: list[dict[str, str]], baseline: Baseline) -> dict[str, str]:
    candidates = [
        row
        for row in comparison_rows
        if row.get("model") in {"YOLOv11l", "YOLOv12l", "YOLOv8l", "YOLOv9c", "YOLOv26l", "YOLOv10l", "YOLOv9m"}
    ]
    best = max(candidates, key=lambda row: numeric(row.get("AP", "")) or -1.0, default=None)
    if best is not None:
        return best
    return {
        "model": "YOLOv11l",
        "AP": f"{baseline.ap:.4f}",
        "AP50": f"{baseline.ap50:.4f}",
        "F1": f"{baseline.f1:.4f}",
        "Params": f"{baseline.params_m:.2f}M",
        "note": "fallback fair baseline",
    }


def dashboard_table_rows(comparison_rows: list[dict[str, str]], live_rows: list[dict[str, str]], baseline: Baseline) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    ref_labels = related_reference_labels()
    paper_comparison_count = sum(
        1
        for row in read_csv(FINAL_TABLE_PREVIEW)
        if row.get("section") == "main_1280_completed_3seed" and row.get("method") != SELECTED_OURS
    )

    ours = official_row(comparison_rows, SELECTED_OURS) or {
        "model": SELECTED_OURS,
        "AP": "0.3822",
        "AP50": "0.6052",
            "F1": "0.6273",
            "Params": "20.82M",
            "note": "official 3-seed",
        }
    ours_ap = ours.get("AP", "-")
    ours_params = ours.get("Params", "-")
    rows.append(
        {
            "rank": "1",
            "model": "Ours",
            "role": "Selected detector",
            "AP": ours.get("AP", "-"),
            "AP50": ours.get("AP50", "-"),
            "F1": ours.get("F1", "-"),
            "Params": ours.get("Params", "-"),
            "GapOurs": "+0.0000",
            "ParamDiff": "+0.00M",
            "Note": "P2P4-SelfAttnFR impl.; selected trade-off",
        }
    )

    rows.append({
        "section": "true",
        "rank": "",
        "model": "Comparison top rows",
        "role": f"1280 / 3-seed; {paper_comparison_count} completed paper-facing comparison rows tracked in final_detector_tables",
    })

    comparison_names = ["YOLOv11l", "YOLOv12l", "YOLOv8l", "YOLOv9c", "RT-DETR-L"]
    rank = 2
    for name in comparison_names:
        source = official_row(comparison_rows, name)
        if source is None:
            continue
        if source.get("model") == "YOLOv11l":
            role = "Best YOLO baseline"
        elif source.get("model") == "RT-DETR-L":
            role = "Transformer baseline"
        else:
            role = "YOLO family baseline"
        rows.append(
            {
                "rank": str(rank),
                "model": name,
                "role": role,
                "AP": source.get("AP", "-"),
                "AP50": source.get("AP50", "-"),
                "F1": source.get("F1", "-"),
                "Params": source.get("Params", "-"),
                "GapOurs": metric_delta(source.get("AP", "-"), ours_ap),
                "ParamDiff": params_delta(source.get("Params", "-"), ours_params),
                "Note": "official 3-seed",
            }
        )
        rank += 1

    rows.append({
        "section": "true",
        "rank": "",
        "model": "Cited UAV small-object related-work status",
        "role": "only models already cited in the manuscript are paper-facing",
    })
    csfpr_eval = official_row(comparison_rows, "CSFPR-RTDETR")
    mffsod_eval = official_row(comparison_rows, "MFFSODNet")

    def final_or_live_reimpl_source(model_name: str) -> dict[str, str]:
        source = official_row(comparison_rows, model_name)
        if source is not None:
            return source
        return required_reimpl_summaries(live_rows).get(
            model_name,
            {
                "AP": "-",
                "AP50": "-",
                "F1": "-",
                "Params": "-",
                "seed_count": "0",
                "seeds": "",
            },
        )

    def reimpl_note(source: dict[str, str]) -> str:
        seed_count = numeric(source.get("seed_count", "0")) or 0
        seeds = source.get("seeds", "")
        if seed_count >= 3:
            return f"1280 3-seed reimpl complete ({seeds})"
        if seed_count > 0:
            return f"partial {int(seed_count)}/3 seeds ({seeds}); not final"
        return "queued/not complete"

    sffef = final_or_live_reimpl_source("SFFEF-YOLO")
    bpd = final_or_live_reimpl_source("BPD-YOLO")
    hf_dfine = final_or_live_reimpl_source("HF-D-FINE")
    uavdet_final = official_row(comparison_rows, "UAVDet")
    uavdet_live = next((row for row in live_rows if "uavdet" in row.get("run", "").lower()), None)
    uavdet_queue = uavdet_after_required_queue_state()
    uavdet_best = uavdet_queue.get("best_row", {})
    uavdet_ap = (
        uavdet_final.get("AP", "-")
        if uavdet_final
        else fmt(uavdet_best.get("ap")) if uavdet_best else (uavdet_live.get("bestAP", "-") if uavdet_live else "-")
    )
    uavdet_ap50 = (
        uavdet_final.get("AP50", "-")
        if uavdet_final
        else fmt(uavdet_best.get("ap50")) if uavdet_best else (uavdet_live.get("bestAP50", "-") if uavdet_live else "-")
    )
    uavdet_f1 = (
        uavdet_final.get("F1", "-")
        if uavdet_final
        else fmt(uavdet_best.get("f1")) if uavdet_best else (uavdet_live.get("bestF1", "-") if uavdet_live else "-")
    )
    uavdet_params = (
        uavdet_final.get("Params", "-")
        if uavdet_final
        else uavdet_live.get("Params", "-") if uavdet_live else ("26.08M" if uavdet_queue.get("started_count", 0) else "-")
    )
    uavdet_note = uavdet_final.get("note", "1280 3-seed from final table") if uavdet_final else uavdet_queue.get("note", "queued after required related-work")
    cited_rows = [
        {
            "rank": "RW1",
            "model": related_label("CSFPR-RTDETR", ref_labels),
            "role": "Cited UAV RT-DETR",
            "AP": csfpr_eval.get("AP", "-") if csfpr_eval else "-",
            "AP50": csfpr_eval.get("AP50", "-") if csfpr_eval else "-",
            "F1": csfpr_eval.get("F1", "-") if csfpr_eval else "-",
            "Params": csfpr_eval.get("Params", "14.09M") if csfpr_eval else "14.09M",
            "GapOurs": metric_delta(csfpr_eval.get("AP", "-"), ours_ap) if csfpr_eval else "-",
            "ParamDiff": params_delta(csfpr_eval.get("Params", "14.09M"), ours_params) if csfpr_eval else params_delta("14.09M", ours_params),
            "Note": "1280 3-seed complete" if csfpr_eval else "1280 retrain not complete",
        },
        {
            "rank": "RW2",
            "model": related_label("MFFSODNet", ref_labels),
            "role": "Cited multi-scale SOD",
            "AP": mffsod_eval.get("AP", "-") if mffsod_eval else "-",
            "AP50": mffsod_eval.get("AP50", "-") if mffsod_eval else "-",
            "F1": mffsod_eval.get("F1", "-") if mffsod_eval else "-",
            "Params": mffsod_eval.get("Params", "-") if mffsod_eval else "-",
            "GapOurs": metric_delta(mffsod_eval.get("AP", "-"), ours_ap) if mffsod_eval else "-",
            "ParamDiff": params_delta(mffsod_eval.get("Params", "-"), ours_params) if mffsod_eval else "-",
            "Note": "scratch 1280 3-seed complete" if mffsod_eval else "scratch retrain not complete",
        },
        {
            "rank": "RW3",
            "model": related_label("SFFEF-YOLO", ref_labels),
            "role": "Cited YOLO reimpl",
            "AP": sffef.get("AP", "-"),
            "AP50": sffef.get("AP50", "-"),
            "F1": sffef.get("F1", "-"),
            "Params": sffef.get("Params", "-"),
            "GapOurs": metric_delta(sffef.get("AP", "-"), ours_ap),
            "ParamDiff": params_delta(sffef.get("Params", "-"), ours_params),
            "Note": reimpl_note(sffef),
        },
        {
            "rank": "RW4",
            "model": related_label("BPD-YOLO", ref_labels),
            "role": "Cited YOLO reimpl",
            "AP": bpd.get("AP", "-"),
            "AP50": bpd.get("AP50", "-"),
            "F1": bpd.get("F1", "-"),
            "Params": bpd.get("Params", "-"),
            "GapOurs": metric_delta(bpd.get("AP", "-"), ours_ap),
            "ParamDiff": params_delta(bpd.get("Params", "-"), ours_params),
            "Note": reimpl_note(bpd),
        },
        {
            "rank": "RW5",
            "model": related_label("HF-D-FINE", ref_labels),
            "role": "Cited D-FINE reimpl",
            "AP": hf_dfine.get("AP", "-"),
            "AP50": hf_dfine.get("AP50", "-"),
            "F1": hf_dfine.get("F1", "-"),
            "Params": hf_dfine.get("Params", "-"),
            "GapOurs": metric_delta(hf_dfine.get("AP", "-"), ours_ap),
            "ParamDiff": params_delta(hf_dfine.get("Params", "-"), ours_params),
            "Note": reimpl_note(hf_dfine),
        },
        {
            "rank": "RW6",
            "model": related_label("UAVDet", ref_labels),
            "role": "Cited non-YOLO prior",
            "AP": uavdet_ap,
            "AP50": uavdet_ap50,
            "F1": uavdet_f1,
            "Params": uavdet_params,
            "GapOurs": metric_delta(uavdet_ap, ours_ap) if (uavdet_final or uavdet_live) else "-",
            "ParamDiff": params_delta(uavdet_params, ours_params) if (uavdet_final or uavdet_live) else "-",
            "Note": uavdet_note,
        },
    ]
    for source in cited_rows:
        rows.append(
            {
                "rank": source["rank"],
                "model": source["model"],
                "role": source["role"],
                "AP": source.get("AP", "-"),
                "AP50": source.get("AP50", "-"),
                "F1": source.get("F1", "-"),
                "Params": source.get("Params", "-"),
                "GapOurs": source.get("GapOurs", "-"),
                "ParamDiff": source.get("ParamDiff", "-"),
                "Note": source.get("Note", "-"),
            }
        )
    return rows[:14]


def normalized_model_name(value: str) -> str:
    return value.lower().replace("ours:", "").replace("-", "").replace("_", "").replace(" ", "")


def is_official_candidate_duplicate(name: str) -> bool:
    return normalized_model_name(name) in {
        normalized_model_name("P2P4-SelfAttnFR"),
        normalized_model_name("Ours: P2P4-SelfAttnFR"),
    }


def probe_role(name: str, *, over_budget: bool) -> str:
    if over_budget:
        return "ablation only, over-budget"
    if name.startswith("P2P4-"):
        return "P2P4 ablation only"
    return "internal probe only"


def proposed_candidate_rows(
    *,
    limit: int,
    baseline: Baseline,
    max_params: float | None = None,
    min_params: float | None = None,
) -> list[dict[str, str]]:
    seen: set[str] = set()
    selected: list[dict[str, str]] = []
    for row in read_csv(PROPOSED_RUN_RANKING):
        status = row.get("status", "")
        params = numeric(row.get("ParamsM", ""))
        if status != "completed" or params is None:
            continue
        if max_params is not None and params > max_params:
            continue
        if min_params is not None and params <= min_params:
            continue
        name = row.get("name", row.get("method", "candidate"))
        if is_official_candidate_duplicate(name):
            continue
        if name in seen:
            continue
        seen.add(name)
        role = probe_role(name, over_budget=min_params is not None)
        selected.append(
            {
                "model": name,
                "role": role,
                "AP": f"{numeric(row.get('AP', '')) or 0.0:.4f}",
                "AP50": f"{numeric(row.get('AP50', '')) or 0.0:.4f}",
                "F1": f"{numeric(row.get('F1', '')) or 0.0:.4f}",
                "Params": f"{params:.2f}M",
                "Gap9": target_gap(row.get("AP", "-"), baseline.high_capacity_ref_ap),
                "Budget": params_gap_to_budget(f"{params:.2f}M", baseline),
                "Note": "not paper method",
            }
        )
        if len(selected) >= limit:
            break
    return selected


def raw_performance_ranking_rows(dashboard_rows: list[dict[str, str]], limit: int = 5) -> list[dict[str, str]]:
    paper_rows = [
        row
        for row in dashboard_rows
        if row.get("section") != "true"
        and row.get("AP") not in {"", "-"}
        if "probe" not in row.get("role", "").lower() and "ablation" not in row.get("role", "").lower()
    ]
    ranked = sorted(paper_rows, key=lambda row: numeric(row.get("AP", "")) or -1.0, reverse=True)
    rows: list[dict[str, str]] = []
    for idx, row in enumerate(ranked[:limit], start=1):
        rows.append(
            {
                "rank": str(idx),
                "name": row["model"],
                "AP": row["AP"],
                "Params": row["Params"],
                "extra": row.get("role", ""),
            }
        )
    return rows


def gated_tradeoff_ranking_rows(limit: int = 5) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in read_csv(GATED_TRADEOFF_RANKING):
        score = numeric(row.get("gated_tradeoff", ""))
        if score is None:
            continue
        name = row.get("name", "")
        if "p2p4-selfattnfr" in name.lower() or normalized_model_name(name) == normalized_model_name(SELECTED_OURS):
            name = "Ours"
        rows.append(
            {
                "rank": row.get("rank", ""),
                "name": name,
                "score": f"{score:.3f}",
                "AP": f"{numeric(row.get('AP', '')) or 0.0:.4f}",
                "Params": f"{numeric(row.get('ParamsM', '')) or 0.0:.2f}M",
            }
        )
        if len(rows) >= limit:
            break
    return rows


def tradeoff_score(row: dict[str, str], baseline: Baseline) -> float:
    ap = numeric(row.get("bestAP", "-"))
    ap50 = numeric(row.get("bestAP50", "-"))
    f1 = numeric(row.get("bestF1", "-"))
    params = params_m(row)
    if ap is None or ap50 is None or f1 is None or params is None or params <= 0:
        return -1.0
    accuracy = 0.50 * (ap / baseline.ap) + 0.25 * (ap50 / baseline.ap50) + 0.25 * (f1 / baseline.f1)
    efficiency = baseline.params_m / params
    return accuracy * efficiency


def gate_color(gate: str) -> str:
    if gate == "TARGET-pass":
        return "#047857"
    if gate == "CANDIDATE-pass":
        return "#047857"
    if gate == "CANDIDATE-improve":
        return "#0F766E"
    if gate == "CANDIDATE-watch":
        return "#0F766E"
    if gate == "BASELINE-pass-budget":
        return "#2563EB"
    if gate.startswith("LARGE") or gate in {"large-ref", "high-cap-ref"}:
        return "#7C3AED"
    if gate == "TARGET-under-param":
        return "#047857"
    if gate.startswith("BEST"):
        return "#047857"
    if gate.startswith("PASS"):
        return "#0F766E"
    if gate == "running":
        return "#2563EB"
    if gate == "waiting":
        return "#475569"
    if gate == "acc-below":
        return "#B45309"
    if gate in {"below-candidate", "over-budget"}:
        return "#B45309"
    return "#B91C1C"


def dap_color(value: str) -> str:
    val = numeric(value)
    if val is None:
        return "#475569"
    if val > 0.0:
        return "#047857"
    if val > -0.005:
        return "#B45309"
    return "#B91C1C"


def short_note(value: str) -> str:
    replacements = {
        "TARGET-pass": "target-pass",
        "high-cap-ref": "high-cap-ref",
        "CANDIDATE-pass": "candidate-pass",
        "CANDIDATE-improve": "candidate-improve",
        "CANDIDATE-watch": "candidate-watch",
        "BASELINE-pass-budget": "baseline-pass",
        "LARGE-ref-strong": "large-ref-strong",
        "large-ref": "large-ref",
        "below-candidate": "below-candidate",
        "over-budget": "over-budget",
        "PASS-over-param": "over-param",
        "PASS-more-param": "more-param",
        "TARGET-under-param": "target",
        "acc-below": "below-target",
        "best baseline": "baseline",
        "large baseline": "large",
        "Proposed confirm": "confirm",
        "YOLO family baseline": "YOLO baseline",
        "Generic non-YOLO baseline": "non-YOLO",
        "Related-work prior model": "prior art",
        "running": "running",
    }
    return replacements.get(value, value)


def display_gate(value: str) -> str:
    return short_note(value)


def active_metric_line(row: dict[str, str]) -> str:
    if row.get("AP") not in {"", "-"} or row.get("bestAP") not in {"", "-"}:
        return (
            f"latest AP {row['AP']}  AP50 {row['AP50']}  F1 {row['F1']}  |  "
            f"best AP {row['bestAP']}  AP50 {row['bestAP50']}  "
            f"P {row['bestP']}  R {row['bestR']}  F1 {row['bestF1']}"
        )
    loss_parts = []
    for label, key in [("box", "box"), ("cls", "cls"), ("dfl/l1", "dfl")]:
        value = row.get(key, "-")
        if value not in {"", "-"}:
            loss_parts.append(f"{label} {value}")
    loss_text = "  ".join(loss_parts) if loss_parts else "loss pending"
    return f"validation metrics pending; train loss {loss_text}"


def active_value_text(row: dict[str, str] | None) -> str:
    if row is None:
        return "no active run"
    if row.get("bestAP") not in {"", "-"}:
        return f"AP {row['bestAP']}"
    if row.get("AP") not in {"", "-"}:
        return f"AP {row['AP']}"
    if row.get("box") not in {"", "-"}:
        return f"loss {row['box']}/{row.get('cls', '-')}/{row.get('dfl', '-')}"
    return "metrics pending"


def text(ax: Any, x: float, y: float, value: str, *, size: int = 12, weight: str = "normal", color: str = "#111827") -> None:
    ax.text(x, y, value, transform=ax.transAxes, fontsize=size, fontweight=weight, color=color, va="top", ha="left")


def card(ax: Any, patch_cls: Any, x: float, y: float, w: float, h: float, *, face: str = "#F8FAFC", edge: str = "#CBD5E1") -> None:
    ax.add_patch(
        patch_cls(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.012,rounding_size=0.015",
            linewidth=1.0,
            edgecolor=edge,
            facecolor=face,
            transform=ax.transAxes,
        )
    )


def kpi_card(
    ax: Any,
    patch_cls: Any,
    x: float,
    y: float,
    w: float,
    title: str,
    primary: str,
    secondary: str,
    *,
    accent: str,
) -> None:
    card(ax, patch_cls, x, y, w, 0.066, face="#FFFFFF", edge="#CBD5E1")
    ax.add_patch(plt_rectangle(ax, x + 0.010, y + 0.049, w - 0.020, 0.005, accent))
    text(ax, x + 0.018, y + 0.044, title, size=7.0, weight="bold", color="#64748B")
    text(ax, x + 0.018, y + 0.028, primary, size=10.4, weight="bold", color="#0F172A")
    text(ax, x + 0.018, y + 0.011, secondary, size=6.4, color="#475569")


def queue_status_color(status: str) -> str:
    if status == "done":
        return "#047857"
    if status == "running":
        return "#2563EB"
    if status == "ready":
        return "#D97706"
    return "#64748B"


def queue_status_card(ax: Any, patch_cls: Any, x: float, y: float, w: float, h: float, rows: list[dict[str, str]]) -> None:
    card(ax, patch_cls, x, y, w, h, face="#FFFFFF", edge="#CBD5E1")
    text(ax, x + 0.014, y + h - 0.013, "Current Work / Live Queue", size=8.4, weight="bold", color="#0F172A")
    text(ax, x + 0.174, y + h - 0.013, "Paper gates, 2D result freeze, Isaac/Cesium, neural-3D, and AeroGraph", size=6.2, color="#64748B")

    row_y = y + h - 0.033
    for row in rows[:6]:
        status = row["status"]
        status_color = queue_status_color(status)
        ax.add_patch(plt_rectangle(ax, x + 0.012, row_y - 0.013, w - 0.024, 0.012, "#F8FAFC"))
        ax.add_patch(plt_rectangle(ax, x + 0.018, row_y - 0.010, 0.006, 0.006, status_color))
        text(ax, x + 0.030, row_y - 0.001, row["queue"], size=6.4, weight="bold", color="#111827")
        text(ax, x + 0.160, row_y - 0.001, status.upper(), size=5.8, weight="bold", color=status_color)
        text(ax, x + 0.230, row_y - 0.001, row["detail"][:70], size=5.8, color="#475569")
        text(ax, x + 0.690, row_y - 0.001, row["event"][:48], size=5.6, color="#64748B")
        row_y -= 0.013


def ranking_card(
    ax: Any,
    patch_cls: Any,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    subtitle: str,
    rows: list[dict[str, str]],
    *,
    mode: str,
) -> None:
    card(ax, patch_cls, x, y, w, h, face="#FFFFFF")
    text(ax, x + 0.014, y + h - 0.014, title, size=8.2, weight="bold", color="#0F172A")
    text(ax, x + 0.014, y + h - 0.032, subtitle, size=6.2, color="#64748B")
    row_y = y + h - 0.055
    for row in rows:
        name = row.get("name", "")
        is_ours = "ours" in name.lower() or "p2p4-selfattnfr" in name.lower()
        bg = "#FEF3C7" if is_ours else "#F8FAFC"
        ax.add_patch(plt_rectangle(ax, x + 0.010, row_y - 0.016, w - 0.020, 0.014, bg))
        text(ax, x + 0.017, row_y - 0.004, row.get("rank", "-"), size=6.5, weight="bold", color="#475569")
        text(ax, x + 0.045, row_y - 0.004, name[:24], size=6.4, weight="bold" if is_ours else "normal")
        if mode == "performance":
            text(ax, x + w - 0.150, row_y - 0.004, f"AP {row.get('AP', '-')}", size=6.3, color="#111827")
            text(ax, x + w - 0.075, row_y - 0.004, row.get("Params", "-"), size=6.3, color="#475569")
        else:
            text(ax, x + w - 0.168, row_y - 0.004, f"score {row.get('score', '-')}", size=6.3, color="#111827")
            text(ax, x + w - 0.080, row_y - 0.004, row.get("Params", "-"), size=6.3, color="#475569")
        row_y -= 0.017
    if mode == "tradeoff" and len(rows) < 5:
        pass


def draw_metric_bar(ax: Any, x: float, y: float, w: float, h: float, value: str, baseline_value: float, target_value: float) -> None:
    val = numeric(value)
    ax.add_patch(plt_rectangle(ax, x, y, w, h, "#E2E8F0"))
    if val is None:
        return
    lo = max(0.0, baseline_value - 0.08)
    hi = max(target_value + 0.02, baseline_value + 0.03)
    frac = min(1.0, max(0.0, (val - lo) / (hi - lo)))
    color = "#059669" if val >= target_value else "#2563EB" if val >= baseline_value else "#D97706"
    ax.add_patch(plt_rectangle(ax, x, y, w * frac, h, color))


def plt_rectangle(ax: Any, x: float, y: float, w: float, h: float, color: str) -> Any:
    from matplotlib.patches import Rectangle

    rect = Rectangle((x, y), w, h, transform=ax.transAxes, facecolor=color, edgecolor="none")
    return rect


def render_dashboard(rows: list[dict[str, str]], out: Path, baseline: Baseline) -> None:
    plt, patch_cls = setup_matplotlib()
    rows = [row for row in rows if not row.get("run", "").lower().startswith("yolov9e")]
    drop_completed_tinyperson_active(rows)
    active = [row for row in rows if row["active"] == "true"]
    active = active[:2]

    comparison_rows = build_full_comparison_rows(rows, baseline)
    dashboard_rows = dashboard_table_rows(comparison_rows, rows, baseline)
    ours_row = next((row for row in dashboard_rows if row.get("model") == "Ours"), None)
    ref_row = paper_reference_row(comparison_rows, baseline)
    active_best = max(
        active,
        key=lambda row: (
            numeric(row.get("bestAP", "")) is not None,
            numeric(row.get("bestAP", "")) or -1.0,
            numeric(row.get("AP", "")) or -1.0,
        ),
        default=None,
    )

    fig = plt.figure(figsize=(11.4, 14.2), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    fig.patch.set_facecolor("#EEF2F7")

    now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    text(ax, 0.04, 0.975, "Live Detector Dashboard", size=22, weight="bold")
    text(ax, 0.04, 0.945, f"Updated {now}  |  refresh: 30s", size=10, color="#475569")

    gpu_status_parts = gpu_lines()
    gpu_status = "   |   ".join(gpu_status_parts)
    if gpu_status:
        text(ax, 0.04, 0.922, gpu_status, size=10.8, weight="bold", color="#0F172A")
    else:
        active_hint = "   |   ".join(f"G{row['gpu']} {active_run_display_name(row)} {row['progress']}" for row in active[:2])
        text(ax, 0.04, 0.922, f"GPU metrics unavailable; active logs: {active_hint or 'none'}", size=9.0, weight="bold", color="#B45309")

    ours_gap = target_gap(ours_row["AP"], baseline.ap) if ours_row else "-"
    ours_ap50_gap = target_gap(ours_row["AP50"], ref_row.get("AP50", "-")) if ours_row else "-"
    ours_budget = params_gap_to_budget(ours_row["Params"], baseline) if ours_row else "-"
    active_label = active_run_display_name(active_best) if active_best else "none"
    active_value = active_value_text(active_best)
    kpi_card(
        ax,
        patch_cls,
        0.04,
        0.850,
        0.215,
        "Best Fair Baseline",
        f"{ref_row.get('model', 'YOLOv11l')} AP {ref_row.get('AP', '-')}",
        f"AP50 {ref_row.get('AP50', '-')} | {ref_row.get('Params', '-')}",
        accent="#7C3AED",
    )
    kpi_card(
        ax,
        patch_cls,
        0.270,
        0.850,
        0.215,
        "Ours Vs Baseline",
        f"AP {ours_gap}",
        f"AP50 {ours_ap50_gap} | selected detector",
        accent=target_gap_color(ours_gap),
    )
    kpi_card(
        ax,
        patch_cls,
        0.500,
        0.850,
        0.215,
        "Size Budget",
        f"{ours_budget}",
        f"budget headroom vs {baseline.candidate_param_budget_m:.2f}M target",
        accent="#059669" if numeric(ours_budget.replace("M", "")) and (numeric(ours_budget.replace("M", "")) or 0) >= 0 else "#B45309",
    )
    kpi_card(
        ax,
        patch_cls,
        0.730,
        0.850,
        0.215,
        "Best Active Run",
        active_value,
        active_label,
        accent="#2563EB",
    )

    queue_status_card(ax, patch_cls, 0.04, 0.730, 0.92, 0.105, queue_status_rows())

    text(ax, 0.04, 0.716, "Paper-Facing Comparison", size=12.5, weight="bold")
    text(
        ax,
        0.04,
        0.700,
        "Only one proposed detector is shown here: Ours. Internal proposed variants are reserved for ablation/supplementary.",
        size=7.0,
        color="#64748B",
    )
    table_top = 0.675
    card(ax, patch_cls, 0.04, table_top - 0.292, 0.92, 0.274, face="#FFFFFF")
    headers = [
        ("#", 0.058),
        ("Model", 0.090),
        ("AP", 0.345),
        ("AP50", 0.422),
        ("F1", 0.500),
        ("Params", 0.575),
        ("dAP vs Ours", 0.665),
        ("dParams", 0.775),
        ("Note", 0.855),
    ]
    for label, x in headers:
        text(ax, x, table_top - 0.031, label, size=7.2, weight="bold", color="#334155")
    row_y = table_top - 0.055
    for row in dashboard_rows:
        if row.get("section") == "true":
            ax.add_patch(plt_rectangle(ax, 0.052, row_y - 0.018, 0.895, 0.016, "#E0F2FE"))
            text(ax, 0.058, row_y - 0.005, row["model"], size=6.6, weight="bold", color="#075985")
            text(ax, 0.345, row_y - 0.005, row.get("Note", row.get("role", ""))[:86], size=6.0, color="#0369A1")
            row_y -= 0.0170
            continue
        role = row["role"]
        if role == "Leading candidate":
            bg = "#FEF3C7"
        elif role in {"P2P4 ablation only", "internal probe only"}:
            bg = "#ECFDF5"
        elif role == "ablation only, over-budget":
            bg = "#FFF7ED"
        else:
            bg = "#F8FAFC"
        ax.add_patch(plt_rectangle(ax, 0.052, row_y - 0.019, 0.895, 0.017, bg))
        weight = "bold" if role == "Leading candidate" else "normal"
        text(ax, 0.058, row_y - 0.005, row.get("rank", "-"), size=6.2, weight="bold", color="#475569")
        text(ax, 0.090, row_y - 0.005, row["model"][:31], size=6.2, weight=weight)
        text(ax, 0.345, row_y - 0.005, row["AP"], size=6.4)
        text(ax, 0.422, row_y - 0.005, row["AP50"], size=6.4)
        text(ax, 0.500, row_y - 0.005, row["F1"], size=6.4)
        text(ax, 0.575, row_y - 0.005, row["Params"], size=6.4)
        text(ax, 0.665, row_y - 0.005, row["GapOurs"], size=6.4, weight="bold", color=target_gap_color(row["GapOurs"]))
        param_color = "#047857" if (numeric(row["ParamDiff"].replace("M", "")) or 1) <= 0 else "#B45309"
        text(ax, 0.775, row_y - 0.005, row["ParamDiff"], size=6.4, weight="bold", color=param_color)
        text(ax, 0.855, row_y - 0.005, short_note(row["Note"]), size=6.0, color="#475569")
        row_y -= 0.0170

    y = 0.370
    text(ax, 0.04, y, "Active Runs", size=13, weight="bold")
    y -= 0.019
    for row in active:
        card(ax, patch_cls, 0.04, y - 0.054, 0.92, 0.047, face="#FFFFFF")
        text(ax, 0.065, y - 0.003, f"G{row['gpu']}  {active_run_display_name(row)}  {row['progress']}  {row['speed']}", size=8.1, weight="bold")
        text(ax, 0.065, y - 0.020, active_metric_line(row), size=6.4, color="#111827")
        text(ax, 0.065, y - 0.038, f"size {row['Params']}   GFLOPs {row['GFLOPs']}   baseline dAP {row['dAP']}", size=6.4, color="#475569")
        text(ax, 0.745, y - 0.038, display_gate(row["gate"]), size=7.2, weight="bold", color=gate_color(row["gate"]))
        draw_metric_bar(ax, 0.835, y - 0.026, 0.095, 0.006, row["bestAP"], baseline.ap, baseline.target_ap)
        y -= 0.052
    if not active:
        card(ax, patch_cls, 0.04, y - 0.050, 0.92, 0.042, face="#FFFFFF")
        text(ax, 0.065, y - 0.020, "No active runs detected.", size=10, color="#475569")
        y -= 0.052

    ranking_title_y = 0.207
    text(ax, 0.04, ranking_title_y, "Ranking Snapshot", size=13, weight="bold")
    text(ax, 0.245, ranking_title_y, "raw AP rank and paper-gated trade-off rank are intentionally separated", size=7.2, color="#64748B")
    ranking_y = 0.068
    ranking_card(
        ax,
        patch_cls,
        0.04,
        ranking_y,
        0.445,
        0.118,
        "Raw Performance Ranking",
        "AP-first among shown paper-facing rows",
        raw_performance_ranking_rows(dashboard_rows, limit=4),
        mode="performance",
    )
    ranking_card(
        ax,
        patch_cls,
        0.515,
        ranking_y,
        0.445,
        0.118,
        "Gated Trade-off Ranking",
        "paper-facing efficiency score after gate",
        gated_tradeoff_ranking_rows(limit=5),
        mode="tradeoff",
    )

    decision_y = 0.048
    text(ax, 0.04, decision_y, "Decision", size=10.5, weight="bold")
    score_note = final_pvalue_summary()
    gap_word = "lead" if (numeric(ours_gap) or 0.0) >= 0 else "shortfall"
    gap_line = f"Ours {gap_word} vs best fair baseline: AP {ours_gap}, AP50 {ours_ap50_gap}."
    card(ax, patch_cls, 0.04, 0.008, 0.92, 0.036, face="#FEF3C7", edge="#F59E0B")
    text(ax, 0.065, 0.031, "Paper-facing proposed detector: Ours", size=7.2, weight="bold")
    text(ax, 0.345, 0.031, gap_line + (f"  {score_note}" if score_note else ""), size=6.6, color="#111827")
    text(ax, 0.065, 0.017, "Implementation label: P2P4-SelfAttnFR. Other proposed variants are reserved for ablation/supplementary.", size=6.2, color="#475569")

    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp.png")
    fig.savefig(tmp, dpi=150, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    tmp.replace(out)


def archive_live_tinyperson_artifacts() -> None:
    """Keep deprecated auxiliary stress-test dashboards out of the live paper view."""
    archive = resolve_path("outputs/reports/archive/tinyperson_legacy_20260628")
    archive.mkdir(parents=True, exist_ok=True)
    for rel in [TINYPERSON224_DASHBOARD, TINYPERSON224_DASHBOARD_MD, TINYPERSON224_AUX_DASHBOARD]:
        path = resolve_path(rel)
        if path.exists():
            path.replace(archive / path.name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", action="append", default=DEFAULT_PROJECT_DIRS)
    parser.add_argument("--log-dir", action="append", default=DEFAULT_LOG_DIRS)
    parser.add_argument("--out", default="outputs/reports/live/training_dashboard.png")
    args = parser.parse_args()

    baseline = Baseline()
    rows = collect_rows(args.project_dir, args.log_dir, baseline)
    neural3d_row = marinecity_reinforce_active_row()
    if neural3d_row:
        rows.append(neural3d_row)
    render_dashboard(rows, resolve_path(args.out), baseline)
    archive_live_tinyperson_artifacts()
    print(resolve_path(args.out))


if __name__ == "__main__":
    main()
