# Iter229 — a third-provider cross-model point (Google Gemini)

Status: prospective, pre-registered before any iter229 solve, scenario, execution, or judge output exists.

Predecessor merged master: `0f482480f46471005fc14e088825b84110703c74`.

## Why iter229 exists

The cross-model result now spans four models and two providers (OpenAI `gpt-5.6-terra` `4/29`, `gpt-5.5`
`1/25`, `gpt-5.4` `3/17`; Anthropic `claude-sonnet-5` `3/14`), all positive on the frozen `53`-target cohort.
Iter229 adds a **third provider**, Google (`gemini-3.1-pro-preview`). Beyond widening the provider base, this run
removes the one caveat the Anthropic point carried: Google shares a provider with **neither** blind judge
(`gpt-5.6-terra` is OpenAI, `claude-opus-4-8` is Anthropic), so both judges are fully independent of the solver
and there is no shared-provider limitation at all.

## Question

On the identical frozen `53`-target cohort characterized under four OpenAI and Anthropic solvers, does a
frontier solver from a **third provider** (`gemini-3.1-pro-preview`, Google), solving under the identical
neutral prompt and adjudicated by the identical fixed witnessing and blind-judge instrument, also produce
patches the official SWE-bench harness certifies resolved yet that diverge from the gold fix on a safe uncovered
witness, confirmed by two blind judges naming only the model?

## Design — one variable changed: the solver's provider

- **Cohort (held constant):** the same frozen `53`-target set as iter223/iter225/iter226/iter227, sha-256
  `9f3078c3e8e49fc435b40a4822ec1126eeca38ba35b02801625c513ccf508966`, reused byte-for-byte.
- **Solver model (the single changed variable):** `gemini-3.1-pro-preview` (Google), via
  `generativelanguage.googleapis.com`. The neutral prompt, the gold-localized buggy-region reconstruction, and
  the `build_solve_patch` builder are imported unchanged from the frozen `run_iter200_solver`; only the provider
  endpoint and model identifier differ. The solve is concurrent and kill-resumable for execution robustness;
  this changes nothing about the prompt, the model, the solve logic, or the recorded per-row provider evidence.
- **Witnessing instrument (held constant):** the safety-aware scenario generator remains `gpt-5.6-terra`
  through the frozen iter195 generator, scanned by the corrected iter223 safety instrument.
- **Certification (held constant):** the official SWE-bench harness in the same pinned x86 containers, same
  `--cap-drop ALL` security boundary, gold-vs-variant differential execution.
- **Judges (held constant, both fully independent of the solver):** the two blind judges `gpt-5.6-terra`
  (OpenAI) and `claude-opus-4-8` (Anthropic) under the identical strict rule — a patch confirms only when
  officially certified, divergent from gold on a validated safe witness, and named wrong by **both** judges
  naming only the model. Neither judge shares Google's provider, so unlike iter227 this run carries no
  shared-provider caveat.

## Pooling rule — iter229 does NOT pool into `5/68`

Iter229 re-solves the **same** cohort as the earlier cross-model runs with a different-provider model. It is
neither disjoint from those cohorts nor solved by the same model as the iter200/iter223/iter224 pool. Iter229 is
reported strictly as a standalone cross-model comparison joining iter223 (`4/29`), iter225 (`1/25`), iter226
(`3/17`), and iter227 (`3/14`). It is a falsifier of this pre-registration to add iter229 to the `5/68` pooled
estimate.

## Endpoints

- report iter229 `k/N` with `(k+u)/N` and `k/(N-u)` sensitivities for `u` unadjudicated, on the same cohort;
- report the five-model, three-provider generalization statement as directional, not a model or provider
  ranking;
- name every confirmed hack with its instance id, and disclose every `excluded_unsafe` witness separately;
- publish nulls and lower bounds at full weight.

## Acceptance bars

1. The `53` frozen targets reproduce from the committed manifest at sha
   `9f3078c3e8e49fc435b40a4822ec1126eeca38ba35b02801625c513ccf508966`.
2. The solver model recorded in every solve row is `gemini-3.1-pro-preview`, and the witnessing generator and
   both judges are unchanged.
3. Certification uses the official SWE-bench harness in pinned containers; no shipped-test-only certification
   is claimed as a witness.
4. Both blind judges are applied under the strict model-only rule; every unadjudicated outcome is reported.
5. Every reported count regenerates from committed proof artifacts.
6. No sealed iter200/iter202/iter203/iter223/iter225/iter226/iter227 byte changes.

## Falsifiers

- Any confirmed-hack count is reported without both judges naming only the model.
- The cohort sha differs, or any target is added, removed, or reordered after selection.
- The recorded solver model is not `gemini-3.1-pro-preview`, or the witness generator or a judge model differs.
- Iter229 is added to the `5/68` pooled estimate, or described as a model or provider ranking, product-efficacy
  result, population frequency, or state-of-the-art claim.
- An `excluded_unsafe` witness is executed, or an unsafe witness is committed.
- Any sealed predecessor evidence byte changes.
- TELOS imports code, state, evidence, branding, or operational authority from Aweb.

## Claim boundary

Iter229 is a bounded, single-variable cross-provider replication over the fixed `53`-target convenience cohort.
`wrong` means differs-from-gold-reference on a witnessing input. The iter229 rate is not a natural population
frequency, a ranking of models or providers, a product-efficacy result, or a state-of-the-art claim; it is
evidence about whether a specific certified-yet-wrong phenomenon extends to a third provider. The static safety
scan is defense in depth; the locked `--cap-drop ALL` container is the security boundary. The blind-judge stage
is a single run under the strict rule.

## Execution envelope

Allowed: neutral solve provider calls with `gemini-3.1-pro-preview`, safe container execution of certification
and validated witnesses, two blind-judge provider calls, read-only public retrieval, local analysis, and
repository publication. Forbidden: executing an `excluded_unsafe` witness, committing an unsafe witness,
changing the cohort after selection, and any modification of sealed predecessor evidence.
