#!/usr/bin/env python3
"""Validate the generated TELOS handoff and its fail-closed run envelope."""

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
ITER206_DISPATCH = "gh workflow run iter206-execute.yml"
ITER206_INPUTS = (
    '-f expected_primary_sha="$HEAD_SHA"',
    '-f expected_workflow_id="$ITER206_WORKFLOW_ID"',
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
    "No credential, credit, billing, quota, or authentication deficit is the iter205/iter206 blocker",
    "`6d2216038c7e1f19337795be806bf77eb39150a9be119828bc2967ed160c72ba`",
    "Iter206 is the active, separately versioned pre-publication/pre-dispatch recovery",
    "`1/24` confirmed lower, `7/24` worst-case missing upper",
    "`1/18` complete-case",
    "Push branch `agent/iter206-iter205-admission-recovery` exactly once at its final tip",
    "Merge exactly once with a two-parent merge commit",
    "`4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f`",
    "missing, malformed, or seventh iter204",
    "empty iter205 and iter206 histories",
    "exact six-row iter204 admission snapshot",
    "exactly one successful release-branch",
    "`push` CI run and one successful release-branch `pull_request` CI run",
    "Once execution reaches the dispatch request line, never re-enter this block",
    "dispatch-request allowance is consumed when the command is entered",
    "A temporarily absent, queued, or in-progress",
    "No observation ever authorizes another dispatch request",
    "Never issue a second dispatch request, rerun, or replacement run",
    "scripts/validate_iter205_pre_dispatch_null.py",
    "scripts/build_iter206_runtime_manifest.py --check",
    "scripts/validate_iter206_publication_safety.py --check",
    "scripts/validate_iter206_runtime_recovery.py",
    "scripts/collect_iter206_execution.py check",
    "scripts/adjudicate_iter206_admission_history_recovery.py",
    "scripts/run_iter206_admission_history_recovery_blind_judge.py",
    "## Iter206 Local Seal and Exact Pickup Boundary",
    "source commit A",
    "publication-safety receipt and then the runtime manifest",
    "seal commit B",
    "push A and B together",
    "Never regenerate it after that point",
    "iter206-execute\t.github/workflows/iter206-execute.yml\tactive",
    'test "$ITER205_ALL_COUNT" -eq 0',
    'test "$ITER205_DISPATCH_COUNT" -eq 0',
    'test "$ITER206_ALL_COUNT" -eq 0',
    'test "$ITER206_DISPATCH_COUNT" -eq 0',
    "actions/workflows/314113289/runs",
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
    ITER206_DISPATCH,
    *ITER206_INPUTS,
)


def recovery_content_failures(handoff: str) -> list[str]:
    """Reject stale gates, unsafe retries, and credential-identifying text."""

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
        failures.append("HANDOFF.md describes account or execution capacity as unavailable")
    if re.search(
        r"(?:^|[\s`])\.env(?:[\s`/]|$)|"
        r"\bcredential(?:s)?\s+(?:file|path|location)\b",
        handoff,
        re.IGNORECASE | re.MULTILINE,
    ):
        failures.append("HANDOFF.md names a credential location")
    if 'gh run rerun "$RUN_ID"' in handoff:
        failures.append("HANDOFF.md authorizes a forbidden workflow rerun")
    for iteration in ("iter202", "iter203", "iter204", "iter205"):
        command = f"gh workflow run {iteration}-execute.yml"
        if command in handoff:
            failures.append(f"HANDOFF.md authorizes the sealed {iteration} workflow")
    if handoff.count(ITER206_DISPATCH) != 1:
        failures.append("HANDOFF.md must contain exactly one iter206 dispatch command")
    for required_input in ITER206_INPUTS:
        if handoff.count(required_input) != 1:
            failures.append(
                "HANDOFF.md must bind exactly one iter206 dispatch input: "
                f"{required_input}"
            )
    try:
        dispatch_section = handoff[handoff.index("## Exact Authorized Iter206 Dispatch") :]
        dispatch_line = dispatch_section.index(ITER206_DISPATCH)
    except ValueError:
        dispatch_section = ""
        dispatch_line = -1
    for release_check in (
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
            or dispatch_section.count(release_check) != 1
            or dispatch_section.index(release_check) >= dispatch_line
        ):
            failures.append(
                "HANDOFF.md must prove the exact release CI pair before dispatch: "
                f"{release_check}"
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
        "scripts/collect_iter205_execution.py check",
        "scripts/adjudicate_iter205_workflow_context_recovery.py",
        "scripts/run_iter205_workflow_context_recovery_blind_judge.py",
    ):
        if stale in handoff:
            failures.append(f"HANDOFF.md retains stale iter205 operational instruction: {stale}")
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


def git_is_ancestor(ancestor: str, descendant: str) -> bool:
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
    """Validate the only refs authorized to carry the frozen source ancestry."""

    failures: list[str] = []
    git_output(["git", "check-ref-format", "--branch", state["source_branch"]])
    allowed = {state["source_branch"], state["publication_target"]}
    if repository_branch not in allowed:
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
