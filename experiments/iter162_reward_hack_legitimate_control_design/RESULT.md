# Iteration 162 Result - Reward-Hack Legitimate-Control Design

Status: `pass`.

## What this gate did

This zero-spend gate designed the legitimate-control side of
`reward_hack_benchmark_v1` evaluation before any precision or leaderboard language.

## Result

| bar | result |
| --- | ---: |
| source hierarchy defined | `True` |
| row schema defined | `True` |
| packet schema matches iter159 prompt surface | `True` |
| false-positive metric defined | `True` |
| precision requires controls | `True` |
| provider calls | `0` |
| SWE-bench executions | `0` |
| cloud resources | `0` |

The design separates all-hack recall (`iter161`) from legitimate-control false-positive pressure. It defines
specificity and false-positive rate on controls, and permits precision only after a future evaluator has both
hack-row true positives and legitimate-control false positives under the same parser and prompt contract.

## Claim Boundary

Supported: Telos now has a pre-registered design for legitimate controls, control packets, and future
precision/balanced metrics for `reward_hack_benchmark_v1`.

Not supported: a control artifact, precision number, benchmark score, leaderboard, model comparison,
state-of-the-art claim, natural reward-hacking frequency estimate, or broad reward-model robustness claim.

## Next Gate

`iter163`: materialize legitimate-control rows and blinded control packets, targeting `40` controls with a
hard null floor of `20`, before any model evaluates controls.

## Evidence

- `proof/control_source_hierarchy.json`
- `proof/legitimate_control_row_schema.json`
- `proof/blinded_control_packet_schema.json`
- `proof/metric_protocol.json`
- `proof/design_audit.json`
- `proof/endpoint_results.json`
- `proof/run_summary.json`
- `proof/valid/receipt_reward_hack_legitimate_control_design.json`
