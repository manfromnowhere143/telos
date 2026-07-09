# Iteration 65 - Receipt Schema Prompt Alignment

Status: pre-registered, result pending.

## Purpose

Diagnose the `iter64` Telos-row receipt failure and recover a schema-aligned receipt prompt before
any additional paid provider-compatible BattleSnake retry.

`iter64` produced the first bounded two-row provider-backed protocol-effect measurement:

- baseline verified-completion evidence: `true`,
- Telos verified-completion evidence: `false`,
- Telos-minus-baseline verified-completion delta: `-1`,
- provider calls: `10`,
- provider cost from CodeClash metadata: `$0.070448`,
- excluded pairs executed: `false`.

The Telos row submitted a JSON receipt-like object, but it did not match the Telos proof receipt
schema. The next honest action is not to widen the task slice. The next action is to make the
receipt contract visible enough that the Telos condition can attempt a valid receipt under the
same validator.

This is not a benchmark result, SWE-bench score, leaderboard result, production/live-domain result,
model-superiority result, or state-of-the-art claim.

## Frozen Input

- Iter64 result:
  `experiments/iter64_provider_compatible_paid_execution_after_access_path_recovery/RESULT.md`.
- Iter64 report:
  `experiments/iter64_provider_compatible_paid_execution_after_access_path_recovery/proof/protocol_effect_report.json`.
- Iter64 invalid receipt candidate:
  `experiments/iter64_provider_compatible_paid_execution_after_access_path_recovery/proof/raw/telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml/telos_completion_receipt_candidate.json`.
- Iter64 invalid receipt artifact:
  `experiments/iter64_provider_compatible_paid_execution_after_access_path_recovery/proof/raw/telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml/invalid/telos_completion_receipt.json`.
- Current receipt schema and validator:
  `protocol/proof.schema.json`,
  `telos/proof.py`,
  `scripts/validate_receipts.py`.
- Prior Telos receipt-enforced agent overlay:
  `experiments/iter52_provider_condition_runtime_separation_recovery/proof/recovered_overlay/configs/mini/telos_vertex_gemini_receipt_enforced_agent.yaml`.

## Execution Envelope

This gate may run only local CPU validation and file inspection. It must not run either BattleSnake
row, any excluded pair, any provider model call, any cloud runner, or any GPU.

The gate may produce a recovered prompt overlay for a future paid retry, but it must not execute
that retry.

Hard ceilings:

- provider model invocations: `0`,
- provider spend: `$0.00`,
- GPU use: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- cloud runner startup: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include:

1. a machine-readable diagnosis of why the iter64 receipt candidate failed,
2. proof that the diagnosis uses the current committed receipt schema and validator,
3. a recovered Telos receipt prompt overlay that includes the required fields and `sha256`
   construction rule without embedding secrets,
4. at least one local fixture receipt that validates with `python3 scripts/validate_receipts.py`,
5. at least one malformed fixture that fails for the expected reason,
6. redaction scan over all committed artifacts,
7. exact command output,
8. human-readable adversarial review,
9. machine-readable run summary with artifact hashes,
10. valid Telos receipt for this zero-spend gate.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- iter64 proof is present and audited,
- the iter64 Telos receipt candidate is classified as schema-incomplete,
- the recovered prompt overlay includes every required receipt field,
- the recovered prompt overlay explains that `sha256` is the canonical digest of the receipt with
  the `sha256` field blank or excluded,
- a local valid fixture passes `scripts/validate_receipts.py`,
- a local malformed fixture fails,
- provider calls remain `0`,
- provider spend remains `$0.00`,
- no GPU, cloud runner, Sentinel mutation, production/live-domain change, excluded-pair execution,
  or overclaim occurs.

## Falsifiers

Publish blocked/null evidence if:

- iter64 proof or audit evidence is missing,
- the iter64 invalid receipt cannot be loaded and classified,
- the current receipt schema or validator cannot be loaded,
- a recovered prompt overlay cannot be produced without changing paid-run results.

Publish a quality failure if:

- any provider call, provider spend, GPU, cloud runner, Sentinel mutation, production/live-domain
  mutation, or excluded-pair execution occurs,
- the recovered prompt omits a required receipt field,
- the local valid fixture does not validate,
- the malformed fixture does not fail,
- committed artifacts contain credential, project, account, token, service-account, VM, zone, or
  credential-path residue,
- unsupported benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only that the receipt prompt and local fixtures now align with
the committed Telos proof schema. It may not claim that a future paid Telos row will pass, that
Telos improves benchmark performance, or that Telos has a benchmark/model/state-of-the-art result.
