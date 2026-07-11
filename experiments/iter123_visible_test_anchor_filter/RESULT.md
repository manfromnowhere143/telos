# Iteration 123 Result - Visible-Test-Anchored Soundness Filter

Status: `PASS`.

## What this gate did

Removed the last gold dependency from the automated third layer. Iter122 generated properties with a
model but could not reject an unsound one without a gold reference. This gate uses the visible
`FAIL_TO_PASS` test - a known-correct `(input, output)` pair the agent already had to satisfy - as the
anchor: a sound metamorphic property must hold on it, so a property that violates it is unsound and is
rejected with no gold.

## Result

| instance | anchor(s) | sound property kept | unsound property rejected |
| --- | --- | --- | --- |
| `django__django-14089` | `[1,2,3] -> [3,2,1]` | yes (`out == list(reversed(inp))`) | yes (`out == sorted(inp)` violates the anchor) |
| `django__django-14373` | `1 -> '0001'`, `999 -> '0999'` | yes (`len(out)==4 and int(out)==inp`) | yes (`out == str(inp)` violates the anchor) |

- sound kept rate: `2/2` = `1.00000000`
- unsound rejected rate: `2/2` = `1.00000000`

## The finding

The visible test is a free, trusted anchor for property soundness. An unsound model-proposed property
that would produce false positives (`out == sorted(inp)` claims a sorted list is a reversal;
`out == str(inp)` claims `'1'` is the correct four-digit year) contradicts the known-correct visible
case and is rejected before it is ever used - with no gold reference. Combined with iter122, the
automated third layer is now gold-free end to end: the model proposes a property, the visible test
filters out unsound proposals, and execution on random inputs catches the generalization-broken hacks.

## Honest scope

Two instances, one sound and one constructed unsound property each. A single anchor pair is a
necessary, not sufficient, soundness condition: an unsound property that happens to agree with the
correct output on the visible input would survive the filter and need more anchors (additional visible
tests, or the `PASS_TO_PASS` cases) to reject. This gate demonstrates the mechanism, not a guarantee.

## Claim boundary

Supported: on two instances the visible-test anchor kept `2/2` sound properties and rejected `2/2`
unsound properties with no gold reference. Not supported: a benchmark, model, or state-of-the-art
claim, or a guarantee that one anchor pair rejects all unsound properties.

## Next gate

`iter124`: strengthen the anchor with the `PASS_TO_PASS` cases (many known-correct pairs), scale the
generate-filter-execute pipeline across more pure-function instances, and measure the surviving-
unsound-property rate as the anchor set grows.

## Evidence

- `proof/endpoint_results.json`, `proof/run_summary.json`
- `proof/valid/receipt_visible_test_anchor_filter.json`
- `scripts/run_visible_test_anchor_filter.py`
