# Iteration 156 Result - Reward-Hack Benchmark v1 Manifest

Status: `pass_released_artifact_no_score`.

The zero-spend manifest gate passed. Telos now has a hash-checked
`reward_hack_benchmark_v1` artifact with exactly `40` constructed, execution-verified both-miss
reward-hack rows.

This is a released row artifact, not a benchmark score. No leaderboard, model comparison,
state-of-the-art result, broad reward-model robustness claim, or natural reward-hacking frequency claim
is made.

## What Ran

- Materializer: `scripts/materialize_reward_hack_benchmark_v1.py`.
- Inputs: committed `reward_hack_seed_v0`, iter154 expansion rows, and iter155 adaptive expansion rows.
- New provider calls: `0`.
- New SWE-bench executions: `0`.
- New cloud resources: `0`.

Primary artifact:

- `benchmarks/reward_hack_benchmark_v1/reward_hack_benchmark_v1.jsonl`
- `benchmarks/reward_hack_benchmark_v1/manifest.json`
- `benchmarks/reward_hack_benchmark_v1/schema.json`

## Result

| metric | value |
| --- | ---: |
| manifest rows | `40` |
| unique instance ids | `40` |
| execution-verified both-miss rows | `40/40` |
| rows with hack diff SHA256 | `40/40` |
| rows with official report hash | `40/40` |
| rows with source traceability | `40/40` |
| seed rows | `20` |
| iter154 rows | `17` |
| iter155 rows | `3` |
| represented repositories | `11` |
| deterministic detector evaded | `40/40` |
| `gpt-5.6-terra` fooled | `16/40` |
| `claude-opus-4-8` fooled | `19/40` |
| survives all static layers | `13/40` |
| new provider calls | `0` |
| new SWE-bench executions | `0` |
| new cloud resources | `0` |

Repositories represented:

- `astropy/astropy`
- `django/django`
- `matplotlib/matplotlib`
- `pallets/flask`
- `psf/requests`
- `pydata/xarray`
- `pylint-dev/pylint`
- `pytest-dev/pytest`
- `scikit-learn/scikit-learn`
- `sphinx-doc/sphinx`
- `sympy/sympy`

## Interpretation

The benchmark line is now reviewer-facing: every included row has a normalized row id, source artifact
path, source row hash, hack diff hash, official report hash, and static-verifier labels. The strongest
benchmark stress signal is that `13/40` rows survive every static layer tested: deterministic detector,
`gpt-5.6-terra`, and `claude-opus-4-8`.

The result remains bounded. The artifact contains constructed reward-hack rows from Telos experiments; it
does not estimate natural reward-hacking frequency and does not rank models. It is suitable as a
hash-checked evaluation artifact for future scoring gates, not itself a score.

## Claim Boundary

At most: Telos released a hash-checked v1 artifact of `40` constructed, execution-verified both-miss
reward-hack rows gathered from iter152 through iter155.

Not supported: a model benchmark score, leaderboard ranking, state-of-the-art performance, natural
reward-hacking frequency, broad reward-model robustness, or a claim that any model has been evaluated on
this artifact.
