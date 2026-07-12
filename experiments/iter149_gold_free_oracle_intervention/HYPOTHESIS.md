# Iteration 149 - Does the Protocol Effect Survive a Gold-Free Oracle?

Status: pre-registered design; executed as a deployment-faithful self-attack.

## Why this gate exists

The sharpest attack on iter146-iter148 is that the completion gate used the real held-out `PASS_TO_PASS`
tests as its execution oracle. That is a realistic regression suite - existing tests a real PR runs
against - not a hidden answer key, but it still means the gate leaned on test coverage of the broken
behavior. The genuinely dangerous both-miss (iter139) is the thin-coverage one where no existing test
covers the break, and there the gate must be the gold-free property layer. This gate turns our own gun on
the intervention: replace the regression oracle with a gold-free, model-proposed property and ask whether
the protocol effect survives.

## Method

For django both-miss instances with a docstring-checkable contract: a model writes a self-contained
property-check script from the function's docstring/signature and the visible test only - never the
held-out tests - that exercises the documented contract on many inputs and reports pass/fail. The property
is validated **sound** by requiring it to pass on the correct (gold) code. Then a both-miss (gamed)
completion is constructed. The **gold-free gate** runs the property on the gamed completion: if it fails,
the completion is rejected and the agent is given a generic generalize-signal to repair, and the property
re-checks. Real completion is scored against the true held-out tests, which never enter the gate. An
instance is *evaluated* only when both a sound property and a both-miss are obtained.

## Endpoints

- gold-free gate catch rate on the constructed both-miss completions.
- gold-free real-completion rate (repair driven by the property gate, scored against true held-out).
- property soundness rate over the targeted functions.

## Acceptance / interpretation rule

If the gold-free property gate catches the gamed completions and drives at least one repair to real
completion, the intervention survives a gold-free oracle and the "you used the real tests" objection is
answered on the property-derivable subset. The evaluated N is expected to be small because it requires a
sound property and a both-miss on the same instance.

## Falsifiers

1. The gate must use only a docstring-derived property executed on inputs; no held-out/`PASS_TO_PASS` test enters the gate.
2. A property must be validated sound (pass on gold) before it gates a completion.
3. Real completion is scored against the true held-out tests, which never enter the gate.

## Execution envelope

- native django execution + `gpt-5.6-terra` (property author, gaming agent, repairing agent), no GPU;
  production mutation forbidden; benchmark/model/SOTA claim forbidden. Model-written property scripts are
  executed in a scratchpad checkout with Django settings configured by the harness.

## Claim boundary (pre-committed)

At most: "on `N` evaluated django both-miss completions, a gold-free property gate (no held-out tests)
catches the gamed completion `K/N` and drives gold-free repair to real completion `J/N`; the intervention
survives a gold-free oracle on the property-derivable subset." Not a benchmark, model, or SOTA claim; small
`N`, format-function subset.
