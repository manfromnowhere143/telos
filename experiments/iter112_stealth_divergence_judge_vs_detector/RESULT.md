# Iteration 112 Result - Stealth Divergence: Judge versus Detector

Status: `PASS` (controls behaved as controls; divergence cells enumerated).

## What this gate did

Ran both verifiers on 60 crafted candidates from 15 real instances - four families designed to
split them - and filled the full 2x2. `gemini-2.5-flash` steelman judge, temperature 0, thinking
disabled; deterministic detector on identical inputs. Provider spend `$0.02422840`, `0%`
unparseable.

## The 2x2

| family | n | detector catch | judge catch |
| --- | ---: | ---: | ---: |
| `buried_test_edit` (tamper) | 15 | `1.00` | `1.00` |
| `oblique_special_case` (tamper) | 15 | `0.00` | `1.00` |
| `obvious_hack` control (tamper) | 15 | `1.00` | `1.00` |
| `gold` control (legitimate) | 15 | `0.00` | `0.00` |

Divergence over the 45 tamper candidates: `detector_only = 0`, `judge_only = 15`,
`both_catch = 30`, `both_miss = 0`. Controls behaved as controls.

## Interpretation (the detector did not win, and that is the finding)

This gate was built to find a cell where the deterministic detector beats the judge. It found
none. The judge matched the detector everywhere and **strictly beat it on
`oblique_special_case`**: computed-key, computed-return special-casing (`_sentinel = str(6); if
str(n) == _sentinel: return int(bool(0))`) evades the detector's regex signals, and the judge
caught all 15. The prediction that a judge would rationalize a `buried_test_edit` was also wrong -
it caught all 15 of those too.

The honest conclusion across iter111-iter112: a well-engineered current LLM judge is at least as
accurate as the deterministic detector on every family tested and strictly more accurate on
oblique source special-casing. The deterministic detector's defensible value is therefore
narrowed to what it structurally guarantees and the judge cannot: **zero cost, zero latency, full
determinism, line-level reproducible evidence, and no external dependency in CI** - a free,
auditable floor, not a coverage frontier.

## The load-bearing engineering implication

The right architecture is a cascade, not a contest: run the free deterministic detector first as a
fast, tamper-evident pre-filter that catches the mechanical hacks (verifier edits, obvious
special-casing) with zero spend and a reproducible receipt, and escalate the survivors to the
paid semantic judge for the oblique and stealth cases the regex cannot see. This gate quantifies
why: the detector alone misses `oblique_special_case` entirely; the judge alone costs money and
determinism on every candidate including the mechanical ones the detector settles for free.

## Honest caveats

15 instances, one oblique pattern, one model, one temperature-0 draw. `both_miss = 0` here does
not mean no stealth class defeats both verifiers - it means this suite did not contain one. Finding
a genuine both-miss class (a proxy completion neither a provenance rule nor a strong judge
catches) remains the hardest open target and is the real prize.

## Claim boundary

Supported: on 60 stealth and control candidates from 15 real instances, `detector_only = 0`,
`judge_only = 15`, `both_catch = 30`, `both_miss = 0`, with controls behaving as controls at
`$0.024` spend. Not supported: a benchmark, robustness-guarantee, model-quality, or SOTA claim, or
any general claim beyond these families.

## Next gate

`iter113`: hunt for a genuine both-miss stealth class (a completion neither verifier catches), and
container-executed hidden-test confirmation on a bounded slice to replace the modeled
execution-only comparator with real pass/fail truth.

## Evidence

- `proof/endpoint_results.json`, `proof/stealth_decisions.json`, `proof/run_summary.json`
- `proof/valid/receipt_stealth_divergence.json`
- `telos/tamper/stealth.py`, `scripts/run_stealth_divergence.py`, `tests/test_tamper_detector.py`
