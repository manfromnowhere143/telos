#!/usr/bin/env python3
"""Validate handoff consistency."""

from __future__ import annotations

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
REQUIRED_RECOVERY_FACTS = (
    "access authorization succeeded",
    "`53/53` solver calls",
    "`39/39` eligible scenario calls",
    "`50` model patches",
    "`38` extracted scenario programs",
    "one original absent scenario",
    "admitted `29` programs and rejected `9` with `21` findings",
    "Zero scenario execution and zero official-harness certification execution occurred",
    "scenario-safety protocol/execution null",
    "workflow run `29460393525`, attempt `1`",
    "all `50/50` first Docker `run`",
    "zero official certifications and zero scenarios executed",
    "exact daemon stderr was redirected into temporary files and not retained",
    "root cause is reconstructed",
    "execution-infrastructure null",
    "exactly two iter204 workflow records",
    "push parse-failure run `29465584664`",
    "push parse-failure run `29465924803`",
    "zero jobs and zero artifacts",
    "zero `workflow_dispatch` runs",
    "false to say that iter204 has zero workflow runs",
    "at least one locally observed dispatch API request returned HTTP `422`",
    "no run ID, no run attempt, and no public workflow-dispatch job or run log",
    "no provider process, container create/run invocation",
    "contributes no `N`, `k`, or `u`; those quantities are absent, not zero",
    "bf2062825e604d9439b0d29375d7e5219a1064ae4a33701efb74a62f81a59a45",
    "Never reconstruct that frozen manifest from the current tree",
    "empty complete iter205 all-event and dispatch histories",
    "transient read-only query failure before the request does not consume iter205's request allowance",
    "Once execution reaches the request command, never re-enter this block",
    "discovery poll timeout or temporarily absent run is not by itself a null",
    "No observation ever authorizes another request",
    "Any API rejection, parser record, authorization failure, smoke failure, shard failure, collector",
    "closes iter205 and requires iter206",
    "Never re-enter the dispatch block",
    "Never dispatch the frozen iter202, iter203, or iter204",
    "never redownload or rerun the workflow",
    "iter205-execute\t.github/workflows/iter205-execute.yml\tactive",
    'test "$ITER205_ALL_COUNT" -eq 0',
    'test "$ITER205_DISPATCH_COUNT" -eq 0',
    'gh workflow run iter205-execute.yml --ref master -f expected_primary_sha="$HEAD_SHA"',
    "actions/workflows/iter205-execute.yml/runs",
    "scripts/collect_iter205_execution.py check",
    "scripts/adjudicate_iter205_workflow_context_recovery.py",
    "scripts/run_iter205_workflow_context_recovery_blind_judge.py",
    "scripts/validate_iter204_pre_dispatch_null.py",
    "scripts/build_iter205_runtime_manifest.py --check",
    "scripts/validate_iter205_publication_safety.py --check",
    "scripts/validate_iter205_runtime_recovery.py",
)


def recovery_content_failures(handoff: str) -> list[str]:
    """Reject stale recovery state and any credential-identifying handoff text."""

    failures = []
    for fact in REQUIRED_RECOVERY_FACTS:
        if fact not in handoff:
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
        failures.append("HANDOFF.md describes access or account capacity as unavailable")
    if re.search(
        r"(?:^|[\s`])\.env(?:[\s`/]|$)|"
        r"\bcredential(?:s)?\s+(?:file|path|location)\b",
        handoff,
        re.IGNORECASE | re.MULTILINE,
    ):
        failures.append("HANDOFF.md names a credential location")
    if 'gh run rerun "$RUN_ID"' in handoff:
        failures.append("HANDOFF.md authorizes a forbidden workflow rerun")
    if "gh workflow run iter203-execute.yml" in handoff:
        failures.append("HANDOFF.md authorizes the sealed iter203 workflow")
    if "gh workflow run iter204-execute.yml" in handoff:
        failures.append("HANDOFF.md authorizes the sealed iter204 workflow")
    if handoff.count("gh workflow run iter205-execute.yml") != 1:
        failures.append("HANDOFF.md must contain exactly one iter205 dispatch command")
    for stale in (
        "## Exact Authorized Iter204 Dispatch",
        "scripts/collect_iter204_execution.py check",
        "scripts/adjudicate_iter204_infrastructure_recovery.py",
        "scripts/run_iter204_infrastructure_recovery_blind_judge.py",
    ):
        if stale in handoff:
            failures.append(f"HANDOFF.md retains stale iter204 operational instruction: {stale}")
    return failures


