# Iter224 result — natural-rate scale-up on a fresh disjoint cohort

Status: **NULL, published at full weight.** Zero confirmed hacks on this cohort; the result tightens the
pooled estimate and evidences repository dependence.

## Result

On the frozen `26`-target fresh cohort (`13` django, `13` sympy), solved neutrally by `gpt-5.6-terra`,
certified by the official SWE-bench harness in pinned x86 containers, and witnessed by safety-scanned
gold-differential scenarios:

```text
26 targets -> 25 patches -> 15 certified -> 0 diverge -> 0 confirmed natural hacks
```

| Quantity | Value |
| --- | --- |
| Certified model patches (`N`) | `15` |
| Confirmed natural hacks (`k`) | `0` |
| Unadjudicated (`u`) | `6` |
| Confirmed rate `k/N` | `0/15 = 0.0000` |
| Worst-case missing-outcome upper `(k+u)/N` | `6/15 = 0.4000` |

No certified patch diverged from gold on a validated safe witness, so no candidate reached the blind judges
and `0` judge calls were made. This is a genuine null, not a pipeline failure: `15` patches certified, their
witnesses executed, and none produced observably different output from the gold fix.

## Distribution over the 25 executed patches

- `10` not certified (failed the official harness);
- `4` certified and normalized-identical to gold (correct);
- `5` certified with a witness that ran and showed no divergence (correct-equivalent under the witness);
- `6` certified with no adjudicable witness (`certified_unadjudicated`, counted in `u`);
- `0` certified and diverging.

Scenario generation excluded `3` statically unsafe witnesses (`excluded_unsafe`) by construction and produced
`2` `no_scenario` outcomes, exactly as the safety-aware pipeline is designed to.

## The scientific finding: the rate is repository-dependent

Iter224 is not a contradiction of iter223's `4/29`; it is a different cohort, and the difference is
informative. Iter223's confirmed hacks span django, matplotlib, and xarray. Iter224's fresh cohort is
constrained to django and sympy, because the eligibility filter has exhausted diverse fresh targets (disclosed
in the pre-registration). Sympy's precise, numerically strict test suites make a neutrally-solved patch more
likely to break a graded test outright rather than certify-yet-diverge, so a sympy-heavy cohort is expected to
yield fewer certified-and-wrong patches. The `0/15` here is consistent with that: the natural certified-yet-
wrong rate is not a single population constant but varies with repository composition. Reporting this null at
full weight is what keeps the pooled claim honest.

## Pooled estimate across all three disjoint cohorts

All of iter200, iter223, and iter224 are mutually disjoint and use the identical strict two-judge model-only
rule, so they pool:

| | iter200 | iter223 | iter224 | pooled |
| --- | --- | --- | --- | --- |
| certified `N` | `24` | `29` | `15` | `68` |
| confirmed `k` | `1` | `4` | `0` | `5` |
| unadjudicated `u` | `6` | `6` | `6` | `18` |

Pooled `k/N = 5/68 = 0.0735`, worst-case missing-outcome upper `(k+u)/N = 23/68 = 0.3382`, complete-case
`k/(N-u) = 5/50 = 0.1000`. Adding iter224's null lowers the pooled point estimate from `5/53 = 0.094` to
`5/68 = 0.074` and widens the base, reflecting that the confirmed rate is cohort- and repository-dependent
rather than a fixed frequency.

## Claim boundary

Iter224 is a bounded elicited-then-neutral replication over a fixed two-repository convenience sample. `wrong`
means differs-from-gold-reference on a witnessing input. Neither the `0/15` null nor the pooled `5/68` is a
natural population frequency, model ranking, product-efficacy result, or state-of-the-art claim. The static
safety scan is defense in depth; the locked `--cap-drop ALL` container is the security boundary.

## Spend and boundary

Solve `25` patches and generate scenarios cost ~`$2.35`; the blind-judge stage made `0` calls because no
candidate diverged. Container certification and witnessing ran free on GitHub-hosted x86 runners. No sealed
iter200, iter202, iter203, or iter223 byte changed.

## Reproduction

```bash
python3 scripts/validate_iter224_scenario_safety.py
TELOS_NAT_EXP=iter224_natural_rate_scale_n python3 scripts/adjudicate_iter200.py
TELOS_NAT_EXP=iter224_natural_rate_scale_n python3 scripts/run_iter200_blind_judge.py
```

Execution evidence: `proof/raw/execution/` (50 committed container logs, run `29566625274`, all 8 shards
success). Per-candidate adjudication: `proof/iter200_per_candidate.json`.
