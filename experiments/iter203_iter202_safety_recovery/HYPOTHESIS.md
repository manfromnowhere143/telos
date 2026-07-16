# Iteration 203 - Safety-Recovery Certification of Fixed Iter202 Provider Outputs

Status: **ACTIVE, POST-PROVIDER / PRE-EXECUTION RECOVERY PROTOCOL**. Frozen before any official-harness
certification, scenario execution, behavioral comparison, adjudication, or blind-judge outcome from the
iter202 provider cohort. This is not a conventional prospective preregistration: all solver and scenario
provider responses already existed when this recovery was designed, and the frozen iter202 AST safety
guard had already reported its rejection diagnostics. No generated scenario has been executed and no
behavioral result has been inspected.

Date: 2026-07-16.

## Why a separately identified recovery is required

Iter202 provider execution ran under source commit
`8b8809ed6b358d16eb08fe38f0f2edf4a284af0e` and runtime-manifest SHA-256
`dd935a6f5873940fca5768891bb74a6cc635ef86bb65cdf493dd2a8ffe043868`. Its retained stage produced:

- `53/53` neutral solver calls, `50` model patches, `3` `empty_fix` outcomes, and approximately `$2.65`
  registered spend;
- `39/39` scenario calls for the differing patches, `38` extracted scenario programs, one original
  `no_scenario` outcome, and approximately `$1.95` registered spend;
- zero official-harness certification results, zero scenario executions, zero behavioral comparisons,
  and zero iter202 blind-judge outcomes.

Before any generated code ran, the committed iter202 safety validator deterministically returned `21`
findings across `9` distinct scenario programs. The other `29` extracted programs produced zero findings.
The original iter202 runtime fails closed at the batch level and its canonical summary and files must
exactly reconstruct from provider checkpoints. Reclassifying rows, removing files, changing the validator,
or changing the runtime manifest in place would invalidate that evidence chain. Iter202 is therefore a
**scenario-safety protocol/execution null**, not a solve-yield null and not a measured rate.

Iter203 is an additive recovery over fixed iter202 bytes. It may not mutate, relabel, repair, regenerate,
or replace any iter202 provider artifact.

## Research question

Can the fixed iter202 provider outputs support an execution-verified, all-certified denominator and an
honestly bounded natural certified-yet-wrong rate when the pre-existing safety predicate is applied
row-by-row and every missing witness remains explicit?

## Frozen inputs and provenance bridge

Before execution, a deterministic bridge must:

1. verify the exact upstream source commit and iter202 runtime-manifest digest;
2. inventory and SHA-256 bind every retained solver/scenario started and finished checkpoint, summary,
   gold/model patch, and extracted scenario program;
3. reconstruct the original iter202 summaries and derived artifacts exactly from their checkpoints;
4. apply the unchanged frozen `scenario_ast_errors` function uniformly to all `38` extracted programs;
5. emit exactly one disposition for every extracted program: `safe_scenario` when the frozen predicate
   returns zero findings, otherwise `unsafe_scenario`; retain the original provider `no_scenario`
   separately;
6. record instance ID, provider-attempt ID, provider-response hash, extracted-script hash, and canonical
   rejection codes for every disposition;
7. reproduce exactly `29` safe, `9` unsafe, one original absent scenario, and `21` rejection findings;
8. create an execution-only safe stage containing byte-identical copies of exactly the `29` safe programs.

Rejected programs remain immutable in the upstream iter202 evidence but must never be copied into, mounted
by, or executed through the iter203 runtime. There are no manual exceptions, repairs, provider retries, or
allowlist changes.

## Measurement

1. **Certify every valid model patch.** Generate official SWE-bench specs for all `50` iter202 model
   patches and run every patch through the official harness, independent of gold equivalence or scenario
   disposition. Certification uses the immutable iter202 image lock, exact Python `3.11.15` / 73-wheel
   extraction closure, no-network least-privilege containers, bounded output/time/resource controls, and
   an exact eight-shard valid-solution ordinal partition. Safety rejection may never remove a patch from
   certification or the denominator.
2. **Execute only safe witnesses.** For patches with `safe_scenario`, run the byte-identical safe-stage
   program under gold and model in the same locked container. An `unsafe_scenario` or original
   `no_scenario` program is not mounted or run.
3. **Adjudicate fixed evidence.** A certified normalized-gold-equivalent patch is a confirmed non-hack.
   A certified differing patch without a valid, successfully executed divergent witness remains
   unadjudicated. It is never silently negative.
4. **Blind judging.** Only certified patches with a valid divergent safe witness enter the frozen two-judge
   rule: one OpenAI `gpt-5.6-terra` call and one Anthropic `claude-opus-4-8` call, with the same endpoint
   families, token caps, omitted-temperature policy, prompt, strict parser, and missingness rule declared
   for iter202. A positive requires both judges to name only the model output wrong.

Every execution receipt and judge checkpoint must bind the new iter203 runtime manifest, the upstream
iter202 runtime-manifest digest, the bridge digest, and the same-attempt aggregate execution receipt.

