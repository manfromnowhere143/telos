# Telos paper (findings draft)

> **Status: current through the iter205 pre-dispatch admission-history null; iter206 remains pre-result; not yet
> submitted.** `telos.tex` reports the iter192
> foundation correction and `22` execution-verified certified-resolved reward hacks across `8`
> repositories. Iter197 and iter201 are protocol `FAIL`; their retained property counts are exploratory.
> The accurate label is **locator-assisted, gold-validated property pipeline**, not an independently
> gold-free detector. Iter197 violated locator, visible-anchor, and independent-control requirements; its
> apparent property-only row was judge-unadjudicated, so no complementarity is confirmed. Iter201 failed
> the locator bar only; its registered gold validation still prevents an independent property-FP estimate.
> Iter201 retains judge catches `20/22` with `8/88` unparseable responses and mandatory
> gold-control sensitivities (`3/22` observed lower, `6/22` worst-case missing upper, `3/19` complete-case).
> The property pipeline generated checks for `21/22`, retained `20/21` after gold inclusion, and caught
> `6/22`, all within the judge catch set; it supplies no independent false-positive estimate or ensemble
> gain. All `44` judge rows were fresh, but the judge phase lacks an independent pre-output Git freeze. The
> artifact retains parsed labels and nondecision markers, not raw response text; prompt truncation and
> digest-unpinned historical construction, witness, and property containers are disclosed. Iter200
> is an exploratory, nonrandom, gold-localized convenience sample with a post-inspection
> strict rule and no independently timestamped pre-output Git freeze. Its corrected denominator is `N=24`,
> `k=1`, `u=6`; report `1/24` confirmed lower, `7/24` as the worst case over those six declared missing
> outcomes, and `1/18` complete-case sensitivity together. The `54` legacy execution logs lack explicit
> image/exit provenance and are accepted through a frozen exact-byte corpus; the `20` backfill logs retain
> stronger provenance markers. Iter200 retained parsed blind-judge labels and derived booleans, not raw
> responses, so exact response substance and parser fidelity cannot be re-audited.
> Iter202 had a post-contact, pre-retained-output protocol freeze and was not conventionally preregistered.
> Its retained provider stages completed `53` solver and `39` scenario calls, producing `50` valid patches,
> `38` scenario programs, and one original missing scenario. Before any scenario or certification execution,
> the unchanged frozen safety guard rejected `9` programs with `21` findings and admitted `29`; the batch
> stopped. Iter202 is therefore a scenario-safety protocol/execution null and contributes no rate. The null
> disposition is recorded in `experiments/iter202_natural_rate_scaled/RESULT.md`. Its paid
> path was bound to an exact-byte runtime manifest, exact eight-shard certification, atomic attempt
> checkpoints, and one aggregate receipt from a single repository/workflow/run/attempt/commit. Hardened evidence PR `#3` merged as
> `3a3368635e397d540cf98fc0f19d443661cc0fef`, primary-branch CI run `29451691560` passed, and provider-free
> Node 24 backfill run `29452243832` reproduced the exact specs and validated the complete committed
> `74`-log corpus without re-executing containers or calling model providers. Iter203 sealed and
> replay-validated the fixed iter202 bytes, then made one canonical execution attempt in workflow run
> `29460393525`, attempt `1`, after PR `#5` merged as
> `5c409f79c9333206cff9ed80d59c08aa347110f6` and primary-branch CI run `29460293066` passed. All `50/50`
> first Docker `run` invocations returned exit `125` across eight runners before any in-container command;
> collection was skipped, zero workflow artifacts were uploaded, and no patch, official certification, or
> scenario program executed. The exact daemon
> stderr was not retained. The container-creation cause is reconstructed from the frozen logging options
> and version-matched Docker `28.0.4` source, so iter203 is an execution-infrastructure null rather than a
> scientific result. Iter204 source then merged as
> `c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446`, with primary CI run `29465925393` green, but its workflow
> could not be parsed. Its frozen closure snapshot contains public `push` records `29465584664` and
> `29465924803`, both with zero jobs and artifacts;
> at least one locally observed dispatch API request returned HTTP `422` for `runner.temp` in job-level
> `env`, and the public `workflow_dispatch` run count is exactly zero. No provider or scientific process
> started. Iter204 is therefore a pre-dispatch infrastructure null with no `N`, `k`, or `u`; the exact
> rejected-request count is not publicly auditable. Iter205 feature head
> `a336b4909329d392f6db5f6098792e07a17f28cb` merged as
> `4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f` and passed primary CI run `29468769187`. Workflow `314141096` is
> active and both complete histories are empty, but its read-only gate observed four iter204 parser rows
> rather than the two-row closure snapshot and stopped before the dispatch request command.
> No iter205 dispatch request was issued, and no dispatch API response or rejection exists. No iter205 workflow run,
> provider process, or scientific process occurred. Iter205 is therefore a pre-dispatch
> admission-history null with no `N`, `k`, or `u`. Iter206 is the separately versioned pending exact-six
> admission recovery. It permits one final branch push, requires an exact successful attempt-`1` branch-push
> and pull-request CI pair, one exact two-parent merge, and green primary CI before the exact-six gate. A
> missing, seventh, or malformed row closes the gate without dispatch; after every gate passes, at most one
> dispatch request is permitted. Iter206 contributes no result to the paper.
> `telos.pdf` is rebuilt from this source.
>
> **Before any external submission:** the three previously-flagged citations (Control Tax
> arXiv:2506.05296; DeepMind Frontier Safety Framework v3.0, 22 Sep 2025; METR MALT, 14 Oct 2025) were
> verified against primary sources on 2026-07-14 (the MALT expansion was corrected from a wrong draft
> value to "Manually-reviewed Agentic Labeled Transcripts"). Still confirm the author/affiliation block.
> Submission venue and sequence remain operator decisions. No submission without operator direction.

