# Iteration 17 - Provider Lint Hygiene Control

Status: pre-registered, result pending.

## Purpose

Test whether the clean workspace-hygiene result from `iter16` can be preserved while also removing
the concrete style caveat observed in the submitted `main.py` diff.

This is not a scale-up and not a leaderboard attempt. It is a narrow quality-control run: can the
provider-backed agent complete the same CodeClash smoke while leaving no helper residue and no
trailing-whitespace diff hygiene issue?

## Frozen Run

- Provider: Google Vertex AI.
- Model endpoint: `gemini-3.1-pro-preview-customtools`.
- Region: `global`.
- Runner: ephemeral GCE VM attached to the dedicated runner short ID `telos-vertex-runner`.
- Base CodeClash config:
  `experiments/iter09_provider_model_pilot_smoke/proof/overlay/configs/test/telos_battlesnake_vertex_gemini_pilot.yaml`.
- Agent under test: `p1`, provider-backed Mini-SWE-Agent.
- Control: `p2`, dummy.
- Task: one-round, one-simulation BattleSnake edit smoke.
- Maximum model invocations: `8`.
- Maximum output tokens per call: `4096`.
- Dollar ceiling: `$25`.
- Wall-clock ceiling: `45` minutes.

## Intervention

Keep the `iter16` workspace-hygiene instruction and add only a source-style hygiene instruction:

- before submitting, run `git diff --check` or an equivalent trailing-whitespace check against the
  submitted workspace,
- if that check reports whitespace errors, fix only those whitespace errors before submitting,
- final submitted diff may include task-relevant source changes and `README_agent.md`,
- final submitted diff must not include unreferenced helper, scratch, cache, generated, or
  secret-risk files.

No result may compare this intervention to a model capability baseline unless the evidence supports
that exact claim.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- preflight confirms the dedicated runner can call the selected Vertex endpoint without committing
  sensitive Google identifiers,
- CodeClash exits successfully under the frozen model, task, runner, and budget,
- raw output is retained under `proof/raw/` with sensitive identifiers and provider-private fields
  redacted before commit,
- provider trajectory, cost, API-call stats, changed files, and full diff scope are recorded,
- strict workspace-hygiene status is `clean`,
- submitted diff has no helper, scratch, cache, generated, or secret-risk residue,
- submitted diff has no trailing-whitespace or `git diff --check` style failure,
- no leaderboard, SWE-bench, production, or live-domain claim is made.

## Falsifiers

Publish blocked/null evidence if:

- the dedicated runner cannot call the selected Vertex endpoint during preflight,
- CodeClash cannot run the provider-backed config without leaking credentials,
- the run exceeds the frozen `$25` ceiling or 45-minute wall-clock ceiling,
- provider cost or API-call counts are missing and cannot be bounded by local logs,
- raw artifacts cannot be sanitized without destroying audit evidence.

Publish a quality failure, not a clean pass, if:

- execution succeeds but any unrequested helper, scratch, cache, generated, or secret-risk file
  remains in the submitted diff,
- execution succeeds but the submitted diff contains trailing whitespace or another
  `git diff --check` failure,
- the changed-file set cannot be reconstructed from committed artifacts,
- the result tries to use the one-game score as model-capability evidence.

## Scope Boundary

This remains a smoke test of the Telos evidence loop with one paid provider-backed agent attempt.
It is not a leaderboard run, not a SWE-bench result, and not a production/live-domain verification.
