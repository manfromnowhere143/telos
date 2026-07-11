# Iteration 128 - Property Strategy by Function Type (closing 10999)

Status: pre-registered; executed with a mid-gate correction recorded transparently.

## Why this gate exists

Iter127 left `10999` (parse_duration) as an unsound-generated-property residual. The ledger's next
action was to retry generation with the visible-test anchor as feedback. This gate does that and, in
doing so, surfaces a structural rule about which gold-free property works for which kind of function.

## Method and the correction

First attempt: an anchor-in-the-loop generation - propose a property, check it against the test's
known-correct `(input_string, expected_timedelta)` pairs, retry on violation. It failed every retry.
On inspection the failure was a harness bug, not a model failure: the sound property for a parser is
an inverse round-trip whose input is a `timedelta`, but the check was being fed the test's
`(input_string, expected)` anchors, whose input convention does not match a `timedelta`-input harness.
Forcing string anchors onto a round-trip harness rejects valid properties.

Correction: test the inverse round-trip directly - `parse_duration(duration_string(td)) == td` for
random `timedelta` - which is self-validating and needs no external anchor.

## Endpoints

- `roundtrip_sound`: whether the inverse round-trip holds on gold over random inputs.
- resulting `genuine_sound_rate` over the seven instances.
- the property-strategy taxonomy by function type.

## Acceptance / interpretation rule

If the inverse round-trip is sound, `10999` is closed with a gold-free self-validating property and
the genuine-sound rate reaches `6/7`. The finding is that gold-free property strategy is
function-type-dependent: a contract property for pure transforms, an inverse round-trip for invertible
parsers/formatters; and that an anchor must match the harness input convention.

## Falsifiers

1. If the inverse round-trip is not sound on gold, `10999` is not closed; record the violations.
2. The mid-gate correction is recorded transparently rather than hidden.

## Execution envelope

- native execution only, no provider calls beyond the failed anchor-loop attempt (< `$0.02`),
- production/live-domain mutation: forbidden, benchmark/model/SOTA claim: forbidden.

## Claim boundary (pre-committed)

At most: "the inverse round-trip is a sound gold-free property for `parse_duration`, closing `10999`
and raising the genuine-sound rate to `6/7`; gold-free property strategy is function-type-dependent."
Not a benchmark, model, or SOTA claim.
