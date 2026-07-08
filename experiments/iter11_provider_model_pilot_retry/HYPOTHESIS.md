# Iteration 11 - Provider Model Pilot Retry

Status: pre-registered, result pending.

## Purpose

Retry the already selected Vertex Gemini CodeClash provider-model pilot after `iter10` restored a
secret-safe ADC path.

This gate exists because `iter09` remains a valid blocked result. The retry must be a new result,
not a rewrite of the blocked record.

## Frozen Run

- Provider: Google Vertex AI.
- Model endpoint: `gemini-3.1-pro-preview-customtools`.
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

- zero-spend preflight confirms ADC refresh with token output suppressed,
- the CodeClash run exits successfully under the frozen model, task, and budget,
- raw CodeClash output is retained under `proof/raw/`,
- the proof bundle records whether `p1` submitted, which files changed, the diff summary, and
  reported model cost if available,
- no token, API key, credential JSON, account email, or Google Cloud project identifier is
  committed,
- no leaderboard, SWE-bench, production, or live-domain claim is made.

## Falsifiers

Publish blocked/null evidence if:

- ADC refresh fails again,
- the model endpoint is unavailable to the configured project,
- LiteLLM or CodeClash cannot construct or execute the provider-backed agent,
- model cost is missing and cannot be bounded by the local run logs,
- any credential material would need to be printed or committed,
- the run would exceed the frozen `$25` ceiling or 45-minute wall-clock ceiling.

## Scope Boundary

This is a smoke test of the Telos evidence loop with one paid provider-backed agent attempt. It is
not a leaderboard run, not a SWE-bench result, and not a production/live-domain verification.
