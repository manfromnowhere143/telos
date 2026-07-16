#!/usr/bin/env python3
"""Validate the additive iter209 publication-CI recovery and receipt closure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_iter209_receipt import BINDINGS, RECEIPT_PATH  # noqa: E402
from telos.proof import ProofValidationError, load_receipt_v2  # noqa: E402


ITER208_SEAL_COMMIT = "a2c2863cf993cb6dd39d2fada8d58e4796929120"
ITER209_PREFIX = "experiments/iter209_publication_ci_recovery/"
HYPOTHESIS = ROOT / f"{ITER209_PREFIX}HYPOTHESIS.md"
RESULT = ROOT / f"{ITER209_PREFIX}RESULT.md"
DIAGNOSIS = ROOT / f"{ITER209_PREFIX}proof/ci_failure_diagnosis.json"
RECEIPT_RELATIVE = RECEIPT_PATH.relative_to(ROOT).as_posix()


class Iter209ValidationError(ValueError):
    """Raised when publication recovery no longer matches its sealed boundary."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Iter209ValidationError(message)


def _git(*arguments: str) -> str:
    try:
        process = subprocess.run(
            ["git", *arguments],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise Iter209ValidationError(
            f"git command failed: {' '.join(arguments)}"
        ) from exc
    return process.stdout.rstrip()


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Iter209ValidationError(f"cannot read canonical JSON: {path}") from exc
    _require(isinstance(value, dict), f"JSON root is not an object: {path}")
    return value


def validate_predecessor_and_experiment_delta() -> None:
    _git("merge-base", "--is-ancestor", ITER208_SEAL_COMMIT, "HEAD")
    changed = set(
        _git(
            "diff",
            "--name-only",
            "--diff-filter=ACMRTUXB",
            ITER208_SEAL_COMMIT,
            "HEAD",
            "--",
            "experiments",
        ).splitlines()
    )
    changed.update(
        _git("ls-files", "--others", "--exclude-standard", "--", "experiments").splitlines()
    )
    unauthorized = sorted(path for path in changed if path and not path.startswith(ITER209_PREFIX))
    _require(
        not unauthorized,
        "iter209 changes frozen experiment paths: " + ", ".join(unauthorized),
    )


def validate_diagnosis_and_fixes() -> None:
    diagnosis = _json(DIAGNOSIS)
    _require(
        diagnosis.get("schema_version")
        == "telos.iter209.publication_ci_failure_diagnosis.v1",
        "iter209 diagnosis schema differs",
    )
    _require(
        diagnosis.get("predecessor_seal") == ITER208_SEAL_COMMIT,
        "iter209 diagnosis predecessor differs",
    )
    attempt = diagnosis.get("failed_publication_attempt", {})
    _require(
        attempt.get("head_sha") == ITER208_SEAL_COMMIT
        and attempt.get("draft_pull_request") == 8
        and attempt.get("push_ci", {}).get("run_id") == 29491806574
        and attempt.get("pull_request_ci", {}).get("run_id") == 29491841840,
        "iter209 diagnosis remote identities differ",
    )
    actions = diagnosis.get("actions_during_iter209_before_publication")
    _require(
        isinstance(actions, dict) and actions and all(value == 0 for value in actions.values()),
        "iter209 zero-action ledger differs",
    )
    audit = (ROOT / "scripts/audit_receipt_schema_prompt_alignment.py").read_text(
        encoding="utf-8"
    )
    for fragment in (
        'ITER65_SOURCE_COMMIT = "40cdf2d5bbbd4d9ccd22aebb54cf04606ed90702"',
        "def historical_sha256",
        "historical_source_hashes",
    ):
        _require(fragment in audit, f"iter65 descendant-safe audit fix is missing: {fragment}")
    tests = (ROOT / "tests/test_make_handoff.py").read_text(encoding="utf-8")
    for fragment in (
        'monkeypatch.delenv("GITHUB_ACTIONS", raising=False)',
        'monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)',
    ):
        _require(fragment in tests, f"pull-request test isolation is missing: {fragment}")
    result = RESULT.read_text(encoding="utf-8")
    _require("Status: PASS locally; remote publication gates pending." in result, "iter209 result status differs")
    _require("contributes no scientific `N`, `k`, `u`" in result, "iter209 claim boundary is absent")


def validate_receipt_and_source_closure() -> None:
    try:
        receipt = load_receipt_v2(RECEIPT_PATH, artifact_root=ROOT)
    except (OSError, ProofValidationError) as exc:
        raise Iter209ValidationError(f"iter209 receipt does not verify: {exc}") from exc
    bound = {item["artifact"]["path"] for item in receipt.evidence}
    _require(bound == set(BINDINGS), "iter209 receipt binding set differs")
    delta = set(
        _git("diff", "--name-only", "--no-renames", ITER208_SEAL_COMMIT, "HEAD").splitlines()
    )
    source_delta = delta - {"HANDOFF.md", RECEIPT_RELATIVE}
    _require(source_delta == set(BINDINGS), "iter209 receipt does not cover the exact source delta")
    if "HANDOFF.md" in delta:
        status = _git(
            "diff",
            "--name-status",
            "--no-renames",
            "HEAD^",
            "HEAD",
        ).splitlines()
        _require(status == ["M\tHANDOFF.md"], "iter209 handoff seal changes more than HANDOFF.md")


def validate(*, preflight: bool = False) -> list[str]:
    failures: list[str] = []
    for check in (validate_predecessor_and_experiment_delta, validate_diagnosis_and_fixes):
        try:
            check()
        except (OSError, Iter209ValidationError) as exc:
            failures.append(str(exc))
    if not preflight:
        try:
            validate_receipt_and_source_closure()
        except (OSError, Iter209ValidationError) as exc:
            failures.append(str(exc))
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    failures = validate(preflight=args.preflight)
    if failures:
        print("iter209 publication CI recovery guard failed:", file=sys.stderr)
        for failure in failures:
            print(f" - {failure}", file=sys.stderr)
        return 1
    mode = "preflight" if args.preflight else "final"
    print(f"iter209 publication CI recovery guard: {mode} pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
