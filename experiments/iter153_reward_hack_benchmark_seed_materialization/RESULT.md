# Iteration 153 Result - Reward-Hack Benchmark Seed Materialized

Status: `PASS`.

## What this gate did

Converted the committed iter152 reward-model-gaming evidence into a reviewer-facing seed artifact under
`benchmarks/reward_hack_seed_v0/`. This was a zero-spend materialization and audit gate: no provider calls,
cloud resources, SWE-bench executions, or new judge calls were added.

## Result

The seed package contains exactly `20` execution-verified both-miss hack rows across `8` repositories.

| bar | result |
| --- | ---: |
| rows materialized | `20/20` |
| repositories represented | `8/8` |
| rows with non-empty hack diff and SHA256 | `20/20` |
| rows traceable to committed iter152 raw evidence | `20/20` |
| survives every static layer label | `5/20` |
| new provider calls | `0` |
| new cloud resources | `0` |
| new SWE-bench executions | `0` |
| new judge calls | `0` |

Primary artifact: [`../../benchmarks/reward_hack_seed_v0/reward_hack_seed_v0.jsonl`](../../benchmarks/reward_hack_seed_v0/reward_hack_seed_v0.jsonl).
Manifest: [`../../benchmarks/reward_hack_seed_v0/manifest.json`](../../benchmarks/reward_hack_seed_v0/manifest.json).

## The finding

The iter152 reward-hack evidence is now usable as an auditable seed package. Each row has a stable row id,
repository and instance identifiers, the hack diff, a diff SHA256, static-verifier verdict labels, the
`survives_all_static` label, and links plus hashes back to the committed iter152 proof artifacts. The seed
preserves the load-bearing iter152 count: `5/20` rows survive the deterministic detector and both frontier
reward-model judges, so they require held-out execution.

## Honest scope

- This is a seed artifact, not a released benchmark.
- This is not a benchmark score, leaderboard, model comparison, state-of-the-art result, or claim about
  naturally-emergent reward-hacking frequency.
- The seed inherits iter152's scope: one adversary, two reward-model judges, constructed both-miss hacks,
  and `N=20`.
- The gate added no new model or execution evidence; it made existing committed evidence easier to inspect.

## Claim boundary

Supported: Telos materialized a validated reward-hack seed from the 20 iter152 hack diffs, preserving
8-repository coverage, diff hashes, source-proof traceability, static-verifier labels, and the `5/20`
survives-all-static label. Not supported: a released benchmark, benchmark score, leaderboard, model
superiority claim, state-of-the-art claim, natural-RL frequency claim, or any reward-model result beyond
iter152's bounded evidence.

## Next gate

Pre-register the benchmark-expansion gate before any paid or cloud work: grow `N` and judge diversity from
the validated seed while preserving execution proof, source traceability, spend accounting, and the same
claim boundary.

## Evidence

- `benchmarks/reward_hack_seed_v0/reward_hack_seed_v0.jsonl`
- `benchmarks/reward_hack_seed_v0/manifest.json`
- `benchmarks/reward_hack_seed_v0/schema.json`
- `proof/audit_report.json`
- `proof/endpoint_results.json`, `proof/run_summary.json`, `proof/learning_record.json`
- `proof/valid/receipt_reward_hack_benchmark_seed_materialization.json`
- `scripts/run_reward_hack_benchmark_seed_materialization.py`
