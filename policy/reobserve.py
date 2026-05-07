"""Next-view candidate generation and policy selection."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from ambiguity import AmbiguityDiagnosis


@dataclass(slots=True)
class CandidateView:
    view_type: str
    expected_information_gain: float
    flight_distance_cost: float
    time_cost: float
    energy_cost: float
    safety_penalty: float = 0.0

    def total_cost(self) -> float:
        return self.flight_distance_cost + self.time_cost + self.energy_cost

    def score(self, lambda_cost: float = 0.2, lambda_risk: float = 1.0) -> float:
        return self.expected_information_gain - lambda_cost * self.total_cost() - lambda_risk * self.safety_penalty

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["score"] = self.score()
        return payload


def generate_candidate_views(base_gain: float = 0.4) -> list[CandidateView]:
    return [
        CandidateView("side view", base_gain + 0.20, 12.0, 4.0, 3.0, 0.05),
        CandidateView("front view", base_gain + 0.10, 8.0, 3.0, 2.0, 0.03),
        CandidateView("rear view", base_gain + 0.08, 9.0, 3.0, 2.0, 0.03),
        CandidateView("top-down view", base_gain - 0.05, 4.0, 2.0, 1.0, 0.01),
        CandidateView("closer view", base_gain + 0.25, 15.0, 5.0, 4.0, 0.08),
    ]


def select_next_view(
    candidates: list[CandidateView],
    *,
    lambda_cost: float = 0.2,
    lambda_risk: float = 1.0,
) -> CandidateView:
    if not candidates:
        raise ValueError("At least one candidate view is required")
    return max(candidates, key=lambda candidate: candidate.score(lambda_cost, lambda_risk))


def select_action(diagnosis: AmbiguityDiagnosis) -> dict[str, object]:
    if diagnosis.level == "low":
        return {"action": "finalize", "candidate_view": None}
    if diagnosis.level == "medium":
        return {"action": "VLM verify", "candidate_view": None}
    candidates = generate_candidate_views(base_gain=min(1.0, diagnosis.score))
    best = select_next_view(candidates)
    return {"action": "active re-observe", "candidate_view": best.to_dict()}

