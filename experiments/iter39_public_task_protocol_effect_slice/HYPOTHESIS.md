# Iteration 39 - Public Task Protocol-Effect Slice

Status: pre-registered, result pending.

## Purpose

`iter38` proved malformed self-coverage public prose is rejected. This gate moves the research line
toward the missing empirical layer: a frozen public task slice that can compare baseline agent
completion evidence against Telos receipt-enforced completion evidence.

## Frozen Input

- Candidate public tasks: CodeClash task configs and SWE-bench Verified-style task metadata already
  referenced by the Telos target survey.
- Existing proof records under `experiments/`.
- Public state files: `README.md`, `CONTINUITY.md`, `docs/REPORT.md`, `docs/NEXT_PHASE.md`,
  `docs/MISSION_LOOP.md`, and `mission/loop.json`.
- Provider/model: no provider call allowed for this slice-selection gate.
- Compute: local CPU only.

## Verification Plan

Select and freeze a small external-task protocol-effect slice for the next execution gate. The slice
must define:

- task family and exact task identifiers,
- baseline condition without Telos receipt enforcement,
- Telos-instrumented condition with receipt enforcement,
- primary metric: real-completion rate under verifier evidence,
- secondary metrics: proxy-pass/receipt-fail rate, unsupported-claim rate, over-edit rate,
  audit cost, false-positive rate, and false-negative rate,
- minimum sample size or a reasoned null if available local/public infrastructure cannot support
  the sample,
- exact cost ceiling and provider authorization boundary for any later execution gate,
- negative controls and audit packet requirements.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- no provider, API, GPU, or cloud spend occurs in this slice-selection gate,
- the selected public task slice is frozen with exact identifiers,
- baseline and Telos-instrumented conditions are both specified,
- the primary and secondary metrics are specified before execution,
- unsupported claims, hidden nulls, and benchmark/leaderboard overclaims are explicitly forbidden,
- command output and proof artifacts are committed,
- no leaderboard, SWE-bench, production, live-domain, or model-superiority result is claimed.

## Falsifiers

Publish blocked/null evidence if:

- no suitable public task slice can be frozen from committed or locally discoverable task metadata,
- the task identifiers cannot be recorded without relying on hidden state,
- the next execution gate would require unbounded provider spend or undefined infrastructure.

Publish a quality failure, not a clean pass, if:

- the slice omits a baseline or Telos-instrumented condition,
- metrics are chosen after seeing execution results,
- failed/null outcomes are excluded from the planned reporting surface,
- the result widens the claim beyond a frozen protocol-effect slice.

## Scope Boundary

This is a slice-selection and pre-registration gate for a future external-task protocol-effect
execution. It is not a provider rerun, not a benchmark result, and not a production/live-domain
verification.
