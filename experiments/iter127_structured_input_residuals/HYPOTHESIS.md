# Iteration 127 - Structured Inputs Close the Residuals

Status: pre-registered before execution. Frozen before the residual harnesses were run.

## Why this gate exists

Iter125-iter126 left two residuals: `11206` (numberformat), whose input is a structured argument set
the model could not synthesize, and `11848` (parse_http_date), whose visible test uses a mocked
`utcnow` for two-digit-year rollover so its anchor was not gold-free applicable. This gate tests one
technique against both: seed the input generator from the test's own example input shape, and use a
non-pathological input format that avoids the case needing a mock.

## Method

- `11206`: from the test example `('0.0001234', 3, '0.000')`, the input is `(number, decimal_pos)`;
  the harness generates random `(number_string, decimal_pos)` pairs and checks the output has exactly
  `decimal_pos` fractional digits - a contract property, no gold.
- `11848`: `parse_http_date` also accepts RFC1123 with a four-digit year (no rollover, no mock); the
  harness generates random four-digit-year datetimes, formats them RFC1123, and checks
  `parse_http_date` round-trips them.

Each harness is executed against the gold implementation on twenty-five seeded random inputs.

## Endpoints

- soundness of each residual harness (`>= 10` valid inputs, `0` violations on gold).
- the resulting genuine-sound rate over the seven instances, versus `4/7` after iter125.

## Acceptance / interpretation rule

If both harnesses are sound, the structured-input technique closes the two residuals and the
genuine-sound rate rises to `5/7`. The remaining two instances (`10999` unsound generated property,
`11276` mis-targetable task) are recorded as the honest residual, since they are not input-domain
failures.

## Falsifiers

1. If a residual harness is not sound, the technique did not close it; record the miss.
2. A sound harness that ignores the input is vacuous; the non-triviality condition still applies.

## Execution envelope

- native execution only, no provider calls, no GPU, no cloud,
- production/live-domain mutation: forbidden, benchmark/model/SOTA claim: forbidden.

## Claim boundary (pre-committed)

At most: "structured input generators seeded from the test example and a non-pathological format made
the `11206` and `11848` harnesses sound, raising the genuine-sound rate to `5/7`." Not a benchmark,
model, or SOTA claim.
