"""Track visible detector training experiments and paper-ready summaries."""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.config import PROJECT_ROOT, resolve_path


DEFAULT_OUTPUT_ROOT = Path("outputs/experiments")
INDEX_COLUMNS = [
    "run_id",
    "status",
    "started_at",
    "finished_at",
    "model",
    "dataset",
    "epochs",
    "imgsz",
    "batch",
    "seed",
    "AP",
    "AP50",
    "ROC-AUC",
    "precision",
    "recall",
    "run_dir",
    "results_csv",
    "best_weight",
]


@dataclass(frozen=True)
class ExperimentPaths:
    """Paths belonging to one tracked experiment."""

    run_dir: Path
    manifest: Path
    markdown: Path


def now_iso() -> str:
    """Return a stable local timestamp with timezone."""

    return datetime.now().astimezone().isoformat(timespec="seconds")


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def safe_slug(value: str) -> str:
    """Create a Windows-friendly slug."""

    slug = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_") or "run"


def get_git_commit() -> str | None:
    """Return current git commit, or None outside git."""

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            check=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def experiment_paths(run_id: str, *, output_root: str | Path = DEFAULT_OUTPUT_ROOT) -> ExperimentPaths:
    output_root = resolve_path(output_root)
    run_dir = output_root / run_id
    return ExperimentPaths(run_dir=run_dir, manifest=run_dir / "manifest.json", markdown=run_dir / "experiment.md")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def read_manifest(run_id: str, *, output_root: str | Path = DEFAULT_OUTPUT_ROOT) -> dict[str, Any]:
    paths = experiment_paths(run_id, output_root=output_root)
    if not paths.manifest.exists():
        raise FileNotFoundError(f"Experiment manifest not found: {paths.manifest}")
    return json.loads(paths.manifest.read_text(encoding="utf-8"))


