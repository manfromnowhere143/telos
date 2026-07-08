"""Target-survey validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from telos.scorecard import CandidateScore, rank_candidates


class SurveyValidationError(ValueError):
    """Raised when an iter00 target survey does not satisfy the frozen contract."""


VALID_DECISIONS = {
    "TARGET_SELECTED",
    "HYBRID_OVERLAY_SELECTED",
    "SURVEY_NULL",
    "BLOCKED",
}


@dataclass(frozen=True)
class SurveyDecision:
    """Validated target-survey decision."""

    generated_at: str
    decision: str
    candidates: list[CandidateScore]
    winner: CandidateScore | None


def _require_url(value: str, path: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise SurveyValidationError(f"{path} is not an http(s) URL: {value}")


def _candidate_from_dict(raw: dict[str, Any], idx: int) -> CandidateScore:
    try:
        candidate = CandidateScore(
            candidate_id=str(raw["candidate_id"]),
            frontier_relevance=int(raw["frontier_relevance"]),
            public_baseline_quality=int(raw["public_baseline_quality"]),
            falsifiability=int(raw["falsifiability"]),
            evidence_surface=int(raw["evidence_surface"]),
            aweb_fit=int(raw["aweb_fit"]),
            saturation_risk=int(raw["saturation_risk"]),
            operational_cost=int(raw["operational_cost"]),
        )
    except KeyError as exc:
        raise SurveyValidationError(f"candidates[{idx}] missing {exc.args[0]}") from exc

    candidate.validate()
    sources = raw.get("sources")
    if not isinstance(sources, list) or not sources:
        raise SurveyValidationError(f"candidates[{idx}].sources must be non-empty")
    for source_idx, source in enumerate(sources):
        if not isinstance(source, str):
            raise SurveyValidationError(f"candidates[{idx}].sources[{source_idx}] must be string")
        _require_url(source, f"candidates[{idx}].sources[{source_idx}]")

    rationale = raw.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        raise SurveyValidationError(f"candidates[{idx}].rationale must be non-empty")

    return candidate


def validate_survey(data: dict[str, Any]) -> SurveyDecision:
    """Validate the frozen iter00 survey output."""

    decision = data.get("decision")
    if decision not in VALID_DECISIONS:
        raise SurveyValidationError(f"invalid decision: {decision}")

    generated_at = data.get("generated_at")
    if not isinstance(generated_at, str):
        raise SurveyValidationError("generated_at must be a string")
    try:
        datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SurveyValidationError(f"generated_at is not ISO-like: {generated_at}") from exc

    raw_candidates = data.get("candidates")
    if not isinstance(raw_candidates, list) or len(raw_candidates) < 5:
        raise SurveyValidationError("candidates must contain at least five entries")

    candidates = [_candidate_from_dict(raw, idx) for idx, raw in enumerate(raw_candidates)]
    ids = [candidate.candidate_id for candidate in candidates]
    if len(ids) != len(set(ids)):
        raise SurveyValidationError("candidate_id values must be unique")

    ranked = rank_candidates(candidates)
    winner = ranked[0] if ranked else None

    if decision in {"TARGET_SELECTED", "HYBRID_OVERLAY_SELECTED"}:
        if winner is None:
            raise SurveyValidationError("positive decision requires a winner")
        positive_components = [
            winner.frontier_relevance,
            winner.public_baseline_quality,
            winner.falsifiability,
            winner.evidence_surface,
            winner.aweb_fit,
        ]
        if winner.total() < 16:
            raise SurveyValidationError(f"winner adjusted score below 16: {winner.total()}")
        if min(positive_components) < 3:
            raise SurveyValidationError("winner has a positive component below 3")
        if winner.operational_cost > 3:
            raise SurveyValidationError("winner operational cost is above 3")

    return SurveyDecision(
        generated_at=generated_at,
        decision=str(decision),
        candidates=candidates,
        winner=winner,
    )


def load_survey(path: str | Path) -> SurveyDecision:
    """Load and validate a survey scorecard."""

    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise SurveyValidationError("survey root must be an object")
    return validate_survey(data)
