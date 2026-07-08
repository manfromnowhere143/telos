# Iteration 00 - Target Survey Result

Status: `HYBRID_OVERLAY_SELECTED`

## Result

The first Telos target is a hybrid completion-proof overlay on public software-agent tasks:

```text
telos_codeclash_swebench_overlay
```

Adjusted score:

```text
5 + 5 + 5 + 5 + 5 - 1 - 2 = 22
```

The frozen gate required adjusted score at least 16, no positive component below 3, operational
cost at most 3, public baseline support, and a first-run falsifier. The selected target clears all
bars.

## Scorecard

| candidate | adjusted score | decision |
|---|---:|---|
| Telos overlay on CodeClash + SWE-bench Verified | 22 | selected |
| SWE-bench Verified alone | 20 | strong anchor, not enough goal-shaped pressure alone |
| METR RE-Bench | 17 | later high-value line, cost above first-run bar |
| AgentDojo | 16 | later security line |
| tau2/tau3-bench | 14 | later service-agent line |

Raw scorecard: [`proof/scorecard.json`](proof/scorecard.json)

## Why This Target

CodeClash is aligned with the Telos question because it evaluates goal-oriented software
engineering rather than only isolated ticket resolution. SWE-bench Verified is aligned because it
provides human-validated real GitHub tasks, patch artifacts, tests, and a stable public leaderboard.

Together they let Telos ask a sharper question than either benchmark asks alone:

> Did the agent complete the real objective, and can the claim be proven from artifacts?

## What This Does Not Claim

- No model has been evaluated by Telos yet.
- No benchmark score has improved.
- No public leaderboard result is claimed.
- No receipt protocol result exists until `iter01` runs.

## First Falsifier For The Next Run

`iter01` fails if a single baseline task attempt cannot produce an independently valid receipt with:

- stated goal,
- acceptance criteria,
- test or artifact evidence,
- diff-scope evidence when code changes,
- falsifiers,
- canonical `sha256`.

If the receipt cannot validate, the protocol fails before any benchmark claim.

## Evidence

- Sources: [`proof/sources.md`](proof/sources.md)
- Decision: [`proof/decision.md`](proof/decision.md)
- Adversarial review: [`proof/review.md`](proof/review.md)
