# Telos

**A research program for verifying autonomous agent work by evidence, not by trust.**

No model result is claimed yet. The repository begins with a completed target survey:
[`experiments/iter00_target_survey`](experiments/iter00_target_survey/RESULT.md), which selected a
hybrid Telos overlay on public software-agent tasks.

The question is narrow and testable:

> When an AI agent says a long-horizon task is done, can an external protocol prove that the real
> objective was completed, that the agent did not merely satisfy the visible proxy, and that it
> stopped at the correct boundary?

The target is not a better chat transcript. The target is a receipt-bearing completion protocol:
tests when code changed, typecheck/build when applicable, diff-scope checks, live-domain checks
when production behavior changed, artifact hashes, stated acceptance criteria, named falsifiers,
and an adversarial review pass.

## The Real-Trajectory Verification Arc (iter109 onward)

The current frontier of this program moved completion verification off self-authored fixtures and
onto real external ground truth. Earlier iterations (iter104, iter107) scored a detector that
branched on fixture taxonomy or read authored packet booleans, so both the traps and the detector
were written by the same process and no external validity was earned. The arc below fixes that.

The subject is the real `princeton-nlp/SWE-bench_Verified` dataset. A candidate solution is a raw
unified diff plus the public `FAIL_TO_PASS` test ids. The deterministic detector
(`telos/tamper/`) reads only that - never a ground-truth label, an attack-type field, or an
authored semantic boolean. It encodes the documented reward-hack failure modes: editing the
verifier (the tests that must fail-to-pass, `conftest.py`, pytest config), weakening assertions,
hard-coding a hidden expected value in source, and tampering with a receipt digest.

| iter | question | result |
| --- | --- | --- |
| [109](experiments/iter109_real_trajectory_tamper_detection_pilot/RESULT.md) | Does a raw-diff detector work on real data? | `0/200` false positives on real human gold patches; the execution-only default catches none of the hacks |
| [110](experiments/iter110_adversarial_hardening_hacker_fixer_loop/RESULT.md) | Does it survive adversarial evolution? | source-only evasion recall `0 -> 1.0` at `0/200` false positives (one hacker-fixer round) |
| [111](experiments/iter111_llm_judge_steelman_baseline/RESULT.md) | Is a strong LLM judge already enough? | a `gemini-2.5-flash` steelman judge ties the detector on obvious hacks: `0.00` FP, `1.00` recall, `$0.044` |
| [112](experiments/iter112_stealth_divergence_judge_vs_detector/RESULT.md) | Where do they diverge? | on 60 stealth candidates: `detector_only=0`, `judge_only=15`, `both_catch=30`, `both_miss=0` - the judge strictly beats the detector on oblique special-casing |
| [113](experiments/iter113_native_execution_ground_truth/RESULT.md) | Do the hacks really pass the tests? | native execution of a real instance: base fails, gold passes, a hard-coded hack passes the real hidden test; execution-only and the detector accept it, only the judge flags it |
| [114](experiments/iter114_batch_native_execution/RESULT.md) | Does gold resolution hold across a batch? | `4/5` gold patches resolve under real execution; `0/5` detector false positives; one honest native-harness fidelity gap |
| [115](experiments/iter115_wider_batch_native_execution/RESULT.md) | Tighten the fidelity estimate | `17/18` gold patches resolve under real execution (`0.94`); `0/18` detector false positives; the same single fidelity gap |
| [116](experiments/iter116_executed_hack_catch_rate/RESULT.md) | Measured catch rate on executed hacks | on three hacks that really pass their hidden tests: execution-only `0/3`, detector `1/3`, judge `3/3` |
| [117](experiments/iter117_precision_coverage_boundary/RESULT.md) | Can the detector gap close for free? | a constant-return signal catches `2/2` missed hacks but costs `1/200` real false positives - the first hardening that trades precision, so it is not adopted and the class is judge territory |
| [118](experiments/iter118_both_miss_stealth_class/RESULT.md) | Is there a hack neither verifier catches? | yes - `2/2` disguised hacks pass the hidden test, evade the detector, and fool the judge; both are wrong on a held-out input, so held-out-input execution is the required defense |
| [119](experiments/iter119_metamorphic_defense/RESULT.md) | Does held-out-input execution catch them? | yes - on the both-miss class the visible test, detector, and judge each catch `0/2` while metamorphic held-out-input execution catches `2/2`; the loop closes |
| [120](experiments/iter120_generalized_metamorphic/RESULT.md) | Does the metamorphic layer generalize past a hand-picked input? | yes - seeded random held-out inputs catch `2/2` (diverging on `10/12` and `8/12`); the open problem narrows to an oracle without gold |
| [121](experiments/iter121_gold_free_property_oracle/RESULT.md) | Can the oracle drop the gold reference? | yes - contract properties (no gold) catch `2/2` (violating `27/30`, `30/30`) at `0` false positives on gold; the frontier narrows to automatic property generation |
| [122](experiments/iter122_automatic_property_generation/RESULT.md) | Can the model generate the property itself? | yes - `gemini-2.5-flash` proposes properties that catch `2/2` (violating `28/30`, `26/30`) at `0` gold false positives; the model, fooled as a judge, is reliable as a property generator because execution checks it |
| [123](experiments/iter123_visible_test_anchor_filter/RESULT.md) | Can unsound properties be rejected without gold? | yes - the visible test is a known-correct anchor; it keeps `2/2` sound properties and rejects `2/2` unsound ones with no gold reference |
| [124](experiments/iter124_property_generation_at_scale/RESULT.md) | Does automatic property generation generalize? | not yet - across seven real instances only `2/7` produce a clean sound auto-generated harness; the mechanism is real but the harness/input synthesizer is the bottleneck (generation, syntax, input-domain, mis-target failures) |
| [125](experiments/iter125_harness_synthesizer/RESULT.md) | Does a validated synthesizer help? | yes - test-source targeting, input validation, and retry roughly double the rate to `4/7`; a non-triviality filter is required and catches a vacuous harness raw soundness accepted; two residual failures (unsound property, structured-input domain) remain |
| [126](experiments/iter126_gold_free_soundness_gate/RESULT.md) | Can the soundness decision drop gold too? | yes - non-triviality plus the visible-test anchor keeps the `3` genuine-sound harnesses, rejects the unsound `10999` property gold was needed for, and rejects the vacuous `11276`; the pipeline is gold-free at every step |
| [127](experiments/iter127_structured_input_residuals/RESULT.md) | Can structured inputs close the residuals? | yes - seeding the generator from the test example and using a non-pathological format make `11206` and `11848` sound, raising the genuine-sound rate to `5/7`; the remaining two are an unsound generated property and a mis-targetable task, not input-domain failures |
| [128](experiments/iter128_property_strategy_taxonomy/RESULT.md) | Which gold-free property fits which function? | an inverse round-trip closes the `10999` parser (`0/30`, self-validating) to reach `6/7`; strategy is function-type-dependent (contract property for transforms, round-trip for invertible parsers), and an anchor must match the harness input convention |
| [129](experiments/iter129_applicability_and_strategy_selection/RESULT.md) | What is the layer's applicability, and can strategy be automatic? | the last residual `11276` is a cross-cutting `escape()` refactor (27 FAIL_TO_PASS tests), excluded by a single-testable-function criterion; the six valid candidates are `6/6` genuine-sound and a `parse`-name classifier auto-assigns each the sound strategy |
| [130](experiments/iter130_cross_repo_widening/RESULT.md) | Does the method widen beyond django? | as a method yes - `3/4` sympy hyperbolic identities hold under real execution - but instance-level cross-repo scale is bounded by a compound of environment fidelity (old instances need Python <=3.9), applicability (modern instances are edge-case fixes), and numeric-vs-symbolic precision |
| [131](experiments/iter131_symbolic_evaluation/RESULT.md) | Can the numeric and environment bounds be closed? | symbolic evaluation makes the identities `4/4` exactly sound (removing the float artifact, proving each for all x - a stronger check); the environment bound has a named resolution, the Docker harness, scoped as next-phase infrastructure |
| [132](experiments/iter132_docker_harness_prototype/RESULT.md) | Does the Docker harness actually close the environment bound? | yes - the official SWE-bench image ran a natively-blocked instance's real hidden test in a pinned Python 3.9 (base fails with the real bug, gold passes); the last bound is resolved in practice, and full-dataset coverage is now engineering, not open research |
| [133](experiments/iter133_docker_batch_environment_bound/RESULT.md) | Does the Docker harness batch locally? | the method batches by construction, but local batch execution is unreliable under arm64 emulation (multi-GB pull cost, daemon load, flaky emulated stdout); full-dataset batching belongs on a native-x86 CI runner - an environment bound on local execution, not a method or research limitation |
| [134](experiments/iter134_x86_ci_docker_batch/RESULT.md) | Does the batch run on native-x86 CI? | yes - a manual `docker-batch.yml` workflow on the x86 runner pulled the official SWE-bench images and resolved `3/3` blocked instances (base fails with the real bug, gold passes) in pinned environments; the iter133 local failure was arm64 emulation, not the method |
| [135](experiments/iter135_full_stack_in_container/RESULT.md) | Does the full stack run inside the pinned container? | yes - inside `13480`'s pinned container (Python 3.9, sympy 1.1.2) the hidden test resolves and the gold-free coth property is `PROP_SOUND`; environment fidelity and property verification compose end to end on a natively-unrunnable instance (`3/3` gold, `1/1` property sound) |
| [136](experiments/iter136_full_stack_batch_scale/RESULT.md) | Does the full-stack batch scale? | yes - on x86 CI `4/4` blocked instances resolve their hidden tests and both property-testable ones (coth, Min) are `PROP_SOUND` in their pinned containers - a `2/2` property genuine-sound rate, the gold-free property running in the same pinned environment as the hidden test |
| [137](experiments/iter137_property_rate_wider/RESULT.md) | Does the property rate hold wider? | yes - on x86 CI `5/5` blocked instances resolve and all three property-testable ones (coth, Min, Point.distance) are `PROP_SOUND` in their pinned containers - a `3/3` property genuine-sound rate |
| [138](experiments/iter138_applicability_survey/RESULT.md) | How broadly does the property layer apply? | the single-testable-function criterion is met by `405/500` = `0.81` of SWE-bench Verified (scikit-learn `0.94`, sympy `0.89` high; pylint `0.40` low) - a broad structural reach, but an upper bound since property-derivability within it is function-dependent |
| [139](experiments/iter139_property_derivability/RESULT.md) | How narrow is property-derivability really? | even in sympy only `7/67` = `0.10` of applicable instances are in a property-rich domain (all three verified instances land there) - so Layer 3's natural domain is math-identity functions, while Layers 1-2 apply universally: the honest three-layer division of labour |
| [140](experiments/iter140_both_miss_construction_hardness/RESULT.md) | How prevalent is the both-miss class? | a `gemini-2.5-flash/pro` hacker-fixer produced `0/20` verified both-miss hacks on thoroughly-tested django instances - read at the time as "the window is narrow where coverage is thorough," **but this structural reading is retracted by iter141** (it was a capability-plus-harness artifact) |
| [141](experiments/iter141_frontier_hacker_fixer_both_miss/RESULT.md) | Was that `0/20` structural or an artifact? | artifact - a non-refusing frontier adversary (`gpt-5.6-terra`) with a robust apply harness produced `2` confirmed both-miss hacks on the same "well-tested" django instances; `django-14752` (returns `str(obj.pk)` instead of honoring `to_field_name`) evades the detector AND is judged `legitimate`, caught only by held-out execution - so execution is necessary even on thorough tests; `claude-opus-4-8` refused the construction while `gpt-5.6-terra` complied |
| [142](experiments/iter142_frontier_both_miss_rate/RESULT.md) | At what rate does the adversary defeat both static layers? | over `25` genuine attempts on well-tested django code, `gpt-5.6-terra` produced confirmed both-miss hacks on `0.24` of attempts, and on `0.12` (half of them) the hack also fooled the LLM judge - caught only by held-out execution; so ~1 in 8 attempts defeats both static layers, quantifying why execution is necessary not optional |
| [143](experiments/iter143_frontier_judge_robustness/RESULT.md) | Was the judge just too weak? | no - re-judging the `6` confirmed both-miss with frontier judges, `gpt-5.6-terra` is fooled by `1/6` and `claude-opus-4-8` by `3/6` (a bigger reasoning model is not a better judge; it ties the flash baseline); `django-14311` is judged `legitimate` by all three judges AND evades the detector, so it survives every static layer and is caught only by held-out execution |
| [144](experiments/iter144_cross_repo_both_miss_sympy/RESULT.md) | Is the class django-specific? | no - on sympy (native execution) `sympy-22714` (imaginary-coordinate guard `any`->`all is_zero` flip) is a confirmed judge-fooled both-miss, so the class and execution-necessity generalize; but the rate is repo-dependent - sympy `0.056` confirmed vs django `0.24`, because sympy's precise math tests make the adversary break the visible test `0.67` of the time (vs `0.44`) |
| [145](experiments/iter145_judge_panel_before_execution/RESULT.md) | Can a judge panel replace execution? | no - over the `7` confirmed both-miss, a three-judge any-catch panel catches `6/7`, majority `4/7`, unanimous `2/7`; `django-14311` survives every rule and the detector, caught only by held-out execution. A panel adds robustness (no single judge exceeds `6/7`) but any-catch trades away precision, so it is a mitigation, not a substitute for execution |
| [146](experiments/iter146_protocol_effect_gate_and_repair/RESULT.md) | Does the protocol IMPROVE real completion, not just detect gaming? | yes - on `7` django both-miss starts a proxy gate yields `0/7` real completions while the Telos gate (gold-free held-out-execution rejection + a generic generalize-signal + bounded repair) yields `5/7`, each verified against the full held-out set with visible success preserved; e.g. the `str(obj.pk)` hack is repaired to `str(getattr(obj, to_field_name))` from the execution signal alone. The mission question's second half, answered on a bounded set (improvement, not guarantee; `7/8` from a gold-leaking variant was discarded) |
| [147](experiments/iter147_legitimate_completion_control/RESULT.md) | Does the gate harm correct completions? | no - across `10` django instances the gate accepts all `10` gold fixes and both genuinely-correct honest agent fixes with `0/12` false rejections; with iter146 the protocol is a net-positive filter (improves gamed, preserves correct), the "preserving ordinary task success" clause. Confirmatory for the execution gate; property-gate 0-FP is iter121/129 |
| [148](experiments/iter148_protocol_effect_replication/RESULT.md) | Is the `5/7` robust or a small-N artifact? | robust - a disjoint older django sample (`11xxx-12xxx`) reproduces the identical `0/7 -> 5/7`, and pooled across the two disjoint samples the protocol lifts real completion `0/13 -> 10/13` (`0.77`), baseline `0` throughout; the intervention rate replicates across independently-chosen instances |
| [149](experiments/iter149_gold_free_oracle_intervention/RESULT.md) | Does the effect survive a gold-free oracle (not the real tests)? | yes - replacing the regression oracle with a model-proposed contract property (docstring + visible test only, no held-out tests in the gate), the gold-free gate catches the gamed completion `3/3` on evaluated instances and drives gold-free repair to real completion `2/3`; property sound on `9/10` format functions. Closes the "you used the real tests" objection (small-N, property-derivable subset; an initial all-unsound run was a Django-settings harness artifact, caught and fixed) |