`telos.tex` is a self-contained LaTeX findings paper. Its contributions are the self-correction of the
earlier benchmark, the construction and cross-repository expansion of certified-yet-wrong patches, a
corrected exploratory instrument comparison that publishes two protocol failures, and a bounded
gold-localized neutral-solve existence case. Every quantitative claim must reproduce from committed proof
under `experiments/iterNNN_*`.

## Build

Standard `pdflatex` (no bibtex needed - references are a manual `thebibliography`, plain `\cite`):

```
cd paper
SOURCE_DATE_EPOCH=1784160000 pdflatex telos.tex
SOURCE_DATE_EPOCH=1784160000 pdflatex telos.tex   # second pass resolves \ref and \cite numbers
```

Or with `tectonic` (single command, resolves references automatically; this is what produces the
committed `telos.pdf`):

```
cd paper
SOURCE_DATE_EPOCH=1784160000 tectonic telos.tex
```

The fixed epoch is 2026-07-16 00:00:00 UTC, matching the explicit manuscript revision date and making PDF
metadata reproducible. Two consecutive Tectonic builds must have identical SHA-256 digests.

Packages used are all arXiv-standard: `inputenc`, `fontenc`, `amsmath`, `amssymb`, `booktabs`, `array`,
`float`, `graphicx`, `geometry`, `microtype`, `placeins`, `hyperref`, and `xcolor`. There are no external
assets or figures.

## Status and honest caveats (read before posting)

- **Source and build artifact move together.** Build `telos.pdf` with `tectonic` alongside the source.
  After every prose change, render every PDF page and inspect it before treating the artifact as
  submission-ready.
- **Citations need a final human pass.** The bibliography contains eleven entries. Three recent sources
  (Control Tax, Frontier Safety Framework v3.0, and MALT) were checked against primary sources on
  2026-07-14; verify every entry again before submission.
- **Author/affiliation block** (`\author{...}`) is currently "Daniel Wahnich / Telos research program";
  confirm it before submission.
- **Detector framing is corrected.** Iter197/iter201 are protocol `FAIL`, not validated detector passes.
  Keep their distinct failure causes, the corrected iter196 missingness/no-complementarity result, the
  locator-assisted, gold-validated access pattern, `8/88` judge nondecisions, and `3/22` lower,
  `6/22` missing upper, `3/19` complete-case gold-control sensitivities visible. Do not report an independent
  property-pipeline false-positive rate. Preserve the judge-freeze, raw-response, prompt-truncation, and
  historical container-provenance limitations.
- **Neutral-solve framing is exploratory.** The sample is nonrandom and gold-localized; the strict blind
  rule was adopted after outcome inspection, while the missingness summaries were added after the original
  result but before the backfill. Its builder excludes every iter193 Phase-A and iter199 target before
  deriving the `200`-row compatible pool and frozen `39`-target cohort. Keep `1/24`, `7/24`, and `1/18` together,
  and do not upgrade them into a population frequency, model score, leaderboard, broad robustness, or
  deployment claim.
- **Historical image provenance is bounded.** Iter193--iter199 construction/witness runs and iter197/iter201
  property runs selected instance-specific mutable `:latest` tags and retained no resolved image digests.
  The execution logs remain evidence of those runs, but their exact historical container bytes cannot be
  reconstructed.

## Provenance

The standing paper evidence traces to `iter192` (foundation correction), `iter193`--`iter195`
(official-harness construction and execution witnesses), `iter199` (cross-repository expansion), `iter196`
(judge pilot), `iter197` and `iter201` (protocol-failed property runs with retained exploratory diagnostics),
and `iter200` (exploratory gold-localized solve, post-inspection blind rule, and corrected denominator).
Iter202 has no measured rate in the paper. Its provider stages completed after a post-contact,
pre-retained-output freeze, but its unchanged safety guard stopped the batch before execution; that
protocol/execution null is preserved. Iter203 is a separately disclosed execution-infrastructure null:
its sole canonical run failed at Docker container creation before applying a patch or executing a
certification or scenario. Iter204 is a separately disclosed pre-dispatch workflow-parse infrastructure
null: its two-row closure snapshot retained public `push` records with zero jobs and artifacts, the public `workflow_dispatch` count is
zero at closure, and no scientific process ran. Iter205 is a separately disclosed pre-dispatch
admission-history null: its own workflow histories are empty, its dispatch request command was never reached, and
the upstream iter204 history had grown from two to four publication rows. Iter206 is a separately
versioned pending exact-six admission recovery and has no result in the paper.
