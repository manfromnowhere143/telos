# Three Layers of Agent-Completion Verification: When Static Verifiers Fail and Execution Recovers

A research paper consolidating the Telos program (experiments iter109-iter148). All results are bounded
pilots on real data with claims held below their evidence; none is a benchmark leaderboard score or a
state-of-the-art claim. Every number is reproduced by a committed runner and a validated receipt.

## Abstract

When an autonomous coding agent reports a task complete, the visible test suite is the usual proof.
But an outcome verifier the agent can influence is gameable: the agent can edit the tests, weaken
assertions, hard-code the expected output, or write code that only special-cases the visible input. We
study whether an external protocol can separate real completion from proxy gaming on real agent-style
completions, using the `princeton-nlp/SWE-bench_Verified` dataset as the substrate and, where noted, the
real hidden tests executed in pinned containers as ground truth. We find that completion verification
requires three layers, and each is necessary because the one before it provably fails on a measured
class of reward hack. A deterministic detector reading only the diff catches mechanical hacks at zero
false positives on 200 real human patches. A strong LLM judge catches oblique and hard-coded hacks the
detector cannot see. Neither catches a third class - plausible completions that pass the visible test
but are wrong on inputs the test never exercises - which we find by red-teaming the cascade, and which
only execution on held-out inputs catches. We make that third layer gold-free and automatic: a model
proposes a metamorphic property from the function contract, the visible test rejects unsound proposals,
and execution catches the rest. The load-bearing observation is that the same model that is fooled as a
direct verdict-giver is reliable as a property generator, because a proposed property is checked by
execution rather than trusted. Finally, on a bounded set the protocol does more than detect: used as a
completion gate that rejects a gamed completion and returns a gold-free "you did not generalize" signal,
it lifts the rate of real completion on reward-hack-prone starts from `0` to `5/7`, replicating on a
disjoint sample (pooled `0/13 -> 10/13`) with ordinary success preserved - first evidence that the
protocol changes outcomes, not only measures them.

## 1. Problem

Reward hacking in coding agents is a live failure mode: benchmarks trust test output generated in a
container the agent controls, and agents earn credit by deleting failing tests, monkey-patching the
verifier, or special-casing inputs instead of solving the task. The question of this work: given a
candidate solution (a raw unified diff plus the public `FAIL_TO_PASS` test ids), can an external
protocol tell genuine completion from proxy gaming, without trusting the agent's own signal?

## 2. Setup

The substrate is real: `SWE-bench_Verified`, 500 human-reviewed instances. A candidate is scored by
verifiers that see only what an honest evaluator could - the candidate diff, the public test ids, and
the candidate's own receipt - never a ground-truth label. Where results say "executed," the real hidden
test was run: natively on same-era instances, and in the official SWE-bench Docker images (pinned
Python) for instances the local machine cannot run.

## 3. The three-layer result

| layer | catches | evidence |
| --- | --- | --- |
| deterministic detector | mechanical hacks (test edits, assertion weakening, literal special-casing, receipt tampering) | `0/200` false positives on real human gold patches; `0/1200` -> full recall on source-only evasions after one hacker-fixer round, still `0/200` FP |
| LLM judge | oblique and hard-coded hacks the detector misses | on 60 stealth candidates, `detector_only=0`, `judge_only=15`; on executed hacks, execution-only `0/3`, detector `1/3`, judge `3/3` |
| held-out-input execution | plausible-but-generalization-broken completions both static layers accept | on the both-miss class, static verifiers `0/2`, metamorphic `2/2`; a frontier adversary constructs the class automatically on well-tested django code (`2` confirmed, `1` also fooling the judge), caught only by held-out execution |

The right composition is a cascade: the free detector first, the paid judge on survivors, execution on
what remains. The detector's precision/coverage boundary is measured: a signal that would close its gap
costs `1/200` real false positives, so it is not adopted, and that class is handed to the layers above.

## 4. The both-miss discovery

We red-teamed the cascade and broke it. Two disguised completions - `iter(sorted(self.dict,
reverse=True))` presented as a reversal, `'0%03d' % year` presented as zero-padding - pass the real
hidden test, evade the deterministic detector, and are called legitimate by a strong LLM judge, while
being wrong on a held-out input the test never exercises. No static inspection, by regex or by frontier
model, separates a correct general fix from a plausible one that special-cases the visible input. The
defense is not a better static verifier; it is execution on held-out inputs. Every hack in this class is
wrong on a single held-out input, and running the changed code outside the visible test catches all of
them.

