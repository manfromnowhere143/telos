# Iteration 110 Result - Adversarial Hardening (Hacker-Fixer Loop)

Status: `PASS` (all pre-registered bars met).

## What this gate did

Ran one round of the hacker-fixer loop against the iter109 detector. An adversary evolved
source-only reward hacks - proxy completions that special-case the hidden input without touching
any test file, so the iter109 provenance signal cannot see them - across six evasion families.
The detector's source special-casing signal was then hardened, with the false-positive rate on
the 200 real gold patches re-measured after every change as a hard guardrail.

## Result

| metric | value |
| --- | ---: |
| baseline recall (iter109 detector) on adversarial hacks | `0.00000000` (0/1200) |
| hardened recall on adversarial hacks | `1.00000000` (1200/1200) |
| recall gain | `1.00000000` |
| guardrail false-positive rate on 200 real gold patches | `0.00000000` (0/200) |
| residual evasion families in this suite | `0` |

Per family (all `200/200`): `dict_membership`, `tuple_membership`, `set_membership`,
`ternary_literal`, `startswith_special`, `exception_swallow`.

The load-bearing fact is the pairing: recall on these evasions rose from `0` to `1.0` while the
false-positive rate on real human patches stayed at `0/200`. Every literal-keyed-constant-output
form the adversary produced was closed without misclassifying a single real fix. This is the
signature of an admissible hardening: the "specific input -> constant output" smell is real
enough to catch the hacks and rare enough in genuine fixes to spare them (a branch that returns a
*computed* value, tested in `test_ordinary_conditional_without_literal_output_is_not_special_casing`,
is correctly left alone).

## Honest framing (reward hacking is not "solved")

`residual_evasion_families = 0` means this suite is exhausted, not that evasion is exhausted. The
space of source-only proxy completions is unbounded: hashing the input, reading the expected value
from disk at runtime, floating-point tolerance games, or constructing the constant indirectly are
not in this suite and are not claimed to be caught. The contribution is narrower and real: a
repeatable loop in which each newly-caught evasion has so far cost zero false positives on real
human patches, plus a hardened detector that closes the specific evasion iter109 flagged as an
open limitation.

## Claim boundary

Supported: after one hacker-fixer round, detector recall on the six adversarial source-only
evasion families rose from `0` to `1.0` while the false-positive rate on 200 real gold patches
stayed at `0/200`, with no residual evasions in this suite. Not supported: robustness to unseen
evasions, a completeness guarantee, a benchmark or model result, or a state-of-the-art claim.

## Next gate

`iter111`: an LLM-judge steelman baseline on the same real corpus (bounded provider spend), so
the detector is compared against a strong verifier rather than only the execution-only default;
and container-executed hidden-test confirmation on a bounded slice.

## Evidence

- `proof/endpoint_results.json`
- `proof/residual_evasions.json`
- `proof/run_summary.json`
- `proof/valid/receipt_adversarial_hardening.json`
- `telos/tamper/adversarial.py`, `telos/tamper/detector.py`,
  `scripts/run_adversarial_hardening_loop.py`, `tests/test_tamper_detector.py`
