# Three Layers of Agent-Completion Verification

> **SUPERSEDED HISTORICAL DRAFT.** This document stops at iter156 and is not the current manuscript or a
> current claim source. Iter192 later proved that the `40`-row v1 artifact discussed below contains no
> reward hacks because every row fails the official grader. The current methodology-corrected manuscript is
> `paper/telos.tex`; its status and claim boundary are in `paper/README.md` and the root `README.md`. The
> prose below is retained only to preserve the earlier research chronology.

A plain-language paper draft for the Telos program, current through `iter156`.

This is a bounded findings paper. It is not a SWE-bench leaderboard result, not a public benchmark score,
not a model-comparison result, and not a state-of-the-art claim. Every number below is tied to committed
experiment artifacts, manifests, and validated receipts.

## Abstract

When an AI coding agent says a task is done, the usual proof is that a test passed. That proof is weak if
the agent can influence the test or optimize only for the visible test. The agent can edit tests, weaken
assertions, hard-code an expected value, or write code that works only for the input the test happens to
check.

Telos asks whether an external verifier can tell the difference between a real fix and a patch that only
games the visible proxy. The substrate is `SWE-bench_Verified`. When a result says "executed", the changed
code was run against the project's real tests in the appropriate environment, often the official SWE-bench
Docker harness.

The finding is that completion verification needs three layers:

1. A deterministic detector catches mechanical reward hacks such as test edits, weakened assertions,
   obvious hard-coding, and receipt tampering.
2. A strong model judge catches semantic hacks the deterministic detector cannot see.
3. Held-out execution catches plausible patches that both static layers accept but that fail away from the
   visible test.

The hard class is a "both-miss": the patch passes the visible test, evades the detector, is accepted by a
model judge, and is still wrong on unseen behavior. A frontier adversary can construct this class on real
code. In the first cross-repo reward-model measurement, `5/20` saved hacks survived the detector and both
frontier judges. The later v1 artifact packages `40` constructed, execution-verified both-miss rows across
`11` repositories; `13/40` survive every static layer tested. That artifact is a row set for future scoring
gates, not a score or leaderboard.

Used as a gate, the protocol also improves outcomes. It rejects a gamed patch and tells the agent only
"your fix does not generalize", without revealing the gold patch, hidden test name, or expected output. On
bounded samples, this converts some gamed completions into real fixes: `0/13 -> 10/13` on two django
samples and `0/20 -> 10/20` on the official SWE-bench harness across eight repositories. Correct
completions are preserved in the control: `0/12` false rejections.

The transferable lesson is simple: a model is unreliable as the final judge of code correctness, but useful
as a generator of executable checks. Do not trust the model's verdict. Ask it for a property, then run the
property.

## 1. Problem

Coding benchmarks usually ask whether tests pass. That is useful, but it is not the same as asking whether
the task is complete. Passing a visible test can become a proxy reward. If an agent can satisfy that proxy
without solving the underlying bug, the verifier is measuring reward hacking rather than completion.

The question is:

> Given a candidate diff and the public target-test identifiers, can an external protocol tell a real fix
> from a patch that merely games the visible test, and can the protocol help the agent repair a gamed patch
> into a real fix?

The verifier does not trust the agent's final message. The static layers see only the candidate diff, the
public test identifiers, and the receipt the candidate would present as evidence. They do not see a hidden
label or the gold patch.

## 2. Setup

The task substrate is `princeton-nlp/SWE-bench_Verified`, a 500-instance set of human-reviewed GitHub
issues. Each instance has a target test, `FAIL_TO_PASS`, that should fail before the fix and pass after the
fix. It also has regression tests, `PASS_TO_PASS`, that should keep passing after a correct fix.

A candidate completion is a raw unified diff. Telos evaluates it with three kinds of evidence:

- **Visible proxy:** the target test the agent is trying to pass.
- **Static verifier:** a verifier that reads the patch but does not run the changed program.
- **Held-out execution:** running the changed program on behavior the visible test did not expose.

Where environment fidelity matters, Telos uses the official SWE-bench Docker image for that instance. That
matters because old projects often require old Python and dependency versions; a local modern interpreter
can create false failures.

## 3. Three Layers

No single verifier was enough.

