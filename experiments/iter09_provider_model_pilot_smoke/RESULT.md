# Iteration 09 - Provider Model Pilot Smoke Result

Status: `BLOCKED`

## Result

The paid provider-model smoke did not run.

The required zero-spend preflight failed before any model call because Google Application Default
Credentials could not refresh in non-interactive execution.

Blocked preflight:

```text
experiments/iter09_provider_model_pilot_smoke/proof/preflight/adc_check.log
```

## What Was Checked

- `gcloud` is installed.
- A Google Cloud project is configured, but its identifier is not committed.
- The selected model remains `gemini-3.1-pro-preview-customtools`.
- The selected budget remains `$25`.
- ADC token refresh was attempted with token output suppressed.
- ADC refresh failed with a non-interactive reauthentication error.

## What Did Not Happen

- No paid model call was made.
- No provider-model capability is claimed.
- No CodeClash run was started.
- No CodeClash leaderboard result is claimed.
- No SWE-bench result is claimed.
- No production/live-domain change occurred.
- No token, API key, credential JSON, account email, or Google Cloud project identifier is committed.

## Evidence

- Blocked preflight: [`proof/preflight.json`](proof/preflight.json)
- Raw preflight log: [`proof/preflight/adc_check.log`](proof/preflight/adc_check.log)
- Receipt: [`proof/valid/receipt_provider_model_pilot_smoke_blocked.json`](proof/valid/receipt_provider_model_pilot_smoke_blocked.json)
- Review: [`proof/review.md`](proof/review.md)
- Overlay prepared for the blocked run: [`proof/overlay`](proof/overlay)
- Learning record: [`proof/learning_record.json`](proof/learning_record.json)

## Next Gate

Restore a secret-safe provider credential path before retrying the paid smoke. The cleanest options
are non-interactive ADC refresh for local execution or a GitHub Actions Workload Identity / secret
path that can be verified without exposing values.