def start_experiment(
    *,
    model: str,
    dataset: str,
    epochs: int,
    imgsz: int,
    batch: int,
    data_yaml: str | Path,
    seed: int | None = None,
    command: str | None = None,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    visible_execution: bool = True,
    notes: str | None = None,
) -> dict[str, Any]:
    """Create a tracked experiment folder and manifest."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_slug = safe_slug(Path(model).stem)
    dataset_slug = safe_slug(dataset)
    run_id = f"{timestamp}_{model_slug}_{dataset_slug}"
    paths = experiment_paths(run_id, output_root=output_root)
    for subdir in ("logs", "metrics", "artifacts"):
        (paths.run_dir / subdir).mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "run_id": run_id,
        "status": "running",
        "started_at": now_iso(),
        "finished_at": None,
        "model": model,
        "dataset": dataset,
        "epochs": epochs,
        "imgsz": imgsz,
        "batch": batch,
        "seed": seed,
        "data_yaml": str(resolve_path(data_yaml)),
        "command": command,
        "visible_execution": visible_execution,
        "git_commit": get_git_commit(),
        "conda_env": os.environ.get("CONDA_DEFAULT_ENV"),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "notes": notes or "",
        "metrics": {},
        "artifacts": {},
    }
    write_json(paths.manifest, manifest)
    write_markdown_summary(manifest, paths.markdown)
    write_experiment_index(output_root)
    return manifest


def find_latest_results_csv(detector_root: str | Path, *, started_at: str | None = None) -> Path | None:
    """Find the newest Ultralytics results.csv, preferring files written after start."""

    root = resolve_path(detector_root)
    if not root.exists():
        return None
    candidates = sorted(root.rglob("results.csv"), key=lambda path: path.stat().st_mtime, reverse=True)
    started_dt = parse_iso(started_at)
    if started_dt is None:
        return candidates[0] if candidates else None
    if started_dt.tzinfo is None:
        started_dt = started_dt.replace(tzinfo=timezone.utc)
    for candidate in candidates:
        modified = datetime.fromtimestamp(candidate.stat().st_mtime, tz=started_dt.tzinfo)
        if modified >= started_dt:
            return candidate
    return candidates[0] if candidates else None


def last_csv_row(path: Path) -> dict[str, str]:
    rows = list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))
    return rows[-1] if rows else {}


def as_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def first_metric(row: dict[str, str], keys: list[str]) -> float | None:
    stripped = {key.strip(): value for key, value in row.items()}
    for key in keys:
        value = as_float(stripped.get(key))
        if value is not None:
            return value
    return None


def parse_ultralytics_metrics(results_csv: Path) -> dict[str, Any]:
    """Parse the final row of an Ultralytics training results.csv."""

    row = last_csv_row(results_csv)
    if not row:
        return {}
    return {
        "epoch": first_metric(row, ["epoch"]),
        "precision": first_metric(row, ["metrics/precision(B)", "metrics/precision"]),
        "recall": first_metric(row, ["metrics/recall(B)", "metrics/recall"]),
        "AP50": first_metric(row, ["metrics/mAP50(B)", "metrics/mAP50"]),
        "AP": first_metric(row, ["metrics/mAP50-95(B)", "metrics/mAP50-95"]),
        "train_box_loss": first_metric(row, ["train/box_loss"]),
        "val_box_loss": first_metric(row, ["val/box_loss"]),
    }


def find_weight_files(results_csv: Path | None) -> dict[str, str]:
    if results_csv is None:
        return {}
    weights_dir = results_csv.parent / "weights"
    artifacts: dict[str, str] = {"results_csv": str(results_csv)}
    for name in ("best.pt", "last.pt"):
        path = weights_dir / name
        if path.exists():
            artifacts[name.replace(".pt", "_weight")] = str(path)
    return artifacts


def finish_experiment(
    *,
    run_id: str,
    status: str,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    detector_root: str | Path = "outputs/detectors",
    results_csv: str | Path | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Mark an experiment finished and attach metrics/artifacts."""

    paths = experiment_paths(run_id, output_root=output_root)
    manifest = read_manifest(run_id, output_root=output_root)
    resolved_results = resolve_path(results_csv) if results_csv else find_latest_results_csv(detector_root, started_at=manifest.get("started_at"))
    metrics = parse_ultralytics_metrics(resolved_results) if resolved_results and resolved_results.exists() else {}
    artifacts = find_weight_files(resolved_results)

    manifest["status"] = status
    manifest["finished_at"] = now_iso()
    manifest["metrics"] = metrics
    manifest["artifacts"] = artifacts
    if notes:
        manifest["notes"] = "\n".join(part for part in [manifest.get("notes", ""), notes] if part)
    write_json(paths.manifest, manifest)
    write_markdown_summary(manifest, paths.markdown)
    write_experiment_index(output_root)
    return manifest


