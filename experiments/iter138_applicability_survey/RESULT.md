# Iteration 138 Result - Dataset-Wide Applicability Survey of the Property Layer

Status: `PASS`.

## What this gate did

Measured how broadly the property-based third layer can apply, across the whole `SWE-bench_Verified`
dataset, rather than adding one more property instance. For all 500 instances it applies the iter129
structural criterion - a single source file edited and a narrow `FAIL_TO_PASS` (at most three tests) -
and reports the applicability rate overall and per repo.

## Result

- overall structural applicability: `405/500` = `0.81`

| repo | applicable / total | rate |
| --- | ---: | ---: |
| scikit-learn/scikit-learn | 30/32 | `0.94` |
| sympy/sympy | 67/75 | `0.89` |
| matplotlib/matplotlib | 28/34 | `0.82` |
| astropy/astropy | 18/22 | `0.82` |
| sphinx-doc/sphinx | 36/44 | `0.82` |
| django/django | 186/231 | `0.81` |
| pytest-dev/pytest | 15/19 | `0.79` |
| pydata/xarray | 15/22 | `0.68` |
| psf/requests | 4/8 | `0.50` |
| mwaskom/seaborn | 1/2 | `0.50` |
| pylint-dev/pylint | 4/10 | `0.40` |
| pallets/flask | 1/1 | `1.00` |

## The finding

The single-testable-function criterion is met by four in five real SWE-bench Verified instances. The
property-based layer is not a niche - structurally it applies broadly, and to the majority of every
large repo in the dataset. The variation is meaningful and interpretable: math and modeling libraries
(scikit-learn, sympy) sit highest, while tooling libraries (pylint) and small samples (requests,
seaborn) sit lower, reflecting how concentrated their fixes are on a single function.

## The honest bound

This is an upper bound on the layer's reach, not the property genuine-sound rate. Structural
applicability is necessary but not sufficient: an applicable instance still needs a function with a
derivable gold-free property. That property-derivability is function-dependent - abundant in
mathematical libraries (iter130-iter137 showed clean identities for coth, Min, Point.distance) and
rarer in application libraries. So `0.81` bounds where Layer 3 could apply; the fraction that admits a
sound property within it is lower and is the next measurement.

## Claim boundary

Supported: the single-testable-function structural criterion is met by `405/500` = `0.81` of SWE-bench
Verified, with the per-repo breakdown recorded; this is an upper bound on the property layer's reach.
Not supported: a benchmark, model, or state-of-the-art claim, or a claim that `0.81` is the property
genuine-sound rate.

## Next gate

`iter139`: within the high-applicability repos, measure the fraction of applicable instances that admit
a derivable gold-free property, turning the upper bound into a property-derivability rate.

## Evidence

- `proof/applicability_survey.json` (frozen survey over all 500 instances)
- `proof/endpoint_results.json`, `proof/run_summary.json`, `proof/learning_record.json`
- `proof/valid/receipt_applicability_survey.json`
- `scripts/run_applicability_survey.py`
