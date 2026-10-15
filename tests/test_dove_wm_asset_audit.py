from __future__ import annotations

import json
from pathlib import Path

from dove_wm.asset_audit import audit_assets, write_audit


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_audit_identifies_materialized_detector_pilot(tmp_path: Path) -> None:
    capture_root = tmp_path / "captures"
    evidence_root = tmp_path / "evidence"
    session = capture_root / "session_a"
    image_dir = session / "real_cesium_capture"
    image_dir.mkdir(parents=True)

    views = []
    summary_frames = []
    for action in ("a01", "a02"):
        frame_id = f"scene_h001_{action}"
        image_id = f"{frame_id}_rgb"
        (image_dir / f"{image_id}.png").write_bytes(b"rgb")
        (image_dir / f"{frame_id}_depth.npy").write_bytes(b"depth")
        views.append(
            {
                "scene_id": "scene_001",
                "frame_id": frame_id,
                "image_id": image_id,
                "uav_id": "uav_03",
                "altitude_m": 100.0,
                "metadata": {
                    "hypothesis_id": "H001",
                    "scenario_id": "scene_001",
                    "class_name": "car",
                },
            }
        )
        summary_frames.append(
            {
                "frame_id": frame_id,
                "image_id": image_id,
                "rgb_path": f"real_cesium_capture/{image_id}.png",
                "depth_npy_path": f"real_cesium_capture/{frame_id}_depth.npy",
            }
        )

    _write_json(session / "capture_plan.json", {"views": views})
    _write_json(
        session / "real_cesium_capture_summary.json",
        {"status": "complete", "frames": summary_frames},
    )
    evidence_path = evidence_root / "detector_run" / "evidence_tokens.jsonl"
    evidence_path.parent.mkdir(parents=True)
    evidence_path.write_text(
        "\n".join(
            json.dumps(
                {
                    "image_id": view["image_id"],
                    "confidence": 0.8,
                    "metadata": {
                        "frame_id": view["frame_id"],
                        "class_name": "car",
                    },
                }
            )
            for view in views
        )
        + "\n",
        encoding="utf-8",
    )

    audit = audit_assets(capture_root, evidence_root)

    assert audit["summary"]["planned_actions"] == 2
    assert audit["summary"]["complete_multi_action_groups"] == 1
    assert audit["summary"]["detector_outcome_pilot_groups"] == 1
    assert audit["summary"]["ground_truth_outcome_labeled_groups"] == 0
    assert audit["summary"]["readiness"]["detector_output_pilot"] is True
    assert audit["summary"]["readiness"]["supervised_world_model_training"] is False

    output_dir = tmp_path / "report"
    written = write_audit(audit, output_dir)
    assert len(written) == 5
    assert (output_dir / "summary.json").is_file()
    assert (output_dir / "action_groups.csv").is_file()


def test_audit_does_not_mark_incomplete_group_ready(tmp_path: Path) -> None:
    session = tmp_path / "captures" / "session_b"
    _write_json(
        session / "capture_plan.json",
        {
            "views": [
                {
                    "scene_id": "scene_002",
                    "frame_id": "only_action",
                    "image_id": "only_action_rgb",
                    "metadata": {
                        "hypothesis_id": "H002",
                        "scenario_id": "scene_002",
                        "class_name": "pedestrian",
                    },
                }
            ]
        },
    )

    audit = audit_assets(tmp_path / "captures")

    assert audit["summary"]["multi_action_hypothesis_groups"] == 0
    assert audit["summary"]["complete_multi_action_groups"] == 0
    assert audit["summary"]["readiness"]["counterfactual_tuple_materialization"] is False
