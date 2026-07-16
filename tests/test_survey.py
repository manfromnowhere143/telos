from __future__ import annotations

import pytest

from telos.survey import SurveyValidationError, validate_survey


def candidate(candidate_id: str, total_bias: int = 0) -> dict:
    return {
        "candidate_id": candidate_id,
        "frontier_relevance": 4 + total_bias,
        "public_baseline_quality": 4,
        "falsifiability": 4,
        "evidence_surface": 4,
        "mission_fit": 4,
        "saturation_risk": 1,
        "operational_cost": 2,
        "rationale": "public baseline and receipt surface are both inspectable",
        "sources": ["https://example.com/benchmark"],
    }


def survey(decision: str = "TARGET_SELECTED") -> dict:
    return {
        "generated_at": "2026-07-08T00:00:00Z",
        "decision": decision,
        "candidates": [
            candidate("swebench", 1),
            candidate("rebench"),
            candidate("taubench"),
            candidate("agentdojo"),
            candidate("overlay"),
        ],
    }


def test_valid_positive_survey_passes() -> None:
    result = validate_survey(survey())
    assert result.decision == "TARGET_SELECTED"
    assert result.winner is not None
    assert result.winner.candidate_id == "swebench"


def test_positive_survey_requires_winning_bar() -> None:
    data = survey()
    for item in data["candidates"]:
        item["frontier_relevance"] = 3
        item["public_baseline_quality"] = 3
        item["falsifiability"] = 3
        item["evidence_surface"] = 3
        item["mission_fit"] = 3
        item["saturation_risk"] = 3
        item["operational_cost"] = 3

    with pytest.raises(SurveyValidationError, match="below 16"):
        validate_survey(data)


def test_sources_must_be_urls() -> None:
    data = survey("SURVEY_NULL")
    data["candidates"][0]["sources"] = ["not-a-url"]

    with pytest.raises(SurveyValidationError, match="not an http"):
        validate_survey(data)


def test_legacy_aweb_fit_is_read_for_frozen_iter00_artifacts() -> None:
    data = survey()
    for item in data["candidates"]:
        item["aweb_fit"] = item.pop("mission_fit")
    result = validate_survey(data)
    assert result.winner is not None
    assert result.winner.mission_fit == 4


def test_current_and_legacy_fit_fields_cannot_conflict() -> None:
    data = survey()
    data["candidates"][0]["aweb_fit"] = 0
    with pytest.raises(SurveyValidationError, match="conflicts"):
        validate_survey(data)
