# Iter221 result — cross-platform guard tolerance

Status: PASS locally; remote publication gates pending. Publication-only. No iter219 number changes.

## Result

Iter220's exact seal `3cee092420c2d13227005c8d78e584ec69da832f` was published unchanged on draft PR `#14`.
Push CI run `29540341974` and pull-request CI run `29540356205` both failed on Python 3.11 and 3.12 at
`Iter219 temporal consequence-test yield guard`:

```text
iter219: delta=180: control Wilson interval does not recompute
```

The interval was correct. `scripts/validate_iter219_temporal_consequence_test_yield.py` compared stored
Wilson intervals to recomputed ones with bit-exact float equality, and `telos.tcp1.wilson_interval` calls
`sqrt`, whose last-place result depends on the platform `libm`. The report's intervals were computed on
macOS; Linux recomputes them to within one unit in the last place, and exact equality fails on a correct
value.

Iter220's branch and PR remain unchanged, were not rerun, and must not be merged.

## Why this surfaced only now

CI stops a job at its first failing step. Iter219's CI died at the detector guard and never reached this one.
Iter220 repaired the detector guard, CI advanced further, and the next latent defect reached daylight for the
first time.

This chain — iter219, iter220, iter221 — is not the publication churn that produced ten scientifically empty
iterations before it. Each link is a distinct real defect that only remote execution could expose, and each
was fixed at its class rather than its instance.

## Relationship to iter214

Iter214 canonicalized the two mathematically exact Wilson boundaries: `lower=0.0` at `k=0` and `upper=1.0` at
`k=n`. Interior Wilson values have no exact closed form to canonicalize and remain genuinely
platform-dependent. Iter214 could not have prevented this. It is the same bug class at the interior rather
than the boundary.

By contrast `telos.tcp1.exact_one_sided_mcnemar` sums `comb()` over exact integers and divides by `2**n`.
IEEE 754 division is exactly specified, so its p-value is bit-identical on every platform and keeps an exact
check.

## Why the derived closure did not catch it

Iter220 fixed the closure's **command set**; it did not fix the closure's **platform**. `run_ci_closure.py`
runs on macOS under Python 3.14 while CI runs Linux under 3.11 and 3.12. A macOS closure cannot certify a
Linux `libm`.

The response is not to acquire a Linux runner before every push. It is to make guards **platform-independent
by construction**, so no platform is the ground truth. A guard asserting bit-exact floating-point equality
across machines asserts something the standard does not promise.

## Corrections

`C1` — Wilson intervals compare at `rel_tol=1e-9`. One unit in the last place is about `1e-16` relative, so
the tolerance forgives platform noise by seven orders of magnitude, while the coarsest tampering that could
change a reported four-decimal figure is about `1e-4` relative and still fails. Integer counts, yields,
exposure totals, and the exact paired test keep exact comparison. A test asserts no `sqrt`-derived value is
compared bit-exactly anywhere in the guard, and a test reproduces the exact Linux failure by nudging an
interval one unit in the last place.

`C2` — `run_ci_closure.py` accepts `--python` so the closure can run under CI's interpreter versions, and
prints its interpreter and platform with an explicit note that a clean local run does not certify CI's Linux
runners.

## Bars

| Bar | Requirement | Observed | Verdict |
| --- | --- | --- | --- |
| 1 | Passes at one ULP drift; fails at `1e-9` relative tampering | both | pass |
| 2 | No libm-derived value compared bit-exactly | `0` offenders | pass |
| 3 | Closure reports interpreter and platform, accepts `--python` | verified | pass |
| 4 | Every CI guard passes locally at the seal | `259/259` | pass |
| 5 | Iter219 evidence and iter220 corrections byte-identical | verified | pass |
| 6 | PR `#13` and PR `#14` unchanged | unmutated, unrerun, unmerged | pass |
| 7 | No provider, GPU, container, dispatch, payment, release, or scientific claim | all zero | pass |

## Claim boundary

Iter221 contributes no scientific `N`, `k`, `u`, benchmark score, effect estimate, model comparison,
population estimate, or TCP-1 admission change. Iter219's null stands exactly as published: forward `0.4066`
against a backward within-repository control of `0.4336`, difference `-0.0270` at `p = 0.925`, with the
cross-repository control's `p = 3.48e-24` recorded as the false positive a pre-data amendment averted.

TCP-1 admission remains `2/11` with `9` blocked and `execution_authorized=false`. Iter212 remains unchanged
and inactive.

## Zero-action boundary

`0` provider or model requests, `0` GPU allocations, `0` scientific containers, `0` repository test
executions, `0` workflow dispatches or reruns, `0` payments, `0` releases, and `$0.00` spent.
