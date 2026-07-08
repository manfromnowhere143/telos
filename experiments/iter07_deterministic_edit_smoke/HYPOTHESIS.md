# Iteration 07 - Deterministic Edit Smoke

Status: pre-registered, result pending.

## Purpose

Run the selected deterministic edit slice from `iter06` and verify that Telos can capture a
non-empty code diff through the real CodeClash Mini-SWE-Agent path.

## Frozen Slice

- CodeClash commit: `381cdfa05a35e8acd35853b9fc7e13005121b127`
- Overlay model config:
  `experiments/iter06_deterministic_edit_slice/proof/overlay/configs/mini/telos_edit_battlesnake_marker.yaml`
- Overlay run config:
  `experiments/iter06_deterministic_edit_slice/proof/overlay/configs/test/telos_battlesnake_edit_test.yaml`
- Effective CodeClash config: `configs/test/telos_battlesnake_edit_test.yaml`
- Expected modified file: `telos_marker.py`
- Expected provider cost: `0`
- Expected deterministic model invocations: at least `2`

## GitHub Execution Surface

```text
.github/workflows/codeclash-deterministic-edit.yml
```

## Bars

The gate passes only if all hold:

- CodeClash run exits 0.
- Metadata contains a parsed BattleSnake result.
- `p1` has a Mini-SWE-Agent trajectory artifact.
- `p1` agent stats record zero provider cost and at least two deterministic model invocations.
- `p1` diff-scope record is non-empty and names `telos_marker.py`.
- A Telos receipt validates with `scripts/validate_receipts.py`.
- No model capability, leaderboard, SWE-bench, production, or live-domain result is claimed.

## Falsifiers

Publish a null or blocked result if:

- the overlay cannot be applied to the pinned CodeClash checkout,
- the selected config requires provider credentials,
- the deterministic model path records fewer than two model invocations,
- the deterministic model path records nonzero provider cost,
- trajectory or agent_stats artifacts are missing,
- `p1` diff-scope evidence is absent or empty,
- the result cannot be separated from a benchmark claim.

## Scope Boundary

No provider model call is authorized by this gate. No GPU run is authorized. No production or
live-domain change is authorized.
