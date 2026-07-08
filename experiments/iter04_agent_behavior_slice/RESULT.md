# Iteration 04 - Agent Behavior Slice Result

Status: `PASS`

## Result

The first real agent-behavior slice is:

```text
codeclash_battlesnake_instant_submit_pvp_slice
```

Selected config:

```text
configs/test/battlesnake_pvp_test.yaml
```

## Why This Slice

`iter03` proved the receipt loop on a dummy-vs-dummy CodeClash tournament. The next slice must
exercise real agent machinery without jumping to a paid model benchmark.

`configs/test/battlesnake_pvp_test.yaml` is the smallest public CodeClash config that does that:

- one BattleSnake simulation,
- one tournament round,
- one Mini-SWE-Agent player,
- one dummy opponent,
- deterministic `instant_submit` model,
- expected provider API calls: zero.

This adds agent trajectory and agent-stat evidence while preserving the cheap-first standard.

## Candidate Scorecard

| candidate | score | decision |
|---|---:|---|
| `configs/test/battlesnake_pvp_test.yaml` | 21 | selected |
| `configs/test/battlesnake_ladder_smoke.yaml` | 18 | stronger ladder workflow, higher moving parts |
| custom deterministic edit agent | 15 | useful later, but adds local harness design before public config |

Raw scorecard: [`proof/scorecard.json`](proof/scorecard.json)

## What This Does Not Claim

- No model capability is claimed.
- No CodeClash leaderboard result is claimed.
- No SWE-bench result is claimed.
- The selected deterministic model may submit without editing; the next gate must report that
  honestly from trajectory and diff-scope artifacts.

## Next Gate

Run `iter05_agent_behavior_smoke`:

1. execute the selected config,
2. preserve logs, metadata, trajectory, agent stats, and diff-scope records,
3. produce a Telos receipt,
4. publish a null if the run lacks trajectory or agent-stat evidence.

## Evidence

- Selected slice: [`proof/slice.json`](proof/slice.json)
- Candidate scorecard: [`proof/scorecard.json`](proof/scorecard.json)
- Decision: [`proof/decision.md`](proof/decision.md)
- Learning record: [`proof/learning_record.json`](proof/learning_record.json)