def format_metric(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_markdown_summary(manifest: dict[str, Any], path: Path) -> None:
    """Write a compact Markdown summary for one run."""

    metrics = manifest.get("metrics", {}) or {}
    artifacts = manifest.get("artifacts", {}) or {}
    lines = [
        f"# Training Experiment: {manifest['run_id']}",
        "",
        "## Summary",
        "",
        f"- Status: {manifest.get('status', '')}",
        f"- Model: {manifest.get('model', '')}",
        f"- Seed: {manifest.get('seed') if manifest.get('seed') is not None else ''}",
        f"- Dataset: {manifest.get('dataset', '')}",
        f"- Started: {manifest.get('started_at', '')}",
        f"- Finished: {manifest.get('finished_at') or ''}",
        f"- Visible execution: {manifest.get('visible_execution', False)}",
        f"- Git commit: {manifest.get('git_commit') or ''}",
        "",
        "## Command",
        "",
        "```bat",
        manifest.get("command") or "",
        "```",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| AP | {format_metric(metrics.get('AP'))} |",
        f"| AP50 | {format_metric(metrics.get('AP50'))} |",
        f"| ROC-AUC | {format_metric(metrics.get('ROC-AUC'))} |",
        f"| Precision | {format_metric(metrics.get('precision'))} |",
        f"| Recall | {format_metric(metrics.get('recall'))} |",
        f"| Epoch | {format_metric(metrics.get('epoch'))} |",
        "",
        "## Artifacts",
        "",
    ]
    if artifacts:
        for key, value in artifacts.items():
            lines.append(f"- {key}: `{value}`")
    else:
        lines.append("- No artifacts recorded yet.")
    if manifest.get("notes"):
        lines.extend(["", "## Notes", "", str(manifest["notes"])])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_all_manifests(output_root: str | Path = DEFAULT_OUTPUT_ROOT) -> list[dict[str, Any]]:
    root = resolve_path(output_root)
    manifests: list[dict[str, Any]] = []
    for manifest_path in sorted(root.glob("*/manifest.json")):
        try:
            manifests.append(json.loads(manifest_path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return manifests


def manifest_to_index_row(manifest: dict[str, Any], *, output_root: str | Path = DEFAULT_OUTPUT_ROOT) -> dict[str, str]:
    metrics = manifest.get("metrics", {}) or {}
    artifacts = manifest.get("artifacts", {}) or {}
    row = {
        "run_id": manifest.get("run_id", ""),
        "status": manifest.get("status", ""),
        "started_at": manifest.get("started_at", ""),
        "finished_at": manifest.get("finished_at") or "",
        "model": manifest.get("model", ""),
        "dataset": manifest.get("dataset", ""),
        "epochs": str(manifest.get("epochs", "")),
        "imgsz": str(manifest.get("imgsz", "")),
        "batch": str(manifest.get("batch", "")),
        "seed": str(manifest.get("seed", "")),
        "AP": format_metric(metrics.get("AP")),
        "AP50": format_metric(metrics.get("AP50")),
        "ROC-AUC": format_metric(metrics.get("ROC-AUC")),
        "precision": format_metric(metrics.get("precision")),
        "recall": format_metric(metrics.get("recall")),
        "run_dir": str(experiment_paths(manifest.get("run_id", ""), output_root=output_root).run_dir) if manifest.get("run_id") else "",
        "results_csv": artifacts.get("results_csv", ""),
        "best_weight": artifacts.get("best_weight", ""),
    }
    return row


def write_experiment_index(output_root: str | Path = DEFAULT_OUTPUT_ROOT) -> Path:
    root = resolve_path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    index_path = root / "training_experiment_index.csv"
    rows = [manifest_to_index_row(manifest, output_root=root) for manifest in load_all_manifests(root)]
    with index_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=INDEX_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return index_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Track CoM3D-ACE training experiments.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    start = subparsers.add_parser("start", help="Create a running experiment record.")
    start.add_argument("--model", required=True)
    start.add_argument("--dataset", default="VisDrone2019-DET")
    start.add_argument("--epochs", type=int, default=100)
    start.add_argument("--imgsz", type=int, default=1280)
    start.add_argument("--batch", type=int, default=8)
    start.add_argument("--seed", type=int, default=None)
    start.add_argument("--data-yaml", default="configs/detector/visdrone_yolo_data.yaml")
    start.add_argument("--command", default=None)
    start.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    start.add_argument("--notes", default=None)
    start.add_argument("--hidden-execution", action="store_true")
    start.add_argument("--print-run-id", action="store_true")

    finish = subparsers.add_parser("finish", help="Finish an experiment record.")
    finish.add_argument("--run-id", required=True)
    finish.add_argument("--status", choices=["completed", "failed", "cancelled"], default="completed")
    finish.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    finish.add_argument("--detector-root", default="outputs/detectors")
    finish.add_argument("--results-csv", default=None)
    finish.add_argument("--notes", default=None)

    index = subparsers.add_parser("index", help="Rewrite the experiment CSV index.")
    index.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.mode == "start":
        manifest = start_experiment(
            model=args.model,
            dataset=args.dataset,
            epochs=args.epochs,
            imgsz=args.imgsz,
            batch=args.batch,
            data_yaml=args.data_yaml,
            seed=args.seed,
            command=args.command,
            output_root=args.output_root,
            visible_execution=not args.hidden_execution,
            notes=args.notes,
        )
        if args.print_run_id:
            print(manifest["run_id"])
        else:
            print(json.dumps(manifest, indent=2, ensure_ascii=False))
    elif args.mode == "finish":
        manifest = finish_experiment(
            run_id=args.run_id,
            status=args.status,
            output_root=args.output_root,
            detector_root=args.detector_root,
            results_csv=args.results_csv,
            notes=args.notes,
        )
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
    else:
        index_path = write_experiment_index(args.output_root)
        print(index_path)


if __name__ == "__main__":
    main()
