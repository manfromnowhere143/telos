# Iteration 06 - Deterministic Edit Slice

Status: pre-registered, result pending.

## Purpose

Select the first zero-provider-spend slice that produces a real non-empty code diff through an
agent path. `iter05` proved trajectory and agent-stat capture for deterministic submit. The next
gate must add edit evidence before any provider-model run.

Paid provider models are authorized by the operator only if a later frozen gate names the model,
cost ceiling, task, and expected evidence before execution.

## Bars

The selected slice must satisfy all of these:

- It runs without provider credentials.
- It produces a non-empty diff inside the allowed task workspace.
- It records the agent trajectory or equivalent command trace.
- It records agent stats with zero provider cost.
- It has deterministic replay or a frozen output script.
- It can emit a Telos receipt with artifact, diff-scope, test, review, and live-check evidence.
- It does not claim provider-model capability, leaderboard performance, SWE-bench performance, or
  production/live-domain verification.

## Candidate Families

Score at least these candidates before selecting:

- public CodeClash deterministic edit path,
- minimal local deterministic edit harness around a public task fixture,
- public CodeClash BattleSnake config with a deterministic scripted edit agent.

## Falsifiers

Publish a null if no candidate can produce non-empty edit evidence without either provider spend or
private task machinery.

## Scope Boundary

No provider model call is authorized by this gate. No GPU run is authorized. No production or
live-domain change is authorized.
