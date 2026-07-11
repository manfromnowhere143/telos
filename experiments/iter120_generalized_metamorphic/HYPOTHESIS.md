# Iteration 120 - Generalized Metamorphic Check (Random Held-Out Inputs)

Status: pre-registered design; executed and published in the same gate (native Django execution).

## Why this gate exists

Iter119 caught the both-miss class with a held-out input chosen by hand per instance. This gate tests
whether the metamorphic layer generalizes past hand-picking: it generates random held-out inputs
(seeded) and differential-tests the candidate against a trusted reference (the gold implementation),
flagging any input on which they diverge.

## Method

For each iter118 both-miss instance, apply the candidate (disguised hack) and the reference (gold),
run both on the same twelve seeded random inputs, and count divergent inputs. A non-zero divergence
count catches the hack without a hand-selected probe.

## Endpoints

- `divergent_inputs` per instance over twelve random inputs.
- `generalized_catch_rate`: fraction of both-miss hacks caught by random-input differential testing.

## Acceptance / interpretation rule

If random-input differential testing catches both hacks, the metamorphic layer generalizes on input
selection. The honest caveat - that this uses the gold implementation as the reference oracle, which
is not available at real verification time - is recorded, and oracle-without-gold (metamorphic
relations / properties) is named as the remaining open problem.

## Falsifiers

1. If a hack produces zero divergence over the random inputs, it is not caught; record the miss.
2. If a probe errors under either variant, it is invalid; fix or exclude it.

## Execution envelope

- native execution only, no provider calls, no GPU, no cloud,
- production/live-domain mutation: forbidden, benchmark/model/SOTA claim: forbidden.

## Claim boundary (pre-committed)

At most: "random-input differential testing against the gold reference caught `N/2` both-miss hacks,
diverging on M of 12 random inputs each, without a hand-picked probe." Not a benchmark, model, or SOTA
claim, and not a claim that the reference oracle is available without gold.
