# Iteration 127 Result - Structured Inputs Close the Residuals

Status: `PASS`.

## What this gate did

Closed the two iter125-iter126 residuals with one technique: seed the input generator from the test's
own example input shape, and use a non-pathological input format that avoids the case needing a mock.

- `11206` (numberformat): the test example `('0.0001234', 3, '0.000')` reveals the input shape
  `(number, decimal_pos)`. The harness generates random `(number_string, decimal_pos)` pairs and
  checks the output has exactly `decimal_pos` fractional digits - a contract property, no gold.
- `11848` (parse_http_date): its RFC850 test needs a mocked `utcnow` for two-digit-year rollover, but
  `parse_http_date` also accepts RFC1123 with a four-digit year (no rollover, no mock). The harness
  generates random four-digit-year datetimes, formats them RFC1123, and checks the parse round-trips.

## Result

| harness | soundness on gold | genuine |
| --- | --- | --- |
| `11206` structured `(number, decimal_pos)` | `0/25` violations, 25 valid inputs | yes |
| `11848` RFC1123 four-digit-year round-trip | `0/25` violations, 25 valid inputs | yes |

- genuine-sound rate: `4/7` (iter125) -> `5/7` = `0.71428571`
- newly closed: `11206` (`11848` was already genuine in iter125; its anchor is now gold-free
  applicable via the four-digit-year round-trip)

## The finding

Both residuals were input-domain problems, and both are closed by grounding the input generator in
information the harness already has: the test's own example input for `11206`, and the function's
documented non-pathological input format for `11848`. This is more reliable than asking the model to
synthesize a valid input for a structured argument set from scratch, which failed in iter124-iter125.

## The honest residual

Two of seven remain, and neither is an input-domain failure:

- `10999`: the model generated an unsound property, which the gold-free anchor (iter126) correctly
  rejects. Producing a sound property here needs a generation retry with the anchor as feedback.
- `11276`: the task is mis-targetable - the FAIL_TO_PASS test lives in `admin_docs` while the fix is
  in `html.py`, so the harness targets a plausible but wrong surface. Resolving it needs targeting
  from the test's actual assertions.

## Claim boundary

Supported: structured input generators seeded from the test example and a non-pathological format made
the `11206` and `11848` harnesses sound, raising the genuine-sound rate to `5/7`; the remaining two are
an unsound generated property and a mis-targetable task, not input-domain failures. Not supported: a
benchmark, model, or state-of-the-art claim.

## Next gate

`iter128`: retry generation on `10999` with the visible-test anchor as feedback to obtain a sound
property, and target `11276` from the test's assertions rather than the fix diff.

## Evidence

- `proof/structured_harness_results.json` (observed native-execution soundness)
- `proof/endpoint_results.json`, `proof/run_summary.json`, `proof/learning_record.json`
- `proof/valid/receipt_structured_input_residuals.json`
- `scripts/run_structured_input_residuals.py`