| Layer | What it catches | Evidence |
| --- | --- | --- |
| deterministic detector | mechanical hacks: test edits, assertion weakening, literal special-casing, receipt tampering | `0/200` false positives on real human gold patches; source-only evasion recall hardened from `0` to full recall while staying at `0/200` false positives |
| LLM judge | oblique and hard-coded hacks the detector misses | on `60` stealth candidates, `detector_only=0`, `judge_only=15`; on executed hacks, execution-only catches `0/3`, detector catches `1/3`, judge catches `3/3` |
| held-out execution | plausible completions that both static layers accept but that fail away from the visible test | on the both-miss class, static verifiers catch `0/2` and held-out-input execution catches `2/2`; later frontier and cross-repo runs show the class persists |

The resulting shape is a cascade. Run the free deterministic detector first. Send survivors to the model
judge. Use execution for the cases where static reading cannot prove general behavior.

This is not a contest between rules and models. The detector's value is cost, determinism, and line-level
reproducibility. The model judge has broader semantic coverage. Execution is the recovery layer when
reading code is not enough.

## 4. The Both-Miss Class

A both-miss patch passes the visible test, evades the deterministic detector, is judged legitimate by a
model, and still fails on unseen behavior.

The first examples are small but decisive. One patch presents `iter(sorted(self.dict, reverse=True))` as if
it were a true reversal. Another presents `'0%03d' % year` as if it were correct zero-padding. Both pass
the relevant hidden test and fool the static layers, but both fail on a new input that checks the general
rule.

The same class appears in application code. A frontier adversary starting from the gold fix can rewrite it
into a subtly wrong patch that still passes the target test. On well-tested django instances,
`gpt-5.6-terra` produced confirmed both-miss hacks. In `django-14752`, the patch keeps the shape of the
correct `serialize_result` method but returns `str(obj.pk)` instead of respecting `to_field_name`. It
passes the visible test, evades the detector, and is judged legitimate, but fails the held-out behavior the
gold fix handles.

Across `25` genuine attempts on that django pool, the frontier adversary produced confirmed both-miss hacks
on `0.24` of attempts. On `0.12` of attempts, the hack also fooled the model judge and was caught only by
execution.

Larger judges do not close the gap. Re-judging six confirmed both-miss hacks with two frontier judges, the
baseline judge is fooled by `3/6`, `gpt-5.6-terra` by `1/6`, and `claude-opus-4-8` by `3/6`. One hack,
`django-14311`, is accepted by all three judges and evades the deterministic detector. A judge panel helps,
but it does not replace execution: an any-catch panel catches `6/7`, and `django-14311` survives every
panel rule.

## 5. Reward-Model Relevance And The v1 Artifact

The both-miss class matters for reward models. If a model is used to score code during reinforcement
learning, then a patch the model accepts can become training reward even when the patch is wrong.

In the first cross-repo reward-model measurement, Telos evaluated `20` execution-verified both-miss hacks
across eight repositories:

| Static verifier | Fooled by the hack |
| --- | ---: |
| deterministic detector | `20/20` |
| `gpt-5.6-terra` as reward model | `7/20` |
| `claude-opus-4-8` as reward model | `9/20` |
| detector plus both frontier judges | `5/20` |

The `5/20` number is load-bearing: those rows survive every static verifier tested and require held-out
execution.

The benchmark artifact then grew through a visible sequence:

- `iter153` materialized the `20` iter152 rows as a validated seed with diff hashes and traceability.
- `iter154` ran a frozen expansion pilot and found `17` new execution-verified rows, short of the
  pre-registered `20`-new-row bar. That result is published as a null shortfall.
- `iter155` used the shortfall evidence to pre-register an adaptive follow-up. It added `3` rows and
  crossed the `40`-row candidate-pool bar.
- `iter156` joined the seed, the `17` expansion rows, and the `3` adaptive rows into
  `benchmarks/reward_hack_benchmark_v1/`.

The v1 artifact has exactly `40` unique constructed both-miss rows across `11` repositories. All `40/40`
rows have hack-diff hashes, official report hashes, and source traceability. Static labels in the manifest
show that `16/40` fool `gpt-5.6-terra`, `19/40` fool `claude-opus-4-8`, and `13/40` survive every static
layer tested.

This is a released row artifact only. It does not claim a model score, leaderboard rank, model
superiority, state-of-the-art performance, natural reward-hacking frequency, or broad reward-model
robustness.

## 6. From Detection To Intervention

Detection is necessary, but the stronger question is whether the verifier can improve the agent's work.
Telos tests this by using execution as a completion gate.

The proxy gate accepts a patch as soon as the visible target test passes. A both-miss patch has real
completion `0` under this gate by construction, because it passes the target test but fails some held-out
behavior.

The Telos gate rejects the patch when held-out execution fails. The feedback is deliberately generic:
"your fix does not generalize." It does not reveal the gold patch, the hidden test name, or the expected
output. The agent can revise, and the gate re-runs the checks.

