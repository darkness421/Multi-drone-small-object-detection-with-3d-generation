"""Generate tmux job scripts for proposed detector ablations."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shlex
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.config import read_yaml, resolve_path


@dataclass(frozen=True)
class ProposedJob:
    ablation: str
    method: str
    base_model: str
    train_model: str
    proposed_module: str
    model_patches: str
    implementation_status: str
    seed: int
    gpu: int
    run_name: str
    log_file: Path
    status: str
    skip_reason: str
    command: str


def slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", Path(value).stem).strip("_").lower()


def fmt_template(template: str, base_model: str) -> str:
    base_slug = slug(base_model)
    return template.format(base_model=base_model, base_slug=base_slug)


def required_files_exist(requirements: list[str], base_model: str) -> tuple[bool, str]:
    missing: list[str] = []
    for item in requirements:
        path = resolve_path(fmt_template(item, base_model))
        if not path.exists():
            missing.append(str(path))
    if missing:
        return False, "missing required files: " + "; ".join(missing)
    return True, ""


def sh(value: str | Path | int) -> str:
    return shlex.quote(str(value))


def build_jobs(
    config: dict[str, Any],
    *,
    conda_env: str,
    session: str,
    gpus: list[int],
    epochs: int | None,
    batch: int | None,
    imgsz: int | None,
    seeds: list[int] | None,
    enable_planned: bool,
    completed_keys: set[tuple[str, str, str, int]] | None = None,
) -> list[ProposedJob]:
    training = config.get("training", {})
    data_yaml = str(config["data_yaml"])
    dataset_tag = str(config.get("dataset_tag", "dataset"))
    project = str(config.get("project", "outputs/detectors/server_proposed_ablation"))
    log_dir = resolve_path(config.get("log_dir", "outputs/logs/server_baselines"))
    selected_epochs = int(epochs if epochs is not None else training.get("epochs", 100))
    selected_batch = int(batch if batch is not None else training.get("batch", 8))
    selected_imgsz = int(imgsz if imgsz is not None else training.get("imgsz", 1280))
    selected_seeds = seeds or [int(seed) for seed in training.get("seeds", [42, 123, 2026])]
    deterministic = bool(training.get("deterministic", True))

    jobs: list[ProposedJob] = []
    job_index = 0
    for base_model in config.get("base_models", ["yolo11s.pt"]):
        base_model = str(base_model)
        for ablation_cfg in config.get("ablations", []):
            ablation = str(ablation_cfg["name"])
            method = fmt_template(str(ablation_cfg.get("method_template", f"Proposed-{ablation}-{{base_slug}}")), base_model)
            proposed_module = str(ablation_cfg.get("proposed_module", ablation))
            model_patches = str(ablation_cfg.get("model_patches", "") or "")
            implementation_status = str(ablation_cfg.get("implementation_status", "planned"))
            enabled = bool(ablation_cfg.get("enabled", False))
            train_model = fmt_template(str(ablation_cfg.get("train_model_template", "{base_model}")), base_model)
            requirements = [str(item) for item in ablation_cfg.get("requires", [])]
            requirements_ready, missing_reason = required_files_exist(requirements, base_model) if requirements else (True, "")
            should_queue = enabled and (implementation_status == "implemented" or enable_planned) and requirements_ready
            skip_reason = ""
            if not should_queue:
                if not enabled:
                    skip_reason = str(ablation_cfg.get("skip_reason", "ablation disabled until implementation is ready"))
                elif not requirements_ready:
                    skip_reason = missing_reason
                elif implementation_status != "implemented" and not enable_planned:
                    skip_reason = "planned ablation; pass --enable-planned to queue after implementation is verified"

            for seed in selected_seeds:
                run_name = f"proposed_{ablation}_{slug(base_model)}_{dataset_tag}_seed{seed}"
                log_file = log_dir / f"{run_name}.log"
                completed_key = (base_model, ablation, proposed_module, int(seed))
                if should_queue and completed_keys and completed_key in completed_keys:
                    gpu = -1
                    command = ""
                    status = "skipped_completed"
                    completed_reason = "completed in results CSV"
                    jobs.append(
                        ProposedJob(
                            ablation=ablation,
                            method=method,
                            base_model=base_model,
                            train_model=train_model,
                            proposed_module=proposed_module,
                            model_patches=model_patches,
                            implementation_status=implementation_status,
                            seed=int(seed),
                            gpu=gpu,
                            run_name=run_name,
                            log_file=log_file,
                            status=status,
                            skip_reason=completed_reason,
                            command=command,
                        )
                    )
                    continue
                gpu = gpus[job_index % len(gpus)] if should_queue else -1
                if should_queue:
                    command_parts = [
                        "conda",
                        "run",
                        "--no-capture-output",
                        "-n",
                        conda_env,
                        "python",
                        "-m",
                        "detectors.train_yolo",
                        "train",
                        "--model",
                        train_model,
                        "--data-yaml",
                        data_yaml,
                        "--epochs",
                        str(selected_epochs),
                        "--imgsz",
                        str(selected_imgsz),
                        "--batch",
                        str(selected_batch),
                        "--device",
                        str(gpu),
                        "--seed",
                        str(seed),
                        "--project",
                        project,
                        "--name",
                        run_name,
                        "--method",
                        method,
                        "--ablation",
                        ablation,
                        "--base-model",
                        base_model,
                        "--proposed-module",
                        proposed_module,
                        "--model-patches",
                        model_patches,
                        "--implementation-status",
                        implementation_status,
                    ]
                    if not model_patches:
                        index = command_parts.index("--model-patches")
                        del command_parts[index : index + 2]
                    if not deterministic:
                        command_parts.append("--non-deterministic")
                    command_parts[command_parts.index("--device") + 1] = "0"
                    command = (
                        f"CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES={sh(gpu)} "
                        + " ".join(shlex.quote(part) for part in command_parts)
                    )
                    status = "queued"
                    job_index += 1
                else:
                    command = ""
                    status = "skipped_not_implemented"
                jobs.append(
                    ProposedJob(
                        ablation=ablation,
                        method=method,
                        base_model=base_model,
                        train_model=train_model,
                        proposed_module=proposed_module,
                        model_patches=model_patches,
                        implementation_status=implementation_status,
                        seed=int(seed),
                        gpu=gpu,
                        run_name=run_name,
                        log_file=log_file,
                        status=status,
                        skip_reason=skip_reason,
                        command=command,
                    )
                )
    return jobs


def load_completed_keys(paths: list[Path]) -> set[tuple[str, str, str, int]]:
    completed: set[tuple[str, str, str, int]] = set()
    for path in paths:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if str(row.get("status", "")).strip().lower() != "completed":
                    continue
                base_model = str(row.get("base_model") or row.get("model") or "").strip()
                ablation = str(row.get("ablation") or "").strip()
                proposed_module = str(row.get("proposed_module") or "").strip()
                if not base_model or not ablation or not proposed_module:
                    continue
                try:
                    seed = int(float(str(row.get("seed", "")).strip()))
                except ValueError:
                    continue
                completed.add((base_model, ablation, proposed_module, seed))
    return completed


def write_command_csv(path: Path, jobs: list[ProposedJob], session: str, data_yaml: str, epochs: int, batch: int, imgsz: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "created_at",
        "session",
        "ablation",
        "method",
        "base_model",
        "train_model",
        "proposed_module",
        "model_patches",
        "implementation_status",
        "seed",
        "physical_gpu",
        "ultralytics_device",
        "imgsz",
        "batch",
        "epochs",
        "data_yaml",
        "run_name",
        "log_file",
        "status",
        "skip_reason",
        "command",
    ]
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        if not exists:
            writer.writeheader()
        created_at = datetime.now().astimezone().isoformat(timespec="seconds")
        for job in jobs:
            writer.writerow(
                {
                    "created_at": created_at,
                    "session": session,
                    "ablation": job.ablation,
                    "method": job.method,
                    "base_model": job.base_model,
                    "train_model": job.train_model,
                    "proposed_module": job.proposed_module,
                    "model_patches": job.model_patches,
                    "implementation_status": job.implementation_status,
                    "seed": job.seed,
                    "physical_gpu": job.gpu if job.gpu >= 0 else "",
                    "ultralytics_device": "0" if job.gpu >= 0 else "",
                    "imgsz": imgsz,
                    "batch": batch,
                    "epochs": epochs,
                    "data_yaml": data_yaml,
                    "run_name": job.run_name,
                    "log_file": str(job.log_file),
                    "status": job.status,
                    "skip_reason": job.skip_reason,
                    "command": job.command,
                }
            )


def write_job_scripts(job_root: Path, jobs: list[ProposedJob], config: dict[str, Any], conda_env: str, gpus: list[int], imgsz: int) -> None:
    job_root.mkdir(parents=True, exist_ok=True)
    root = resolve_path(".")
    data_yaml = str(config["data_yaml"])
    project = str(config.get("project", "outputs/detectors/server_proposed_ablation"))
    training = config.get("training", {})
    run_eval = bool(training.get("run_eval", True))
    roc_auc = bool(training.get("roc_auc", True))

    scripts: dict[int, list[str]] = {}
    for gpu in gpus:
        scripts[gpu] = [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            f"cd {sh(root)}",
            "export CUDA_DEVICE_ORDER=PCI_BUS_ID",
            f"export CUDA_VISIBLE_DEVICES={sh(gpu)}",
            'export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"',
            f"export MPLCONFIGDIR={sh(root / '.cache/matplotlib')}",
            f"export YOLO_CONFIG_DIR={sh(root / '.cache/ultralytics')}",
            'mkdir -p "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR"',
        ]

    for job in jobs:
        if job.status != "queued" or job.gpu < 0:
            continue
        lines = scripts[job.gpu]
        lines.append(f'echo "START ablation={job.ablation} method={job.method} seed={job.seed} gpu={job.gpu} at $(date -Is)"')
        lines.append(f"{job.command} 2>&1 | tee {sh(job.log_file)}")
        if run_eval:
            lines.extend(
                [
                    f'run_dir=$(find {sh(project)} -maxdepth 1 -type d -name "*_{job.run_name}" -printf "%T@ %p\\n" | sort -nr | head -n 1 | cut -d" " -f2-)',
                    'if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then',
                    "  eval_args=("
                    f"eval --model \"$run_dir/ultralytics/weights/best.pt\" --data-yaml {sh(data_yaml)} "
                    f"--imgsz {sh(imgsz)} --device 0 --project {sh(project)} --name {sh('eval_' + job.run_name)} "
                    f"--method {sh(job.method)} --ablation {sh(job.ablation)} --base-model {sh(job.base_model)} "
                    f"--proposed-module {sh(job.proposed_module)} --implementation-status {sh(job.implementation_status)})",
                    "  if [[ " + sh("1" if roc_auc else "0") + ' == "1" ]]; then eval_args+=(--roc-auc); fi',
                    f"  conda run --no-capture-output -n {sh(conda_env)} python -m detectors.train_yolo \"${{eval_args[@]}}\" 2>&1 | tee -a {sh(job.log_file)}",
                    "fi",
                ]
            )
        lines.append(f'echo "DONE ablation={job.ablation} method={job.method} seed={job.seed} gpu={job.gpu} at $(date -Is)"')

    for gpu, lines in scripts.items():
        path = job_root / f"gpu{gpu}.sh"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        path.chmod(0o755)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate proposed detector ablation tmux job scripts.")
    parser.add_argument("--config", default="configs/experiments/proposed_detector_ablation.yaml")
    parser.add_argument("--job-root", required=True)
    parser.add_argument("--session", default="server-proposed-ablation")
    parser.add_argument("--conda-env", default="com3d-ace")
    parser.add_argument("--gpus", default="0,1")
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch", type=int, default=None)
    parser.add_argument("--imgsz", type=int, default=None)
    parser.add_argument("--seeds", default=None)
    parser.add_argument("--enable-planned", action="store_true")
    parser.add_argument("--manifest", default=None)
    parser.add_argument(
        "--completed-results-csv",
        action="append",
        default=[],
        help="Results CSV with completed proposed ablation rows to skip. Can be passed multiple times.",
    )
    parser.add_argument("--skip-completed", action="store_true", help="Skip completed ablation/base/seed keys.")
    args = parser.parse_args()

    config = read_yaml(args.config)
    gpus = [int(item.strip()) for item in args.gpus.split(",") if item.strip()]
    if not gpus:
        raise ValueError("--gpus must contain at least one GPU id")
    seeds = [int(item.strip()) for item in args.seeds.split(",") if item.strip()] if args.seeds else None
    completed_keys = (
        load_completed_keys([resolve_path(path) for path in args.completed_results_csv])
        if args.skip_completed
        else None
    )
    jobs = build_jobs(
        config,
        conda_env=args.conda_env,
        session=args.session,
        gpus=gpus,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        seeds=seeds,
        enable_planned=args.enable_planned,
        completed_keys=completed_keys,
    )
    training = config.get("training", {})
    selected_epochs = int(args.epochs if args.epochs is not None else training.get("epochs", 100))
    selected_batch = int(args.batch if args.batch is not None else training.get("batch", 8))
    selected_imgsz = int(args.imgsz if args.imgsz is not None else training.get("imgsz", 1280))
    write_command_csv(
        resolve_path(config.get("command_csv", "outputs/experiments/proposed_ablation_commands.csv")),
        jobs,
        args.session,
        str(config["data_yaml"]),
        selected_epochs,
        selected_batch,
        selected_imgsz,
    )
    job_root = resolve_path(args.job_root)
    write_job_scripts(job_root, jobs, config, args.conda_env, gpus, selected_imgsz)
    manifest = {
        "session": args.session,
        "job_root": str(job_root),
        "queued_count": sum(1 for job in jobs if job.status == "queued"),
        "skipped_count": sum(1 for job in jobs if job.status != "queued"),
        "skipped_completed_count": sum(1 for job in jobs if job.status == "skipped_completed"),
        "jobs": [job.__dict__ | {"log_file": str(job.log_file)} for job in jobs],
    }
    manifest_path = resolve_path(args.manifest) if args.manifest else job_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "manifest": str(manifest_path),
                "queued_count": manifest["queued_count"],
                "skipped_count": manifest["skipped_count"],
                "skipped_completed_count": manifest["skipped_completed_count"],
            }
        )
    )


if __name__ == "__main__":
    main()
