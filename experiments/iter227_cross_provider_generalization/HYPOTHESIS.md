# Iter227 — cross-PROVIDER generalization of the certified-yet-wrong rate

Status: prospective, pre-registered before any iter227 solve, scenario, execution, or judge output exists.

Predecessor merged master: `7279a437a5b094573ce9ead6ce10e02157635126`.

## Why iter227 exists

Iter223, iter225, and iter226 showed the certified-yet-wrong phenomenon reproduces across three OpenAI models
spanning three generations (`4/29`, `1/25`, `3/17`). Those three points share a single provider, so they
cannot yet distinguish "a property of one lab's models" from "a property of the certification process." Iter227
crosses the provider boundary: the solver becomes an Anthropic model, `claude-sonnet-5`, on the identical
cohort and pipeline. If a model from a different lab also slips a certified-yet-wrong patch past the same
official graded suite, the effect is a property of the SWE-bench certification process across providers, not of
any one lab's training.

## Question

On the identical fixed cohort of SWE-bench Verified issues characterized under three OpenAI solvers, does a
frontier solver from a **different provider** (`claude-sonnet-5`, Anthropic), solving under the identical
neutral prompt and adjudicated by the identical fixed witnessing and blind-judge instrument, also produce
patches the official SWE-bench harness certifies resolved yet that diverge from the gold fix on a safe
uncovered witness, confirmed by two blind judges naming only the model?

## Design — one variable changed: the solver's provider

- **Cohort (held constant):** the same frozen `53`-target set as iter223/iter225/iter226, sha-256
  `9f3078c3e8e49fc435b40a4822ec1126eeca38ba35b02801625c513ccf508966`, reused byte-for-byte.
- **Solver model (the single changed variable):** `claude-sonnet-5` (Anthropic), versus the OpenAI solvers of
  the prior runs. The neutral prompt, the gold-localized buggy-region reconstruction, and the
  `build_solve_patch` builder are imported unchanged from the frozen `run_iter200_solver`; only the provider
  endpoint (`api.anthropic.com/v1/messages`) and the model identifier differ. The solve is concurrent and
  kill-resumable for execution robustness; this changes nothing about the prompt, the model, the solve logic,
  or the recorded per-row provider evidence.
- **Witnessing instrument (held constant):** the safety-aware scenario generator remains `gpt-5.6-terra`
  through the frozen iter195 generator, scanned by the corrected iter223 safety instrument.
- **Certification (held constant):** the official SWE-bench harness in the same pinned x86 containers, same
  `--cap-drop ALL` security boundary, gold-vs-variant differential execution.
- **Judges (held constant):** the two blind judges `gpt-5.6-terra` and `claude-opus-4-8` under the identical
  strict rule — a patch confirms only when officially certified, divergent from gold on a validated safe
  witness, and named wrong by **both** judges naming only the model.

## Disclosed limitation — one judge shares the solver's provider

One of the two fixed blind judges, `claude-opus-4-8`, is from the same provider (Anthropic) as the
`claude-sonnet-5` solver. This is disclosed before any data. It is **conservative for confirmation, not
inflationary**: a hypothetical provider-loyal judge would decline to flag its own provider's patches, which can
only *suppress* confirmations under the both-judges-name-only-the-model rule, never manufacture them. The other
judge, `gpt-5.6-terra`, is a fully independent cross-provider judge, and a confirmed hack still requires it to
name only the model. A `k>0` result therefore survives the strictest reading of this limitation; a `0/N` result
is reported at full weight without attributing it to the shared provider.

## Pooling rule — iter227 does NOT pool into `5/68`

Iter227 re-solves the **same** cohort as the OpenAI cross-model runs with a different-provider model. It is
neither disjoint from those cohorts nor solved by the same model as the iter200/iter223/iter224 pool. Iter227
is reported strictly as a standalone cross-provider comparison joining iter223 (`4/29`), iter225 (`1/25`), and
iter226 (`3/17`). It is a falsifier of this pre-registration to add iter227 to the `5/68` pooled estimate.

## Endpoints

- report iter227 `k/N` with `(k+u)/N` and `k/(N-u)` sensitivities for `u` unadjudicated, on the same cohort;
- report the cross-provider generalization statement (four models, two providers) as directional, not a model
  or provider ranking;
- name every confirmed hack with its instance id, and disclose every `excluded_unsafe` witness separately;
- publish nulls and lower bounds at full weight.

## Acceptance bars

1. The `53` frozen targets reproduce from the committed manifest at sha
   `9f3078c3e8e49fc435b40a4822ec1126eeca38ba35b02801625c513ccf508966`.
2. The solver model recorded in every solve row is `claude-sonnet-5`, and the witnessing generator and both
   judges are unchanged from the OpenAI cross-model runs.
3. Certification uses the official SWE-bench harness in pinned containers; no shipped-test-only certification
   is claimed as a witness.
4. Both blind judges are applied under the strict model-only rule; every unadjudicated outcome is reported.
5. Every reported count regenerates from committed proof artifacts.
6. No sealed iter200/iter202/iter203/iter223/iter225/iter226 byte changes.

## Falsifiers

- Any confirmed-hack count is reported without both judges naming only the model.
- The cohort sha differs, or any target is added, removed, or reordered after selection.
- The recorded solver model is not `claude-sonnet-5`, or the witness generator or a judge model differs.
- Iter227 is added to the `5/68` pooled estimate, or described as a model or provider ranking, product-efficacy
  result, population frequency, or state-of-the-art claim.
- The shared-provider judge limitation is used to explain away a null, or is omitted from the result.
- An `excluded_unsafe` witness is executed, or an unsafe witness is committed.
- Any sealed predecessor evidence byte changes.
- TELOS imports code, state, evidence, branding, or operational authority from Aweb.

## Claim boundary

Iter227 is a bounded, single-variable cross-provider replication over the fixed `53`-target convenience cohort.
`wrong` means differs-from-gold-reference on a witnessing input. The iter227 rate is not a natural population
frequency, a ranking of models or providers, a product-efficacy result, or a state-of-the-art claim; it is
evidence about whether one certified-yet-wrong phenomenon crosses the provider boundary. The static safety scan
is defense in depth; the locked `--cap-drop ALL` container is the security boundary. The blind-judge stage is a
single run under the strict rule with the shared-provider limitation disclosed.

## Execution envelope

Allowed: neutral solve provider calls with `claude-sonnet-5`, safe container execution of certification and
validated witnesses, two blind-judge provider calls, read-only public retrieval, local analysis, and repository
publication. Forbidden: executing an `excluded_unsafe` witness, committing an unsafe witness, changing the
cohort after selection, and any modification of sealed predecessor evidence.
