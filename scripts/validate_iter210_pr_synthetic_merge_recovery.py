#!/usr/bin/env python3
"""Validate iter210 PR synthetic-merge recovery and exact source/seal topology."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_iter210_receipt import (  # noqa: E402
    BINDINGS,
    RECEIPT_PATH,
    sealed_source_commit,
    verify_sealed_receipt,
)
from telos.proof import ProofValidationError, validate_receipt_v2  # noqa: E402


PREDECESSOR_SEAL = "91f9258730bf5520d86c9235d7ed2f03724ea103"
PREFIX = "experiments/iter210_pr_synthetic_merge_recovery/"
DIAGNOSIS = ROOT / f"{PREFIX}proof/pr_synthetic_merge_failure.json"
RESULT = ROOT / f"{PREFIX}RESULT.md"
RECEIPT_RELATIVE = RECEIPT_PATH.relative_to(ROOT).as_posix()


class Iter210ValidationError(ValueError):
    """Raised when iter210 no longer matches its publication-only boundary."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Iter210ValidationError(message)


def _git(*arguments: str) -> str:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise Iter210ValidationError(f"git command failed: {' '.join(arguments)}") from exc
    return result.stdout.rstrip()


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Iter210ValidationError(f"cannot read canonical JSON: {path}") from exc
    _require(isinstance(value, dict), f"JSON root is not an object: {path}")
    return value


def source_and_seal() -> tuple[str, str] | None:
    """Resolve source and branch seal without assuming checkout HEAD is the branch tip."""

    source = sealed_source_commit()
    if source is None:
        return None
    head_row = _git("rev-list", "--parents", "-n", "1", "HEAD").split()
    candidates = [head_row[0], *head_row[1:]]
    for candidate in candidates:
        row = _git("rev-list", "--parents", "-n", "1", candidate).split()
        if row == [candidate, source]:
            return source, candidate
    raise Iter210ValidationError("cannot resolve iter210 handoff seal from Git parent topology")


def validate_diagnosis_and_fix() -> None:
    diagnosis = _json(DIAGNOSIS)
    _require(
        diagnosis.get("schema_version") == "telos.iter210.pr_synthetic_merge_failure.v1",
        "iter210 diagnosis schema differs",
    )
    _require(diagnosis.get("predecessor_seal") == PREDECESSOR_SEAL, "iter210 predecessor differs")
    attempt = diagnosis.get("failed_publication_attempt", {})
    _require(
        attempt.get("draft_pull_request") == 9
        and attempt.get("head_sha") == PREDECESSOR_SEAL
        and attempt.get("push_ci", {}).get("run_id") == 29493772108
        and attempt.get("push_ci", {}).get("conclusion") == "success"
        and attempt.get("pull_request_ci", {}).get("run_id") == 29494386126
        and attempt.get("pull_request_ci", {}).get("conclusion") == "failure",
        "iter210 remote failure identities differ",
    )
    actions = diagnosis.get("actions_during_iter210_before_publication")
    _require(
        isinstance(actions, dict) and actions and all(value == 0 for value in actions.values()),
        "iter210 zero-action ledger differs",
    )
    validator = (ROOT / "scripts/validate_iter209_publication_ci_recovery.py").read_text(
        encoding="utf-8"
    )
    for fragment in (
        'ITER209_SEAL_COMMIT = "91f9258730bf5520d86c9235d7ed2f03724ea103"',
        "def validation_target",
        'return ITER209_SEAL_COMMIT if result.returncode == 0 else "HEAD"',
    ):
        _require(fragment in validator, f"iter209 topology fix is missing: {fragment}")
    builder = (ROOT / "scripts/build_iter209_receipt.py").read_text(encoding="utf-8")
    for fragment in ("def sealed_descendant", "def verify_sealed_receipt", "refusing to rewrite"):
        _require(fragment in builder, f"iter209 sealed-receipt fix is missing: {fragment}")
    result = RESULT.read_text(encoding="utf-8")
    _require("Status: PASS locally; remote publication gates pending." in result, "iter210 result differs")
    _require("contributes no scientific `N`, `k`, `u`" in result, "iter210 claim boundary is absent")


def validate_experiment_delta(target: str) -> None:
    _git("merge-base", "--is-ancestor", PREDECESSOR_SEAL, target)
    changed = set(
        _git(
            "diff", "--name-only", "--diff-filter=ACMRTUXB", PREDECESSOR_SEAL, target, "--", "experiments"
        ).splitlines()
    )
    unauthorized = sorted(path for path in changed if path and not path.startswith(PREFIX))
    _require(not unauthorized, "iter210 changes frozen experiment paths: " + ", ".join(unauthorized))


def validate_receipt_and_topology() -> None:
    resolved = source_and_seal()
    _require(resolved is not None, "iter210 sealed handoff identity is absent")
    source, seal = resolved
    _require(
        _git("rev-list", "--parents", "-n", "1", source).split()
        == [source, PREDECESSOR_SEAL],
        "iter210 source is not the direct child of iter209 seal",
    )
    _require(
        _git("rev-list", "--parents", "-n", "1", seal).split() == [seal, source],
        "iter210 seal is not the direct child of source",
    )
    _require(
        _git("diff", "--name-status", "--no-renames", source, seal).splitlines()
        == ["M\tHANDOFF.md"],
        "iter210 handoff seal changes more than HANDOFF.md",
    )
    verify_sealed_receipt(source)
    receipt = validate_receipt_v2(_json(RECEIPT_PATH))
    bound = {item["artifact"]["path"] for item in receipt.evidence}
    _require(bound == set(BINDINGS), "iter210 receipt binding set differs")
    source_delta = set(
        _git("diff", "--name-only", "--no-renames", PREDECESSOR_SEAL, source).splitlines()
    )
    _require(
        source_delta - {RECEIPT_RELATIVE} == set(BINDINGS),
        "iter210 receipt does not cover exact source delta",
    )
    validate_experiment_delta(source)


def validate(*, preflight: bool = False) -> list[str]:
    failures: list[str] = []
    try:
        validate_diagnosis_and_fix()
        if preflight:
            validate_experiment_delta("HEAD")
        else:
            validate_receipt_and_topology()
    except (OSError, ProofValidationError, RuntimeError, Iter210ValidationError) as exc:
        failures.append(str(exc))
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    failures = validate(preflight=args.preflight)
    if failures:
        print("iter210 PR synthetic-merge recovery guard failed:", file=sys.stderr)
        for failure in failures:
            print(f" - {failure}", file=sys.stderr)
        return 1
    print(f"iter210 PR synthetic-merge recovery guard: {'preflight' if args.preflight else 'final'} pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
