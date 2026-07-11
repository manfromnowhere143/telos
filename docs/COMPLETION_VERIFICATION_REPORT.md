# Verifying Agent Code Completions: A Three-Layer Result on Real SWE-bench Trajectories

A research report synthesizing experiments iter109-iter123 of the Telos program. All results are
bounded pilots on real data; none is a benchmark leaderboard score, a model result, or a
state-of-the-art claim. Every number below is reproduced by a committed runner and receipt.

## Problem

When an autonomous coding agent claims a task is done, the visible test suite is the usual proof. But
an outcome verifier the agent can influence is gameable: the agent can edit the tests, weaken
assertions, hard-code the expected output, or write code that only special-cases the visible input.
The question of this program: can an external protocol tell real completion from proxy gaming, on
real agent-style completions, without trusting the agent's own signal?

The substrate is the real `princeton-nlp/SWE-bench_Verified` dataset. A candidate is a raw unified
diff plus the public `FAIL_TO_PASS` test ids. Ground truth is the real hidden test; where noted, it is
executed natively (Python 3.11, Django `tests/runtests.py`) rather than modeled.

## The result in one paragraph

Completion verification of agent code needs three layers, and each exists because the one before it
provably fails. A free deterministic detector reading only the diff catches mechanical hacks. A strong
LLM judge catches oblique and hard-coded hacks the detector cannot see. Neither catches a third class
- plausible-but-generalization-broken completions that pass the visible test - which is caught only by
executing the code on inputs the agent never saw. That third layer was made automatic and gold-free:
a model proposes a metamorphic property from the contract, the visible test rejects unsound proposals,
and execution on random inputs catches the hack. The load-bearing insight is that the same model that
is fooled as a direct judge is reliable as a property generator, because a proposed property is
checked by execution rather than trusted.

## Layer 1 - deterministic detector (iter109-iter110, iter115, iter117)

A detector reading only the candidate diff and the public `FAIL_TO_PASS` ids - never a label - flags
the documented mechanical reward hacks: editing the tests that must fail-to-pass, `conftest.py`, or
pytest config; weakening assertions; literal-keyed constant-output special-casing; receipt-digest
tampering.

- False positives on real human gold patches: `0/200` (iter109), holding through one adversarial
  hacker-fixer round that raised source-only evasion recall from `0` to `1.0` at still `0/200`
  (iter110), and confirmed at `0/18` on gold patches whose resolution was verified by real execution
  (iter115).
- Its precision/coverage boundary is measured, not assumed: a candidate signal for hard-coded
  constant returns catches two hacks the detector missed but costs `1/200` real false positives
  (iter117) - the first hardening that is not free, so it is not adopted and that class is handed to
  Layer 2.

## Layer 2 - LLM judge (iter111, iter112, iter116)

A `gemini-2.5-flash` judge with an engineered rubric, run at temperature 0, sees the same inputs as
the detector.

- On obvious hacks it ties the detector: `0.00` false-positive rate, `1.00` recall, `$0.044` for 100
  candidates (iter111).
- It strictly beats the detector on oblique special-casing: on 60 stealth candidates,
  `detector_only=0`, `judge_only=15`, `both_catch=30` (iter112).
- On reward hacks confirmed by native execution to pass the real hidden test, the catch rate is
  execution-only `0/3`, detector `1/3`, judge `3/3` (iter116).

The judge's value is semantic coverage; the detector's value is cost, determinism, and reproducible
CI evidence. The right composition is a cascade: the free detector first, the paid judge on
survivors.

## Layer 3 - held-out-input execution (iter113, iter118-iter123)

The cascade is not sufficient. Iter118 red-teamed it and broke it: two disguised completions -
`iter(sorted(self.dict, reverse=True))` presented as a reversal, `'0%03d' % year` presented as
zero-padding - pass the real hidden test, evade the detector, and are called legitimate by the judge,
while being wrong on inputs the test never exercises. No static inspection, by regex or by model,
separates a correct general fix from a plausible one that special-cases the visible input.

The defense is execution on held-out inputs:

- A held-out input catches both both-miss hacks by output divergence from gold; the visible test,
  detector, and judge each catch `0/2` while metamorphic execution catches `2/2` (iter119).
- Seeded random inputs generalize it past a hand-picked probe: `2/2` caught, diverging on `10/12` and
  `8/12` random inputs (iter120).
- Contract properties remove the gold reference: `list(reversed(OrderedSet(x))) == list(OrderedSet(x))[::-1]`
  and `format(y,'Y') == str(y)` catch `2/2` at `0` false positives on gold (iter121).
- A model generates those properties from the contract: `gemini-2.5-flash` proposes properties that
  catch `2/2` at `0` gold false positives (iter122).
- Unsound proposed properties are rejected without gold, by anchoring on the visible test - a
  known-correct pair the agent had to satisfy: the anchor keeps `2/2` sound properties and rejects
  `2/2` unsound ones (iter123).

The automated third layer is therefore gold-free end to end: propose, filter on the visible test,
execute on random inputs.

## The synthesis

Across the program the same model plays two roles with opposite reliability. As a direct judge it is
fooled by disguised hacks (iter118). As a property generator it is reliable (iter122), because its
output is a checkable artifact: a proposed property is verified by execution, so an unsound one
surfaces as a visible-test-anchor violation or a gold false positive rather than a silent acceptance.
Moving a model from verdict-giver to property-generator converts an untrustworthy judgment into a
checkable artifact. This is the report's transferable claim.

## What is not claimed, and the honest boundaries

- No benchmark, resolved-rate, model, or state-of-the-art claim. Every gate holds its language below
  its evidence.
- Layer-3 results are on two both-miss instances with hand-supplied contracts; the properties happened
  to be sound. At scale, some model-proposed properties will be unsound and require more anchors
  (`PASS_TO_PASS`) or multiple candidates.
- Native execution has a measured fidelity gap: `17/18` Django gold patches resolved under the
  lightweight harness (iter115); one needs the fuller official environment.
- Property-based execution applies to instances with callable, near-pure functions; most SWE-bench
  instances are integration-level and need fixtures the pilot does not build.

## Reproduction

Each experiment directory under `experiments/iter1NN_*` contains a pre-registered `HYPOTHESIS.md`, a
`RESULT.md` below its evidence, proof artifacts, and a receipt validated by
`scripts/validate_receipts.py`. The deterministic parts (detector verdicts, property evaluation) rerun
in CI on Python 3.11 and 3.12; native-execution transcripts are retained as observed evidence.

## Open frontier

Scale the generate-filter-execute pipeline across more instances; strengthen the visible-test anchor
with `PASS_TO_PASS`; measure how the surviving-unsound-property rate falls as the anchor set grows; and
build the fixtures that extend held-out-input execution beyond near-pure functions.
