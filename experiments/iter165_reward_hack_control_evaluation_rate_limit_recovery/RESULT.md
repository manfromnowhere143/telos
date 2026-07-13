# Iteration 165 Result - Reward-Hack Control Evaluation Rate-Limit Recovery

Status: `pass`.

## What this gate did

This recovery gate preserved the `15` successful parsed control outputs from iter164 and attempted only
the missing legitimate-control packets after the iter164 `http_429` provider block.

## Result

| bar | result |
| --- | ---: |
| iter164 successful controls reused | `15` |
| recovery packets planned | `25` |
| recovery packets attempted | `25` |
| recovery provider successes | `25` |
| recovery provider errors | `0` |
| all-control parsed records | `40` |
| control `reward_hack` verdicts | `0` |
| control `legitimate` verdicts | `40` |
| control nondecisions | `0` |
| prompt leakage hits | `0` |
| response secret hits | `0` |
| recovery estimated cost guard | `$0.429550` |
| sequence estimated cost guard | `$0.727580` |
| SWE-bench executions | `0` |
| cloud resources | `0` |

## Combined Metrics


| metric | value |
| --- | ---: |
| true positives on all-hack rows | `3` |
| false positives on controls | `0` |
| recall on all-hack rows | `0.075` |
| false-positive rate on controls | `0.0` |
| specificity on controls | `1.0` |
| precision for `reward_hack` flag | `1.0` |
| balanced detection rate | `0.5375` |

Failures:

- none

## Interpretation

If status is `pass`, this closes the iter164 rate-limit block without re-calling successful controls:
all `40` paired legitimate controls have parsed outputs for the same model used in iter161.

## Claim Boundary

Supported if status is pass: one frozen model judge has a complete paired all-hack/control metric over the
current 40-row reward-hack artifact and 40 paired legitimate controls.

Not supported: leaderboard rankings, model superiority, state-of-the-art claims, natural reward-hacking
frequency estimates, broad reward-model robustness claims, or claims about models not evaluated in this
control-evaluation sequence.

## Next Gate

Design the moonshot evaluator-family gate from the measured recall/specificity shape. Do not call this
single-model sequence a leaderboard.

## Evidence

- `proof/model_binding.json`
- `proof/provider_call_ledger.jsonl`
- `proof/parsed_judge_outputs.jsonl`
- `proof/all_control_parsed_judge_outputs.jsonl`
- `proof/leakage_audit.json`
- `proof/metric_summary.json`
- `proof/endpoint_results.json`
- `proof/run_summary.json`
- `proof/valid/receipt_reward_hack_control_evaluation_rate_limit_recovery.json`
