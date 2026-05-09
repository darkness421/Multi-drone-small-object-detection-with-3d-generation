"""Smoke tests for the CoM3D-ACE research scaffold."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from alignment.costs import pairwise_evidence_cost, reliability_weight
from ambiguity.ambiguity_scorer import score_hypothesis
from ambiguity import diagnose_ambiguity
from data.converters.coco_to_yolo import convert_coco_to_yolo
from evidence import EvidenceToken, extract_crop, load_tokens_jsonl, save_tokens_jsonl
from evidence.lifting import lift_bbox_center_to_world
from evidence.uncertainty import class_entropy, max_softmax_confidence
from graph import build_evidence_graph
from graph.graph_builder import build_object_hypotheses
from policy import select_action
from policy.policy_simulator import simulate_policy
from evaluation.policy_compare import empty_reobservation_table
from evaluation.detector_compare import empty_detector_table
from evaluation.detector_metrics_collector import collect_detector_metrics
from evaluation.association_eval import evaluate_association, infer_gt_from_tokens
from evaluation.system_level_runner import build_system_rows
from evaluation.system_compare import empty_system_table
from evaluation.vlm_compare import empty_vlm_table
from runtime.config import load_config
from runtime.outputs import prepare_run_dir
from scripts.check_dataset_readiness import inspect_dataset
from scripts.check_training_readiness import inspect_data_yaml
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
            gt_by_obs, gt_centers = infer_gt_from_tokens(outputs["tokens"])
            hypotheses = __import__("json").loads(outputs["hypotheses"].read_text(encoding="utf-8"))
            metrics = evaluate_association(hypotheses, gt_by_obs, gt_centers)
            self.assertIn("association_f1", metrics)
            self.assertIn("false_merge_rate", metrics)
            system_rows = build_system_rows(metrics, {"com3d-policy": {"final_acc": "0.6", "ambiguity_resolution_rate": "0.2", "reobs_count": "1"}})
            self.assertEqual(system_rows[-1]["Method"], "Full CoM3D-ACE")

            rows = write_plan(tmp_path / "detector_plan.csv", "configs/detector/visdrone_yolo_data.yaml")
            self.assertGreaterEqual(len(rows), 1)
            self.assertIn(rows[0]["status"], {"ready", "skipped"})

            metrics_dir = tmp_path / "metrics"
            metrics_dir.mkdir()
            (metrics_dir / "yolo.json").write_text(
                __import__("json").dumps(
                    {
                        "Method": "YOLOv8n",
                        "Dataset": "VisDrone2019-DET",
                        "AP": 0.1,
                        "AP50": 0.2,
                        "FPS": 120,
                    }
                ),
                encoding="utf-8",
            )
            metric_rows = collect_detector_metrics(metrics_dir, ["VisDrone2019-DET"])
            self.assertEqual(metric_rows[0]["AP"], 0.1)

    def test_coco_to_yolo_converter(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            image_path = tmp_path / "image_0001.jpg"
            image_path.write_text("placeholder", encoding="utf-8")
            coco_path = tmp_path / "sample_coco.json"
            coco_path.write_text(
                __import__("json").dumps(
                    {
                        "images": [{"id": 1, "file_name": str(image_path), "width": 100, "height": 50}],
                        "annotations": [{"id": 1, "image_id": 1, "category_id": 1, "bbox": [10, 5, 20, 10]}],
                        "categories": [{"id": 1, "name": "car"}],
                    }
                ),
                encoding="utf-8",
            )
            data_yaml = convert_coco_to_yolo(coco_path, tmp_path / "yolo")
            self.assertTrue(data_yaml.exists())
            label_files = list((tmp_path / "yolo" / "labels").rglob("*.txt"))
            self.assertEqual(len(label_files), 1)

    def test_dataset_readiness_inspection(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            images = tmp_path / "images"
            annotations = tmp_path / "annotations"
            images.mkdir()
            annotations.mkdir()
            (images / "frame_0001.jpg").write_text("placeholder", encoding="utf-8")
            (annotations / "frame_0001.txt").write_text("1,2,3,4", encoding="utf-8")
            row = inspect_dataset("visdrone", {"images": images, "annotations": annotations})
            self.assertTrue(row.ready)
            self.assertEqual(row.counts["images"], 1)
            self.assertEqual(row.counts["annotations"], 1)

    def test_training_readiness_detects_placeholder_images(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            yolo_root = tmp_path / "yolo"
            for split in ("train", "val"):
                (yolo_root / "images" / split).mkdir(parents=True)
                (yolo_root / "labels" / split).mkdir(parents=True)
                (yolo_root / "images" / split / "frame_0001.jpg").write_text(
                    "image_placeholder=C:/raw/frame_0001.jpg\n",
                    encoding="utf-8",
                )
                (yolo_root / "labels" / split / "frame_0001.txt").write_text(
                    "0 0.5 0.5 0.1 0.1\n",
                    encoding="utf-8",
                )
            data_yaml = tmp_path / "data.yaml"
            data_yaml.write_text(
                "\n".join(
                    [
                        f"path: {yolo_root.as_posix()}",
                        "train: images/train",
                        "val: images/val",
                        "names:",
                        "  0: car",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            readiness = inspect_data_yaml(data_yaml)
            self.assertFalse(readiness.ready)
            self.assertGreater(readiness.splits[0].placeholder_count, 0)


if __name__ == "__main__":
    unittest.main()
