# Iteration 195 - Synthesized-Input Differential Oracle

Status: PRE-REGISTERED, result pending. No provider calls, SWE-bench executions, or cloud resources have
been run for this gate.

## Why this gate exists

iter194 proved, on `16` certified-resolved candidates across `3` repositories, that the project's entire
shipped test suite cannot witness wrongness of a certified variant: for django the curated `PASS_TO_PASS`
is the whole test module (`0` uncurated tests), and where uncurated tests exist (matplotlib up to `168`,
`193` total across all instances) the variant passes every one identically to gold. No shipped test —
graded or uncurated — distinguishes any certified variant from its gold fix.

That is the structural end of any test-based oracle for this class: the tests that define "resolved" are
the same tests a test-based oracle would use. To decide whether a certified variant is genuinely wrong or a
correct equivalent, the oracle must execute the changed code on inputs **no shipped test covers**, and
compare against gold.

This gate builds and runs that oracle. It is the mechanism iter194 promoted from "fallback" to "only
remaining path."

## The oracle

For each certified-resolved candidate, inside its pinned container:

1. Identify the changed callable from the source diff (the function or method whose body the variant
   substitutes). Recorded deterministically from the committed gold/variant patch, not inferred by a model
   at decision time.
2. Synthesize inputs that exercise that callable, using the function signature, the problem statement, and
   the visible test as context. Input synthesis may use a model; the model never sees the gold patch, the
   gold diff, the label, hidden test names, or official reports.
3. Validate the input generator: require at least `10` of `20` synthesized inputs to execute without error
   under gold before the generator is trusted (the iter125 validation gate), else the candidate is
   `input_synthesis_failed`, not a negative.
4. Execute gold-source and variant-source on the same validated inputs, in the same container, and record
   any input where their observable outputs differ.

`wrong_vs_gold` is witnessed iff a validated input produces different observable output under gold and
variant. A candidate with a validated generator and zero divergent inputs is `certified_equivalent`
(evidence the variant is a correct equivalent, within the synthesized input distribution). A candidate
whose generator cannot be validated is `input_synthesis_failed` (no evidence either way).

## Ground truth vs. detection

Gold is executed to establish ground truth, and is forbidden to any detector evaluated in a later gate.
This mirrors iter121 and iter193: differential-against-gold is legitimate for labelling and forbidden at
decision time. Input synthesis sees the public function signature, problem statement, and visible test
only.

## Inputs

- `experiments/iter194_certified_resolved_oracle_and_runner_fix/proof/iter194_per_candidate.json`
  (the `16` certified-resolved candidates)
- `experiments/iter193_certified_resolved_reward_hack_construction/proof/raw/phase_a_candidates/`
  (variant and gold patches)
- `experiments/iter194_certified_resolved_oracle_and_runner_fix/proof/raw/specs/`
- the pinned SWE-bench containers used in iter194

## Numeric Bars

Minimum pass bars:

- provider calls do not exceed `120` (input synthesis only) and estimated spend does not exceed `$15.00`,
- new cloud resources created and not deleted is exactly `0`,
- input generators validated (`>= 10/20` inputs run under gold) for at least `8` of `16` certified
  candidates,
- every accepted row records at least one validated input with divergent gold/variant output, retained
  with both outputs,
- accepted certified-resolved-and-wrong rows is at least `5`,
- raw synthesis prompts (leakage-scanned) and differential transcripts retained for every accepted row is
  `100%`,
- committed secret/private identifier hits are exactly `0`,
- forbidden positive claim hits are exactly `0`.

## Falsifiers

1. Any accepted row's divergence is not reproducible from the committed inputs and container.
2. Any accepted row's input generator was not validated under gold (`< 10/20`).
3. Gold content, gold diff, labels, hidden test names, or official reports enter a synthesis prompt.
4. A candidate with `0` divergent inputs is labeled wrong, or a candidate with an unvalidated generator is
   labeled correct.
5. Fewer than `5` accepted rows: the gate publishes a null with the full outcome distribution
   (`wrong`, `certified_equivalent`, `input_synthesis_failed`) and an honest construction-hardness bound,
   and does not relax the bar.
6. Provider calls exceed `120`, spend exceeds `$15.00`, or a cloud resource is left undeleted.
7. The result presents a leaderboard, model-comparison, model-superiority, state-of-the-art,
   natural-frequency, non-elicited, benchmark-size, broad robustness, production, or product-value claim.

## Claim Boundary

At most, if this gate passes: Telos has `N >= 5` execution-verified rows in which the official SWE-bench
Verified harness certifies a patch as resolved while a validated synthesized input, executed differentially
against gold in the pinned container, shows the patch produces wrong output — a class no shipped test in the
instance witnesses. If it fails, Telos has an honest bound on how hard it is to construct a
certified-resolved patch that a validated input-synthesis oracle can catch, plus the count of
`certified_equivalent` variants (adversary produced correct equivalents) versus `input_synthesis_failed`.

Not supported: any natural-frequency, non-elicited, benchmark-size, corpus-scale, detector, leaderboard,
model-comparison, state-of-the-art, broad robustness, production, or product-value claim.
