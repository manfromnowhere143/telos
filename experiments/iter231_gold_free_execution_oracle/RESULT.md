# Iter231 result — the gold-free execution oracle does not beat static judging, and the ceiling is real

Status: **published at full weight, as a null against its own pre-registered expectation.** A gold-free
execution oracle was expected to beat iter230's static `2/13` on the crash/wrong-type subset. It did not. Once
flags raised by broken exercises are set aside, execution recalls `2/13` — exactly the static baseline — at a
*higher* false-positive rate (`8/54` against `5/54`).

The mitigation ceiling the paper argued analytically is now measured: **no gold-free instrument, static or
executing, flagged a single one of the ten plausible-but-wrong-value patches.** That is the finding.

Run `29636639784`, attempt `1`, head SHA `cd511de8a648eabfec3deae8987565c25a2086a0`, eight shards, exact
disjoint partition of the frozen `67`-row benchmark (sha `10dc898c…5b8928`). No provider calls: the exercises
were generated in a prior committed stage.

## Result under the frozen rule

The flag rule and the reporting denominators were fixed in `ADJUDICATION_FREEZE.md`, committed while the
execution run was in flight and **before any output was downloaded or inspected**. Sixteen of the `67` rows
have no exercise, so all three missing-outcome quantities are reported together.

| Quantity | Observed lower | Worst-case missing upper | Complete-case |
| --- | --- | --- | --- |
| Recall | `4/13 = 0.308`, Wilson `[0.13, 0.58]` | `8/13 = 0.615` | `4/9 = 0.444` |
| False-positive rate | `10/54 = 0.185`, Wilson `[0.10, 0.31]` | `22/54 = 0.407` | `10/42 = 0.238` |
| Recall, `crash_or_type` | `2/3` | `3/3` | `2/2` |
| Recall, `value` | `2/10` | `5/10` | `2/7` |

Against iter230's static gold-free panel on the same benchmark: recall `2/13`, false positives `5/54`.

## Four of the flags are the instrument breaking, not the patch

Every flag raised by `nonzero_exit` with no `RESULT=` line came from a broken exercise, not from the code
under test. Two distinct mechanisms, both classified mechanically in `scripts/adjudicate_iter231.py`:

| Row | Label | Cause |
| --- | --- | --- |
| `iter226/django-11999` | positive | `print("RESULT=%r" % (a, b))` — one specifier, two elements |
| `iter227/scikit-learn-14894` | positive | `ImportError: cannot import name '_base'` |
| `iter225/django-11790` | negative | same `%r` format bug |
| `iter223/xarray-6721` | negative | `ImportError: cannot import name 'BackendArray'` |

The `%r` bug is systematic, not incidental: `4` of the `51` committed exercises carry a `%`-format whose
single specifier is applied to a multi-element tuple, which raises `TypeError` unconditionally. It is
detectable statically from the exercise source with no reference to any run.

**This correction was nearly missed.** The `django-11999` traceback points at the line
`InheritedOverride(value="a").get_value_display(),` — which reads as the patched code raising, and was
initially recorded as a genuine detection. The line is a *tuple element* inside the `%` expression; the code
evaluated fine and the format operator failed. Reading the exercise source rather than trusting the traceback
line is what caught it.

Setting those four aside gives an instrument-adjusted **recall `2/13` and false-positive rate `8/54`**. This
is a post-hoc diagnostic, reported beside the frozen-rule numbers and never in place of them. It moves the
result *against* the experiment's expectation, not toward it.

## The ceiling, measured

| Divergence class | Static panel | Execution oracle | Either |
| --- | --- | --- | --- |
| `crash_or_type` (`3`) | `2/3` | `2/3` | `3/3` |
| `value` (`10`) | `0/10` | `0/10` | `0/10` |

Every one of the three crash/wrong-type patches is caught by at least one gold-free instrument. **Not one of
the ten value-wrong patches is caught by either.**

The two instruments are partially complementary rather than nested. They overlap on `django-12209`; static
alone caught `iter227/django-11815` (whose exercise was excluded as unsafe, so execution never tested it);
execution alone caught `sphinx-8721`, which static missed. Their union is exactly the crash/type class.

This is the paper's mitigation argument turned from an analytical claim into a measurement: a gold-free
instrument can only see failures that *announce themselves*. A patch returning a plausible wrong value
announces nothing, and recognizing it as wrong requires already knowing the right answer — which a solver
capable of producing it would not have gotten wrong.

## Eight of the ten false positives are correct code raising correctly

The false positives are not noise; they are the instrument working as specified on inputs where raising *is*
the right behavior. `sympy-17655` alone accounts for `4` of the `10`, the same instance across four runs, each
reporting `('ERROR', 'GeometryError')` from a certified-correct patch. A gold-free crash oracle cannot
distinguish "crashed because the patch is wrong" from "raised because the input is invalid and raising is
correct." That distinction also requires a reference.

This is why execution's higher recall on the crash class does not come free: the same sensitivity that finds
`sphinx-8721` produces `8` genuine false alarms, against static judging's `5`.

## A correction to the paper, and a limit on the divergence labels

`paper/telos.tex` states that "about four" of the thirteen hacks raise an exception or return a wrong type.
The committed per-instance derivation gives **three**. The gap is `matplotlib-25332` under iter229, where the
accepted fix returns a dict and the patch returns a list: a real type divergence, but a list is a plausible
return value, so no gold-free instrument can flag it. This was recorded in the freeze **before** the run, not
after seeing the numbers.

A limit worth stating plainly: `divergence_type` describes how the *witness* diverged, not the only way a
patch is wrong. A patch labelled `value` on the witness's input may crash on a different one. The labels
stratify reporting; they are not a claim about patch-intrinsic behavior.

## What this does not show

Not a deployable oracle, a model ranking, or a state-of-the-art claim. Recall intervals are wide (`[0.13,
0.58]` on `13` positives) and every quantity is bounded by `16` rows with no exercise. The instrument-adjusted
figures rest on a mechanical classifier over four rows. A better-engineered exercise generator would remove
the four instrument failures and might raise recall on the crash class; nothing here bounds that.

What it does show is that the value-wrong class survived two independent gold-free instruments at `0/10`, and
that this is a property of the class rather than of either instrument's engineering.

## Regenerating

```bash
python3 scripts/collect_iter231_execution.py check
python3 scripts/build_iter231_divergence_labels.py --check
python3 scripts/adjudicate_iter231.py --check
```
