# Iteration 06 - Deterministic Edit Slice Result

Status: `PASS`

## Result

The selected deterministic edit slice is:

```text
codeclash_overlay_workspace_python_marker_edit_slice
```

It uses the pinned public CodeClash checkout plus a committed Telos overlay:

- [`proof/overlay/configs/mini/telos_edit_battlesnake_marker.yaml`](proof/overlay/configs/mini/telos_edit_battlesnake_marker.yaml)
- [`proof/overlay/configs/test/telos_battlesnake_edit_test.yaml`](proof/overlay/configs/test/telos_battlesnake_edit_test.yaml)

## Why This Slice

The slice keeps the real CodeClash Mini-SWE-Agent path and replaces only the deterministic model
outputs:

1. create `telos_marker.py` in the player workspace,
2. submit.

This should produce the first non-empty `p1` Python diff-scope artifact while keeping provider cost,
GPU spend, and cloud spend at zero.

Correction after first execution attempt: workflow run `28937796613` completed the CodeClash run but
failed in the summarizer because the original target path was outside the player workspace and no
modified file was recorded. The corrected slice targets `telos_marker.py`, a deterministic Python
file created inside the workspace.

## Candidate Scorecard

| candidate | score | decision |
|---|---:|---|
| `codeclash_overlay_workspace_python_marker_edit` | 25 | selected |
| `minimal_local_edit_harness_public_fixture` | 19 | defer |
| `codeclash_ladder_instant_submit_variant` | 14 | reject for this gate |

Raw scorecard: [`proof/scorecard.json`](proof/scorecard.json)

## What This Does Not Claim

- No provider-model capability is claimed.
- No CodeClash leaderboard result is claimed.
- No SWE-bench result is claimed.
- No production/live-domain change occurred.
- The slice is not a benchmark score; it is the next receipt-quality gate.

## Next Gate

Run `iter07_deterministic_edit_smoke` and publish a receipt or null result.

## Evidence

- Selected slice: [`proof/slice.json`](proof/slice.json)
- Candidate scorecard: [`proof/scorecard.json`](proof/scorecard.json)
- Decision: [`proof/decision.md`](proof/decision.md)
- Learning record: [`proof/learning_record.json`](proof/learning_record.json)
