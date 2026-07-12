# Iteration 150 - Is the Intervention Oracle-Agnostic? (Gold-Free Rate)

Status: pre-registered design; executed to grow the gold-free-oracle evaluated set.

## Why this gate exists

iter149 showed the protocol effect survives a gold-free oracle on `3` evaluated instances - enough for an
existence result, not a rate. This gate grows the evaluated set by attacking more instances (including ones
already known to yield both-miss), pools across the gold-free runs, and asks whether the gold-free
real-completion rate matches the regression-gated rate from iter146/iter148. If it does, the intervention
is oracle-agnostic: the improvement comes from execution-based rejection plus a generalize-signal, not from
the gate having the real tests.

## Method

Same gold-free harness as iter149 (a model writes a docstring-derived property, validated sound on gold,
executed on random inputs, no held-out tests in the gate; then a both-miss is constructed and the property
gate plus repair is run; real completion is scored against the true held-out). Attack a wider instance set
and more both-miss retries. Pool the evaluated instances (a sound property AND a constructed both-miss) by
id across the two iter149 runs and this run - property synthesis is stochastic, so an instance may be sound
in one run and unsound in another, and pooling assembles the evaluated set honestly. Report the pooled
catch rate, gold-free real-completion rate, and the regression-gated reference.

## Endpoints

- pooled gold-free gate catch rate on the constructed both-miss completions.
- pooled gold-free real-completion rate, and its comparison to the regression-gated rate (`10/13`).

## Acceptance / interpretation rule

If the gold-free gate catches every evaluated gamed completion and its real-completion rate is comparable
(within sampling noise at this N) to the regression-gated rate, the intervention is oracle-agnostic. The
evaluated set remains bounded to the property-derivable subset.

## Falsifiers

1. An evaluated instance requires a sound gold-free property and a constructed both-miss; no held-out test enters the gate.
2. Real completion is scored against the true held-out tests, which never enter the gate.
3. The gold-free/regression comparison is a rate over evaluated instances, not a benchmark.

## Execution envelope

- native django execution + `gpt-5.6-terra`, no GPU; production mutation forbidden; benchmark/model/SOTA
  claim forbidden.

## Claim boundary (pre-committed)

At most: "pooled over `N` evaluated django both-miss, a gold-free property gate catches the gamed completion
`K/N` and reaches real completion `J/N`, comparable to the regression-gated rate, so the intervention is
oracle-agnostic on the property-derivable subset." Not a benchmark, model, or SOTA claim; small `N`.
