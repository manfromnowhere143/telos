#!/usr/bin/env python3
"""Validate the additive iter208 correction and its artifact-bound evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import validate_current_paper  # noqa: E402
from telos.proof import (  # noqa: E402
    ProofValidationError,
    load_receipt_v2,
    validate_receipt_v2,
)


ITER207_SEAL_COMMIT = "f4ee0d5bcb3b4abee7ebf1683be5b9edda263c28"
ITER208_SOURCE_COMMIT = "184883088336cbae834e812a8d1dce0b7b031821"
ITER208_SEAL_COMMIT = "a2c2863cf993cb6dd39d2fada8d58e4796929120"
ITER208_PREFIX = "experiments/iter208_post_seal_forensic_correction/"
EXP = ROOT / ITER208_PREFIX
PROOF = EXP / "proof"
RECEIPT = PROOF / "receipt_v2.json"
RESULT = EXP / "RESULT.md"

REQUIRED_BINDINGS = {
    ".github/workflows/ci.yml",
    "AGENTS.md",
    "CITATION.cff",
    "README.md",
    "docs/FORENSIC-AUDIT-2026-07-16.md",
    "docs/MISSION_LOOP.md",
    "docs/TELOS-ROADMAP-2026.md",
    f"{ITER208_PREFIX}HYPOTHESIS.md",
    f"{ITER208_PREFIX}RESULT.md",
    f"{ITER208_PREFIX}proof/forensic_findings.json",
    f"{ITER208_PREFIX}proof/frontier_sources.json",
    f"{ITER208_PREFIX}proof/hardware_preflight.json",
    "paper/README.md",
    "paper/telos.pdf",
    "paper/telos.tex",
    "mission/loop.json",
    "scripts/audit_iter207_claim_integrity.py",
    "scripts/build_iter207_runtime_manifest.py",
    "scripts/validate_current_paper.py",
    "scripts/validate_handoff.py",
    "scripts/validate_iter207_publication_safety.py",
    "scripts/validate_iter208_post_seal_forensic_correction.py",
    "scripts/validate_mission_loop.py",
    "telos/__init__.py",
    "telos/proof.py",
    "telos/scorecard.py",
    "telos/survey.py",
    "telos/tamper/llm_judge.py",
    "tests/test_iter208_post_seal_forensic_correction.py",
    "tests/test_llm_judge_parse.py",
    "tests/test_make_handoff.py",
    "tests/test_mission_loop_guard.py",
    "tests/test_proof.py",
    "tests/test_survey.py",
}

REQUIRED_ORGANIZATIONS = {
    "OpenAI",
    "Anthropic",
    "NASA",
    "Tesla",
    "SpaceX",
    "Cognition",
    "Perplexity",
    "Stanford",
    "Harvard and Princeton",
    "Cambridge",
}


class Iter208ValidationError(ValueError):
    """Raised when the correction no longer satisfies its frozen boundary."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Iter208ValidationError(message)


def _text(relative: str) -> str:
    path = ROOT / relative
    _require(path.is_file() and not path.is_symlink(), f"missing regular file: {relative}")
    if _is_sealed_descendant():
        try:
            return _git_bytes(ITER208_SOURCE_COMMIT, relative).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise Iter208ValidationError(
                f"sealed iter208 text is not UTF-8: {relative}"
            ) from exc
    return path.read_text(encoding="utf-8")


def _json(relative: str) -> dict[str, Any]:
    try:
        value = json.loads(_text(relative))
    except json.JSONDecodeError as exc:
        raise Iter208ValidationError(f"invalid JSON: {relative}") from exc
    _require(isinstance(value, dict), f"JSON root is not an object: {relative}")
    return value


def _git_output(arguments: list[str]) -> str:
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
        raise Iter208ValidationError(f"git command failed: {' '.join(arguments)}") from exc
    return process.stdout


