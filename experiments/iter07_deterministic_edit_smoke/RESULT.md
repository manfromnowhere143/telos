# Iteration 07 - Deterministic Edit Smoke Result

Status: `PASS`

## Result

The selected deterministic Mini-SWE-Agent BattleSnake edit smoke ran successfully on GitHub
Actions and produced a valid Telos receipt with a real non-empty `p1` diff.

GitHub run:

```text
https://github.com/manfromnowhere143/telos/actions/runs/28938078039
```

Frozen CodeClash commit:

```text
381cdfa05a35e8acd35853b9fc7e13005121b127
```

## What Passed

- Docker readiness passed on the Ubuntu runner.
- CodeClash was cloned at the frozen commit.
- `uv run codeclash run configs/test/telos_battlesnake_edit_test.yaml` exited successfully.
- `p1` used the Mini-SWE-Agent integration with the deterministic
  `telos_edit_workspace_marker` model.
- `p1` produced a Mini-SWE-Agent trajectory artifact.
- `p1` agent stats recorded zero provider cost and two deterministic model invocations.
- `p1` diff-scope evidence is non-empty and names `telos_marker.py`.
- `p2` remained an empty-diff dummy control.
- The Telos receipt validates with `scripts/validate_receipts.py`.
- The proof bundle audits cleanly with `scripts/audit_deterministic_edit_smoke.py`.

## Tournament Summary

The configured tournament used one round and one simulation, while metadata emitted two parsed
round-stat entries. Both parsed entries reported valid submissions.

| parsed round | winner | p1 score | p2 score | submissions valid |
|---:|---|---:|---:|---|
| 0 | p1 | 1 | 0.0 | yes |
| 1 | p1 | 1 | 0.0 | yes |

The deterministic edit created this workspace file in `p1`:

```text
telos_marker.py
```

The file content captured in the CodeClash change record is:

```python
TELOS_DETERMINISTIC_EDIT_MARKER = True
```

## What This Does Not Claim

- No provider-model capability is claimed.
- No CodeClash leaderboard result is claimed.
- No SWE-bench result is claimed.
- No production/live-domain change occurred.
- The result does not prove that a model can improve a game bot; it proves that Telos can capture
  and audit a real non-empty diff through the public CodeClash Mini-SWE-Agent path.

## Evidence

- Receipt: [`proof/valid/receipt_deterministic_edit_smoke.json`](proof/valid/receipt_deterministic_edit_smoke.json)
- Run summary: [`proof/run_summary.json`](proof/run_summary.json)
- Adversarial review: [`proof/review.md`](proof/review.md)
- Raw artifacts: [`proof/raw`](proof/raw)
- Learning record: [`proof/learning_record.json`](proof/learning_record.json)
