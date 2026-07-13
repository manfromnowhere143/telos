# Iteration 161 - Reward-Hack Single-Model Judge Execution

Status: pre-registered execution gate; no provider calls, SWE-bench executions, cloud resources, or model
scoring have been run for this gate.

## Why this gate exists

`iter159` froze blinded judge packets for the 40-row `reward_hack_benchmark_v1` artifact, and `iter160`
validated a strict local parser for judge outputs. The next evidence step is a bounded single-model
execution that uses those frozen packets and parser without exposing labels, official reports, source
splits, prior static verdicts, or known-both-miss wording.

## Method

Inputs:

- `benchmarks/reward_hack_benchmark_v1/blinded_model_judge_packets_v1/packets.jsonl`
- `benchmarks/reward_hack_benchmark_v1/blinded_model_judge_packets_v1/manifest.json`
- `experiments/iter159_reward_hack_blinded_packet_materialization/proof/leakage_audit.json`
- `experiments/iter160_reward_hack_judge_parser_preflight/proof/parser_audit.json`
- `telos/reward_hack_judge_parser.py`

Planned output:

- frozen model-binding record before the first call,
- raw prompt records for every attempted packet,
- raw provider output records for every attempted packet,
- parsed judge-output records produced only by the iter160 parser,
- provider call ledger and spend ledger,
- redaction/leakage audit over prompts and retained outputs,
- run summary with nulls at full weight.

Execution envelope:

- one model only,
- temperature `0` when the selected provider supports it,
- at most one provider call per packet,
- no parser-repair retry,
- provider call ceiling: `40`,
- spend ceiling: `$20.00`,
- new SWE-bench executions: `0`,
- new cloud runner/resources: `0`.

## Numeric Bars

Minimum pass bars:

- packet artifact hash matches the iter159 packet manifest,
- iter159 leakage audit status is `pass`,
- iter160 parser audit status is `pass`,
- model binding is frozen before the first provider call,
- prompt payload fields match the iter159 packet contract exactly,
- prompt scan finds `0` labels, official reports, report hashes, source splits, source experiments, prior
  judge labels, static verdicts, or known-both-miss wording,
- provider calls are `<= 40`,
- spend is `<= $20.00`,
- every attempted output is parsed by `telos/reward_hack_judge_parser.py`,
- refusals are counted as `refusal`, malformed or missing-field outputs as `invalid`, and inconclusive
  outputs as `inconclusive`,
- raw prompts, raw outputs, parsed records, parser errors, call ledger, and spend ledger are retained,
- new SWE-bench executions: `0`,
- new cloud runner/resources: `0`.

Reported but not pass-required:

- `reward_hack` verdict count and rate over the 40 all-hack rows,
- refusal count and rate,
- invalid count and rate,
- inconclusive count and rate,
- per-repository counts,
- cost and token totals.

## Falsifiers

1. Packet hashes differ from the iter159 frozen packet manifest.
2. Iter159 leakage audit or iter160 parser audit is not `pass`.
3. Any prompt includes labels, official reports, source splits, source experiments, prior static verdicts,
   or known-both-miss wording.
4. Any output is interpreted without the iter160 parser.
5. Provider calls or spend exceed the pre-registered ceiling.
6. A provider/runtime block is hidden instead of published as blocked/null evidence.

## Claim Boundary

At most, if the gate passes: "One frozen model judge was evaluated on the 40 blinded
`reward_hack_benchmark_v1` packets under the iter160 parser, and its recall/refusal/invalid rates on this
all-hack artifact were recorded."

Not supported: precision, leaderboard rankings, model superiority, state-of-the-art claims, natural
reward-hacking frequency estimates, broad reward-model robustness claims, or any claim about models not run
in this gate.
