# Iteration 08 - Provider Model Pilot Slice

Status: pre-registered, result pending.

## Purpose

Select the first paid provider-model pilot only after the deterministic receipt loop has proven
that CodeClash Mini-SWE-Agent trajectory, stats, raw artifacts, and non-empty diffs can be audited.

This is a selection gate, not a model run.

## Candidate Families

Score at least three candidate pilots:

1. CodeClash BattleSnake provider-model edit against a dummy or frozen baseline control.
2. SWE-bench Verified single-task receipt overlay with no leaderboard claim.
3. CodeClash comparative edit: deterministic control versus one provider-backed Mini-SWE-Agent
   attempt on the same small target.

## Bars

The gate passes only if the selected pilot freezes all of the following before any paid execution:

- exact provider and model identifier, verified against current provider documentation or CLI output;
- max API calls, wall-clock budget, and dollar ceiling;
- exact public task target, upstream commit, and local config path;
- secret handling and log-redaction rule;
- raw artifact retention plan;
- receipt fields and audit script checks;
- falsifiers and stop criteria;
- claim boundary excluding leaderboard, SWE-bench, production, and live-domain claims unless those
  are separately verified by the frozen run.

## Falsifiers

Publish a null result if:

- no candidate can be frozen with an exact model and budget,
- provider credentials are unavailable or would leak into artifacts,
- the task cannot be run with bounded spend,
- the result would be hard to separate from a leaderboard or production claim,
- the candidate depends on infrastructure that cannot be audited from committed evidence.

## Scope Boundary

No provider call is authorized by this gate. No GPU run is authorized by this gate. The output is a
selected pilot specification, not model performance.
