#!/usr/bin/env python3
"""Generate the one-time iter211 handoff from its exact clean source commit."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BRANCH = "agent/iter211-tcp1-materialization"
BASELINE_MERGE = "fb348eb1f67c0605679cd56a1cfa210cf192db03"
RECEIPT_PATH = ROOT / "experiments/iter211_tcp1_materialization_preflight/proof/receipt_v2.json"
HANDOFF = ROOT / "HANDOFF.md"


def git(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        diagnostic = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git command failed: {' '.join(arguments)}: {diagnostic}")
    return result.stdout.rstrip()


def render() -> str:
    branch = git("branch", "--show-current")
    if branch != BRANCH:
        raise RuntimeError(f"iter211 handoff requires branch {BRANCH}, got {branch!r}")
    source = git("rev-parse", "HEAD")
    if re.fullmatch(r"[0-9a-f]{40}", source) is None:
        raise RuntimeError("iter211 source commit is not a full Git id")
    parents = git("rev-list", "--parents", "-n", "1", source).split()
    if parents != [source, BASELINE_MERGE]:
        raise RuntimeError("iter211 source must be the direct child of merged iter210 master")
    if git("status", "--short"):
        raise RuntimeError("iter211 handoff requires a clean source worktree")

    from scripts.build_iter211_receipt import BINDINGS  # noqa: PLC0415
    from telos.proof import load_receipt_v2  # noqa: PLC0415

    source_delta = set(git("diff", "--name-only", BASELINE_MERGE, source).splitlines())
    receipt_relative = RECEIPT_PATH.relative_to(ROOT).as_posix()
    if source_delta != set(BINDINGS) | {receipt_relative}:
        raise RuntimeError("iter211 source delta differs from the artifact-bound closure")
    receipt = load_receipt_v2(RECEIPT_PATH, artifact_root=ROOT)
    if receipt.status != "blocked":
        raise RuntimeError("iter211 scientific-execution receipt must be blocked")

    generated = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return f"""# HANDOFF — iter211 TCP-1 materialization preflight

Generated: {generated} from the exact clean source commit below. Read Current Gates first.

TELOS is a standalone repository. Resolve its root with `git rev-parse --show-toplevel`, then run every TELOS command from that root.

## Repository State

```text
handoff_schema: telos.iter211.handoff.v1
source_branch: {BRANCH}
source_commit: {source}
predecessor_merge: {BASELINE_MERGE}
publication_target: master
```

The source worktree was clean. This file is the sole allowed delta in the iter211 seal commit.

## Current Gates

Active gate: `experiments/iter207_claim_integrity_and_admission_recovery/HYPOTHESIS.md`

This remains sealed historical runtime authority only. It authorizes no current scientific execution.

Active publication gate: `experiments/iter211_tcp1_materialization_preflight/HYPOTHESIS.md`

Frozen upstream gate recorded by runtime-bound `CONTINUITY.md`: `experiments/iter202_natural_rate_scaled/HYPOTHESIS.md`

Materialization-preflight status: **PASS; scientific execution BLOCKED**.

## Exact Merged Baseline

Iter210 PR `#10` merged at exact two-parent commit `{BASELINE_MERGE}` with the old master first and iter210
seal `c109312d5ee525599abfbac178c3fb245117ab49` second. Non-scientific CI passed for branch push run
`29496323167`, pull-request run `29496355871`, and merged-master run `29496560409`, each with Python 3.11
and 3.12 jobs. The recurring iter204 workflow parser record remains frozen historical infrastructure
evidence and is not current CI.

## What Iter211 Establishes

Iter211 materializes TCP-1's protocol, deterministic seeds, task/trajectory/label/aggregate schemas,
analysis-input contract, exact statistical accounting, separate-control policy, resource envelope,
isolation threat model, and machine-readable admission decision.

It does not materialize a scientific cohort. There are zero admitted tasks and no filled reviewer, model,
hidden-test, control, runtime, hardware, external-timestamp, throughput, or monetary-budget evidence. The
admission report has two passing local-design gates and nine blocked external gates. Execution authorization
is false and cannot be inferred from repository publication.

## Source Receipt

Receipt path: `experiments/iter211_tcp1_materialization_preflight/proof/receipt_v2.json`

Receipt status: `blocked`

Receipt evidence count: `{len(receipt.evidence)}`

Receipt closure SHA-256: `{receipt.evidence_closure_sha256}`

Receipt SHA-256: `{receipt.receipt_sha256}`

The handoff and receipt guards check exact source Git blobs. The receipt proves byte identity, not authorship,
external chronology, license, independence, or semantic truth.

## Verification Before Publication

Run from the repository root:

```bash
git status --short
git show --no-ext-diff --stat {source}
ruff check .
python3 -m compileall -q telos scripts tests
pytest -q
python3 scripts/validate_json.py
python3 scripts/validate_docs.py
python3 scripts/validate_current_paper.py
python3 scripts/validate_mission_loop.py
python3 scripts/validate_supply_chain.py
python3 scripts/build_iter210_receipt.py --check
python3 scripts/validate_iter210_pr_synthetic_merge_recovery.py
python3 scripts/build_iter211_tcp1_packet.py --check
python3 scripts/build_iter211_receipt.py --check
python3 scripts/validate_iter211_tcp1_materialization_preflight.py
python3 scripts/validate_handoff.py
```

Before merge, verify the exact branch tip, base, receipt, review state, required push and pull-request CI,
and two-parent mergeability. Do not amend, rebase, force-push, or extend the branch after its seal.

## Publication Boundary

The seal commit must be the direct child of source commit `{source}` and modify exactly `HANDOFF.md`. Publish
that unchanged source-plus-handoff tip once on `{BRANCH}` and open one draft pull request against `master`.
Merge once with a two-parent merge commit only after both non-scientific CI matrices pass at the exact tip
and no substantive review blocker remains.

Repository publication authorizes no release, paper submission, provider request, GPU allocation,
scientific container or trajectory, workflow dispatch or rerun, deployment, payment, or scientific action.

## Scientific Boundary and Next Gate

Iter211 contributes no scientific `N`, `k`, `u`, benchmark score, effect estimate, model comparison,
population estimate, product-efficacy result, deployment claim, priority claim, or state-of-the-art claim.

The next separately versioned gate is
`experiments/iter212_tcp1_independent_cohort_and_custody_freeze/HYPOTHESIS.md`. It may fill genuine human,
model, task, hidden-test, control, runtime, isolation, timestamp, and budget evidence. It authorizes no model
call, accelerator allocation, or scientific trajectory. A later throughput gate is required before any
bounded pilot execution can be considered.

This iteration made three read-only GitHub CLI metadata queries and no pre-seal remote mutation. The CLI's
internal HTTP request count was not instrumented; no exact HTTP request count is claimed.
"""


def main() -> int:
    if "handoff_schema: telos.iter211.handoff.v1" in HANDOFF.read_text(encoding="utf-8"):
        raise RuntimeError("iter211 handoff already exists; refusing regeneration")
    HANDOFF.write_text(render(), encoding="utf-8")
    print("iter211 handoff builder: wrote one source-bound blocked-execution handoff")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
