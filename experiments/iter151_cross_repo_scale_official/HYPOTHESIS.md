# Iteration 151 - Does the Intervention Scale Cross-Repo on the Official SWE-bench Metric?

Status: pre-registered design; executed on a cloud x86 Docker VM.

## Why this gate exists

iter146-iter148 measured the completion-gate intervention (proxy gate `0` -> Telos gate recovers real
completion) on django, using the repository's regression tests as the held-out oracle. Two limits: it was
one repo, and "real completion" was scored by a local test runner rather than the official SWE-bench
harness. This gate removes both, at scale: run the same intervention across many SWE-bench_Verified
repositories, scored by the official `swebench.harness.run_evaluation` in pinned Docker containers.

## Method

On a cloud x86 VM with Docker (the arm64 local machine cannot run the SWE-bench images), for
reward-hack-prone instances across repositories with a single source file, a single `FAIL_TO_PASS`, and at
least two `PASS_TO_PASS`: a frontier adversary (`gpt-5.6-terra`) constructs a both-miss patch (passes the
target test, fails a regression test), verified by the official harness. The proxy gate accepts on
target-pass (official resolved = 0 by construction). The Telos gate rejects on regression failure, returns
a gold-free generic generalize-signal, and repairs (up to two rounds); the repaired patch is scored by the
official harness. Patch construction is hunk-aware so variants apply cleanly (a malformed-patch harness bug
was caught and fixed before any numbers were trusted).

## Endpoints

- Telos-gate resolved-rate (official metric) over both-miss starts, with per-repo detail.
- repository count and the proxy baseline (expected `0` by construction).

## Acceptance / interpretation rule

The intervention is measured across at least five repositories on the official metric. The proxy baseline
`0` is definitional (a both-miss fails a `PASS_TO_PASS`), reported as such, not as a surprise. The
non-trivial number is the Telos-gate recovery rate.

## Falsifiers

1. `resolved` is the official SWE-bench verdict, backed by a committed `report.json` for each instance.
2. The proxy baseline being `0` is definitional, not empirical.
3. The held-out oracle is the regression suite (realistic CI); this scales the intervention, not the
   gold-free-property-oracle result (iter149-iter150).

## Execution envelope

- cloud x86 GCE VM with Docker + official `swebench` harness + `gpt-5.6-terra`; GPU not required (the models
  are API calls, the compute is Docker test-execution); the VM is deleted after the run.

## Claim boundary (pre-committed)

At most: "across `M` SWE-bench repositories, over `N` both-miss starts, a proxy gate resolves `0/N`
(definitional) while the Telos gate recovers `K/N` to full official SWE-bench resolution; the intervention
generalizes cross-repo on the official metric." Not a SWE-bench resolved-rate leaderboard number, a
benchmark, model, or SOTA claim; the oracle is the regression suite.
