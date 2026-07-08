from __future__ import annotations

import pytest

from telos.scorecard import CandidateScore, rank_candidates


def test_rank_candidates_prefers_higher_adjusted_score() -> None:
    shallow = CandidateScore("shallow", 4, 4, 4, 2, 4, 4, 1)
    strong = CandidateScore("strong", 5, 5, 5, 5, 5, 1, 2)

    assert [item.candidate_id for item in rank_candidates([shallow, strong])] == [
        "strong",
        "shallow",
    ]


def test_score_range_is_enforced() -> None:
    candidate = CandidateScore("bad", 6, 0, 0, 0, 0, 0, 0)
    with pytest.raises(ValueError, match="frontier_relevance"):
        candidate.validate()