def _git_bytes(commit: str, relative: str) -> bytes:
    try:
        process = subprocess.run(
            ["git", "show", f"{commit}:{relative}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise Iter208ValidationError(
            f"cannot read sealed iter208 Git blob: {commit}:{relative}"
        ) from exc
    return process.stdout


def _is_sealed_descendant() -> bool:
    try:
        _git_output(["merge-base", "--is-ancestor", ITER208_SEAL_COMMIT, "HEAD"])
    except Iter208ValidationError:
        return False
    return True


def validate_seal_and_experiment_delta() -> None:
    _git_output(["merge-base", "--is-ancestor", ITER207_SEAL_COMMIT, "HEAD"])
    target = ITER208_SOURCE_COMMIT if _is_sealed_descendant() else "HEAD"
    if target == ITER208_SOURCE_COMMIT:
        source_parents = _git_output(
            ["rev-list", "--parents", "-n", "1", ITER208_SOURCE_COMMIT]
        ).split()
        seal_parents = _git_output(
            ["rev-list", "--parents", "-n", "1", ITER208_SEAL_COMMIT]
        ).split()
        _require(
            source_parents == [ITER208_SOURCE_COMMIT, ITER207_SEAL_COMMIT],
            "iter208 sealed source topology differs",
        )
        _require(
            seal_parents == [ITER208_SEAL_COMMIT, ITER208_SOURCE_COMMIT],
            "iter208 handoff-seal topology differs",
        )
    changed = set(
        _git_output(
            [
                "diff",
                "--name-only",
                "--diff-filter=ACMRTUXB",
                ITER207_SEAL_COMMIT,
                target,
                "--",
                "experiments",
            ]
        ).splitlines()
    )
    untracked = (
        set()
        if target == ITER208_SOURCE_COMMIT
        else set(
            _git_output(
                ["ls-files", "--others", "--exclude-standard", "--", "experiments"]
            ).splitlines()
        )
    )
    experiment_delta = {path for path in changed | untracked if path}
    unauthorized = sorted(
        path for path in experiment_delta if not path.startswith(ITER208_PREFIX)
    )
    _require(
        not unauthorized,
        "iter208 changes frozen historical experiment paths: " + ", ".join(unauthorized),
    )


def _require_fragments(relative: str, required: tuple[str, ...], forbidden: tuple[str, ...] = ()) -> None:
    text = " ".join(_text(relative).split())
    for fragment in required:
        _require(fragment in text, f"{relative} missing required fragment: {fragment}")
    for fragment in forbidden:
        _require(fragment not in text, f"{relative} retains forbidden fragment: {fragment}")


def validate_claim_surfaces() -> None:
    _require_fragments(
        "CITATION.cff",
        (
            "cff-version: 1.2.0",
            'title: "TELOS: Evidence Protocols for Verifying Autonomous Agent Work"',
            "family-names: Wahnich",
            "given-names: Daniel",
            'version: "0.0.1"',
            'repository-code: "https://github.com/manfromnowhere143/telos"',
            "license: Apache-2.0",
        ),
        ("doi:", "date-released:",),
    )
    _require_fragments(
        "AGENTS.md",
        (
            "TELOS, Sentinel, Inbar, and Odeya are closely related projects",
            "They are all separate from Aweb",
            "Preserve sealed experiments and raw evidence byte-for-byte",
        ),
    )
    _require_fragments(
        "README.md",
        (
            "Local correction PASS — publication seal pending",
            "Artifact-bound receipt v2",
            "Iter207 is an immutable local seal",
            "208 local PASS",
            "post-seal forensic correction",
        ),
        ("may bias recall downward",),
    )
    _require_fragments(
        "paper/telos.tex",
        (
            "We therefore make no priority or state-of-the-art claim",
            "forensic real-task case series",
            "no causal direction or magnitude is established",
            "SpecBench",
            "RewardHackingAgents",
            "Hack-Verifiable Environments",
            "fresh tasks, pre-authored consequence tests",
        ),
        ("may bias recall downward", "possible downward recall bias"),
    )
    _require_fragments(
        "paper/README.md",
        (
            "iter207 is a sealed local correction baseline",
            "iter208 passed local forensic correction",
            "bibliography contains eighteen entries",
        ),
        ("may bias recall downward",),
    )
    _require_fragments(
        "docs/MISSION_LOOP.md",
        (
            "Sealed runtime/admission gate",
            "Active publication-correction gate",
            "Iter208 is the active post-seal forensic correction",
            "artifact-bound receipt v2",
        ),
    )
    _require_fragments(
        f"{ITER208_PREFIX}HYPOTHESIS.md",
        (
            "operator's later 2026-07-16 amendment",
            "one final branch publication and a draft pull request",
            "Merge is permitted only after non-scientific branch and pull-request CI pass",
        ),
    )
    _require_fragments(
        "docs/FORENSIC-AUDIT-2026-07-16.md",
        (
            "Publication is on hold during iter208",
            "Honest strategic verdict",
            "No merge or push is justified",
        ),
    )
    _require_fragments(
        "docs/TELOS-ROADMAP-2026.md",
        (
            "TELOS Trace–Consequence Pilot 1",
            "60 trajectories",
            "independent human",
            "64 accelerator-hours",
            "No model call, GPU allocation, or scientific execution is authorized",
        ),
    )


def validate_active_code_corrections() -> None:
    scorecard = _text("telos/scorecard.py")
    _require("mission_fit: int" in scorecard, "active scorecard lacks mission_fit")
    _require("def aweb_fit" in scorecard, "legacy iter00 compatibility alias is missing")
    survey = _text("telos/survey.py")
    _require(
        '"mission_fit" in raw' in survey and '"aweb_fit" in raw' in survey,
        "survey does not preserve explicit legacy-field compatibility",
    )
    judge = _text("telos/tamper/llm_judge.py")
    _require("TELOS_VERTEX_PROJECT" in judge, "Vertex project is not environment-driven")
    _require(
        "sunlit-unison-487018-b0" not in judge,
        "active Vertex module retains the historical cloud project locator",
    )
    proof = _text("telos/proof.py")
    for fragment in (
        "RECEIPT_V2_SCHEMA",
        "build_artifact_binding",
        "evidence_closure_digest",
        "validate_receipt_v2",
        "verify_receipt_v2_artifacts",
        "O_NOFOLLOW",
    ):
        _require(fragment in proof, f"receipt v2 implementation missing: {fragment}")


def validate_machine_evidence() -> None:
    findings = _json(f"{ITER208_PREFIX}proof/forensic_findings.json")
    _require(
        findings.get("predecessor_seal") == ITER207_SEAL_COMMIT,
        "forensic findings predecessor differs",
    )
    actions = findings.get("actions_during_audit")
    _require(isinstance(actions, dict), "forensic action ledger is missing")
    _require(all(value == 0 for value in actions.values()), "forensic action ledger is not zero")
    boundary = findings.get("claim_boundary")
    _require(isinstance(boundary, dict), "forensic claim boundary is missing")
    for field in (
        "top_tier_benchmark_claim_supported",
        "population_frequency_claim_supported",
        "model_ranking_claim_supported",
        "production_verifier_claim_supported",
        "personal_endorsements_inferred",
    ):
        _require(boundary.get(field) is False, f"forensic claim boundary overclaims: {field}")
    _require(
        boundary.get("strict_existence_case_supported") is True,
        "forensic claim boundary loses the strict existence finding",
    )

    frontier = _json(f"{ITER208_PREFIX}proof/frontier_sources.json")
    sources = frontier.get("sources")
    _require(isinstance(sources, list) and sources, "frontier source list is empty")
    organizations = {
        row.get("organization")
        for row in sources
        if isinstance(row, dict)
    }
    _require(
        REQUIRED_ORGANIZATIONS.issubset(organizations),
        "frontier source list misses named organizations",
    )
    for row in sources:
        _require(
            isinstance(row, dict)
            and isinstance(row.get("url"), str)
            and row["url"].startswith("https://")
            and isinstance(row.get("observed"), str)
            and isinstance(row.get("telos_implication"), str),
            "frontier source row is malformed",
        )

    hardware = _json(f"{ITER208_PREFIX}proof/hardware_preflight.json")
    _require(
        hardware.get("decision") == "not_suitable_for_tcp1_full_pilot",
        "hardware preflight decision differs",
    )
    hardware_actions = hardware.get("actions")
    _require(
        isinstance(hardware_actions, dict)
        and all(value is False for value in hardware_actions.values()),
        "hardware preflight implies a resource or scientific action",
    )


def validate_receipt() -> None:
    _require(RECEIPT.is_file() and not RECEIPT.is_symlink(), "iter208 receipt v2 is missing")
    try:
        if _is_sealed_descendant():
            relative_receipt = RECEIPT.relative_to(ROOT).as_posix()
            sealed_receipt = _git_bytes(ITER208_SOURCE_COMMIT, relative_receipt)
            data = json.loads(sealed_receipt.decode("utf-8"))
            receipt = validate_receipt_v2(data)
            for item in receipt.evidence:
                artifact = item["artifact"]
                payload = _git_bytes(ITER208_SOURCE_COMMIT, artifact["path"])
                _require(
                    len(payload) == artifact["bytes"]
                    and hashlib.sha256(payload).hexdigest() == artifact["sha256"],
                    f"iter208 sealed artifact differs: {artifact['path']}",
                )
        else:
            receipt = load_receipt_v2(RECEIPT, artifact_root=ROOT)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ProofValidationError) as exc:
        raise Iter208ValidationError(f"iter208 receipt v2 does not verify: {exc}") from exc
    bound_paths = {item["artifact"]["path"] for item in receipt.evidence}
    _require(bound_paths == REQUIRED_BINDINGS, "iter208 receipt v2 binding set differs")
    _require(receipt.status == "pass", "iter208 receipt status is not pass")


def validate(*, preflight: bool = False) -> list[str]:
    failures: list[str] = []
    checks = [
        validate_seal_and_experiment_delta,
        validate_claim_surfaces,
        validate_active_code_corrections,
        validate_machine_evidence,
    ]
    for check in checks:
        try:
            check()
        except (OSError, Iter208ValidationError) as exc:
            failures.append(str(exc))
    failures.extend(validate_current_paper.validate())
    if not preflight:
        try:
            _require(
                RESULT.is_file() and "Status: PASS" in RESULT.read_text(encoding="utf-8"),
                "iter208 RESULT.md is not final PASS",
            )
            validate_receipt()
        except (OSError, Iter208ValidationError) as exc:
            failures.append(str(exc))
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    failures = validate(preflight=args.preflight)
    if failures:
        for failure in failures:
            print(f"iter208 correction guard failed: {failure}", file=sys.stderr)
        return 1
    mode = "preflight" if args.preflight else "final"
    print(f"iter208 post-seal forensic correction guard: {mode} pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
