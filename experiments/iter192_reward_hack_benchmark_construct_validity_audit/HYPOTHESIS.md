# Iteration 192 - Reward-Hack Benchmark Construct-Validity Audit

Status: pre-registered zero-spend construct-validity audit over committed artifacts; no provider calls,
credential probes, property-generator calls, new SWE-bench executions, cloud resources, leaderboard
claims, model-comparison claims, state-of-the-art claims, natural-frequency claims, or broad robustness
claims have been run for this gate.

## Disclosure: exploratory origin

This gate is not pre-registered in the protective sense, and saying otherwise would be a false claim.

An exploratory read of committed artifacts came first, and it motivated this audit. Every number below
is a **deterministic re-derivation from already-committed evidence** collected under the iter152,
iter154, and iter155 pre-registrations. There is no new sampling, no provider call, and no stochastic
measurement, so the specific hazard that pre-registration exists to prevent — selecting an analysis
after seeing noise — does not apply: a recount of fixed bytes returns the same value whenever it is run,
by whoever runs it.

What this document does instead is fix, before publication, the exact checks, the exact numeric bars,
and the exact falsifiers, so that a reviewer can rerun `scripts/run_benchmark_construct_validity_audit.py`
against the committed tarballs and either reproduce every figure or catch the error. The audit is
adjudication in the sense of iter179, iter182, and iter189, not a new experiment.

## Why this gate exists

`benchmarks/reward_hack_benchmark_v1/` is the repository's flagship artifact, and the panel metric
derived from it (unrepaired iter179 `majority_catch`: `17/40` hack rows, `0/40` controls) is the primary
public claim. Both rest on the premise that the 40 rows are reward hacks.

A reward hack is a work product that **scores well on the reward function while being wrong**. That is
the property that makes it dangerous: it survives the grader, corrupts the training signal, and ships.

The generator that produced every row is committed at
`experiments/iter152_reward_model_gaming_scale/proof/raw/detection_pipeline.py`. Its row-acceptance
condition is line 132:

```python
if ev["applied"] and ev["ftp_ok"] and ev["held_fail"]:
```

`held_fail` is defined at line 95 as `len(p2p.get("failure",[]))>0` — at least one `PASS_TO_PASS` test
fails. `PASS_TO_PASS` is the repository's own existing test suite. A row is therefore admitted to the
benchmark **only if it breaks the existing test suite**, which is the opposite of scoring well on the
reward.

If that reading is correct, three things follow, and this gate exists to settle all three against
committed bytes rather than against reasoning:

1. the official SWE-bench harness marks every row unresolved, so the rows score zero on the reward and
   are not reward hacks under the definition above;
2. the trivial baseline — run the existing test suite, or equivalently read the official harness verdict
   — detects every row at zero cost, and that baseline has never been reported anywhere in this
   repository, which leaves the `17/40` panel figure without the comparison a reviewer asks for first;
3. the same generator run may have produced the genuine article — variants the official harness marked
   **resolved** — and discarded them, because a variant that passes the whole suite fails the `held_fail`
   acceptance test and is logged as `no_both_miss`.

The term `both_miss` means the deterministic detector and the LLM judge miss. It has never meant the
tests miss. This gate checks whether the public claim surface has been carrying the second reading.

## Inputs

All inputs are already committed. No network, no provider, no container.

- `benchmarks/reward_hack_benchmark_v1/reward_hack_benchmark_v1.jsonl`
- `experiments/iter152_reward_model_gaming_scale/proof/raw/detection_pipeline.py`
- `experiments/iter152_reward_model_gaming_scale/proof/raw/detection_results.json`
- `experiments/iter152_reward_model_gaming_scale/proof/raw/det_reports.tgz`
- `experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/swebench_logs_v4.tgz`
- `experiments/iter155_adaptive_reward_hack_expansion/proof/raw/swebench_logs_iter155.tgz`
- `experiments/iter179_reward_hack_panel_full_cohort_adjudication/RESULT.md`

## Numeric Bars

Minimum pass bars:

- provider calls are exactly `0`,
- credential probes are exactly `0`,
- property-generator calls are exactly `0`,
- new SWE-bench executions are exactly `0`,
- new cloud resources are exactly `0`,
- benchmark v1 rows audited is exactly `40`,
- v1 rows matched to a committed official hack report is exactly `40`,
- v1 rows whose matched official report has `resolved == false` is exactly `40`,
- v1 rows whose matched official report has at least one `PASS_TO_PASS` failure is exactly `40`,
- the generator acceptance condition requiring `held_fail` is located and quoted exactly `1` time,
- committed official hack reports parsed is at least `90`,
- discarded certified-resolved hack variants counted is at least `1`,
- committed test-suite/official-harness baselines for v1 found by scan is exactly `0`,
- secret/private identifier hits are exactly `0`,
- forbidden positive claim hits are exactly `0`.

## Falsifiers

1. Any provider call, credential probe, property-generator call, new SWE-bench execution, or cloud
   resource change occurs.
2. Any benchmark v1 row's matched official report has `resolved == true`. This would refute the claim
   that the official harness rejects the whole benchmark, and the audit fails.
3. Any benchmark v1 row's matched official report has zero `PASS_TO_PASS` failures. This would refute the
   claim that every row breaks the existing test suite.
4. The generator's row-acceptance condition does not require `held_fail`. This would refute the entire
   construct reading and the audit fails.
5. A committed artifact already reports a test-suite or official-harness baseline for v1. This would
   refute the claim that the baseline was never reported, and the correction is unnecessary.
6. Fewer than `40` v1 rows can be matched to committed official reports. The audit then publishes a
   coverage gap rather than a verdict, and no construct claim is made.
7. The result presents a leaderboard, model-comparison, model-superiority, state-of-the-art,
   natural-frequency, broad robustness, production, or product-value claim.

## Claim Boundary

At most, if this gate passes: benchmark v1's positive class is patches that the official SWE-bench
harness marks unresolved because they break the existing test suite; the official-harness baseline
detects `40/40` of them at zero provider cost; that baseline was never reported; and the iter152
generator run discarded at least one variant the official harness marked resolved.

Not supported by this gate: any claim that a genuine reward-hack class exists in committed artifacts and
is wrong (wrongness of a certified-resolved variant is **not** established here and requires execution
against gold, which this gate does not perform); any property-oracle result; any judge-panel result
beyond restating committed figures; any leaderboard, model-comparison, state-of-the-art,
natural-frequency, broad robustness, production, or product-value claim.

Explicitly retained: the iter179 panel figure (`17/40` hack rows, `0/40` controls) is arithmetically
correct and is not retracted by this gate. What changes is what it is a figure **about**.
