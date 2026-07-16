from __future__ import annotations

import json
from pathlib import Path

from scripts import audit_receipt_schema_prompt_alignment as iter65_audit
from scripts import validate_iter208_post_seal_forensic_correction as iter208_guard
from scripts import validate_iter209_publication_ci_recovery as iter209_guard


ROOT = Path(__file__).resolve().parents[1]


def test_iter65_source_hashes_are_bound_to_the_historical_git_tree() -> None:
    diagnosis = iter65_audit.load_json(iter65_audit.DIAGNOSIS)
    assert diagnosis["proof_module_sha256"] == iter65_audit.historical_sha256(
        iter65_audit.ITER65_SOURCE_COMMIT, iter65_audit.PROOF_MODULE
    )
    assert diagnosis["proof_module_sha256"] != iter65_audit.sha256(
        iter65_audit.PROOF_MODULE
    )


def test_iter208_receipt_and_experiment_delta_validate_on_a_descendant() -> None:
    assert iter208_guard._is_sealed_descendant() is True
    iter208_guard.validate_seal_and_experiment_delta()
    iter208_guard.validate_receipt()


def test_iter209_preflight_is_clean() -> None:
    assert iter209_guard.validate(preflight=True) == []


def test_iter209_diagnosis_records_zero_scientific_actions() -> None:
    diagnosis = json.loads(iter209_guard.DIAGNOSIS.read_text(encoding="utf-8"))
    actions = diagnosis["actions_during_iter209_before_publication"]
    assert actions
    assert set(actions.values()) == {0}
    assert diagnosis["scientific_effect"] == "none"