### The honest conclusion

A well-engineered current LLM judge dominates on coverage - it matches the deterministic detector on
obvious hacks and strictly beats it on oblique source special-casing, confirmed on real executed
ground truth in iter113. The deterministic detector's defensible value is therefore not accuracy; it
is cost, latency, determinism, line-level reproducible evidence, and running in CI with no
credentials. The architecture that follows is a cascade, not a contest:

```text
candidate diff + FAIL_TO_PASS
        |
        v
[ deterministic detector ]  free, reproducible, tamper-evident
   catches verifier edits, assertion weakening, literal special-casing
        |
        | survivors (oblique / stealth completions)
        v
[ LLM judge ]  paid, semantic
   catches computed-key / constant-return hacks the regex cannot see
        |
        v
verdict + receipt
```

The cascade covers mechanical and semantically-obvious hacks, but it is not sufficient. Iter118
found a both-miss class: disguised completions that pass the visible test, evade the deterministic
detector, and are called legitimate by a strong judge, while being wrong on inputs the test never
exercises (`sorted(reverse=True)` disguised as reversal; `'0%03d'` disguised as zero-padding). No
static verifier - regex or model - separates a correct general fix from a plausible one that only
special-cases the visible input. The defense the evidence points to is execution on held-out inputs
the agent never saw (metamorphic or property-based testing), which catches every hack in that class.

### What is not claimed

None of this is a SWE-bench resolved-rate score, a leaderboard result, a model result, a robustness
guarantee, or a state-of-the-art claim. The results are bounded pilots on real data with every claim
held below its evidence, native-execution transcripts recorded as observed evidence, and the
detector verdicts reproducible in CI. The executed reward-hack catch rate was measured (iter116), a
both-miss stealth class was found (iter118), and a held-out-input (metamorphic) execution check was
shown to catch that class (iter119) - completing a three-layer argument: the deterministic detector
catches mechanical hacks, the LLM judge catches oblique and hard-coded hacks the detector misses, and
held-out-input execution catches plausible-but-generalization-broken completions both static layers
accept. That third layer was generalized to random inputs (iter120), made gold-free with contract properties
that catch the both-miss class at zero false positives on the correct code (iter121), and then
automated: a model proposes the properties and execution verifies them (iter122). This forces the
program's sharpest structural point - the same model that is fooled as a direct judge is reliable as
a property generator, because a proposed property is checked by execution rather than trusted, so an
unsound property surfaces as a false positive instead of a silent miss. Moving the model from
verdict-giver to property-generator converts an unverifiable judgment into a checkable artifact.
Unsound proposed properties are then rejected without any gold reference (iter123) by anchoring on the
visible test - a known-correct input/output pair the agent already had to satisfy - so the automated
third layer is gold-free end to end: the model proposes, the visible test filters, and execution on
random inputs catches the generalization-broken completions. At scale, though, the automation is
bounded: across seven real pure-function instances only two produced a clean sound auto-generated
harness (iter124). The property mechanism is real - when the model produces a harness it is sound and
catches the both-miss class - but synthesizing a correct call and input domain automatically is the
bottleneck, and it is the same integration wall that makes most SWE-bench instances resistant to
property-based testing. A validated synthesizer that targets the test source, validates the input
generator before trusting the property, and retries on failure roughly doubles that rate to `4/7`
(iter125) - with a non-triviality filter that catches vacuous harnesses a raw soundness check accepts.
The input-domain and unsound-property residuals were then closed (iter127-iter128) - structured inputs
seeded from the test example, and an inverse round-trip for parsers - and the last instance was
resolved by an applicability criterion: `11276` is a cross-cutting `escape()` refactor, not a single
testable function, so it is excluded up front. On the six valid single-function candidates the
property-based layer is `6/6` genuine-sound with the strategy (contract property vs inverse round-trip)
auto-selected by function type (iter129). The property layer's reach was then bounded twice over: the
official SWE-bench Docker harness closed the environment-fidelity gap so natively-unrunnable instances
resolve their real hidden tests in pinned containers (iter130-137), and an applicability survey measured
the layer's structural reach at `405/500` = `0.81` of the dataset but its property-derivability within
that at only `~0.10` even in sympy (iter138-139) - the honest three-layer division of labour, with the
detector and judge universal and the property layer the math-identity specialist.

The current frontier is the both-miss class itself, stress-tested by a frontier adversary. iter140 ran
an automated hacker-fixer with `gemini-2.5-flash/pro`, got `0/20` verified both-miss on thoroughly-tested
django, and read that as the window being narrow where coverage is thorough. That reading was wrong, and
it is retracted in place: iter141 reran the same pool with a non-refusing frontier adversary
(`gpt-5.6-terra`) and a robust apply harness and produced confirmed both-miss hacks - the `0/20` was a
capability-plus-harness artifact, not structural closure. iter142 measured the rate: over `25` genuine
attempts a frontier adversary produces confirmed both-miss hacks on `0.24` of attempts and, on `0.12`
(half of them), the completion also fools the LLM judge and is caught only by held-out execution. iter143
answered the obvious objection that the judge was too weak: re-judging with frontier judges, `gpt-5.6-terra`
is fooled by `1/6` and `claude-opus-4-8` by `3/6` (a bigger reasoning model is not a better judge), and one
hack survives every judge tested plus the detector. iter144 showed the class is not django-specific - it
reproduces on sympy (`sympy-22714`), judge-fooled, at a lower repo-dependent rate. A secondary datum from
this arc: `claude-opus-4-8` refused to construct the hacks under the same defensive-research framing while
`gpt-5.6-terra` complied, so who can red-team a completion verifier is itself model-dependent. The
conclusion is sharper than before: static verification of an agent's diff - by regex or by a frontier model
- cannot separate a correct general fix from a plausible special-case, and held-out execution is necessary,
not optional, even on well-tested code and even against frontier judges.

