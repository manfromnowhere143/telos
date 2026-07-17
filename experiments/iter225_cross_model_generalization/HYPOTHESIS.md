# Iter225 — cross-model generalization of the certified-yet-wrong rate

Status: prospective, pre-registered before any iter225 solve, scenario, execution, or judge output exists.

Predecessor merged master: `930f8870c3f0fac7c5bea55bd8b14bf750075eaa`.

## Why iter225 exists

Iter200, iter223, and iter224 all measured the natural certified-yet-wrong rate with a single solver model,
`gpt-5.6-terra`. Their pooled `5/68` is therefore silent on the most consequential question for the claim:
is a certified-yet-wrong patch a property of one model, or of the SWE-bench certification process itself? If a
different frontier model, solving the identical issues under the identical pipeline, also produces patches the
official harness certifies yet that diverge from gold on an uncovered witness, the phenomenon is a property of
the benchmark's coverage, not of one model. If it does not, the effect is model-idiosyncratic. Iter225 runs
the controlled version of that test.

## Question

On the identical fixed cohort of SWE-bench Verified issues that iter223 already characterized under
`gpt-5.6-terra`, does a **different** frontier solver model (`gpt-5.5`), solving under the identical neutral
prompt and adjudicated by the identical fixed witnessing and blind-judge instrument, also produce patches the
official SWE-bench harness certifies resolved yet that diverge from the gold fix on a safe uncovered witness,
confirmed by two blind judges naming only the model?

## Design — a controlled single-variable comparison

Iter225 changes exactly one variable from iter223: the solver model. Everything else is held byte-identical.

- **Cohort (held constant):** the same frozen `53`-target set as iter223, sha-256
  `9f3078c3e8e49fc435b40a4822ec1126eeca38ba35b02801625c513ccf508966`, reused byte-for-byte
  (`experiments/iter223_natural_rate_safety_aware/proof/raw/solve_targets.json`). Same repositories, same
  issues, same eligibility provenance.
- **Solver model (the single changed variable):** `gpt-5.5`, versus iter223's `gpt-5.6-terra`. `gpt-5.5` is a
  full minor generation earlier and a distinct training run, chosen so certification power stays comparable
  (a much weaker model would simply certify less often and confound the model effect with a capability gap).
  The neutral prompt, the gold-localized buggy-region reconstruction, and the `build_solve_patch` builder are
  imported unchanged from the frozen `run_iter200_solver`, so every solve is byte-for-byte the frozen
  procedure with only the model identifier swapped.
- **Witnessing instrument (held constant):** the safety-aware scenario generator remains `gpt-5.6-terra`
  through the frozen iter195 generator, scanned by the corrected iter223 safety instrument. The adjudication
  instrument is deliberately identical to iter223's so the only difference between the two results is the
  solver, not the witness generator.
- **Certification (held constant):** the official SWE-bench harness in the same pinned x86 containers, same
  `--cap-drop ALL` security boundary, gold-vs-variant differential execution.
- **Judges (held constant):** the two blind judges `gpt-5.6-terra` and `claude-opus-4-8` under the identical
  strict rule — a patch confirms only when officially certified, divergent from gold on a validated safe
  witness, and named wrong by **both** judges naming only the model. `both`, `neither`, invalid, or missing
  never confirm.

## Pooling rule — iter225 does NOT pool into `5/68`

Iter225 re-solves the **same** cohort as iter223 with a **different** model. It is therefore neither disjoint
from iter223 nor solved by the same model as the iter200/iter223/iter224 pool. Iter225 is reported strictly as
a standalone cross-model comparison against iter223's `4/29`. It is a falsifier of this pre-registration to
add iter225 to the `5/68` pooled estimate.

## Endpoints

- report iter225 `k/N` with `(k+u)/N` and `k/(N-u)` sensitivities for `u` unadjudicated, on the same cohort as
  iter223;
- report the head-to-head against iter223 (`gpt-5.6-terra`, `4/29`) as a generalization statement, not a model
  ranking: whether the certified-yet-wrong phenomenon reproduces under a different solver;
- name every confirmed hack with its instance id, and disclose every `excluded_unsafe` witness separately;
- publish nulls and lower bounds at full weight. A `0/N` iter225 result is a genuine, publishable finding that
  the phenomenon is model-dependent on this cohort; a `k>0` result is evidence it generalizes.

## Acceptance bars

1. The `53` frozen targets reproduce from the committed manifest at sha
   `9f3078c3e8e49fc435b40a4822ec1126eeca38ba35b02801625c513ccf508966`, identical to iter223's cohort.
2. The solver model recorded in every solve row is `gpt-5.5`, and the witnessing generator and both judges are
   unchanged from iter223.
3. Certification uses the official SWE-bench harness in pinned containers; no shipped-test-only certification
   is claimed as a witness.
4. Both blind judges are applied under the strict model-only rule; every unadjudicated outcome is reported.
5. Every reported count regenerates from committed proof artifacts.
6. No sealed iter200/iter202/iter203/iter223 byte changes.

## Falsifiers

- Any confirmed-hack count is reported without both judges naming only the model.
- The cohort sha differs from iter223's, or any target is added, removed, or reordered after selection.
- The recorded solver model is not `gpt-5.5`, or the witness generator or a judge model differs from iter223.
- Iter225 is added to the `5/68` pooled estimate, or described as a model ranking, product-efficacy result,
  population frequency, or state-of-the-art claim.
- An `excluded_unsafe` witness is executed, or an unsafe witness is committed.
- Any sealed predecessor evidence byte changes.
- TELOS imports code, state, evidence, branding, or operational authority from Aweb.

## Claim boundary

Iter225 is a bounded, single-variable cross-model replication over the fixed `53`-target convenience cohort of
iter223. `wrong` means differs-from-gold-reference on a witnessing input. The iter225 rate is not a natural
population frequency, a ranking of `gpt-5.5` against `gpt-5.6-terra`, a product-efficacy result, or a
state-of-the-art claim; it is evidence about whether one specific certified-yet-wrong phenomenon depends on
the solver model. The static safety scan is defense in depth; the locked `--cap-drop ALL` container is the
security boundary. The blind-judge stage is a single run under the strict rule.

## Execution envelope

Allowed: neutral solve provider calls with `gpt-5.5`, safe container execution of certification and validated
witnesses, two blind-judge provider calls, read-only public retrieval, local analysis, and repository
publication. Forbidden: executing an `excluded_unsafe` witness, committing an unsafe witness, changing the
cohort after selection, and any modification of sealed predecessor evidence.
