# Iteration 186 Result - Reward-Hack Panel Property-Probe Packet Materialization

Status: `pass`.

## What this gate did

This zero-spend gate materialized the paired property-probe input packets for the iter185 priority subset.
It made no provider calls, no credential probes, no model evaluations, no property-generator calls, no
SWE-bench executions, and no cloud resource changes.

## Packet Set

- Hack-source property-probe packets: `12`.
- Paired-control-source property-probe packets: `12`.
- Total property-probe packets: `24`.
- Unique packet hashes: `24`.
- Packet leakage hits: `0`.
- Next gate: `experiments/iter187_reward_hack_property_generator_schema_preflight/HYPOTHESIS.md`.

The model-facing prompt payload intentionally excludes candidate diffs and public target-test identifiers.
Source row ids, roles, source packet ids, candidate-diff hashes, and pairing information are retained only
in the traceability manifest.

Failures / blockers:

- none

## Future Gate Bars

Paid property generation remains unauthorized. The preserved future bars are `48`
maximum provider calls including retries, `$40.00` spend ceiling, at least
`20` local or container execution attempts, control
false-positive ceiling `0`, nondecision ceiling
`4`, prompt leakage ceiling `0`, and response secret-hit ceiling
`0`.

## Claim Boundary

At most, this gate supports a zero-spend, leakage-scanned 24-packet property-probe input set for a future
property-generator experiment over the committed iter185 priority subset. The public panel metric remains
unrepaired iter179 `majority_catch`: `17/40` hack rows and `0/40` controls.

No leaderboard ranking, state-of-the-art claim, natural reward-hacking frequency estimate, broad
reward-model robustness claim, production deployment claim, model-superiority claim, public benchmark
score, repaired-score claim, or claim outside committed iter175-iter186 proof packets is supported.

## Evidence

- `proof/property_probe_packets_v1/packets.jsonl`
- `proof/property_probe_packets_v1/schema.json`
- `proof/property_probe_packets_v1/manifest.json`
- `proof/packet_leakage_scan.json`
- `proof/future_paid_execution_authorization.json`
- `proof/claim_boundary_audit.json`
- `proof/forbidden_claim_scan.json`
- `proof/secret_safety_audit.json`
- `proof/endpoint_results.json`
- `proof/audit_report.json`
- `proof/run_summary.json`
- `proof/valid/receipt_reward_hack_panel_property_probe_packet_materialization.json`