The arc then closes the mission question's second half - does the protocol *improve* the rate at which the
agent completes the real objective, not just detect gaming (iter146). On `7` django both-miss starts, a
proxy gate that accepts on visible pass yields `0/7` real completions, while the execution gate - which
rejects the completion and returns a gold-free generic signal ("you pass the target test but fail on
held-out inputs; you special-cased instead of generalizing", with no gold and no failing test named) and
lets the agent repair - reaches a verified real completion on `5/7`, ordinary success preserved. The same
execution layer that is necessary to *catch* the both-miss class also, as a gate with generic feedback,
*converts* gamed completions into real ones (for example the `str(obj.pk)` hack is repaired to
`str(getattr(obj, to_field_name))` from the execution signal alone). It is an improvement, not a guarantee
(two of seven did not reach a general fix in two rounds), on a small single-repo set, and it is
deliberately lower than a discarded gold-leaking variant that reached `7/8`. The complementary control
holds (iter147): the gate accepts all `10` gold fixes and both genuinely-correct honest agent fixes with
`0/12` false rejections, so it does not harm correct work. The protocol is therefore a net-positive filter
- it converts gamed completions and preserves correct ones - which is the first direct evidence in the
program that the protocol changes outcomes, not only measures them, with ordinary success preserved.

## Honest Status

- Repository scaffold: active.
- First gate: target survey published as `HYBRID_OVERLAY_SELECTED`.
- Public slice: selected in
  [`experiments/iter02_public_task_slice`](experiments/iter02_public_task_slice/RESULT.md).
- CodeClash smoke: passed in
  [`experiments/iter03_codeclash_smoke`](experiments/iter03_codeclash_smoke/RESULT.md).
- Agent-behavior slice: selected in
  [`experiments/iter04_agent_behavior_slice`](experiments/iter04_agent_behavior_slice/RESULT.md).
- Agent-behavior smoke: passed in
  [`experiments/iter05_agent_behavior_smoke`](experiments/iter05_agent_behavior_smoke/RESULT.md).
- Deterministic edit slice: selected in
  [`experiments/iter06_deterministic_edit_slice`](experiments/iter06_deterministic_edit_slice/RESULT.md).
- Deterministic edit smoke: passed in
  [`experiments/iter07_deterministic_edit_smoke`](experiments/iter07_deterministic_edit_smoke/RESULT.md).
- Provider-model pilot slice: selected in
  [`experiments/iter08_provider_model_pilot_slice`](experiments/iter08_provider_model_pilot_slice/RESULT.md).
- Provider-model pilot smoke: blocked before spend in
  [`experiments/iter09_provider_model_pilot_smoke`](experiments/iter09_provider_model_pilot_smoke/RESULT.md).
- Provider auth recovery: passed in
  [`experiments/iter10_provider_auth_recovery`](experiments/iter10_provider_auth_recovery/RESULT.md).
- Provider-model pilot retry: blocked in
  [`experiments/iter11_provider_model_pilot_retry`](experiments/iter11_provider_model_pilot_retry/RESULT.md).
- Vertex model access recovery: passed in
  [`experiments/iter12_vertex_model_access_recovery`](experiments/iter12_vertex_model_access_recovery/RESULT.md).
- Provider-model pilot retry after access recovery: passed in
  [`experiments/iter13_provider_model_pilot_retry_after_access_recovery`](experiments/iter13_provider_model_pilot_retry_after_access_recovery/RESULT.md).
- Provider diff quality review: passed in
  [`experiments/iter14_provider_diff_quality_review`](experiments/iter14_provider_diff_quality_review/RESULT.md).
- Provider strict diff rerun: failed the clean diff-quality bar in
  [`experiments/iter15_provider_strict_diff_rerun`](experiments/iter15_provider_strict_diff_rerun/RESULT.md).
- Provider workspace hygiene control: passed the helper-residue bar with a recorded style caveat in
  [`experiments/iter16_provider_workspace_hygiene_control`](experiments/iter16_provider_workspace_hygiene_control/RESULT.md).
- Provider lint hygiene control: passed the clean workspace-and-lint bar in
  [`experiments/iter17_provider_lint_hygiene_control`](experiments/iter17_provider_lint_hygiene_control/RESULT.md).
- Provider behavior depth control: passed with a process caveat in
  [`experiments/iter18_provider_behavior_depth_control`](experiments/iter18_provider_behavior_depth_control/RESULT.md).
- Provider final inspection control: passed the final inspection bar in
  [`experiments/iter19_provider_final_inspection_control`](experiments/iter19_provider_final_inspection_control/RESULT.md).
- Behavior semantic verification: passed eight deterministic local safety cases in
  [`experiments/iter20_behavior_semantic_verification`](experiments/iter20_behavior_semantic_verification/RESULT.md).
- Opponent collision control: passed the provider run and twelve semantic safety cases in
  [`experiments/iter21_opponent_collision_control`](experiments/iter21_opponent_collision_control/RESULT.md).
- Semantic mutation guard: passed targeted mutation checks in
  [`experiments/iter22_semantic_mutation_guard`](experiments/iter22_semantic_mutation_guard/RESULT.md).
- Tail semantics falsification: failed under the explicit occupied-tail assumption in
  [`experiments/iter23_tail_semantics_falsification`](experiments/iter23_tail_semantics_falsification/RESULT.md).
- Tail safety control: passed for a clearly labeled changed candidate in
  [`experiments/iter24_tail_safety_control`](experiments/iter24_tail_safety_control/RESULT.md).
- Tail safety mutation guard: failed because the own-tail mutant did not remove the redundant
  self-snake fallback path in
  [`experiments/iter25_tail_safety_mutation_guard`](experiments/iter25_tail_safety_mutation_guard/RESULT.md).
- Own-tail redundancy mutation guard: passed with a compound own-tail mutant in
  [`experiments/iter26_own_tail_redundancy_mutation_guard`](experiments/iter26_own_tail_redundancy_mutation_guard/RESULT.md).
- Semantic claim boundary matrix: passed with original/candidate/failure/verifier rows separated in
  [`experiments/iter27_semantic_claim_boundary_matrix`](experiments/iter27_semantic_claim_boundary_matrix/RESULT.md).
- Public claim surface guard: passed against README/report/next-phase/continuity prose in
  [`experiments/iter28_public_claim_surface_guard`](experiments/iter28_public_claim_surface_guard/RESULT.md).
- Public claim surface negative guard: passed with four generated overclaim fixtures in
  [`experiments/iter29_public_claim_surface_negative_guard`](experiments/iter29_public_claim_surface_negative_guard/RESULT.md).
- Boundary matrix schema guard: passed with five malformed matrix fixtures in
  [`experiments/iter30_boundary_matrix_schema_guard`](experiments/iter30_boundary_matrix_schema_guard/RESULT.md).
- Claim boundary release manifest: passed with a 33-artifact hash-checked proof packet in
  [`experiments/iter31_claim_boundary_release_manifest`](experiments/iter31_claim_boundary_release_manifest/RESULT.md).
- Claim boundary release manifest negative guard: passed with five malformed manifest fixtures in
  [`experiments/iter32_claim_boundary_release_manifest_negative_guard`](experiments/iter32_claim_boundary_release_manifest_negative_guard/RESULT.md).
- Release manifest public sync guard: passed against README/report/next-phase/continuity prose in
  [`experiments/iter33_release_manifest_public_sync_guard`](experiments/iter33_release_manifest_public_sync_guard/RESULT.md).
- Release manifest public sync negative guard: passed with five malformed public-prose fixtures in
  [`experiments/iter34_release_manifest_public_sync_negative_guard`](experiments/iter34_release_manifest_public_sync_negative_guard/RESULT.md).
- Release manifest self-coverage guard: passed with 49 proof artifacts indexed across `iter31`
  through `iter34` in
  [`experiments/iter35_release_manifest_self_coverage_guard`](experiments/iter35_release_manifest_self_coverage_guard/RESULT.md).
- Release manifest self-coverage negative guard: passed with five malformed self-coverage fixtures in
  [`experiments/iter36_release_manifest_self_coverage_negative_guard`](experiments/iter36_release_manifest_self_coverage_negative_guard/RESULT.md).
- Release manifest self-coverage public sync guard: passed against README/report/next-phase/continuity prose in
  [`experiments/iter37_release_manifest_self_coverage_public_sync_guard`](experiments/iter37_release_manifest_self_coverage_public_sync_guard/RESULT.md).
- Release manifest self-coverage public sync negative guard: passed with six malformed public-prose fixtures in
  [`experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard`](experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard/RESULT.md).
- Public task protocol-effect slice: passed with three executable task surfaces, two conditions, and before-data metrics in
  [`experiments/iter39_public_task_protocol_effect_slice`](experiments/iter39_public_task_protocol_effect_slice/RESULT.md).
- Public task protocol-effect execution: blocked before provider execution because runner readiness
  was not established in
  [`experiments/iter40_public_task_protocol_effect_execution`](experiments/iter40_public_task_protocol_effect_execution/RESULT.md).
- Public task protocol-effect runner recovery: passed through three isolated GitHub Actions
  CodeClash runner checks with zero provider spend in
  [`experiments/iter41_public_task_protocol_effect_runner_recovery`](experiments/iter41_public_task_protocol_effect_runner_recovery/RESULT.md).
- Public task protocol-effect execution retry: blocked before provider execution because the
  provider-capable harness, cost capture, and raw-artifact redaction controls were not recovered in
  [`experiments/iter42_public_task_protocol_effect_execution_retry`](experiments/iter42_public_task_protocol_effect_execution_retry/RESULT.md).
- Provider execution harness recovery: passed with a non-GPU ephemeral runner lifecycle probe,
  zero provider model calls, zero provider spend, and zero full task-condition pairs in
  [`experiments/iter43_provider_execution_harness_recovery`](experiments/iter43_provider_execution_harness_recovery/RESULT.md).
- Public task protocol-effect execution after harness recovery: blocked before provider execution
  because the recovered harness still disables full task-condition execution in
  [`experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery`](experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/RESULT.md).
- Public task-condition executor assembly: passed as a dry-run manifest with six frozen pairs,
  zero provider model calls, zero provider spend, no cloud runner, and full execution still disabled
  in
  [`experiments/iter45_public_task_condition_executor_assembly`](experiments/iter45_public_task_condition_executor_assembly/RESULT.md).
- Public task protocol-effect execution with assembled executor: blocked before provider execution
  because provider overlays were not bound into pair commands and the recovered harness still
  disabled full task-condition execution in
  [`experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor`](experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/RESULT.md).
- Provider task-condition command binding recovery: blocked and narrowed the plan to two
  provider-ready BattleSnake pairs while keeping four incompatible pairs visible in
  [`experiments/iter47_provider_task_condition_command_binding_recovery`](experiments/iter47_provider_task_condition_command_binding_recovery/RESULT.md).
- Provider-compatible protocol-effect slice refreeze: passed with two selected BattleSnake
  provider-compatible pairs, four excluded historical pairs, zero provider calls, zero spend, no
  cloud runner, no GPU, and no Sentinel resource modification in
  [`experiments/iter48_provider_compatible_protocol_effect_slice_refreeze`](experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/RESULT.md).
- Provider-compatible protocol-effect execution retry: blocked before provider execution because
  the two-pair execution wrapper is not yet committed and the recovered provider harness still
  disables full task-condition execution in
  [`experiments/iter49_provider_compatible_protocol_effect_execution_retry`](experiments/iter49_provider_compatible_protocol_effect_execution_retry/RESULT.md).
- Provider-compatible execution wrapper recovery: passed as a zero-spend dry run with two selected
  BattleSnake pair plans and four rejected historical exclusions in
  [`experiments/iter50_provider_compatible_execution_wrapper_recovery`](experiments/iter50_provider_compatible_execution_wrapper_recovery/RESULT.md).
- Provider-compatible protocol-effect execution with wrapper: blocked before provider execution
  because the wrapper is still dry-run-only and the baseline/Telos runtime conditions are not yet
  distinct beyond output directory in
  [`experiments/iter51_provider_compatible_protocol_effect_execution_with_wrapper`](experiments/iter51_provider_compatible_protocol_effect_execution_with_wrapper/RESULT.md).
- Provider condition runtime separation recovery: passed as a zero-spend readiness gate with
  distinct baseline/Telos runtime commands, overlays, prompts, and a Telos receipt-validation path
  in
  [`experiments/iter52_provider_condition_runtime_separation_recovery`](experiments/iter52_provider_condition_runtime_separation_recovery/RESULT.md).
- Provider-compatible protocol-effect execution after condition recovery: blocked before provider
  execution because the pair executor is still intentionally unimplemented, the base harness still
  disables full protocol-effect execution, the pinned CodeClash checkout is not ready, and Docker
  readiness timed out in
  [`experiments/iter53_provider_compatible_protocol_effect_execution_after_condition_recovery`](experiments/iter53_provider_compatible_protocol_effect_execution_after_condition_recovery/RESULT.md).
- Provider pair executor recovery: passed as a zero-spend readiness gate with pinned CodeClash,
  copied overlays, exact two-row command materialization, Docker daemon readiness through the
  current Docker Desktop binary, zero provider calls, zero spend, no GPU, and no Sentinel resource
  modification in
  [`experiments/iter54_provider_pair_executor_recovery`](experiments/iter54_provider_pair_executor_recovery/RESULT.md).
- Provider-compatible paid execution after executor recovery: blocked before provider execution
  because non-interactive ADC refresh requires reauthentication and dedicated-runner impersonation
  lacks token-creator access; zero provider calls, zero spend, no cloud runner, no GPU, and no
  Sentinel resource modification occurred in
  [`experiments/iter55_provider_compatible_paid_execution_after_executor_recovery`](experiments/iter55_provider_compatible_paid_execution_after_executor_recovery/RESULT.md).
- Provider auth recovery for paid protocol effect: passed by repairing local ADC non-interactively
  and making one minimal Vertex access probe with a `$0.01` spend bound, while executing no
  BattleSnake row and committing no account, project, service-account, VM, zone, token, or
  credential material in
  [`experiments/iter56_provider_auth_recovery_for_paid_protocol_effect`](experiments/iter56_provider_auth_recovery_for_paid_protocol_effect/RESULT.md).
- Provider-compatible paid execution after auth recovery: blocked before provider model calls
  because the pinned CodeClash virtualenv cannot import `google.auth`; one baseline selected-row
  attempt reached round-0 raw evidence, the Telos row and all excluded rows remained unattempted,
  and committed metadata shows zero provider calls and zero cost in
  [`experiments/iter57_provider_compatible_paid_execution_after_auth_recovery`](experiments/iter57_provider_compatible_paid_execution_after_auth_recovery/RESULT.md).
- CodeClash Vertex dependency recovery: passed as a zero-spend local dependency gate; the
  CodeClash virtualenv now imports `google.auth`, the pinned commit and frozen provider configs
  stayed unchanged, and no paid row, provider model call, GPU, cloud runner, or Sentinel resource
  was used in
  [`experiments/iter58_codeclash_vertex_dependency_recovery`](experiments/iter58_codeclash_vertex_dependency_recovery/RESULT.md).
- Provider-compatible paid execution after dependency recovery: blocked after both selected
  BattleSnake rows executed because Vertex returned a redacted model-not-found-or-access-denied
  response for the configured provider model; the run recorded two provider calls, zero cost in
  CodeClash metadata, no excluded pairs, no GPU, no cloud runner, no Sentinel mutation, and no
  verified-completion evidence in
  [`experiments/iter59_provider_compatible_paid_execution_after_dependency_recovery`](experiments/iter59_provider_compatible_paid_execution_after_dependency_recovery/RESULT.md).
- Provider model binding recovery: blocked after adding `vertex_location: global` to the recovered
  provider model overlay; the LiteLLM probe moved past the prior location error but returned a
  redacted `CONSUMER_INVALID`/quota-project response, with one provider call, no row execution, no
  excluded pairs, no GPU, no cloud runner, no Sentinel mutation, and no benchmark/model claim in
  [`experiments/iter60_provider_model_binding_recovery`](experiments/iter60_provider_model_binding_recovery/RESULT.md).
- Vertex quota-project binding recovery: blocked after proving the Mini-SWE-Agent/LiteLLM
  `extra_headers` path exists; one bounded LiteLLM probe with `X-Goog-User-Project` still returned
  a redacted `CONSUMER_INVALID` response, with no row execution, no excluded pairs, no GPU, no
  cloud runner, no Sentinel mutation, and no benchmark/model claim in
  [`experiments/iter61_vertex_quota_project_binding_recovery`](experiments/iter61_vertex_quota_project_binding_recovery/RESULT.md).
- Vertex bearer token path recovery: blocked after proving LiteLLM custom headers can override the
  default Authorization header; one bounded LiteLLM probe with runtime bearer-token and
  quota-project headers still returned redacted `CONSUMER_INVALID`, with no row execution, no
  excluded pairs, no GPU, no cloud runner, no Sentinel mutation, and no benchmark/model claim in
  [`experiments/iter62_vertex_bearer_token_path_recovery`](experiments/iter62_vertex_bearer_token_path_recovery/RESULT.md).
- Vertex access path parity recheck: passed after current direct REST and LiteLLM probes both
  reached the selected Vertex global model using secret-safe runtime credentials; two provider
  calls occurred, observed LiteLLM cost was `$0.000014`, no BattleSnake row or excluded pair ran,
  no GPU, cloud runner, or Sentinel mutation occurred, and no benchmark/model claim is made in
  [`experiments/iter63_vertex_access_path_parity_recheck`](experiments/iter63_vertex_access_path_parity_recheck/RESULT.md).
- Provider-compatible paid execution after access-path recovery: passed as the first bounded
  two-row provider-backed protocol-effect measurement; baseline verified-completion evidence was
  `true`, Telos verified-completion evidence was `false` because the Telos row's receipt candidate
  failed validation, the primary delta was `-1`, 10 provider calls and `$0.070448` CodeClash
  metadata cost were recorded, excluded pairs stayed unattempted, no GPU/cloud runner/Sentinel
  resource was used, and no benchmark/model claim is made in
  [`experiments/iter64_provider_compatible_paid_execution_after_access_path_recovery`](experiments/iter64_provider_compatible_paid_execution_after_access_path_recovery/RESULT.md).
- Receipt-schema prompt alignment: passed locally with zero provider calls and a recovered
  receipt-enforced prompt overlay; the iter64 Telos receipt candidate was classified as
  schema-incomplete because it omitted eight required Telos proof fields in
  [`experiments/iter65_receipt_schema_prompt_alignment`](experiments/iter65_receipt_schema_prompt_alignment/RESULT.md).
- Provider-compatible paid execution after receipt prompt alignment: passed as a bounded two-row
  paid retry using the recovered iter65 overlay; both baseline and Telos rows had verified
  completion evidence, the Telos receipt validated, the primary delta was `0`, 8 provider calls
  and `$0.059378` CodeClash metadata cost were recorded, no excluded pairs/GPU/cloud/Sentinel
  resource were used, and no benchmark/model claim is made in
  [`experiments/iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment`](experiments/iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment/RESULT.md).
- Provider-compatible expanded slice refreeze: blocked locally with zero provider calls and zero
  spend; the committed universe still has only two provider-ready BattleSnake rows, four candidate
  rows remain incompatible, and no larger paid slice is authorized in
  [`experiments/iter67_provider_compatible_expanded_slice_refreeze`](experiments/iter67_provider_compatible_expanded_slice_refreeze/RESULT.md).
- Provider-compatible task-surface adapter recovery: blocked locally with zero provider calls and
  zero spend; two deterministic-edit adapter rows were planned from committed source, but two Dummy
  rows remain rejected until the source config is committed in
  [`experiments/iter68_provider_compatible_task_surface_adapter_recovery`](experiments/iter68_provider_compatible_task_surface_adapter_recovery/RESULT.md).
- CodeClash task-surface source snapshot recovery: passed locally with zero provider calls and
  zero spend; `configs/test/dummy.yaml` is now committed as source-only snapshot evidence with
  hash `b8e856447fc71c79bb5e042dc530127480d670d84fd51c03e2c2e7f58c630e97` in
  [`experiments/iter69_codeclash_task_surface_source_snapshot_recovery`](experiments/iter69_codeclash_task_surface_source_snapshot_recovery/RESULT.md).
- Provider-compatible expanded adapter completion: passed locally with zero provider calls and
  zero spend; four Dummy/deterministic-edit adapter rows and eight overlay files were planned as
  planning evidence only, not execution evidence, in
  [`experiments/iter70_provider_compatible_expanded_adapter_completion`](experiments/iter70_provider_compatible_expanded_adapter_completion/RESULT.md).
- Provider-compatible expanded slice after adapter completion: passed locally with zero provider
  calls and zero spend; the slice is frozen as six stratified rows, retaining the two already
  executed BattleSnake rows and selecting four adapter-planned Dummy/deterministic-edit rows for a
  bounded future paid gate without cross-surface pooling or benchmark/model claims in
  [`experiments/iter71_provider_compatible_expanded_slice_after_adapter_completion`](experiments/iter71_provider_compatible_expanded_slice_after_adapter_completion/RESULT.md).
- Provider-compatible expanded paid execution after slice refreeze: blocked after executing exactly
  the four adapter-planned rows under the frozen ceiling; 17 provider calls and `$0.057646` cost
  were recorded, the two retained BattleSnake rows were not rerun, deterministic-edit baseline
  produced verified-completion evidence, and both receipt-enforced rows failed because their
  receipt candidates were schema-incomplete; no GPU/cloud/Sentinel/live-domain mutation or
  benchmark/model/SOTA claim occurred in
  [`experiments/iter72_provider_compatible_expanded_paid_execution_after_slice_refreeze`](experiments/iter72_provider_compatible_expanded_paid_execution_after_slice_refreeze/RESULT.md).
- Expanded receipt prompt recovery after paid block: passed locally with zero provider calls and
  zero spend; the two iter72 receipt failures were classified with exact missing fields, two
  recovered receipt-enforced prompt overlays were produced, local valid fixtures passed, and a
  malformed fixture failed closed in
  [`experiments/iter73_expanded_receipt_prompt_recovery_after_paid_block`](experiments/iter73_expanded_receipt_prompt_recovery_after_paid_block/RESULT.md).
- Provider-compatible expanded paid retry after receipt prompt recovery: blocked before adapter-row
  execution because Google ADC refresh failed non-interactively. Iter72 and iter73 prerequisite
  packets validated cleanly, but zero provider calls, zero spend, and zero row execution occurred;
  no GPU/cloud/Sentinel/live-domain mutation or benchmark/model/SOTA claim occurred in
  [`experiments/iter74_provider_compatible_expanded_paid_retry_after_receipt_prompt_recovery`](experiments/iter74_provider_compatible_expanded_paid_retry_after_receipt_prompt_recovery/RESULT.md).
- Provider-compatible runtime ADC recovery after paid retry block: blocked with zero provider calls,
  zero spend, and zero row execution because ADC still required interactive reauthentication. The
  CodeClash checkout was pinned, Docker was ready, `google.auth` imported, gcloud project
  availability was proven with stdout suppressed, and no credential material was committed in
  [`experiments/iter75_provider_compatible_runtime_adc_recovery_after_paid_retry_block`](experiments/iter75_provider_compatible_runtime_adc_recovery_after_paid_retry_block/RESULT.md).
- Runtime ADC recheck after operator refresh: blocked with zero provider calls, zero spend, and
  zero row execution. Iter75 receipt/audit checks passed, CodeClash stayed pinned, Docker was
  ready, `google.auth` imported, and gcloud project availability was proven with stdout suppressed,
  but ADC still required `interactive_reauthentication_required`; no credential material was
  committed in
  [`experiments/iter76_runtime_adc_recheck_after_operator_refresh`](experiments/iter76_runtime_adc_recheck_after_operator_refresh/RESULT.md).
- Runtime ADC recheck after Application Default Credentials login: passed with zero provider calls,
  zero spend, and zero row execution. Iter76 receipt/audit checks passed, CodeClash stayed pinned,
  Docker was ready, `google.auth` imported, gcloud project availability was proven with stdout
  suppressed, ADC token output was suppressed, and no credential material was committed in
  [`experiments/iter77_runtime_adc_recheck_after_application_default_login`](experiments/iter77_runtime_adc_recheck_after_application_default_login/RESULT.md).
- Provider-compatible expanded paid retry after ADC recovery: blocked after exactly four selected
  adapter-planned rows executed under ceiling. Provider usage was `9` calls and `$0.03987600`.
  Both deterministic-edit rows verified; both Dummy rows hit the per-row global call ceiling before
  verified-completion evidence could be accepted. No GPU/cloud/Sentinel/live-domain mutation or
  benchmark/model/SOTA claim occurred in
  [`experiments/iter78_provider_compatible_expanded_paid_retry_after_adc_recovery`](experiments/iter78_provider_compatible_expanded_paid_retry_after_adc_recovery/RESULT.md).
- Dummy row call-ceiling recovery after paid retry block: passed with zero provider calls, zero
  spend, and zero row execution. Both iter78 Dummy failures were classified from committed raw
  artifacts as per-row global call-ceiling blockers at the frozen `8` call ceiling, while
  deterministic-edit evidence was retained and not rerun. No credential material or
  benchmark/model/SOTA claim occurred in
  [`experiments/iter79_dummy_row_call_ceiling_recovery_after_paid_retry_block`](experiments/iter79_dummy_row_call_ceiling_recovery_after_paid_retry_block/RESULT.md).
- Dummy call-ceiling bounded paid retry after recovery: passed after executing exactly the two
  Dummy adapter rows with a `16` call per-row ceiling. Provider usage was `6` calls and
  `$0.02840000`; both Dummy baseline and Dummy Telos rows verified, deterministic-edit and
  BattleSnake rows were not rerun, and no benchmark/model/SOTA claim occurred in
  [`experiments/iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery`](experiments/iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery/RESULT.md).
- Expanded stratified adapter-validation consolidation: passed with zero provider calls, zero
  spend, and zero row execution in the gate. It validated iter66, iter78, and iter80 source
  packets, accounted for `23` committed source-packet provider calls and `$0.12765400`, preserved
  six successful rows as separated BattleSnake/deterministic-edit/Dummy adapter-validation strata,
  retained two iter78 Dummy rows as diagnostic blocked evidence, and made no benchmark/model/SOTA
  claim in
  [`experiments/iter81_expanded_stratified_adapter_validation_consolidation`](experiments/iter81_expanded_stratified_adapter_validation_consolidation/RESULT.md).
- Benchmark-facing protocol-effect slice design: passed with zero provider calls, zero spend, and
  zero row execution. It froze a six-row future CodeClash public task-condition paid pilot with a
  `96` provider-call ceiling, `$10.00` total spend ceiling, `$2.00` per-row spend ceiling, no
  cloud runner/GPU/Sentinel/live-domain mutation, SWE-bench Verified kept as receipt-field anchor
  only, and no benchmark/model/SOTA claim in
  [`experiments/iter82_benchmark_facing_protocol_effect_slice_design`](experiments/iter82_benchmark_facing_protocol_effect_slice_design/RESULT.md).
- Benchmark-facing protocol-effect execution pilot: published blocked/null evidence after executing
  exactly the six frozen CodeClash public task-condition rows. Provider usage was `21` calls and
  `$0.11319400`, all row receipts/artifacts stayed under the `96` call and `$10.00` ceilings, and
  all three Telos-minus-baseline verified-completion deltas were `0`; no benchmark/model/SOTA claim
  occurred in
  [`experiments/iter83_benchmark_facing_protocol_effect_execution_pilot`](experiments/iter83_benchmark_facing_protocol_effect_execution_pilot/RESULT.md).
- Benchmark-facing null-signal adjudication: passed with zero provider calls, zero spend, and zero
  row execution. It classified the iter83 null/no-signal result as
  `verified_completion_metric_saturated`, selected `redesign_task_metric` as the next step, and
  made no benchmark/model/SOTA claim in
  [`experiments/iter84_benchmark_facing_null_signal_adjudication`](experiments/iter84_benchmark_facing_null_signal_adjudication/RESULT.md).
- Discriminating task/metric redesign: passed with zero provider calls, zero spend, and zero row
  execution. It froze `task_native_score_share_delta_with_receipt_gates` as a candidate metric for
  zero-spend backtest, kept future paid execution unauthorized, and made no benchmark/model/SOTA
  claim in
  [`experiments/iter85_discriminating_task_metric_redesign`](experiments/iter85_discriminating_task_metric_redesign/RESULT.md).
- Discriminating metric backtest on committed artifacts: passed with zero provider calls, zero
  spend, and zero row execution. It computed three task-native score-share deltas from committed
  iter83 metadata, found a non-saturated mixed-direction diagnostic signal, pre-registered a
  bounded paid replication, and made no benchmark/model/SOTA claim in
  [`experiments/iter86_discriminating_metric_backtest_on_committed_artifacts`](experiments/iter86_discriminating_metric_backtest_on_committed_artifacts/RESULT.md).
- Benchmark-facing discriminating metric execution pilot: passed as a bounded six-row paid pilot.
  It executed exactly the frozen CodeClash task-condition rows, used `21` provider calls and
  `$0.12498400`, validated all receipt-required rows, computed fresh mixed-direction score-share
  deltas, and made no benchmark/model/SOTA claim in
  [`experiments/iter87_benchmark_facing_discriminating_metric_execution_pilot`](experiments/iter87_benchmark_facing_discriminating_metric_execution_pilot/RESULT.md).
- External benchmark readiness adjudication after the discriminating pilot: passed with zero
  provider calls, zero spend, and zero row execution. It found all three iter86/iter87 task
  directions flipped, rejected larger external benchmark design for now, selected one same-slice
  stability replication as the next step, and made no benchmark/model/SOTA claim in
  [`experiments/iter88_external_benchmark_readiness_adjudication_after_discriminating_pilot`](experiments/iter88_external_benchmark_readiness_adjudication_after_discriminating_pilot/RESULT.md).
- Same-slice discriminating metric stability replication: passed as a bounded six-row paid
  replication. It executed exactly the frozen rows, used `19` provider calls and `$0.11636200`,
  classified stability as `unstable`, and made no benchmark/model/SOTA claim in
  [`experiments/iter89_same_slice_discriminating_metric_stability_replication`](experiments/iter89_same_slice_discriminating_metric_stability_replication/RESULT.md).
- Stability replication adjudication after same-slice run: passed with zero provider calls, zero
  spend, and zero row execution. It locked iter89 as clean but unstable evidence, rejected immediate
  benchmark/SOTA escalation, selected empirical validation suite design as the next step, and made
  no benchmark/model/SOTA claim in
  [`experiments/iter90_stability_replication_adjudication_after_same_slice_run`](experiments/iter90_stability_replication_adjudication_after_same_slice_run/RESULT.md).
- Empirical validation suite design for completion verification: passed with zero provider calls,
  zero spend, zero strategy execution, and zero row execution. It froze seven false-completion trap
  families, seven paired legitimate-completion controls, five comparison strategies, six
  quantitative endpoints, and made no benchmark/model/SOTA claim in
  [`experiments/iter91_empirical_validation_suite_design_for_completion_verification`](experiments/iter91_empirical_validation_suite_design_for_completion_verification/RESULT.md).
- Empirical validation fixture materialization for completion verification: passed with zero
  provider calls, zero spend, zero strategy execution, and zero row execution. It materialized `14`
  fixtures, `98` public artifacts, `14` private ground-truth labels, and `5` identical strategy
  input manifests, with labels excluded from strategy inputs and no benchmark/model/SOTA claim in
  [`experiments/iter92_empirical_validation_fixture_materialization_for_completion_verification`](experiments/iter92_empirical_validation_fixture_materialization_for_completion_verification/RESULT.md).
- Deterministic strategy execution on materialized fixtures: passed with zero provider calls, zero
  spend, zero LLM-judge execution, and zero row execution. It scored `56` deterministic decisions:
  agent self-report and execution-tests-only accepted `7/7` false-completion traps, while external
  verifier and complete Telos protocol accepted `0/7`, with all four preserving `7/7` legitimate
  controls. This is partial deterministic fixture evidence, not a benchmark/model/SOTA claim, in
  [`experiments/iter93_deterministic_strategy_execution_on_materialized_fixtures`](experiments/iter93_deterministic_strategy_execution_on_materialized_fixtures/RESULT.md).
- Provider LLM judge execution on materialized fixtures: blocked after one provider call. The call
  used `$0.00470000` and returned HTTP 200, but the response ended with `MAX_TOKENS` before a
  parseable JSON decision was produced. No LLM-judge decision, all-strategy endpoint, benchmark,
  model, or SOTA claim is made in
  [`experiments/iter94_provider_llm_judge_execution_on_materialized_fixtures`](experiments/iter94_provider_llm_judge_execution_on_materialized_fixtures/RESULT.md).
- Provider LLM judge prompt-budget recovery after block: passed with zero provider calls, zero
  spend, zero LLM-judge execution, and zero row execution. It tied the iter94 blocker to the
  `256` output-token ceiling being consumed by hidden reasoning before parseable JSON, materialized
  `14` recovered prompts with private labels excluded, and pre-registered a bounded retry without
  any benchmark/model/SOTA claim in
  [`experiments/iter95_provider_llm_judge_prompt_budget_recovery_after_block`](experiments/iter95_provider_llm_judge_prompt_budget_recovery_after_block/RESULT.md).
- Provider LLM judge bounded retry after prompt-budget recovery: passed with `14` provider calls,
  `$0.19588800` spend, and `14` parseable fixture decisions. It accepted `0/7`
  false-completion traps but rejected `5/7` legitimate controls, so this is adverse fixture
  evidence for the LLM-judge strategy, not a benchmark/model/SOTA claim, in
  [`experiments/iter96_provider_llm_judge_bounded_retry_after_prompt_budget_recovery`](experiments/iter96_provider_llm_judge_bounded_retry_after_prompt_budget_recovery/RESULT.md).
- Five-strategy completion-verification adjudication after LLM judge: passed with zero provider
  calls, zero spend, zero strategy execution, and zero row execution. It found that external
  verifier and complete Telos both passed the frozen fixture bars, while self-report/tests accepted
  every false-completion trap and the provider LLM judge false-rejected `5/7` legitimate controls.
  Benchmark escalation is rejected because this suite does not yet distinguish complete Telos from
  external verifier, in
  [`experiments/iter97_five_strategy_completion_verification_adjudication_after_llm_judge`](experiments/iter97_five_strategy_completion_verification_adjudication_after_llm_judge/RESULT.md).
- External-verifier/Telos differential suite design after adjudication: passed with zero provider
  calls, zero spend, zero strategy execution, and zero row execution. It froze `8` differential
  target families and `16` planned fixtures to test protocol-specific evidence that may separate
  complete Telos from generic external verification, without claiming the expected divergence as a
  result, in
  [`experiments/iter98_external_verifier_telos_differential_suite_design_after_adjudication`](experiments/iter98_external_verifier_telos_differential_suite_design_after_adjudication/RESULT.md).
- External-verifier/Telos differential fixture materialization after design: passed with zero
  provider calls, zero spend, zero strategy execution, and zero row execution. It materialized `16`
  blinded fixtures across `8` target families, `96` public artifacts, `16` private labels, and `5`
  identical strategy-input manifests with labels excluded, without claiming a differential result,
  in
  [`experiments/iter99_external_verifier_telos_differential_fixture_materialization_after_design`](experiments/iter99_external_verifier_telos_differential_fixture_materialization_after_design/RESULT.md).
- Deterministic strategy execution on differential fixtures after materialization: passed with zero
  provider calls and `64` deterministic decisions. External verifier accepted `4/8`
  false-completion traps while complete Telos accepted `0/8`, producing a limited deterministic
  fixture delta of `0.50000000` without claiming a benchmark or broad superiority result, in
  [`experiments/iter100_deterministic_strategy_execution_on_differential_fixtures_after_materialization`](experiments/iter100_deterministic_strategy_execution_on_differential_fixtures_after_materialization/RESULT.md).
- Provider LLM judge execution on differential fixtures after deterministic: blocked after `14`
  provider calls and `$0.22777400` estimated spend. It produced `13/16` parseable LLM-judge
  decisions, then `DIFX-FIXTURE-0014` hit `MAX_TOKENS`; all-strategy endpoint evidence remains
  incomplete and no benchmark/model/SOTA or superiority claim is made, in
  [`experiments/iter101_provider_llm_judge_execution_on_differential_fixtures_after_deterministic`](experiments/iter101_provider_llm_judge_execution_on_differential_fixtures_after_deterministic/RESULT.md).
- Provider LLM judge differential retry recovery after block: passed with zero provider calls,
  zero spend, zero LLM-judge execution, and zero row execution. It tied the iter101 blocker to
  hidden reasoning exhausting the `2048` output budget, materialized `16` recovered prompts with
  private labels excluded, and pre-registered a full recovered retry, in
  [`experiments/iter102_provider_llm_judge_differential_retry_recovery_after_block`](experiments/iter102_provider_llm_judge_differential_retry_recovery_after_block/RESULT.md).
- Differential provider LLM judge full retry after block recovery: passed with `16` provider calls,
  `$0.23633000` estimated spend, and `16/16` parseable LLM-judge decisions. It accepted `0/8`
  false-completion traps but preserved only `2/8` legitimate controls, so this is adverse
  LLM-judge strategy evidence, not a benchmark/model/SOTA or superiority claim, in
  [`experiments/iter103_differential_provider_llm_judge_full_retry_after_block_recovery`](experiments/iter103_differential_provider_llm_judge_full_retry_after_block_recovery/RESULT.md).
- Five-strategy differential adjudication after recovered LLM judge: passed with zero provider
  calls and zero spend. Complete Telos was the only balanced pass on the frozen 16-fixture
  differential suite; external verifier accepted `4/8` false-completion traps and the recovered
  LLM judge rejected `6/8` legitimate controls. This is a fixture-level differential result, not a
  benchmark/model/SOTA claim, in
  [`experiments/iter104_five_strategy_differential_adjudication_after_recovered_llm_judge`](experiments/iter104_five_strategy_differential_adjudication_after_recovered_llm_judge/RESULT.md).
- External benchmark pilot design after differential adjudication: passed with zero provider calls,
  zero spend, and zero benchmark/task execution. It designed a `20`-packet external pilot with a
  future `30` provider-call and `$10.00000000` spend ceiling, but it is a design result only, not a
  benchmark/model/SOTA claim, in
  [`experiments/iter105_external_benchmark_pilot_design_after_differential_adjudication`](experiments/iter105_external_benchmark_pilot_design_after_differential_adjudication/RESULT.md).
- External benchmark pilot materialization after design: passed with zero provider calls, zero
  spend, and zero benchmark/task execution. It materialized `20` pilot packets, `160` public
  artifacts, `10` false-completion private labels, `10` legitimate-control private labels, and
  `5` identical public-only strategy-input manifests, in
  [`experiments/iter106_external_benchmark_pilot_materialization_after_design`](experiments/iter106_external_benchmark_pilot_materialization_after_design/RESULT.md).
- External benchmark pilot execution after materialization: passed with `20` provider calls,
  `$0.38674600` estimated spend, `100` strategy decisions, and `40` raw LLM prompt/response
  artifacts. Complete Telos accepted `0/10` false-completion packets and preserved `10/10`
  legitimate controls; the external verifier accepted `2/10` false-completion packets; the LLM
  judge accepted `0/10` false-completion packets but rejected `10/10` legitimate controls. This is
  a bounded 20-packet pilot result only, not a benchmark/model/SOTA or all-strategy superiority
  claim, in
  [`experiments/iter107_external_benchmark_pilot_execution_after_materialization`](experiments/iter107_external_benchmark_pilot_execution_after_materialization/RESULT.md).
- Real-trajectory line: the detector and comparators were moved off self-authored packets onto the
  external `princeton-nlp/SWE-bench_Verified` dataset. On `200` real human-authored gold patches a
  raw-diff verifier-provenance and assertion-integrity detector held a `0/200` false-positive rate
  while catching reward-hack variants that the execution-only default accepts, in
  [`experiments/iter109_real_trajectory_tamper_detection_pilot`](experiments/iter109_real_trajectory_tamper_detection_pilot/RESULT.md).
  One hacker-fixer round raised recall on source-only evasions from `0` to `1.0` at `0/200`
  false positives on the same real patches, in
  [`experiments/iter110_adversarial_hardening_hacker_fixer_loop`](experiments/iter110_adversarial_hardening_hacker_fixer_loop/RESULT.md).
  A `gemini-2.5-flash` steelman judge matched the detector on obvious hacks (`0.00` false-positive
  rate, `1.00` recall, `$0.044` spend), in
  [`experiments/iter111_llm_judge_steelman_baseline`](experiments/iter111_llm_judge_steelman_baseline/RESULT.md).
  A stealth 2x2 recorded `detector_only=0`, `judge_only=15`, `both_catch=30`, `both_miss=0` across
  `60` candidates, in
  [`experiments/iter112_stealth_divergence_judge_vs_detector`](experiments/iter112_stealth_divergence_judge_vs_detector/RESULT.md).
  These are bounded pilot results only, not a benchmark, model, or state-of-the-art claim.
- Native execution ground truth: the modeled "hacks pass the visible tests" assumption was replaced
  with a real native run of `django__django-14089` (Python 3.11, `tests/runtests.py`). The hidden
  test failed on base and passed on gold; a hard-coded reward hack passed the real hidden test while
  being a general non-fix; the execution-only default and the deterministic detector accepted it and
  the `gemini-2.5-flash` judge flagged it, in
  [`experiments/iter113_native_execution_ground_truth`](experiments/iter113_native_execution_ground_truth/RESULT.md).
  Native execution was then extended to a five-instance Django batch: `4/5` gold patches resolved
  the real hidden test and the detector flagged `0/5`, with the one non-resolving instance recorded
  as a native-harness fidelity gap, in
  [`experiments/iter114_batch_native_execution`](experiments/iter114_batch_native_execution/RESULT.md).
  A wider eighteen-instance batch tightened the native-harness fidelity estimate to `17/18` gold
  resolution (`0.94`) with the detector still at `0/18` false positives, in
  [`experiments/iter115_wider_batch_native_execution`](experiments/iter115_wider_batch_native_execution/RESULT.md).
- Current gate: judge-panel-before-execution (iter145, `PASS`), pre-registered in
  [`experiments/iter145_judge_panel_before_execution`](experiments/iter145_judge_panel_before_execution/HYPOTHESIS.md);
  the next gate is a third repo plus a measured any-catch precision cost on legitimate controls. The
  real-trajectory arc (iter109 onward) superseded the earlier external-benchmark-pilot adjudication gate
  [`experiments/iter108_external_benchmark_pilot_adjudication_after_execution`](experiments/iter108_external_benchmark_pilot_adjudication_after_execution/HYPOTHESIS.md).
- Benchmark leaderboard or broad benchmark result: none yet. Bounded external pilot evidence now
  exists only for the 20 frozen iter107 packets.
- Provider-backed protocol-effect result: bounded two-row clean pilot, stratified
  adapter-validation rows, one bounded six-row null/no-signal pilot, one bounded six-row
  discriminating-metric pilot, and one bounded six-row unstable stability replication; none is a
  benchmark result.
- Current target: Telos overlay on CodeClash + SWE-bench Verified public software-agent tasks.

Claim-boundary reviewer entry point:
[`experiments/iter31_claim_boundary_release_manifest/proof/claim_boundary_release_manifest.json`](experiments/iter31_claim_boundary_release_manifest/proof/claim_boundary_release_manifest.json).
It indexes the current claim-boundary proof packet and keeps failed/null rows, changed candidates,
and no-claim exclusions visible. It is not a leaderboard, SWE-bench, production, live-domain, or
model-superiority result.

Self-coverage reviewer entry points:
[`experiments/iter35_release_manifest_self_coverage_guard/proof/self_coverage_report.json`](experiments/iter35_release_manifest_self_coverage_guard/proof/self_coverage_report.json)
and
[`experiments/iter36_release_manifest_self_coverage_negative_guard/proof/negative_guard_report.json`](experiments/iter36_release_manifest_self_coverage_negative_guard/proof/negative_guard_report.json).
They account for the release manifest's own self-verification gates and negative fixtures without
changing the claim boundary.

This repo deliberately separates the research line from Sentinel. Sentinel proved a standard:
frozen bars, public baselines, nulls published, raw evidence committed, corrections on the record.
This repo applies that standard to autonomous agent completion.

## The First Number To Freeze

`iter00_target_survey` will score candidate benchmark families against seven criteria:

| criterion | meaning |
|---|---|
| frontier relevance | the problem matches current autonomous-agent failure modes |
| public baseline quality | there is a named benchmark, split, and published score |
| falsifiability | the protocol can fail clearly, before narrative interpretation |
| evidence surface | the task can emit receipts beyond a final answer |
| Aweb fit | Aweb can run and verify it without hidden fleet-scale infrastructure |
| saturation risk | current leaderboards have not made the target uninformative |
| operational cost | the first honest experiment is affordable |

The survey chose one of three actions:

1. Freeze the first public benchmark target.
2. **Freeze a hybrid benchmark built from public tasks plus Telos proof receipts.**
3. Publish a survey null if no candidate clears the bar.

Survey result: [`experiments/iter00_target_survey/RESULT.md`](experiments/iter00_target_survey/RESULT.md).
Receipt dry run: [`experiments/iter01_receipt_dry_run/RESULT.md`](experiments/iter01_receipt_dry_run/RESULT.md).
Public slice: [`experiments/iter02_public_task_slice/RESULT.md`](experiments/iter02_public_task_slice/RESULT.md).
CodeClash smoke: [`experiments/iter03_codeclash_smoke/RESULT.md`](experiments/iter03_codeclash_smoke/RESULT.md).
Agent-behavior slice: [`experiments/iter04_agent_behavior_slice/RESULT.md`](experiments/iter04_agent_behavior_slice/RESULT.md).
Agent-behavior smoke: [`experiments/iter05_agent_behavior_smoke/RESULT.md`](experiments/iter05_agent_behavior_smoke/RESULT.md).
Deterministic edit slice: [`experiments/iter06_deterministic_edit_slice/RESULT.md`](experiments/iter06_deterministic_edit_slice/RESULT.md).
Deterministic edit smoke: [`experiments/iter07_deterministic_edit_smoke/RESULT.md`](experiments/iter07_deterministic_edit_smoke/RESULT.md).
Provider-model pilot slice: [`experiments/iter08_provider_model_pilot_slice/RESULT.md`](experiments/iter08_provider_model_pilot_slice/RESULT.md).
Provider-model pilot smoke: [`experiments/iter09_provider_model_pilot_smoke/RESULT.md`](experiments/iter09_provider_model_pilot_smoke/RESULT.md).
Provider auth recovery: [`experiments/iter10_provider_auth_recovery/RESULT.md`](experiments/iter10_provider_auth_recovery/RESULT.md).
Provider-model pilot retry: [`experiments/iter11_provider_model_pilot_retry/RESULT.md`](experiments/iter11_provider_model_pilot_retry/RESULT.md).
Vertex model access recovery: [`experiments/iter12_vertex_model_access_recovery/RESULT.md`](experiments/iter12_vertex_model_access_recovery/RESULT.md).
Provider-model pilot retry after access recovery: [`experiments/iter13_provider_model_pilot_retry_after_access_recovery/RESULT.md`](experiments/iter13_provider_model_pilot_retry_after_access_recovery/RESULT.md).
Provider diff quality review: [`experiments/iter14_provider_diff_quality_review/RESULT.md`](experiments/iter14_provider_diff_quality_review/RESULT.md).
Provider strict diff rerun: [`experiments/iter15_provider_strict_diff_rerun/RESULT.md`](experiments/iter15_provider_strict_diff_rerun/RESULT.md).
Provider workspace hygiene control: [`experiments/iter16_provider_workspace_hygiene_control/RESULT.md`](experiments/iter16_provider_workspace_hygiene_control/RESULT.md).
Provider lint hygiene control: [`experiments/iter17_provider_lint_hygiene_control/RESULT.md`](experiments/iter17_provider_lint_hygiene_control/RESULT.md).
Provider behavior depth control: [`experiments/iter18_provider_behavior_depth_control/RESULT.md`](experiments/iter18_provider_behavior_depth_control/RESULT.md).
Provider final inspection control: [`experiments/iter19_provider_final_inspection_control/RESULT.md`](experiments/iter19_provider_final_inspection_control/RESULT.md).
Behavior semantic verification: [`experiments/iter20_behavior_semantic_verification/RESULT.md`](experiments/iter20_behavior_semantic_verification/RESULT.md).
Opponent collision control: [`experiments/iter21_opponent_collision_control/RESULT.md`](experiments/iter21_opponent_collision_control/RESULT.md).
Semantic mutation guard: [`experiments/iter22_semantic_mutation_guard/RESULT.md`](experiments/iter22_semantic_mutation_guard/RESULT.md).
Tail semantics falsification: [`experiments/iter23_tail_semantics_falsification/RESULT.md`](experiments/iter23_tail_semantics_falsification/RESULT.md).
Tail safety control: [`experiments/iter24_tail_safety_control/RESULT.md`](experiments/iter24_tail_safety_control/RESULT.md).
Tail safety mutation guard: [`experiments/iter25_tail_safety_mutation_guard/RESULT.md`](experiments/iter25_tail_safety_mutation_guard/RESULT.md).
Own-tail redundancy mutation guard: [`experiments/iter26_own_tail_redundancy_mutation_guard/RESULT.md`](experiments/iter26_own_tail_redundancy_mutation_guard/RESULT.md).
Semantic claim boundary matrix: [`experiments/iter27_semantic_claim_boundary_matrix/RESULT.md`](experiments/iter27_semantic_claim_boundary_matrix/RESULT.md).
Public claim surface guard: [`experiments/iter28_public_claim_surface_guard/RESULT.md`](experiments/iter28_public_claim_surface_guard/RESULT.md).
Public claim surface negative guard: [`experiments/iter29_public_claim_surface_negative_guard/RESULT.md`](experiments/iter29_public_claim_surface_negative_guard/RESULT.md).
Boundary matrix schema guard: [`experiments/iter30_boundary_matrix_schema_guard/RESULT.md`](experiments/iter30_boundary_matrix_schema_guard/RESULT.md).
Claim boundary release manifest: [`experiments/iter31_claim_boundary_release_manifest/RESULT.md`](experiments/iter31_claim_boundary_release_manifest/RESULT.md).
Claim boundary release manifest negative guard: [`experiments/iter32_claim_boundary_release_manifest_negative_guard/RESULT.md`](experiments/iter32_claim_boundary_release_manifest_negative_guard/RESULT.md).
Release manifest public sync guard: [`experiments/iter33_release_manifest_public_sync_guard/RESULT.md`](experiments/iter33_release_manifest_public_sync_guard/RESULT.md).
Release manifest public sync negative guard: [`experiments/iter34_release_manifest_public_sync_negative_guard/RESULT.md`](experiments/iter34_release_manifest_public_sync_negative_guard/RESULT.md).
Release manifest self-coverage guard: [`experiments/iter35_release_manifest_self_coverage_guard/RESULT.md`](experiments/iter35_release_manifest_self_coverage_guard/RESULT.md).
Release manifest self-coverage negative guard: [`experiments/iter36_release_manifest_self_coverage_negative_guard/RESULT.md`](experiments/iter36_release_manifest_self_coverage_negative_guard/RESULT.md).
Release manifest self-coverage public sync guard: [`experiments/iter37_release_manifest_self_coverage_public_sync_guard/RESULT.md`](experiments/iter37_release_manifest_self_coverage_public_sync_guard/RESULT.md).
Release manifest self-coverage public sync negative guard: [`experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard/RESULT.md`](experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard/RESULT.md).
Public task protocol-effect slice: [`experiments/iter39_public_task_protocol_effect_slice/RESULT.md`](experiments/iter39_public_task_protocol_effect_slice/RESULT.md).
Public task protocol-effect execution: [`experiments/iter40_public_task_protocol_effect_execution/RESULT.md`](experiments/iter40_public_task_protocol_effect_execution/RESULT.md).
Public task protocol-effect runner recovery: [`experiments/iter41_public_task_protocol_effect_runner_recovery/RESULT.md`](experiments/iter41_public_task_protocol_effect_runner_recovery/RESULT.md).
Public task protocol-effect execution retry: [`experiments/iter42_public_task_protocol_effect_execution_retry/RESULT.md`](experiments/iter42_public_task_protocol_effect_execution_retry/RESULT.md).
Provider execution harness recovery: [`experiments/iter43_provider_execution_harness_recovery/RESULT.md`](experiments/iter43_provider_execution_harness_recovery/RESULT.md).
Public task protocol-effect execution after harness recovery: [`experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/RESULT.md`](experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/RESULT.md).
Public task-condition executor assembly: [`experiments/iter45_public_task_condition_executor_assembly/RESULT.md`](experiments/iter45_public_task_condition_executor_assembly/RESULT.md).
Public task protocol-effect execution with assembled executor: [`experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/RESULT.md`](experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/RESULT.md).
Provider task-condition command binding recovery: [`experiments/iter47_provider_task_condition_command_binding_recovery/RESULT.md`](experiments/iter47_provider_task_condition_command_binding_recovery/RESULT.md).
Provider-compatible protocol-effect slice refreeze: [`experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/RESULT.md`](experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/RESULT.md).
Provider-compatible protocol-effect execution retry: [`experiments/iter49_provider_compatible_protocol_effect_execution_retry/RESULT.md`](experiments/iter49_provider_compatible_protocol_effect_execution_retry/RESULT.md).
Provider-compatible execution wrapper recovery: [`experiments/iter50_provider_compatible_execution_wrapper_recovery/RESULT.md`](experiments/iter50_provider_compatible_execution_wrapper_recovery/RESULT.md).
Provider-compatible protocol-effect execution with wrapper: [`experiments/iter51_provider_compatible_protocol_effect_execution_with_wrapper/RESULT.md`](experiments/iter51_provider_compatible_protocol_effect_execution_with_wrapper/RESULT.md).
Provider condition runtime separation recovery: [`experiments/iter52_provider_condition_runtime_separation_recovery/RESULT.md`](experiments/iter52_provider_condition_runtime_separation_recovery/RESULT.md).
Provider-compatible execution after condition recovery: [`experiments/iter53_provider_compatible_protocol_effect_execution_after_condition_recovery/RESULT.md`](experiments/iter53_provider_compatible_protocol_effect_execution_after_condition_recovery/RESULT.md).
Provider pair executor recovery: [`experiments/iter54_provider_pair_executor_recovery/RESULT.md`](experiments/iter54_provider_pair_executor_recovery/RESULT.md).
Provider-compatible paid execution after executor recovery: [`experiments/iter55_provider_compatible_paid_execution_after_executor_recovery/RESULT.md`](experiments/iter55_provider_compatible_paid_execution_after_executor_recovery/RESULT.md).
Provider auth recovery for paid protocol effect: [`experiments/iter56_provider_auth_recovery_for_paid_protocol_effect/RESULT.md`](experiments/iter56_provider_auth_recovery_for_paid_protocol_effect/RESULT.md).
Provider-compatible paid execution after auth recovery: [`experiments/iter57_provider_compatible_paid_execution_after_auth_recovery/RESULT.md`](experiments/iter57_provider_compatible_paid_execution_after_auth_recovery/RESULT.md).
CodeClash Vertex dependency recovery: [`experiments/iter58_codeclash_vertex_dependency_recovery/RESULT.md`](experiments/iter58_codeclash_vertex_dependency_recovery/RESULT.md).
Provider-compatible paid execution after dependency recovery: [`experiments/iter59_provider_compatible_paid_execution_after_dependency_recovery/RESULT.md`](experiments/iter59_provider_compatible_paid_execution_after_dependency_recovery/RESULT.md).
Provider model binding recovery: [`experiments/iter60_provider_model_binding_recovery/RESULT.md`](experiments/iter60_provider_model_binding_recovery/RESULT.md).
Vertex quota-project binding recovery: [`experiments/iter61_vertex_quota_project_binding_recovery/RESULT.md`](experiments/iter61_vertex_quota_project_binding_recovery/RESULT.md).
Vertex bearer token path recovery: [`experiments/iter62_vertex_bearer_token_path_recovery/RESULT.md`](experiments/iter62_vertex_bearer_token_path_recovery/RESULT.md).
Vertex access path parity recheck: [`experiments/iter63_vertex_access_path_parity_recheck/RESULT.md`](experiments/iter63_vertex_access_path_parity_recheck/RESULT.md).
Provider-compatible paid execution after access-path recovery:
[`experiments/iter64_provider_compatible_paid_execution_after_access_path_recovery/RESULT.md`](experiments/iter64_provider_compatible_paid_execution_after_access_path_recovery/RESULT.md).
Receipt-schema prompt alignment:
[`experiments/iter65_receipt_schema_prompt_alignment/RESULT.md`](experiments/iter65_receipt_schema_prompt_alignment/RESULT.md).
Provider-compatible paid execution after receipt prompt alignment:
[`experiments/iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment/RESULT.md`](experiments/iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment/RESULT.md).
Provider-compatible expanded slice refreeze:
[`experiments/iter67_provider_compatible_expanded_slice_refreeze/RESULT.md`](experiments/iter67_provider_compatible_expanded_slice_refreeze/RESULT.md).
Provider-compatible task-surface adapter recovery:
[`experiments/iter68_provider_compatible_task_surface_adapter_recovery/RESULT.md`](experiments/iter68_provider_compatible_task_surface_adapter_recovery/RESULT.md).
CodeClash task-surface source snapshot recovery:
[`experiments/iter69_codeclash_task_surface_source_snapshot_recovery/RESULT.md`](experiments/iter69_codeclash_task_surface_source_snapshot_recovery/RESULT.md).
Provider-compatible expanded adapter completion:
[`experiments/iter70_provider_compatible_expanded_adapter_completion/RESULT.md`](experiments/iter70_provider_compatible_expanded_adapter_completion/RESULT.md).
Provider-compatible expanded slice after adapter completion:
[`experiments/iter71_provider_compatible_expanded_slice_after_adapter_completion/RESULT.md`](experiments/iter71_provider_compatible_expanded_slice_after_adapter_completion/RESULT.md).
Provider-compatible expanded paid execution after slice refreeze:
[`experiments/iter72_provider_compatible_expanded_paid_execution_after_slice_refreeze/RESULT.md`](experiments/iter72_provider_compatible_expanded_paid_execution_after_slice_refreeze/RESULT.md).
Current gate:
[`experiments/iter145_judge_panel_before_execution/HYPOTHESIS.md`](experiments/iter145_judge_panel_before_execution/HYPOTHESIS.md).

## Current Evidence Arc

The live evidence is the real-trajectory arc (iter109-iter149); the full per-gate result is the
summary table near the top of this file. Its shape:

```mermaid
flowchart LR
  L1["109-110<br/>detector<br/>0/200 FP"]-->L2["111-112<br/>steelman judge<br/>+ stealth 2x2"]-->L3["113-116<br/>real execution<br/>catch rate"]-->BM["117-118<br/>precision boundary<br/>both-miss found"]-->DEF["119-121<br/>metamorphic defense<br/>gold-free"]-->AUT["122-123<br/>auto-generate<br/>+ anchor filter"]-->SC["124-129<br/>scale: 2/7 -> 6/7<br/>+ strategy taxonomy"]-->APP["130-139<br/>docker harness<br/>+ applicability 0.81 / 0.10"]-->FBM["140-145<br/>frontier adversary<br/>both-miss 0.24 · judge-fooled 0.12<br/>survives frontier judges + panel · cross-repo"]-->PE["146-149<br/>protocol effect<br/>gamed 0/13 -> 10/13 · gold-free 3/3 catch<br/>net-positive filter"]
  classDef d fill:#e4f0ff,stroke:#1565c0,color:#0c2742;
  classDef risk fill:#fee,stroke:#c22,color:#000;
  classDef fix fill:#e2f3e5,stroke:#2e7d32,color:#13361b;
  class L1,L2,L3 d;
  class BM,FBM risk;
  class DEF,AUT,SC,APP,PE fix;
```

The FBM node was the adversarial frontier: iter140's `0/20` gemini null read the both-miss window as
narrow, but iter141 overturned that reading - a non-refusing frontier adversary manufactures the class on
well-tested code, iter142 measured the rate, iter143 showed it survives frontier judges, iter144
generalized it to a second repo, and iter145 showed a judge panel does not close it. The PE node then
closes the loop: used as a gate with gold-free repair feedback, the protocol lifts real completion on
reward-hack-prone starts from `0/7` to `5/7`, the first evidence that it changes outcomes rather than only
measuring them. The earlier provider-pilot and semantic-guard arc (iter00-iter108) is preserved in the
Honest Status log above and the learning ledger.

## Candidate Target Families

The initial candidates are documented in [`benchmarks/CANDIDATES.md`](benchmarks/CANDIDATES.md):

- coding-agent completion: SWE-bench Verified, CodeClash, Terminal-Bench-style tasks
- AI R&D agents: METR RE-Bench-style research engineering tasks
- tool-using service agents: tau-bench-style policy and database-state tasks
- adversarial tool agents: AgentDojo-style utility/security tradeoffs
- custom Telos overlay: public tasks with receipt requirements added around them

The target was not chosen by taste. It was chosen by the frozen survey.

## Architecture

The real-trajectory arc (iter109-iter149) established a three-layer completion verifier, each layer
present because the one before it provably fails on a measured class of reward hack (see the arc
section above and the synthesis report). The necessity of the third layer is not asserted but measured:
a frontier adversary defeats both static layers on `0.12` of attempts against well-tested code, and one
such hack survives every frontier judge tested (iter142-iter144). The cascade runs cheapest-first and
escalates only the survivors:

```mermaid
flowchart LR
  C["candidate diff<br/>+ FAIL_TO_PASS"] --> D["Layer 1<br/>deterministic detector<br/>free · reproducible"]
  D -->|mechanical hacks caught| X["reward_hack"]
  D -->|survivors| J["Layer 2<br/>LLM judge<br/>paid · semantic"]
  J -->|oblique/hard-coded caught| X
  J -->|survivors| M["Layer 3<br/>held-out-input execution<br/>gold-free property"]
  M -->|generalization-broken caught| X
  M -->|holds| OK["accept<br/>+ receipt"]
  classDef base fill:#f6f8fa,stroke:#57606a,color:#1f2328;
  classDef layer fill:#e4f0ff,stroke:#1565c0,color:#0c2742;
  classDef hack fill:#fee,stroke:#c22,color:#000;
  classDef ok fill:#e2f3e5,stroke:#2e7d32,color:#13361b;
  class C base;
  class D,J,M layer;
  class X hack;
  class OK ok;
```

Layer 3 is automated and gold-free: a model proposes a metamorphic property from the function
contract, the visible test filters unsound proposals, and execution on random held-out inputs catches
completions the static layers accept - with the property strategy chosen by function type (a contract
property for pure transforms, an inverse round-trip for invertible parsers/formatters).

Full design: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
Paper: [`docs/PAPER.md`](docs/PAPER.md) - the consolidated result (iter109-iter149), submission-shaped.
Synthesis report: [`docs/COMPLETION_VERIFICATION_REPORT.md`](docs/COMPLETION_VERIFICATION_REPORT.md).
Presentation standard: [`docs/PRESENTATION.md`](docs/PRESENTATION.md).
Learning engine: [`docs/LEARNING_ENGINE.md`](docs/LEARNING_ENGINE.md).
Mission loop: [`docs/MISSION_LOOP.md`](docs/MISSION_LOOP.md).

## Repository Map

```text
README.md                  research front door and live status
PREREGISTRATION.md         frozen first-stage target-selection protocol
CONTINUITY.md              operator invariants and handoff discipline
HANDOFF.md                 dynamic snapshot generated by scripts/make_handoff.py
telos/                     receipt validation, scorecard primitives, and telos/tamper (the three-layer verifier)
telos/tamper/              the deterministic detector, attack/adversarial generators, and the LLM-judge client
benchmarks/                candidate benchmark registry
docs/                      architecture, related work, the completion-verification synthesis report, next phase
experiments/               one folder per pre-registered experiment (iter00-iter149), each with a learning record
mission/                   machine-readable mission loop contract
protocol/                  proof receipt schema
scripts/                   validation and handoff tooling
tests/                     repository and protocol tests
```

## Reproduce The Current State

```bash
ruff check .
pytest -q
python3 scripts/validate_docs.py
python3 scripts/validate_mission_loop.py
python3 scripts/validate_target_survey.py
python3 scripts/validate_public_slice.py
python3 scripts/validate_agent_behavior_slice.py
python3 scripts/validate_deterministic_edit_slice.py
python3 scripts/validate_provider_model_pilot_slice.py
python3 scripts/validate_receipts.py experiments/iter01_receipt_dry_run/proof
python3 scripts/validate_receipts.py experiments/iter03_codeclash_smoke/proof
python3 scripts/audit_codeclash_smoke.py
python3 scripts/validate_receipts.py experiments/iter05_agent_behavior_smoke/proof
python3 scripts/audit_agent_behavior_smoke.py
python3 scripts/validate_receipts.py experiments/iter07_deterministic_edit_smoke/proof
python3 scripts/audit_deterministic_edit_smoke.py
python3 scripts/validate_receipts.py experiments/iter09_provider_model_pilot_smoke/proof
python3 scripts/audit_provider_model_pilot_smoke.py
python3 scripts/validate_receipts.py experiments/iter10_provider_auth_recovery/proof
python3 scripts/audit_provider_auth_recovery.py
python3 scripts/validate_receipts.py experiments/iter11_provider_model_pilot_retry/proof
python3 scripts/audit_provider_model_pilot_retry.py
python3 scripts/validate_receipts.py experiments/iter12_vertex_model_access_recovery/proof
python3 scripts/audit_vertex_model_access_recovery.py
python3 scripts/validate_receipts.py experiments/iter13_provider_model_pilot_retry_after_access_recovery/proof
python3 scripts/audit_provider_model_pilot_after_access.py
python3 scripts/validate_receipts.py experiments/iter14_provider_diff_quality_review/proof
python3 scripts/audit_provider_diff_quality_review.py
python3 scripts/validate_receipts.py experiments/iter15_provider_strict_diff_rerun/proof
python3 scripts/audit_provider_strict_diff_rerun.py
python3 scripts/validate_receipts.py experiments/iter16_provider_workspace_hygiene_control/proof
python3 scripts/audit_provider_workspace_hygiene_control.py
python3 scripts/validate_receipts.py experiments/iter17_provider_lint_hygiene_control/proof
python3 scripts/audit_provider_lint_hygiene_control.py
python3 scripts/validate_receipts.py experiments/iter18_provider_behavior_depth_control/proof
python3 scripts/audit_provider_behavior_depth_control.py
python3 scripts/validate_receipts.py experiments/iter19_provider_final_inspection_control/proof
python3 scripts/audit_provider_final_inspection_control.py
python3 scripts/validate_receipts.py experiments/iter20_behavior_semantic_verification/proof
python3 scripts/audit_behavior_semantic_verification.py
python3 scripts/validate_receipts.py experiments/iter21_opponent_collision_control/proof
python3 scripts/audit_opponent_collision_control.py
python3 scripts/validate_receipts.py experiments/iter22_semantic_mutation_guard/proof
python3 scripts/audit_semantic_mutation_guard.py
python3 scripts/validate_receipts.py experiments/iter23_tail_semantics_falsification/proof
python3 scripts/audit_tail_semantics_falsification.py
python3 scripts/validate_receipts.py experiments/iter24_tail_safety_control/proof
python3 scripts/audit_tail_safety_control.py
python3 scripts/validate_receipts.py experiments/iter25_tail_safety_mutation_guard/proof
python3 scripts/audit_tail_safety_mutation_guard.py
python3 scripts/validate_receipts.py experiments/iter26_own_tail_redundancy_mutation_guard/proof
python3 scripts/audit_own_tail_redundancy_mutation_guard.py
python3 scripts/validate_receipts.py experiments/iter27_semantic_claim_boundary_matrix/proof
python3 scripts/audit_semantic_claim_boundary_matrix.py
python3 scripts/validate_receipts.py experiments/iter28_public_claim_surface_guard/proof
python3 scripts/audit_public_claim_surface_guard.py
python3 scripts/validate_receipts.py experiments/iter29_public_claim_surface_negative_guard/proof
python3 scripts/audit_public_claim_surface_negative_guard.py
python3 scripts/validate_receipts.py experiments/iter30_boundary_matrix_schema_guard/proof
python3 scripts/audit_boundary_matrix_schema_guard.py
python3 scripts/validate_receipts.py experiments/iter31_claim_boundary_release_manifest/proof
python3 scripts/audit_claim_boundary_release_manifest.py
python3 scripts/validate_receipts.py experiments/iter32_claim_boundary_release_manifest_negative_guard/proof
python3 scripts/audit_claim_boundary_release_manifest_negative_guard.py
python3 scripts/validate_receipts.py experiments/iter33_release_manifest_public_sync_guard/proof
python3 scripts/audit_release_manifest_public_sync_guard.py
python3 scripts/validate_receipts.py experiments/iter34_release_manifest_public_sync_negative_guard/proof
python3 scripts/audit_release_manifest_public_sync_negative_guard.py
python3 scripts/validate_receipts.py experiments/iter35_release_manifest_self_coverage_guard/proof
python3 scripts/audit_release_manifest_self_coverage_guard.py
python3 scripts/validate_receipts.py experiments/iter36_release_manifest_self_coverage_negative_guard/proof
python3 scripts/audit_release_manifest_self_coverage_negative_guard.py
python3 scripts/validate_receipts.py experiments/iter37_release_manifest_self_coverage_public_sync_guard/proof
python3 scripts/audit_release_manifest_self_coverage_public_sync_guard.py
python3 scripts/validate_receipts.py experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard/proof
python3 scripts/audit_release_manifest_self_coverage_public_sync_negative_guard.py
python3 scripts/validate_receipts.py experiments/iter39_public_task_protocol_effect_slice/proof
python3 scripts/audit_public_task_protocol_effect_slice.py
python3 scripts/validate_receipts.py experiments/iter40_public_task_protocol_effect_execution/proof
python3 scripts/audit_public_task_protocol_effect_execution.py
python3 scripts/validate_receipts.py experiments/iter41_public_task_protocol_effect_runner_recovery/proof
python3 scripts/audit_public_task_protocol_effect_runner_recovery.py
python3 scripts/validate_receipts.py experiments/iter42_public_task_protocol_effect_execution_retry/proof
python3 scripts/audit_public_task_protocol_effect_execution_retry.py
python3 scripts/validate_receipts.py experiments/iter43_provider_execution_harness_recovery/proof
python3 scripts/audit_provider_execution_harness_recovery.py
python3 scripts/validate_receipts.py experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/proof
python3 scripts/audit_public_task_protocol_effect_execution_after_harness_recovery.py
python3 scripts/validate_receipts.py experiments/iter45_public_task_condition_executor_assembly/proof
python3 scripts/audit_public_task_condition_executor_assembly.py
python3 scripts/validate_receipts.py experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/proof
python3 scripts/audit_public_task_protocol_effect_execution_with_assembled_executor.py
python3 scripts/validate_receipts.py experiments/iter47_provider_task_condition_command_binding_recovery/proof
python3 scripts/audit_provider_task_condition_command_binding_recovery.py
python3 scripts/validate_receipts.py experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/proof
python3 scripts/audit_provider_compatible_protocol_effect_slice_refreeze.py
python3 scripts/validate_receipts.py experiments/iter49_provider_compatible_protocol_effect_execution_retry/proof
python3 scripts/audit_provider_compatible_protocol_effect_execution_retry.py
python3 scripts/validate_receipts.py experiments/iter50_provider_compatible_execution_wrapper_recovery/proof
python3 scripts/audit_provider_compatible_execution_wrapper_recovery.py
python3 scripts/validate_receipts.py experiments/iter51_provider_compatible_protocol_effect_execution_with_wrapper/proof
python3 scripts/audit_provider_compatible_protocol_effect_execution_with_wrapper.py
python3 scripts/validate_receipts.py experiments/iter52_provider_condition_runtime_separation_recovery/proof
python3 scripts/audit_provider_condition_runtime_separation_recovery.py
python3 scripts/validate_receipts.py experiments/iter53_provider_compatible_protocol_effect_execution_after_condition_recovery/proof
python3 scripts/audit_provider_compatible_protocol_effect_execution_after_condition_recovery.py
python3 scripts/validate_receipts.py experiments/iter54_provider_pair_executor_recovery/proof
python3 scripts/audit_provider_pair_executor_recovery.py
python3 scripts/validate_receipts.py experiments/iter55_provider_compatible_paid_execution_after_executor_recovery/proof
python3 scripts/audit_provider_compatible_paid_execution_after_executor_recovery.py
python3 scripts/validate_receipts.py experiments/iter56_provider_auth_recovery_for_paid_protocol_effect/proof
python3 scripts/audit_provider_auth_recovery_for_paid_protocol_effect.py
python3 scripts/validate_receipts.py experiments/iter57_provider_compatible_paid_execution_after_auth_recovery/proof
python3 scripts/audit_provider_compatible_paid_execution_after_auth_recovery.py
python3 scripts/validate_receipts.py experiments/iter58_codeclash_vertex_dependency_recovery/proof
python3 scripts/audit_codeclash_vertex_dependency_recovery.py
python3 scripts/validate_receipts.py experiments/iter59_provider_compatible_paid_execution_after_dependency_recovery/proof
python3 scripts/audit_provider_compatible_paid_execution_after_dependency_recovery.py
python3 scripts/validate_receipts.py experiments/iter60_provider_model_binding_recovery/proof
python3 scripts/audit_provider_model_binding_recovery.py
python3 scripts/validate_receipts.py experiments/iter61_vertex_quota_project_binding_recovery/proof
python3 scripts/audit_vertex_quota_project_binding_recovery.py
python3 scripts/validate_receipts.py experiments/iter62_vertex_bearer_token_path_recovery/proof
python3 scripts/audit_vertex_bearer_token_path_recovery.py
python3 scripts/validate_receipts.py experiments/iter63_vertex_access_path_parity_recheck/proof
python3 scripts/audit_vertex_access_path_parity_recheck.py
python3 scripts/validate_receipts.py experiments/iter64_provider_compatible_paid_execution_after_access_path_recovery/proof
python3 scripts/audit_provider_compatible_paid_execution_after_access_path_recovery.py
python3 scripts/validate_receipts.py experiments/iter65_receipt_schema_prompt_alignment/proof
python3 scripts/audit_receipt_schema_prompt_alignment.py
python3 scripts/validate_receipts.py experiments/iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment/proof
python3 scripts/audit_provider_compatible_paid_execution_after_receipt_prompt_alignment.py
python3 scripts/validate_receipts.py experiments/iter67_provider_compatible_expanded_slice_refreeze/proof
python3 scripts/audit_provider_compatible_expanded_slice_refreeze.py
python3 scripts/validate_receipts.py experiments/iter68_provider_compatible_task_surface_adapter_recovery/proof
python3 scripts/audit_provider_compatible_task_surface_adapter_recovery.py
python3 scripts/validate_receipts.py experiments/iter69_codeclash_task_surface_source_snapshot_recovery/proof
python3 scripts/audit_codeclash_task_surface_source_snapshot_recovery.py
python3 scripts/validate_receipts.py experiments/iter70_provider_compatible_expanded_adapter_completion/proof
python3 scripts/audit_provider_compatible_expanded_adapter_completion.py
python3 scripts/validate_learning_ledger.py
python3 scripts/validate_json.py
python3 scripts/validate_handoff.py
python3 scripts/make_handoff.py
```

## Writing Standard

The language in this repo must stay below the evidence. A claim is allowed only when it has a
source, a receipt, a log, or a clearly marked hypothesis behind it. Nulls and blocked gates are
first-class results. Corrections remain in the record.
