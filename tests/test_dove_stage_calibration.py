import unittest

import numpy as np

from scripts.evaluate_dove_proxy_gt import _box_inside_image, _same_outcome
from scripts.evaluate_dove_visual_world_models import (
    _conditional_visual_features,
    leave_one_scene_out_predictions,
)
from simulation.isaac.build_marinecity_stage import _focal_length_mm
from simulation.isaac.capture_marinecity_proxy import _scene_variant_transform


class DoveStageCalibrationTests(unittest.TestCase):
    def test_focal_pixels_are_converted_with_sensor_aperture(self) -> None:
        focal_mm = _focal_length_mm(780.0, 1280, 20.955)
        self.assertAlmostEqual(focal_mm, 12.769453125)
        recovered_px = focal_mm * 1280 / 20.955
        self.assertAlmostEqual(recovered_px, 780.0)

    def test_invalid_calibration_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            _focal_length_mm(0.0, 1280, 20.955)

    def test_box_coordinate_audit_uses_saved_image_extent(self) -> None:
        self.assertTrue(_box_inside_image([0.0, 0.0, 1280.0, 720.0], 1280, 720))
        self.assertFalse(_box_inside_image([-1.0, 0.0, 10.0, 10.0], 1280, 720))
        self.assertFalse(_box_inside_image([0.0, 0.0, 1281.0, 720.0], 1280, 720))

    def test_oracle_outcome_ties_ignore_deterministic_view_tiebreak(self) -> None:
        left = {"recall_at_iou50": 0.0, "f1_at_iou50": 0.0}
        right = {"recall_at_iou50": 0.0, "f1_at_iou50": 0.0}
        self.assertTrue(_same_outcome(left, right))

    def test_visual_terms_are_conditioned_on_candidate_action(self) -> None:
        action = np.asarray([1.0, 0.0])
        visual = np.asarray([0.25, 0.75])
        left = _conditional_visual_features(action, visual, np.asarray([1.0, 0.0]))
        right = _conditional_visual_features(action, visual, np.asarray([0.0, 1.0]))
        self.assertFalse(np.array_equal(left, right))

    def test_each_world_model_prediction_is_out_of_scene(self) -> None:
        rows = []
        for scene in range(3):
            for index, uav_id in enumerate(("uav_01", "uav_02")):
                rows.append(
                    {
                        "scene_variant": scene,
                        "uav_id": uav_id,
                        "candidate_x_m": float(index),
                        "candidate_y_m": 0.0,
                        "candidate_z_m": 10.0 + index,
                        "candidate_pitch_deg": -90.0,
                        "candidate_yaw_deg": 0.0,
                        "range_to_origin_m": 10.0 + index,
                        "movement_from_current_m": float(index),
                        "current_visual_00": float(scene),
                        "recall_at_iou50": float(scene == 2 and index == 1),
                        "f1_at_iou50": 0.0,
                    }
                )
        predictions = leave_one_scene_out_predictions(
            rows,
            ["uav_01", "uav_02"],
            ["current_visual_00"],
            alpha=1.0,
            visual_pca_components=1,
        )
        self.assertEqual(len(predictions), len(rows))
        self.assertTrue(
            all(
                int(row["scene_variant"]) == int(row["held_out_scene_variant"])
                for row in predictions
            )
        )

    def test_balanced_scene_variants_move_in_both_axes(self) -> None:
        transforms = [_scene_variant_transform(index, "balanced") for index in range(12)]
        self.assertGreater(len({value[0] for value in transforms}), 8)
        self.assertGreater(len({value[1] for value in transforms}), 8)
        self.assertGreater(len({value[2] for value in transforms}), 8)
        self.assertEqual(_scene_variant_transform(0, "balanced"), (0.0, 0.0, 0.0))

    def test_legacy_scene_variant_formula_is_preserved(self) -> None:
        self.assertEqual(_scene_variant_transform(1, "legacy"), (2.0, 1.0, -5.0))


if __name__ == "__main__":
    unittest.main()
