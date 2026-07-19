# Iter236 result — the transfer analysis reproduces; two figures of record do not

Status: complete. Pre-registration: `HYPOTHESIS.md`, committed at `d6480e2` before this builder existed.

Builder: `scripts/build_iter236_transfer_analysis.py`
Artifact: `proof/transfer_analysis.json`
Cost: `$0`. No provider call, no container, no network.

## Headline

**The `$0` analysis that redirected the programme was scientifically correct, and is now regenerable.** Seven
of nine audited claims reproduce exactly. The two that do not are figures of record carried in the handoff
chain and in the paper, and both are corrected below.

| # | Claim of record | Rebuilt | Verdict |
| --- | --- | --- | --- |
| C1 | hacked median `4` added source lines vs `1` | `4.0` vs `1` | reproduces |
| C2 | one-sided `p=0.0027` | `0.0026736527` | reproduces |
| C3 | held-out median `5`, higher than hacked | `5` vs `4` | reproduces |
| C4 | `>=4` keeps `61%` of `447` | `61.30%` | reproduces |
| C5 | `added_per_f2p` selects `50%` | `49.89%` | reproduces |
| C6 | `added_per_graded` selects `41%` | `41.16%` | reproduces |
| C7 | `0` positives from **`59`** solved patches | `0` from **`62`** | **mismatch** |
| C8 | paper's two-sided `p=0.008` | `0.0053`; exact variant `0.0072` | **mismatch** |
| C9 | null cohorts eligible under iter202's stricter rule | `26/26` and `38/38` | holds |

## What this does not establish

A reproduced number shows the record is internally consistent. It establishes no model behaviour, detector
efficacy, cohort, throughput, rate, or population frequency, and it does not make the underlying science
stronger. The programme's headline figures are unchanged by this iteration.

## C1–C6 — the redirection was sound

The conclusion the handoff drew stands on committed evidence for the first time. Fix size separates the
hacked group *within* the `53`-target cohort (one-sided `p=0.0027`) and **does not transfer**: held-out
SWE-bench Verified has a *higher* median added-source-line count (`5`) than the hacked group (`4`), so a
`>=4` rule selects `61%` of `447` held-out instances and enriches nothing. The two mechanism-derived variants
are no better at `50%` and `41%`.

C5 and C6 are the strongest evidence that the reconstruction recovered the original construction rather than
coincidentally landing nearby. The threshold rule — *hacked-group median per selector* — was fixed in the
builder's docstring before any figure was computed, as falsifier F3 required, and was applied to all three
selectors without variation. It reproduced two independently recorded percentages to the stated precision.

**A successor may now rely on this negative and should not re-test fix size.** That instruction is backed by
an artifact with a `--check` guard.

## C7 — the null holds, the denominator does not

`docs/HANDOFF-2026-07-18-iter234.md:81` records the two fresh cohorts as yielding `0` positives from **`59`**
solved patches. Rebuilt from `proof/iter200_per_candidate.json` in both runs:

| run | solved patches | certified | confirmed |
| --- | --- | --- | --- |
| iter224 | `25` | `15` | `0` |
| iter228 | `37` | `22` | `0` |
| **total** | **`62`** | **`37`** | **`0`** |

The scientific content is untouched — both cohorts are null, and the null is the load-bearing part. The
denominator is wrong by three, and no committed artifact equals `59`.

The figure propagated to `docs/HANDOFF-2026-07-18-iter235.md:138,228` and into
`experiments/iter235_witness_recovery/HYPOTHESIS.md:29`, which is a **sealed pre-registration**. Per the
never-edit-sealed-evidence rule that file is not modified; the correction is additive and iter235's
`RESULT.md` carries a pointer to this one.

This is the pre-committed uncomfortable consequence from `HYPOTHESIS.md`, and it is recorded rather than
quietly dropped.

## C8 — a published statistic that does not regenerate

