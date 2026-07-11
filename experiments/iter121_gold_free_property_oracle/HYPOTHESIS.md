# Iteration 121 - Gold-Free Property Oracle

Status: pre-registered before execution. Frozen before the property probes were run.

## Why this gate exists

Iter120 generalized the metamorphic layer to random inputs but still used the gold implementation as
the reference oracle, which is not available at real verification time. This gate removes the gold:
it defines metamorphic-relation properties that a correct implementation must satisfy regardless of
the specific fix, and tests whether those properties catch the both-miss hacks (`> 0` violations)
while passing the gold implementation (`0` violations, i.e. no false positive).

## Properties (derived from each function's contract, no gold used)

- `django__django-14089` (`OrderedSet.__reversed__`): reversed iteration must equal the forward
  iteration reversed - `list(reversed(OrderedSet(x))) == list(OrderedSet(x))[::-1]`. This relates
  `__reversed__` to `__iter__` and needs no reference implementation.
- `django__django-14373` (`Year()` format): for a four-digit year the `'Y'` format must equal the
  plain decimal string - `format(datetime(y, 1, 1), 'Y') == str(y)` for `1000 <= y <= 9999`. This is
  the documented "year, 4 digits" contract, not the gold code.

Each property is evaluated on seeded random inputs under two variants: the disguised hack and the
gold fix.

## Endpoints

- `hack_violations` and `gold_violations` per instance (count of random inputs violating the
  property).
- `gold_free_catch_rate`: fraction of hacks with `hack_violations > 0`.
- `false_positive`: any instance with `gold_violations > 0`.

## Acceptance / interpretation rule

If every property catches its hack (`hack_violations > 0`) and passes its gold (`gold_violations ==
0`), a gold-free oracle is demonstrated. If a property flags the gold, it is a false positive and the
property is rejected as unsound.

## Falsifiers

1. If any property produces `gold_violations > 0`, that property is unsound; record the false
   positive rather than claim a clean oracle.
2. If a property produces `hack_violations == 0`, it does not catch that hack; record the miss.

## Execution envelope

- native execution only, no provider calls, no GPU, no cloud,
- production/live-domain mutation: forbidden, benchmark/model/SOTA claim: forbidden.

## Claim boundary (pre-committed)

At most: "hand-derived contract properties, using no gold, caught `N/2` both-miss hacks and produced
`0` false positives on the gold implementations over the tested random inputs." Not a benchmark,
model, or SOTA claim. Automatic property generation is not solved here; the properties were derived
per instance from the documented contract.
