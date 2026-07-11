# Iteration 123 - Visible-Test-Anchored Soundness Filter

Status: pre-registered before evaluation. Frozen before the anchor checks were run.

## Why this gate exists

Iter122 automated property generation but named the open risk: a model can propose an unsound
property, and rejecting it seemed to need a gold reference. This gate removes that need. The visible
`FAIL_TO_PASS` test the agent had to pass is a known-correct `(input, output)` pair. Any sound
metamorphic property must hold on that pair. So a property that violates the visible-test anchor is
unsound and can be rejected with no gold reference.

## Method

For each both-miss instance, take the anchor pair(s) from the visible test, and evaluate two
properties on the anchor: the sound property the model generated in iter122, and a constructed
plausible-but-unsound property. A property is kept only if it holds on every anchor pair.

## Anchors and properties

- `django__django-14089`: anchor `inp=[1,2,3] -> out=[3,2,1]`. Sound `out == list(reversed(inp))`;
  unsound `out == sorted(inp)`.
- `django__django-14373`: anchors `1 -> '0001'`, `999 -> '0999'`. Sound
  `len(out)==4 and out.isdigit() and int(out)==inp`; unsound `out == str(inp)`.

## Endpoints

- `sound_kept_rate`: fraction of sound properties that hold on the anchor (kept).
- `unsound_rejected_rate`: fraction of unsound properties that violate the anchor (rejected).

## Acceptance / interpretation rule

If the anchor keeps every sound property and rejects every unsound one, the filter is a valid
gold-free soundness check: unsound proposed properties are caught by the test the agent already had
to pass, with no reference implementation.

## Falsifiers

1. If a sound property violates the anchor, the anchor is too strict; record it.
2. If an unsound property holds on the anchor, the anchor does not catch it; record the miss and note
   that a single anchor pair is insufficient.

## Execution envelope

- pure evaluation, no execution, no provider calls, no GPU, no cloud,
- production/live-domain mutation: forbidden, benchmark/model/SOTA claim: forbidden.

## Claim boundary (pre-committed)

At most: "on two instances, the visible-test anchor kept `N/2` sound properties and rejected `M/2`
unsound properties, with no gold reference." Not a benchmark, model, or SOTA claim; a single anchor
pair is a necessary, not sufficient, soundness condition.
