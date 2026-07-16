"""Candidate target scorecard.

The first research act is target selection. A target can be exciting and still
wrong for this repo if it cannot be measured, falsified, reproduced, or improved.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateScore:
    """Scores one candidate benchmark or task family for the target survey."""

    candidate_id: str
    frontier_relevance: int
    public_baseline_quality: int
    falsifiability: int
    evidence_surface: int
    mission_fit: int
    saturation_risk: int
    operational_cost: int

    @property
    def aweb_fit(self) -> int:
        """Legacy read-only alias for frozen iter00 artifacts."""

        return self.mission_fit

    def total(self) -> int:
        """Higher is better; saturation and cost subtract from the positive bars."""

        positives = (
            self.frontier_relevance
            + self.public_baseline_quality
            + self.falsifiability
            + self.evidence_surface
            + self.mission_fit
        )
        penalties = self.saturation_risk + self.operational_cost
        return positives - penalties

    def validate(self) -> None:
        """Validate score ranges."""

        values = {
            "frontier_relevance": self.frontier_relevance,
            "public_baseline_quality": self.public_baseline_quality,
            "falsifiability": self.falsifiability,
            "evidence_surface": self.evidence_surface,
            "mission_fit": self.mission_fit,
            "saturation_risk": self.saturation_risk,
            "operational_cost": self.operational_cost,
        }
        for name, value in values.items():
            if not 0 <= value <= 5:
                raise ValueError(f"{name} out of range: {value}")


def rank_candidates(candidates: list[CandidateScore]) -> list[CandidateScore]:
    """Return candidates sorted by survey score, then stable id."""

    for candidate in candidates:
        candidate.validate()
    return sorted(candidates, key=lambda item: (-item.total(), item.candidate_id))
