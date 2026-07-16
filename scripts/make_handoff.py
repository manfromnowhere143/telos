#!/usr/bin/env python3
"""Generate the fail-closed TELOS mission handoff from repository state."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import re
import shlex
import subprocess


ITER203_RUN_ID = "29460393525"
ITER203_RUN_ATTEMPT = "1"
ITER204_WORKFLOW_ID = "314113289"
ITER204_FEATURE_PUSH_RUN_ID = "29465584664"
ITER204_FEATURE_PUSH_COMMIT = "8342315dd2fa7ec865bd7c654ec4ec098675dfab"
ITER204_PRIMARY_PUSH_RUN_ID = "29465924803"
ITER204_MERGE_COMMIT = "c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446"
ITER204_RUNTIME_MANIFEST_SHA256 = (
    "bf2062825e604d9439b0d29375d7e5219a1064ae4a33701efb74a62f81a59a45"
)
ITER205_PULL_REQUEST = "7"
ITER205_FEATURE_COMMIT = "a336b4909329d392f6db5f6098792e07a17f28cb"
ITER205_MERGE_COMMIT = "4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f"
ITER205_PRIMARY_CI_RUN_ID = "29468769187"
ITER205_WORKFLOW_ID = "314141096"
ITER205_FEATURE_PUSH_RUN_ID = "29468669956"
ITER205_PRIMARY_PUSH_RUN_ID = "29468768706"
ITER205_PUBLIC_MANIFEST_SHA256 = (
    "6d2216038c7e1f19337795be806bf77eb39150a9be119828bc2967ed160c72ba"
)
ITER207_BRANCH = "agent/iter207-claim-integrity-admission-recovery"


def repository_banner() -> str:
    return (
        "TELOS is a standalone repository. Resolve its root with "
        "`git rev-parse --show-toplevel`, then run every TELOS command from that root."
    )


def run(args: list[str]) -> str:
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        diagnostic = result.stderr.strip() or result.stdout.strip() or "no diagnostic"
        raise RuntimeError(
            f"command failed with exit {result.returncode}: {shlex.join(args)}: {diagnostic}"
        )
    return result.stdout.rstrip()


def current_branch() -> str:
    """Return one attached branch name or fail on ambiguous source state."""

    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if not branch or "\n" in branch or branch == "HEAD":
        raise RuntimeError(f"cannot generate handoff from branch state: {branch!r}")
    return branch


def current_commit() -> str:
    commit = run(["git", "rev-parse", "HEAD"])
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise RuntimeError(f"cannot resolve an immutable source commit: {commit!r}")
    return commit


def source_provenance(branch: str) -> tuple[str, str]:
    """Bind the one allowed generation to the exact iter207 source branch."""

    if branch != ITER207_BRANCH:
        raise RuntimeError(
            "handoff generation is allowed only on the exact iter207 source branch: "
            f"expected={ITER207_BRANCH} actual={branch}"
        )
    return branch, current_commit()


def normalize_worktree_status(raw_status: str) -> str:
    """Exclude the generator's own HANDOFF.md rewrite from the status snapshot."""

    lines = []
    for line in raw_status.splitlines():
        parts = line.split(maxsplit=1)
        path = line[3:] if len(line) >= 4 and line[2] == " " else ""
        if not path and len(parts) == 2:
            path = parts[1]
        if path == "HANDOFF.md":
            continue
        lines.append(line)
    return "\n".join(lines) or "clean"


def experiment_status(gate: str) -> list[str]:
    rows = []
    active_experiment = Path(gate).parent
    for path in sorted(Path("experiments").glob("iter*/")):
        result = path / "RESULT.md"
        hypothesis = path / "HYPOTHESIS.md"
        if result.exists():
            result_head = result.read_text(encoding="utf-8")[:2000]
            if re.search(r"^status:\s*[`*_]*fail\b", result_head, re.IGNORECASE | re.MULTILINE):
                status = "RESULT RECORDED (FAIL)"
            elif re.search(
                r"^status:.*\b(?:null|unpublished|without publication)\b",
                result_head,
                re.IGNORECASE | re.MULTILINE,
            ):
                status = "RESULT RECORDED (TERMINAL NULL; publication not implied)"
            else:
                status = "RESULT RECORDED (publication not implied)"
        elif path == active_experiment and hypothesis.exists():
            status = "HYPOTHESIS ACTIVE, result pending"
        elif hypothesis.exists():
            status = "HYPOTHESIS ONLY (inactive or superseded)"
        else:
            status = "artifacts only"
        rows.append(f"- {path.as_posix().rstrip('/')}: {status}")
    return rows


def frozen_upstream_gate() -> str:
    """Return the runtime-bound upstream gate retained by CONTINUITY.md."""

    continuity = Path("CONTINUITY.md").read_text(encoding="utf-8")
    matches = re.findall(r"Current gate:\n\n- `([^`]+)`", continuity)
    if len(matches) != 1:
        raise RuntimeError("CONTINUITY.md does not declare exactly one current gate")
    continuity_gate = matches[0]
    contract = json.loads(Path("mission/loop.json").read_text(encoding="utf-8"))
    if contract.get("frozen_upstream_gate") != continuity_gate:
        raise RuntimeError("CONTINUITY.md and mission/loop.json frozen gates disagree")
    if not Path(continuity_gate).is_file():
        raise RuntimeError(f"frozen upstream gate does not exist: {continuity_gate}")
    return continuity_gate


def active_gate() -> str:
    """Return the additive current gate without mutating the frozen upstream gate."""

    upstream_gate = frozen_upstream_gate()
    contract = json.loads(Path("mission/loop.json").read_text(encoding="utf-8"))
    contract_gate = contract.get("active_gate")
    if not isinstance(contract_gate, str) or not Path(contract_gate).is_file():
        raise RuntimeError(f"active gate does not exist: {contract_gate}")
    if contract_gate == upstream_gate:
        raise RuntimeError("active recovery gate must differ from its frozen upstream gate")
    return contract_gate


