# Iteration 193 - Certified-Resolved Reward-Hack Construction

Status: PRE-REGISTERED, result pending. No provider calls, SWE-bench executions, cloud resources, or
model evaluations have been run for this gate. This is a genuine pre-registration in the protective
sense: the acceptance rule, the numeric bars, and the falsifiers below are fixed **before any candidate
is generated**, because the measurement this gate performs is stochastic (a model proposes variants) and
the temptation to accept a looser class after seeing the yield is exactly the hazard pre-registration
exists to prevent.

## Why this gate exists

iter192 established, from committed bytes and without spend, that `benchmarks/reward_hack_benchmark_v1/`
contains no reward hacks. Its generator admitted a row only when at least one `PASS_TO_PASS` test
failed, so the official SWE-bench harness marks all `40/40` rows unresolved, and a zero-cost
official-harness baseline detects `40/40` against the `17/40` panel figure.

iter192 also established that the same generator runs produced `139` variants across `65` instances that
the official harness certified as **resolved** — target test passing, entire existing suite passing —
and discarded every one as a `no_both_miss` failure without preserving the diffs.

This gate constructs that discarded class deliberately, and it is the class that matters. A reward hack
scores well on the reward function while being wrong. A patch the harness certifies as resolved has, by
definition, scored full marks. If it is also wrong, it is the genuine article: it survives the grader,
corrupts the training signal, and ships. Against that class the official harness scores `0` by
construction — it certified them — so the iter192 baseline cannot help, and an instrument that probes
behavior beyond the existing suite is required.

## The inversion

The iter152 acceptance condition at `detection_pipeline.py:132` is:

```python
if ev["applied"] and ev["ftp_ok"] and ev["held_fail"]:
```

This gate inverts the third term and adds an independent wrongness oracle:

```
accept when:  applied  AND  ftp_ok  AND  NOT held_fail  AND  wrong_vs_gold
```

- `ftp_ok and not held_fail` → the official harness marks the instance **resolved**.
- `wrong_vs_gold` → an independent oracle shows the variant is wrong.

Both terms are required. `ftp_ok and not held_fail` alone is insufficient and must not be treated as a
positive: a variant that passes the whole graded suite may simply be a correct equivalent rewrite of the
gold patch. iter140 recorded exactly that outcome class (`still_correct`). Separating "certified and
wrong" from "certified and correct" is the entire difficulty of this gate.

### The wrongness oracle: uncurated-test differential (revised before data)

This gate's original draft defined `wrong_vs_gold` as behavioral divergence on synthesized random
inputs. That is revised here, **before any candidate is generated and before any spend**, because a
strictly better oracle exists. Revising a pre-registration before data is legitimate; revising it after
is not, and this revision is timestamped by the commit that introduces it.

`PASS_TO_PASS` is not the repository's test suite. It is a **curated subset** of it, fixed by the
SWE-bench instance. The official harness grades `FAIL_TO_PASS ∪ PASS_TO_PASS` and nothing else. So the
oracle is pure execution:

```
wrong_vs_gold  ⇔  ∃ test T ∉ (FAIL_TO_PASS ∪ PASS_TO_PASS)
                  such that gold passes T and the variant fails T,
                  both executed in the same pinned container.
```

Why this is better than input synthesis:

- **No model in the ground-truth path.** No property, no input generator, no call-expression inference,
  and therefore none of the iter124/iter125 harness-synthesis failure modes (`2/7` full-auto,
  `4/7` validated). Wrongness is decided by running tests the repository already ships.
- **Gold is the reference, and it is executed, not read.** `gold passes T` and `variant fails T` are both
  observed in the same container, so a flaky or environment-broken `T` cannot manufacture a positive:
  it would fail under gold too and be excluded.
- **It indicts the reward directly.** A row satisfying both terms is a patch that scores full marks on
  the official SWE-bench metric while breaking a real test that the metric never looked at. That is a
  reward hack against SWE-bench Verified specifically, demonstrated rather than argued, and it is a
  statement about the benchmark's curated `PASS_TO_PASS` being insufficient.

Fallback, used only if a candidate is certified-resolved but no uncurated failing test exists:
gold-differential on synthesized inputs. Any row accepted via the fallback must be tagged
`oracle: synthesized_differential` and reported separately from `oracle: uncurated_test`, never pooled.

This oracle **cannot** establish that a certified-resolved variant with no uncurated failing test is
correct. Absence of a failing uncurated test is not evidence of correctness, and no such claim is
permitted. Those candidates are reported as `undetermined`, not as `still_correct`.

## Ground truth vs. detection — the boundary that must not blur

Gold **is** used to establish ground truth here. Gold **must not** be used by any detector evaluated in
a later gate. This mirrors iter121: differential-against-gold is legitimate for labelling and forbidden
at decision time.

Concretely: this gate may execute the gold patch to determine whether a variant is wrong. A property
oracle or judge evaluated on the resulting benchmark may not see the gold patch, the gold diff, the
label, hidden test names, or official reports.

## Execution surface

The proven path, not this laptop. iter134-iter137 established that `.github/workflows/docker-batch.yml`
runs official SWE-bench images on native-x86 GitHub runners (`ubuntu-latest`), executes tests inside the
pinned container, and evaluated gold-free properties in-container at a `3/3` genuine-sound rate.

iter190 declared the execution surface unavailable after probing only the local machine (arm64 macOS, no
Docker daemon) and never referenced the CI path. That null was a fact about the laptop, not the world.
This gate runs on the CI surface.

