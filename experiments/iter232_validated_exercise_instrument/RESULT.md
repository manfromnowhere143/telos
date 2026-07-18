# Iter232 result — with a working instrument, the execution oracle recalls exactly what static judging does

Status: **published at full weight.** Repairing the instrument did not rescue the execution oracle. It
recalls `2/13`, identical to iter230's static panel, at `12/54` false positives against static's `5/54`.
Iter231's raw `4/13` was instrument artifact, and its instrument-adjusted estimate of `2/13` is confirmed
exactly.

The ceiling is now airtight. The ten plausible-but-wrong-value patches are flagged **`0/10` with zero missing
outcomes**, Wilson upper bound `0.278`. Iter231 could only report `2/10` with `3` missing and an explanation;
iter232 reports `0/10` with complete data.

Run `29638614496`, attempt `1`, head SHA `40d0c64db206cb200234265e50b9ab236cf3a6a5`, eight shards, exact
disjoint partition of the frozen `67`-row benchmark. Flag rule imported byte-identically from iter231's
`ADJUDICATION_FREEZE.md` (sha `f1103f3f…53d8dd`), which is unchanged.

## Result

| Quantity | Observed | Worst-case upper | Complete-case | Missing |
| --- | --- | --- | --- | --- |
| Recall | `2/13 = 0.154`, Wilson `[0.04, 0.42]` | `2/13` | `2/13` | **`0`** |
| False positives | `12/54 = 0.222`, Wilson `[0.13, 0.35]` | `14/54` | `12/52` | `2` |
| Recall, `crash_or_type` | `2/3` | `2/3` | `2/3` | `0` |
| Recall, `value` | **`0/10`**, Wilson `[0.000, 0.278]` | `0/10` | `0/10` | **`0`** |

Every flagged positive was flagged by `error_observable`; not one by a crashed exercise.

| Instrument | Recall | False positives |
| --- | --- | --- |
| iter230 static panel | `2/13` | `5/54` |
| iter231 oracle (defective instrument) | `4/13` | `10/54` |
| **iter232 oracle (validated instrument)** | **`2/13`** | **`12/54`** |

Coverage rose from `51/67` (six defective) to `65/67`, and missing positive outcomes fell from `4` to `0`.
The false-positive rate rose with coverage: newly-covered rows contributed new false alarms, not new
detections.

## What the repair proved

Iter231 reported `4/13` and argued that two of those flags were the instrument breaking. That argument is now
tested rather than asserted: with the format bugs fixed and the import failures regenerated, the two disputed
flags disappear and recall lands on exactly the predicted `2/13`. The post-hoc correction was right, and the
experiment that could have embarrassed it instead confirmed it.

The direction matters. A repaired instrument moved the headline number **down**, and the pre-registered
expectation that execution would beat static judging is now falsified twice, the second time with no excuse
available.

## CORRECTION — the stage B gate was defective and is withdrawn

Stage B — executing an exercise's imports in isolation inside its container — rejected `6` rows. **Five of
those six rejections were wrong**: the full exercise ran and reported an observable. The failures were
`ImproperlyConfigured: Requested setting INSTALLED_APPS`, Django refusing to import app modules before
`settings.configure()` runs. The exercises call it in their prologue; the probe strips everything but the
imports and so removes the very setup those imports depend on.

The premise "imports can be executed in isolation" is false for any configuration-dependent framework. The
probe is therefore **withdrawn as a classifier**. Its output is retained in the committed logs and reported as
`stage_b_deprecated_probe` so the defect stays visible and auditable, but nothing gates on it.

### What replaced it

A row is an instrument failure iff it **exited non-zero having printed no `RESULT=` line**. Every exercise is
instructed to wrap its whole run in try/except and always report, so one that printed nothing died before it
could — at import or definition time, or in a broken handler. That is an instrument defect by construction,
whatever the exception type, and unlike the probe it cannot false-alarm on an exercise that actually worked.

It also catches what the probe's narrower import test missed. `django-11066` died on `ImproperlyConfigured`
while defining a model without configuring settings — a real instrument defect that is not an import error at
all, and the only genuine one in the run.

Residual ambiguity, stated rather than hidden: a patch that hard-crashes the interpreter, or that breaks
module import for an exercise whose imports sit outside its try block, would also report nothing and be
counted as instrument failure. Timeouts are unaffected; the executor emits an explicit
`RESULT=('TIMEOUT', ...)`.

### The corrected secondary figure

| Figure | Previously published | Corrected |
| --- | --- | --- |
| Instrument-valid-only recall | `2/13` | `2/13` (unchanged) |
| Instrument-valid-only false positives | `10/54` | **`11/54`** |

The headline frozen-rule numbers are untouched: recall `2/13`, false positives `12/54`. The correction makes
the oracle look slightly *worse*, and it arrived by auditing my own gate rather than the hypothesis.

**This did not corrupt the measurement.** Stage A gated which exercises were committed; stage B only ran
alongside. But had stage B been used as the commit gate as originally designed, it would have discarded five
working instruments and the result would have rested on a quietly smaller denominator.

## A pre-registered sub-prediction that failed

Expectation 3 named `iter227/django-11815`: `crash_or_type` by its witness, `excluded_unsafe` in iter231, and
therefore never tested by execution. If recovered and flagged, `crash_or_type` recall would reach `3/3`.

It was recovered. It was **not** flagged. Its new exercise ran cleanly and returned a value,
`(("__main__.Status['GOOD']", ('import __main__',)), …)`, not an error.

This is the witness-specificity limit stated in iter231, now with a second instance: `divergence_type`
describes how the *witness* diverged, not a patch-intrinsic property. A patch whose witness crashed can
return a well-formed value on a different issue-plausible input, and then no gold-free instrument can flag it.
The `crash_or_type` class is not reliably crash-reachable; it is only crash-reachable *on the witness's
input*, which a gold-free instrument does not have.

That makes the ceiling argument stronger, not weaker: even the class execution was supposed to own is only
partially reachable without a reference.

## Coverage held at 65/67 by choice

`psf/requests-5414` and `psf/requests-6028` have no exercise after three attempts each. Both require importing
`requests`, an HTTP client on the safety instrument's forbidden list. Admitting it would admit network
capability, which the pre-registration names as a falsifier, so the rows stay uncovered and appear in the
false-positive denominator as `2` missing outcomes. The container already runs `--network none`; holding a
defense-in-depth line when it is cheap is the point of having one.

The single allowlist extension was `astropy`, a pure computational package and a peer of the already-allowed
`numpy`, `sympy`, `sklearn`, `xarray`, `matplotlib`, applied in iter232's own validator so iter223–iter229
keep validating their evidence against the exact instrument that produced it.

## What this does not show

Not a deployable oracle, a ranking, or a state-of-the-art claim. `13` positives keep the recall interval wide
(`[0.04, 0.42]`) even with complete data. The `0/10` value-class result has a Wilson upper bound of `0.278`,
so it bounds the class rather than proving impossibility. A different exercise generator, or exercises given
more than one input per patch, could reach further; nothing here bounds that.

What it does show is that the value-wrong class survived two independent gold-free instruments at `0/10` with
no missing data, and that the crash-reachable class is smaller than its label suggests.

## Regenerating

```bash
python3 scripts/validate_iter232_exercise_validity.py
python3 scripts/collect_iter232_execution.py check
python3 scripts/adjudicate_iter232.py --check
```
