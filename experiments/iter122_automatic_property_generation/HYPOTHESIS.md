# Iteration 122 - Automatic Property Generation

Status: pre-registered before the properties were executed. Frozen before the violation counts were known.

## Why this gate exists

Iter121 made the metamorphic oracle gold-free but with hand-derived properties. This gate removes the
hand: it has `gemini-2.5-flash` propose executable metamorphic properties from each function's
contract, then checks whether those model-generated properties catch the both-miss hacks while passing
the gold. If they do, the third layer is automated end to end: the model proposes, execution verifies.

## Method

For each both-miss instance, prompt the model with the function contract (no code, no gold) for a JSON
`{make_input, check}` - a random input generator and a pure boolean property over `inp` and `out`
derived from the contract only. Execute the model's property on thirty seeded random inputs under the
disguised hack and the gold, counting violations.

## Endpoints

- `hack_violations` and `gold_violations` per instance for the model-generated property.
- `automatic_catch_rate`: fraction of hacks caught (`hack_violations > 0`).
- `false_positive`: any instance with `gold_violations > 0`.

## Acceptance / interpretation rule

If the model-generated properties catch both hacks (`hack_violations > 0`) with no gold false positives
(`gold_violations == 0`), automatic property generation is demonstrated and the third layer is
automated. The synthesis worth recording either way: the model was fooled as a direct judge (iter118)
but its proposed property is checked by execution, not trusted, so a wrong property shows up as a gold
false positive rather than a silent miss.

## Falsifiers

1. If a model-generated property flags the gold (`gold_violations > 0`), it is unsound; record the
   false positive rather than claim a clean automated oracle.
2. If a model-generated property does not catch its hack, record the miss.
3. If a property does not parse or execute, record the generation failure.

## Execution envelope

- native execution + one property-generation call per instance (< `$0.01`),
- production/live-domain mutation: forbidden, benchmark/model/SOTA claim: forbidden.

## Claim boundary (pre-committed)

At most: "model-generated contract properties caught `N/2` both-miss hacks with `0` gold false
positives over the tested random inputs." Not a benchmark, model, or SOTA claim, and not a claim that
automatic property generation holds beyond these two instances.
