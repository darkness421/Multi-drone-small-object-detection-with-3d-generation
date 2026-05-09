"""Smoke tests for the CoM3D-ACE research scaffold."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from alignment.costs import pairwise_evidence_cost, reliability_weight
from ambiguity.ambiguity_scorer import score_hypothesis
from ambiguity import diagnose_ambiguity
from evidence import EvidenceToken, extract_crop, load_tokens_jsonl, save_tokens_jsonl
from evidence.lifting import lift_bbox_center_to_world
from evidence.uncertainty import class_entropy, max_softmax_confidence
from graph import build_evidence_graph
from graph.graph_builder import build_object_hypotheses
from policy import select_action
from policy.policy_simulator import simulate_policy
from evaluation.policy_compare import empty_reobservation_table
from evaluation.detector_compare import empty_detector_table
from evaluation.system_compare import empty_system_table
from evaluation.vlm_compare import empty_vlm_table
from runtime.config import load_config
from runtime.outputs import prepare_run_dir
from scripts.run_core_pipeline import run_pipeline
from scripts.run_detector_baselines import write_plan
from simulation.isaac.export_rgb_depth_pose import build_dry_run_manifest
from vlm import build_sage_prompt, parse_sage_response


def make_token(token_id: str, uav_id: str, logits: list[float], center: list[float]) -> EvidenceToken:
    return EvidenceToken(
        token_id=token_id,
        image_id=f"{uav_id}_frame",
        uav_id=uav_id,
        timestamp=1.0,
        bbox_2d=[10.0, 20.0, 16.0, 12.0],
        class_logits=logits,
        confidence=max_softmax_confidence(logits),
        uncertainty=class_entropy(logits),
        crop_feature=[0.1, 0.2, 0.3],
        resolution_level="p3",
        camera_intrinsic=[[100.0, 0.0, 32.0], [0.0, 100.0, 32.0], [0.0, 0.0, 1.0]],
        camera_extrinsic=np.eye(4).tolist(),
        uav_pose=center,
        depth_value=10.0,
        metadata={"center_3d": center},
    )


class TestCom3DAceCore(unittest.TestCase):
    def test_uncertainty(self) -> None:
        logits = [4.0, 1.0, 0.0]
        self.assertGreater(max_softmax_confidence(logits), 0.8)
        self.assertLess(class_entropy(logits), 0.5)

    def test_lifting(self) -> None:
        depth = np.full((64, 64), 10.0)
        result = lift_bbox_center_to_world(
            [22.0, 22.0, 20.0, 20.0],
            depth,
            [[100.0, 0.0, 32.0], [0.0, 100.0, 32.0], [0.0, 0.0, 1.0]],
            np.eye(4).tolist(),
        )
        self.assertEqual(len(result["center_3d"]), 3)
        self.assertAlmostEqual(result["center_3d"][2], 10.0)

    def test_alignment_graph_policy_vlm(self) -> None:
        t1 = make_token("t1", "uav1", [3.0, 0.1], [0.0, 0.0, 10.0])
        t2 = make_token("t2", "uav2", [2.8, 0.2], [0.1, 0.0, 10.1])
        self.assertLess(pairwise_evidence_cost(t1, t2), 2.0)
        self.assertGreater(reliability_weight(t1), 0.0)

        graph = build_evidence_graph([t1, t2], association_threshold=2.0)
        self.assertEqual(len(graph.objects), 1)
        diagnosis = diagnose_ambiguity(graph.objects[0], cross_view_disagreement=0.1)
        self.assertIn(diagnosis.level, {"low", "medium", "high"})
        action = select_action(diagnosis)
        self.assertIn(action["action"], {"finalize", "VLM verify", "active re-observe"})

        prompt = build_sage_prompt(
            scene_summary="urban road",
            graph_summary=graph.to_dict(),
            ambiguity_reasons=diagnosis.reasons,
            candidate_classes=["van", "truck"],
        )
        self.assertIn("SAGE", prompt)
        parsed = parse_sage_response('{"decision":"verified","predicted_class":"van","confidence":0.8}')
        self.assertEqual(parsed["decision"], "verified")

    def test_reobservation_table_template(self) -> None:
        rows = empty_reobservation_table()
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0]["Method"], "No re-observation")
        self.assertEqual(rows[-1]["Method"], "CoM3D-ACE policy")

    def test_vlm_table_template(self) -> None:
        rows = empty_vlm_table()
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0]["Method"], "No VLM")
        self.assertEqual(rows[-1]["Method"], "SAGE-triggered VLM")

    def test_detector_and_system_table_templates(self) -> None:
        detector_rows = empty_detector_table(["VisDrone2019-DET"])
        self.assertEqual(detector_rows[0]["Method"], "YOLOv8n")
        self.assertEqual(detector_rows[-1]["Method"], "Ours AEG")

        system_rows = empty_system_table()
        self.assertEqual(system_rows[0]["Method"], "Single-view detector")
        self.assertEqual(system_rows[-1]["Method"], "Full CoM3D-ACE")

    def test_evidence_jsonl_and_fake_detection_crop(self) -> None:
        tokens = [
            make_token("fake_1", "uav1", [3.0, 0.1], [0.0, 0.0, 10.0]),
            make_token("fake_2", "uav2", [2.5, 0.2], [0.1, 0.0, 10.0]),
        ]
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            jsonl_path = tmp_path / "tokens.jsonl"
            save_tokens_jsonl(tokens, jsonl_path)
            loaded = load_tokens_jsonl(jsonl_path)
            self.assertEqual(len(loaded), 2)
            self.assertEqual(loaded[0].token_id, "fake_1")

            try:
                import cv2
            except ImportError:
                return
            image_path = tmp_path / "image.jpg"
            cv2.imwrite(str(image_path), np.full((48, 64, 3), 255, dtype=np.uint8))
            crop = extract_crop(image_path, [4, 5, 20, 10])
            self.assertEqual(crop.shape[0], 10)
            self.assertEqual(crop.shape[1], 20)

    def test_graph_ambiguity_policy_prototypes(self) -> None:
        tokens = [
            make_token("fake_1", "uav1", [2.0, 1.8], [0.0, 0.0, 10.0]),
            make_token("fake_2", "uav2", [1.9, 1.7], [0.2, 0.0, 10.0]),
        ]
        hypotheses = build_object_hypotheses(tokens, threshold=2.0)
        self.assertGreaterEqual(len(hypotheses), 1)
        scored = score_hypothesis(hypotheses[0].to_dict())
        self.assertIn("ambiguity_score", scored)
        rows = simulate_policy([hypothesis.to_dict() for hypothesis in hypotheses], [scored])
        self.assertEqual({row["method"] for row in rows}, {"no-reobserve", "random", "uncertainty-only", "information-gain-only", "com3d-policy"})

    def test_runtime_config_and_isaac_dry_manifest(self) -> None:
        config = load_config("configs/sim/isaac_export.yaml")
        self.assertEqual(config["name"], "com3d_uav_sim_export")
        manifest = build_dry_run_manifest(config)
        self.assertEqual(manifest["dataset"], "CoM3D-UAV-Sim")
        self.assertGreaterEqual(len(manifest["frames"]), 3)

        with TemporaryDirectory() as tmp:
            run_dir = prepare_run_dir("unit_test", output_root=tmp)
            self.assertTrue((run_dir / "logs").exists())
            self.assertTrue((run_dir / "metrics").exists())
            self.assertTrue((run_dir / "artifacts").exists())

    def test_windows_pipeline_entrypoints(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            outputs = run_pipeline(tmp_path / "tokens.jsonl", tmp_path / "core", make_dummy=True)
            self.assertTrue(outputs["hypotheses"].exists())
            self.assertTrue(outputs["ambiguity"].exists())
            self.assertTrue(outputs["policy"].exists())

            rows = write_plan(tmp_path / "detector_plan.csv", "configs/detector/visdrone_yolo_data.yaml")
            self.assertGreaterEqual(len(rows), 1)
            self.assertIn(rows[0]["status"], {"ready", "skipped"})


if __name__ == "__main__":
    unittest.main()
