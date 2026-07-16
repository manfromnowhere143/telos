# Telos paper (findings draft)

> **Status: current through corrected iter200; iter202 is a safety null and iter203 remains pre-result; not yet submitted.** `telos.tex` reports the iter192
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
> `74`-log corpus without re-executing containers or calling model providers. Iter203 now seals the fixed
> iter202 bytes, certifies all `50` patches, and exposes only safety-admitted copies to execution; rejected or
> missing witnesses remain unresolved. No iter203 result is in the paper. Recovery execution requires a
> clean green primary branch and the separately bound iter203 preflight; generated `HANDOFF.md` owns the
> current branch and readiness snapshot.
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
protocol/execution null is preserved. Iter203 is a separately disclosed post-provider recovery and has no
result in the paper.
