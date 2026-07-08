# Iteration 13 - Provider Model Pilot Retry After Access Recovery

Status: pre-registered, result pending.

## Purpose

Retry the provider-model CodeClash pilot only after `iter12` verified that the original Vertex
custom-tools endpoint is reachable from an ephemeral GCE runner using the dedicated Telos runner
identity.

This gate must produce either a completed provider-agent smoke result or a blocked/null result with
raw evidence. It must not rewrite `iter11` or `iter12`.

## Frozen Run

- Provider: Google Vertex AI.
- Model endpoint: `gemini-3.1-pro-preview-customtools`.
- Vertex endpoint path:
  `publishers/google/models/gemini-3.1-pro-preview-customtools:generateContent`.
- Region: `global`.
- Runner: ephemeral GCE VM attached to the dedicated runner short ID `telos-vertex-runner`.
- CodeClash config: `configs/test/telos_battlesnake_vertex_gemini_pilot.yaml`.
- Agent under test: `p1`, provider-backed Mini-SWE-Agent.
- Control: `p2`, dummy.
- Task: one-round, one-simulation BattleSnake edit smoke.
- Maximum model invocations: `8`.
- Maximum output tokens per call: `4096`.
- Dollar ceiling: `$25`.
- Wall-clock ceiling: `45` minutes.

## Bars

The gate passes only if all hold:

- preflight confirms the dedicated runner identity can call the selected Vertex endpoint without
  committing account email, project identifier, token, or credential JSON,
- the CodeClash run exits successfully under the frozen model, task, runner, and budget,
- raw CodeClash output is retained under `proof/raw/` with sensitive identifiers redacted before
  commit,
- the proof bundle records whether `p1` submitted, which files changed, the diff summary, the
  provider trajectory path, reported model cost if available, and API-call stats if available,
- no token, API key, credential JSON, account email, or Google Cloud project identifier is
  committed,
- no leaderboard, SWE-bench, production, or live-domain claim is made.

## Falsifiers

Publish blocked/null evidence if:

- the dedicated runner cannot call the selected Vertex endpoint during preflight,
- CodeClash cannot run the provider-backed config without leaking credentials,
- the run exceeds the frozen `$25` ceiling or 45-minute wall-clock ceiling,
- `p1` trajectory or agent stats are missing after an otherwise completed provider attempt,
- provider cost is missing and cannot be bounded by local run logs,
- raw artifacts cannot be sanitized without destroying the evidence needed for audit,
- the result would require changing model, provider, budget, task, or runner shape inside this gate.

## Scope Boundary

This is a smoke test of the Telos evidence loop with one paid provider-backed agent attempt. It is
not a leaderboard run, not a SWE-bench result, and not a production/live-domain verification.
