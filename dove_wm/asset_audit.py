"""Audit existing MarineCity captures for a DOVE-WM counterfactual pilot.

The audit deliberately separates materialized action outcomes from labels. RGB,
depth, poses, and detector predictions can support a pipeline smoke test, but
detector predictions are not ground-truth utility labels for a world model.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def _normalise_label(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def _evidence_index(evidence_root: Path | None) -> dict[str, Any]:
    by_image: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_frame: dict[str, list[dict[str, Any]]] = defaultdict(list)
    evidence_files: list[str] = []
    invalid_rows: list[dict[str, Any]] = []

    if evidence_root is None or not evidence_root.exists():
        return {
            "by_image": by_image,
            "by_frame": by_frame,
            "files": evidence_files,
            "invalid_rows": invalid_rows,
        }

    for path in sorted(evidence_root.rglob("evidence_tokens.jsonl")):
        evidence_files.append(str(path))
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    token = json.loads(line)
                except json.JSONDecodeError as exc:
                    invalid_rows.append(
                        {
                            "path": str(path),
                            "line": line_number,
                            "error": str(exc),
                        }
                    )
                    continue
                if not isinstance(token, dict):
                    invalid_rows.append(
                        {
                            "path": str(path),
                            "line": line_number,
                            "error": "row is not a JSON object",
                        }
                    )
                    continue

                metadata = token.get("metadata")
                if not isinstance(metadata, dict):
                    metadata = {}
                image_id = str(token.get("image_id") or metadata.get("image_id") or "")
                frame_id = str(metadata.get("frame_id") or "")
                class_name = metadata.get("class_name")
                if class_name is None:
                    class_name = token.get("class_name", token.get("class_id"))
                record = {
                    "source": str(path),
                    "image_id": image_id,
                    "frame_id": frame_id,
                    "class_name": _normalise_label(class_name),
                    "confidence": token.get("confidence"),
                    "object_id": token.get("object_id"),
                }
                if image_id:
                    by_image[image_id].append(record)
                if frame_id:
                    by_frame[frame_id].append(record)

    return {
        "by_image": by_image,
        "by_frame": by_frame,
        "files": evidence_files,
        "invalid_rows": invalid_rows,
    }


def _resolve_capture_path(session_dir: Path, value: Any, fallback: Path) -> Path:
    if value:
        path = Path(str(value))
        if not path.is_absolute():
            return session_dir / path
        if path.exists():
            return path
    return fallback


def _write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    materialized = list(rows)
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in materialized:
        for key in row:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not fieldnames:
            return
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(materialized)


def audit_assets(
    capture_root: str | Path,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    """Return a factual inventory of candidate actions and materialized outcomes."""

    capture_root = Path(capture_root).expanduser().resolve()
    if not capture_root.exists():
        raise FileNotFoundError(f"Capture root does not exist: {capture_root}")
    resolved_evidence_root = (
        Path(evidence_root).expanduser().resolve() if evidence_root is not None else None
    )
    evidence = _evidence_index(resolved_evidence_root)

    actions: list[dict[str, Any]] = []
    sessions: list[dict[str, Any]] = []
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)

    for plan_path in sorted(capture_root.rglob("capture_plan.json")):
        session_dir = plan_path.parent
        plan = _read_json(plan_path)
        views = plan.get("views")
        if not isinstance(views, list):
            views = []

        summary_path = session_dir / "real_cesium_capture_summary.json"
        capture_summary = _read_json(summary_path) if summary_path.exists() else {}
        summary_frames = capture_summary.get("frames")
        if not isinstance(summary_frames, list):
            summary_frames = []
        frames_by_id = {
            str(frame.get("frame_id")): frame
            for frame in summary_frames
            if isinstance(frame, dict) and frame.get("frame_id")
        }
        frames_by_image = {
            str(frame.get("image_id")): frame
            for frame in summary_frames
            if isinstance(frame, dict) and frame.get("image_id")
        }

        session_actions: list[dict[str, Any]] = []
        for view in views:
            if not isinstance(view, dict):
                continue
            frame_id = str(view.get("frame_id") or "")
            image_id = str(view.get("image_id") or (f"{frame_id}_rgb" if frame_id else ""))
            frame = frames_by_id.get(frame_id) or frames_by_image.get(image_id) or {}
            metadata = view.get("metadata")
            if not isinstance(metadata, dict):
                metadata = {}

            hypothesis_id = str(
                metadata.get("hypothesis_id") or frame.get("hypothesis_id") or ""
            )
            scenario_id = str(
                metadata.get("scenario_id")
                or frame.get("scenario_id")
                or view.get("scene_id")
                or session_dir.name
            )
            target_class = _normalise_label(
                metadata.get("class_name")
                or metadata.get("target_class")
                or frame.get("class_name")
            )
            rgb_path = _resolve_capture_path(
                session_dir,
                frame.get("rgb_path"),
                session_dir / "real_cesium_capture" / f"{image_id}.png",
            )
            depth_path = _resolve_capture_path(
                session_dir,
                frame.get("depth_npy_path"),
                session_dir / "real_cesium_capture" / f"{frame_id}_depth.npy",
            )

            tokens = list(evidence["by_image"].get(image_id, []))
            if not tokens and frame_id:
                tokens = list(evidence["by_frame"].get(frame_id, []))
            token_classes = sorted({token["class_name"] for token in tokens if token["class_name"]})
            evidence_sources = sorted({token["source"] for token in tokens})
            target_class_hits = sum(
                1 for token in tokens if target_class and token["class_name"] == target_class
            )

            row = {
                "session": session_dir.name,
                "session_path": str(session_dir),
                "scenario_id": scenario_id,
                "hypothesis_id": hypothesis_id,
                "frame_id": frame_id,
                "image_id": image_id,
                "uav_id": str(view.get("uav_id") or frame.get("uav_id") or ""),
                "target_class": target_class,
                "altitude_m": view.get("altitude_m"),
                "before_ambiguity": metadata.get(
                    "before_ambiguity", frame.get("before_ambiguity")
                ),
                "rgb_path": str(rgb_path),
                "rgb_exists": rgb_path.is_file(),
                "depth_path": str(depth_path),
                "depth_exists": depth_path.is_file(),
                "capture_summary_present": summary_path.is_file(),
                "detector_evidence_present": bool(tokens),
                "detector_token_count": len(tokens),
                "detector_source_count": len(evidence_sources),
                "detector_classes": "|".join(token_classes),
                "target_class_hit_count": target_class_hits,
                "target_class_hit": target_class_hits > 0,
                "ground_truth_outcome_label_present": False,
            }
            actions.append(row)
            session_actions.append(row)
            if hypothesis_id:
                groups[(session_dir.name, scenario_id, hypothesis_id)].append(row)

        session_group_keys = {
            (row["session"], row["scenario_id"], row["hypothesis_id"])
            for row in session_actions
            if row["hypothesis_id"]
        }
        sessions.append(
            {
                "session": session_dir.name,
                "session_path": str(session_dir),
                "capture_status": str(capture_summary.get("status") or "missing_summary"),
                "planned_action_count": len(session_actions),
                "rgb_action_count": sum(bool(row["rgb_exists"]) for row in session_actions),
                "depth_action_count": sum(bool(row["depth_exists"]) for row in session_actions),
                "detector_covered_action_count": sum(
                    bool(row["detector_evidence_present"]) for row in session_actions
                ),
                "hypothesis_count": len(session_group_keys),
            }
        )

    group_rows: list[dict[str, Any]] = []
    for (session, scenario_id, hypothesis_id), group_actions in sorted(groups.items()):
        candidate_count = len(group_actions)
        complete_materialization = (
            candidate_count >= 2
            and all(row["rgb_exists"] for row in group_actions)
            and all(row["depth_exists"] for row in group_actions)
        )
        detector_covered = complete_materialization and all(
            row["detector_evidence_present"] for row in group_actions
        )
        target_classes = sorted({row["target_class"] for row in group_actions if row["target_class"]})
        group_rows.append(
            {
                "session": session,
                "scenario_id": scenario_id,
                "hypothesis_id": hypothesis_id,
                "target_classes": "|".join(target_classes),
                "candidate_action_count": candidate_count,
                "rgb_action_count": sum(bool(row["rgb_exists"]) for row in group_actions),
                "depth_action_count": sum(bool(row["depth_exists"]) for row in group_actions),
                "detector_covered_action_count": sum(
                    bool(row["detector_evidence_present"]) for row in group_actions
                ),
                "target_class_hit_action_count": sum(
                    bool(row["target_class_hit"]) for row in group_actions
                ),
                "complete_multi_action_materialization": complete_materialization,
                "detector_outcome_pilot_ready": detector_covered,
                "ground_truth_outcome_label_present": False,
                "frame_ids": "|".join(row["frame_id"] for row in group_actions),
            }
        )

    multi_action_groups = [row for row in group_rows if row["candidate_action_count"] >= 2]
    complete_groups = [
        row for row in multi_action_groups if row["complete_multi_action_materialization"]
    ]
    detector_ready_groups = [
        row for row in multi_action_groups if row["detector_outcome_pilot_ready"]
    ]
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "capture_root": str(capture_root),
        "evidence_root": str(resolved_evidence_root) if resolved_evidence_root else None,
        "capture_plan_sessions": len(sessions),
        "planned_actions": len(actions),
        "captured_rgb_actions": sum(bool(row["rgb_exists"]) for row in actions),
        "captured_depth_actions": sum(bool(row["depth_exists"]) for row in actions),
        "detector_covered_actions": sum(
            bool(row["detector_evidence_present"]) for row in actions
        ),
        "hypothesis_groups": len(group_rows),
        "multi_action_hypothesis_groups": len(multi_action_groups),
        "complete_multi_action_groups": len(complete_groups),
        "detector_outcome_pilot_groups": len(detector_ready_groups),
        "ground_truth_outcome_labeled_groups": 0,
        "evidence_files": evidence["files"],
        "invalid_evidence_rows": evidence["invalid_rows"],
        "readiness": {
            "counterfactual_tuple_materialization": bool(complete_groups),
            "detector_output_pilot": bool(detector_ready_groups),
            "supervised_world_model_training": False,
            "counterfactual_benchmark_claim": False,
        },
        "limitations": [
            "Detector evidence is a prediction artifact, not a ground-truth outcome label.",
            "Multiple evidence files may contain repeated detector runs at different thresholds.",
            "No split audit or scene-independent generalization evidence is established here.",
            "The audit validates assets and joins only; it reports no DOVE-WM accuracy claim.",
        ],
    }
    return {
        "summary": summary,
        "sessions": sessions,
        "actions": actions,
        "action_groups": group_rows,
    }


def write_audit(audit: dict[str, Any], output_dir: str | Path) -> list[Path]:
    """Write the audit as JSON, CSV tables, and a short human-readable note."""

    output_dir = Path(output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "summary": output_dir / "summary.json",
        "sessions": output_dir / "sessions.csv",
        "actions": output_dir / "actions.csv",
        "action_groups": output_dir / "action_groups.csv",
        "readme": output_dir / "README.md",
    }
    with paths["summary"].open("w", encoding="utf-8") as handle:
        json.dump(audit["summary"], handle, indent=2, sort_keys=True)
        handle.write("\n")
    _write_csv(paths["sessions"], audit["sessions"])
    _write_csv(paths["actions"], audit["actions"])
    _write_csv(paths["action_groups"], audit["action_groups"])

    summary = audit["summary"]
    readiness = summary["readiness"]
    lines = [
        "# DOVE-WM Asset Preflight",
        "",
        f"- Capture-plan sessions: {summary['capture_plan_sessions']}",
        f"- Planned actions: {summary['planned_actions']}",
        f"- Complete multi-action groups: {summary['complete_multi_action_groups']}",
        f"- Detector-output pilot groups: {summary['detector_outcome_pilot_groups']}",
        f"- Ground-truth outcome-labeled groups: {summary['ground_truth_outcome_labeled_groups']}",
        "",
        "## Readiness",
        "",
        f"- Counterfactual tuple materialization: {readiness['counterfactual_tuple_materialization']}",
        f"- Detector-output pilot: {readiness['detector_output_pilot']}",
        f"- Supervised world-model training: {readiness['supervised_world_model_training']}",
        f"- Counterfactual benchmark claim: {readiness['counterfactual_benchmark_claim']}",
        "",
        "This inventory does not convert detector predictions into ground truth and does not",
        "constitute an empirical DOVE-WM result.",
    ]
    paths["readme"].write_text("\n".join(lines) + "\n", encoding="utf-8")
    return list(paths.values())
