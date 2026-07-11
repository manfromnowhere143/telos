# Iteration 128 Result - Property Strategy by Function Type

Status: `PASS`.

## What this gate did

Closed the `10999` residual and, in doing so, established which gold-free property works for which
kind of function. It also records a mid-gate correction transparently.

## The correction (recorded, not hidden)

The first attempt was an anchor-in-the-loop generation: propose a property, check it against the
test's known-correct `(input_string, expected_timedelta)` pairs, retry on violation. It failed every
retry. Inspection showed the failure was a harness bug, not a model failure: the sound property for a
parser is an inverse round-trip whose input is a `timedelta`, but the check was being fed the test's
`(input_string, expected)` anchors, whose input convention does not match a `timedelta`-input harness.
Forcing string anchors onto a round-trip harness rejects valid properties. Reporting the anchor-loop
as a model failure would have been a false negative.

## The result

The inverse round-trip `parse_duration(duration_string(td)) == td` for random `timedelta` is sound on
gold: `0/30` violations. It is self-validating - it checks the parser against its own formatter and
needs no external anchor.

- genuine-sound rate: `5/7` (iter127) -> `6/7` = `0.85714286`
- `10999` closed via inverse round-trip
- honest residual: `11276` only - a mis-targetable task (FAIL_TO_PASS test in `admin_docs`, fix in
  `html.py`), which needs targeting from the test's assertions rather than the fix diff

## The finding - a property-strategy taxonomy by function type

Gold-free property strategy is not one-size-fits-all; it is chosen by the function's structure:

- pure transform (reversal, year formatting): a contract property relating `out` to `inp`.
- invertible parser or formatter (parse_duration, parse_http_date): an inverse round-trip
  `f(f_inverse(x)) == x`, self-validating and needing no external anchor.
- the visible-test anchor is a soundness filter, valid only when it matches the harness input
  convention - the lesson from the corrected attempt.

This is why full-auto generation from a diff struggled: it must also pick the right strategy. Naming
the strategy by function type is the lever that closed six of seven instances.

## Claim boundary

Supported: the inverse round-trip is a sound gold-free property for `parse_duration` (`0/30`
violations), closing `10999` and raising the genuine-sound rate to `6/7`; gold-free property strategy
is function-type-dependent, and an anchor must match the harness input convention. Not supported: a
benchmark, model, or state-of-the-art claim, or a rate beyond these seven instances.

## Next gate

`iter129`: resolve `11276` by targeting from the test's assertions rather than the fix diff, and make
strategy selection (transform property vs inverse round-trip) automatic from the function signature.

## Evidence

- `proof/roundtrip_10999.json` (observed native-execution round-trip soundness)
- `proof/endpoint_results.json`, `proof/run_summary.json`, `proof/learning_record.json`
- `proof/valid/receipt_property_strategy_taxonomy.json`
- `scripts/run_property_strategy_taxonomy.py`