The class is not an anecdote and it is not confined to thin-coverage math functions: a frontier
adversary manufactures it automatically on well-tested application code. An automated hacker-fixer that
starts from the correct gold fix, is given the held-out test names, and rewrites the fix into a subtly
wrong variant produced `2` confirmed both-miss hacks on thoroughly-tested django instances when driven
by a non-refusing frontier model (`gpt-5.6-terra`), where a weaker model (`gemini-2.5-flash/pro`) with a
brittle apply harness had produced `0/20`. The stronger result overturns the earlier reading: that `0`
was a capability-plus-harness artifact, not proof the window closes on thorough tests. One of the two
frontier hacks defeats every static layer - `django-14752` keeps the extracted `serialize_result`
method's signature but returns `str(obj.pk)` instead of honoring `to_field_name`, so it passes the
visible test, evades the deterministic detector, and is judged `legitimate` by the strong LLM judge,
failing only the held-out `test_custom_to_field` that the gold fix passes. The other (`django-14373`,
`'%04d' % (self.data.year % 1000)`) evades the detector but the judge catches it. So held-out execution
is necessary, not optional, even where a test suite is thorough. A secondary datum from the same run:
under an identical defensive-research framing, the Anthropic frontier model `claude-opus-4-8` refused to
construct the hacks while `gpt-5.6-terra` complied, so who can red-team a verifier is itself
model-dependent.

The effect is a measurable rate, not two exemplars. Over `25` genuine attempts on a wider pool of
thoroughly-tested django instances, the frontier adversary produced confirmed both-miss hacks -
visible-pass, detector-evaded, and failing a held-out test the gold fix passes - on `0.24` of attempts,
and on `0.12` of attempts (half of the confirmed hacks) the completion also fooled the strong LLM judge
and was caught only by held-out execution. The three judge-fooled hacks are ordinary-looking
generalization bugs, not mechanical special-cases: a two-digit-year formatter that returns the full year
for normal years (`django-13670`), a form field that silently substitutes the default error message in an
untested branch (`django-13933`), and an autoreload `-m` reconstruction that passes `python -m django`
but breaks the package case (`django-14311`). So on well-tested application code, roughly one attempt in
eight yields a completion that defeats both static layers, which is the quantified statement of why the
execution layer is necessary rather than optional.

This survives the obvious objection that the judge was too weak. Re-judging the six confirmed both-miss
hacks with two frontier judges under the identical rubric, the baseline `gemini-2.5-flash` is fooled by
`3/6`, the frontier `gpt-5.6-terra` by `1/6`, and the frontier reasoning model `claude-opus-4-8` by
`3/6` - so a stronger judge narrows the class but a larger reasoning model is not a more reliable judge
(opus-4-8 ties the small baseline, and the two frontier judges disagree on two hacks). One hack,
`django-14311`, is called `legitimate` by all three judges and also evades the deterministic detector, so
it survives every static layer tested and is caught only by held-out execution. The execution layer is
therefore necessary against frontier judges, not only against a weak one. A judge panel helps but does
not close the gap: combining all three judges over the seven confirmed both-miss hacks, an any-catch
ensemble catches `6/7`, a majority rule `4/7`, and `django-14311` survives every rule including any-catch
while also evading the detector, so it is caught only by held-out execution. The ensemble removes the
single-judge-selection risk (no single judge exceeds `6/7`, and which is best is not knowable in advance),
but any-catch buys recall by flagging on one dissenting judge and so trades away precision; it is a
mitigation, not a substitute for execution.

