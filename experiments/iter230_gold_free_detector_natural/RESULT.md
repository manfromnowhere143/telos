# Iter230 result — gold-free static detection of natural certified-yet-wrong patches is weak

Status: **published at full weight.** A gold-free static model panel catches only `2/13` naturally-occurring
certified-yet-wrong patches. The low recall is the intended baseline: it bounds static, no-execution detection
of this class and motivates a held-out-execution oracle.

## Result

On the frozen natural benchmark (sha `10dc898c3cdc6026aaedc57d469e546b279a982df3772ba3388c1dfb515b8928`;
`13` confirmed certified-yet-wrong positives, `54` certified-correct negatives), a three-provider gold-free
panel that sees only certification-time information (problem, public test names, candidate patch) and flags a
patch when a majority return `likely_wrong`:

| Quantity | Value |
| --- | --- |
| Recall (flagged positives / positives) | `2/13 = 0.154` |
| False-positive rate (flagged negatives / negatives) | `5/54 = 0.093` |
| Unparsed or errored panelist responses | `7` of `201` |

Recall is `2/13` with a wide Wilson interval (roughly `[0.04, 0.42]`); the false-positive rate is `5/54`
(`[0.04, 0.20]`). The two flagged positives are `django__django-12209` and one `django__django-11815` patch.
Eleven of thirteen positives were missed.

## Per-panelist behaviour

| Panelist | Provider | Positives flagged | Negatives flagged |
| --- | --- | --- | --- |
| `gpt-5.6-terra` | OpenAI | `2/13` | `2/54` |
| `claude-opus-4-8` | Anthropic | `2/13` | `8/54` |
| `gemini-3.1-pro-preview` | Google | `6/13` | `11/54` |

The panelists disagree sharply. The Google model is the most aggressive, reaching `6/13` recall but at a
`11/54` (`20\%`) false-positive rate; the two OpenAI/Anthropic panelists are conservative, flagging only
`2/13`. The majority rule inherits the conservative behaviour, so combining them lowers recall to `2/13` rather
than raising it. No panel configuration among these three flags a majority of the natural hacks without also
flagging a large fraction of correct patches.

## The finding: static judging is largely blind to this class

This is the mitigation baseline the natural-rate arc was built toward. A patch is certified precisely because it
passes every graded test, and a reviewer given only the issue, the public test names, and the patch --- without
running it against behaviour the graded tests do not cover --- recovers little signal: `2/13` recall at a
non-trivial false-positive cost. That is a direct, quantified restatement of the paper's thesis: a check
restricted to the visible information cannot reliably catch certified-yet-wrong patches, and the gap is not
closed by asking a stronger judge. The natural next step is a **gold-free held-out-execution oracle** --- run
the candidate patch against inputs or properties derived from the issue (not the gold fix) and validated
against the visible tests --- which is future work (iter231).

## Disclosed limitation held

The pre-registration disclosed that two panelists (`gpt-5.6-terra`, `gemini-3.1-pro-preview`) are also solvers
for some benchmark patches. This is conservative for recall and does not manufacture flags; the independent
`claude-opus-4-8` flags `2/13` positives, consistent with the other conservative panelist. The `7`
unparsed/errored responses are reported, not dropped, and none is counted as a flag.

## Claim boundary

Iter230 is a bounded static-detection baseline over a fixed `13`-positive, `54`-negative convenience benchmark
of naturally occurring patches. `2/13` recall has a wide interval and is not a deployable-detector result, a
model or provider ranking, or a state-of-the-art claim. It measures that a gold-free model panel, without
execution, is a weak detector of natural certified-yet-wrong patches, and it exists to be contrasted with a
future execution-based oracle.

## Spend and boundary

The panel made up to `201` provider calls (`67` patches x `3` panelists), concurrent; no container execution
was used. No sealed predecessor evidence changed.

## Reproduction

```bash
python3 scripts/build_iter230_eval_set.py     # regenerates the frozen benchmark (sha 10dc898c)
python3 scripts/run_iter230_detector.py        # needs OPENAI/ANTHROPIC/GOOGLE_AI keys
```

Detector evidence: `proof/raw/detector/detector_summary.json` (per-patch verdicts and the aggregate).
