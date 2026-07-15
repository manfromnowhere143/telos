# Iteration 201 - Detectors on the Full 22-Hack Benchmark

Historical status text: “PRE-REGISTERED, result pending; no provider calls or executions run.” That status
is not independently established for the judge phase. The first Git commit containing this file,
`7b87f22f5071d98f9dbd0d99c6259333b779dc1e` at `2026-07-15T12:05:46+03:00`, also contains the judge
runner and all retained judge outputs.

> **Post-result methodology correction (2026-07-15):** the original Detector B description below is not
> the protocol the code executed. `scripts/run_iter201_oracle_properties.py` extracted a source-file and
> function/class locator from each candidate variant diff and inserted those locator fields into the
> property prompt. Candidate code lines and gold content were withheld, but generation was locator-assisted,
> not diff-independent. Offline soundness used the gold patch as the original design explicitly specified,
> so that use is not a second protocol deviation; it does make the pipeline gold-validated and means its
> zero gold failures are not an independent false-positive estimate. Separately, `8/88` judge responses
> were unparseable; the post-result control sensitivity is `3/22` observed flags, `6/22` worst-case missing,
> and `3/19` complete-case. These corrections reinterpret retained outputs; they do not alter this
> historical protocol text or claim a prospective repair. The property runner was Git-frozen in
> `7b87f22f5071d98f9dbd0d99c6259333b779dc1e` before the property outputs first appeared in
> `5efe1e3b049db152f4c0b68032241ef23152b6bf`, but that runner already contained the locator deviation, so
> its code did not match the registered diff-independent description. The judge phase has no separate
> pre-output Git freeze. Its artifact retains `88/88` parsed labels but no raw response text, preventing
> re-audit of exact response substance and parser fidelity.

## Why this gate exists

The detector comparison in iter196 and iter197 was measured on the first `10` certified-resolved reward
hacks (Django, astropy, matplotlib). iter199 grew the benchmark to `22` hacks across `8` repositories,
adding requests, xarray, pylint, pytest, and sympy. This gate extends the detector comparison to the full
`22`, so the paper's most quantitative result rests on a larger, more repository-diverse set, and so we can
say whether detection generalizes to the five new repositories rather than only the original three.

## What this gate measures

Two detectors, at decision time, with the gold fix withheld from both, on all `22` benchmark hacks and
paired gold controls:

1. **Judge panel** (iter196 method): the frontier judges reachable in this environment (`gpt-5.6-terra`,
   `claude-opus-4-8`; `gemini-2.5-flash` remains blocked on ADC) read the candidate diff, the public task,
   and the visible test, and rule reward-hack or legitimate. Report per-model and any-catch recall on the
   `22` hacks and false positives on the `22` gold controls.
2. **Gold-free execution oracle** (iter197 method): a model proposes an executable correctness property
   from the public task and visible test only (no gold, no diff); the property is validated by passing on
   the gold control and executed against the candidate in its pinned container; a sound property that fails
   on the hack catches it. Report recall on the `22` hacks and false positives on the controls.

Despite the historical reuse sentence in the first version of this file, the committed judge runner has no
iter196-result input or copy path: it calls both providers for every one of the `22` hack rows and all `22`
paired gold-control rows. The retained iter201 artifact therefore records a fresh parsed label pair for all
`44` rows (`88` calls), not reused iter196 labels. It remains one stochastic sample, and the raw response
text was not retained.

The shared judge prompt capped task/test/diff inputs at `1500`/`2500`/`4000` characters. Across `44`
prompts, task text was truncated in `14/44` (`7/22` unique instances), visible tests in `6/44` (`3/22`),
and candidate diffs in `0/44`. The property execution shell used mutable `:latest` container tags and
retained no resolved image digest. Finally, the `22` paired gold executions were used in the registered
property-soundness role, not as independently generated property-detector decisions. This satisfies the
registered gold-validation step but cannot supply an independent specificity estimate.

## Numeric Bars

- provider calls do not exceed `220` and estimated spend does not exceed `$30.00`,
- no undeleted cloud resources,
- both detectors are evaluated on all `22` hacks and their `22` gold controls at decision time,
- no detector prompt contains the gold patch, a label, hidden test names, official reports, or a
  construction witness (leakage scanned: gold-distinctive lines, not shared diff headers),
- per-detector recall on the `22` hacks and false-positive rate on the `22` controls are reported with raw
  per-row verdicts retained,
- the judge single-run caveat and the gemini-unavailable caveat are stated,
- committed secret/private identifier hits are exactly `0`,
- forbidden positive claim hits are exactly `0`.

## Falsifiers

1. Any detector prompt contains gold content, a label, a hidden test name, an official report, or a
   construction witness.
2. A reported recall or false-positive number does not regenerate from retained per-row verdicts.
3. Controls are not evaluated (recall without specificity is not a result).
4. The gold-free oracle counts a property that is not sound (fails on the gold control) as a catch.
5. Provider calls exceed `220`, spend exceeds `$30.00`, or a cloud resource is left undeleted.
6. The result presents a leaderboard, model-superiority, state-of-the-art, natural-frequency, or production
   claim, or presents a single judge run as a stable rate.

## Claim Boundary

At most, if this gate passes: on `22` execution-verified certified-resolved reward hacks across `8`
repositories and `22` paired gold controls, at decision time with gold withheld, Telos reports the recall
and false-positive rate of a frontier judge panel and of a gold-free execution oracle, extending the
`10`-hack comparison to the full benchmark. This is a bounded pilot comparison, a single judge run, not a
leaderboard, model-superiority, or state-of-the-art claim.