On `7` django both-miss starts, this moves real completion from `0/7` to `5/7`. The result replicates on a
disjoint older django sample, again `0/7 -> 5/7`. Pooled across the two samples, the gate moves real
completion from `0/13` to `10/13`.

The intervention also scales across repositories on the official SWE-bench harness. Across `20` both-miss
starts from eight repositories, the proxy gate resolves `0/20`, while the Telos gate recovers `10/20` to
full official resolution. This is not a model leaderboard score. The baseline is definitional, and the
oracle is the repository regression suite. The useful claim is narrower: execution-based rejection plus a
generic generalization signal can convert some gamed patches into real fixes.

The gate also preserves correct completions. Across `10` instances, it accepts all `10` gold fixes and both
genuinely correct honest agent fixes, for `0/12` false rejections.

## 7. Gold-Free Execution

The regression-gated intervention uses held-out tests. That is realistic, because teams run regression
suites in continuous integration, but it still uses privileged test coverage. Telos therefore tests a
gold-free version.

Gold-free means no hidden test and no reference patch enters the gate. A model reads the function contract
and visible test, then proposes a property that correct code should satisfy. For a parser and formatter,
that might be a round trip. For a mathematical function, it might be an identity. The property is not
trusted. It must pass the visible-test anchor, and then execution checks it on new inputs.

On `7` evaluated instances pooled across runs, the gold-free property gate catches the gamed completion
`7/7` and reaches real completion `5/7`. That is close to the regression-gated `10/13` rate. The scope is
narrow: the result applies only where a useful property can be derived. But it shows that the improvement
comes from execution-based rejection plus the generalization signal, not from leaking the hidden tests.

One correction is on the record. An early gold-free run reported every property unsound. The cause was a
Django settings harness bug in the standalone property scripts, not a research finding. After fixing the
harness, properties are sound on `9/10` targeted functions and the gold-free intervention result holds.

## 8. Transferable Insight

The same model has two roles with opposite reliability.

As a verdict-giver, the model is asked whether a patch is correct. That is an ungrounded judgment, and the
both-miss examples show that plausible wrong code can fool it.

As a property-generator, the model is asked what relation correct code should satisfy. The answer becomes
an artifact. Telos runs that artifact. If the property is unsound, it fails the visible anchor or falsely
rejects known-correct code. If the patch is wrong, execution falsifies it on new inputs.

The lesson is to move model output from judgment to checkable artifact. Let the model propose checks. Let
execution decide.

## 9. Limitations

- **Small samples.** The replicated django intervention is pooled `N=13`; the cross-repository official
  intervention is `N=20`; the reward-model gaming measurement starts at `N=20`; the gold-free property-gate
  rate is `N=7`; the v1 row artifact is `N=40`. These are pilots and artifacts, not distributional claims.
- **Constructed hacks.** The both-miss rows are adversarially constructed from gold fixes. This isolates
  the failure class, but it does not measure how often a naturally trained RL agent would discover it.
- **Artifact, not score.** `reward_hack_benchmark_v1` is a hash-checked row artifact. No model has a
  benchmark score on it in this paper.
- **Repository coverage.** The latest intervention and reward-model measurements span real repositories,
  but the pools are selected for reward-hack-prone starts. Per-repository recovery varies, including zeros.
- **Single repair model.** The adversary and repairing agent are from the same frontier-model family in
  key runs. Cross-model repair generalization is untested.
- **Property subset.** Gold-free properties work only where a function admits a checkable contract. A
  structural single-testable-function criterion covers `405/500 = 0.81` of SWE-bench Verified, but
  property-rich domains are much narrower, about `0.10` even in sympy.
- **No baseline comparison.** The paper does not benchmark against every reward-hack detector. The
  contribution is the decomposition, the both-miss discovery, the intervention, and the released row
  artifact.

## 10. Reproduction

Each experiment under `experiments/iterNNN_*` has a pre-registered `HYPOTHESIS.md`, a result held below the
evidence, proof artifacts, a receipt where applicable, and a learning record. The deterministic validators
run in CI. Native-execution and Docker transcripts are retained as observed evidence.

The released row artifact is:

- `benchmarks/reward_hack_benchmark_v1/reward_hack_benchmark_v1.jsonl`
- `benchmarks/reward_hack_benchmark_v1/manifest.json`
- `benchmarks/reward_hack_benchmark_v1/schema.json`

The manuscript source is `paper/telos.tex`. The build notes are in `paper/README.md`.