`paper/telos.tex:405` reports Mann-Whitney `p=0.008` two-sided on the same comparison. Under the committed
derivation the two-sided value is `0.0053`. Enumerating standard variants as forensics, not as a search for
agreement:

| variant | value |
| --- | --- |
| asymptotic, continuity correction | `0.005347` |
| asymptotic, no continuity correction | `0.005152` |
| exact | `0.007184` |

None equals `0.008`; the closest, the exact test, rounds to `0.007`. The medians the paper reports alongside
it (`4` against `1`) reproduce exactly, so the discrepancy is confined to the test statistic.

The paper's claim is directionally and inferentially unaffected — every variant is significant at the same
level and the sentence is already labelled "uncorrected and chosen after inspection." **The digit is
nonetheless not reproducible, and it sits in a submission-ready artifact.** It is reported here rather than
silently amended; `paper/telos.tex` is not edited in this iteration because a paper change cascades into a
PDF rebuild and a refresh of both SHAs in `validate_current_paper.py`, and paper submission is operator-only.

## C9 — a plausible confounder, refuted at $0

`build_iter202_solve_targets.py:82` requires a `build_solve_patch` round-trip that `build_iter228_cohort.py`
omits, and the two implementations of the contiguous-added-run test differ (exact equality with a reset
versus substring matching without one). Since the `53`-target cohort is enriched and the fresh cohorts are
null, a difference in how they were drawn was a candidate explanation for the programme's largest open
question.

It is not one. Applying iter202's stricter rule to the null cohorts:

- iter224: `26/26` eligible
- iter228: `38/38` eligible

Every target in both null cohorts would also have been eligible under the stricter rule. **The cohorts are
comparable on this axis and the enrichment question is untouched by it.** The difference is real in the code
and absent in the data.

This is published because a reviewer comparing the two builders would raise it, and the answer should exist
before they do. It was found by reading builder source rather than inspecting outcomes, which is why testing
it was instrument-validity selection and not outcome selection.

## F2 — what this iteration cannot verify

`docs/HANDOFF-2026-07-18-iter234.md:87` states that **six** predictors were tested and names **three**. The
other three are unrecorded anywhere in the repository. This iteration reproduces the three that are named and
**cannot verify the other three at all**.

Per falsifier F2 they are reported as an irrecoverable gap, not as reproduced. The sentence "treat all of it
as negative" therefore remains an **assertion** covering three unnamed predictors, and a successor cannot
check it or avoid re-testing them. The multiple-comparisons judgement it encodes — six predictors on `53` rows
with `10` positives is fishing — is sound reasoning regardless, but the specific family is not documented.

## The closure blind spot this exposes

`run_ci_closure.py` derives its `285` commands from `ci.yml`. An analysis that was never registered there is
invisible to it, so **a green closure was never evidence that every published number regenerates** — only that
every *registered* number does. The gap was not hypothetical: it hid an unregistered analysis that redirected
the programme's forward plan, and a misstated denominator that propagated into a sealed pre-registration.

This builder is registered in `ci.yml`, so the closure now covers it. That closes this instance and not the
class. Any figure asserted in a handoff or paper without a registered builder remains outside the closure.

## Correction propagation

| Document | Figure | Action |
| --- | --- | --- |
| `docs/HANDOFF-2026-07-18-iter234.md:81` | `59` solved patches | superseded by this RESULT; sealed handoff not edited |
| `docs/HANDOFF-2026-07-18-iter235.md:138,228` | `59` solved patches | superseded by this RESULT |
| `experiments/iter235_witness_recovery/HYPOTHESIS.md:29` | `59` solved patches | sealed pre-registration; pointer added to iter235 `RESULT.md` |
| `experiments/iter235_witness_recovery/RESULT.md` | — | pointer added |
| `paper/telos.tex:405` | `p=0.008` | reported unreproduced; correction deferred to an operator-authorized paper pass |
| `README.md` | — | iter236 indexed |
