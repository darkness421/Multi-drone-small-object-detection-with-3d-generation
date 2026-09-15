from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/ace_v_core.py"
SPEC = importlib.util.spec_from_file_location("ace_v_core", MODULE_PATH)
CORE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = CORE
SPEC.loader.exec_module(CORE)


def row(identity, x, y=0.0, w=10.0, h=10.0):
    return {"id": identity, "x": x, "y": y, "w": w, "h": h, "conf": 1.0}


def edge(source, destination, cost, gap=1):
    return {
        "earlier": source,
        "later": destination,
        "controlled_cost": cost,
        "gap": gap,
    }


class AceVCoreTests(unittest.TestCase):
    def test_margin_includes_null_and_local_competitors(self):
        predictions = {0: [row(1, 0), row(2, 0)], 2: [row(3, 2), row(4, 2)]}
        features = CORE.add_verification_features(
            [edge(1, 3, 0.4), edge(1, 4, 0.2), edge(2, 3, 0.3)], predictions
        )
        target = next(item for item in features if CORE.pair(item) == (1, 3))
        self.assertAlmostEqual(target["outgoing_margin"], -0.2)
        self.assertAlmostEqual(target["incoming_margin"], -0.1)
        self.assertAlmostEqual(target["competition_ambiguity"], 0.2)

    def test_linear_motion_agreement(self):
        predictions = {
            0: [row(1, 0)], 1: [row(1, 1)], 2: [row(1, 2)],
            5: [row(2, 5)], 6: [row(2, 6)], 7: [row(2, 7)],
        }
        feature = CORE.motion_feature(CORE.tracklet_rows(predictions), 1, 2)
        self.assertTrue(feature["motion_available"])
        self.assertAlmostEqual(feature["motion_residual"], 0.0, places=10)
        self.assertAlmostEqual(feature["motion_source_fit_residual_pixels"], 0.0, places=10)

    def test_motion_missing_is_explicit(self):
        predictions = {0: [row(1, 0)], 2: [row(2, 2)]}
        enriched = CORE.add_verification_features([edge(1, 2, 0.2)], predictions)[0]
        self.assertFalse(enriched["motion_available"])
        self.assertEqual(enriched["motion_missing_reason"], "fewer_than_two_distinct_frames")
        self.assertTrue(CORE.verifier_pass(enriched, "V_motion", 0.0, 1.0))
        self.assertTrue(CORE.verifier_pass(enriched, "V_full", 0.0, 1.0))

    def test_symmetric_null_hungarian_leaves_expensive_edge_unlinked(self):
        selected = CORE.partial_hungarian([edge(1, 3, 0.2), edge(2, 4, 1.2)])
        self.assertEqual([CORE.pair(item) for item in selected], [(1, 3)])

    def test_hungarian_is_one_to_one_and_order_invariant(self):
        values = [edge(1, 3, 0.1), edge(1, 4, 0.2), edge(2, 3, 0.15), edge(2, 4, 0.9)]
        expected = {(1, 4), (2, 3)}
        self.assertEqual({CORE.pair(item) for item in CORE.partial_hungarian(values)}, expected)
        self.assertEqual({CORE.pair(item) for item in CORE.partial_hungarian(reversed(values))}, expected)

    def test_path_greedy_enforces_endpoint_degrees(self):
        values = [edge(1, 3, 0.1), edge(1, 4, 0.2), edge(2, 3, 0.15)]
        selected = CORE.path_constrained_greedy(values)
        self.assertEqual([CORE.pair(item) for item in selected], [(1, 3)])
        CORE.assert_path_constraints(selected)

    def test_verifier_off_reproduces_both_base_solvers(self):
        values = [
            {
                **edge(1, 3, 0.1),
                "competition_ambiguity": 1.0,
                "motion_available": False,
            },
            {
                **edge(1, 4, 0.2),
                "competition_ambiguity": 1.0,
                "motion_available": False,
            },
            {
                **edge(2, 3, 0.15),
                "competition_ambiguity": 1.0,
                "motion_available": False,
            },
        ]
        verifier_off = CORE.filter_edges(values, "V_off", 0.0, 0.0)
        for solver in (CORE.partial_hungarian, CORE.path_constrained_greedy):
            self.assertEqual(
                [CORE.pair(item) for item in solver(values)],
                [CORE.pair(item) for item in solver(verifier_off)],
            )


if __name__ == "__main__":
    unittest.main()
