# Iter235 result — recovering measurements that were already paid for

Status: **published at full weight.** All three pre-registered expectations held. The headline is not the
four new positives; it is that the missing-outcome term `u` fell from `41` to `8`, collapsing the
uncertainty band on the natural certified-yet-wrong rate across six published experiments.

Witness run: provider regeneration bounded at three attempts per row. Execution: run `29650269586`, eight
shards, green on first dispatch. Adjudication: the frozen two-judge protocol, imported unchanged.

> **Additive correction from iter236.** This experiment's `HYPOTHESIS.md:29` motivates itself in part with
> "fresh cohorts yielded `0` from `59` solved patches." Rebuilt from committed artifacts by
> [iter236](../iter236_transfer_analysis_reconstruction/RESULT.md), the correct denominator is **`62`**
> (iter224 `25` + iter228 `37`); no committed artifact equals `59`. The null itself is unaffected — both
> cohorts confirmed `0`. The sealed pre-registration is deliberately **not** edited; this pointer is the
> correction. Iter236 also reproduced the `p=0.0027` fix-size non-transfer result that iter235 cites, so
> that part of the motivation now rests on a guarded artifact.

## Result

| Quantity | Before | After |
| --- | --- | --- |
| Confirmed positives `k` | `13` | **`17`** |
| Unadjudicated `u` | `41` | **`8`** |
| Certified denominator `N` | `125` | `125` |
| Pooled observed `k/N` | `13/125 = 0.104` | `17/125 = 0.136` |
| Pooled worst-case upper `(k+u)/N` | `54/125 = 0.432` | **`25/125 = 0.200`** |
| Pooled complete-case `k/(N-u)` | `13/84 = 0.155` | `17/117 = 0.145` |

Per run:

| run | `N` | `k` before → after | `u` before → after | upper before → after |
| --- | --- | --- | --- | --- |
| iter200 | 24 | 1 → 2 | 5 → 1 | `6/24` → `3/24` |
| iter223 | 29 | 4 → 5 | 5 → 0 | `9/29` → `5/29` |
| iter225 | 25 | 1 → 2 | 7 → 2 | `8/25` → `4/25` |
| iter226 | 17 | 3 → 3 | 8 → 2 | `11/17` → `5/17` |
| iter227 | 14 | 3 → 4 | 6 → 2 | `9/14` → `6/14` |
| iter229 | 16 | 1 → 1 | 10 → 1 | `11/16` → `2/16` |

The band between the observed rate and its worst case narrows from `[0.104, 0.432]` to `[0.136, 0.200]`.
That is the result. The point estimate barely moved; what moved is how much of the uncertainty was missing
data rather than sampling.

## All three pre-registered expectations held

1. **Recovery is partial**: `33/41`. A rate near `100%` would have been evidence the validity gate was too
   permissive, not that the loop was good.
2. **Confirmed rate at or below base**: `4/33 = 12%` among recovered rows, against `~13/84 = 15%` among
   already-adjudicable certified patches. Rows that resisted witnessing were indeed no richer than the rest.
3. **`u` shrinks more than `k` grows**: `u` fell by `33` while `k` rose by `4`. This was the falsifiable
   claim and it held decisively.

## The number that looks better than it is

Four new positives is a `31%` increase in `k`. It is worth much less than that sounds.

**Three of the four are `sphinx-8721` from three different runs** — the same SWE-bench instance with three
different candidate patches. Only `matplotlib-23476` is a genuinely new instance. Unique instances rise from
`11` to `12`.

So the correlation problem that makes a `13`-positive benchmark statistically weak is **not solved**. Every
downstream question that needs independent instances — the width of detector recall intervals, iter234's
underpowered independence measurement — is essentially where it was. Anyone citing `17` positives without
citing `12` unique instances is overstating this result.

## What the witness stage was actually doing wrong

The committed logs named the failure precisely: `AttributeError` (9 variant / 8 gold) and `TypeError` (6 / 7),
occurring **symmetrically across arms**. A witness that raises on the gold patch is provably broken, because
gold is the correct fix. These were never divergences the judge failed to see; they were scripts that could
not run.

The original prompt already required the witness to "run to completion under GOLD without raising". Nothing
enforced it. Iter232 gave the exercise generator a validity gate and a retry loop; the witness generator never
had one. Adding both, plus a paired preflight requiring a `RESULT=` on **both** arms, took `33` of `41` rows
from unadjudicable to adjudicable — and all `33` produced results on both arms, with no candidate-only,
gold-only, or silent rows.

## A bug that nearly became a published null

The first judge run returned **`0` confirmed of `11`**, a tidy negative result.

It was wrong. `order_ab` returns `(output_a, output_b, ordering_key)`, where the third value is a descriptive
string like `"A=model,B=gold"` rather than a slot letter. Verdicts (`"A"`/`"B"`) were compared against that
string, so confirmation was structurally impossible.

What exposed it was not a test. It was noticing that the judges were **agreeing with each other while nothing
confirmed** — a combination that cannot happen if the comparison is sound. The signature was checked instead
of the zero being written up.

This is the third artifact this session that looked publishable: iter231's `4/13`, iter234's `3/10`, and this
`0/11`. All three moved the number in the direction that would have been easier to report.

## Quality caveats, reported not buried

- **`2` of the `11` divergences had the witness erroring on the gold arm too.** A witness that fails on a
  correct implementation is suspect evidence even when it technically produced a result. Neither confirmed,
  and all four confirmed rows have a clean gold arm.
- **One judge response was unparseable** (`sklearn-14894`), counted as a nondecision. Under the frozen rule a
  nondecision never confirms.
- **`8` rows remain unrecovered**, and they are the safety boundary rather than retry exhaustion: every one
  was rejected for reaching for `os`, `pathlib`, `tempfile`, `pickle`, or an absolute path literal.
  `django-12143` and `matplotlib-25332` are six of the eight and failed identically on all three attempts.
  Widening the instrument to reach them is a registered falsifier, so they stay in `u`.

## Correction to published figures

The originals stay in their `RESULT.md` files. The corrected `k`, `u`, and upper bounds are the table above,
and each affected experiment carries a pointer to it. The frozen iter230 benchmark (`13` positives, `54`
negatives) is **not** altered: it is the fixed substrate for iter230–iter234, and changing it would silently
invalidate four published detector results. Whether to build a successor benchmark including these four rows
is a separate decision with its own pre-registration.

## What this does not show

No new cohort, no new detector, no population rate. The corrected rates remain cohort-specific lower bounds
from a nonrandom convenience sample, exactly as the originals were. A tighter band on a bad sample is still a
bad sample — what improved is that the band now reflects sampling rather than lost measurements.

## Regenerating

```bash
python3 scripts/build_iter235_targets.py --check
python3 scripts/validate_iter235_execution_safety.py
```
