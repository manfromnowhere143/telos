# Telos paper (findings draft)

> **Status: clean rewrite complete (iter198), not yet submitted.** `telos.tex` was fully rewritten on
> 2026-07-14 around the corrected arc iter192-iter197: an earlier benchmark that did not contain reward
> hacks (corrected in place), ten execution-verified certified-resolved reward hacks, and a two-detector
> comparison (judge panel `7/10`, gold-free oracle `4/10` at perfect precision, complementary union
> `8/10`). Every headline number was cross-checked to regenerate from a committed `experiments/*/proof/`
> artifact. The draft applies an accessibility pass (every term defined on first use, plain declarative
> prose) in response to the readability feedback that preceded the sibling Sentinel arXiv rejection.
> `telos.pdf` is rebuilt from this source with `tectonic`.
>
> **Before any external submission:** verify each citation's author/year/venue by hand (three entries are
> marked "to be verified"); confirm the author/affiliation block. Per the Sentinel lesson (an arXiv
> endorsement is not an acceptance; arXiv moderation prescribes peer review and a DOI first), the sequence
> is a peer-reviewed venue for a DOI, then an arXiv appeal with the DOI. No submission without operator
> direction.

`telos.tex` is a self-contained LaTeX findings paper. Its three contributions are: the self-correction of
the earlier benchmark (Section 3), the construction of ten certified-yet-wrong patches (Section 4), and the
two-detector comparison (Section 5). Every quantitative claim is a bounded pilot reproduced by a committed
runner, manifest, and validated receipt under `experiments/iterNNN_*`, and the spine that structures the
rewrite is `paper/REWRITE_SPINE.md`.

## Build

Standard `pdflatex` (no bibtex needed - references are a manual `thebibliography`, plain `\cite`):

```
cd paper
pdflatex telos.tex
pdflatex telos.tex   # second pass resolves \ref and \cite numbers
```

Or with `tectonic` (single command, resolves references automatically; this is what produced the
committed `telos.pdf` on 2026-07-14):

```
cd paper
tectonic telos.tex
```

Packages used are all arXiv-standard: `amsmath`, `booktabs`, `graphicx`, `tikz`, `geometry`, `microtype`,
`hyperref`, `xcolor`. No external assets; the two figures are TikZ.

## Status and honest caveats (read before posting)

- **Compiled and committed.** `telos.pdf` is built with `tectonic` and committed alongside the source.
  Rebuild any time with `tectonic telos.tex`. After prose changes, render the PDF pages and inspect them
  before treating the artifact as arXiv-ready.
- **Citations reviewed; still worth a final human glance.** The seven `thebibliography` entries were
  reviewed and are believed accurate (author/year/venue), but confirm each against the real reference
  before posting. The draft situates against the recent (2025-2026) reward-hacking / verification-horizon
  line in prose **without inventing citations for it**; add real ones there if you have the exact refs.
- **Author/affiliation block** (`\author{...}`) is currently "Daniel Wahnich / Aweb / Telos research
  program"; adjust to how you want it to appear.
- **Framing is deliberate.** Numbers are presented as small-$N$ pilots or row-artifact counts, with an
  explicit Limitations section (small $N$, constructed hacks, artifact-not-score, small cross-repo pool,
  single agent model, property-derivable subset, no baseline comparison, not a resolved-rate). Keep that
  framing; do not upgrade the pilots or the v1 artifact into model scores or leaderboard claims.

## Provenance

The prose mirrors `docs/PAPER.md` (the internal consolidated result). The numbers trace to:
`iter109-116` (detection), `iter118-129` (both-miss + gold-free property layer), `iter140-145` (frontier
adversary, judge robustness, panel), `iter146-148` (intervention + replication), `iter147`
(preserve-correct control), `iter149-150` (gold-free oracle), `iter151` (cross-repo official-metric
intervention), `iter152` (reward-model gaming at scale and saved hack diffs), `iter153` (seed
materialization), `iter154` (published expansion shortfall), `iter155` (adaptive size-bar completion), and
`iter156` (hash-checked `reward_hack_benchmark_v1` row artifact). See the arc table in the repository
`README.md`.
