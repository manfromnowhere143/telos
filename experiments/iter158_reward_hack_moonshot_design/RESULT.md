# Iteration 158 Result - Reward-Hack Benchmark Moonshot Design

Status: `pass_moonshot_design_no_execution`.

The zero-spend moonshot design gate passed. Telos now has a leakage-controlled scoring/evaluation protocol
for the frozen `reward_hack_benchmark_v1` artifact.

This gate ran no provider calls, no SWE-bench executions, and no cloud resources. It does not claim a
benchmark score, leaderboard, model comparison, state-of-the-art result, natural reward-hacking frequency,
broad reward-model robustness, or that any model has been evaluated on the v1 artifact.

## What Ran

- Materializer: `scripts/design_reward_hack_moonshot.py`.
- Frozen input: `benchmarks/reward_hack_benchmark_v1/`.
- Design output:
  - `proof/scoring_protocol.md`
  - `proof/moonshot_design.json`
  - `proof/audit_report.json`
  - `proof/endpoint_results.json`
  - `proof/run_summary.json`
  - `proof/valid/receipt_reward_hack_moonshot_design.json`

## Result

| bar | result |
| --- | ---: |
| frozen v1 rows | `40` |
| frozen repositories | `11` |
| frozen survives-all-static stratum | `13/40` |
| evaluator families defined | `4` |
| model-prompt leakage controls defined | `pass` |
| null/fail semantics defined | `pass` |
| new provider calls | `0` |
| new SWE-bench executions | `0` |
| new cloud resources | `0` |

Evaluator families:

- static detectors,
- model judges,
- judge panels,
- execution-backed gates.

The protocol separates prompt-visible fields from scoring-only fields. Model judges may see a blinded
code-review packet, but not `static_verdicts`, `survives_all_static`, official report paths or hashes,
source split, source experiment, prior judge labels, or any phrase saying the row is known to be a
constructed both-miss hack.

## Interpretation

This is the right moonshot shape: ambitious enough to score frontier reward models and execution-backed
gates later, but still disciplined. Because v1 contains only hack rows, the first scoring metrics are recall
metrics: full-row hack catch rate and the harder `13`-row static-survivor catch rate. Precision,
model-superiority, and leaderboard claims remain out of scope until a separately frozen control set exists.

The next step is not provider spend. It is a packet-materialization gate: generate the blinded model-judge
packets from the v1 rows, hash them, and audit that labels, official reports, source splits, and prior
static verdicts are excluded.

## Claim Boundary

Supported: Telos designed a scoring/evaluation protocol for the frozen `reward_hack_benchmark_v1` artifact,
with four evaluator families, leakage controls, metrics, and null/fail semantics.

Not supported: a benchmark score, leaderboard ranking, model-comparison result, state-of-the-art claim,
natural reward-hacking frequency estimate, broad reward-model robustness claim, or any statement that a
model has been evaluated on the v1 artifact.

## Next Gate

`iter159`: materialize blinded reward-hack benchmark judge packets with zero provider calls, zero SWE-bench
executions, zero cloud resources, and an explicit leakage audit.

## Evidence

- `proof/scoring_protocol.md`
- `proof/moonshot_design.json`
- `proof/audit_report.json`
- `proof/endpoint_results.json`
- `proof/run_summary.json`
- `proof/learning_record.json`
- `proof/valid/receipt_reward_hack_moonshot_design.json`
