# Iteration 124 - Automatic Property Generation at Scale

Status: pre-registered before execution. Frozen before the soundness classification was known.

## Why this gate exists

Iter122 showed a model can generate a sound metamorphic property on two instances. This gate asks
whether that generalizes: across a larger set of real pure-function SWE-bench instances, how often
does a fully automatic harness (the model proposes the call, the input generator, and the property
from the diff alone) produce a clean, sound, executable oracle? The honest answer - including failure
modes - bounds how far the automated third layer reaches today.

## Method

Seven real Django pure-function instances whose gold patches resolve under native execution. For the
five not already covered, `gemini-2.5-flash` is given the fix diff and asked for JSON
`{call, make_input, check}`. Each harness is executed against the gold implementation on twenty-five
seeded random inputs and classified:

- `sound`: at least ten valid inputs and zero property violations on gold;
- `unsound_or_miswired`: violations on gold;
- `too_few_valid_inputs`: the input generator or call errored on nearly all inputs;
- `harness_error`: the harness did not execute;
- `generation_failed`: the model did not return parseable JSON.

## Endpoints

- `clean_sound_rate`: fraction of instances classified `sound`.
- the failure taxonomy: counts per non-sound class.

## Acceptance / interpretation rule

Descriptive. Whatever the rate, it is recorded with the failure taxonomy. A rate below `1.0` is the
expected and honest outcome and identifies exactly where full automation breaks (generation,
input-domain synthesis, call-target inference).

## Falsifiers

1. A `sound` classification is not a correctness guarantee: a harness can be internally consistent yet
   test the wrong function (mis-inferred call target). Such cases are flagged in the result.
2. If every harness is sound, automation generalizes cleanly; if not, the failure modes are the
   finding.

## Execution envelope

- native execution + one generation call per new instance (< `$0.02`),
- production/live-domain mutation: forbidden, benchmark/model/SOTA claim: forbidden.

## Claim boundary (pre-committed)

At most: "of seven real pure-function instances, `N` produced a clean sound auto-generated harness and
`7-N` failed, distributed across the recorded failure classes." Not a benchmark, model, or SOTA claim.