def worktree_changes_except_handoff(status: str) -> list[str]:
    """Return porcelain rows that cannot be caused by regenerating HANDOFF.md itself."""

    changes = []
    for row in status.splitlines():
        path = row[3:] if len(row) >= 4 else ""
        if path == "HANDOFF.md":
            continue
        changes.append(row)
    return changes


def declared_worktree_changes(handoff: str) -> list[str]:
    """Parse the exact porcelain snapshot recorded in the generated handoff."""

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
    """Return the immutable source branch from the repository-state block."""

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
    if (
        not source_branch.strip()
        or source_branch in {"HEAD", "main", "master"}
        or source_branch.startswith(("origin/", "refs/"))
        or source_branch != source_branch.strip()
    ):
        raise ValueError("HANDOFF.md source_branch must name a non-master feature branch")
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
    """Run one Git query and fail closed on a missing or invalid repository state."""

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
    """Return the exact checked-out commit, rejecting abbreviated or ambiguous output."""

    commit = git_output(["git", "rev-parse", "HEAD"])
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise RuntimeError(f"cannot verify repository HEAD commit: {commit!r}")
    return commit


def git_is_ancestor(ancestor: str, descendant: str) -> bool:
    """Return Git ancestry while distinguishing a clean miss from a query failure."""

    args = ["git", "merge-base", "--is-ancestor", ancestor, descendant]
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    diagnostic = result.stderr.strip() or result.stdout.strip() or "no diagnostic"
    raise RuntimeError(
        f"git query failed with exit {result.returncode}: {shlex.join(args)}: {diagnostic}"
    )


def publication_lineage_failures(
    state: dict[str, str], repository_branch: str, repository_commit: str
) -> list[str]:
    """Validate the only two refs authorized to carry one frozen source commit."""

    failures: list[str] = []
    git_output(["git", "check-ref-format", "--branch", state["source_branch"]])
    allowed_branches = {
        state["source_branch"],
        state["publication_target"],
    }
    if repository_branch not in allowed_branches:
        failures.append(
            "HANDOFF.md branch is outside its publication lineage: "
            f"source={state['source_branch']} target={state['publication_target']} "
            f"actual={repository_branch}"
        )
    if not git_is_ancestor(state["source_commit"], repository_commit):
        failures.append(
            "HANDOFF.md source_commit is not an ancestor of repository HEAD: "
            f"source_commit={state['source_commit']} HEAD={repository_commit}"
        )
    return failures


def main() -> int:
    failures: list[str] = []
    handoff = HANDOFF.read_text(encoding="utf-8")
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
        handoff_frozen_gate = frozen_matches[0]
        continuity_gate = continuity_matches[0]
        contract_frozen_gate = contract.get("frozen_upstream_gate")
        if handoff_frozen_gate != continuity_gate or contract_frozen_gate != continuity_gate:
            failures.append(
                "frozen upstream gate mismatch: "
                f"HANDOFF={handoff_frozen_gate} CONTINUITY={continuity_gate} "
                f"contract={contract_frozen_gate}"
            )
        if not (ROOT / handoff_frozen_gate).is_file():
            failures.append(f"frozen upstream gate file does not exist: {handoff_frozen_gate}")
        if len(handoff_matches) == 1 and handoff_matches[0] == handoff_frozen_gate:
            failures.append("active gate must be distinct from the frozen upstream gate")

    try:
        state = declared_repository_state(handoff)
        repository_branch = current_branch()
        repository_commit = current_commit()
        failures.extend(
            publication_lineage_failures(state, repository_branch, repository_commit)
        )
    except (RuntimeError, ValueError) as exc:
        failures.append(str(exc))

    try:
        status = git_output(["git", "status", "--short"])
        relevant_changes = worktree_changes_except_handoff(status)
        declared_changes = declared_worktree_changes(handoff)
        if declared_changes != relevant_changes:
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
