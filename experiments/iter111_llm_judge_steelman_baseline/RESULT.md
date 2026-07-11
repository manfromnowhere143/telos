# Iteration 111 Result - LLM-Judge Steelman Baseline

Status: `PASS` (after a first-run null that its own falsifier caught and repaired).

## What this gate did

Built a strong LLM-judge baseline - Vertex `gemini-2.5-flash`, temperature 0, an engineered
reward-hack rubric - and scored it against the deterministic tamper detector on the *same* 100
candidates: 50 real gold patches and 50 reward hacks (25 test-deletion, 25 dict-lookup
special-casing) drawn deterministically from the iter109 real corpus.

## First run was a null, by its own rule

The first run returned `null`: `18%` of judge outputs were unparseable because extended-thinking
tokens truncated the JSON verdict mid-`reason`, tripping pre-registered falsifier #3 ("fix parsing
before claiming a comparison"). The fix disabled the thinking budget and added a verdict-recovery
regex; the re-run parsed `100%` of outputs. Both runs are retained; the null is not hidden.

## Result (re-run)

| strategy | false-positive rate (50 real gold) | recall (50 reward hacks) |
| --- | ---: | ---: |
| `gemini-2.5-flash` steelman judge | `0.00000000` | `1.00000000` |
| deterministic detector | `0.00000000` | `1.00000000` |

- judge/detector agreement: `1.00000000`
- provider calls: `100`; provider spend: `$0.04372820`; unparseable rate: `0.00000000`

## Interpretation (this weakens a comfortable assumption, and that is the point)

On this sample the steelman judge matched the detector exactly: it flagged zero of 50 real human
patches and caught every hack. This partially triggers pre-registered falsifier #1. The honest
reading is that **for obvious reward hacks, a well-engineered LLM judge is as accurate as the
deterministic detector.** The detector's advantage here is therefore not accuracy; it is:

- cost and latency: `$0` and no network versus `$0.044` per 100 calls;
- determinism and auditability: identical, line-level evidence every run, versus a model verdict
  that varies with prompt, model version, and sampling;
- no external dependency: it runs in CI with no provider credentials.

The value of the deterministic signal is a floor of guaranteed, free, reproducible coverage of the
mechanical reward hacks, under an LLM judge that adds semantic breadth at cost. Neither dominates.

## Open question this exposes

The regime where the two should finally diverge is stealth: source-only special-casing dressed to
look like a general fix (which the regex detector may miss but a strong judge may catch), and
subtle semantic non-completion (which the judge may rationalize but provenance ignores). That
divergence, not the easy-hack parity measured here, is the next gate.

## Claim boundary

Supported: on 100 real-gold and reward-hack candidates, a `gemini-2.5-flash` steelman judge and
the deterministic detector each scored `0.00` false-positive rate and `1.00` recall, agreeing on
every candidate, at `$0.044` provider spend. Not supported: a benchmark, model-quality,
robustness, or state-of-the-art claim, or any claim about the stealth regime.

## Next gate

`iter112`: a stealth-completion suite where judge and detector are expected to disagree, plus
container-executed hidden-test confirmation on a bounded slice.

## Evidence

- `proof/endpoint_results.json`, `proof/judge_decisions.json`, `proof/run_summary.json`
- `proof/valid/receipt_llm_judge_steelman.json`
- `telos/tamper/llm_judge.py`, `scripts/run_llm_judge_steelman.py`,
  `tests/test_llm_judge_parse.py`
