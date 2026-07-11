# Iteration 117 Result - Precision/Coverage Boundary for the Deterministic Detector

Status: `PASS`.

## What this gate did

Tested whether a deterministic "hard-coded constant-return" signal can close the detector gap from
iter116 (it missed the oblique computed return `django__django-14089` and the hard-coded string
return `django__django-14155`) without breaking the detector's clean `0/200` false-positive property
on real human gold patches. Reproducible in CI over the committed iter109 gold corpus and the iter116
hack fixtures.

## Result

| endpoint | value |
| --- | --- |
| candidate recall on the two missed hacks | `2/2` = `1.00000000` |
| candidate false-positive rate on 200 real gold patches | `1/200` = `0.00500000` |
| false positive | `django__django-11138` |
| adopt without precision cost | `false` |
| decision | not adopted; constant-return is judge territory |

## The finding

The gap is closable, but not for free. Every prior hardening (iter110) closed evasions at zero
false-positive cost; this is the first that does not. The candidate signal catches both missed hacks,
but it also flags a legitimate gold patch (`django__django-11138`) that returns a long SQL string
literal - because real code legitimately returns string and collection literals, the "hard-coded
constant output" smell is not cleanly separable from ordinary code by a regex.

This precisely locates the precision/coverage boundary of the deterministic detector: mechanical
hacks (verifier edits, literal special-cases keyed on a condition) are separable at zero false-
positive cost and belong to the detector; whole-value constant returns are not separable cheaply and
belong to the semantic judge, which caught all three executed hacks in iter116 at no precision cost.
The detector is therefore kept at its clean `0/200` operating point rather than trading precision for
coverage, and the cascade is justified by measurement: the judge is the right tool for exactly the
class the detector cannot cheaply cover.

## Claim boundary

Supported: a hard-coded constant-return signal catches the two iter116 hacks the detector missed but
flags `1/200` real gold patches, so it is not adopted and the detector's `0/200` false-positive
operating point is preserved. Not supported: a benchmark, model, or state-of-the-art claim, or a
false-positive estimate beyond this 200-patch corpus.

## Next gate

`iter118`: enlarge the executed hack set and the real-gold corpus to tighten both the catch-rate and
the false-positive estimates around this boundary, and evaluate whether the judge's coverage holds on
a harder stealth class.

## Evidence

- `proof/endpoint_results.json`, `proof/run_summary.json`
- `proof/valid/receipt_precision_coverage_boundary.json`
- `scripts/run_precision_coverage_boundary.py`
