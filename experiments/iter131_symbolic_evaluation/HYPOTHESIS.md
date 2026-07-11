# Iteration 131 - Symbolic Property Evaluation and Docker-Harness Scoping

Status: pre-registered before execution. Frozen before the symbolic evaluation was run.

## Why this gate exists

Iter130 left two levers. First, numeric property checking produced a float-precision false positive on
an exact identity; symbolic evaluation should remove it and be stronger. Second, environment fidelity
blocks the pre-3.10 clean-function instances; the Docker harness is the path to full coverage. This
gate executes the first and scopes the second.

## Method

- Symbolic evaluation: for each of the four iter130 hyperbolic identities, evaluate the property with a
  free `Symbol` via exact simplification (`simplify(expr) == 0`) rather than numeric sampling, and
  count how many are sound.
- Docker-harness scoping: record concretely what the official SWE-bench Docker harness provides
  (pinned per-instance Python and dependencies) and which measured failures it resolves.

## Endpoints

- `symbolic_sound`: how many of the four identities are exact-zero under symbolic evaluation.
- `numeric_to_symbolic_gain`: the change from the iter130 numeric result.
- the Docker-harness scope: the failure classes it removes.

## Acceptance / interpretation rule

If symbolic evaluation makes all four identities sound (removing the numeric artifact) and is a
universally-quantified check rather than a sampled one, symbolic evaluation is adopted for property
checking. The Docker-harness scope is recorded as the next-phase infrastructure, not built here.

## Falsifiers

1. If a symbolic evaluation does not reduce to zero for a true identity, the check is wrong; record it.
2. The Docker-harness scope is a design record; it must not claim the harness is built.

## Execution envelope

- native symbolic execution on modern sympy, no provider calls, no GPU, no cloud,
- production/live-domain mutation: forbidden, benchmark/model/SOTA claim: forbidden.

## Claim boundary (pre-committed)

At most: "symbolic evaluation makes `4/4` identities exactly sound, removing the numeric artifact and
proving each for all x; the Docker harness is scoped as the path to running the environment-fidelity-
blocked instances." Not a benchmark, model, or SOTA claim, and not a claim that the Docker harness is
built.
