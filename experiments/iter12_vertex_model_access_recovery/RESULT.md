# Iteration 12 - Vertex Model Access Recovery Result

Status: `PASS`

## Result

The Vertex model access recovery gate passed.

The original selected endpoint,
`gemini-3.1-pro-preview-customtools`, was kept. No replacement model was selected.

A minimal live probe from an ephemeral Google Compute Engine VM attached to the dedicated Telos
runner identity reached the Vertex `generateContent` path for the original custom-tools endpoint.
The response returned HTTP `200`, one candidate, and usage metadata. The probe used a four-token
output ceiling and did not run CodeClash, SWE-bench, a model sweep, or a leaderboard task.

This is an access result, not a provider capability or benchmark result.

## What Changed

- Created or retained the dedicated runner short ID `telos-vertex-runner`.
- Granted the dedicated runner `roles/aiplatform.user` for Vertex access.
- Granted the active operator attach permission for the dedicated runner so an ephemeral VM can use
  it.
- Removed the temporary token-impersonation permission used during debugging.
- Deleted the ephemeral probe VM after the access check.

Full service-account email, active account email, Google Cloud project identifier, tokens, and
credential JSON are not committed.

## What Passed

- Local ADC was present and required Google services were enabled before the cloud probe.
- The dedicated runner identity was verified through VM metadata credentials, not through local
  token impersonation.
- The original model endpoint remained
  `publishers/google/models/gemini-3.1-pro-preview-customtools:generateContent`.
- The region remained `global`.
- The probe made exactly one minimal model-access request and recorded only sanitized evidence.
- The ephemeral VM was deleted.

## What This Does Not Claim

- No provider-model capability is claimed.
- No CodeClash run was started.
- No CodeClash leaderboard result is claimed.
- No SWE-bench result is claimed.
- No production/live-domain behavior changed.
- No replacement model was selected.

## Evidence

- Probe summary: [`proof/probe.json`](proof/probe.json)
- Cloud state: [`proof/cloud_state.json`](proof/cloud_state.json)
- Sanitized probe transcript:
  [`proof/raw/vertex_access_probe_serial.log`](proof/raw/vertex_access_probe_serial.log)
- Receipt: [`proof/valid/receipt_vertex_model_access_recovery.json`](proof/valid/receipt_vertex_model_access_recovery.json)
- Review: [`proof/review.md`](proof/review.md)
- Learning record: [`proof/learning_record.json`](proof/learning_record.json)

## Next Gate

Run `iter13_provider_model_pilot_retry_after_access_recovery` as a new pre-registered provider
smoke. Use the original Vertex custom-tools model, the dedicated Telos runner identity, the frozen
CodeClash task, and the `$25` ceiling. Do not treat this access result as a benchmark result.
