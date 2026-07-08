# Next Phase

## Current Action

Run `iter00_target_survey` exactly as frozen in
[`../experiments/iter00_target_survey/HYPOTHESIS.md`](../experiments/iter00_target_survey/HYPOTHESIS.md).

The output is not a model score. It is a target decision:

- choose a benchmark,
- publish a survey null,
- or freeze a hybrid Telos overlay.

## After A Positive Survey

If one target clears the bar:

1. Write `experiments/iter01_<target>/HYPOTHESIS.md`.
2. Freeze the primary metric and baseline number.
3. Implement the smallest faithful harness.
4. Run a dry receipt on one task.
5. Stop if the receipt cannot be independently validated.

## After A Survey Null

If no target clears the bar:

1. Publish the null in `RESULT.md`.
2. Name the failed criteria per candidate.
3. Do not start `iter01`.
4. Either revise the candidate list with new public sources or close the repo as a clean negative
   target-selection result.
