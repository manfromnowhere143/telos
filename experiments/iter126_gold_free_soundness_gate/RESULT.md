# Iteration 126 Result - Gold-Free Soundness Gate

Status: `PASS`.

## What this gate did

Removed the gold reference from the soundness decision. Iter125 used the gold implementation to catch
the unsound `10999` property. This gate replaces that with a gold-free gate: a synthesized property is
kept only if it is non-trivial (uses the random input; relates `inp` and `out`) and holds on the
visible-test anchor - the known-correct `(input, output)` pairs read off the FAIL_TO_PASS test.

## Result

| decision | instances |
| --- | --- |
| kept (non-trivial and holds on anchor) | `14089`, `14373`, `13670` |
| rejected as unsound (violates the anchor, no gold) | `10999` |
| rejected as vacuous (fails non-triviality) | `11276` |
| anchor not applicable (mocked-date dependent) | `11848` |

- agreement with the iter125 gold-based decision where an anchor is applicable: `true`

## The finding

The soundness decision is gold-free. The `10999` property was built only for the `out is None` cases
and evaluates to false on the anchor `'-172800' -> timedelta(days=-2)` (a non-None case), so the
visible-test anchor rejects it with no gold reference - exactly the property iter125 needed the gold
implementation to catch. The vacuous `11276` harness is rejected by non-triviality, and the three
genuine-sound properties hold on their anchors and are kept. Where an anchor is applicable, the
gold-free decision matches the gold-based one.

Combined with iter122-iter125, the automated third layer is now gold-free at every step: the model
proposes a harness from the test source, the input generator is validated, the property is retried on
failure, and the property is accepted only if non-trivial and consistent with the visible-test anchor
- no gold implementation anywhere in the loop.

## Honest scope

The `11848` anchor depends on a mocked `utcnow` for two-digit-year rollover and is recorded as not
applicable rather than forced; a date-independent anchor or the `PASS_TO_PASS` cases would cover it. A
single anchor pair is a necessary, not sufficient, soundness condition - it rejected this unsound
property, but an unsound property agreeing with the correct output on the anchor input would need more
anchors.

## Claim boundary

Supported: a gold-free gate (non-triviality plus the visible-test anchor) kept `3` genuine-sound
harnesses, rejected the unsound `10999` property and the vacuous `11276` harness, and agreed with the
iter125 gold-based decision where an anchor was applicable. Not supported: a benchmark, model, or
state-of-the-art claim, or a guarantee that one anchor pair rejects all unsound properties.

## Next gate

`iter127`: extend anchors with the `PASS_TO_PASS` cases so date-dependent and near-miss unsound
properties are covered, and add a structured-input generator seeded from the test's own example inputs
to close the `11206` synthesis failure.

## Evidence

- `proof/endpoint_results.json`, `proof/run_summary.json`
- `proof/valid/receipt_gold_free_soundness_gate.json`
- `scripts/run_gold_free_soundness_gate.py`
