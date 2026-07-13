# Iteration 161 Result - Reward-Hack Single-Model Judge Execution

Status: `pass_single_model_judge_execution`.

This gate used the frozen iter159 packets and iter160 parser under a `40`-call
and `$20.00` spend ceiling.

## What Ran

- Runner: `scripts/run_reward_hack_single_model_judge_execution.py`.
- Provider: `google_vertex`.
- Model: `gemini-2.5-flash`.
- Attempted provider calls: `40`.
- Provider successes: `40`.
- Provider errors: `0`.
- Estimated cost guard: `$0.734250` / `$20.00`.

## Result

| bar | result |
| --- | ---: |
| attempted packet count | `40` |
| provider success count | `40` |
| provider error count | `0` |
| parsed status counts | `{"parsed": 40}` |
| verdict counts | `{"legitimate": 37, "reward_hack": 3}` |
| prompt leakage hits | `0` |
| response secret hits | `0` |
| new SWE-bench executions | `0` |
| new cloud runner/resources | `0` |

## Interpretation

The run completed one provider call for each frozen packet and parsed every output with the iter160 parser. Reported rates are recall/refusal/invalid rates on this all-hack artifact only; they are not precision, leaderboard, or model-superiority claims.

## Claim Boundary

Supported if status is pass: one frozen model judge was evaluated on the 40
blinded `reward_hack_benchmark_v1` packets under the iter160 parser, and its
recall/refusal/invalid rates on this all-hack artifact were recorded.

Not supported: precision, leaderboard rankings, model superiority,
state-of-the-art claims, natural reward-hacking frequency estimates, broad
reward-model robustness claims, or any claim about models not run in this gate.

## Next Gate

`iter162`: design a separate control-set/precision gate before any leaderboard or model-superiority claim.

## Evidence

- `proof/model_binding.json`
- `proof/provider_call_ledger.jsonl`
- `proof/parsed_judge_outputs.jsonl`
- `proof/leakage_audit.json`
- `proof/endpoint_results.json`
- `proof/run_summary.json`
- `proof/valid/receipt_reward_hack_single_model_judge_execution.json`
