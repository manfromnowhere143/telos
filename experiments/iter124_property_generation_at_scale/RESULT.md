# Iteration 124 Result - Automatic Property Generation at Scale

Status: `PASS` (a descriptive measurement; the finding is a bound, not a success rate to celebrate).

## What this gate did

Tested whether iter122's automatic property generation generalizes. Across seven real Django
pure-function instances whose gold patches resolve under native execution, a fully automatic harness -
the model proposes the call expression, the input generator, and the property from the fix diff alone
- was generated and executed against the gold implementation, then classified.

## Result

| class | count | instances |
| --- | ---: | --- |
| clean sound | `2` | `14089`, `14373` |
| sound but mis-targeted | `1` | `11276` (call inferred as `html.escape`, but the task concerns the `make_list` filter) |
| too few valid inputs | `2` | `11206`, `13670` (the generated input generator or call errored on nearly all inputs) |
| harness error | `1` | `10999` (generated harness did not execute - syntax) |
| generation failed | `1` | `11848` (model returned unparseable JSON) |

- clean-sound rate: `2/7` = `0.28571429` (excluding the mis-targeted harness)

## The finding - the honest boundary

Full-auto property-harness generation does not reliably generalize across diverse pure functions. It
succeeds cleanly only when the function has a simple contract and an easily-synthesized input domain
(integer years, small integer lists). It fails in four distinct ways at scale: generation truncation,
syntactically invalid harnesses, input domains the model cannot synthesize valid samples for
(structured strings, numberformat argument dicts), and call-target mis-inference from the diff.

This corrects any impression that iter122 generalized cleanly. The mechanism is real - a model can
produce a checkable property, and when it does the property is sound and catches the both-miss class -
but the automation as a whole clears only two of seven real instances end to end. The bottleneck is
not the property idea; it is synthesizing a correct call harness and input domain automatically. That
is the same integration wall that makes most SWE-bench instances resistant to property-based testing.

## Implication

The third layer is deployable today with a human-in-the-loop harness (the two clean instances were
hand-verifiable) or on the simple-contract subset. Fully hands-off deployment needs a harness
synthesizer more reliable than a single diff-to-JSON prompt - for example, generating the call from
the function signature and existing test fixtures rather than the diff, retrying on failure, and
validating the input generator before trusting the property.

## Claim boundary

Supported: of seven real pure-function instances, `2` produced a clean sound auto-generated harness,
`1` was sound but tested the wrong function, and `4` failed across generation, syntax, input-domain,
and execution classes. Not supported: a benchmark, model, or state-of-the-art claim, or a
success-rate claim beyond these seven instances.

## Next gate

`iter125`: a harness synthesizer that generates the call from the function signature and validates the
input generator before use, retrying on failure, and re-measures the clean-sound rate on the same
seven instances.

## Evidence

- `proof/generated_harnesses.json` (the model-generated harnesses)
- `proof/soundness_classification.json` (observed native-execution classification)
- `proof/endpoint_results.json`, `proof/run_summary.json`
- `proof/valid/receipt_property_generation_at_scale.json`
- `scripts/run_property_generation_at_scale.py`
