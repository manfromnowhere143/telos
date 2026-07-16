#!/usr/bin/env python3
"""Validate the generated TELOS handoff and its fail-closed run envelope."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys


ROOT = Path.cwd()
HANDOFF = ROOT / "HANDOFF.md"
CONTINUITY = ROOT / "CONTINUITY.md"
MISSION_CONTRACT = ROOT / "mission" / "loop.json"
REPOSITORY_DECLARATION = (
    "TELOS is a standalone repository. Resolve its root with "
    "`git rev-parse --show-toplevel`"
)
FORBIDDEN_WORKSPACE_LABEL = "a" + "web"
ITER207_BRANCH = "agent/iter207-claim-integrity-admission-recovery"
ITER208_BRANCH = "agent/iter208-post-seal-forensic-correction"
ITER208_HANDOFF_SCHEMA = "telos.iter208.handoff.v1"
ITER208_PREDECESSOR_SEAL = "f4ee0d5bcb3b4abee7ebf1683be5b9edda263c28"
ITER208_RECEIPT = (
    "experiments/iter208_post_seal_forensic_correction/proof/receipt_v2.json"
)
ITER209_BRANCH = "agent/iter209-publication-ci-recovery"
ITER209_HANDOFF_SCHEMA = "telos.iter209.handoff.v1"
ITER209_PREDECESSOR_SEAL = "a2c2863cf993cb6dd39d2fada8d58e4796929120"
ITER209_RECEIPT = "experiments/iter209_publication_ci_recovery/proof/receipt_v2.json"
ITER210_BRANCH = "agent/iter210-pr-synthetic-merge-recovery"
ITER210_HANDOFF_SCHEMA = "telos.iter210.handoff.v1"
ITER210_PREDECESSOR_SEAL = "91f9258730bf5520d86c9235d7ed2f03724ea103"
ITER210_RECEIPT = "experiments/iter210_pr_synthetic_merge_recovery/proof/receipt_v2.json"
ITER205_MERGE_COMMIT = "4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f"
ITER206_SEAL_COMMIT = "a2a05ef2ed05a0c457076f2bd5f1475507190685"
ITER207_SEAL_DIFF = (
    "M\tHANDOFF.md",
    "A\texperiments/iter207_claim_integrity_and_admission_recovery/"
    "proof/pre_execution_publication_safety.json",
    "A\texperiments/iter207_claim_integrity_and_admission_recovery/"
    "proof/raw/runtime_manifest.json",
)
ITER207_DERIVED_PATHS = tuple(row.split("\t", 1)[1] for row in ITER207_SEAL_DIFF)
ITER207_DISPATCH = "gh workflow run iter207-execute.yml"
ITER207_INPUTS = (
    '-f expected_primary_sha="$HEAD_SHA"',
    '-f expected_workflow_id="$ITER207_WORKFLOW_ID"',
    '-f expected_iter206_workflow_id="$ITER206_WORKFLOW_ID"',
    '-f expected_iter204_release_run_id="$ITER204_RELEASE_RUN_ID"',
    '-f expected_iter204_primary_run_id="$ITER204_PRIMARY_RUN_ID"',
)
REQUIRED_RECOVERY_FACTS = (
    "two-row closure snapshot",
    "`29465584664` and `29465924803`",
    "four-row iter205 admission baseline",
    "`29468669956` and `29468768706`",
    "zero jobs, zero artifacts",
    "HTTP `404`",
    "zero iter204 `workflow_dispatch` runs",
    "source PR `#7` merged as `4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f`",
    "`29468769187`, attempt `1`, completed successfully",
    "`314141096` is active",
    "zero all-event runs and zero dispatch runs",
    "pre-dispatch admission-history null",
    "No iter205 dispatch request was issued",
    "no dispatch API response or rejection exists",
    "iter205 contributes no `N`, `k`, or `u`; those quantities are absent, not zero",
    "`6d2216038c7e1f19337795be806bf77eb39150a9be119828bc2967ed160c72ba`",
    "Iter206 was sealed locally at source `e7c2ec28daa746dbcfb5812d3771ab981ff984c0`",
    "pre-publication claim-integrity null",
    "zero branch pushes, pull requests, merges, workflow runs, dispatch requests, provider calls",
    "Iter206 contributes no `N`, `k`, or `u`",
    "conservatively adjudicates conceptual novelty `FAIL`",
    "literal v1-specific falsifier trigger as indeterminate",
    "only `23` discarded iter152 IDs are decision-bound",
    "do not call all `139` discarded variants",
    "Of the iter192/iter195 correction pair, only iter195 is a strict protocol `FAIL`",
    "`$13.128090`, not a provider invoice",
    "rounded `$13.59` through-repair total includes diagnostic calls excluded from the score",
    "corpus is not independent semantic ground truth",
    "proof/claim_integrity_correction.json",
    "exactly two authenticated, read-only GitHub metadata GETs",
    "They made no remote mutation and contacted no model provider",
    "inherits one ShellCheck `SC2034` warning",
    "exact iter206-to-iter207 runtime-identity guard",
    "Iter207 is the active, separately versioned pre-publication/pre-dispatch correction and recovery",
    "`50` patches in the same order, eight shards, `29` admitted",
    "`1/24` confirmed lower, `7/24` worst-case missing upper",
    "`1/18` complete-case",
    "Push branch `agent/iter207-claim-integrity-admission-recovery` exactly once at its final tip",
    "Merge exactly once with a two-parent merge commit",
    "`4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f`",
    "missing, malformed, or seventh iter204",
    "empty iter205, iter206, and iter207 histories",
    "exact six-row iter204 admission snapshot",
    "exactly one successful release-branch",
    "`push` CI run and one successful release-branch `pull_request` CI run",
    "Once execution reaches the dispatch request line, never re-enter this block",
    "dispatch-request allowance is consumed when the command is entered",
    "A temporarily absent, queued, or in-progress",
    "No observation ever authorizes another dispatch request",
    "Never issue a second dispatch request, rerun, or replacement run",
    "scripts/audit_iter207_claim_integrity.py",
    "scripts/validate_iter206_pre_publication_null.py",
    "scripts/build_iter207_runtime_manifest.py --check",
    "scripts/validate_iter207_publication_safety.py --check",
    "scripts/validate_iter207_runtime_recovery.py",
    "scripts/collect_iter207_execution.py check",
    "scripts/adjudicate_iter207_claim_integrity_and_admission_recovery.py",
    "scripts/run_iter207_claim_integrity_and_admission_recovery_blind_judge.py",
    "## Iter207 Local Seal and Exact Pickup Boundary",
    "source commit A",
    "publication-safety receipt and then the runtime manifest",
    "seal commit B",
    "push A and B together",
    "Never regenerate it after that point",
    "workflow_history_payload()",
    "iter207-execute\t.github/workflows/iter207-execute.yml\tactive",
    'test "$ITER205_ALL_COUNT" -eq 0',
    'test "$ITER205_DISPATCH_COUNT" -eq 0',
    'test "$ITER206_ALL_COUNT" -eq 0',
    'test "$ITER206_DISPATCH_COUNT" -eq 0',
    'test "$ITER207_ALL_COUNT" -eq 0',
    'test "$ITER207_DISPATCH_COUNT" -eq 0',
    "iter206-execute\t.github/workflows/iter206-execute.yml\tactive",
    'workflow_history_payload "314113289"',
    "actions/runs/$ITER204_RUN_ID/attempts/1/jobs",
    "actions/runs/$ITER204_RUN_ID/artifacts",
    "verify py3.11\tsuccess",
    "verify py3.12\tsuccess",
    "verify_release_ci()",
    'RELEASE_PUSH_CI_RUN_ID="$(verify_release_ci push)"',
    'RELEASE_PULL_REQUEST_CI_RUN_ID="$(verify_release_ci pull_request)"',
    'test "$RELEASE_PUSH_CI_RUN_ID" != "$RELEASE_PULL_REQUEST_CI_RUN_ID"',
    '-f head_sha="$SECOND_PARENT"',
    "[.id,.conclusion,.event,.head_branch,.head_sha,.path,.run_attempt,.status,.head_repository.full_name] | @tsv",
    "completed\tmanfromnowhere143/telos",
    "[.total_count, (.workflow_runs | length)] | @tsv",
    "[.total_count, (.jobs | length)] | @tsv",
    ".jobs[] | [.name,.conclusion,.head_sha,.id,.run_attempt,.status,.html_url] | @tsv",
    'test "$html_url" = "https://github.com/$REPO/actions/runs/$run_id/job/$job_id"',
    "repos/$REPO/commits/$HEAD_SHA/check-runs",
    "PRIMARY_CHECK_HISTORY_COMPLETE",
    'PRIMARY_PY311_CHECK_ID="$(verify_primary_check \'verify py3.11\')"',
    'PRIMARY_PY312_CHECK_ID="$(verify_primary_check \'verify py3.12\')"',
    "github-actions",
    ITER207_DISPATCH,
    *ITER207_INPUTS,
)


def recovery_content_failures(handoff: str) -> list[str]:
    """Reject stale gates, unsafe retries, and sensitive-runtime details."""

    failures = []
    normalized_handoff = " ".join(handoff.split())
    for fact in REQUIRED_RECOVERY_FACTS:
        if " ".join(fact.split()) not in normalized_handoff:
            failures.append(f"HANDOFF.md is missing bounded recovery fact: {fact}")
    if re.search(r"\b[A-Z][A-Z0-9_]*(?:KEY|TOKEN|SECRET)\b", handoff):
        failures.append("HANDOFF.md names a credential variable")
    if re.search(
        r"\b(?:credentials?|credits?|billing|quota|authentication|authorization|access)\b"
        r".{0,80}\b(?:absent|missing|unavailable|not present|exhausted)\b|"
        r"\b(?:absent|missing|unavailable|not present|exhausted)\b.{0,80}"
        r"\b(?:credentials?|credits?|billing|quota|authentication|authorization|access)\b",
        handoff,
        re.IGNORECASE | re.DOTALL,
    ):
        failures.append("HANDOFF.md describes account or execution capacity as unavailable")
    if re.search(
        r"(?:^|[\s`])\.env(?:[\s`/]|$)|"
        r"\bcredential(?:s)?\s+(?:file|path|location)\b",
        handoff,
        re.IGNORECASE | re.MULTILINE,
    ):
        failures.append("HANDOFF.md names a credential location")
    if re.search(r"(?im)^[ \t]*gh[ \t]+run[ \t]+rerun(?:[ \t]|$)", handoff):
        failures.append("HANDOFF.md authorizes a forbidden workflow rerun")
    workflow_dispatches = re.findall(
        r"(?im)^[ \t]*gh[ \t]+workflow[ \t]+run"
        r"(?:(?:[ \t]+)|(?:[ \t]*\\\n[ \t]*))[^\n]*"
        r"\b(iter20[2-7]-execute\.ya?ml)\b",
        handoff,
    )
    workflow_dispatches.extend(
        re.findall(
            r"(?i)actions/workflows/[^\s`\"']*"
            r"\b(iter20[2-7]-execute\.ya?ml)\b/dispatches\b",
            handoff,
        )
    )
    workflow_dispatches = [workflow.casefold() for workflow in workflow_dispatches]
    predecessor_dispatches = [
        workflow for workflow in workflow_dispatches if workflow != "iter207-execute.yml"
    ]
    for workflow in sorted(set(predecessor_dispatches)):
        failures.append(f"HANDOFF.md authorizes a sealed predecessor workflow: {workflow}")
    if (
        handoff.count(ITER207_DISPATCH) != 1
        or workflow_dispatches.count("iter207-execute.yml") != 1
    ):
        failures.append("HANDOFF.md must contain exactly one iter207 dispatch command")
    for required_input in ITER207_INPUTS:
        if handoff.count(required_input) != 1:
            failures.append(
                "HANDOFF.md must bind exactly one iter207 dispatch input: "
                f"{required_input}"
            )
    try:
        dispatch_section = handoff[handoff.index("## Exact Authorized Iter207 Dispatch") :]
        dispatch_block_match = re.search(
            r"```bash\n(.*?)\n```", dispatch_section, re.DOTALL
        )
        if dispatch_block_match is None:
            raise ValueError
        dispatch_block = dispatch_block_match.group(1)
        dispatch_line = dispatch_block.index(ITER207_DISPATCH)
    except ValueError:
        dispatch_block = ""
        dispatch_line = -1
    for pre_dispatch_check in (
        "scripts/audit_iter207_claim_integrity.py --check",
        "scripts/validate_iter206_pre_publication_null.py",
        "scripts/build_iter207_runtime_manifest.py --check",
        "scripts/validate_iter207_publication_safety.py --check",
        "scripts/validate_iter207_runtime_recovery.py",
        "workflow_history_payload()",
        "[(.total_count | type), (.workflow_runs | type)] | @tsv",
        ".total_count == (.workflow_runs | length)",
        'ITER206_WORKFLOW_BINDING="$(gh api -X GET',
        'test "$ITER206_WORKFLOW_ID" != "314113289"',
        'test "$ITER206_WORKFLOW_ID" != "314141096"',
        'test "$ITER206_WORKFLOW_ID" != "$ITER207_WORKFLOW_ID"',
        'test "$ITER206_ALL_COUNT" -eq 0',
        'test "$ITER206_DISPATCH_COUNT" -eq 0',
        'test "$ITER207_ALL_COUNT" -eq 0',
        'test "$ITER207_DISPATCH_COUNT" -eq 0',
        'test "$ITER204_ALL_COUNT" -eq 6',
        'test "$ITER204_DISPATCH_COUNT" -eq 0',
        "verify_release_ci()",
        'RELEASE_PUSH_CI_RUN_ID="$(verify_release_ci push)"',
        'RELEASE_PULL_REQUEST_CI_RUN_ID="$(verify_release_ci pull_request)"',
        'test "$RELEASE_PUSH_CI_RUN_ID" != "$RELEASE_PULL_REQUEST_CI_RUN_ID"',
        "[.id,.conclusion,.event,.head_branch,.head_sha,.path,.run_attempt,.status,.head_repository.full_name] | @tsv",
        "completed\tmanfromnowhere143/telos",
        'run_payload="$(gh api -X GET "repos/$REPO/actions/workflows/ci.yml/runs"',
        'jobs_payload="$(gh api -X GET "repos/$REPO/actions/runs/$run_id/attempts/1/jobs"',
        'test "$html_url" = "https://github.com/$REPO/actions/runs/$run_id/job/$job_id"',
        "repos/$REPO/commits/$HEAD_SHA/check-runs",
        'test "$PRIMARY_CHECK_HISTORY_COMPLETE" -eq 1',
        'PRIMARY_PY311_CHECK_ID="$(verify_primary_check \'verify py3.11\')"',
        'PRIMARY_PY312_CHECK_ID="$(verify_primary_check \'verify py3.12\')"',
    ):
        if (
            dispatch_line < 0
            or dispatch_block.count(pre_dispatch_check) != 1
            or dispatch_block.index(pre_dispatch_check) >= dispatch_line
        ):
            failures.append(
                "HANDOFF.md must prove each exact invariant before dispatch: "
                f"{pre_dispatch_check}"
            )
    try:
        verification_section = handoff[handoff.index("## Verification Before Action") :]
    except ValueError:
        verification_section = ""
    if "python3 scripts/make_handoff.py" in verification_section:
        failures.append(
            "HANDOFF.md must not regenerate itself in post-seal verification"
        )
    for stale in (
        "## Exact Authorized Iter205 Dispatch",
        "## Exact Authorized Iter206 Dispatch",
        "scripts/collect_iter205_execution.py check",
        "scripts/adjudicate_iter205_workflow_context_recovery.py",
        "scripts/run_iter205_workflow_context_recovery_blind_judge.py",
        "scripts/collect_iter206_execution.py check",
        "scripts/adjudicate_iter206_admission_history_recovery.py",
        "scripts/run_iter206_admission_history_recovery_blind_judge.py",
    ):
        if stale in handoff:
            failures.append(f"HANDOFF.md retains stale predecessor instruction: {stale}")
    return failures


def worktree_changes_except_handoff(status: str) -> list[str]:
    """Return porcelain rows that cannot be caused by regenerating HANDOFF.md."""

    changes = []
    for row in status.splitlines():
        path = row[3:] if len(row) >= 4 else ""
        if path == "HANDOFF.md":
            continue
        changes.append(row)
    return changes


def declared_worktree_changes(handoff: str) -> list[str]:
    """Parse the exact porcelain snapshot recorded by the generated handoff."""

    matches = re.findall(
        r"^Working tree:\n\n```text\n(.*?)\n```$",
        handoff,
        re.MULTILINE | re.DOTALL,
    )
    if len(matches) != 1:
        raise ValueError("HANDOFF.md must record exactly one working-tree snapshot")
    snapshot = matches[0]
    return [] if snapshot == "clean" else snapshot.splitlines()


def declared_branch(handoff: str) -> str:
    return declared_repository_state(handoff)["source_branch"]


def declared_repository_state(handoff: str) -> dict[str, str]:
    """Parse and validate the exact publication lineage recorded by the handoff."""

    matches = re.findall(
        r"^## Repository State\n\n```text\n"
        r"source_branch: ([^\n]+)\n"
        r"source_commit: ([^\n]+)\n"
        r"publication_target: ([^\n]+)\n```$",
        handoff,
        re.MULTILINE,
    )
    if len(matches) != 1:
        raise ValueError("HANDOFF.md must record exactly one publication-lineage block")
    source_branch, source_commit, publication_target = matches[0]
    if source_branch != ITER207_BRANCH:
        raise ValueError(
            "HANDOFF.md source_branch must name the exact iter207 feature branch: "
            f"expected={ITER207_BRANCH} actual={source_branch}"
        )
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ValueError("HANDOFF.md source_commit must be a full lowercase Git commit id")
    if publication_target != "master":
        raise ValueError("HANDOFF.md publication_target must be master")
    return {
        "source_branch": source_branch,
        "source_commit": source_commit,
        "publication_target": publication_target,
    }


def git_output(args: list[str]) -> str:
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        diagnostic = result.stderr.strip() or result.stdout.strip() or "no diagnostic"
        raise RuntimeError(
            f"git query failed with exit {result.returncode}: {shlex.join(args)}: {diagnostic}"
        )
    return result.stdout.rstrip()


def current_branch() -> str:
    """Resolve an attached local branch or a GitHub Actions publication branch."""

    branch = git_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if branch == "HEAD" and os.environ.get("GITHUB_ACTIONS") == "true":
        branch = os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_REF_NAME", "")
    if not branch or "\n" in branch or branch == "HEAD":
        raise RuntimeError(f"cannot verify handoff branch from repository state: {branch!r}")
    return branch


def current_commit() -> str:
    commit = git_output(["git", "rev-parse", "HEAD"])
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise RuntimeError(f"cannot verify repository HEAD commit: {commit!r}")
    return commit


def publication_lineage_failures(
    state: dict[str, str], repository_branch: str, repository_commit: str
) -> list[str]:
    """Validate the exact iter206-seal -> source A -> seal B publication topology."""

    failures: list[str] = []
    git_output(["git", "check-ref-format", "--branch", state["source_branch"]])
    allowed = {state["source_branch"], state["publication_target"]}
    if repository_branch not in allowed:
        failures.append(
            "HANDOFF.md branch is outside its publication lineage: "
            f"source={state['source_branch']} target={state['publication_target']} "
            f"actual={repository_branch}"
        )
        return failures

    def parents(commit: str) -> list[str]:
        row = git_output(["git", "rev-list", "--parents", "-n", "1", commit]).split()
        if (
            not row
            or row[0] != commit
            or any(not re.fullmatch(r"[0-9a-f]{40}", value) for value in row)
        ):
            raise RuntimeError(f"cannot verify exact commit parents for {commit}")
        return row

    pull_request_merge = (
        repository_branch == state["source_branch"]
        and os.environ.get("GITHUB_ACTIONS") == "true"
        and os.environ.get("GITHUB_EVENT_NAME") == "pull_request"
    )
    if repository_branch == state["publication_target"] or pull_request_merge:
        merge_row = parents(repository_commit)
        if len(merge_row) != 3 or merge_row[1] != ITER205_MERGE_COMMIT:
            failures.append(
                "HANDOFF.md publication commit must be the exact two-parent iter207 "
                "merge over the frozen iter205 master"
            )
            return failures
        seal_commit = merge_row[2]
    else:
        seal_commit = repository_commit

    source_commit = state["source_commit"]
    source_row = parents(source_commit)
    if source_row != [source_commit, ITER206_SEAL_COMMIT]:
        failures.append(
            "HANDOFF.md source commit A must be the single direct child of the "
            f"frozen iter206 seal: source={source_commit}"
        )
    seal_row = parents(seal_commit)
    if seal_row != [seal_commit, source_commit]:
        failures.append(
            "HANDOFF.md seal commit B must be the single direct child of source "
            f"commit A: source={source_commit} seal={seal_commit}"
        )

    source_changed_paths = set(
        git_output(
            [
                "git",
                "diff",
                "--name-only",
                "--no-renames",
                ITER206_SEAL_COMMIT,
                source_commit,
            ]
        ).splitlines()
    )
    leaked_derived = sorted(source_changed_paths.intersection(ITER207_DERIVED_PATHS))
    if leaked_derived:
        failures.append(
            "HANDOFF.md source commit A changes derived seal paths: "
            + ", ".join(leaked_derived)
        )

    seal_diff = git_output(
        [
            "git",
            "diff",
            "--name-status",
            "--no-renames",
            source_commit,
            seal_commit,
        ]
    ).splitlines()
    if sorted(seal_diff) != sorted(ITER207_SEAL_DIFF):
        failures.append(
            "HANDOFF.md seal commit B must change exactly HANDOFF.md and the two "
            "iter207 derived records with exact statuses"
        )
    return failures


def iter208_declared_repository_state(handoff: str) -> dict[str, str]:
    """Parse the publication-only iter208 handoff identity block."""

    matches = re.findall(
        r"^## Repository State\n\n```text\n"
        r"handoff_schema: ([^\n]+)\n"
        r"source_branch: ([^\n]+)\n"
        r"source_commit: ([^\n]+)\n"
        r"predecessor_seal: ([^\n]+)\n"
        r"publication_target: ([^\n]+)\n```$",
        handoff,
        re.MULTILINE,
    )
    if len(matches) != 1:
        raise ValueError("HANDOFF.md must record exactly one iter208 repository-state block")
    schema, source_branch, source_commit, predecessor_seal, target = matches[0]
    if schema != ITER208_HANDOFF_SCHEMA:
        raise ValueError(f"HANDOFF.md iter208 schema differs: {schema}")
    if source_branch != ITER208_BRANCH:
        raise ValueError(f"HANDOFF.md iter208 source branch differs: {source_branch}")
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("HANDOFF.md iter208 source commit is not a full lowercase Git id")
    if predecessor_seal != ITER208_PREDECESSOR_SEAL:
        raise ValueError("HANDOFF.md iter208 predecessor seal differs")
    if target != "master":
        raise ValueError("HANDOFF.md iter208 publication target must be master")
    return {
        "source_branch": source_branch,
        "source_commit": source_commit,
        "predecessor_seal": predecessor_seal,
        "publication_target": target,
    }


def iter208_content_failures(handoff: str, contract: dict[str, object]) -> list[str]:
    """Check the bounded iter208 publication handoff without consulting Git."""

    failures: list[str] = []
    try:
        iter208_declared_repository_state(handoff)
    except ValueError as exc:
        failures.append(str(exc))
    if REPOSITORY_DECLARATION not in handoff:
        failures.append("HANDOFF.md does not declare the standalone TELOS repository")
    if FORBIDDEN_WORKSPACE_LABEL in handoff.casefold():
        failures.append("HANDOFF.md names an unrelated workspace")
    if re.search(r"\b[A-Z][A-Z0-9_]*(?:KEY|TOKEN|SECRET)\b", handoff):
        failures.append("HANDOFF.md names a credential variable")
    if re.search(r"(?:^|[\s`])\.env(?:[\s`/]|$)", handoff, re.IGNORECASE | re.MULTILINE):
        failures.append("HANDOFF.md names a credential location")
    if re.search(r"(?im)^[ \t]*gh[ \t]+(?:run[ \t]+rerun|workflow[ \t]+run)\b", handoff):
        failures.append("HANDOFF.md authorizes a workflow dispatch or rerun")

    required = (
        "Local correction status: **PASS; publication seal pending**.",
        "No provider call, GPU run, scientific container run, workflow dispatch, or release is authorized.",
        "TCP-1 remains design-only and unexecuted.",
        "Merge requires green non-scientific branch and pull-request CI at the unchanged seal tip.",
        "The receipt proves byte identity, not authorship, external chronology, or semantic truth.",
        "python3 scripts/validate_iter208_post_seal_forensic_correction.py",
        "python3 scripts/validate_handoff.py",
        "pytest -q",
    )
    normalized = " ".join(handoff.split())
    for fact in required:
        if " ".join(fact.split()) not in normalized:
            failures.append(f"HANDOFF.md is missing iter208 publication fact: {fact}")

    expected_runtime = contract.get("active_gate")
    expected_publication = contract.get("active_publication_gate")
    expected_frozen = contract.get("frozen_upstream_gate")
    if handoff.count(f"Active gate: `{expected_runtime}`") != 1:
        failures.append("HANDOFF.md does not bind the sealed runtime gate exactly once")
    if handoff.count(f"Active publication gate: `{expected_publication}`") != 1:
        failures.append("HANDOFF.md does not bind the active publication gate exactly once")
    frozen_line = (
        "Frozen upstream gate recorded by runtime-bound `CONTINUITY.md`: "
        f"`{expected_frozen}`"
    )
    if handoff.count(frozen_line) != 1:
        failures.append("HANDOFF.md does not bind the frozen upstream gate exactly once")
    return failures


def _git_bytes(args: list[str]) -> bytes:
    process = subprocess.run(args, capture_output=True, check=False)
    if process.returncode != 0:
        diagnostic = process.stderr.decode("utf-8", errors="replace").strip() or "no diagnostic"
        raise RuntimeError(
            f"git query failed with exit {process.returncode}: {shlex.join(args)}: {diagnostic}"
        )
    return process.stdout


def iter208_handoff_failures(handoff: str) -> list[str]:
    """Validate iter208 source custody and the exact one-file handoff seal."""

    failures: list[str] = []
    try:
        contract = json.loads(MISSION_CONTRACT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot load mission gate contract: {exc}"]
    if not isinstance(contract, dict):
        return ["mission gate contract root is not an object"]
    failures.extend(iter208_content_failures(handoff, contract))
    try:
        state = iter208_declared_repository_state(handoff)
    except ValueError:
        return failures

    source_commit = state["source_commit"]

    def parents(commit: str) -> list[str]:
        row = git_output(["git", "rev-list", "--parents", "-n", "1", commit]).split()
        if not row or row[0] != commit:
            raise RuntimeError(f"cannot resolve exact parents for {commit}")
        return row

    try:
        git_output(["git", "check-ref-format", "--branch", state["source_branch"]])
        if parents(source_commit) != [source_commit, ITER208_PREDECESSOR_SEAL]:
            failures.append("iter208 source commit A is not the direct child of the iter207 seal")

        receipt_path = ROOT / ITER208_RECEIPT
        if receipt_path.is_symlink() or not receipt_path.is_file():
            failures.append("iter208 source receipt is missing or symlinked")
        else:
            source_receipt = _git_bytes(["git", "show", f"{source_commit}:{ITER208_RECEIPT}"])
            if source_receipt != receipt_path.read_bytes():
                failures.append("iter208 receipt differs from source commit A")
            else:
                sys.path.insert(0, str(ROOT))
                from telos.proof import (  # noqa: PLC0415
                    ProofValidationError,
                    load_receipt_v2,
                )

                try:
                    receipt = load_receipt_v2(receipt_path, artifact_root=ROOT)
                except (OSError, ProofValidationError) as exc:
                    failures.append(f"iter208 source receipt does not verify: {exc}")
                else:
                    for item in receipt.evidence:
                        artifact = item["artifact"]
                        payload = _git_bytes(
                            ["git", "show", f"{source_commit}:{artifact['path']}"]
                        )
                        if len(payload) != artifact["bytes"] or (
                            hashlib.sha256(payload).hexdigest() != artifact["sha256"]
                        ):
                            failures.append(
                                "iter208 source Git blob differs from receipt: "
                                f"{artifact['path']}"
                            )
                    for line in (
                        f"Receipt evidence count: `{len(receipt.evidence)}`",
                        f"Receipt closure SHA-256: `{receipt.evidence_closure_sha256}`",
                        f"Receipt SHA-256: `{receipt.receipt_sha256}`",
                    ):
                        if handoff.count(line) != 1:
                            failures.append(f"HANDOFF.md does not bind receipt identity: {line}")

        repository_branch = current_branch()
        repository_commit = current_commit()
        status = git_output(["git", "status", "--short"])
        if repository_commit == source_commit:
            if repository_branch != state["source_branch"]:
                failures.append("iter208 pre-seal branch differs from the source branch")
            if worktree_changes_except_handoff(status):
                failures.append("iter208 pre-seal tree changes files other than HANDOFF.md")
            if "HANDOFF.md" not in status:
                failures.append("iter208 pre-seal mode requires a HANDOFF.md change")
        else:
            if repository_branch == state["source_branch"] and not (
                os.environ.get("GITHUB_ACTIONS") == "true"
                and os.environ.get("GITHUB_EVENT_NAME") == "pull_request"
            ):
                seal_commit = repository_commit
            elif repository_branch in {state["source_branch"], state["publication_target"]}:
                merge_row = parents(repository_commit)
                if len(merge_row) != 3:
                    failures.append("iter208 publication checkout is not a two-parent merge")
                    seal_commit = ""
                else:
                    seal_commit = merge_row[2]
            else:
                failures.append("iter208 repository branch is outside the publication lineage")
                seal_commit = ""
            if seal_commit:
                if parents(seal_commit) != [seal_commit, source_commit]:
                    failures.append("iter208 seal commit B is not the direct child of source commit A")
                seal_diff = git_output(
                    ["git", "diff", "--name-status", "--no-renames", source_commit, seal_commit]
                ).splitlines()
                if seal_diff != ["M\tHANDOFF.md"]:
                    failures.append("iter208 seal commit B must modify exactly HANDOFF.md")
            if status:
                failures.append("iter208 post-seal working tree is not clean")
    except (OSError, RuntimeError, ValueError) as exc:
        failures.append(str(exc))
    return failures


def iter209_declared_repository_state(handoff: str) -> dict[str, str]:
    """Parse the additive iter209 publication-recovery identity block."""

    matches = re.findall(
        r"^## Repository State\n\n```text\n"
        r"handoff_schema: ([^\n]+)\n"
        r"source_branch: ([^\n]+)\n"
        r"source_commit: ([^\n]+)\n"
        r"predecessor_seal: ([^\n]+)\n"
        r"publication_target: ([^\n]+)\n```$",
        handoff,
        re.MULTILINE,
    )
    if len(matches) != 1:
        raise ValueError("HANDOFF.md must record exactly one iter209 repository-state block")
    schema, source_branch, source_commit, predecessor_seal, target = matches[0]
    if schema != ITER209_HANDOFF_SCHEMA:
        raise ValueError(f"HANDOFF.md iter209 schema differs: {schema}")
    if source_branch != ITER209_BRANCH:
        raise ValueError(f"HANDOFF.md iter209 source branch differs: {source_branch}")
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("HANDOFF.md iter209 source commit is not a full lowercase Git id")
    if predecessor_seal != ITER209_PREDECESSOR_SEAL:
        raise ValueError("HANDOFF.md iter209 predecessor seal differs")
    if target != "master":
        raise ValueError("HANDOFF.md iter209 publication target must be master")
    return {
        "source_branch": source_branch,
        "source_commit": source_commit,
        "predecessor_seal": predecessor_seal,
        "publication_target": target,
    }


def iter209_content_failures(handoff: str, contract: dict[str, object]) -> list[str]:
    """Check that the iter209 handoff is publication-only and fail-closed."""

    failures: list[str] = []
    try:
        iter209_declared_repository_state(handoff)
    except ValueError as exc:
        failures.append(str(exc))
    if REPOSITORY_DECLARATION not in handoff:
        failures.append("HANDOFF.md does not declare the standalone TELOS repository")
    if FORBIDDEN_WORKSPACE_LABEL in handoff.casefold():
        failures.append("HANDOFF.md names an unrelated workspace")
    if re.search(r"\b[A-Z][A-Z0-9_]*(?:KEY|TOKEN|SECRET)\b", handoff):
        failures.append("HANDOFF.md names a credential variable")
    if re.search(r"(?im)^[ \t]*gh[ \t]+(?:run[ \t]+rerun|workflow[ \t]+run)\b", handoff):
        failures.append("HANDOFF.md authorizes a workflow dispatch or rerun")
    required = (
        "Local recovery status: **PASS; fresh publication seal pending**.",
        "The failed iter208 branch remains unchanged.",
        "No provider request, GPU run, scientific container run, workflow dispatch, release, or scientific execution is authorized.",
        "Merge requires green non-scientific push and pull-request CI at the unchanged iter209 seal tip.",
        "The receipt proves byte identity, not authorship, external chronology, or semantic truth.",
        "python3 scripts/build_iter209_receipt.py --check",
        "python3 scripts/validate_iter209_publication_ci_recovery.py",
        "python3 scripts/validate_handoff.py",
        "pytest -q",
    )
    normalized = " ".join(handoff.split())
    for fact in required:
        if " ".join(fact.split()) not in normalized:
            failures.append(f"HANDOFF.md is missing iter209 publication fact: {fact}")
    expected_runtime = contract.get("active_gate")
    expected_publication = contract.get("active_publication_gate")
    expected_frozen = contract.get("frozen_upstream_gate")
    if handoff.count(f"Active gate: `{expected_runtime}`") != 1:
        failures.append("HANDOFF.md does not bind the sealed runtime gate exactly once")
    if handoff.count(f"Active publication gate: `{expected_publication}`") != 1:
        failures.append("HANDOFF.md does not bind the active publication gate exactly once")
    frozen_line = (
        "Frozen upstream gate recorded by runtime-bound `CONTINUITY.md`: "
        f"`{expected_frozen}`"
    )
    if handoff.count(frozen_line) != 1:
        failures.append("HANDOFF.md does not bind the frozen upstream gate exactly once")
    return failures


def iter209_handoff_failures(handoff: str) -> list[str]:
    """Validate iter209 source custody and its exact one-file handoff seal."""

    failures: list[str] = []
    try:
        contract = json.loads(MISSION_CONTRACT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot load mission gate contract: {exc}"]
    if not isinstance(contract, dict):
        return ["mission gate contract root is not an object"]
    failures.extend(iter209_content_failures(handoff, contract))
    try:
        state = iter209_declared_repository_state(handoff)
    except ValueError:
        return failures

    source_commit = state["source_commit"]

    def parents(commit: str) -> list[str]:
        row = git_output(["git", "rev-list", "--parents", "-n", "1", commit]).split()
        if not row or row[0] != commit:
            raise RuntimeError(f"cannot resolve exact parents for {commit}")
        return row

    try:
        git_output(["git", "check-ref-format", "--branch", state["source_branch"]])
        if parents(source_commit) != [source_commit, ITER209_PREDECESSOR_SEAL]:
            failures.append("iter209 source commit is not the direct child of the iter208 seal")

        receipt_path = ROOT / ITER209_RECEIPT
        if receipt_path.is_symlink() or not receipt_path.is_file():
            failures.append("iter209 source receipt is missing or symlinked")
        else:
            source_receipt = _git_bytes(["git", "show", f"{source_commit}:{ITER209_RECEIPT}"])
            if source_receipt != receipt_path.read_bytes():
                failures.append("iter209 receipt differs from its source commit")
            else:
                sys.path.insert(0, str(ROOT))
                from telos.proof import ProofValidationError, load_receipt_v2  # noqa: PLC0415

                try:
                    receipt = load_receipt_v2(receipt_path, artifact_root=ROOT)
                except (OSError, ProofValidationError) as exc:
                    failures.append(f"iter209 source receipt does not verify: {exc}")
                else:
                    for item in receipt.evidence:
                        artifact = item["artifact"]
                        payload = _git_bytes(
                            ["git", "show", f"{source_commit}:{artifact['path']}"]
                        )
                        if len(payload) != artifact["bytes"] or (
                            hashlib.sha256(payload).hexdigest() != artifact["sha256"]
                        ):
                            failures.append(
                                "iter209 source Git blob differs from receipt: "
                                f"{artifact['path']}"
                            )
                    for line in (
                        f"Receipt evidence count: `{len(receipt.evidence)}`",
                        f"Receipt closure SHA-256: `{receipt.evidence_closure_sha256}`",
                        f"Receipt SHA-256: `{receipt.receipt_sha256}`",
                    ):
                        if handoff.count(line) != 1:
                            failures.append(f"HANDOFF.md does not bind receipt identity: {line}")

        repository_branch = current_branch()
        repository_commit = current_commit()
        status = git_output(["git", "status", "--short"])
        if repository_commit == source_commit:
            if repository_branch != state["source_branch"]:
                failures.append("iter209 pre-seal branch differs from the source branch")
            if worktree_changes_except_handoff(status):
                failures.append("iter209 pre-seal tree changes files other than HANDOFF.md")
            if "HANDOFF.md" not in status:
                failures.append("iter209 pre-seal mode requires a HANDOFF.md change")
        else:
            if repository_branch == state["source_branch"] and not (
                os.environ.get("GITHUB_ACTIONS") == "true"
                and os.environ.get("GITHUB_EVENT_NAME") == "pull_request"
            ):
                seal_commit = repository_commit
            elif repository_branch in {state["source_branch"], state["publication_target"]}:
                merge_row = parents(repository_commit)
                if len(merge_row) != 3:
                    failures.append("iter209 publication checkout is not a two-parent merge")
                    seal_commit = ""
                else:
                    seal_commit = merge_row[2]
            else:
                failures.append("iter209 repository branch is outside the publication lineage")
                seal_commit = ""
            if seal_commit:
                if parents(seal_commit) != [seal_commit, source_commit]:
                    failures.append("iter209 seal commit is not the direct child of its source commit")
                seal_diff = git_output(
                    ["git", "diff", "--name-status", "--no-renames", source_commit, seal_commit]
                ).splitlines()
                if seal_diff != ["M\tHANDOFF.md"]:
                    failures.append("iter209 seal commit must modify exactly HANDOFF.md")
            if status:
                failures.append("iter209 post-seal working tree is not clean")
    except (OSError, RuntimeError, ValueError) as exc:
        failures.append(str(exc))
    return failures


def iter210_declared_repository_state(handoff: str) -> dict[str, str]:
    """Parse the additive iter210 PR-topology recovery identity block."""

    matches = re.findall(
        r"^## Repository State\n\n```text\n"
        r"handoff_schema: ([^\n]+)\n"
        r"source_branch: ([^\n]+)\n"
        r"source_commit: ([^\n]+)\n"
        r"predecessor_seal: ([^\n]+)\n"
        r"publication_target: ([^\n]+)\n```$",
        handoff,
        re.MULTILINE,
    )
    if len(matches) != 1:
        raise ValueError("HANDOFF.md must record exactly one iter210 repository-state block")
    schema, source_branch, source_commit, predecessor_seal, target = matches[0]
    if schema != ITER210_HANDOFF_SCHEMA:
        raise ValueError(f"HANDOFF.md iter210 schema differs: {schema}")
    if source_branch != ITER210_BRANCH:
        raise ValueError(f"HANDOFF.md iter210 source branch differs: {source_branch}")
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("HANDOFF.md iter210 source commit is not a full lowercase Git id")
    if predecessor_seal != ITER210_PREDECESSOR_SEAL:
        raise ValueError("HANDOFF.md iter210 predecessor seal differs")
    if target != "master":
        raise ValueError("HANDOFF.md iter210 publication target must be master")
    return {
        "source_branch": source_branch,
        "source_commit": source_commit,
        "predecessor_seal": predecessor_seal,
        "publication_target": target,
    }


def iter210_content_failures(handoff: str, contract: dict[str, object]) -> list[str]:
    """Check that the iter210 handoff is publication-only and fail-closed."""

    failures: list[str] = []
    try:
        iter210_declared_repository_state(handoff)
    except ValueError as exc:
        failures.append(str(exc))
    if REPOSITORY_DECLARATION not in handoff:
        failures.append("HANDOFF.md does not declare the standalone TELOS repository")
    if FORBIDDEN_WORKSPACE_LABEL in handoff.casefold():
        failures.append("HANDOFF.md names an unrelated workspace")
    if re.search(r"\b[A-Z][A-Z0-9_]*(?:KEY|TOKEN|SECRET)\b", handoff):
        failures.append("HANDOFF.md names a credential variable")
    if re.search(r"(?im)^[ \t]*gh[ \t]+(?:run[ \t]+rerun|workflow[ \t]+run)\b", handoff):
        failures.append("HANDOFF.md authorizes a workflow dispatch or rerun")
    required = (
        "Local recovery status: **PASS; fresh publication seal pending**.",
        "The failed iter209 branch remains unchanged.",
        "No provider request, GPU run, scientific container run, workflow dispatch, release, or scientific execution is authorized.",
        "Merge requires green non-scientific push and pull-request CI at the unchanged iter210 seal tip.",
        "The receipt proves byte identity, not authorship, external chronology, or semantic truth.",
        "python3 scripts/build_iter210_receipt.py --check",
        "python3 scripts/validate_iter210_pr_synthetic_merge_recovery.py",
        "python3 scripts/validate_handoff.py",
        "pytest -q",
    )
    normalized = " ".join(handoff.split())
    for fact in required:
        if " ".join(fact.split()) not in normalized:
            failures.append(f"HANDOFF.md is missing iter210 publication fact: {fact}")
    if handoff.count(f"Active gate: `{contract.get('active_gate')}`") != 1:
        failures.append("HANDOFF.md does not bind the sealed runtime gate exactly once")
    if handoff.count(f"Active publication gate: `{contract.get('active_publication_gate')}`") != 1:
        failures.append("HANDOFF.md does not bind the active publication gate exactly once")
    frozen_line = (
        "Frozen upstream gate recorded by runtime-bound `CONTINUITY.md`: "
        f"`{contract.get('frozen_upstream_gate')}`"
    )
    if handoff.count(frozen_line) != 1:
        failures.append("HANDOFF.md does not bind the frozen upstream gate exactly once")
    return failures


def iter210_handoff_failures(handoff: str) -> list[str]:
    """Validate iter210 source custody across branch, PR merge, and merged-master modes."""

    failures: list[str] = []
    try:
        contract = json.loads(MISSION_CONTRACT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot load mission gate contract: {exc}"]
    if not isinstance(contract, dict):
        return ["mission gate contract root is not an object"]
    failures.extend(iter210_content_failures(handoff, contract))
    try:
        state = iter210_declared_repository_state(handoff)
    except ValueError:
        return failures
    source = state["source_commit"]

    def parents(commit: str) -> list[str]:
        row = git_output(["git", "rev-list", "--parents", "-n", "1", commit]).split()
        if not row or row[0] != commit:
            raise RuntimeError(f"cannot resolve exact parents for {commit}")
        return row

    try:
        git_output(["git", "check-ref-format", "--branch", state["source_branch"]])
        if parents(source) != [source, ITER210_PREDECESSOR_SEAL]:
            failures.append("iter210 source is not the direct child of the iter209 seal")

        receipt_path = ROOT / ITER210_RECEIPT
        if receipt_path.is_symlink() or not receipt_path.is_file():
            failures.append("iter210 source receipt is missing or symlinked")
        else:
            source_receipt = _git_bytes(["git", "show", f"{source}:{ITER210_RECEIPT}"])
            if source_receipt != receipt_path.read_bytes():
                failures.append("iter210 receipt differs from source commit")
            else:
                sys.path.insert(0, str(ROOT))
                from telos.proof import ProofValidationError, validate_receipt_v2  # noqa: PLC0415

                try:
                    receipt = validate_receipt_v2(json.loads(source_receipt.decode("utf-8")))
                except (UnicodeDecodeError, json.JSONDecodeError, ProofValidationError) as exc:
                    failures.append(f"iter210 source receipt does not verify: {exc}")
                else:
                    for item in receipt.evidence:
                        artifact = item["artifact"]
                        payload = _git_bytes(["git", "show", f"{source}:{artifact['path']}"])
                        if len(payload) != artifact["bytes"] or (
                            hashlib.sha256(payload).hexdigest() != artifact["sha256"]
                        ):
                            failures.append(
                                "iter210 source Git blob differs from receipt: "
                                f"{artifact['path']}"
                            )
                    for line in (
                        f"Receipt evidence count: `{len(receipt.evidence)}`",
                        f"Receipt closure SHA-256: `{receipt.evidence_closure_sha256}`",
                        f"Receipt SHA-256: `{receipt.receipt_sha256}`",
                    ):
                        if handoff.count(line) != 1:
                            failures.append(f"HANDOFF.md does not bind receipt identity: {line}")

        repository_commit = current_commit()
        status = git_output(["git", "status", "--short"])
        if repository_commit == source:
            if current_branch() != state["source_branch"]:
                failures.append("iter210 pre-seal branch differs from source branch")
            if worktree_changes_except_handoff(status):
                failures.append("iter210 pre-seal tree changes files other than HANDOFF.md")
            if "HANDOFF.md" not in status:
                failures.append("iter210 pre-seal mode requires a HANDOFF.md change")
        else:
            head_row = parents(repository_commit)
            candidates = [repository_commit, *head_row[1:]]
            seal = ""
            for candidate in candidates:
                if parents(candidate) == [candidate, source]:
                    seal = candidate
                    break
            if not seal:
                failures.append("cannot resolve iter210 seal from publication checkout topology")
            else:
                seal_diff = git_output(
                    ["git", "diff", "--name-status", "--no-renames", source, seal]
                ).splitlines()
                if seal_diff != ["M\tHANDOFF.md"]:
                    failures.append("iter210 seal must modify exactly HANDOFF.md")
            if status:
                failures.append("iter210 post-seal working tree is not clean")
    except (OSError, RuntimeError, ValueError) as exc:
        failures.append(str(exc))
    return failures


def main() -> int:
    failures: list[str] = []
    handoff = HANDOFF.read_text(encoding="utf-8")
    if f"handoff_schema: {ITER210_HANDOFF_SCHEMA}" in handoff:
        failures.extend(iter210_handoff_failures(handoff))
        if failures:
            print("handoff guard failed:")
            for failure in failures:
                print(f" - {failure}")
            return 1
        print("handoff guard: clean iter210 PR-topology recovery seal")
        return 0
    if f"handoff_schema: {ITER209_HANDOFF_SCHEMA}" in handoff:
        failures.extend(iter209_handoff_failures(handoff))
        if failures:
            print("handoff guard failed:")
            for failure in failures:
                print(f" - {failure}")
            return 1
        print("handoff guard: clean iter209 publication-recovery seal")
        return 0
    if f"handoff_schema: {ITER208_HANDOFF_SCHEMA}" in handoff:
        failures.extend(iter208_handoff_failures(handoff))
        if failures:
            print("handoff guard failed:")
            for failure in failures:
                print(f" - {failure}")
            return 1
        print("handoff guard: clean iter208 publication seal")
        return 0
    continuity = CONTINUITY.read_text(encoding="utf-8")
    try:
        contract = json.loads(MISSION_CONTRACT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"cannot load mission gate contract: {exc}")
        contract = {}

    if REPOSITORY_DECLARATION not in handoff:
        failures.append("HANDOFF.md does not declare the standalone TELOS repository")
    if FORBIDDEN_WORKSPACE_LABEL in handoff.casefold():
        failures.append("HANDOFF.md names an unrelated workspace")
    failures.extend(recovery_content_failures(handoff))

    handoff_matches = re.findall(r"Active gate: `([^`]+)`", handoff)
    frozen_matches = re.findall(
        r"Frozen upstream gate recorded by runtime-bound `CONTINUITY\.md`: `([^`]+)`",
        handoff,
    )
    continuity_matches = re.findall(r"Current gate:\n\n- `([^`]+)`", continuity)
    if len(handoff_matches) != 1:
        failures.append("HANDOFF.md must name exactly one active gate")
    if len(continuity_matches) != 1:
        failures.append("CONTINUITY.md must name exactly one current gate")
    if len(frozen_matches) != 1:
        failures.append("HANDOFF.md must name exactly one frozen upstream gate")

    if len(handoff_matches) == 1:
        handoff_gate = handoff_matches[0]
        contract_gate = contract.get("active_gate")
        if handoff_gate != contract_gate:
            failures.append(
                f"active gate mismatch: HANDOFF={handoff_gate} contract={contract_gate}"
            )
        if not (ROOT / handoff_gate).is_file():
            failures.append(f"active gate file does not exist: {handoff_gate}")

    if len(frozen_matches) == 1 and len(continuity_matches) == 1:
        handoff_frozen = frozen_matches[0]
        continuity_gate = continuity_matches[0]
        contract_frozen = contract.get("frozen_upstream_gate")
        if handoff_frozen != continuity_gate or contract_frozen != continuity_gate:
            failures.append(
                "frozen upstream gate mismatch: "
                f"HANDOFF={handoff_frozen} CONTINUITY={continuity_gate} "
                f"contract={contract_frozen}"
            )
        if not (ROOT / handoff_frozen).is_file():
            failures.append(f"frozen upstream gate file does not exist: {handoff_frozen}")
        if len(handoff_matches) == 1 and handoff_matches[0] == handoff_frozen:
            failures.append("active gate must differ from the frozen upstream gate")

    try:
        state = declared_repository_state(handoff)
        failures.extend(
            publication_lineage_failures(state, current_branch(), current_commit())
        )
    except (RuntimeError, ValueError) as exc:
        failures.append(str(exc))

    try:
        status = git_output(["git", "status", "--short"])
        if declared_worktree_changes(handoff) != worktree_changes_except_handoff(status):
            failures.append("HANDOFF.md working-tree snapshot does not exactly match git status")
    except (RuntimeError, ValueError) as exc:
        failures.append(str(exc))

    if failures:
        print("handoff guard failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1
    print("handoff guard: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
