# Iteration 00 - Target Survey

Status: pre-registered, result pending.

## Purpose

Choose the first benchmark target for Telos without relying on taste or momentum.
This is a survey gate, not a result about agents.

## Hypothesis

At least one public benchmark family will clear the Telos target bar:

- adjusted score at least 16,
- every positive component at least 3,
- operational cost at most 3,
- public baseline exists,
- first-run falsifier can be stated before harness work begins.

If no candidate clears the bar, the correct result is a survey null.

## Candidates

The survey must score:

1. SWE-bench Verified / coding agents
2. METR RE-Bench / AI R&D agents
3. tau-bench / service agents
4. AgentDojo / adversarial tool agents
5. Telos overlay on public tasks

## Scoring

Use the scorecard implemented in [`../../telos/scorecard.py`](../../telos/scorecard.py):

```text
frontier_relevance
+ public_baseline_quality
+ falsifiability
+ evidence_surface
+ aweb_fit
- saturation_risk
- operational_cost
```

Scores are integers from 0 to 5. Every score must cite a source or a local artifact.

## Required Proof Artifacts

Publish these under `proof/`:

- `sources.md`: source URLs and short notes,
- `scorecard.json`: candidate scores and rationale,
- `decision.md`: selected target or survey null,
- `review.md`: adversarial review of the target decision.

## Falsifiers

The survey fails to select a target if:

- no candidate has a public baseline,
- no candidate can emit evidence beyond final answer text,
- every candidate either costs too much or is too saturated,
- the selected target requires private data to reproduce,
- the selected target has no clear first-run falsifier.

## Output Rule

The result must state one of:

- `TARGET_SELECTED`,
- `HYBRID_OVERLAY_SELECTED`,
- `SURVEY_NULL`,
- `BLOCKED`.

No `iter01` experiment may be created until this result exists.
