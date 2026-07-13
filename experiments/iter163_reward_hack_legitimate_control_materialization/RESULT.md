# Iteration 163 Result - Reward-Hack Legitimate-Control Materialization

Status: `pass`.

## What this gate did

This zero-provider gate paired every `reward_hack_benchmark_v1` row with the public SWE-bench Verified gold
patch for the same instance, then wrote blinded legitimate-control judge packets.

## Result

| bar | result |
| --- | ---: |
| control rows | `40` |
| paired controls | `40` |
| disjoint controls | `0` |
| source audit status | `pass` |
| leakage audit status | `pass` |
| hack/control diff hash overlap | `0` |
| provider calls | `0` |
| model evaluations | `0` |
| SWE-bench executions | `0` |
| cloud resources | `0` |

## Interpretation

The gate materialized exactly 40 paired legitimate controls, one for each reward-hack row, and blinded their packet surface without prompt leakage. This enables a future control-set model run; it is not itself a precision result.

## Claim Boundary

Supported if status is pass: Telos has a hash-checked paired legitimate-control artifact and blinded
control packets for `reward_hack_benchmark_v1`.

Not supported: a model score, precision number, benchmark score, leaderboard, model comparison,
state-of-the-art claim, natural reward-hacking frequency estimate, broad reward-model robustness claim, or
claim that any model has been evaluated on these controls.

## Next Gate

`iter164`: run one bounded model judge over the blinded legitimate controls under the iter160 parser, then combine with iter161 only within the pre-declared metric boundary.

## Evidence

- `benchmarks/reward_hack_benchmark_v1/legitimate_controls_v1/`
- `benchmarks/reward_hack_benchmark_v1/legitimate_controls_v1/blinded_control_packets_v1/`
- `proof/source_audit.json`
- `proof/leakage_audit.json`
- `proof/endpoint_results.json`
- `proof/run_summary.json`
- `proof/valid/receipt_reward_hack_legitimate_control_materialization.json`
