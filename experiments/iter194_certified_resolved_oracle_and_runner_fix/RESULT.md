# Iteration 194 Result - Certified-Resolved Oracle and Runner Fix

Status: `null` on the `>= 5` accepted-row bar, with a definitive and more informative finding than the bar
anticipated. The runner fix fully succeeded; the uncurated-test oracle is structurally exhausted; and this
result transparently re-scopes the second half of the iter194 plan into a standalone gate (iter195). No
row is claimed as a reward hack.

Provider calls `0`, new cloud resources `0`, spend `$0.00` for this gate (it reuses the iter193
candidates; execution is CI Docker only).

## Half one succeeded: the runner fix closed the iter193 gap

iter193 could execute only `6/16` candidates because it used a bare `pytest` invocation that django (no
pytest in its testbed) and astropy (collection gap) do not support. iter194 replaced that with each
instance's official SWE-bench `eval_script` (extracted via `make_test_spec`, committed as static
artifacts), run inside the pinned container under gold and under the variant, and parsed with the
vendored official SWE-bench parsers (byte-identical to upstream, locked by tests).

Result of the fix, from CI run `29339072961` (`success`):

- candidates executed project-correct: **`16/16`** (up from `6/16`);
- gold applied cleanly and was fully green in every instance;
- certification is real: all `16` variants are certified-resolved — each passes every `FAIL_TO_PASS` and
  `PASS_TO_PASS` test, with the graded node-ids matched exactly by the official parser.

The iter193 runner-fitness gap is closed. This is verified, not asserted.

## Half two: the uncurated-test oracle is structurally exhausted

With execution working, the pre-registered uncurated-test oracle found `0` witnesses, and the reason is
structural, not a shortfall of effort. Per-instance, comparing gold and variant across the entire test
module the eval_script runs:

| repo | instances | graded tests | tests in module | uncurated available | variant≠gold (any test) |
| --- | ---: | ---: | ---: | ---: | ---: |
| django | 8 | 8–143 | equal to graded | mostly `0` | `0` |
| astropy | 2 | 7, 427 | +2, +3 | `2`, `3` | `0` |
| matplotlib | 6 | 47–863 | +1 to +168 | `1`–`168` | `0` |

Two facts, both airtight across all `16`:

1. **For django, SWE-bench's curated `PASS_TO_PASS` *is* the whole test module.** There are `0` uncurated
   tests to hold out: a certified variant has, by definition, already passed every test that exists in the
   module. No oracle built from the project's own tests can exist for these instances.
2. **Where uncurated tests do exist (matplotlib up to `168`, astropy `2`–`3`), the variant passes every one
   identically to gold.** Across all `16` instances and the `193` uncurated tests available in total, not a
   single test — graded or uncurated — distinguishes any certified variant from its gold fix.

So the certified variants are behaviorally identical to gold across every shipped test. This admits exactly
two explanations, and this gate cannot separate them:

- the adversary produced correct equivalents (the 1:1 line-substitution constraint plus "stay certified"
  forced semantic equivalence); or
- the variants are wrong, but only on behavior that **no shipped test exercises**.

## What this establishes

A clean, and for the mission a load-bearing, negative result about reference-free verification:

> On `16` certified-resolved candidates across `3` repositories, the project's entire shipped test suite —
> the `40`-to-`863`-test graded set plus all `193` additional uncurated tests in the same modules — cannot
> distinguish a certified variant from the gold fix.

Reference-free verification of a patch the reward already certifies therefore **cannot rely on the
project's own tests**. They are either fully inside the reward (django) or do not exercise the difference
(matplotlib/astropy). Witnessing wrongness requires probing behavior no shipped test covers: synthesized
inputs to the changed code, executed differentially against gold.

This is the iter139 coverage lesson at its logical end point, now proven on real certified patches: the
binding constraint is not the runner and not the judge — it is that the tests defining "resolved" are the
same tests any test-based oracle would use.

## Transparent re-scope (this changes the iter194 plan, and says so)

iter194 pre-registered two changes: (1) the runner fix, and (2) a synthesized-input gold-differential
fallback oracle. Change (1) is delivered and validated. Change (2) is **not built in this gate**, and that
is a deliberate, disclosed re-scope rather than a silent omission.

The execution data revealed that the synthesized-input oracle is not a "fallback" to the uncurated-test
oracle — it is the *only* mechanism that can work, because the uncurated oracle is structurally exhausted.
Building it well (identify the changed callable, synthesize valid inputs for framework-internal functions,
execute differentially in-container) is a substantial standalone effort with its own failure modes
(iter124: `2/7` full-auto, `4/7` validated). Folding it into this gate would rush it. It is therefore
promoted to its own pre-registered gate, `experiments/iter195_synthesized_input_differential_oracle/`,
with this result as its precise motivation.

The `>= 5` bar is reported honestly as `0`. No bar is relaxed and no candidate is re-labeled; what changed
is that the reason for `0` is now understood at the structural level, and the next instrument is named.

## What this does and does not support

Supported: the iter193 runner gap is closed (`16/16` executed, certification real); the project's shipped
tests cannot witness wrongness of any of the `16` certified variants; reference-free verification of
certified patches must synthesize probes beyond the shipped tests.

Not supported: any claim that the `16` variants are correct (they are `undetermined` — no witness either
way); any claim that certified-resolved-and-wrong patches cannot be constructed (the synthesized oracle has
not yet run); any natural-frequency, non-elicited, benchmark-size, detector, leaderboard, model-comparison,
state-of-the-art, broad robustness, production, or product-value claim.

## Evidence

- `proof/raw/specs/` — 16 official eval_scripts and spec.json (extracted via `make_test_spec`)
- `proof/raw/execution/` — 32 gold/variant execution logs from CI run `29339072961`
- `proof/iter194_per_candidate.json` — per-candidate certification and uncurated derivation
- `proof/accepted_rows.json` — the accepted set (empty)
- `proof/audit_report.json` — bars, outcome distribution, null reason
- `proof/valid/receipt_certified_resolved_oracle_and_runner_fix.json`

Regenerate the adjudication from committed logs with:

```bash
python3 scripts/adjudicate_iter194.py
```

## Claim Boundary

Supported: the runner fix executed all `16` candidates project-correctly and confirmed all `16` are
certified-resolved; no shipped test (graded or uncurated, `193` uncurated available) distinguishes any
certified variant from gold; the wrongness oracle for certified patches must therefore synthesize probes
beyond the shipped tests (pre-registered as iter195). Not supported: any of the excluded claims above.
