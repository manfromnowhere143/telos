# Iteration 05 - Agent Behavior Smoke

Status: pre-registered, result pending.

## Purpose

Run the selected CodeClash Mini-SWE-Agent behavior slice and convert its artifacts into a Telos
receipt.

This is not a model-capability benchmark. It uses a deterministic test model to exercise the real
agent path without provider API calls.

## Frozen Slice

- CodeClash commit: `381cdfa05a35e8acd35853b9fc7e13005121b127`
- Config: `configs/test/battlesnake_pvp_test.yaml`
- Agent under test: `p1`
- Agent type: `mini`
- Model: `instant_submit`
- Model class: `minisweagent.models.test_models.DeterministicModel`
- Expected provider cost: `0`
- Expected deterministic model invocations: at least `1`

## Primary Command

```bash
uv run codeclash run configs/test/battlesnake_pvp_test.yaml -o /tmp/telos-codeclash-agent-behavior-smoke
```

## GitHub Execution Surface

If local Docker remains blocked, run:

```text
.github/workflows/codeclash-agent-behavior.yml
```

The workflow fails if `p1` has no Mini-SWE-Agent trajectory, if `p1` agent stats are missing, if
deterministic-model invocations are zero, or if provider cost is nonzero.

## Bars

The gate passes only if all hold:

- CodeClash run exits 0.
- Metadata contains a parsed BattleSnake round result.
- `p1` has a Mini-SWE-Agent trajectory artifact.
- `p1` agent stats record zero provider cost and at least one deterministic model invocation.
- Player change records exist for diff-scope evidence.
- A Telos receipt validates with `scripts/validate_receipts.py`.
- No model capability, leaderboard, or SWE-bench result is claimed.

## Falsifiers

Publish a null or blocked result if:

- the selected config requires provider credentials,
- the deterministic model path records zero model invocations,
- the deterministic model path records nonzero provider cost,
- trajectory or agent_stats artifacts are missing,
- diff-scope evidence is absent,
- the result cannot be separated from a benchmark claim.

## Scope Boundary

No GPU run is authorized. No provider model call is authorized.
