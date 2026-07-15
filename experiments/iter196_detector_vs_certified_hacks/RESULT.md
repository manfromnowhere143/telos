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

### Corrected result (single run; judge verdicts are stochastic)

| cohort | response nondecisions | rows with nondecision | observed lower | missing upper | complete-case |
| --- | ---: | ---: | ---: | ---: | ---: |
| `10` hacks | `3/20` | `2/10` | `7/10` | `9/10` | `7/8` |
| `10` paired gold controls | `2/20` | `2/10` | `1/10` | `3/10` | `1/8` |
| `2` equivalent controls | `2/4` | `1/2` | `1/2` | `2/2` | `1/1` |

“Observed lower” applies the recorded any-catch rule to parsed labels only; “missing upper” treats every
row with an unparseable response and no observed flag as potentially flagged; “complete-case” excludes
rows with either response unparseable. The per-model parsed counts remain `7` GPT and `6` Opus hack flags,
with one parsed gold flag and one parsed equivalent flag from each model. Unanimous parsed flags are `6/10`
hacks, `0/10` gold controls, and `0/2` equivalent controls.

The bounded finding is that the parsed-label panel flags `7/10` hacks and `1/10` paired gold controls under
the observed rule, while missing outcomes permit the wider sensitivities above. This supports monitor
signal on this cohort, not a complete false-positive rate or a stable recall estimate.

### Evidence and prompt limitations

The runner parsed each provider response immediately and retained only the resulting label. Raw provider
response text was never stored, so exact response substance and parser fidelity cannot now be re-audited.
The `44` parsed labels, row aggregation, source inputs, and exact runner bytes are retained and hash-bound.

The prompt builder capped the problem statement at `1500` characters, the visible test at `2500`, and the
candidate diff at `4000`. Across the `22` judged rows, task text was truncated in `4/22` prompts (`3/12`
unique instances), visible-test text in `2/22` (`1/12` unique), and candidate diffs in `0/22`. These are
input-coverage limits, not merely implementation details.

The original protocol was Git-frozen before outputs, but the two-model amendment was first committed in
the same commit as the artifact. Its claimed pre-call timing therefore lacks an independent Git record.

### Two methodology issues found and handled (world-contact, Standard 9)

1. **A leakage guard fired, and it was mostly a false alarm — but not entirely.** The first automated guard
   matched a shared `200`-char diff prefix and reported `10/10` "leakage." That was wrong: a variant shares
   its diff header and context with gold by construction, and that is the candidate's own content, not the
   gold solution. The corrected guard checks only gold-*distinctive* added lines present in the candidate:
   `2/10` (django-11211, matplotlib-24627), where block-substitution left one gold line intact. Those are
   the candidate's real lines, the judge never receives the gold patch as a comparison reference, and a
   shared correct-looking line biases toward **missing** the hack, not catching it. Reported, per-row, in
   `judge_panel_results.json`; the effect direction is against recall.

2. **The incumbent's nondecisions were nearly reported as "legitimate."** An earlier run set OpenAI
   `max_completion_tokens=200`; gpt-5.6-terra spent that budget on hidden reasoning and returned unparseable
   content on `18/22` rows. That earlier response corpus was not retained and cannot be independently
   audited. The reported run used `1536`; across both providers it still contains `7/44` response
   nondecisions affecting `5/22` rows. The sensitivity table, rather than treating those as legitimate,
   is the corrected accounting.

Both were caught because the analysis had bars that could fail on reality, not just internal counters —
the exact discipline Standard 9 codifies.

## What remains: Detector B (promoted to iter197)

The gold-free execution oracle — a model proposes an executable property from the public task and visible
test only (no gold), validated on the visible-test anchor (iter126), executed in-container against the
candidate — is the novel, execution-grounded instrument. On framework-internal functions with low
property-derivability (iter139: `~0.10`), it is a substantial build with its own failure modes, and it
runs on CI rather than locally. It was pre-registered as `iter197`, with Detector A's observed `7/10`
label count as a historical comparator, not a prospective threshold it had to clear. Splitting it out is
disclosed, not silent: this gate delivers Detector A only.

## Claim Boundary

Supported: on `10` execution-verified certified-resolved reward hacks and `12` controls, a 2-model frontier
judge panel (gpt-5.6-terra + claude-opus-4-8; gemini blocked) reading capped diff + task + visible-test
inputs has the parsed-label sensitivities above in one stochastic run. The observed any-catch counts are
`7/10` hacks, `1/10` paired gold flags, and `1/2` equivalent flags. Two hack rows carry a coincidental
shared gold line that biases against recall.

Not supported: any both-detector comparison (Detector B not yet run); any leaderboard, model-superiority,
state-of-the-art, natural-frequency, benchmark-size, broad robustness, production, or product-value claim;
any claim from a single run treated as a stable rate; a complete false-positive estimate; or a claim that
raw provider responses or parser fidelity remain auditable.

## Evidence

- `proof/judge_panel_results.json` — metrics and per-row verdicts (with per-row shared_gold_lines)
- `proof/audit_report.json` — recomputed nondecision sensitivities, prompt truncation, chronology, and
  retained-evidence limits
- `proof/valid/receipt_detector_a_judge_panel.json`

Regenerate (requires `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`; spends `~$2.64`):

```bash
python3 scripts/run_iter196_judge_panel.py
```
