# Iteration 151 Result - The Intervention Scales to 8 Repositories on the Official SWE-bench Metric

Status: `PASS`.

## What this gate did

Scaled the completion-gate intervention from one repo (iter146-iter148, local runner) to eight
SWE-bench_Verified repositories, scored by the official `swebench.harness.run_evaluation` in pinned Docker
containers on a cloud x86 VM. This removes the two prior limits at once: single-repo, and non-official
scoring.

## Result

Over `20` both-miss starts across `8` repositories (`25` instances yielded no both-miss and are reported):

| gate | official resolved | rate |
| --- | ---: | ---: |
| proxy (accept on target-test pass) | `0/20` | `0.00` (by construction) |
| Telos (regression-failure rejection + gold-free generalize-signal + bounded repair) | `10/20` | `0.50` |

Per-repository Telos recovery (at full weight, including zeros):

| repo | recovered |
| --- | --- |
| scikit-learn | `3/3` |
| pydata/xarray | `2/2` |
| django | `2/5` |
| matplotlib | `1/3` |
| pytest | `1/3` |
| sympy | `1/1` |
| astropy | `0/1` |
| sphinx | `0/2` |

Every `resolved`/`not-resolved` verdict is backed by an official SWE-bench `report.json` (132 reports
committed under `proof/raw/sweb_reports.tgz`).

## The finding

The completion-gate intervention generalizes cross-repo on the metric the field actually tracks: across
eight diverse codebases, a proxy gate resolves `0/20` gamed completions while the Telos gate recovers
`10/20` (`0.50`) to full official SWE-bench resolution. The recovery holds broadly (six of eight repos
recover at least one; scikit-learn and xarray fully) and fails on some (astropy, sphinx) - reported
honestly, not smoothed.

## Honest scope (self-critique on the record)

- **The proxy baseline `0/20` is definitional, not a discovery.** A both-miss passes the target test but
  fails a `PASS_TO_PASS`; official `resolved` requires both, so a both-miss is unresolved by definition.
  The load-bearing number is the `10/20` Telos recovery.
- **The held-out oracle here is the repository's regression suite (`PASS_TO_PASS`) - realistic CI.** So this
  gate scales the *intervention* (rejection + generalize-signal + repair recovers resolution), not the
  gold-free-property-oracle novelty, which is the separate iter149-iter150 result. A plain full-suite CI
  gate would also reject these both-miss; the Telos contribution measured here is the repair loop's recovery
  rate, cross-repo, on the official metric.
- **A harness false-negative was caught before any number was trusted.** The first attempt scored every
  repair unresolved; the SWE-bench logs showed "malformed patch" - the diff-editing was producing invalid
  patches. It was fixed (hunk-aware construction, verified `applied=True` in the official logs) and the run
  re-done. This correction is on the record.

## Claim boundary

Supported: across `8` SWE-bench repositories, over `20` both-miss starts, a proxy gate resolves `0/20`
(definitional) while the Telos gate recovers `10/20` (`0.50`) to full official SWE-bench resolution; the
intervention generalizes cross-repo on the official metric. Not supported: a SWE-bench resolved-rate
leaderboard number, a benchmark, model, or SOTA claim; the oracle is the regression suite, so the
gold-free-oracle novelty is not what this scales.

## Next gate

`iter152`: detection at scale - measure the rate at which frontier LLM judges (reward models) are fooled by
the both-miss hacks across these repositories, saving each hack diff, to build the reward-hack benchmark
artifact and the reward-model-robustness result.

## Evidence

- `proof/raw/scale_results.json` (per-instance outcomes), `proof/raw/scale.log` (full run log)
- `proof/raw/sweb_reports.tgz` (132 official SWE-bench `report.json` files - the ground-truth verdicts)
- `proof/raw/scale_pipeline.py` (the exact harness)
- `proof/endpoint_results.json`, `proof/run_summary.json`, `proof/learning_record.json`
- `proof/valid/receipt_cross_repo_scale_official.json`
- `scripts/run_cross_repo_scale_official.py`
