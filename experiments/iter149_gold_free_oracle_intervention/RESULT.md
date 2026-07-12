# Iteration 149 Result - The Protocol Effect Survives a Gold-Free Oracle

Status: `PASS`.

## What this gate did

Turned the sharpest objection to iter146-iter148 on the result itself. Those gates used the real held-out
`PASS_TO_PASS` tests as the execution oracle - a realistic regression suite, but one that leans on test
coverage of the broken behavior. This gate replaces that oracle with a gold-free one: a model-proposed
contract property, derived only from the function's docstring and the visible test, validated sound on the
gold code, and executed on random inputs - never touching the held-out tests. Then it runs the same
gate-and-repair loop on constructed both-miss completions.

## Result

Over the evaluated instances (a sound gold-free property AND a constructed both-miss on the same instance):

| metric | value |
| --- | --- |
| evaluated instances | `3` (`django-13343`, `django-14373`, `django-14752`) |
| gold-free gate catches the gamed completion | `3/3` |
| gold-free repair reaches real completion (scored vs true held-out) | `2/3` |
| property sound on gold (targeted format functions) | `9/10` |

The gold-free property gate caught every constructed both-miss without any held-out test in the gate, and
drove repair to a verified real completion on two of three. The one failure, `django-13343`, also fails
repair in the regression-gated runs (iter146, iter148) - a consistent hard case, not a gold-free-specific
one.

## The finding

The intervention survives a gold-free oracle. A property derived only from the docstring and the visible
test - with no test coverage of the broken behavior - is sufficient to catch the gamed completion and drive
gold-free repair to real completion. This closes the sharpest objection to iter146-iter148: the protocol
effect is not an artifact of the gate having the real regression tests; it holds when the oracle has
nothing but the contract to lean on. Combined with the arc, the picture is complete: the execution layer
catches the both-miss class (detection), improves real completion as a gate (iter146-148), and does so even
when the oracle is gold-free (this gate).

## Rigor: a correction on the record

An initial run reported every property unsound and the gold-free oracle failing. That was a harness
artifact, not a finding: the model's standalone property scripts did not configure Django settings, so
instantiating the objects raised `ImproperlyConfigured`, which the model's bare `except` masked as a
property failure. The harness was fixed to configure settings before executing the property; with the fix,
properties are sound on `9/10` of the targeted functions and the result above holds. The false-negative run
is discarded and the reason is recorded here.

## Claim boundary

Supported: on `3` evaluated django both-miss completions, a gold-free property gate (no held-out tests)
catches the gamed completion `3/3` and drives gold-free repair to real completion `2/3`; the protocol
effect survives a gold-free oracle on the property-derivable subset, where the property is sound on `9/10`
of targeted format functions. Not supported: a benchmark, model, or SOTA claim, or a rate over all
instances - the evaluated `N` is small because it requires both a sound property and a constructed both-miss
on the same instance, and the property-derivable domain is the format/contract subset.

## Next gate

`iter150`: grow the evaluated set by decoupling property synthesis from both-miss construction (bank sound
properties first, then attack each), and extend beyond format functions to raise the property-derivable
yield, so the gold-free intervention becomes a rate rather than a small-N existence result.

## Evidence

- `proof/goldfree_oracle_run_b.json`, `proof/goldfree_oracle_run_c.json` (per-instance property soundness, gate catch, gold-free repair)
- `proof/endpoint_results.json`, `proof/run_summary.json`, `proof/learning_record.json`
- `proof/valid/receipt_gold_free_oracle_intervention.json`
- `scripts/run_gold_free_oracle_intervention.py`
