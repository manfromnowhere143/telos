# Iteration 05 - Agent Behavior Smoke Result

Status: `PASS`

## Result

The selected deterministic Mini-SWE-Agent BattleSnake PvP smoke ran successfully on GitHub Actions
and produced a valid Telos receipt.

GitHub run:

```text
https://github.com/manfromnowhere143/telos/actions/runs/28936411484
```

Frozen CodeClash commit:

```text
381cdfa05a35e8acd35853b9fc7e13005121b127
```

## What Passed

- Docker readiness passed on the Ubuntu runner.
- CodeClash was cloned at the frozen commit.
- `uv run codeclash run configs/test/battlesnake_pvp_test.yaml` exited successfully.
- `p1` used the Mini-SWE-Agent integration with the deterministic `instant_submit` model.
- `p1` produced a Mini-SWE-Agent trajectory artifact.
- `p1` agent stats recorded zero provider cost and one deterministic model invocation.
- Player change records were captured for both players.
- The Telos receipt validates with `scripts/validate_receipts.py`.
- The proof bundle audits cleanly with `scripts/audit_agent_behavior_smoke.py`.

## Tournament Summary

The configured tournament used one round and one simulation, while metadata emitted two parsed
round-stat entries. Both parsed entries reported valid submissions.

| parsed round | winner | p1 score | p2 score | submissions valid |
|---:|---|---:|---:|---|
| 0 | p1 | 1 | 0.0 | yes |
| 1 | p1 | 1 | 0.0 | yes |

The deterministic model submitted immediately. The empty diffs are expected for this gate: the
measurement is whether Telos can capture the real Mini-SWE-Agent path, trajectory, stats, and
diff-scope records without provider spend.

## What This Does Not Claim

- No provider-model capability is claimed.
- No CodeClash leaderboard result is claimed.
- No SWE-bench result is claimed.
- No production/live-domain change occurred.
- The result does not prove that an agent can improve a game bot; it proves that the Telos receipt
  loop can capture deterministic Mini-SWE-Agent behavior.

## Evidence

- Receipt: [`proof/valid/receipt_agent_behavior_smoke.json`](proof/valid/receipt_agent_behavior_smoke.json)
- Run summary: [`proof/run_summary.json`](proof/run_summary.json)
- Adversarial review: [`proof/review.md`](proof/review.md)
- Raw artifacts: [`proof/raw`](proof/raw)
- Learning record: [`proof/learning_record.json`](proof/learning_record.json)
