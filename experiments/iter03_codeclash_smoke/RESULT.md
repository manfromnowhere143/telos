# Iteration 03 - CodeClash Smoke Receipt Result

Status: `PASS`

## Result

The no-LLM CodeClash dummy tournament ran successfully on GitHub Actions and produced a valid
Telos receipt.

GitHub run:

```text
https://github.com/manfromnowhere143/telos/actions/runs/28935161907
```

Frozen CodeClash commit:

```text
381cdfa05a35e8acd35853b9fc7e13005121b127
```

## What Passed

- Docker readiness passed on the Ubuntu runner.
- CodeClash was cloned at the frozen commit.
- CodeClash dependencies installed with `uv`.
- CodeClash dummy-arena unit smoke passed: `9 passed`.
- `uv run codeclash run configs/test/dummy.yaml` exited successfully.
- The tournament produced metadata, logs, player change records, and round archives.
- The Telos receipt validates with `scripts/validate_receipts.py`.

## Tournament Summary

The run produced four competition phases: initial round `0` plus rounds `1..3`.

| round | winner | p1 score | p2 score | submissions valid |
|---:|---|---:|---:|---|
| 0 | p1 | 513 | 487 | yes |
| 1 | p1 | 519 | 481 | yes |
| 2 | p1 | 504 | 496 | yes |
| 3 | p1 | 503 | 497 | yes |

The dummy agents made no code changes. That is expected for this smoke: the gate tests artifact
capture and receipt validity, not model behavior.

## What This Does Not Claim

- No model was evaluated.
- No CodeClash leaderboard result is claimed.
- No SWE-bench result is claimed.
- No production/live-domain change occurred.
- The result does not prove that a model can complete the task; it proves the receipt loop can
  capture a public CodeClash run.

## Evidence

- Receipt: [`proof/valid/receipt_codeclash_smoke.json`](proof/valid/receipt_codeclash_smoke.json)
- Run summary: [`proof/run_summary.json`](proof/run_summary.json)
- Adversarial review: [`proof/review.md`](proof/review.md)
- Raw artifacts: [`proof/raw`](proof/raw)
- Learning record: [`proof/learning_record.json`](proof/learning_record.json)
