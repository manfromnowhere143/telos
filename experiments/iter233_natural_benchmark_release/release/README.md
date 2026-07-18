# Natural certified-yet-wrong benchmark

A fixed set of `67` real model-generated patches for public SWE-bench Verified issues. Every one **passes the
official graded test suite**. Thirteen of them are nonetheless *wrong*, confirmed by executing a
gold-differential witness. Fifty-four are correct.

The question it poses: **can your detector tell them apart without seeing the accepted fix?**

## Layout

| Path | Contract |
| --- | --- |
| `inputs/` | Everything a gold-free detector may see: issue text, public `FAIL_TO_PASS` test names, candidate patch. |
| `answers/answers.json` | Labels, gold-differential witness observables, divergence types. Enough to score, and enough to cheat. |
| `reference_exercises/` | The 65 validated exercises from one execution-oracle design. A reference instrument, not part of the task. |
| `index.json` | Row index with candidate-patch digests. |

Row ids are opaque. The originating experiment run does not appear in `inputs/` — one of those run names
contains the string `certified_yet_wrong`, and an eval input should not hand a detector a provenance cue to
key on instead of the patch.

## How to use it

1. For each row in `inputs/`, decide: is this patch wrong? Emit `{"row_id": ..., "flagged": true|false}`.
2. Score with `scripts/score_iter233_release.py --decisions your_decisions.json`.

You get recall, false-positive rate, Wilson intervals, the missing-outcome triple, and the recall split by
divergence type — the same reporting contract this benchmark's own baselines are held to.

## Baselines

Measured on this exact set, all gold-free:

| Detector | Recall | False positives |
| --- | --- | --- |
| Static three-model panel | `2/13` | `5/54` |
| Execution oracle (defective instrument) | `4/13` | `10/54` |
| Execution oracle (validated instrument) | `2/13` | `12/54` |

The value-wrong subclass — ten of the thirteen positives — is caught **`0/10` by both**, with no missing
outcomes and a Wilson upper bound of `0.278`.

## Limitations. Read these before reporting any number.

**Small. `13` positives.** Any recall measured here carries a Wilson interval roughly `±0.2` wide. This
benchmark **cannot** separate two detectors whose true recall differs by less than that. It is not a
leaderboard and does not support ranking claims.

**There is a gold-lookup shortcut, and it is severe.** `29` of the `54` negatives are byte-identical to the
public SWE-bench gold patch, while `0` of the `13` positives are. A detector that retrieves the public gold
patch and flags "differs from gold" therefore scores `13/13` recall at `25/54` false positives without
understanding anything. That is not a detection result; it is the benchmark's construction leaking through an
external reference we cannot remove, because the instances are public.

If your detector consults gold, or any resource derived from it, **its number here is meaningless.** For a
harder read, score only against the `25` negatives that are *not* gold-identical; `answers.json` carries what
you need to select them.

**Some issues contain the fix.** In a few instances the reporter proposed the accepted change in the issue
text — `django-11951`'s issue writes out the one-liner. That text stays, because it is genuine
certification-time information a human reviewer would also see, but it makes those rows easier for reasons
unrelated to detector quality.

**Contamination.** The instances are public SWE-bench Verified rows and the candidate patches are committed in
a public repository. A model trained after this release may have seen them, including the labels. This
limitation is permanent and cannot be mitigated by anything in this artifact.

**Not a population sample.** These `67` rows come from six solver runs over one cohort, selected by which
patches certified and which produced a usable witness. The `13/67` proportion is not a natural rate of
anything.

## Provenance

Built from committed evidence by `scripts/build_iter233_release.py`; rebuilds byte-identically. Frozen
benchmark sha `10dc898c3cdc6026aaedc57d469e546b279a982df3772ba3388c1dfb515b8928`. Leakage and integrity are
machine-checked by `scripts/validate_iter233_release.py` against the built artifact, not asserted here.
