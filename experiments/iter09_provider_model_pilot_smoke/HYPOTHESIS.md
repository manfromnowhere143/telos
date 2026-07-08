# Iteration 09 - Provider Model Pilot Smoke

Status: pre-registered, result pending.

## Purpose

Run the selected `iter08` provider-model pilot once, under a hard spend ceiling, to capture the
first provider-backed CodeClash Mini-SWE-Agent evidence bundle.

This is a paid smoke test, not a model benchmark.

## Frozen Pilot

- Provider: Google Vertex AI.
- Model endpoint: `gemini-3.1-pro-preview-customtools`.
- CodeClash commit: `381cdfa05a35e8acd35853b9fc7e13005121b127`.
- Game: BattleSnake.
- Tournament rounds: `1`.
- Simulations per round: `1`.
- Agent under test: `p1`, provider-backed Mini-SWE-Agent.
- Control: `p2`, dummy.
- Maximum model invocations: `8`.
- Maximum output tokens per call: `4096`.
- Maximum wall-clock time: `45` minutes.
- Dollar ceiling: `$25`.

## Required Zero-Spend Preflight

Before any model call:

- confirm `gcloud` has an active account and configured project without logging identifiers,
- confirm `aiplatform.googleapis.com` and `generativelanguage.googleapis.com` are enabled,
- confirm the model endpoint can be resolved without printing tokens or credential JSON,
- confirm the CodeClash provider config can be generated with the frozen model id,
- confirm logs redact environment variables and credentials.

## Bars

The gate passes only if all hold:

- the zero-spend preflight passes,
- the CodeClash run exits successfully,
- `p1` is provider-backed and records a trajectory,
- `p1` agent stats record model invocations greater than zero and no more than `8`,
- provider cost is numeric, greater than zero, and no more than `$25`,
- player change records exist for diff-scope evidence,
- raw artifacts are preserved,
- a Telos receipt validates,
- an adversarial review rejects leaderboard, SWE-bench, production, and live-domain claims.

## Falsifiers

Publish blocked/null evidence if:

- credentials or service readiness cannot be verified without exposing secrets,
- the selected model endpoint is unavailable,
- provider cost is missing or exceeds the frozen ceiling,
- model invocations exceed the frozen ceiling,
- trajectory, metadata, agent stats, or change records are missing,
- the result cannot be separated from a benchmark or production claim.

## Scope Boundary

This gate authorizes only the single frozen paid smoke. It does not authorize broad model sweeps,
leaderboard submissions, SWE-bench claims, production changes, GPU jobs, or live-domain changes.
