# Iteration 114 - Batch Native Execution Ground Truth

Status: pre-registered design; executed and published in the same gate (native Django batch run).

## Why this gate exists

Iter113 executed one real instance natively. This gate extends real execution to a batch to (a)
confirm gold resolution is real across multiple instances, not a single lucky case, and (b) measure
the fidelity of the lightweight native harness honestly, since it does not reproduce the full
official SWE-bench Docker environment.

## Batch

Five same-era Django 4.x SWE-bench Verified instances (single shared editable install, Python
3.11), each executed in SWE-bench order (checkout base commit, apply gold, apply hidden
`test_patch`, run FAIL_TO_PASS via `tests/runtests.py`):
`django__django-14089`, `-14311`, `-14349`, `-14373`, `-14771`.

## Endpoints

- `gold_resolution_rate`: fraction whose gold patch makes the real hidden test pass.
- `native_harness_fidelity`: same fraction, framed as a bound on the lightweight harness (an
  instance whose gold applies cleanly but whose test still errors is a fidelity gap, not a claim
  that the gold is wrong).
- `detector_false_positive_rate` on the five real gold patches (reproducible in CI).

## Acceptance / interpretation rule

This gate is descriptive, not pass/fail on a target rate. It records the real resolution rate and
enumerates any instance the native harness cannot resolve, with its concrete error, so the harness
fidelity is stated rather than assumed.

## Falsifiers

1. If a gold patch fails to apply cleanly, that instance is excluded as a harness error, not a
   resolution failure.
2. If the detector flags any of the five real gold patches, the false-positive claim is weakened;
   record it.

## Execution envelope

- native execution only, no provider calls, no GPU, no cloud,
- production/live-domain mutation: forbidden, benchmark/model/SOTA claim: forbidden.

## Claim boundary (pre-committed)

At most: "on five same-era Django instances executed natively, N/5 gold patches resolved the real
hidden test and the detector flagged 0/5 as tamper; the non-resolving instance is a stated
native-harness fidelity gap." Not a benchmark, resolved-rate, model, or SOTA claim. The native
transcript is observed evidence; the detector verdicts on the committed gold fixtures are
reproducible.