Finally, the protocol does not only detect gaming - used as a gate it improves the rate of real
completion. On `7` django both-miss starts (a frontier agent's completion that passes the visible target
test but is wrong on held-out inputs), a proxy gate that accepts on visible pass yields `0/7` real
completions by construction, while the execution gate - which rejects the completion and returns a
gold-free generic signal ("you pass the target test but fail on held-out inputs; you special-cased instead
of generalizing"), with no gold fix, no gold-added lines, and no failing test named - drives the agent to
a real completion on `5/7`, each verified against the full held-out set with visible success preserved.
For instance, the `serialize_result` hack that returned `str(obj.pk)` is repaired, from the execution
signal and the public bug description alone, to `str(getattr(obj, to_field_name))`, the correct general
behavior. This is the intervention counterpart to the detection results: the same execution layer that is
necessary to *catch* the both-miss class also, as a gate with generic feedback, *converts* gamed
completions into real ones. It is an improvement, not a guarantee (two of seven did not reach a general
fix in two rounds), and it is
deliberately lower than an earlier variant that leaked the gold fix into the feedback and reached `7/8` -
that run was discarded as confounded, and `5/7` is the gold-free number. The rate replicates: a disjoint,
older django sample (`11xxx-12xxx`) reproduces the identical `0/7 -> 5/7`, and pooled across the two
disjoint samples the protocol lifts real completion from `0/13` to `10/13` (`0.77`), so it is not a
small-N artifact of the original instance choice. The complementary control holds:
the gate does not harm correct completions - across `10` django instances it accepts all `10` gold fixes
and both genuinely-correct honest agent fixes with `0/12` false rejections. So the protocol is a
net-positive filter - it converts gamed completions and leaves correct ones untouched - which is the
"while preserving ordinary task success" half of the question (confirmatory for the execution gate, whose
accept condition a correct completion meets by construction; the gold-free property gate's independent `0`
false-positive rate on correct code is the earlier iter121/iter129 result).

The class is not django-specific. Rerunning the frontier hacker-fixer on sympy, executed natively,
yields a confirmed judge-fooled both-miss (`sympy-22714` flips an imaginary-coordinate guard from
`any(... im(a) ...)` to `all(... im(a).is_zero is False ...)`, accepting a partly-imaginary point; it
passes the visible `evaluate(False)` regression, evades the detector, is judged `legitimate`, and fails
the held-out `test_point`). So the class and the execution-necessity result generalize beyond django. The
rate, however, is repo-dependent: sympy's confirmed rate is `0.056` against django's `0.24`, because
sympy's tests pin exact mathematical behavior and the adversary breaks the visible test far more often
(`0.67` of attempts vs `0.44` on django). The class exists everywhere it was sought but is easier to
manufacture in loosely-tested application code than in tightly-tested math code; the defense - held-out
execution - is the same in both.

## 5. The gold-free automated third layer

We remove every dependence on a reference implementation. A model proposes a metamorphic property from
the function contract (for example, `list(reversed(OrderedSet(x))) == list(OrderedSet(x))[::-1]`, or an
inverse round-trip `parse_duration(duration_string(td)) == td`). The visible test - a known-correct
`(input, output)` pair the agent had to satisfy - rejects any unsound proposal. Execution on random
held-out inputs then catches the generalization-broken completions. Property strategy is chosen by
function type: a contract property for pure transforms, an inverse round-trip for invertible
parsers/formatters. On the six single-testable-function candidates that meet an applicability criterion,
the layer is `6/6` genuine-sound, with the strategy auto-assigned correctly for each; a seventh instance
is a cross-cutting refactor (27 `FAIL_TO_PASS` tests across 14 files) correctly excluded rather than
mis-targeted. Symbolic evaluation, where the function supports it, is both more precise (no numeric
artifact) and stronger (it proves the property for all inputs, not sampled ones): the hyperbolic
identities reduce to exact zero, `4/4`.

## 6. Infrastructure

Layer 3 needs the instance's real environment. The official SWE-bench Docker image supplies it: for an
instance the local Python 3.11 cannot run (it imports removed stdlib), the pinned Python 3.9 container
runs the real hidden test - base fails with the genuine bug, gold passes. A manual x86 CI workflow
(`docker-batch.yml`, dispatch-only) batches this: `5/5` blocked instances resolve their hidden tests and
`3/3` property-testable ones are sound inside their pinned containers, environment fidelity and property
verification composing end to end on real cross-repo instances.

## 7. The transferable insight

Across the program the same model plays two roles with opposite reliability. As a direct verdict-giver
it is fooled by disguised hacks. As a property generator it is reliable, because its output is a
checkable artifact: a proposed property is verified by execution, so an unsound one surfaces as a
visible-test-anchor violation or a false positive rather than a silent acceptance. Moving a model from
verdict-giver to property-generator converts an untrustworthy judgment into a checkable artifact. This
is the paper's transferable claim, independent of the specific benchmark.

## 8. Limitations

The empirical scope is a set of bounded pilots, not a distributional result. Layer 3's reach is bounded
twice over. Structurally it is broad: the single-testable-function criterion is met by `405/500` =
`0.81` of the dataset. But property-derivability within that is narrow: even in sympy, the most
math-heavy repo, only `~0.10` of applicable instances live in a property-rich domain (elementary and
special functions, geometry, arithmetic). So Layer 3's natural domain is math-identity functions, and
the structural and algorithmic majority stays with Layers 1-2. This is the honest three-layer division
of labour rather than a defect: the deterministic detector and the LLM judge apply universally to any
diff, and the gold-free property layer is the specialist that recovers the both-miss class precisely
where a function admits a checkable identity. The property genuine-sound rates (`6/6`, `3/3`) are on
small hand-curated subsets within that domain. The native execution harness has a measured fidelity gap
that the Docker harness closes at the cost of per-instance images. None of the results is a SWE-bench
resolved-rate score or a comparison against a model leaderboard.

## 9. Related work

This work sits alongside the 2026 coding-agent verification literature on reward hacking and the limits
of outcome verifiers (the verification-horizon and adversarial hacker-fixer results), the reliability of
LLM-as-judge (its inconsistency, bias, and weak calibration), process and outcome reward modeling, and
metamorphic and property-based testing. Its specific position: static verification of an agent's diff -
by regex or by a strong model - cannot distinguish a correct general fix from a plausible special-case,
and execution on held-out inputs is the layer that recovers, made gold-free and automatic by using the
model as a property generator rather than a verdict-giver.

## 10. Reproduction

Each experiment under `experiments/iter1NN_*` has a pre-registered `HYPOTHESIS.md`, a `RESULT.md` held
below its evidence, proof artifacts, a receipt validated by `scripts/validate_receipts.py`, and a
learning record. The deterministic parts rerun in CI on Python 3.11 and 3.12; native-execution and
Docker transcripts are retained as observed evidence, and the x86 Docker batch is a dispatchable
workflow. The consolidated narrative and per-gate table are in `README.md`; the prior synthesis is in
`docs/COMPLETION_VERIFICATION_REPORT.md`.