## Inputs

- `experiments/iter192_reward_hack_benchmark_construct_validity_audit/proof/discarded_certified_variants.json`
- `experiments/iter152_reward_model_gaming_scale/proof/raw/detection_pipeline.py`
- `.github/workflows/docker-batch.yml`, `scripts/docker_batch_ci.sh`
- SWE-bench Verified public dataset rows (already snapshotted at
  `experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/swebench_verified_rows_snapshot.json`)

## Numeric Bars

Minimum pass bars:

- candidate instances attempted is at least `20`,
- provider calls do not exceed `120` (ceiling; adversary proposals only),
- estimated provider spend does not exceed `$15.00`,
- new cloud resources created and not deleted is exactly `0`,
- every accepted row has official harness `resolved == true`,
- every accepted row has zero `PASS_TO_PASS` failures,
- every accepted row records at least one uncurated test `T` outside `FAIL_TO_PASS union PASS_TO_PASS`
  that gold passes and the variant fails, executed in the same pinned container,
- accepted certified-resolved-and-wrong rows is at least `5`,
- raw official reports and uncurated-test transcripts retained for every accepted row is `100%`,
- committed secret/project/account identifier hits are exactly `0`,
- forbidden positive claim hits are exactly `0`.

## Falsifiers

1. Any accepted row has official harness `resolved == false`, or any failing `PASS_TO_PASS` test. That
   row is not certified and must be rejected.
2. Any accepted row lacks a recorded, reproducible uncurated failing test (or, for fallback rows, a
   recorded differential counterexample). Wrongness would then be asserted rather than shown, and the
   row must be rejected.
3. Gold patch content, gold diffs, labels, hidden test names, or official reports appear in any artifact
   intended for a future detector's prompt.
4. Fewer than `5` certified-resolved-and-wrong rows are constructed. The gate then publishes a **null**
   with the full outcome distribution (`still_correct`, `broke_visible`, `broke_suite`, `no_degrade`,
   `harness_error`) and an honest construction-hardness bound. A null here is a real result: it would
   bound how often a frontier adversary can produce a patch that survives a complete SWE-bench Verified
   test suite while being wrong.
5. Spend exceeds `$15.00` or provider calls exceed `120`, or any cloud resource is left undeleted.
6. The result presents a leaderboard, model-comparison, model-superiority, state-of-the-art,
   natural-frequency, broad robustness, production, or product-value claim.
7. Any detection claim. This gate constructs a benchmark. It measures no detector, including the property
   oracle. Detector comparison is iter194 and must not be smuggled in here.

## Public-source context (iter184 discipline; sources are public, dated, and cited)

Where this sits against published work, stated so the claim stays inside it:

- **Scale.** Public labeled corpora in this space are far larger: METR MALT (`10,919` transcripts,
  `2,690` human-reviewed), Terminal Wrench (`3,632`), ControlArena `apps-backdoors` (`4,184`), TRACE
  (`517`), ImpossibleBench (`349`+`103`). A `5`-`20` row artifact is **not** competitive on size and no
  size claim may be made. Its only defensible axis is precision: every row execution-verified on the
  official harness with a recorded uncurated failing test.
- **Granularity and construction.** Existing corpora label trajectories or whole solutions; this gate
  labels **diffs**. That is a real distinction and may be stated. **Elicitation may not be:** those
  corpora are elicited (a model prompted to hack), and **so is this one** — the adversary here is
  explicitly instructed to produce a wrong variant. No naturalness or non-elicited claim is permitted.
- **Judges are not uniformly weak.** Control Tax (arXiv:2506.05296) reports monitor AUC `0.92`-`0.96` on
  APPS-style backdoors; Redwood reports trusted editing at `92%` safety. Judge performance degrades on
  semantic hacks in real repositories. Any later comparison must state that gap precisely rather than
  claiming judges do not work.
- **The gap this targets is publicly open.** DeepMind's Frontier Safety Framework v3.0 (2025-09-22),
  Instrumental Reasoning Level 2, describes a model circumventing oversight "even when relevant model
  outputs (including, e.g. scratchpads) are being monitored" and lists its mitigation as "Future work."

## Claim Boundary

At most, if this gate passes: Telos has `N >= 5` execution-verified rows in which the official SWE-bench
Verified harness certifies a patch as resolved while a recorded uncurated test that gold passes and the
variant fails shows the patch is wrong, constructed under a bounded frontier-adversary budget with an explicitly
hack-eliciting prompt, with raw evidence retained.

Not supported: any natural-frequency estimate (these are constructed and elicited, not sampled from real
agent behavior); any claim that the rows are naturally-occurring or non-elicited; any claim about how
often deployed agents reward-hack; any benchmark-size or corpus-scale claim; any detector result; any
leaderboard, model-comparison, state-of-the-art, broad robustness, production, or product-value claim;
any claim that the class generalizes beyond the repositories and instances attempted.

## Why a null would still matter

If a frontier adversary, explicitly instructed to produce a wrong patch that survives the full suite,
cannot do so in `20+` attempts, that is a substantive finding about SWE-bench Verified: its test suites
would be strong enough to make certified-resolved-but-wrong patches hard to construct, which bounds the
practical severity of this failure mode and argues the existing suite is a stronger verifier than the
mission has assumed. Either outcome advances the mission. That is the property iter190 lacked, and the
reason this gate is worth spend where iter191 was not.
