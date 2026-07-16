from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

import pytest

from scripts import run_ci_closure
from scripts import validate_iter219_temporal_consequence_test_yield as guard
from telos.tcp1 import exact_one_sided_mcnemar, wilson_interval

ROOT = Path(__file__).resolve().parents[1]


def _next_ulp(value: float, steps: int = 1) -> float:
    for _ in range(steps):
        value = math.nextafter(value, math.inf)
    return value


# --------------------------------------------------------------------------- #
# C1 — forgive platform noise, catch tampering.
# --------------------------------------------------------------------------- #


def test_interval_matches_when_a_platform_differs_by_one_ulp() -> None:
    # This is the exact Linux failure: a correct interval, off by one unit in the last
    # place because sqrt is libm-dependent.
    expected = wilson_interval(163, 482)
    stored = [_next_ulp(expected[0]), _next_ulp(expected[1])]

    assert stored != list(expected), "the fixture must actually differ bitwise"
    assert guard.intervals_match(stored, expected)


def test_interval_matches_across_several_ulps_of_drift() -> None:
    expected = wilson_interval(196, 482)
    stored = [_next_ulp(expected[0], 8), _next_ulp(expected[1], 8)]
    assert guard.intervals_match(stored, expected)


def test_interval_rejects_tampering_at_the_tolerance_boundary() -> None:
    expected = wilson_interval(196, 482)
    tampered = [expected[0] * (1 + 1e-7), expected[1]]
    assert not guard.intervals_match(tampered, expected)


def test_interval_rejects_a_visibly_altered_interval() -> None:
    expected = wilson_interval(196, 482)
    assert not guard.intervals_match([0.99, 1.0], expected)


def test_interval_rejects_a_malformed_interval() -> None:
    assert not guard.intervals_match([0.5], wilson_interval(196, 482))


def test_tolerance_is_far_looser_than_ulp_and_far_tighter_than_a_reported_digit() -> None:
    # One ULP is ~1e-16 relative; the coarsest tampering that changes a printed 4-decimal
    # figure is ~1e-4 relative.  The tolerance must sit strictly between.
    assert 1e-16 < guard.INTERVAL_REL_TOL < 1e-4


def test_the_exact_committed_report_still_validates() -> None:
    assert guard.validate() == []


# --------------------------------------------------------------------------- #
# Everything exactly reproducible must stay exact.
# --------------------------------------------------------------------------- #


def test_mcnemar_is_deterministic_and_must_not_be_given_a_tolerance() -> None:
    # comb() over exact integers, divided by 2**n.  IEEE 754 division is exactly
    # specified, so this is bit-identical on every platform and stays an exact check.
    pairs = [(True, False)] * 132 + [(False, True)] * 16 + [(True, True)] * 334
    first = exact_one_sided_mcnemar(pairs)
    second = exact_one_sided_mcnemar(list(pairs))

    assert first == second
    assert first["one_sided_exact_p_value"] == second["one_sided_exact_p_value"]


def test_guard_still_fires_when_the_paired_test_is_tampered_with() -> None:
    report = json.loads(guard.REPORT.read_text(encoding="utf-8"))
    report["results_by_delta"]["365"]["mcnemar_real_gt_control"]["one_sided_exact_p_value"] = 0.0
    with pytest.raises(guard.Iter219ValidationError, match="McNemar"):
        guard.check_report_recomputes(report)


def test_guard_still_fires_when_integer_counts_are_tampered_with() -> None:
    report = json.loads(guard.REPORT.read_text(encoding="utf-8"))
    report["results_by_delta"]["365"]["real_hits"] += 1
    with pytest.raises(guard.Iter219ValidationError, match="real_hits"):
        guard.check_report_recomputes(report)


def test_no_guard_compares_a_libm_derived_value_bit_exactly() -> None:
    source = Path(guard.__file__).read_text(encoding="utf-8")
    offenders = [
        line.strip()
        for line in source.splitlines()
        if "wilson_interval" in line and "==" in line
    ]
    assert offenders == [], f"bit-exact comparison on a sqrt-derived value: {offenders}"


# --------------------------------------------------------------------------- #
# C2 — a clean local run must not masquerade as a certified one.
# --------------------------------------------------------------------------- #


def test_closure_runner_accepts_a_python_override() -> None:
    result = subprocess.run(
        ["python3", "scripts/run_ci_closure.py", "--python", "python3.11", "--list"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "python3.11 -m compileall" in result.stdout
    assert "python3 -m compileall" not in result.stdout


def test_closure_runner_still_derives_every_command_under_an_override() -> None:
    plain = run_ci_closure.declared_commands()
    assert len(plain) > 200


# --------------------------------------------------------------------------- #
# Predecessor evidence must survive this recovery too.
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "path",
    [
        "experiments/iter219_temporal_consequence_test_yield/HYPOTHESIS.md",
        "experiments/iter219_temporal_consequence_test_yield/RESULT.md",
        "experiments/iter219_temporal_consequence_test_yield/proof/yield_report.json",
        "experiments/iter219_temporal_consequence_test_yield/proof/analysis_amendment.json",
    ],
)
def test_iter219_evidence_survives_the_second_recovery(path: str) -> None:
    sealed = subprocess.run(
        ["git", "show", f"11e335e82100319a4f5f47d86eaea0c8e81edbbc:{path}"],
        cwd=ROOT,
        capture_output=True,
    )
    assert sealed.returncode == 0
    assert (ROOT / path).read_bytes() == sealed.stdout, f"{path} changed during recovery"


# --------------------------------------------------------------------------- #
# Sealed receipts must validate their own source blobs, not a descendant's tree.
# Iter213/iter214 fixed this class once; iter221's receipts reintroduced it by
# binding shared files (README, ci.yml) that later iterations legitimately edit.
# --------------------------------------------------------------------------- #

from scripts import receipt_sealing  # noqa: E402


@pytest.mark.parametrize("tag", ["iter219", "iter220", "iter221"])
def test_sealed_receipt_verifies_against_its_own_source_commit(tag: str) -> None:
    result = subprocess.run(
        ["python3", f"scripts/build_{tag}_receipt.py", "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "sealed source" in result.stdout


def test_introducing_commit_finds_the_adding_commit() -> None:
    commit = receipt_sealing.introducing_commit(
        ROOT, "experiments/iter219_temporal_consequence_test_yield/proof/yield_report.json"
    )
    assert commit is not None and len(commit) == 40


def test_introducing_commit_returns_none_for_an_uncommitted_path(tmp_path) -> None:
    scratch = ROOT / "experiments/.iter221_probe_uncommitted.json"
    scratch.write_text("{}")
    try:
        assert receipt_sealing.introducing_commit(ROOT, scratch.name) is None
    finally:
        scratch.unlink()


def test_sealed_verification_detects_a_tampered_artifact(tmp_path) -> None:
    # Build a throwaway repo whose receipt records a digest that its source blob does not
    # match; sealed verification must refuse it.
    import hashlib as _h
    import json as _j

    repo = tmp_path / "r"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)

    (repo / "bound.txt").write_text("real content")
    receipt = repo / "receipt_v2.json"
    receipt.write_text(
        _j.dumps(
            {
                "evidence": [
                    {
                        "artifact": {
                            "path": "bound.txt",
                            "bytes": len(b"real content"),
                            "sha256": _h.sha256(b"WRONG").hexdigest(),
                        }
                    }
                ]
            }
        )
    )
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "seal"], cwd=repo, check=True)

    with pytest.raises(receipt_sealing.ReceiptSealingError, match="digest differs"):
        receipt_sealing.verify_against_source(repo, receipt)
