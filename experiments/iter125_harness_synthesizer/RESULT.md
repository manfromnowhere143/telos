# Iteration 125 Result - Validated Harness Synthesizer

Status: `PASS`.

## What this gate did

Rebuilt the harness generator to target the iter124 failure modes - mis-targeting, generation
truncation, and unsynthesizable input domains - with three changes: prompt with the FAIL_TO_PASS test
source (not the fix diff) so the model targets what the test calls; validate the input generator by
running the proposed call on twenty candidate inputs and requiring at least ten to succeed before
trusting the property; and retry up to three times with the concrete error fed back. Re-measured on
the same seven instances, then applied a non-triviality filter.

## Result

| metric | value |
| --- | --- |
| iter124 baseline (full-auto, no validation) | `2/7` = `0.28571429` |
| synthesizer genuine-sound rate | `4/7` = `0.57142857` |
| genuine-sound instances | `14089`, `14373`, `13670`, `11848` |
| vacuous harness caught by the non-triviality filter | `11276` |
| residual: unsound property | `10999` |
| residual: input-domain synthesis failure | `11206` |

## The findings

1. Validation and retry roughly double the clean-sound rate. Test-source targeting recovered
   `11848` (previously a generation failure) and `13670` (previously an unsynthesizable input domain),
   and fixed the `11276` mis-target so the model called the right surface. The synthesizer produces
   genuine metamorphic harnesses for four of seven real instances - e.g. `13670` proposed
   `out == str(inp[0])[-2:].zfill(2)` for the two-digit-year format, and `11848` proposed a
   round-trip check that `parse_http_date` recovers the source datetime.

2. A raw soundness classification is not enough - it accepts vacuous harnesses. The synthesizer
   produced a harness for `11276` that passes validation and shows zero violations, but its call is
   `html.format_html("{}{}", 'a', 'b')` with a constant `check: out == 'ab'` - it ignores the random
   input entirely and tests nothing. A non-triviality filter (the call must use `inp`; the check must
   reference both `inp` and `out`) catches it automatically. Without that filter the rate would be
   overstated as `5/7`.

3. Two residual failures remain honest and instructive: `10999` produced an unsound property (one
   violation on gold, so its `parse_duration` contract check was slightly wrong), and `11206`
   (`numberformat` with an argument dict) still could not synthesize valid inputs after three retries.

## Implication

A validated, retrying synthesizer with a non-triviality gate makes the automated third layer work on
a majority of these simple-contract instances, not a minority - a genuine improvement over iter124 -
while honestly bounding it: unsound-property detection still needs a reference or more anchors, and
structured-input domains still defeat automatic input synthesis.

## Claim boundary

Supported: a validated synthesizer with test-source targeting, input validation, retry, and a
non-triviality filter reached a genuine-sound rate of `4/7`, versus `2/7` without it, catching one
vacuous harness that raw soundness classification accepted. Not supported: a benchmark, model, or
state-of-the-art claim, or a rate beyond these seven instances.

## Next gate

`iter126`: add an unsound-property check without gold (property must hold on the visible-test anchor
and the `PASS_TO_PASS` cases) and a structured-input generator for parser/formatter functions, then
re-measure toward closing `10999` and `11206`.

## Evidence

- `proof/synthesizer_results.json` (synthesized harnesses and native-execution classification)
- `proof/endpoint_results.json`, `proof/run_summary.json`
- `proof/valid/receipt_harness_synthesizer.json`
- `scripts/run_harness_synthesizer.py`
