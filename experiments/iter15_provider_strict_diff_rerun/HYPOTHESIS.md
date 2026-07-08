# Iteration 15 - Provider Strict Diff Rerun

Status: pre-registered, result pending.

## Purpose

Rerun the frozen provider-backed CodeClash smoke only after `iter14` converted the first diff
hygiene issue into an explicit quality bar.

The goal is not to chase a score. The goal is to prove the Telos evidence loop can run a paid
provider-agent attempt and refuse a clean pass when the submitted diff leaves unjustified helper or
scratch files.

## Frozen Run

- Provider: Google Vertex AI.
- Model endpoint: `gemini-3.1-pro-preview-customtools`.
- Vertex endpoint path:
  `publishers/google/models/gemini-3.1-pro-preview-customtools:generateContent`.
- Region: `global`.
- Runner: ephemeral GCE VM attached to the dedicated runner short ID `telos-vertex-runner`.
- CodeClash config:
  `experiments/iter09_provider_model_pilot_smoke/proof/overlay/configs/test/telos_battlesnake_vertex_gemini_pilot.yaml`.
- Agent under test: `p1`, provider-backed Mini-SWE-Agent.
- Control: `p2`, dummy.
- Task: one-round, one-simulation BattleSnake edit smoke.
- Maximum model invocations: `8`.
- Maximum output tokens per call: `4096`.
- Dollar ceiling: `$25`.
- Wall-clock ceiling: `45` minutes.

## New Quality Bar

The gate can publish a clean pass only if all hold:

- a zero-spend preflight confirms the dedicated runner can call the selected Vertex endpoint without
  committing sensitive Google identifiers,
- the CodeClash run exits successfully under the frozen model, task, runner, and budget,
- raw output is retained under `proof/raw/` with sensitive identifiers redacted before commit,
- the result records provider trajectory, cost, API-call stats, changed files, and full diff scope,
- a diff-quality review classifies the submitted diff as `clean`,
- unreferenced root helper or scratch files such as `patch.py`, `scratch.py`, `tmp.py`, caches, or
  generated residue prevent a clean pass unless the task explicitly requested them and the result
  justifies them,
- no leaderboard, SWE-bench, production, or live-domain claim is made.

## Falsifiers

Publish blocked/null evidence if:

- the dedicated runner cannot call the selected Vertex endpoint during preflight,
- CodeClash cannot run the provider-backed config without leaking credentials,
- the run exceeds the frozen `$25` ceiling or 45-minute wall-clock ceiling,
- provider cost or API-call counts are missing and cannot be bounded by local logs,
- raw artifacts cannot be sanitized without destroying audit evidence.

Publish a quality failure, not a clean pass, if:

- execution succeeds but the submitted diff leaves an unjustified helper, scratch, cache, generated,
  or secret-risk file,
- the changed-file set cannot be reconstructed from committed artifacts,
- the result tries to use the one-game score as model-capability evidence.

## Scope Boundary

This is still a smoke test of the Telos evidence loop with one paid provider-backed agent attempt.
It is not a leaderboard run, not a SWE-bench result, and not a production/live-domain verification.
