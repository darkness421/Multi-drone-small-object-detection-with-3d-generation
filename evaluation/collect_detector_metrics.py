"""Collect Ultralytics detector run metrics into one server baseline CSV."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

from runtime.config import resolve_path

try:
    import yaml
except ImportError:  # pragma: no cover - guarded by runtime error only when needed.
    yaml = None


METRIC_COLUMNS = [
    "method",
    "model",
    "base_model",
    "ablation",
    "proposed_module",
    "is_proposed",
    "implementation_status",
    "detector_family",
    "architecture_group",
    "model_version",
    "yolo_version",
    "is_yolo",
    "model_scale",
    "name_size_tag",
    "param_size_group",
    "size_group",
    "dataset",
    "protocol_data_yaml",
    "protocol_imgsz",
    "protocol_epochs",
    "protocol_batch",
    "protocol_deterministic",
    "protocol_match",
    "protocol_mismatch_reason",
    "seed",
    "status",
    "run_dir",
    "results_csv",
    "best_weight",
    "best_epoch",
    "best_AP",
    "best_AP50",
    "best_AP75",
    "best_APsmall",
    "best_precision",
    "best_recall",
    "best_F1",
    "final_epoch",
    "final_AP",
    "final_AP50",
    "final_AP75",
    "final_APsmall",
    "final_precision",
    "final_recall",
    "final_F1",
    "ROC-AUC",
    "latency_ms",
    "FPS",
    "Params",
    "GFLOPs",
]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def first_metric(row: dict[str, str], names: list[str]) -> float | None:
    stripped = {key.strip(): value for key, value in row.items()}
    for name in names:
        value = as_float(stripped.get(name))
        if value is not None:
            return value
    return None


def f1(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None or precision + recall == 0:
        return None
    return 2.0 * precision * recall / (precision + recall)


def metric_payload(row: dict[str, str], prefix: str) -> dict[str, float | None]:
    precision = first_metric(row, ["metrics/precision(B)", "metrics/precision"])
    recall = first_metric(row, ["metrics/recall(B)", "metrics/recall"])
    return {
        f"{prefix}_epoch": first_metric(row, ["epoch"]),
        f"{prefix}_AP": first_metric(row, ["metrics/mAP50-95(B)", "metrics/mAP50-95"]),
        f"{prefix}_AP50": first_metric(row, ["metrics/mAP50(B)", "metrics/mAP50"]),
        f"{prefix}_AP75": first_metric(row, ["metrics/mAP75(B)", "metrics/mAP75"]),
        f"{prefix}_APsmall": first_metric(row, ["metrics/mAP50-95(S)", "metrics/APsmall", "metrics/APs"]),
        f"{prefix}_precision": precision,
        f"{prefix}_recall": recall,
        f"{prefix}_F1": f1(precision, recall),
    }


def best_row(rows: list[dict[str, str]]) -> dict[str, str]:
    return max(rows, key=lambda row: first_metric(row, ["metrics/mAP50-95(B)", "metrics/mAP50-95"]) or -1.0)


def infer_seed(run_dir: Path, summary: dict[str, Any]) -> str:
    if summary.get("seed") is not None:
        return str(summary["seed"])
    match = re.search(r"seed(\d+)", run_dir.name)
    return match.group(1) if match else ""


def infer_method(model: str) -> str:
    stem = Path(model).stem
    yolo_match = re.match(r"^yolo(?:v)?(?P<version>\d+)(?P<suffix>[nsmxl](?:u|6)?)?$", stem.lower())
    if yolo_match:
        suffix = yolo_match.group("suffix") or ""
        return f"YOLOv{yolo_match.group('version')}{suffix}"
    if stem.lower().startswith(("rtdetr", "rt-detr")):
        scale = stem.split("-")[-1].upper() if "-" in stem else stem.replace("rtdetr", "").upper()
        return f"RT-DETR-{scale}" if scale else "RT-DETR"
    if stem.lower() in {"lrds-yolo", "lrdsyolo", "lrds_yolo"}:
        return "LRDS-YOLO"
    return stem


def scale_from_suffix(suffix: str) -> str:
    if suffix in {"n", "nu", "n6"}:
        return "nano"
    if suffix in {"s", "su", "s6"}:
        return "small"
    if suffix in {"m", "mu", "m6"}:
        return "medium"
    if suffix in {"l", "lu", "l6"}:
        return "large"
    if suffix in {"x", "xu", "x6"}:
        return "xlarge"
    return "unknown"


def infer_model_metadata(model: str) -> dict[str, str]:
    """Split model identity into family, version, and size fields.

    The checkpoint suffix is useful, but not enough for fair comparison.
    YOLOv7, RT-DETR-R18, and other non-YOLO checkpoints do not map cleanly to
    nano/small/medium suffixes, so measured parameter bins are kept separately.
    """

    stem = Path(model).stem.lower()
    metadata = {
        "detector_family": "Other",
        "architecture_group": "non_yolo",
        "model_version": "unknown",
        "yolo_version": "",
        "is_yolo": "false",
        "model_scale": "unknown",
    }

    yolo_match = re.match(r"^yolo(?:v)?(?P<version>\d+)(?P<suffix>[nsmxl](?:u|6)?)?$", stem)
    if yolo_match:
        version = f"v{yolo_match.group('version')}"
        suffix = yolo_match.group("suffix") or ""
        metadata.update(
            {
                "detector_family": "YOLO",
                "architecture_group": "yolo",
                "model_version": version,
                "yolo_version": version,
                "is_yolo": "true",
                "model_scale": scale_from_suffix(suffix) if suffix else "base",
            }
        )
        return metadata

    if stem.startswith("rtdetr") or stem.startswith("rt-detr"):
        metadata.update(
            {
                "detector_family": "RT-DETR",
                "architecture_group": "non_yolo",
                "model_version": "RT-DETR",
                "model_scale": "unknown",
            }
        )
        if "r18" in stem:
            metadata["model_scale"] = "r18"
        elif stem.endswith("-l") or stem.endswith("_l") or stem.endswith("l"):
            metadata["model_scale"] = "large"
        elif stem.endswith("-x") or stem.endswith("_x") or stem.endswith("x"):
            metadata["model_scale"] = "xlarge"
        return metadata

    if stem in {"lrds-yolo", "lrdsyolo", "lrds_yolo"}:
        metadata.update(
            {
                "detector_family": "LRDS-YOLO",
                "architecture_group": "yolo",
                "model_version": "LRDS-YOLO",
                "yolo_version": "",
                "is_yolo": "true",
                "model_scale": "lightweight",
            }
        )
        return metadata

    if stem.startswith("dfine") or stem.startswith("d-fine"):
        metadata.update(
            {
                "detector_family": "D-FINE",
                "architecture_group": "non_yolo",
                "model_version": "D-FINE",
            }
        )
        return metadata

    if stem.startswith("detr"):
        metadata.update(
            {
                "detector_family": "DETR",
                "architecture_group": "non_yolo",
                "model_version": "DETR",
            }
        )
        return metadata

    if "r18" in stem:
        metadata["model_scale"] = "r18"
    return metadata


def infer_name_size_tag(model: str) -> str:
    return infer_model_metadata(model)["model_scale"]


def infer_param_size_group(params: int | None) -> str:
    if params is None:
        return "unknown"
    params_m = params / 1_000_000
    if params_m < 5:
        return "nano"
    if params_m < 15:
        return "small"
    if params_m < 35:
        return "medium"
    if params_m < 75:
        return "large"
    return "xlarge"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    if yaml is None:
        raise RuntimeError("PyYAML is required to read Ultralytics args.yaml files.")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def read_run_args(run_dir: Path) -> dict[str, Any]:
    return read_yaml(run_dir / "ultralytics" / "args.yaml")


def first_present(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return ""


def as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None or value == "":
        return None
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    return None


def as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return None


def path_matches(value: Any, expected: str | None) -> bool:
    if expected is None or expected == "":
        return True
    if value is None or value == "":
        return False
    left = Path(str(value))
    right = resolve_path(expected)
    if not left.is_absolute():
        left = resolve_path(left)
    try:
        return left.resolve() == right.resolve()
    except OSError:
        return str(left) == str(right)


def protocol_mismatches(row: dict[str, Any], criteria: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if criteria.get("data_yaml") and not path_matches(row.get("protocol_data_yaml"), criteria["data_yaml"]):
        reasons.append(f"data_yaml={row.get('protocol_data_yaml')}")
    for key, label in [("imgsz", "protocol_imgsz"), ("epochs", "protocol_epochs"), ("batch", "protocol_batch")]:
        expected = criteria.get(key)
        if expected is None:
            continue
        if as_int(row.get(label)) != int(expected):
            reasons.append(f"{key}={row.get(label)}")
    if criteria.get("deterministic") is not None:
        actual = as_bool(row.get("protocol_deterministic"))
        if actual is not bool(criteria["deterministic"]):
            reasons.append(f"deterministic={row.get('protocol_deterministic')}")
    return reasons


def apply_protocol_filter(
    rows: list[dict[str, Any]],
    criteria: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not any(value is not None and value != "" for value in criteria.values()):
        return rows, []

    kept: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for row in rows:
        reasons = protocol_mismatches(row, criteria)
        row["protocol_match"] = "false" if reasons else "true"
        row["protocol_mismatch_reason"] = "; ".join(reasons)
        if reasons:
            excluded.append(row)
        else:
            kept.append(row)
    return kept, excluded


def dedupe_rows(rows: list[dict[str, Any]], key_fields: list[str]) -> list[dict[str, Any]]:
    if not key_fields:
        return rows

    selected: dict[tuple[str, ...], tuple[int, dict[str, Any]]] = {}
    for index, row in enumerate(rows):
        key = tuple(str(row.get(field, "")) for field in key_fields)
        current = selected.get(key)
        if current is None:
            selected[key] = (index, row)
            continue
        _, current_row = current
        current_complete = current_row.get("status") == "completed"
        row_complete = row.get("status") == "completed"
        if row_complete and not current_complete:
            selected[key] = (index, row)
        elif row_complete == current_complete:
            selected[key] = (index, row)
    return [row for _, row in sorted(selected.values(), key=lambda item: item[0])]


def strip_timestamp(run_name: str) -> str:
    return re.sub(r"^\d{8}_\d{6}_", "", run_name)


def parse_complexity_from_log(path: Path) -> tuple[int | None, float | None]:
    if not path.exists():
        return None, None
    pattern = re.compile(r"summary(?!(?: \(fused\))):.*?([\d,]+) parameters.*?([\d.]+) GFLOPs", re.IGNORECASE)
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            match = pattern.search(line)
            if not match:
                continue
            params = int(match.group(1).replace(",", ""))
            gflops = float(match.group(2))
            return params, gflops
    except OSError:
        return None, None
    return None, None


def model_complexity(run_dir: Path) -> tuple[int | None, float | None]:
    run_name = strip_timestamp(run_dir.name)
    candidate_logs = [
        resolve_path("outputs/logs/server_baselines") / f"{run_name}.log",
        run_dir / "logs" / "train.log",
    ]
    for root_name in [
        "outputs/logs/server_baselines",
        "outputs/logs/server_fresh_baselines",
        "outputs/logs/server_proposed_ablation",
    ]:
        root = resolve_path(root_name)
        if root.exists():
            candidate_logs.extend(sorted(root.glob(f"**/{run_name}.log")))
    for path in candidate_logs:
        params, gflops = parse_complexity_from_log(path)
        if params is not None or gflops is not None:
            return params, gflops
    return None, None


def infer_dataset(train_summary: dict[str, Any], eval_summary: dict[str, Any], run_dir: Path, results_csv: Path) -> str:
    for summary in (train_summary, eval_summary):
        dataset = summary.get("dataset")
        if dataset:
            return str(dataset)
    haystack = " ".join(
        [
            str(train_summary.get("data", "")),
            str(eval_summary.get("data", "")),
            str(run_dir),
            str(results_csv),
        ]
    ).lower()
    if "uavdt" in haystack:
        return "UAVDT"
    if "visdrone" in haystack:
        return "VisDrone2019-DET"
    if "marine" in haystack or "com3d" in haystack:
        return "CoM3D-MarineCity"
    return "unknown"


def collect_one(results_csv: Path) -> dict[str, Any]:
    run_dir = results_csv.parent.parent if results_csv.parent.name == "ultralytics" else results_csv.parent
    rows = read_csv_rows(results_csv)
    final = rows[-1] if rows else {}
    best = best_row(rows) if rows else {}
    train_summary = read_json(run_dir / "metrics" / "train_summary.json")
    eval_summary = read_json(run_dir / "metrics" / "eval_summary.json")
    run_args = read_run_args(run_dir)
    fallback_model = strip_timestamp(run_dir.name.split("_visdrone")[0])
    if "." not in Path(fallback_model).name and infer_model_metadata(fallback_model)["detector_family"] != "Other":
        fallback_model = f"{fallback_model}.pt"
    model = str(train_summary.get("requested_model") or train_summary.get("model") or fallback_model)
    best_weight = results_csv.parent / "weights" / "best.pt"
    train_summary_path = run_dir / "metrics" / "train_summary.json"
    params, gflops = model_complexity(run_dir)
    metadata = infer_model_metadata(model)
    name_size_tag = metadata["model_scale"]
    param_size_group = infer_param_size_group(params)
    payload: dict[str, Any] = {
        "method": train_summary.get("method") or infer_method(model),
        "model": model,
        "base_model": train_summary.get("base_model") or model,
        "ablation": train_summary.get("ablation") or "",
        "proposed_module": train_summary.get("proposed_module") or "",
        "is_proposed": "true"
        if any(
            token in str(train_summary.get(key, "")).lower()
            for key in ("method", "ablation", "proposed_module")
            for token in ("proposed", "wavelet", "deformable", "tiling", "ours", "com3d", "ace")
        )
        else "false",
        "implementation_status": train_summary.get("implementation_status") or "",
        **metadata,
        "name_size_tag": name_size_tag,
        "param_size_group": param_size_group,
        "size_group": param_size_group if param_size_group != "unknown" else name_size_tag,
        "dataset": infer_dataset(train_summary, eval_summary, run_dir, results_csv),
        "protocol_data_yaml": first_present(train_summary.get("data"), run_args.get("data"), eval_summary.get("data")),
        "protocol_imgsz": first_present(train_summary.get("imgsz"), run_args.get("imgsz"), eval_summary.get("imgsz")),
        "protocol_epochs": first_present(train_summary.get("epochs"), run_args.get("epochs")),
        "protocol_batch": first_present(train_summary.get("batch"), run_args.get("batch")),
        "protocol_deterministic": first_present(train_summary.get("deterministic"), run_args.get("deterministic")),
        "protocol_match": "",
        "protocol_mismatch_reason": "",
        "seed": infer_seed(run_dir, train_summary),
        "status": "completed" if train_summary_path.exists() and best_weight.exists() else "incomplete",
        "run_dir": str(run_dir),
        "results_csv": str(results_csv),
        "best_weight": str(best_weight) if best_weight.exists() else "",
        "ROC-AUC": (eval_summary.get("metrics") or {}).get("ROC-AUC", (eval_summary.get("roc_auc") or {}).get("macro")),
        "Params": params,
        "GFLOPs": gflops,
    }
    payload.update(metric_payload(best, "best"))
    payload.update(metric_payload(final, "final"))
    return payload


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(METRIC_COLUMNS)
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def collect(detector_roots: list[str | Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for detector_root in detector_roots:
        root = resolve_path(detector_root)
        if not root.exists():
            continue
        for path in sorted(root.rglob("results.csv")):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            rows.append(collect_one(path))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect server detector baseline metrics.")
    parser.add_argument(
        "--detector-root",
        action="append",
        dest="detector_roots",
        help="Detector run root. May be passed more than once.",
    )
    parser.add_argument("--out", default="outputs/experiments/server_baseline_results.csv")
    parser.add_argument("--require-data-yaml", default=None)
    parser.add_argument("--require-imgsz", type=int, default=None)
    parser.add_argument("--require-epochs", type=int, default=None)
    parser.add_argument("--require-batch", type=int, default=None)
    parser.add_argument("--require-deterministic", default=None, choices=["true", "false"])
    parser.add_argument("--excluded-out", default=None, help="Optional CSV for rows discarded by protocol filtering.")
    parser.add_argument(
        "--dedupe-key",
        default="",
        help="Comma-separated fields used to keep one row per logical run, for example dataset,method,seed.",
    )
    args = parser.parse_args()

    detector_roots = args.detector_roots or ["outputs/detectors/server_baselines"]
    rows = collect(detector_roots)
    criteria = {
        "data_yaml": args.require_data_yaml,
        "imgsz": args.require_imgsz,
        "epochs": args.require_epochs,
        "batch": args.require_batch,
        "deterministic": as_bool(args.require_deterministic),
    }
    rows, excluded = apply_protocol_filter(rows, criteria)
    if args.dedupe_key:
        key_fields = [field.strip() for field in args.dedupe_key.split(",") if field.strip()]
        rows = dedupe_rows(rows, key_fields)
    out_path = resolve_path(args.out)
    write_csv(out_path, rows)
    print(f"Wrote {out_path} ({len(rows)} rows)")
    if args.excluded_out:
        excluded_path = resolve_path(args.excluded_out)
        write_csv(excluded_path, excluded)
        print(f"Wrote {excluded_path} ({len(excluded)} excluded rows)")


if __name__ == "__main__":
    main()
