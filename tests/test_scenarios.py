"""Tests for CoM3D-MarineCity scenario generation."""

from __future__ import annotations

import unittest

from sim.scenarios.generate_scenarios import generate_scenarios, validate_scenario


class ScenarioGenerationTest(unittest.TestCase):
    """Validate controlled ambiguity scenario generation."""

    def test_generate_requested_count(self) -> None:
        scenarios = generate_scenarios(7)
        self.assertEqual(len(scenarios), 7)

    def test_all_scenarios_validate(self) -> None:
        scenarios = generate_scenarios(10)
        for scenario in scenarios:
            validate_scenario(scenario)

    def test_contains_expected_ambiguity_cases(self) -> None:
        scenarios = generate_scenarios(5)
        ambiguity_pairs = {scenario["objects"][0]["ambiguity_pair"] for scenario in scenarios}
        self.assertIn("van_vs_ambulance", ambiguity_pairs)
        self.assertIn("small_boat_vs_debris", ambiguity_pairs)


if __name__ == "__main__":
    unittest.main()

