# Iteration 126 - Gold-Free Soundness Gate

Status: pre-registered before evaluation. Frozen before the anchor checks were run.

## Why this gate exists

Iter125 rejected the unsound `10999` property using the gold implementation, which is not available
at real verification time. This gate makes the whole soundness decision gold-free: a synthesized
property is accepted only if it is non-trivial (uses the random input; relates `inp` and `out`) and
holds on the visible-test anchor - the known-correct `(input, output)` pairs read off the
FAIL_TO_PASS test. It then checks whether this gold-free gate reproduces the gold-based classification
and, in particular, rejects the unsound `10999` property.

## Method

For each iter125 harness with a determinable visible-test anchor, evaluate its `check` on the anchor
pair(s) with a restricted evaluator. A property is kept only if non-trivial and holding on every
anchor. Compare to the iter125 gold-based genuine-sound set.

## Anchors (read off the visible tests)

- `14089`: `[1,2,3] -> [3,2,1]`. `14373`: `datetime(1,1,1) -> '0001'`. `13670`: `4 -> '04'`.
- `10999`: `'-172800' -> timedelta(days=-2)` (a non-None case the unsound property should fail).
- `11276`: vacuous (rejected by non-triviality, no anchor needed).
- `11848`: anchor is date-dependent (mocked utcnow for two-digit-year rollover); recorded as
  anchor-not-applicable.
- `11206`: synthesis failed in iter125; no harness.

## Endpoints

- `gold_free_kept_ids`: harnesses non-trivial and holding on their anchor.
- `unsound_rejected_by_anchor`: whether the `10999` unsound property violates its anchor.
- `agreement_with_gold_based`: whether the gold-free decision matches the iter125 gold-based one where
  an anchor is applicable.

## Acceptance / interpretation rule

If the gold-free gate keeps the genuine-sound harnesses, rejects the unsound one, and rejects the
vacuous one, the soundness decision is gold-free. Instances whose anchor is not applicable are
recorded, not silently counted.

## Falsifiers

1. If the anchor rejects a genuine-sound property, the anchor is too strict; record it.
2. If the anchor keeps the unsound `10999` property, one anchor pair is insufficient and more are
   needed.

## Execution envelope

- pure evaluation, no execution, no provider calls, no GPU, no cloud,
- production/live-domain mutation: forbidden, benchmark/model/SOTA claim: forbidden.

## Claim boundary (pre-committed)

At most: "a gold-free gate (non-triviality plus visible-test anchor) kept `N` genuine-sound harnesses
and rejected the unsound and vacuous ones, agreeing with the gold-based decision where an anchor was
applicable." Not a benchmark, model, or SOTA claim.
