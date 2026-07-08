# Learning Engine

Telos learns by turning each experiment into a small durable record:

1. what was tried,
2. whether the gate passed, failed, or blocked,
3. what evidence supports that status,
4. what was learned,
5. what the next action is.

The learning engine is not autonomous scope expansion. It is controlled accumulation. Each record
can move the next gate, but it cannot weaken a frozen bar or invent a benchmark result.

## Loop

```mermaid
flowchart LR
  H["hypothesis<br/>bars + falsifiers"] --> R["run<br/>smallest faithful gate"]
  R --> E["evidence<br/>receipts + logs"]
  E --> L["learning record<br/>insight + next action"]
  L --> N["next hypothesis"]
  classDef base fill:#f6f8fa,stroke:#57606a,color:#1f2328;
  classDef proof fill:#e4f0ff,stroke:#1565c0,color:#0c2742;
  classDef next fill:#e2f3e5,stroke:#2e7d32,color:#13361b;
  class H,R base;
  class E,L proof;
  class N next;
```

## Contract

Learning records live at:

```text
experiments/<id>/proof/learning_record.json
```

They must contain:

- `experiment_id`
- `status`
- `result_path`
- `evidence_paths`
- `insight`
- `next_action`

The validator is:

```bash
python3 scripts/validate_learning_ledger.py
```

## Current Learning State

| experiment | status | insight | next action |
|---|---|---|---|
| `iter01_receipt_dry_run` | pass | receipt validation is independently checkable | freeze first public-task slice |

The next experiment should not spend cloud resources until the public-task slice names the exact
task, expected artifact shape, and falsifier.
