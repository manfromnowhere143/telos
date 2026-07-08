# Iteration 10 - Provider Auth Recovery

Status: pre-registered, result pending.

## Purpose

Restore a secret-safe provider authentication path for the selected Vertex Gemini pilot without
making a paid model call.

## Bars

The gate passes only if all hold:

- non-interactive ADC refresh succeeds locally with token output suppressed, or
- a GitHub Actions Workload Identity / secret path is configured and verified without exposing
  secret values,
- no token, API key, credential JSON, account email, or Google Cloud project identifier is committed,
- Vertex and Generative Language service readiness remains verified,
- the result publishes the exact auth surface to use for retrying `iter09` without broadening model
  scope.

## Falsifiers

Publish blocked/null evidence if:

- credentials require an interactive prompt,
- verifying readiness would require printing or committing credential material,
- the available auth path is tied to a production secret that should not be used for research,
- the retry path would bypass the frozen `iter09` budget or evidence bars.

## Scope Boundary

This gate does not authorize a model call. It only restores the credential path needed before
retrying the already frozen paid smoke.