def render_handoff(
    *,
    generated: str,
    source_branch: str,
    source_commit: str,
    worktree: str,
    experiments: str,
    gate: str,
    upstream_gate: str,
) -> str:
    """Render the handoff with literal shell syntax and explicit substitutions."""

    content = """# HANDOFF - dynamic state snapshot

Generated: @@GENERATED@@ by `scripts/make_handoff.py`. Read the Current Gate section first.

@@REPOSITORY_BANNER@@

## Repository State

```text
source_branch: @@SOURCE_BRANCH@@
source_commit: @@SOURCE_COMMIT@@
publication_target: master
```

Working tree:

```text
@@WORKTREE@@
```

## Experiments

@@EXPERIMENTS@@

## Current Gate

- Active gate: `@@ACTIVE_GATE@@`.
- Frozen upstream gate recorded by runtime-bound `CONTINUITY.md`: `@@UPSTREAM_GATE@@`. It remains an
  immutable historical authority; it is not the current execution instruction.
- Iter202 stopped at its static-safety boundary after producing the fixed provider corpus. No scenario or
  official-harness execution occurred, so it is a safety-protocol null with no `N`, `k`, or `u`.
- Iter203's sole canonical workflow run `@@ITER203_RUN_ID@@`, attempt `@@ITER203_RUN_ATTEMPT@@`, failed at
  the first container invocation on every row. It is a sealed execution-infrastructure null; never rerun it.
- The frozen iter204 public-null artifact is a **two-row closure snapshot** containing parse-failure runs
  `@@ITER204_FEATURE_PUSH_RUN_ID@@` and `@@ITER204_PRIMARY_PUSH_RUN_ID@@`. That artifact remains exact
  historical evidence and must not be rewritten merely because the server's append-only history grew.
- At the later iter205 admission gate, the live iter204 history was a **four-row iter205 admission baseline**.
  Rows `1..2` were the frozen closure rows; rows `3..4` were publication parse failures
  `@@ITER205_FEATURE_PUSH_RUN_ID@@` and `@@ITER205_PRIMARY_PUSH_RUN_ID@@`. All four were attempt-`1` push
  failures at the invalid iter204 workflow path with zero jobs, zero artifacts, unavailable logs reported as
  HTTP `404`, and zero iter204 `workflow_dispatch` runs.
- Iter205 source PR `#@@ITER205_PULL_REQUEST@@` merged as `@@ITER205_MERGE_COMMIT@@`; primary CI run
  `@@ITER205_PRIMARY_CI_RUN_ID@@`, attempt `1`, completed successfully. Workflow object
  `@@ITER205_WORKFLOW_ID@@` is active at exact name/path `iter205-execute` /
  `.github/workflows/iter205-execute.yml`, with zero all-event runs and zero dispatch runs.
- Iter205 is a **pre-dispatch admission-history null**: its read-only gate expected two iter204 rows and found
  four. No iter205 dispatch request was issued, and no dispatch API response or rejection exists. No iter205
  workflow run or downstream scientific process occurred,
  and iter205 contributes no `N`, `k`, or `u`; those quantities are absent, not zero. Preserve its terminal
  receipt, public metadata manifest `@@ITER205_PUBLIC_MANIFEST_SHA256@@`, learning record, and frozen source.
- Iter206 was sealed locally at source `e7c2ec28daa746dbcfb5812d3771ab981ff984c0` and seal
  `a2a05ef2ed05a0c457076f2bd5f1475507190685`, then stopped as a **pre-publication claim-integrity null**.
  It made zero branch pushes, pull requests, merges, workflow runs, dispatch requests, provider calls,
  containers, or scientific executions. Iter206 contributes no `N`, `k`, or `u`. Never publish iter206 as
  an active gate, dispatch or rerun its workflow, or mutate its frozen bytes. Its terminal-null evidence may
  travel only as immutable predecessor provenance inside iter207.
- Iter206 flagged an apparent iter192 prior-baseline contradiction; iter207's deeper patch-custody audit
  conservatively adjudicates conceptual novelty `FAIL` while recording the literal v1-specific falsifier
  trigger as indeterminate. Retain iter192's exact `40/40` construct correction and the bounded count of
  `139` harness-resolved hack-tagged evaluations across `65` instance IDs; only `23` discarded iter152 IDs
  are decision-bound (`17` overlap), so do not call all `139` discarded variants. Of the iter192/iter195
  correction pair, only iter195 is a strict protocol `FAIL`; retain its ten clean rows only as exploratory,
  gold-and-variant-hunk-assisted single-scenario reference differentials. Iter196 is partial/protocol-blocked;
  iter199 is post-provider/pre-execution rather than independently preregistered. The `22`-row construction
  corpus is not independent semantic ground truth. The canonical machine ledger is
  `experiments/iter207_claim_integrity_and_admission_recovery/proof/claim_integrity_correction.json`.
- The iter207 integrity audit made exactly two authenticated, read-only GitHub metadata GETs to verify
  historical CI projection semantics. They made no remote mutation and contacted no model provider.
- `scripts/ci_iter207_smoke.sh` inherits one ShellCheck `SC2034` warning for the parsed-but-unused `behavior`
  manifest column. Exclude only `SC2034` when linting that frozen successor: changing the script would break
  the exact iter206-to-iter207 runtime-identity guard.
- The unrepaired iter179 `17/40` score uses `240` score-producing calls with a conservative estimated spend
  guard of `$13.128090`, not a provider invoice. The rounded `$13.59` through-repair total includes
  diagnostic calls excluded from the score and must never be attributed to it.
- Iter207 is the active, separately versioned pre-publication/pre-dispatch correction and recovery. Scientific
  inputs and runtime semantics remain frozen: `50` patches in the same order, eight shards, `29` admitted
  witnesses, `9` rejected witnesses with `21` findings, one absent witness, and unchanged certification,
  scenario, missingness, adjudication, and blind-judge rules.
- The corrected iter200 convenience sample remains exploratory and nonrandom, with `N=24`, `k=1`, and `u=6`.
  Report its descriptive sensitivities together as `1/24` confirmed lower, `7/24` worst-case missing upper,
  and `1/18` complete-case; the historical `1/15` is scenario-eligible chronology only.
- The detector correction remains binding: iter197 and iter201 are protocol `FAIL`; the property instrument
  is a locator-assisted, gold-validated property pipeline, not an independently gold-free detector. Iter201
  retains judge catches `20/22`, `8/88` response nondecisions, paired-gold sensitivities `3/22` observed
  lower, `6/22` missing upper, and `3/19` complete-case; property catches are `6/22`, all within the judge set.
- Current local guards are `scripts/audit_iter207_claim_integrity.py`,
  `scripts/validate_iter206_pre_publication_null.py`,
  `scripts/build_iter207_runtime_manifest.py`, `scripts/validate_iter207_publication_safety.py`, and
  `scripts/validate_iter207_runtime_recovery.py`. The execution path is bound to
  `scripts/collect_iter207_execution.py`, `scripts/adjudicate_iter207_claim_integrity_and_admission_recovery.py`, and
  `scripts/run_iter207_claim_integrity_and_admission_recovery_blind_judge.py`.
- Never dispatch or operationally re-enter iter202, iter203, iter204, iter205, or iter206. Never issue a workflow
  rerun. Missing infrastructure evidence is never a negative scientific outcome.
- No population-frequency, model-comparison, leaderboard, deployment, or state-of-the-art claim is authorized.

## Iter207 Local Seal and Exact Pickup Boundary

Before any remote action, complete one exact two-commit local seal. First finish and validate every mutable
source, test, documentation, and evidence byte, then create source commit A without `HANDOFF.md` or the two
not-yet-generated iter207 derived records. From that clean source commit A, generate `HANDOFF.md` exactly once.
Never regenerate it after that point. Generate the publication-safety receipt and then the runtime manifest,
validate the sealed bytes without invoking the handoff generator, and create seal commit B containing exactly
`HANDOFF.md` plus those two derived records. Require a clean tree, then push A and B together in the single
allowed branch publication.

A new session must inspect the local history and guards before acting. If clean seal commit B exists and both
derived records reproduce, the exact pickup boundary is the one-push publication envelope below; do not
regenerate any seal byte. If B is absent or incomplete, finish the local seal without remote or provider action.

## Iter207 One-Push Publication Envelope

Finalize and adversarially review every iter207 source, test, documentation, runtime, and handoff byte
locally before publication. Push branch `@@ITER207_BRANCH@@` exactly once at its final tip. Make no later
source push, update-branch action, rebase, force-push, or remote branch mutation. The branch and pull-request
CI pair must pass at attempt `1`; a failure requiring changed bytes closes iter207 rather than authorizing a
second push.

Merge exactly once with a two-parent merge commit—never squash or rebase. The merge's first parent must be
`@@ITER205_MERGE_COMMIT@@`, and its second parent must be the single final release-branch tip. The resulting
master commit must pass one exact attempt-`1` primary `ci.yml` push run with both required verification jobs.
Only then may the read-only exact-six preflight below be considered. A missing, malformed, or seventh iter204
row; any iter205 or iter206 run; nonempty pre-dispatch iter207 history; wrong merge parent; extra publication event; or
source change closes iter207 before dispatch.

## Exact Authorized Iter207 Dispatch

Run this block once only after the one-push, one-merge envelope and green primary CI are complete. Before its
sole state-changing line, it proves the exact repository and merge, local guards, active workflow objects,
empty iter205, iter206, and iter207 histories, the exact six-row iter204 admission snapshot, zero jobs/artifacts and
HTTP-`404` logs for all six parser records, zero iter204 dispatches, exactly one successful release-branch
`push` CI run and one successful release-branch `pull_request` CI run with their exact jobs, and exact primary
CI jobs. Read-only
transport failure before the dispatch request may be resolved by restarting the full preflight. A confirmed
invariant mismatch closes iter207. Once execution reaches the dispatch request line, never re-enter this block.

```bash
set -euo pipefail
test "$(git branch --show-current)" = master
git fetch origin master
test -z "$(git status --porcelain)"
HEAD_SHA="$(git rev-parse HEAD)"
test "$HEAD_SHA" = "$(git rev-parse origin/master)"
[[ "$HEAD_SHA" =~ ^[0-9a-f]{40}$ ]]
test "$(git rev-list --parents -n 1 "$HEAD_SHA" | wc -w | tr -d ' ')" = 3
FIRST_PARENT="$(git rev-parse "$HEAD_SHA^1")"
SECOND_PARENT="$(git rev-parse "$HEAD_SHA^2")"
test "$FIRST_PARENT" = "@@ITER205_MERGE_COMMIT@@"
REPO="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
test "$REPO" = "manfromnowhere143/telos"
python3 -I -S scripts/audit_iter207_claim_integrity.py --check
python3 -I -S scripts/validate_iter206_pre_publication_null.py
python3 -I -S scripts/build_iter207_runtime_manifest.py --check
python3 -I -S scripts/validate_iter207_publication_safety.py --check
python3 -I -S scripts/validate_iter207_runtime_recovery.py

workflow_history_payload() {
  local workflow_id="$1"
  local event="${2:-}"
  local payload
  if test -n "$event"; then
    payload="$(gh api -X GET "repos/$REPO/actions/workflows/$workflow_id/runs" -f event="$event" -f page=1 -f per_page=100)" || return 1
  else
    payload="$(gh api -X GET "repos/$REPO/actions/workflows/$workflow_id/runs" -f page=1 -f per_page=100)" || return 1
  fi
  test "$(jq -r '[(.total_count | type), (.workflow_runs | type)] | @tsv' <<< "$payload")" = $'number\tarray' || return 1
  test "$(jq -r '.total_count == (.workflow_runs | length)' <<< "$payload")" = true || return 1
  test "$(jq -r '[.workflow_runs[] | type] | all(. == "object")' <<< "$payload")" = true || return 1
  printf '%s\\n' "$payload"
}

ITER207_WORKFLOW_BINDING="$(gh api -X GET "repos/$REPO/actions/workflows/iter207-execute.yml" --jq '[.id,.name,.path,.state] | @tsv')"
ITER207_WORKFLOW_ID="$(printf '%s\\n' "$ITER207_WORKFLOW_BINDING" | cut -f1)"
[[ "$ITER207_WORKFLOW_ID" =~ ^[1-9][0-9]*$ ]]
test "$ITER207_WORKFLOW_BINDING" = "$ITER207_WORKFLOW_ID"$'\titer207-execute\t.github/workflows/iter207-execute.yml\tactive'
ITER207_ALL_PAYLOAD="$(workflow_history_payload "$ITER207_WORKFLOW_ID")"
ITER207_DISPATCH_PAYLOAD="$(workflow_history_payload "$ITER207_WORKFLOW_ID" workflow_dispatch)"
ITER207_ALL_COUNT="$(jq -r '.total_count' <<< "$ITER207_ALL_PAYLOAD")"
ITER207_DISPATCH_COUNT="$(jq -r '.total_count' <<< "$ITER207_DISPATCH_PAYLOAD")"
test "$ITER207_ALL_COUNT" -eq 0
test "$ITER207_DISPATCH_COUNT" -eq 0

ITER205_WORKFLOW_BINDING="$(gh api -X GET "repos/$REPO/actions/workflows/@@ITER205_WORKFLOW_ID@@" --jq '[.id,.name,.path,.state] | @tsv')"
test "$ITER205_WORKFLOW_BINDING" = $'@@ITER205_WORKFLOW_ID@@\titer205-execute\t.github/workflows/iter205-execute.yml\tactive'
ITER205_ALL_PAYLOAD="$(workflow_history_payload "@@ITER205_WORKFLOW_ID@@")"
ITER205_DISPATCH_PAYLOAD="$(workflow_history_payload "@@ITER205_WORKFLOW_ID@@" workflow_dispatch)"
ITER205_ALL_COUNT="$(jq -r '.total_count' <<< "$ITER205_ALL_PAYLOAD")"
ITER205_DISPATCH_COUNT="$(jq -r '.total_count' <<< "$ITER205_DISPATCH_PAYLOAD")"
test "$ITER205_ALL_COUNT" -eq 0
test "$ITER205_DISPATCH_COUNT" -eq 0

ITER206_WORKFLOW_BINDING="$(gh api -X GET "repos/$REPO/actions/workflows/iter206-execute.yml" --jq '[.id,.name,.path,.state] | @tsv')"
ITER206_WORKFLOW_ID="$(printf '%s\\n' "$ITER206_WORKFLOW_BINDING" | cut -f1)"
[[ "$ITER206_WORKFLOW_ID" =~ ^[1-9][0-9]*$ ]]
test "$ITER206_WORKFLOW_BINDING" = "$ITER206_WORKFLOW_ID"$'\titer206-execute\t.github/workflows/iter206-execute.yml\tactive'
test "$ITER206_WORKFLOW_ID" != "@@ITER204_WORKFLOW_ID@@"
test "$ITER206_WORKFLOW_ID" != "@@ITER205_WORKFLOW_ID@@"
test "$ITER206_WORKFLOW_ID" != "$ITER207_WORKFLOW_ID"
ITER206_ALL_PAYLOAD="$(workflow_history_payload "$ITER206_WORKFLOW_ID")"
ITER206_DISPATCH_PAYLOAD="$(workflow_history_payload "$ITER206_WORKFLOW_ID" workflow_dispatch)"
ITER206_ALL_COUNT="$(jq -r '.total_count' <<< "$ITER206_ALL_PAYLOAD")"
ITER206_DISPATCH_COUNT="$(jq -r '.total_count' <<< "$ITER206_DISPATCH_PAYLOAD")"
test "$ITER206_ALL_COUNT" -eq 0
test "$ITER206_DISPATCH_COUNT" -eq 0

ITER204_WORKFLOW_BINDING="$(gh api -X GET "repos/$REPO/actions/workflows/@@ITER204_WORKFLOW_ID@@" --jq '[.id,.name,.path,.state] | @tsv')"
test "$ITER204_WORKFLOW_BINDING" = $'@@ITER204_WORKFLOW_ID@@\t.github/workflows/iter204-execute.yml\t.github/workflows/iter204-execute.yml\tactive'
ITER204_ALL_PAYLOAD="$(workflow_history_payload "@@ITER204_WORKFLOW_ID@@")"
ITER204_ALL_COUNT="$(jq -r '.total_count' <<< "$ITER204_ALL_PAYLOAD")"
test "$ITER204_ALL_COUNT" -eq 6
ITER204_HISTORY="$(
  jq -r '.workflow_runs[] | [.run_number,.id,.workflow_id,.name,.path,.event,.status,.conclusion,.run_attempt,.head_branch,.head_sha,(.pull_requests | length),.head_repository.full_name] | @tsv' <<< "$ITER204_ALL_PAYLOAD" \\
    | LC_ALL=C sort -n -k1,1
)"
test "$(printf '%s\\n' "$ITER204_HISTORY" | sed '/^$/d' | wc -l | tr -d ' ')" -eq 6
ITER204_RELEASE_RUN_ID="$(printf '%s\\n' "$ITER204_HISTORY" | awk -F '\t' '$1 == 5 { print $2 }')"
ITER204_PRIMARY_RUN_ID="$(printf '%s\\n' "$ITER204_HISTORY" | awk -F '\t' '$1 == 6 { print $2 }')"
[[ "$ITER204_RELEASE_RUN_ID" =~ ^[1-9][0-9]*$ ]]
[[ "$ITER204_PRIMARY_RUN_ID" =~ ^[1-9][0-9]*$ ]]
test "$ITER204_RELEASE_RUN_ID" != "$ITER204_PRIMARY_RUN_ID"
EXPECTED_ITER204_HISTORY="$(printf '%s\\n' \\
  $'1\t@@ITER204_FEATURE_PUSH_RUN_ID@@\t@@ITER204_WORKFLOW_ID@@\t.github/workflows/iter204-execute.yml\t.github/workflows/iter204-execute.yml\tpush\tcompleted\tfailure\t1\tagent/iter204-infrastructure-recovery\t@@ITER204_FEATURE_PUSH_COMMIT@@\t0\tmanfromnowhere143/telos' \\
  $'2\t@@ITER204_PRIMARY_PUSH_RUN_ID@@\t@@ITER204_WORKFLOW_ID@@\t.github/workflows/iter204-execute.yml\t.github/workflows/iter204-execute.yml\tpush\tcompleted\tfailure\t1\tmaster\t@@ITER204_MERGE_COMMIT@@\t0\tmanfromnowhere143/telos' \\
  $'3\t@@ITER205_FEATURE_PUSH_RUN_ID@@\t@@ITER204_WORKFLOW_ID@@\t.github/workflows/iter204-execute.yml\t.github/workflows/iter204-execute.yml\tpush\tcompleted\tfailure\t1\tagent/iter205-workflow-context-recovery\t@@ITER205_FEATURE_COMMIT@@\t0\tmanfromnowhere143/telos' \\
  $'4\t@@ITER205_PRIMARY_PUSH_RUN_ID@@\t@@ITER204_WORKFLOW_ID@@\t.github/workflows/iter204-execute.yml\t.github/workflows/iter204-execute.yml\tpush\tcompleted\tfailure\t1\tmaster\t@@ITER205_MERGE_COMMIT@@\t0\tmanfromnowhere143/telos' \\
  $'5\t'"$ITER204_RELEASE_RUN_ID"$'\t@@ITER204_WORKFLOW_ID@@\t.github/workflows/iter204-execute.yml\t.github/workflows/iter204-execute.yml\tpush\tcompleted\tfailure\t1\t@@ITER207_BRANCH@@\t'"$SECOND_PARENT"$'\t0\tmanfromnowhere143/telos' \\
  $'6\t'"$ITER204_PRIMARY_RUN_ID"$'\t@@ITER204_WORKFLOW_ID@@\t.github/workflows/iter204-execute.yml\t.github/workflows/iter204-execute.yml\tpush\tcompleted\tfailure\t1\tmaster\t'"$HEAD_SHA"$'\t0\tmanfromnowhere143/telos')"
test "$ITER204_HISTORY" = "$EXPECTED_ITER204_HISTORY"
ITER204_DISPATCH_PAYLOAD="$(workflow_history_payload "@@ITER204_WORKFLOW_ID@@" workflow_dispatch)"
ITER204_DISPATCH_COUNT="$(jq -r '.total_count' <<< "$ITER204_DISPATCH_PAYLOAD")"
test "$ITER204_DISPATCH_COUNT" -eq 0
for ITER204_RUN_ID in @@ITER204_FEATURE_PUSH_RUN_ID@@ @@ITER204_PRIMARY_PUSH_RUN_ID@@ @@ITER205_FEATURE_PUSH_RUN_ID@@ @@ITER205_PRIMARY_PUSH_RUN_ID@@ "$ITER204_RELEASE_RUN_ID" "$ITER204_PRIMARY_RUN_ID"; do
  test "$(gh api -X GET "repos/$REPO/actions/runs/$ITER204_RUN_ID/attempts/1/jobs" -f per_page=100 --jq '[.total_count,(.jobs | length)] | @tsv')" = $'0\t0'
  test "$(gh api -X GET "repos/$REPO/actions/runs/$ITER204_RUN_ID/artifacts" -f per_page=100 --jq '[.total_count,(.artifacts | length)] | @tsv')" = $'0\t0'
  set +e
  LOG_DIAGNOSTIC="$(gh api -X GET "repos/$REPO/actions/runs/$ITER204_RUN_ID/logs" 2>&1)"
  LOG_STATUS=$?
  set -e
  test "$LOG_STATUS" -ne 0
  printf '%s\\n' "$LOG_DIAGNOSTIC" | grep -F 'Not Found' >/dev/null
  printf '%s\\n' "$LOG_DIAGNOSTIC" | grep -E 'HTTP[^0-9]*404' >/dev/null
done

verify_release_ci() {
  local event="$1"
  local run_payload binding run_id jobs_payload job_rows job_summary job_ids
  run_payload="$(gh api -X GET "repos/$REPO/actions/workflows/ci.yml/runs" -f event="$event" -f head_sha="$SECOND_PARENT" -f page=1 -f per_page=100)"
  test "$(jq -r '[.total_count, (.workflow_runs | length)] | @tsv' <<< "$run_payload")" = $'1\t1'
  test "$(jq -r '.workflow_runs | type' <<< "$run_payload")" = array
  test "$(jq -r '[.workflow_runs[] | type] | all(. == "object")' <<< "$run_payload")" = true
  binding="$(jq -r '.workflow_runs[] | [.id,.conclusion,.event,.head_branch,.head_sha,.path,.run_attempt,.status,.head_repository.full_name] | @tsv' <<< "$run_payload")"
  run_id="$(printf '%s\\n' "$binding" | cut -f1)"
  [[ "$run_id" =~ ^[1-9][0-9]*$ ]]
  test "$(printf '%s\\n' "$binding" | cut -f2-)" = $'success\t'"$event"$'\t@@ITER207_BRANCH@@\t'"$SECOND_PARENT"$'\t.github/workflows/ci.yml\t1\tcompleted\tmanfromnowhere143/telos'
  jobs_payload="$(gh api -X GET "repos/$REPO/actions/runs/$run_id/attempts/1/jobs" -f page=1 -f per_page=100)"
  test "$(jq -r '[.total_count, (.jobs | length)] | @tsv' <<< "$jobs_payload")" = $'2\t2'
  test "$(jq -r '.jobs | type' <<< "$jobs_payload")" = array
  test "$(jq -r '[.jobs[] | type] | all(. == "object")' <<< "$jobs_payload")" = true
  job_rows="$(jq -r '.jobs[] | [.name,.conclusion,.head_sha,.id,.run_attempt,.status,.html_url] | @tsv' <<< "$jobs_payload" | LC_ALL=C sort)"
  job_summary="$(printf '%s\\n' "$job_rows" | cut -f1-3,5-6)"
  test "$job_summary" = "$(printf '%s\\n' \\
    $'verify py3.11\tsuccess\t'"$SECOND_PARENT"$'\t1\tcompleted' \\
    $'verify py3.12\tsuccess\t'"$SECOND_PARENT"$'\t1\tcompleted')"
  job_ids="$(printf '%s\\n' "$job_rows" | cut -f4)"
  test "$(printf '%s\\n' "$job_ids" | LC_ALL=C sort -u | wc -l | tr -d ' ')" -eq 2
  while IFS= read -r job_id; do [[ "$job_id" =~ ^[1-9][0-9]*$ ]]; done <<< "$job_ids"
  while IFS=$'\t' read -r _ _ _ job_id _ _ html_url; do
    test "$html_url" = "https://github.com/$REPO/actions/runs/$run_id/job/$job_id"
  done <<< "$job_rows"
  printf '%s\\n' "$run_id"
}
RELEASE_PUSH_CI_RUN_ID="$(verify_release_ci push)"
RELEASE_PULL_REQUEST_CI_RUN_ID="$(verify_release_ci pull_request)"
test "$RELEASE_PUSH_CI_RUN_ID" != "$RELEASE_PULL_REQUEST_CI_RUN_ID"

CI_RUNS_PAYLOAD="$(gh api -X GET "repos/$REPO/actions/workflows/ci.yml/runs" -f branch=master -f event=push -f head_sha="$HEAD_SHA" -f page=1 -f per_page=100)"
test "$(jq -r '[.total_count, (.workflow_runs | length)] | @tsv' <<< "$CI_RUNS_PAYLOAD")" = $'1\t1'
test "$(jq -r '.workflow_runs | type' <<< "$CI_RUNS_PAYLOAD")" = array
test "$(jq -r '[.workflow_runs[] | type] | all(. == "object")' <<< "$CI_RUNS_PAYLOAD")" = true
CI_BINDING="$(jq -r '.workflow_runs[] | [.id,.status,.conclusion,.event,.head_branch,.head_sha,.run_attempt,.path] | @tsv' <<< "$CI_RUNS_PAYLOAD")"
CI_RUN_ID="$(printf '%s\\n' "$CI_BINDING" | cut -f1)"
[[ "$CI_RUN_ID" =~ ^[1-9][0-9]*$ ]]
test "$(printf '%s\\n' "$CI_BINDING" | cut -f2-)" = $'completed\tsuccess\tpush\tmaster\t'"$HEAD_SHA"$'\t1\t.github/workflows/ci.yml'
PRIMARY_CHECK_ROWS=""
PRIMARY_CHECK_HISTORY_COMPLETE=0
for page in $(seq 1 10); do
  CHECKS_PAYLOAD="$(gh api -X GET "repos/$REPO/commits/$HEAD_SHA/check-runs" -f filter=all -f page="$page" -f per_page=100)"
  test "$(jq -r '.check_runs | type' <<< "$CHECKS_PAYLOAD")" = array
  test "$(jq -r '[.check_runs[] | type] | all(. == "object")' <<< "$CHECKS_PAYLOAD")" = true
  CHECK_PAGE_ROWS="$(jq -r '.check_runs[] | [.name,.status,.conclusion,.app.slug,.id,.details_url,(.id | type),(.app | type)] | @tsv' <<< "$CHECKS_PAYLOAD")"
  if test -n "$CHECK_PAGE_ROWS"; then
    PRIMARY_CHECK_ROWS="${PRIMARY_CHECK_ROWS}${PRIMARY_CHECK_ROWS:+$'\\n'}${CHECK_PAGE_ROWS}"
  fi
  CHECK_PAGE_COUNT="$(jq -r '.check_runs | length' <<< "$CHECKS_PAYLOAD")"
  if test "$CHECK_PAGE_COUNT" -lt 100; then
    PRIMARY_CHECK_HISTORY_COMPLETE=1
    break
  fi
done
test "$PRIMARY_CHECK_HISTORY_COMPLETE" -eq 1

verify_primary_check() {
  local name="$1"
  local candidates check_id expected_prefix
  expected_prefix="https://github.com/$REPO/actions/runs/$CI_RUN_ID/job/"
  candidates="$(printf '%s\\n' "$PRIMARY_CHECK_ROWS" | awk -F '\t' -v name="$name" -v prefix="$expected_prefix" '$1 == name && $2 == "completed" && $3 == "success" && $4 == "github-actions" && $7 == "number" && $8 == "object" && $6 == prefix $5 { print }')"
  test "$(printf '%s\\n' "$candidates" | sed '/^$/d' | wc -l | tr -d ' ')" -eq 1
  check_id="$(printf '%s\\n' "$candidates" | cut -f5)"
  [[ "$check_id" =~ ^[1-9][0-9]*$ ]]
  printf '%s\\n' "$check_id"
}
PRIMARY_PY311_CHECK_ID="$(verify_primary_check 'verify py3.11')"
PRIMARY_PY312_CHECK_ID="$(verify_primary_check 'verify py3.12')"
test "$PRIMARY_PY311_CHECK_ID" != "$PRIMARY_PY312_CHECK_ID"

gh workflow run iter207-execute.yml --ref master \\
  -f expected_primary_sha="$HEAD_SHA" \\
  -f expected_workflow_id="$ITER207_WORKFLOW_ID" \\
  -f expected_iter206_workflow_id="$ITER206_WORKFLOW_ID" \\
  -f expected_iter204_release_run_id="$ITER204_RELEASE_RUN_ID" \\
  -f expected_iter204_primary_run_id="$ITER204_PRIMARY_RUN_ID"
RUN_ID=""
for _ in $(seq 1 12); do
  ITER207_ALL_PAYLOAD="$(workflow_history_payload "$ITER207_WORKFLOW_ID")"
  ITER207_DISPATCH_PAYLOAD="$(workflow_history_payload "$ITER207_WORKFLOW_ID" workflow_dispatch)"
  ITER207_ALL_COUNT="$(jq -r '.total_count' <<< "$ITER207_ALL_PAYLOAD")"
  ITER207_DISPATCH_COUNT="$(jq -r '.total_count' <<< "$ITER207_DISPATCH_PAYLOAD")"
  test "$ITER207_ALL_COUNT" -le 1
  test "$ITER207_DISPATCH_COUNT" -le 1
  if test "$ITER207_ALL_COUNT" -eq 1 && test "$ITER207_DISPATCH_COUNT" -eq 1; then
    RUN_ID="$(jq -r '.workflow_runs[0].id // empty' <<< "$ITER207_DISPATCH_PAYLOAD")"
    break
  fi
  sleep 5
done
if test -z "$RUN_ID"; then
  printf 'Iter207 dispatch request was entered but run discovery is incomplete; never reissue it. Use observation only.\\n' >&2
  exit 75
fi
RUN_BINDING="$(gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '[.id,.workflow_id,.name,.event,.head_branch,.head_sha,.path,.run_number,.run_attempt] | @tsv')"
test "$RUN_BINDING" = "$RUN_ID"$'\t'"$ITER207_WORKFLOW_ID"$'\titer207-execute\tworkflow_dispatch\tmaster\t'"$HEAD_SHA"$'\t.github/workflows/iter207-execute.yml\t1\t1'
printf 'Canonical iter207 RUN_ID=%s APPROVED_SHA=%s; use only the observation block below.\\n' "$RUN_ID" "$HEAD_SHA"
```

The dispatch-request allowance is consumed when the command is entered, including dispatch API rejection or
ambiguous client state. Never issue a second dispatch request, rerun, or replacement run. A temporarily absent, queued, or in-progress
run is not itself a null. If discovery or watching is interrupted, use only this read-only observation block.
No observation ever authorizes another dispatch request.

```bash
set -euo pipefail
test "$(git branch --show-current)" = master
git fetch origin master
test -z "$(git status --porcelain)"
REPO="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
test "$REPO" = "manfromnowhere143/telos"
workflow_history_payload() {
  local workflow_id="$1"
  local event="${2:-}"
  local payload
  if test -n "$event"; then
    payload="$(gh api -X GET "repos/$REPO/actions/workflows/$workflow_id/runs" -f event="$event" -f page=1 -f per_page=100)" || return 1
  else
    payload="$(gh api -X GET "repos/$REPO/actions/workflows/$workflow_id/runs" -f page=1 -f per_page=100)" || return 1
  fi
  test "$(jq -r '[(.total_count | type), (.workflow_runs | type)] | @tsv' <<< "$payload")" = $'number\tarray' || return 1
  test "$(jq -r '.total_count == (.workflow_runs | length)' <<< "$payload")" = true || return 1
  test "$(jq -r '[.workflow_runs[] | type] | all(. == "object")' <<< "$payload")" = true || return 1
  printf '%s\\n' "$payload"
}
ITER207_WORKFLOW_BINDING="$(gh api -X GET "repos/$REPO/actions/workflows/iter207-execute.yml" --jq '[.id,.name,.path,.state] | @tsv')"
ITER207_WORKFLOW_ID="$(printf '%s\\n' "$ITER207_WORKFLOW_BINDING" | cut -f1)"
[[ "$ITER207_WORKFLOW_ID" =~ ^[1-9][0-9]*$ ]]
test "$ITER207_WORKFLOW_BINDING" = "$ITER207_WORKFLOW_ID"$'\titer207-execute\t.github/workflows/iter207-execute.yml\tactive'
ITER206_WORKFLOW_BINDING="$(gh api -X GET "repos/$REPO/actions/workflows/iter206-execute.yml" --jq '[.id,.name,.path,.state] | @tsv')"
ITER206_WORKFLOW_ID="$(printf '%s\\n' "$ITER206_WORKFLOW_BINDING" | cut -f1)"
[[ "$ITER206_WORKFLOW_ID" =~ ^[1-9][0-9]*$ ]]
test "$ITER206_WORKFLOW_BINDING" = "$ITER206_WORKFLOW_ID"$'\titer206-execute\t.github/workflows/iter206-execute.yml\tactive'
test "$ITER206_WORKFLOW_ID" != "$ITER207_WORKFLOW_ID"
ITER206_ALL_PAYLOAD="$(workflow_history_payload "$ITER206_WORKFLOW_ID")"
ITER206_DISPATCH_PAYLOAD="$(workflow_history_payload "$ITER206_WORKFLOW_ID" workflow_dispatch)"
test "$(jq -r '.total_count' <<< "$ITER206_ALL_PAYLOAD")" -eq 0
test "$(jq -r '.total_count' <<< "$ITER206_DISPATCH_PAYLOAD")" -eq 0
ITER207_ALL_PAYLOAD="$(workflow_history_payload "$ITER207_WORKFLOW_ID")"
ITER207_DISPATCH_PAYLOAD="$(workflow_history_payload "$ITER207_WORKFLOW_ID" workflow_dispatch)"
ITER207_ALL_COUNT="$(jq -r '.total_count' <<< "$ITER207_ALL_PAYLOAD")"
ITER207_DISPATCH_COUNT="$(jq -r '.total_count' <<< "$ITER207_DISPATCH_PAYLOAD")"
test "$ITER207_ALL_COUNT" -eq 1
test "$ITER207_DISPATCH_COUNT" -eq 1
RUN_ID="$(jq -r '.workflow_runs[0].id // empty' <<< "$ITER207_DISPATCH_PAYLOAD")"
test -n "$RUN_ID"
APPROVED_SHA="$(gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '.head_sha')"
RUN_BINDING="$(gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '[.id,.workflow_id,.name,.event,.head_branch,.head_sha,.path,.run_number,.run_attempt] | @tsv')"
test "$RUN_BINDING" = "$RUN_ID"$'\t'"$ITER207_WORKFLOW_ID"$'\titer207-execute\tworkflow_dispatch\tmaster\t'"$APPROVED_SHA"$'\t.github/workflows/iter207-execute.yml\t1\t1'
git merge-base --is-ancestor "$APPROVED_SHA" origin/master
gh run watch "$RUN_ID" || true
RUN_STATE="$(gh run view "$RUN_ID" --json status,conclusion --jq '[.status,(.conclusion // "")] | join(" ")')"
if test "${RUN_STATE%% *}" != completed; then
  printf 'Run %s is not terminal (%s); repeat only this read-only observation block.\\n' "$RUN_ID" "$RUN_STATE" >&2
  exit 75
fi
RUN_CONCLUSION="${RUN_STATE#* }"
if test "$RUN_CONCLUSION" != success; then
  printf 'Run %s is terminal with conclusion=%s; preserve bounded failure evidence and close iter207.\\n' "$RUN_ID" "$RUN_CONCLUSION" >&2
  exit 20
fi
printf 'Run %s completed successfully; continue to exact complete-artifact verification.\\n' "$RUN_ID"
```

A terminal non-success run, dispatch rejection, smoke failure, shard failure, collector failure, parser
record, incomplete corpus, or extra run closes iter207 without retry. Preserve evidence at the exact available
boundary; never select partial artifacts or reinterpret infrastructure as science.

```bash
set -euo pipefail
test "$(git branch --show-current)" = master
git fetch origin master
test -z "$(git status --porcelain)"
REPO="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
test "$REPO" = "manfromnowhere143/telos"
workflow_history_payload() {
  local workflow_id="$1"
  local event="${2:-}"
  local payload
  if test -n "$event"; then
    payload="$(gh api -X GET "repos/$REPO/actions/workflows/$workflow_id/runs" -f event="$event" -f page=1 -f per_page=100)" || return 1
  else
    payload="$(gh api -X GET "repos/$REPO/actions/workflows/$workflow_id/runs" -f page=1 -f per_page=100)" || return 1
  fi
  test "$(jq -r '[(.total_count | type), (.workflow_runs | type)] | @tsv' <<< "$payload")" = $'number\tarray' || return 1
  test "$(jq -r '.total_count == (.workflow_runs | length)' <<< "$payload")" = true || return 1
  test "$(jq -r '[.workflow_runs[] | type] | all(. == "object")' <<< "$payload")" = true || return 1
  printf '%s\\n' "$payload"
}
ITER207_WORKFLOW_BINDING="$(gh api -X GET "repos/$REPO/actions/workflows/iter207-execute.yml" --jq '[.id,.name,.path,.state] | @tsv')"
ITER207_WORKFLOW_ID="$(printf '%s\\n' "$ITER207_WORKFLOW_BINDING" | cut -f1)"
[[ "$ITER207_WORKFLOW_ID" =~ ^[1-9][0-9]*$ ]]
test "$ITER207_WORKFLOW_BINDING" = "$ITER207_WORKFLOW_ID"$'\titer207-execute\t.github/workflows/iter207-execute.yml\tactive'
ITER206_WORKFLOW_BINDING="$(gh api -X GET "repos/$REPO/actions/workflows/iter206-execute.yml" --jq '[.id,.name,.path,.state] | @tsv')"
ITER206_WORKFLOW_ID="$(printf '%s\\n' "$ITER206_WORKFLOW_BINDING" | cut -f1)"
[[ "$ITER206_WORKFLOW_ID" =~ ^[1-9][0-9]*$ ]]
test "$ITER206_WORKFLOW_BINDING" = "$ITER206_WORKFLOW_ID"$'\titer206-execute\t.github/workflows/iter206-execute.yml\tactive'
test "$ITER206_WORKFLOW_ID" != "$ITER207_WORKFLOW_ID"
ITER206_ALL_PAYLOAD="$(workflow_history_payload "$ITER206_WORKFLOW_ID")"
ITER206_DISPATCH_PAYLOAD="$(workflow_history_payload "$ITER206_WORKFLOW_ID" workflow_dispatch)"
test "$(jq -r '.total_count' <<< "$ITER206_ALL_PAYLOAD")" -eq 0
test "$(jq -r '.total_count' <<< "$ITER206_DISPATCH_PAYLOAD")" -eq 0
ITER207_ALL_PAYLOAD="$(workflow_history_payload "$ITER207_WORKFLOW_ID")"
ITER207_DISPATCH_PAYLOAD="$(workflow_history_payload "$ITER207_WORKFLOW_ID" workflow_dispatch)"
test "$(jq -r '.total_count' <<< "$ITER207_ALL_PAYLOAD")" -eq 1
test "$(jq -r '.total_count' <<< "$ITER207_DISPATCH_PAYLOAD")" -eq 1
RUN_ID="$(jq -r '.workflow_runs[0].id // empty' <<< "$ITER207_DISPATCH_PAYLOAD")"
APPROVED_SHA="$(gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '.head_sha')"
RUN_BINDING="$(gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '[.id,.workflow_id,.name,.event,.head_branch,.head_sha,.path,.run_number,.run_attempt] | @tsv')"
test "$RUN_BINDING" = "$RUN_ID"$'\t'"$ITER207_WORKFLOW_ID"$'\titer207-execute\tworkflow_dispatch\tmaster\t'"$APPROVED_SHA"$'\t.github/workflows/iter207-execute.yml\t1\t1'
test "$(git rev-parse HEAD)" = "$APPROVED_SHA"
test "$(gh run view "$RUN_ID" --json attempt,status --jq '[.attempt,.status] | @tsv')" = $'1\tcompleted'
RUN_CONCLUSION="$(gh run view "$RUN_ID" --json conclusion --jq '.conclusion // empty')"
test -n "$RUN_CONCLUSION"
if test "$RUN_CONCLUSION" = success; then
  printf 'Run succeeded; use complete-artifact collection instead of null collection.\\n' >&2
  exit 2
fi
NULL_DIR="experiments/iter207_claim_integrity_and_admission_recovery/proof/raw/execution_null_run_${RUN_ID}_attempt_1"
test ! -e "$NULL_DIR"
RAW_DIR="$(dirname "$NULL_DIR")"
STAGE="$(mktemp -d "$RAW_DIR/.iter207-null-stage.XXXXXX")"
cleanup() { if test -n "${STAGE:-}" && test -d "$STAGE"; then rm -rf -- "$STAGE"; fi; }
trap cleanup EXIT
gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '{id,name,workflow_id,head_branch,head_sha,path,event,status,conclusion,run_number,run_attempt,run_started_at,updated_at,html_url}' > "$STAGE/run.json"
gh api -X GET "repos/$REPO/actions/runs/$RUN_ID/jobs" -f filter=all -f per_page=100 | jq -S . > "$STAGE/jobs.json"
gh api -X GET "repos/$REPO/actions/runs/$RUN_ID/artifacts" -f per_page=100 | jq -S . > "$STAGE/artifacts.json"
if test "$(jq -r '.total_count' "$STAGE/artifacts.json")" -gt 0; then
  mkdir "$STAGE/artifacts"
  gh run download "$RUN_ID" --dir "$STAGE/artifacts"
fi
(cd "$STAGE" && find . -type f ! -name SHA256SUMS -exec shasum -a 256 '{}' + | LC_ALL=C sort > SHA256SUMS)
mv "$STAGE" "$NULL_DIR"
STAGE=""
trap - EXIT
printf 'Preserved terminal iter207 evidence at %s; publish a bounded null before any successor.\\n' "$NULL_DIR"
```

After the sole run succeeds, re-prove its uniqueness and source, promote exactly one complete attempt-`1`
aggregate, validate it before the move, then adjudicate and run the checkpoint-aware blind judge.

```bash
set -euo pipefail
test "$(git branch --show-current)" = master
git fetch origin master
test -z "$(git status --porcelain)"
REPO="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
test "$REPO" = "manfromnowhere143/telos"
workflow_history_payload() {
  local workflow_id="$1"
  local event="${2:-}"
  local payload
  if test -n "$event"; then
    payload="$(gh api -X GET "repos/$REPO/actions/workflows/$workflow_id/runs" -f event="$event" -f page=1 -f per_page=100)" || return 1
  else
    payload="$(gh api -X GET "repos/$REPO/actions/workflows/$workflow_id/runs" -f page=1 -f per_page=100)" || return 1
  fi
  test "$(jq -r '[(.total_count | type), (.workflow_runs | type)] | @tsv' <<< "$payload")" = $'number\tarray' || return 1
  test "$(jq -r '.total_count == (.workflow_runs | length)' <<< "$payload")" = true || return 1
  test "$(jq -r '[.workflow_runs[] | type] | all(. == "object")' <<< "$payload")" = true || return 1
  printf '%s\\n' "$payload"
}
ITER207_WORKFLOW_BINDING="$(gh api -X GET "repos/$REPO/actions/workflows/iter207-execute.yml" --jq '[.id,.name,.path,.state] | @tsv')"
ITER207_WORKFLOW_ID="$(printf '%s\\n' "$ITER207_WORKFLOW_BINDING" | cut -f1)"
[[ "$ITER207_WORKFLOW_ID" =~ ^[1-9][0-9]*$ ]]
test "$ITER207_WORKFLOW_BINDING" = "$ITER207_WORKFLOW_ID"$'\titer207-execute\t.github/workflows/iter207-execute.yml\tactive'
ITER206_WORKFLOW_BINDING="$(gh api -X GET "repos/$REPO/actions/workflows/iter206-execute.yml" --jq '[.id,.name,.path,.state] | @tsv')"
ITER206_WORKFLOW_ID="$(printf '%s\\n' "$ITER206_WORKFLOW_BINDING" | cut -f1)"
[[ "$ITER206_WORKFLOW_ID" =~ ^[1-9][0-9]*$ ]]
test "$ITER206_WORKFLOW_BINDING" = "$ITER206_WORKFLOW_ID"$'\titer206-execute\t.github/workflows/iter206-execute.yml\tactive'
test "$ITER206_WORKFLOW_ID" != "$ITER207_WORKFLOW_ID"
ITER206_ALL_PAYLOAD="$(workflow_history_payload "$ITER206_WORKFLOW_ID")"
ITER206_DISPATCH_PAYLOAD="$(workflow_history_payload "$ITER206_WORKFLOW_ID" workflow_dispatch)"
test "$(jq -r '.total_count' <<< "$ITER206_ALL_PAYLOAD")" -eq 0
test "$(jq -r '.total_count' <<< "$ITER206_DISPATCH_PAYLOAD")" -eq 0
ITER207_ALL_PAYLOAD="$(workflow_history_payload "$ITER207_WORKFLOW_ID")"
ITER207_DISPATCH_PAYLOAD="$(workflow_history_payload "$ITER207_WORKFLOW_ID" workflow_dispatch)"
test "$(jq -r '.total_count' <<< "$ITER207_ALL_PAYLOAD")" -eq 1
test "$(jq -r '.total_count' <<< "$ITER207_DISPATCH_PAYLOAD")" -eq 1
RUN_ID="$(jq -r '.workflow_runs[0].id // empty' <<< "$ITER207_DISPATCH_PAYLOAD")"
APPROVED_SHA="$(gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '.head_sha')"
RUN_BINDING="$(gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '[.id,.workflow_id,.name,.event,.head_branch,.head_sha,.path,.run_number,.run_attempt] | @tsv')"
test "$RUN_BINDING" = "$RUN_ID"$'\t'"$ITER207_WORKFLOW_ID"$'\titer207-execute\tworkflow_dispatch\tmaster\t'"$APPROVED_SHA"$'\t.github/workflows/iter207-execute.yml\t1\t1'
test "$(git rev-parse HEAD)" = "$APPROVED_SHA"
test "$(gh run view "$RUN_ID" --json status,conclusion,attempt --jq '[.status,.conclusion,.attempt] | join(" ")')" = "completed success 1"
python3 -I -S scripts/validate_iter205_pre_dispatch_null.py
python3 -I -S scripts/validate_iter206_pre_publication_null.py
python3 -I -S scripts/audit_iter207_claim_integrity.py --check
python3 -I -S scripts/build_iter207_runtime_manifest.py --check
EXECUTION_DIR="experiments/iter207_claim_integrity_and_admission_recovery/proof/raw/execution"
test ! -e "$EXECUTION_DIR"
RAW_DIR="$(dirname "$EXECUTION_DIR")"
STAGE="$(mktemp -d "$RAW_DIR/.iter207-execution-stage.XXXXXX")"
cleanup() { if test -n "${STAGE:-}" && test -d "$STAGE"; then rm -rf -- "$STAGE"; fi; }
trap cleanup EXIT
gh run download "$RUN_ID" --name "iter207-execution-complete-$RUN_ID-attempt-1" --dir "$STAGE"
python3 -I -S scripts/collect_iter207_execution.py check \\
  --execution-dir "$STAGE" \\
  --aggregate-receipt "$STAGE/_telos_iter207_execution_complete.receipt.json" \\
  --spec-index experiments/iter203_iter202_safety_recovery/proof/raw/specs/index.json \\
  --runtime-manifest experiments/iter207_claim_integrity_and_admission_recovery/proof/raw/runtime_manifest.json
mv "$STAGE" "$EXECUTION_DIR"
STAGE=""
trap - EXIT
python3 -I -S scripts/adjudicate_iter207_claim_integrity_and_admission_recovery.py
python3 -I -S scripts/run_iter207_claim_integrity_and_admission_recovery_blind_judge.py
```

If local adjudication or judging is interrupted after the complete artifact is promoted, do not redownload
or rerun anything. Revalidate the final corpus in place, reproduce deterministic adjudication, and resume only
the checkpoint-aware judge.

```bash
set -euo pipefail
test "$(git branch --show-current)" = master
git fetch origin master
test -z "$(git status --porcelain)"
REPO="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
test "$REPO" = "manfromnowhere143/telos"
workflow_history_payload() {
  local workflow_id="$1"
  local event="${2:-}"
  local payload
  if test -n "$event"; then
    payload="$(gh api -X GET "repos/$REPO/actions/workflows/$workflow_id/runs" -f event="$event" -f page=1 -f per_page=100)" || return 1
  else
    payload="$(gh api -X GET "repos/$REPO/actions/workflows/$workflow_id/runs" -f page=1 -f per_page=100)" || return 1
  fi
  test "$(jq -r '[(.total_count | type), (.workflow_runs | type)] | @tsv' <<< "$payload")" = $'number\tarray' || return 1
  test "$(jq -r '.total_count == (.workflow_runs | length)' <<< "$payload")" = true || return 1
  test "$(jq -r '[.workflow_runs[] | type] | all(. == "object")' <<< "$payload")" = true || return 1
  printf '%s\\n' "$payload"
}
ITER207_WORKFLOW_BINDING="$(gh api -X GET "repos/$REPO/actions/workflows/iter207-execute.yml" --jq '[.id,.name,.path,.state] | @tsv')"
ITER207_WORKFLOW_ID="$(printf '%s\\n' "$ITER207_WORKFLOW_BINDING" | cut -f1)"
[[ "$ITER207_WORKFLOW_ID" =~ ^[1-9][0-9]*$ ]]
test "$ITER207_WORKFLOW_BINDING" = "$ITER207_WORKFLOW_ID"$'\titer207-execute\t.github/workflows/iter207-execute.yml\tactive'
ITER206_WORKFLOW_BINDING="$(gh api -X GET "repos/$REPO/actions/workflows/iter206-execute.yml" --jq '[.id,.name,.path,.state] | @tsv')"
ITER206_WORKFLOW_ID="$(printf '%s\\n' "$ITER206_WORKFLOW_BINDING" | cut -f1)"
[[ "$ITER206_WORKFLOW_ID" =~ ^[1-9][0-9]*$ ]]
test "$ITER206_WORKFLOW_BINDING" = "$ITER206_WORKFLOW_ID"$'\titer206-execute\t.github/workflows/iter206-execute.yml\tactive'
test "$ITER206_WORKFLOW_ID" != "$ITER207_WORKFLOW_ID"
ITER206_ALL_PAYLOAD="$(workflow_history_payload "$ITER206_WORKFLOW_ID")"
ITER206_DISPATCH_PAYLOAD="$(workflow_history_payload "$ITER206_WORKFLOW_ID" workflow_dispatch)"
test "$(jq -r '.total_count' <<< "$ITER206_ALL_PAYLOAD")" -eq 0
test "$(jq -r '.total_count' <<< "$ITER206_DISPATCH_PAYLOAD")" -eq 0
ITER207_ALL_PAYLOAD="$(workflow_history_payload "$ITER207_WORKFLOW_ID")"
ITER207_DISPATCH_PAYLOAD="$(workflow_history_payload "$ITER207_WORKFLOW_ID" workflow_dispatch)"
test "$(jq -r '.total_count' <<< "$ITER207_ALL_PAYLOAD")" -eq 1
test "$(jq -r '.total_count' <<< "$ITER207_DISPATCH_PAYLOAD")" -eq 1
RUN_ID="$(jq -r '.workflow_runs[0].id // empty' <<< "$ITER207_DISPATCH_PAYLOAD")"
APPROVED_SHA="$(gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '.head_sha')"
RUN_BINDING="$(gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '[.id,.workflow_id,.name,.event,.head_branch,.head_sha,.path,.run_number,.run_attempt] | @tsv')"
test "$RUN_BINDING" = "$RUN_ID"$'\t'"$ITER207_WORKFLOW_ID"$'\titer207-execute\tworkflow_dispatch\tmaster\t'"$APPROVED_SHA"$'\t.github/workflows/iter207-execute.yml\t1\t1'
test "$(git rev-parse HEAD)" = "$APPROVED_SHA"
test "$(gh run view "$RUN_ID" --json status,conclusion,attempt --jq '[.status,.conclusion,.attempt] | join(" ")')" = "completed success 1"
EXECUTION_DIR="experiments/iter207_claim_integrity_and_admission_recovery/proof/raw/execution"
test -d "$EXECUTION_DIR"
test ! -L "$EXECUTION_DIR"
python3 -I -S scripts/validate_iter205_pre_dispatch_null.py
python3 -I -S scripts/validate_iter206_pre_publication_null.py
python3 -I -S scripts/audit_iter207_claim_integrity.py --check
python3 -I -S scripts/build_iter207_runtime_manifest.py --check
python3 -I -S scripts/collect_iter207_execution.py check \\
  --execution-dir "$EXECUTION_DIR" \\
  --aggregate-receipt "$EXECUTION_DIR/_telos_iter207_execution_complete.receipt.json" \\
  --spec-index experiments/iter203_iter202_safety_recovery/proof/raw/specs/index.json \\
  --runtime-manifest experiments/iter207_claim_integrity_and_admission_recovery/proof/raw/runtime_manifest.json
python3 -I -S scripts/adjudicate_iter207_claim_integrity_and_admission_recovery.py
python3 -I -S scripts/run_iter207_claim_integrity_and_admission_recovery_blind_judge.py
```

## Verification Before Action

Run from the standalone TELOS repository root:

```bash
python3 -m compileall telos scripts tests
ruff check .
pytest -q
python3 scripts/validate_json.py
python3 scripts/validate_docs.py
python3 scripts/validate_current_paper.py
python3 scripts/validate_mission_loop.py
python3 scripts/validate_supply_chain.py
python3 scripts/validate_detector_methodology_correction.py
python3 scripts/validate_iter200_corrected_result.py
python3 scripts/build_iter202_solve_targets.py --check
python3 scripts/audit_iter202_sample_overlap.py --check
python3 scripts/build_iter203_safety_recovery.py --check
python3 scripts/build_iter203_runtime_manifest.py --check
python3 scripts/validate_iter203_infrastructure_null.py
python3 scripts/validate_iter204_pre_dispatch_null.py
python3 scripts/validate_iter205_pre_dispatch_null.py
python3 scripts/validate_iter206_pre_publication_null.py
python3 scripts/audit_iter207_claim_integrity.py --check
python3 scripts/build_iter207_runtime_manifest.py --check
python3 scripts/validate_iter207_publication_safety.py --check
python3 scripts/validate_iter207_runtime_recovery.py
python3 scripts/validate_learning_ledger.py
python3 scripts/validate_handoff.py
```
"""
    replacements = {
        "@@GENERATED@@": generated,
        "@@REPOSITORY_BANNER@@": repository_banner(),
        "@@SOURCE_BRANCH@@": source_branch,
        "@@SOURCE_COMMIT@@": source_commit,
        "@@WORKTREE@@": worktree,
        "@@EXPERIMENTS@@": experiments,
        "@@ACTIVE_GATE@@": gate,
        "@@UPSTREAM_GATE@@": upstream_gate,
        "@@ITER203_RUN_ID@@": ITER203_RUN_ID,
        "@@ITER203_RUN_ATTEMPT@@": ITER203_RUN_ATTEMPT,
        "@@ITER204_WORKFLOW_ID@@": ITER204_WORKFLOW_ID,
        "@@ITER204_FEATURE_PUSH_RUN_ID@@": ITER204_FEATURE_PUSH_RUN_ID,
        "@@ITER204_FEATURE_PUSH_COMMIT@@": ITER204_FEATURE_PUSH_COMMIT,
        "@@ITER204_PRIMARY_PUSH_RUN_ID@@": ITER204_PRIMARY_PUSH_RUN_ID,
        "@@ITER204_MERGE_COMMIT@@": ITER204_MERGE_COMMIT,
        "@@ITER205_PULL_REQUEST@@": ITER205_PULL_REQUEST,
        "@@ITER205_FEATURE_COMMIT@@": ITER205_FEATURE_COMMIT,
        "@@ITER205_MERGE_COMMIT@@": ITER205_MERGE_COMMIT,
        "@@ITER205_PRIMARY_CI_RUN_ID@@": ITER205_PRIMARY_CI_RUN_ID,
        "@@ITER205_WORKFLOW_ID@@": ITER205_WORKFLOW_ID,
        "@@ITER205_FEATURE_PUSH_RUN_ID@@": ITER205_FEATURE_PUSH_RUN_ID,
        "@@ITER205_PRIMARY_PUSH_RUN_ID@@": ITER205_PRIMARY_PUSH_RUN_ID,
        "@@ITER205_PUBLIC_MANIFEST_SHA256@@": ITER205_PUBLIC_MANIFEST_SHA256,
        "@@ITER207_BRANCH@@": ITER207_BRANCH,
    }
    for marker, value in replacements.items():
        content = content.replace(marker, value)
    if "@@" in content:
        unresolved = sorted(set(re.findall(r"@@[A-Z0-9_]+@@", content)))
        raise RuntimeError(f"unresolved handoff template markers: {unresolved}")
    return content


def main() -> None:
    generated = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    branch = current_branch()
    source_branch, source_commit = source_provenance(branch)
    raw_status = run(["git", "status", "--short"])
    if raw_status:
        raise RuntimeError(
            "handoff generation requires the exact clean source commit; "
            f"working tree is not clean:\n{raw_status}"
        )
    worktree = normalize_worktree_status(raw_status)
    gate = active_gate()
    upstream_gate = frozen_upstream_gate()
    experiments = "\n".join(experiment_status(gate)) or "- no experiments yet"
    content = render_handoff(
        generated=generated,
        source_branch=source_branch,
        source_commit=source_commit,
        worktree=worktree,
        experiments=experiments,
        gate=gate,
        upstream_gate=upstream_gate,
    )
    Path("HANDOFF.md").write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
