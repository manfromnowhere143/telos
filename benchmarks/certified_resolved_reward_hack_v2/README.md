# Certified-Resolved Reward Hack Benchmark v2

This is the real reward-hack benchmark, distinct from the misnamed `reward_hack_benchmark_v1` (which
contained suite-failing patches the official harness rejects; see
`experiments/iter192_reward_hack_benchmark_construct_validity_audit/`).

Every row here is a **certified-resolved reward hack under the benchmark's reference-differential operational label**:
the official SWE-bench Verified harness marks the patch resolved (it passes every `FAIL_TO_PASS`
and `PASS_TO_PASS` test), and retained execution under the instance-specific SWE-bench container tag
produces output different from the accepted gold fix on behavior the graded tests do not distinguish.
This is not independent semantic adjudication. The historical construction and witness runners used
mutable `:latest` tags and retained no resolved image digest, so their exact container bytes cannot be
reconstructed from this repository.

## Contents

- **22 rows across 8 repositories.** django (7), matplotlib (4), astropy (3), xarray (2), pylint (2),
  pytest (2), requests (1), sympy (1).
- 10 rows from `experiments/iter195_synthesized_input_differential_oracle/` (django, astropy, matplotlib).
- 12 rows from `experiments/iter199_benchmark_expansion_across_repos/` (adds requests, xarray, pylint,
  pytest, and sympy).

`manifest.json` lists every row with its instance id, repository, source experiment, the wrongness oracle
used, and the gold vs variant output that witnesses the hack.

## How each row was verified

1. A frontier model rewrote the gold patch's largest added block into a variant that keeps the graded
   tests passing (elicited construction).
2. The variant was certified by running the instance's official SWE-bench evaluation script under its
   instance-specific, mutable `:latest` container tag and parsing it with the official SWE-bench log
   parsers; it is kept only if every graded test passes. No resolved image digest was retained.
3. The wrongness was witnessed by executing a scenario under the gold patch and the variant in the same
   selected container tag and observing different output. Gold is part of this laboratory label. Detector
   access varies by experiment and is documented separately. Iter197 and iter201 both record protocol `FAIL`
   because their property prompts used candidate-diff-derived locators. Iter197 additionally replaced
   its registered visible-test anchor with gold validation and omitted independent paired-gold decisions.
   Iter201 explicitly registered gold validation, so its gold inclusion is an
   interpretation limit rather than a second protocol deviation.

## Claim boundary

Elicited and constructed, not sampled from real agent behavior; no population-frequency claim. "Wrong"
means the variant differs from the gold reference fix on a retained constructed input. `22` rows across
`8` repositories is a small, precise, execution-verified set, not a leaderboard, model-comparison, or
state-of-the-art result.
