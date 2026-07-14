# Iteration 194 - Certified-Resolved Oracle and Runner Fix

Status: PRE-REGISTERED, result pending. No provider calls, SWE-bench executions, or cloud resources have
been run for this gate.

## Why this gate exists

iter193 executed `16` certified-resolved-but-wrong candidates on native-x86 CI and returned a null: `0`
witnessed certified-and-wrong rows. The null decomposed into two fixable gaps, not a scientific dead end.

1. **Runner gap (`10/16` blocked).** The Phase B harness ran a bare `python -m pytest`. The django
   testbed has no `pytest` (it uses `tests/runtests.py` with a settings module); astropy's `-rA` capture
   produced no per-test lines under its collection. Those `10` candidates were never executed and were
   conservatively marked `not_certified`, which is a harness limitation, not a negative.
2. **Oracle-coverage gap (`6/16` undetermined).** The `6` matplotlib candidates executed and were
   certified-resolved, but were identical to gold across their entire test module, so the uncurated-test
   oracle found no wrongness witness. Per iter193, absence of a witness is not evidence of correctness. The
   pre-registered fallback — gold-differential on synthesized inputs — is exactly what these need and was
   never reached.

This gate fixes both, so that the `>= 5` accepted-row bar becomes a fair test of the construction question
rather than a test of harness coverage.

## Inputs

- `experiments/iter193_certified_resolved_reward_hack_construction/proof/raw/phase_a_candidates/`
- `experiments/iter193_certified_resolved_reward_hack_construction/proof/raw/phase_b_execution/`
- `experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/swebench_verified_rows_snapshot.json`
- `.github/workflows/iter193-certified-resolved.yml`, `scripts/ci_certified_resolved_execute.sh`

## What this gate changes

1. **Project-correct execution.** Decide certified-resolved with the runner each instance actually uses:
   the official SWE-bench evaluation harness (`swebench.harness.run_evaluation`) inside the pinned image,
   whose `report.json` gives `resolved`, `FAIL_TO_PASS`, and `PASS_TO_PASS` status directly — the same
   verdict source iter192 read. This removes the framework-specific pytest-invocation fragility for django
   and astropy in one step and aligns certification with the official grader.
2. **Fallback wrongness oracle.** For a certified-resolved candidate with no uncurated failing test, run
   gold and variant on synthesized inputs that exercise the changed function, in the same container, and
   record any input where their observable outputs differ. Rows accepted this way are tagged
   `oracle: synthesized_differential` and reported separately from `oracle: uncurated_test`, never pooled.
   A candidate with neither witness stays `undetermined`.

## Numeric Bars

Minimum pass bars:

- provider calls do not exceed `120` (candidate top-up only; existing iter193 candidates are reused),
- estimated provider spend does not exceed `$15.00`,
- new cloud resources created and not deleted is exactly `0`,
- candidates executed through a project-correct runner is at least `14` of `16` (django + astropy no longer
  silently blocked),
- every accepted row is certified-resolved by the official harness `report.json` (`resolved == true`,
  zero `PASS_TO_PASS` failures),
- every accepted row records either an uncurated failing test or a synthesized-input differential witness,
  with the oracle tagged,
- accepted certified-resolved-and-wrong rows is at least `5`,
- raw harness reports and oracle transcripts retained for every accepted row is `100%`,
- committed secret/private identifier hits are exactly `0`,
- forbidden positive claim hits are exactly `0`.

## Falsifiers

1. Any accepted row is not `resolved == true` in its official harness `report.json`.
2. Any accepted row lacks a recorded, reproducible wrongness witness of its tagged oracle type.
3. Synthesized-input and uncurated-test rows are pooled into a single rate.
4. Gold content, labels, hidden test names, or official reports enter a future detector's prompt.
5. Fewer than `5` accepted rows: the gate publishes a null with the full outcome distribution and a
   construction-hardness bound, and does not relax the bar or re-label blocked candidates.
6. Provider calls exceed `120`, spend exceeds `$15.00`, or a cloud resource is left undeleted.
7. The result presents a leaderboard, model-comparison, model-superiority, state-of-the-art,
   natural-frequency, non-elicited, benchmark-size, broad robustness, production, or product-value claim.

## Claim Boundary

At most, if this gate passes: Telos has `N >= 5` execution-verified rows in which the official SWE-bench
Verified harness certifies a patch as resolved while a recorded wrongness witness (uncurated failing test
or synthesized-input differential, tagged) shows it is wrong, constructed under a bounded, elicited
frontier-adversary budget, with raw evidence retained. If it fails, Telos has an honest
construction-hardness bound over `>= 14` project-correctly executed candidates.

Not supported: any natural-frequency, non-elicited, benchmark-size, corpus-scale, detector, leaderboard,
model-comparison, state-of-the-art, broad robustness, production, or product-value claim.
