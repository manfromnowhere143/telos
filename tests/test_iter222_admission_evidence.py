from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import build_iter222_admission_view as admission
from scripts import run_iter222_isolation_rehearsal as rehearsal
from scripts import validate_iter222_tcp1_agent_solvable_admission_evidence as guard

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / "experiments/iter222_tcp1_agent_solvable_admission_evidence/proof"


# --------------------------------------------------------------------------- #
# Isolation rehearsal: every attack denied, every positive control fires.
# --------------------------------------------------------------------------- #


def test_real_contract_denies_all_five_registered_attacks() -> None:
    contract = json.loads(rehearsal.CONTRACT.read_text(encoding="utf-8"))
    results = rehearsal.evaluate(contract)
    assert len(results) == 5
    assert all(r["denied_by_real_contract"] for r in results)


def test_every_weakened_contract_lets_its_attack_through() -> None:
    # This is the positive control: a rehearsal that could not catch a hole is inert.
    contract = json.loads(rehearsal.CONTRACT.read_text(encoding="utf-8"))
    results = rehearsal.evaluate(contract)
    for result in results:
        assert result["denied_by_weakened_contract"] is False, result["attack"]
        assert result["positive_control_ok"] is True, result["attack"]


def test_rehearsal_would_fail_if_the_contract_already_had_a_hole() -> None:
    # If the real contract were missing a deny rule, the attack would not be denied and the
    # rehearsal must report it — proving the check is not vacuous.
    contract = json.loads(rehearsal.CONTRACT.read_text(encoding="utf-8"))
    contract["zones"]["trusted_grader_vault"]["network_from_agent"] = "allow"
    results = rehearsal.evaluate(contract)
    network = next(r for r in results if "network" in r["attack"])
    assert network["denied_by_real_contract"] is False


# --------------------------------------------------------------------------- #
# Admission view: exactly three flipped, execution stays unauthorized.
# --------------------------------------------------------------------------- #


def test_admission_view_is_five_pass_six_blocked() -> None:
    view = admission.build()
    assert view["passed_gate_count"] == 5
    assert view["blocked_gate_count"] == 6
    assert view["execution_authorized"] is False


def test_admission_view_flips_exactly_the_three_agent_solvable_gates() -> None:
    view = admission.build()
    filled = {g["gate"] for g in view["gates"] if g["iter222_filled"]}
    assert filled == set(admission.FILLED_GATES)
    assert filled == {
        "model_license_cutoff_and_weight_binding",
        "external_transparency_timestamp",
        "hostile_isolation_rehearsal",
    }


def test_admission_gate_stays_blocked_if_its_evidence_fails(tmp_path, monkeypatch) -> None:
    # A gate flips only because its evidence holds.  Point the timestamp evidence at an
    # unverified record and the gate must fall back to blocked, dropping to 4/11.
    monkeypatch.setattr(
        admission, "evidence_holds", lambda g: g != "external_transparency_timestamp"
    )
    view = admission.build()
    assert view["passed_gate_count"] == 4
    assert view["blocked_gate_count"] == 7


# --------------------------------------------------------------------------- #
# Claim boundary: negated mentions pass, assertions fail.
# --------------------------------------------------------------------------- #


def test_negated_forbidden_phrase_is_allowed() -> None:
    assert guard._asserted("this establishes no state of the art here", "state of the art") is False
    assert guard._asserted("it authorizes no execution", "execution authorized") is False


def test_asserted_forbidden_phrase_is_caught() -> None:
    assert guard._asserted("this achieves state of the art results", "state of the art") is True
    assert guard._asserted("execution authorized for the pilot", "execution authorized") is True


def test_committed_result_passes_the_claim_boundary() -> None:
    guard.check_claim_boundary()


def test_claim_boundary_would_fire_on_an_overclaiming_result(tmp_path, monkeypatch) -> None:
    overclaim = tmp_path / "RESULT.md"
    overclaim.write_text("Admission is 5/11 and does not authorize; this achieves state of the art.")
    monkeypatch.setattr(guard, "RESULT", overclaim)
    with pytest.raises(guard.Iter222ValidationError, match="forbidden claim asserted"):
        guard.check_claim_boundary()


# --------------------------------------------------------------------------- #
# Model binding: real digests present, weights never downloaded.
# --------------------------------------------------------------------------- #


def test_committed_model_binding_has_live_digests() -> None:
    record = json.loads((PROOF / "model_binding.json").read_text(encoding="utf-8"))
    default = record["default_model"]
    assert record["weights_downloaded"] is False
    assert len(record["candidate_menu"]) >= 3
    assert default["weight_sha256"]
    assert all(len(d) == 64 for d in default["weight_sha256"].values())
    assert default["license"] == "apache-2.0"


def test_full_guard_passes_at_preflight() -> None:
    assert guard.validate(preflight=True) == []
