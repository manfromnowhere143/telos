# Iteration 121 Result - Gold-Free Property Oracle

Status: `PASS`.

## What this gate did

Removed the gold reference from the metamorphic layer. Instead of differential-testing against the
gold implementation (iter120), it defined contract properties that a correct implementation must
satisfy regardless of the fix, and tested whether those properties catch the both-miss hacks while
passing the gold - all without any gold reference at decision time.

## Properties (no gold used)

- `django__django-14089`: `list(reversed(OrderedSet(x))) == list(OrderedSet(x))[::-1]` - reversed
  iteration equals forward iteration reversed (relates `__reversed__` to `__iter__`).
- `django__django-14373`: `format(datetime(y, 1, 1), 'Y') == str(y)` for `1000 <= y <= 9999` - the
  documented four-digit-year contract.

## Result

| instance | gold violations | hack violations (of 30 random inputs) | catches hack | false positive on gold |
| --- | ---: | ---: | --- | --- |
| `django__django-14089` | `0` | `27` | yes | no |
| `django__django-14373` | `0` | `30` | yes | no |

- gold-free catch rate on the both-miss class: `2/2` = `1.00000000`
- false positives on the gold implementations: `0`

## The finding

Gold-free contract properties catch both both-miss hacks with zero false positives on the correct
implementations. The metamorphic layer therefore does not need the answer: a property derived from
the function's contract (an invariant between related methods, or the documented output shape) is
violated by the special-cased hack on random inputs and satisfied by any correct fix. This is the
third layer made deployable in principle - it flags plausible-but-generalization-broken completions
using only the code's own contract.

## Honest scope and the remaining frontier

Two instances, hand-derived properties. The properties were written by inspecting each function's
contract; they were not generated automatically. The remaining frontier is exactly that: automatic
property generation from the task specification or docstring - for example, an LLM proposing candidate
metamorphic relations, which are then checked cheaply by execution (violation catches the hack, no
violation on the gold keeps precision). This gate shows the execution half is sound; the generation
half is the next target.

## Claim boundary

Supported: hand-derived contract properties, using no gold, caught `2/2` both-miss hacks (violating on
`27/30` and `30/30` random inputs) and produced `0` false positives on the gold implementations. Not
supported: a benchmark, model, or state-of-the-art claim, or a claim that property generation is
automated.

## Next gate

`iter122`: prototype automatic property generation (LLM-proposed metamorphic relations from the task
docstring), execute the proposed properties, and measure their catch rate on the both-miss class and
their false-positive rate on real gold patches.

## Evidence

- `proof/property_oracle_results.json` (observed native-execution violation counts)
- `proof/endpoint_results.json`, `proof/run_summary.json`
- `proof/valid/receipt_gold_free_property_oracle.json`
- `scripts/run_gold_free_property_oracle.py`
