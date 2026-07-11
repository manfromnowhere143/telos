# Iteration 125 - Validated Harness Synthesizer

Status: pre-registered before execution. Frozen before the re-measured clean-sound rate was known.

## Why this gate exists

Iter124 measured full-auto harness generation at `2/7` clean-sound, with four failure modes:
generation truncation, syntax errors, unsynthesizable input domains, and call-target mis-inference.
This gate builds a synthesizer that targets those modes directly and re-measures on the same seven
instances, to see whether validation-and-retry moves the rate.

## Design (the three changes from iter124)

1. Target the right function: prompt the model with the FAIL_TO_PASS test source (what the test
   actually calls and asserts), not the fix diff, so it does not mis-infer the call target.
2. Validate the input generator before trusting the property: generate twenty candidate inputs, run
   the proposed `call` on each, and require at least ten to execute without raising. A harness that
   cannot produce valid inputs is rejected before its property is used.
3. Retry on failure: on a JSON, compile, or input-validity failure, retry up to three times with the
   concrete error fed back to the model.

A harness that passes validation is then executed against the gold implementation and classified sound
(`>= 10` valid inputs, `0` violations) or unsound (`> 0` violations).

## Endpoints

- `clean_sound_rate` on the seven instances, versus the iter124 baseline of `2/7`.
- the failure taxonomy after synthesis (which modes remain).

## Acceptance / interpretation rule

Descriptive. If the synthesizer raises the clean-sound rate above `2/7`, validation-and-retry helps and
by how much is recorded. If it does not, the residual failures are the finding and identify what a
diff-to-JSON-plus-retry approach still cannot do.

## Falsifiers

1. A sound classification is still not a correctness guarantee; any harness that validates but tests a
   function unrelated to the task is flagged.
2. If the rate does not improve, record it plainly rather than tuning the prompt until it does.

## Execution envelope

- native execution + up to three generation calls per instance (< `$0.05` total),
- production/live-domain mutation: forbidden, benchmark/model/SOTA claim: forbidden.

## Claim boundary (pre-committed)

At most: "a validated synthesizer with test-source targeting, input validation, and retry produced a
clean-sound rate of `N/7`, versus `2/7` without it." Not a benchmark, model, or SOTA claim.
