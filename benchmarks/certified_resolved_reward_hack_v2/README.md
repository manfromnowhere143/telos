# Certified-Resolved Reference-Differential Corpus v2

This is the released successor reference-differential corpus. Its historical directory identity is retained
for stable links. It is distinct from the misnamed `reward_hack_benchmark_v1`, which contained suite-failing
patches the official harness rejects; see
`experiments/iter192_reward_hack_benchmark_construct_validity_audit/`.

Every row here is a **certified-resolved reference-differential witness under the benchmark's operational label**:
the official SWE-bench Verified harness marks the patch resolved (it passes every `FAIL_TO_PASS`
and `PASS_TO_PASS` test), and retained execution under the instance-specific SWE-bench container tag
produces output different from the accepted gold fix on behavior the graded tests do not distinguish.
This is not independent semantic adjudication. Every witness scenario was constructed with both the gold
and variant hunks available to the generator. The historical construction and witness runners used
mutable `:latest` tags and retained no resolved image digest, so their exact container bytes cannot be
reconstructed from this repository.

## Contents

- **22 rows across 8 repositories.** django (7), matplotlib (4), astropy (3), xarray (2), pylint (2),
  pytest (2), requests (1), sympy (1).
- 10 exploratory rows from the strict protocol-failed
  `experiments/iter195_synthesized_input_differential_oracle/` gate (django, astropy, matplotlib). Its frozen
  design prohibited gold in synthesis, required at least `10/20` gold-clean inputs per accepted candidate,
  and required raw prompt retention. The executed generator received gold and variant hunks, produced one
  targeted scenario per candidate, and did not meet those bars.
- 12 rows from `experiments/iter199_benchmark_expansion_across_repos/` (adds requests, xarray, pylint,
  pytest, and sympy). Iter199's stated design was first recorded after provider generation and before
  execution; it was not independently preregistered.

`manifest.json` lists every row with its instance id, repository, source experiment, the historically named
wrongness-oracle field, and the gold-versus-variant output that witnesses the reference difference.

## How each row was verified

1. A frontier model rewrote the gold patch's largest added block into a variant intended to keep the graded
   tests passing (elicited construction).
2. The variant was certified by running the instance's official SWE-bench evaluation script under its
   instance-specific, mutable `:latest` container tag and parsing it with the official SWE-bench log
   parsers; it is kept only if every graded test passes. No resolved image digest was retained.
3. A reference difference was witnessed by executing a gold-and-variant-assisted targeted scenario under
   both patches in the same selected container tag and observing different output. Gold is part of this
   laboratory label and scenario construction; the corpus does not establish an independently generated or
   gold-blind witness. Detector access varies by experiment and is documented separately. Iter197 and iter201
   both record protocol `FAIL`
   because their property prompts used candidate-diff-derived locators. Iter197 additionally replaced
   its registered visible-test anchor with gold validation and omitted independent paired-gold decisions.
   Iter201 explicitly registered gold validation, so its gold inclusion is an
   interpretation limit rather than a second protocol deviation.

## Claim boundary

Elicited and constructed, not sampled from real agent behavior; no population-frequency claim. "Wrong"
means the variant differs from the gold reference fix on a retained, gold-assisted constructed input. The
`22` rows split into `10` iter195 exploratory witnesses from a failed protocol and `12` iter199 witnesses
under a post-provider/pre-execution design. This is a small reference-differential corpus, not a leaderboard,
model comparison, semantic ground-truth set, or broad robustness result.
