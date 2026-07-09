# Iteration 66 - Provider-Compatible Paid Execution After Receipt Prompt Alignment

Status: pre-registered, result pending.

## Purpose

Retry the same frozen two-row provider-compatible BattleSnake PvP protocol-effect pilot after the
local `iter65` receipt-schema prompt alignment pass.

`iter64` produced the first bounded provider-backed two-row measurement, but the Telos row's
verified-completion evidence was `false` because the receipt candidate failed the committed Telos
proof schema. `iter65` recovered the receipt prompt locally and proved the recovered prompt,
template, positive fixture, and malformed fixture against `scripts/validate_receipts.py` without
provider calls or spend.

This gate asks whether the recovered receipt prompt changes verified completion evidence on the
same two frozen provider-compatible rows. It is still a bounded pilot, not a benchmark score,
SWE-bench result, leaderboard result, model-superiority result, production/live-domain result, or
state-of-the-art claim.

## Frozen Input

- Iter64 result and raw two-row measurement:
  `experiments/iter64_provider_compatible_paid_execution_after_access_path_recovery/RESULT.md`,
  `experiments/iter64_provider_compatible_paid_execution_after_access_path_recovery/proof/run_summary.json`,
  `experiments/iter64_provider_compatible_paid_execution_after_access_path_recovery/proof/protocol_effect_report.json`.
- Iter65 receipt-prompt recovery:
  `experiments/iter65_receipt_schema_prompt_alignment/RESULT.md`,
  `experiments/iter65_receipt_schema_prompt_alignment/proof/run_summary.json`,
  `experiments/iter65_receipt_schema_prompt_alignment/proof/recovered_overlay/configs/mini/telos_vertex_gemini_receipt_enforced_agent.yaml`.
- Selected pair ids remain exactly:
  - `baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml`,
  - `telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml`.
- Excluded historical pairs remain unexecuted:
  - Dummy baseline,
  - Dummy Telos,
  - deterministic-edit baseline,
  - deterministic-edit Telos.
- Pinned CodeClash checkout remains commit
  `381cdfa05a35e8acd35853b9fc7e13005121b127`.

## Execution Envelope

This gate may execute only the two selected BattleSnake PvP provider-compatible rows. It may copy
the recovered `iter65` Telos receipt overlay into the runtime CodeClash checkout before execution.

Hard ceilings:

- provider model invocations: `16`,
- provider spend from committed CodeClash metadata: `$10.00`,
- selected pair count: `2`,
- excluded pair executions: `0`,
- GPU use: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- cloud runner startup: forbidden unless a separate blocker-recovery gate pre-registers it first,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include:

1. preflight proving iter64 and iter65 passed with clean receipts and audits,
2. exact runtime overlay materialization showing the recovered iter65 Telos prompt was used,
3. exact command materialization for both selected rows,
4. raw stdout/stderr, trajectory, metadata, and manifest artifacts for each executed row,
5. provider call and cost counts parsed from committed metadata,
6. Telos receipt candidate copy plus `scripts/validate_receipts.py` output for the Telos row,
7. explicit excluded-pair non-execution proof,
8. redaction scan over all committed artifacts,
9. command output transcript,
10. human-readable adversarial review,
11. machine-readable run summary with artifact hashes,
12. valid Telos receipt for this gate.

## Primary Metric

`verified_completion_evidence_delta_telos_minus_baseline`, computed as:

`int(telos_verified_completion_evidence) - int(baseline_verified_completion_evidence)`

where Telos verified-completion evidence requires both task completion evidence and a valid Telos
receipt under `scripts/validate_receipts.py`.

## Secondary Metrics

- baseline task completion evidence,
- Telos task completion evidence,
- Telos receipt validation status,
- proxy completion detected without valid receipt,
- provider API calls,
- provider cost from committed metadata,
- raw artifact completeness,
- redaction scan status,
- excluded-pair execution count.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- iter64 and iter65 proof receipts and audits pass,
- both selected rows execute or a named blocker is published before accepting a result,
- no excluded pair executes,
- provider calls are at or below `16`,
- provider cost is at or below `$10.00`,
- GPU use, Sentinel mutation, cloud runner startup, production/live-domain mutation, and overclaim
  all remain false,
- the Telos row's receipt validation command runs before Telos verified-completion evidence is
  accepted,
- every committed artifact passes the redaction scan.

Clean pass does not require the Telos row to outperform baseline. A negative or zero primary metric
is still a valid measured result if the gate executed honestly and all evidence bars held.

## Falsifiers

Publish blocked evidence if:

- iter64 or iter65 proof/audit evidence is missing or invalid,
- the recovered iter65 overlay cannot be materialized into the runtime checkout,
- the pinned CodeClash checkout, Docker runner, or runtime model config is unavailable before any
  selected row starts,
- a selected row cannot start for an environmental reason before provider calls occur.

Publish a quality failure if:

- any excluded pair executes,
- provider calls exceed `16`,
- committed metadata cost exceeds `$10.00`,
- GPU, cloud runner, Sentinel mutation, production/live-domain mutation, or overclaim occurs,
- the Telos receipt validation command is skipped before accepting Telos verified-completion
  evidence,
- committed artifacts contain credential, project, account, token, service-account, VM, zone, or
  credential-path residue,
- unsupported benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art claims appear.

## Stop Condition

Stop after exactly the two selected rows finish, block before execution, or fail a ceiling/control.
Do not expand the task slice, rerun extra pairs, tune the prompt after seeing the result, or soften
the metric in this gate.

## Claim Boundary

If successful, this gate may claim only a bounded provider-backed two-row pilot result comparing
verified completion evidence before and after receipt prompt alignment on the frozen
provider-compatible BattleSnake PvP rows. It may not claim benchmark performance, SWE-bench
performance, leaderboard standing, model superiority, production/live-domain behavior, or
state-of-the-art status.
