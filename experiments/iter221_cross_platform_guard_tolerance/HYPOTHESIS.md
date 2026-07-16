# Iter221 — cross-platform guard tolerance

Status: corrective publication-engineering gate recorded after exact iter220 push and pull-request CI both
failed on one guard's bit-exact float comparison. This gate authorizes no scientific execution and changes no
iter219 number.

Predecessor seal: `3cee092420c2d13227005c8d78e584ec69da832f`.

## Timing and scope

Iter219's null is unchanged. Iter220's corrections are unchanged and retained. This gate repairs one
verification defect only. Iter219's branch and PR `#13`, and iter220's branch and PR `#14`, remain fixed at
their tips; none may be amended, force-pushed, extended, rerun, or merged.

## Observed remote failure

- push CI run `29540341974` and pull-request CI run `29540356205`: Python 3.11 and 3.12 both failed at
  `Iter219 temporal consequence-test yield guard`;
- exact message: `iter219: delta=180: control Wilson interval does not recompute`;
- every earlier step passed, including the detector guard that iter220 repaired.

The machine record is `proof/ci_failure.json`.

## Why this surfaced only now

CI stops a job at its first failing step. Iter219's CI died at the detector guard and never reached the
iter219 guard. Iter220 repaired the detector guard, CI advanced further, and exposed the next latent defect.
Each recovery is not churn: it is a new, real defect reaching daylight for the first time.

## The defect

`scripts/validate_iter219_temporal_consequence_test_yield.py` compares stored Wilson intervals to recomputed
ones with bit-exact equality. `telos.tcp1.wilson_interval` uses `sqrt`, whose last-place result depends on the
platform `libm`. The committed report's intervals were computed on macOS; Linux recomputes them to within one
unit in the last place and the exact comparison fails.

Iter214 canonicalized the two mathematically exact Wilson boundaries (`k=0` lower, `k=n` upper). Interior
Wilson values have no exact closed form to canonicalize, so they remain genuinely platform-dependent. This is
the same bug class, at the interior rather than the boundary, and iter214 could not have prevented it.

`telos.tcp1.exact_one_sided_mcnemar` is unaffected: it computes `comb()` sums over exact integers and divides
by `2**n`, and IEEE 754 division is exactly specified, so its p-value is bit-identical across platforms.

## Why the derived closure did not catch it

Iter220 fixed the closure's **command set** — it now runs every command CI declares. It did not fix the
closure's **platform**. `run_ci_closure.py` runs on macOS under Python 3.14; CI runs on Linux under Python
3.11 and 3.12. A macOS closure can never certify a Linux `libm`.

The correct response is not to acquire a Linux runner before every push. It is to make guards
**platform-independent by construction**, so that no platform can be the ground truth. A guard that asserts
bit-exact floating-point equality across machines is asserting something the standard does not promise.

## Corrections

`C1` — replace bit-exact interval comparison with a bounded tolerance. The guard asserts each stored interval
equals the recomputed interval to `rel_tol=1e-9`. One unit in the last place is about `1e-16` relative, so the
tolerance forgives platform noise by seven orders of magnitude while any meaningful tampering — the smallest
being a shifted final displayed digit — is at least `1e-9` relative and still fails. Integer counts, yields,
exposure totals, and the exact paired test keep exact comparison, because each is exactly reproducible.

`C2` — `run_ci_closure.py` accepts `--python` so the closure can run under CI's exact interpreter versions,
and its report states the interpreter and platform used, so a clean local run can never again be mistaken for
a certified one.

Neither correction touches an iter219 number, bar, amendment, control, or claim.

## Acceptance bars

1. The iter219 guard passes when a stored interval differs from the recomputed interval by one unit in the
   last place, and still fails when an interval is tampered with at `1e-9` relative or coarser.
2. No guard in this repository asserts bit-exact equality on a value derived from `sqrt` or another
   libm-dependent function.
3. `run_ci_closure.py` reports its interpreter version and platform, and accepts `--python`.
4. Every guard CI declares passes locally at the iter221 seal.
5. Iter219's four evidence files and iter220's corrections remain byte-identical to their seals.
6. Iter219 PR `#13` and iter220 PR `#14` remain unchanged as failed-publication evidence.
7. No provider request, model call, GPU allocation, container, repository test execution, workflow dispatch
   or rerun, payment, release, or scientific claim occurs.

## Falsifiers

- Any iter219 or iter220 experiment byte changes.
- Any iter219 yield, control, interval, paired test, bar verdict, or claim boundary changes.
- The tolerance is loose enough to admit a tampered interval at `1e-9` relative.
- A libm-dependent value is compared bit-exactly anywhere in the guard set.
- The failed iter219 or iter220 branch or pull request is mutated, extended, or rerun.
- Fresh push or pull-request CI fails at the unchanged iter221 tip.
- Any scientific, provider, accelerator, dispatch, payment, deployment, or release action occurs.

## Claim boundary

Iter221 contributes no scientific `N`, `k`, `u`, benchmark score, effect estimate, model comparison,
population estimate, or TCP-1 admission change. Iter219's null stands exactly as published. TCP-1 admission
remains `2/11` with `9` blocked and `execution_authorized=false`. Iter212 remains unchanged and inactive.

## Publication boundary

Create one receipt-bound source commit directly above the iter220 seal and one handoff-only seal. Publish the
fresh branch once, open one draft pull request against `master`, then close PR `#14` as superseded without
deleting or modifying its branch. Merge once with a two-parent merge commit only after exact-tip push and
pull-request CI pass on Python 3.11 and 3.12, the secret scan is non-blocking, and no substantive review
blocker remains. Publication authorizes no release or science.
