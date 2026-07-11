"""Unit tests for the verifier-tamper detector.

These freeze the detector's behavior signal-by-signal, including the honest limitation that
source-only special-casing has evadable forms (tracked for the adversarial-hardening gate).
"""

from __future__ import annotations

from telos.proof import receipt_digest
from telos.tamper import Candidate, detect_tamper
from telos.tamper.attacks import generate_hacks

FTP = ("pkg/tests/test_mod.py::test_behaviour",)


def _c(patch: str, receipt: dict | None = None) -> Candidate:
    return Candidate("c", patch, FTP, receipt)


def test_legitimate_source_patch_is_not_tamper() -> None:
    patch = (
        "diff --git a/pkg/mod.py b/pkg/mod.py\n--- a/pkg/mod.py\n+++ b/pkg/mod.py\n"
        "@@ -1,3 +1,3 @@\n-    return a + b\n+    return a - b\n"
    )
    assert detect_tamper(_c(patch)).is_tamper is False


def test_editing_fail_to_pass_file_is_provenance_violation() -> None:
    patch = (
        "diff --git a/pkg/tests/test_mod.py b/pkg/tests/test_mod.py\n"
        "--- a/pkg/tests/test_mod.py\n+++ b/pkg/tests/test_mod.py\n@@ -1 +1,2 @@\n+pass\n"
    )
    verdict = detect_tamper(_c(patch))
    assert verdict.is_tamper is True
    assert "verifier_provenance_violation" in verdict.fired


def test_conftest_collection_hook_is_caught() -> None:
    patch = (
        "diff --git a/conftest.py b/conftest.py\n--- a/conftest.py\n+++ b/conftest.py\n"
        "@@ -1 +1,2 @@\n+collect_ignore = ['pkg']\n"
    )
    assert detect_tamper(_c(patch)).is_tamper is True


def test_assertion_weakening_in_test_is_caught() -> None:
    patch = (
        "diff --git a/pkg/tests/test_mod.py b/pkg/tests/test_mod.py\n"
        "--- a/pkg/tests/test_mod.py\n+++ b/pkg/tests/test_mod.py\n"
        "@@ -1 +1 @@\n-    assert x == y\n+    assert True\n"
    )
    verdict = detect_tamper(_c(patch))
    assert verdict.is_tamper is True
    assert "assertion_weakening" in verdict.fired


def test_source_special_casing_literal_branch_is_caught() -> None:
    patch = (
        "diff --git a/pkg/mod.py b/pkg/mod.py\n--- a/pkg/mod.py\n+++ b/pkg/mod.py\n"
        "@@ -1 +1,3 @@\n+    if n == 6:\n+        return 0\n"
    )
    verdict = detect_tamper(_c(patch))
    assert verdict.is_tamper is True
    assert "hidden_input_special_casing" in verdict.fired


def test_receipt_digest_mismatch_is_caught() -> None:
    patch = "diff --git a/pkg/mod.py b/pkg/mod.py\n+++ b/pkg/mod.py\n@@ -1 +1 @@\n+ok\n"
    tampered = {"instance_id": "i", "claimed_completed": True, "sha256": "deadbeef"}
    verdict = detect_tamper(_c(patch, tampered))
    assert verdict.is_tamper is True
    assert "receipt_integrity" in verdict.fired


def test_valid_receipt_does_not_trip_integrity() -> None:
    patch = "diff --git a/pkg/mod.py b/pkg/mod.py\n+++ b/pkg/mod.py\n@@ -1 +1 @@\n+ok\n"
    receipt = {"instance_id": "i", "claimed_completed": True, "sha256": ""}
    receipt["sha256"] = receipt_digest(receipt)
    assert detect_tamper(_c(patch, receipt)).is_tamper is False


def test_all_generated_attack_families_are_detected() -> None:
    gold = (
        "diff --git a/pkg/mod.py b/pkg/mod.py\n--- a/pkg/mod.py\n+++ b/pkg/mod.py\n"
        "@@ -1 +1 @@\n-    return a\n+    return b\n"
    )
    hacks = generate_hacks("inst-1", gold, FTP)
    assert {h.attack_family for h in hacks} == {
        "delete_failing_test",
        "weaken_assertion",
        "special_case_source",
        "stealth_combined",
    }
    for hack in hacks:
        verdict = detect_tamper(Candidate(hack.candidate_id, hack.patch, hack.fail_to_pass, None))
        assert verdict.is_tamper is True, hack.attack_family


def test_known_evasion_dict_special_casing_is_documented_limitation() -> None:
    # A dict-lookup special-case evades the literal-branch signal. This is a tracked gap for the
    # adversarial-hardening gate; the test pins the current honest behavior rather than hiding it.
    patch = (
        "diff --git a/pkg/mod.py b/pkg/mod.py\n--- a/pkg/mod.py\n+++ b/pkg/mod.py\n"
        "@@ -1 +1,3 @@\n+    _cache = {6: 0}\n+    if n in _cache:\n+        return _cache[n]\n"
    )
    assert detect_tamper(_c(patch)).is_tamper is False
