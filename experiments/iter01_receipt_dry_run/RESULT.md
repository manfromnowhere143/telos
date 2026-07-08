# Iteration 01 - Receipt Dry Run Result

Status: `pass`

## Result

The receipt dry run passed.

The valid receipt passes canonical validation, the deliberately invalid receipt is rejected, and the
learning record names a concrete next action.

## Evidence

| artifact | role |
|---|---|
| [`proof/valid/receipt_valid.json`](proof/valid/receipt_valid.json) | valid receipt |
| [`proof/invalid/receipt_bad_sha.json`](proof/invalid/receipt_bad_sha.json) | invalid receipt, expected rejection |
| [`proof/learning_record.json`](proof/learning_record.json) | learning ledger record |

Command:

```bash
python3 scripts/validate_receipts.py experiments/iter01_receipt_dry_run/proof
```

Expected result:

```text
receipt validation: 1 valid receipts passed
```

## What This Supports

The Telos receipt contract can be checked without trusting final-answer text. A malformed digest is
rejected, and the learning ledger can carry the next action.

## What This Does Not Support

- No model was evaluated.
- No public benchmark task was run.
- No CodeClash, SWE-bench, RE-Bench, tau-bench, or AgentDojo score is claimed.

## Next Action

Freeze the first public-task slice. The next experiment should use a small software-agent task
anchored to the selected CodeClash + SWE-bench Verified target and measure whether a real attempt
can emit a complete Telos receipt.
