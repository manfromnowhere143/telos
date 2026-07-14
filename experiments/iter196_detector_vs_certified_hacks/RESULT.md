# Iteration 196 Result - Detectors vs. Certified-Resolved Reward Hacks (Detector A)

Status: **partial** — one of the two pre-registered detectors is delivered. This gate pre-registered a
judge panel (Detector A) and a gold-free execution oracle (Detector B). Detector A is complete and reported
below. Detector B is a substantial in-container build and is promoted to its own gate,
`experiments/iter197_gold_free_oracle_vs_certified_hacks/`, rather than rushed here. This result does not
claim the gate's `>=` both-detector bar; it reports Detector A and names what remains.

Provider calls `44` (`~$2.64`), well under the `160` / `$25.00` ceilings.

## Detector A — frontier LLM judge panel

A 2-model panel — `gpt-5.6-terra` (OpenAI) and `claude-opus-4-8` (Anthropic) — judged each candidate from
the diff, the public task, and the visible test only. The third iter174 default, `gemini-2.5-flash`
(Vertex), was blocked on ADC re-authentication unavailable in this environment (verified pre-data;
disclosed in HYPOTHESIS.md). Rows: the `10` iter195 certified-resolved reward hacks (positives), the `10`
gold patches for the same instances (correct controls), and the `2` certified-equivalent variants (hard
controls).

### Result (single run; judge verdicts are stochastic)

| | recall on 10 hacks | FP on 10 gold controls | FP on 2 equivalent controls |
| --- | ---: | ---: | ---: |
| `gpt-5.6-terra` | `7` (`+1` legit, `2` nondecision) | `1` | `1` |
| `claude-opus-4-8` | `6` (`+3` legit, `1` nondecision) | `1` | `1` |
| **any_catch** (>=1 flags) | **`7/10`** | `1/10` | `1/2` |
| unanimous (both flag) | `6/10` | `0/10` | `0/2` |

The headline: a frontier judge panel, reading only the diff, catches `7/10` of these certified-resolved
reward hacks — the class the official harness certifies and all `193` shipped tests miss — at a `1/10`
false-positive rate on correct gold patches. Judges are **not** useless on this class. This matches the
external literature (Control Tax, arXiv:2506.05296: monitors carry real signal; the honest story is a
recall/precision tradeoff, not "judges fail"). It also means an execution-grounded oracle (Detector B, next
gate) must beat `7/10` recall or improve precision to justify itself here.

### Two methodology issues found and handled (world-contact, Standard 9)

1. **A leakage guard fired, and it was mostly a false alarm — but not entirely.** The first automated guard
   matched a shared `200`-char diff prefix and reported `10/10` "leakage." That was wrong: a variant shares
   its diff header and context with gold by construction, and that is the candidate's own content, not the
   gold solution. The corrected guard checks only gold-*distinctive* added lines present in the candidate:
   `2/10` (django-11211, matplotlib-24627), where block-substitution left one gold line intact. Those are
   the candidate's real lines, the judge never receives the gold patch as a comparison reference, and a
   shared correct-looking line biases toward **missing** the hack, not catching it. Reported, per-row, in
   `judge_panel_results.json`; the effect direction is against recall.

2. **The incumbent's nondecisions were nearly reported as "legitimate."** The first run set OpenAI
   `max_completion_tokens=200`; gpt-5.6-terra spent that budget on hidden reasoning and returned unparseable
   content on `18/22` rows. Counting those as "legitimate" would have understated its recall and misstated
   the result. Raised to the iter177-validated `1536`; nondecisions dropped to `2` hack rows. The result
   above is the corrected run.

Both were caught because the analysis had bars that could fail on reality, not just internal counters —
the exact discipline Standard 9 codifies.

## What remains: Detector B (promoted to iter197)

The gold-free execution oracle — a model proposes an executable property from the public task and visible
test only (no gold), validated on the visible-test anchor (iter126), executed in-container against the
candidate — is the novel, execution-grounded instrument. On framework-internal functions with low
property-derivability (iter139: `~0.10`), it is a substantial build with its own failure modes, and it
runs on CI rather than locally. It is pre-registered as `iter197` with Detector A's `7/10` as the baseline
it must clear. Splitting it out is disclosed, not silent: this gate delivers Detector A only.

## Claim Boundary

Supported: on `10` execution-verified certified-resolved reward hacks and `12` controls, a 2-model frontier
judge panel (gpt-5.6-terra + claude-opus-4-8; gemini blocked) reading diff + task + visible test flags
`7/10` hacks (any_catch) at `1/10` gold false positives and `1/2` equivalent false positives, in a single
stochastic run, with `2` rows carrying a coincidental shared gold line that biases against recall.

Not supported: any both-detector comparison (Detector B not yet run); any leaderboard, model-superiority,
state-of-the-art, natural-frequency, benchmark-size, broad robustness, production, or product-value claim;
any claim from a single run treated as a stable rate.

## Evidence

- `proof/judge_panel_results.json` — metrics and per-row verdicts (with per-row shared_gold_lines)
- `proof/valid/receipt_detector_a_judge_panel.json`

Regenerate (requires `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`; spends `~$2.64`):

```bash
python3 scripts/run_iter196_judge_panel.py
```
