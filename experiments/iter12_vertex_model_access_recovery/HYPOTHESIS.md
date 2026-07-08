# Iteration 12 - Vertex Model Access Recovery

Status: pre-registered, result pending.

## Purpose

Recover a usable provider-model access path after `iter11` proved that the selected
`gemini-3.1-pro-preview-customtools` path reaches Vertex but is blocked by
`aiplatform.endpoints.predict` permission or endpoint availability.

This gate does not authorize a CodeClash run.

## Bars

The gate passes only if all hold:

- the runner identity is identified without committing account email, project identifier, token, or
  credential JSON,
- Vertex access is verified with a zero- or minimal-spend preflight that does not broaden into a
  benchmark run,
- the selected next model endpoint is either the original
  `gemini-3.1-pro-preview-customtools` path with verified predict access, or a newly
  pre-registered reachable replacement,
- the result records the exact auth surface, endpoint, region, and spend ceiling for the next
  provider smoke,
- no leaderboard, SWE-bench, production, or live-domain claim is made.

## Falsifiers

Publish blocked/null evidence if:

- checking access requires printing or committing credential material,
- the selected model remains unavailable to the runner identity,
- a replacement model would change the scientific question without a new slice decision,
- model access cannot be verified without uncontrolled spend,
- Google Cloud project/account identifiers would appear in committed logs.

## Scope Boundary

This is an access-recovery gate. It may run minimal provider-access probes only if the result can
record spend and sanitize logs. It must not run CodeClash, SWE-bench, a model sweep, or a
leaderboard submission.
