from __future__ import annotations

import unittest

from regr import confidence
from regr.core import resolve_method, select_edges


def row(identity: int, x: float, y: float = 0.0, size: float = 10.0) -> dict:
    return {"id": identity, "x": x, "y": y, "w": size, "h": size}


class MotionConfidenceTest(unittest.TestCase):
    def test_actual_frame_intervals_drive_velocity(self):
        predictions = {
            0: [row(1, 0.0)],
            2: [row(1, 2.0)],
            4: [row(1, 4.0)],
            8: [row(2, 8.0)],
            10: [row(2, 10.0)],
            12: [row(2, 12.0)],
        }
        edge = {
            "earlier": 1,
            "later": 2,
            "gap": 4,
            "endpoint_center_distance_pixels": 4.0,
            "cosine_distance": 0.1,
        }
        confidence.add_candidate_motion_features([edge], predictions, 3, "object_scale")
        self.assertAlmostEqual(edge["motion_residual_pixels"], 0.0, places=8)
        self.assertGreater(edge["motion_confidence"], 0.6)

    def test_two_points_are_uninformative(self):
        predictions = {
            0: [row(1, 0.0)],
            1: [row(1, 1.0)],
            3: [row(2, 3.0)],
            4: [row(2, 4.0)],
        }
        edge = {
            "earlier": 1,
            "later": 2,
            "gap": 2,
            "endpoint_center_distance_pixels": 2.0,
            "cosine_distance": 0.1,
        }
        confidence.add_candidate_motion_features([edge], predictions, 5, "object_scale")
        self.assertEqual(edge["motion_estimate_count"], 0)
        self.assertEqual(edge["motion_confidence"], 0.0)

    def test_object_scale_normalization_is_distinct_from_endpoint(self):
        predictions = {
            0: [row(1, 0.0, size=20.0)],
            1: [row(1, 1.0, size=20.0)],
            2: [row(1, 2.0, size=20.0)],
            5: [row(2, 8.0, size=20.0)],
            6: [row(2, 9.0, size=20.0)],
            7: [row(2, 10.0, size=20.0)],
        }
        base = {
            "earlier": 1,
            "later": 2,
            "gap": 3,
            "endpoint_center_distance_pixels": 6.0,
            "cosine_distance": 0.1,
        }
        endpoint_edge = dict(base)
        scale_edge = dict(base)
        confidence.add_candidate_motion_features([endpoint_edge], predictions, 3, "endpoint")
        confidence.add_candidate_motion_features([scale_edge], predictions, 3, "object_scale")
        self.assertNotEqual(
            endpoint_edge["motion_normalized_residual"],
            scale_edge["motion_normalized_residual"],
        )


class AssignmentTest(unittest.TestCase):
    def test_unmatched_is_a_real_competitor(self):
        edges = [
            {"earlier": 1, "later": 2, "evidence_cost": 0.79},
        ]
        selected, _ = confidence.competition_assignment(
            edges,
            lambda edge: edge["evidence_cost"],
            unmatched_cost=0.80,
            minimum_margin=0.03,
        )
        self.assertEqual(selected, [])

    def test_filter_then_reassign_can_recover_alternative(self):
        edges = [
            {"earlier": 1, "later": 10, "evidence_cost": 0.10},
            {"earlier": 1, "later": 11, "evidence_cost": 0.20},
            {"earlier": 2, "later": 10, "evidence_cost": 0.11},
        ]
        selected, rounds = confidence.competition_assignment(
            edges,
            lambda edge: edge["evidence_cost"],
            unmatched_cost=0.80,
            minimum_margin=0.0,
        )
        self.assertGreaterEqual(rounds, 1)
        self.assertTrue(all(edge["evidence_cost"] < 0.80 for edge in selected))


class ConditionalMotionTest(unittest.TestCase):
    @staticmethod
    def edge(earlier: int, later: int, confidence: float, residual: float) -> dict:
        return {
            "earlier": earlier,
            "later": later,
            "gap": 3,
            "endpoint_center_distance_pixels": 10.0,
            "cosine_distance": 0.1,
            "motion_confidence": confidence,
            "motion_normalized_residual": residual,
        }

    def test_reliable_motion_rejects_only_when_context_is_active(self):
        edges = [self.edge(1, 2, 0.9, 0.5), self.edge(3, 4, 0.9, 2.0)]
        kept, details = confidence._conditional_motion_filter(edges, 0.5, 1.0)
        self.assertTrue(details["guard_active"])
        self.assertEqual([confidence.edge_id(edge) for edge in kept], [(1, 2)])

    def test_sparse_reliable_motion_falls_back_to_unchanged_candidates(self):
        edges = [self.edge(1, 2, 0.9, 0.5), self.edge(3, 4, 0.1, 2.0)]
        kept, details = confidence._conditional_motion_filter(edges, 0.5, 1.0)
        self.assertFalse(details["guard_active"])
        self.assertEqual(len(kept), 2)

    def test_final_alias_matches_frozen_stage2_method(self):
        predictions = {
            0: [row(1, 0.0)],
            1: [row(1, 1.0)],
            2: [row(1, 2.0)],
            5: [row(2, 5.0)],
            6: [row(2, 6.0)],
            7: [row(2, 7.0)],
        }
        candidates = [{
            "earlier": 1,
            "later": 2,
            "gap": 3,
            "endpoint_center_distance_pixels": 3.0,
            "cosine_distance": 0.1,
        }]
        frozen, frozen_key, _ = confidence.select(
            "s2_t_cond_w3_scale_c50_r100", predictions, candidates
        )
        final, final_key, _ = confidence.select("regr_final", predictions, candidates)
        self.assertEqual([confidence.edge_id(edge) for edge in frozen], [(1, 2)])
        self.assertEqual([confidence.edge_id(edge) for edge in final], [(1, 2)])
        self.assertEqual(frozen_key(frozen[0]), final_key(final[0]))

    def test_public_regr_name_resolves_to_frozen_final(self):
        predictions = {
            0: [row(1, 0.0)],
            1: [row(1, 1.0)],
            2: [row(1, 2.0)],
            5: [row(2, 5.0)],
            6: [row(2, 6.0)],
            7: [row(2, 7.0)],
        }
        candidates = [{
            "earlier": 1,
            "later": 2,
            "gap": 3,
            "endpoint_center_distance_pixels": 3.0,
            "cosine_distance": 0.1,
        }]
        proposed, _, details = select_edges("regr", predictions, candidates)
        self.assertEqual(resolve_method("regr"), "regr_final")
        self.assertEqual([confidence.edge_id(edge) for edge in proposed], [(1, 2)])
        self.assertEqual(details["family"], "FINAL")


if __name__ == "__main__":
    unittest.main()
