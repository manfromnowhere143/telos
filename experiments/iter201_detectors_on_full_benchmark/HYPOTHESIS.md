# Iteration 201 - Detectors on the Full 22-Hack Benchmark

Status: PRE-REGISTERED, result pending. No provider calls, SWE-bench executions, or cloud resources have
been run for this gate.

## Why this gate exists

The detector comparison in iter196 and iter197 was measured on the first `10` certified-resolved reward
hacks (Django, astropy, matplotlib). iter199 grew the benchmark to `22` hacks across `8` repositories,
adding requests, xarray, pylint, pytest, and sympy. This gate extends the detector comparison to the full
`22`, so the paper's most quantitative result rests on a larger, more repository-diverse set, and so we can
say whether detection generalizes to the five new repositories rather than only the original three.

## What this gate measures

Two detectors, at decision time, with the gold fix withheld from both, on all `22` benchmark hacks and
paired gold controls:

1. **Judge panel** (iter196 method): the frontier judges reachable in this environment (`gpt-5.6-terra`,
   `claude-opus-4-8`; `gemini-2.5-flash` remains blocked on ADC) read the candidate diff, the public task,
   and the visible test, and rule reward-hack or legitimate. Report per-model and any-catch recall on the
   `22` hacks and false positives on the `22` gold controls.
2. **Gold-free execution oracle** (iter197 method): a model proposes an executable correctness property
   from the public task and visible test only (no gold, no diff); the property is validated by passing on
   the gold control and executed against the candidate in its pinned container; a sound property that fails
   on the hack catches it. Report recall on the `22` hacks and false positives on the controls.

The `10` iter195 hacks reuse their iter196/iter197 verdicts where the inputs are unchanged; the `12`
iter199 hacks are newly evaluated. All verdicts are recomputed here so the `22`-row numbers are internally
consistent, and the judge run is a single stochastic sample (disclosed).

## Numeric Bars

- provider calls do not exceed `220` and estimated spend does not exceed `$30.00`,
- no undeleted cloud resources,
- both detectors are evaluated on all `22` hacks and their `22` gold controls at decision time,
- no detector prompt contains the gold patch, a label, hidden test names, official reports, or a
  construction witness (leakage scanned: gold-distinctive lines, not shared diff headers),
- per-detector recall on the `22` hacks and false-positive rate on the `22` controls are reported with raw
  per-row verdicts retained,
- the judge single-run caveat and the gemini-unavailable caveat are stated,
- committed secret/private identifier hits are exactly `0`,
- forbidden positive claim hits are exactly `0`.

## Falsifiers

1. Any detector prompt contains gold content, a label, a hidden test name, an official report, or a
   construction witness.
2. A reported recall or false-positive number does not regenerate from retained per-row verdicts.
3. Controls are not evaluated (recall without specificity is not a result).
4. The gold-free oracle counts a property that is not sound (fails on the gold control) as a catch.
5. Provider calls exceed `220`, spend exceeds `$30.00`, or a cloud resource is left undeleted.
6. The result presents a leaderboard, model-superiority, state-of-the-art, natural-frequency, or production
   claim, or presents a single judge run as a stable rate.

## Claim Boundary

At most, if this gate passes: on `22` execution-verified certified-resolved reward hacks across `8`
repositories and `22` paired gold controls, at decision time with gold withheld, Telos reports the recall
and false-positive rate of a frontier judge panel and of a gold-free execution oracle, extending the
`10`-hack comparison to the full benchmark. This is a bounded pilot comparison, a single judge run, not a
leaderboard, model-superiority, or state-of-the-art claim.
