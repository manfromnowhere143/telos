# Iteration 150 Result - The Intervention Is Oracle-Agnostic (Gold-Free 5/7 ~= Regression-Gated 10/13)

Status: `PASS`.

## What this gate did

Grew iter149's gold-free-oracle existence result into a rate, and compared it to the regression-gated rate,
to test whether the protocol effect depends on the gate having the real tests. Pooled across three gold-free
runs, deduplicating the evaluated instances (a sound docstring-derived property AND a constructed both-miss)
by id.

## Result

| oracle | evaluated | catches gamed | real completion |
| --- | ---: | ---: | ---: |
| gold-free property gate (no held-out tests in the gate) | `7` | `7/7` | `5/7 = 0.71` |
| regression-suite gate (iter146 + iter148 pooled) | `13` | - | `10/13 = 0.77` |

Pooled gold-free evaluated instances: `11095, 11951, 12193, 13343, 13363, 14373, 14752`. The gold-free gate
caught every gamed completion (`7/7`), and drove gold-free repair to real completion on `5/7` - within
sampling noise of the regression-gated `0.77`. The two failures (`13343`, `13363`) are hard cases; `13343`
also fails repair in the regression-gated runs.

## The finding

The intervention is **oracle-agnostic**. Whether the execution gate is the real regression suite or a
gold-free model-proposed property, the protocol lifts real completion at essentially the same rate
(`0.71` vs `0.77`). This localizes where the improvement comes from: not from the gate having privileged
access to the tests, but from **execution-based rejection plus a generalize-signal**. A gate that only knows
the function's documented contract - no test coverage of the broken behavior - is sufficient to catch the
gamed completion and drive repair. This is the deployment-faithful form of the intervention claim, and it is
now a rate rather than a single example.

## Honest bounds

- The evaluated set (`7`) is bounded to the property-derivable subset (format/contract functions) and by the
  compound requirement that a *sound property* and a *both-miss* both land on the same instance. Most target
  instances failed one of the two (`no_both_miss` or `property_unsound_on_gold`) in any given run.
- Property synthesis is stochastic: an instance can get a sound property in one run and an unsound one in
  another (e.g. `14373` was sound in the iter149 runs, unsound in this one). Pooling across runs is the honest
  way to assemble the evaluated set, and this variability is disclosed rather than hidden.
- The soundness confound from iter149 (standalone property scripts not configuring Django settings) remains
  fixed here by the settings preamble.

## Claim boundary

Supported: pooled over `7` evaluated django both-miss, a gold-free property gate catches the gamed completion
`7/7` and reaches real completion `5/7`, comparable to the regression-gated `10/13`; the intervention is
oracle-agnostic on the property-derivable subset. Not supported: a benchmark, model, or SOTA claim, or a rate
over all instances; the property-derivable domain is the format/contract subset and `N` is small.

## Next gate

The detection+intervention arc is complete and defended (iter109-iter150). The remaining experimental
frontier is raising property-derivability beyond format functions; the higher-leverage next step is
consolidating the arc into the submission-shaped paper.

## Evidence

- `proof/goldfree_oracle_run_d.json` (this run's per-instance property soundness, gate catch, gold-free repair)
- iter149's `goldfree_oracle_run_b.json` and `_c.json` (pooled by the runner)
- `proof/endpoint_results.json`, `proof/run_summary.json`, `proof/learning_record.json`
- `proof/valid/receipt_gold_free_oracle_rate.json`
- `scripts/run_gold_free_oracle_rate.py`