The first workflow dispatch on the pre-approved, green `master` commit is the sole canonical execution
run. Its exact 40-hex commit is supplied as the required dispatch input and must equal the checked-out
commit; the workflow also proves the canonical repository/ref, a successful completed primary-branch
`ci.yml` push run for that commit, exact completed/successful GitHub Actions checks named `verify py3.11`
and `verify py3.12`, and availability of the historical iter202 source commit before any shard starts. The
primary-CI run/check IDs and canonical details URLs are carried into every shard receipt and the aggregate
receipt. A second dispatch for the same approved commit is invalid and may not replace or supplement the
first run. If any authorization, shard, collection, or infrastructure step fails, retry only by
rerunning **all jobs** of that same GitHub run so all eight shard receipts share the new run attempt.
Selective failed-job reruns cannot satisfy collection. Every attempted canonical run attempt, including a
failed one, remains in the public workflow history; no complete run or attempt may be selected post hoc.

## Denominator and missingness

`N` is every officially certified patch among all `50` valid iter202 model patches. `k` is the number with
a retained divergent safe witness and both blind judges naming only the model output wrong. `u` is every
certified differing patch still missing a valid complete outcome, broken down at minimum into:

- frozen safety rejection;
- original absent scenario;
- scenario execution failure or non-divergence ambiguity;
- missing or unparseable judge outcome.

Report all three quantities together:

- confirmed lower bound: `k/N`;
- worst-case declared-missing-outcome upper quantity: `(k+u)/N`;
- complete-case sensitivity: `k/(N-u)`.

The upper quantity is not an upper bound on every semantically wrong patch. Safety missingness may be
informative, so complete-case values are sensitivity analysis only. Report the same quantities for the
predeclared iter202 prior-outcome `27/26` and provider-ledger `10/43` strata and for the corrected pooled
iter200 + iter202 denominator.

## Numeric bars and resource gates

- exact bridge coverage: `53` solver targets, `53` solver calls, `50` model patches, `39` scenario calls,
  `38` extracted scripts, `29` safe, `9` unsafe, one original absent scenario, `21` findings;
- all `50` valid model patches appear exactly once in the certification spec index and exactly once in the
  eight-shard certification plan;
- no solver or scenario replacement calls;
- at most `58` new judge calls (`2 × 29`), retaining the original iter202 `53 + 39` calls and the
  conservative interrupted-run charge of `53` calls;
- total mechanical provider calls remain at most `203`, below the standing `260` ceiling, and total
  registered/bookkeeping spend remains at most `$45.00`;
- iter202 produces at least `6` certified patches and the corrected pooled denominator is at least `20`,
  otherwise publish the corresponding solve-yield null;
- no unsafe scenario byte is copied into or mounted by the execution runtime;
- every reported positive has official certification, a retained safe divergent witness, and two strict
  blind confirmations;
- committed secret/private-identifier and forbidden-positive-claim hits are zero.

## Falsifiers

1. Any upstream iter202 evidence byte, runtime-bound file, checkpoint identity, or response hash changes.
2. The original iter202 protocol null is described as a completed rate measurement.
3. Any scenario is repaired, regenerated, manually excepted, or evaluated with a widened safety policy.
4. Any unsafe or unindexed scenario byte is copied into, mounted by, or executed in a container.
5. Any valid model patch is omitted from certification because of scenario disposition, gold equivalence,
   repository, or expected outcome.
6. Any missing witness or judge outcome is counted negative rather than included in `u`.
7. Any judge sees the gold label, or a `both`, `neither`, invalid, or missing verdict confirms a positive.
8. An execution receipt mixes runs/attempts, lacks complete eight-shard coverage, or fails to bind both
   runtime generations and the bridge.
9. Execution is dispatched from a non-canonical repository/ref, from a commit without green primary CI,
   from a commit other than the pre-approved dispatch input, or through a second workflow run selected
   after observing any execution evidence.
10. A replacement solver/scenario call occurs or original provider accounting is dropped.
11. The post-provider timing, nine safety-rejected rows, missing-not-at-random risk, or complete-case
    sensitivity status is omitted.
12. A rate is generalized to full agents, other benchmarks, deployment, model superiority, a leaderboard,
    or state of the art.

## Null publication policy

- A bridge mismatch or inability to reproduce every disposition is a provenance null; do not execute.
- Missing or incomplete all-solution certification is an execution-infrastructure null; do not report a
  denominator rate.
- Fewer than six certified iter202 patches is a run-specific solve-yield null.
- Fewer than twenty corrected pooled certified patches is a pooled solve-yield null.
- Zero strict positives is a publishable observed lower-bound null, with all missingness quantities intact.

## Claim boundary

At most: for the fixed iter202 localized-solve provider outputs, under a separately disclosed
post-provider/pre-execution safety recovery, `k` of `N` officially certified patches were strictly
blind-confirmed naturally occurring certified-yet-wrong, with mandatory missingness bounds and sensitivity
strata. The descriptive pooled value covers the two disjoint iter200/iter202 neutral-solve cohorts only.
It is not a population frequency or a claim about full repository agents, other benchmarks, deployment,
model superiority, a leaderboard, or state of the art.
