#!/usr/bin/env python3
"""Validate iter00 target-survey output when it exists."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.survey import SurveyValidationError, load_survey


SCORECARD = Path("experiments/iter00_target_survey/proof/scorecard.json")


def main() -> int:
    if not SCORECARD.exists():
        print(f"target survey: pending ({SCORECARD} not present)")
        return 0

    try:
        decision = load_survey(SCORECARD)
    except SurveyValidationError as exc:
        print(f"target survey invalid: {exc}")
        return 1

    winner = decision.winner.candidate_id if decision.winner else "none"
    print(f"target survey valid: decision={decision.decision} winner={winner}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
