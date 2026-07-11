# Iteration 138 - Dataset-Wide Applicability Survey of the Property Layer

Status: pre-registered design; executed on the full dataset.

## Why this gate exists

Iter129-iter137 showed the property-based third layer works on single-testable-function instances but
left the question of how broadly that criterion holds. Rather than add one more property instance, this
gate measures the layer's applicability across the whole `SWE-bench_Verified` dataset, by repo - a
reproducible number that bounds where Layer 3 can apply.

## Method

For all 500 instances, apply the iter129 structural criterion: a candidate is applicable if it edits a
single source file and its `FAIL_TO_PASS` is narrow (at most three tests). Report the applicability rate
overall and per repo.

## Endpoints

- overall structural applicability rate over 500 instances.
- per-repo applicability rate.

## Acceptance / interpretation rule

The survey reports the rate honestly, and states clearly that structural applicability is an upper bound
on the layer's reach: it is necessary but not sufficient, because an applicable instance still needs a
function with a derivable gold-free property, which is abundant in mathematical libraries and rarer in
application libraries (iter130).

## Falsifiers

1. The structural criterion is a necessary condition only; the survey must not present it as the
   property genuine-sound rate.
2. Repos with low applicability are reported as-is, not smoothed.

## Execution envelope

- dataset analysis only, no execution, no provider calls, no GPU, no cloud,
- production/live-domain mutation: forbidden, benchmark/model/SOTA claim: forbidden.

## Claim boundary (pre-committed)

At most: "the single-testable-function structural criterion is met by N/500 SWE-bench Verified instances
overall, with the per-repo breakdown recorded; this is an upper bound on the property layer's reach, not
the property genuine-sound rate." Not a benchmark, model, or SOTA claim.
