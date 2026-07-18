# Iter232 — a validated gold-free exercise instrument, and the oracle re-measured

Status: prospective, pre-registered before any iter232 exercise, container preflight, or oracle output exists.
It reuses the frozen iter230 benchmark and the **unchanged** iter231 flag rule.

Predecessor merged master: `ef807b3`.

## Why iter232 exists

Iter231 measured a gold-free execution oracle at `4/13` recall and `10/54` false positives, and showed that
**four of those flags were the instrument failing rather than the patch**: two exercises could not import
against their pinned image, and two applied a single `%` specifier to a multi-element tuple, which raises
unconditionally. A further `16` of the `67` benchmark rows had no exercise at all — `15` rejected by the
safety instrument, `1` lost to a provider error — leaving `u=4` missing positives and `u=12` missing negatives
and making every reported bound wide.

Iter231's conclusion was therefore limited by instrument quality, not by the science. Iter232 repairs the
instrument and re-measures. The question is narrow and worth asking precisely because the answer could go
either way: **when the exercises actually work, does the oracle's recall change?**

## What is fixed and what is not

The **flag rule is not touched**. `experiments/iter231_gold_free_execution_oracle/ADJUDICATION_FREEZE.md`
stays byte-identical and is applied verbatim. Iter232 changes the instrument that produces observations, never
the rule that reads them. The frozen iter230 benchmark (sha `10dc898c…5b8928`) is likewise unchanged.

## The validity gate

An exercise is committed only if it passes every stage:

- **A — static ($0, offline).** Parses; contains no `%`-format applying a single specifier to a multi-element
  tuple (always raises); passes the AST safety instrument; prints a literal `RESULT=`.
- **B — in-container ($0 provider).** Compiles *and executes its import block* inside its own pinned
  SWE-bench image under the iter231 isolation flags. An exercise that cannot import in the environment it will
  run in is not an instrument, and iter231 shipped two such exercises.
- **C — regeneration (provider spend).** Rows failing A or B, plus rows previously recorded `excluded_unsafe`
  or `provider_error`, are regenerated with a hardened prompt and a validate-and-retry loop, bounded at three
  attempts per row.

**The regeneration trigger is instrument validity only.** A row is never regenerated because of its oracle
outcome, its label, or its divergence type. Those are not inputs to stage C, and this is the bar that keeps
iter232 from becoming a detector tuned on known positives.

## Safety allowlist changes

Iter231's exclusions were dominated by exercises reaching for `os`, `tempfile`, `pathlib`, `io`, `requests`,
`pickle`, `eval`, `exec`, and `compile`. Those are genuine rejections and stay rejected; the hardened prompt
steers the generator away from them rather than the instrument being loosened to admit them.

One class is different: `astropy` was rejected solely for absence from the allowlist, though it is a project
package exactly like the already-allowlisted `django`, `sympy`, `numpy`, `sklearn`, and `xarray`. Closing that
gap is not loosening a bar.

Any allowlist change must therefore be enumerated symbol by symbol with a stated reason, and **must not admit
filesystem, network, subprocess, or dynamic-execution capability**. Widening the instrument to raise coverage
is a falsifier, not a result. The isolated container remains the security boundary; the AST check is defense
in depth.

## Endpoints

- **Validated coverage**: rows with a committed exercise passing A and B, out of `67`, against iter231's `51`
  (of which `6` were defective).
- **Recall and false-positive rate** under the unchanged frozen rule, each with a Wilson interval and the full
  missing-outcome triple (observed lower, worst-case missing upper, complete-case), reported **beside**
  iter231's `4/13` and `10/54` and iter230's static `2/13` and `5/54` — not in place of them.
- **Recall split by divergence type**, `crash_or_type` versus `value`.
- Every row still lacking an exercise after three attempts, listed individually with its reason.

## Pre-registered expectation

Stated before any data, so it can be wrong:

1. The four instrument-failure flags disappear, removing two recall hits and two false positives.
2. Recall under the frozen rule settles near iter231's instrument-adjusted `2/13`, plus whatever genuine
   detections the recovered rows contribute.
3. A specific, named target: `iter227/django-11815` is `crash_or_type` and was `excluded_unsafe`, so execution
   never tested the one crash-class patch the static panel caught and execution could not. If it is recovered
   and flagged, `crash_or_type` recall becomes `3/3`.
4. **The value class stays at `0/N`.** This is the ceiling claim, and iter232 is its strongest test yet
   because it removes the excuse that the instrument was simply broken.

Expectation 4 is the one to attack. If a validated exercise genuinely flags a `value`-labelled positive — by
`error_observable` rather than by a crashed exercise — then a gold-free instrument reached the class argued to
be unreachable, and the mitigation-ceiling claim in the paper must be weakened or retracted.

## Acceptance bars

1. The benchmark sha is unchanged (`10dc898c…5b8928`).
2. `ADJUDICATION_FREEZE.md` is byte-identical to its iter231 commit.
3. Every committed exercise passes stages A and B; the passing set is reproducible offline.
4. No exercise generator or executor is shown the gold patch, a hidden test, or the gold-differential witness.
5. Allowlist changes are enumerated and justified; none admits filesystem, network, subprocess, or dynamic
   execution.
6. Recall and false-positive rate are reported together, with intervals, the missing-outcome triple, and the
   divergence split.
7. No sealed predecessor evidence byte changes, and no runtime-manifest-pinned file is edited.

## Falsifiers

- The flag rule or `ADJUDICATION_FREEZE.md` is edited.
- A row is regenerated because of its oracle outcome, label, or divergence type.
- The safety allowlist is widened to admit filesystem, network, subprocess, or dynamic-execution capability.
- Recall is reported without the matching false-positive rate, or without the missing-outcome triple.
- Iter232 is presented as superseding iter231 rather than as the same measurement with a repaired instrument.
- The benchmark is altered, or a runtime-manifest-pinned file is edited.

## Claim boundary

Iter232 measures the **same oracle with a repaired instrument** over the same fixed `13`-positive,
`54`-negative benchmark. A change in recall is a statement about instrument quality, not evidence of a better
detector design, and not a deployable oracle, ranking, or state-of-the-art claim. Intervals remain wide on
`13` positives.

## Execution envelope

Allowed: gold-free exercise-generation provider calls bounded at three attempts per row; container preflight
and safe container execution of validated exercises; local analysis; repository publication. Forbidden: giving
any stage the gold patch, a hidden test, or the witness; executing an exercise that fails stage A or B;
altering the frozen benchmark or the frozen flag rule; editing any runtime-manifest-pinned file; and any
modification of sealed predecessor evidence.
