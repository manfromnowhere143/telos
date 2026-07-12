# Telos paper (findings draft)

`telos.tex` is a self-contained LaTeX draft of the Telos findings paper, consolidating the
detection+intervention arc (experiments iter109-iter150). It is framed as a findings paper: the
contribution is the both-miss discovery, the three-layer decomposition, the gate-and-repair intervention,
and the verdict-giver-vs-property-generator insight. Every quantitative claim is a bounded pilot reproduced
by a committed runner and a validated receipt under `experiments/iterNNN_*`.

## Build

Standard `pdflatex` (no bibtex needed - references are a manual `thebibliography`, plain `\cite`):

```
cd paper
pdflatex telos.tex
pdflatex telos.tex   # second pass resolves \ref and \cite numbers
```

Packages used are all arXiv-standard: `amsmath`, `booktabs`, `graphicx`, `tikz`, `geometry`, `microtype`,
`hyperref`, `xcolor`. No external assets; the two figures are TikZ.

## Status and honest caveats (read before posting)

- **Not compiled in this environment.** `pdflatex` was not installed on the machine that wrote this draft.
  The source was checked structurally (balanced environments and braces, every `\cite` has a matching
  `\bibitem`, `\citep` removed since natbib is not loaded), but it has **not** been rendered to PDF here.
  Compile it once locally and read the PDF before submitting.
- **Citations must be human-verified.** The `thebibliography` entries are best-effort from memory
  (author/year/venue). Confirm each one against the real reference before posting; do not rely on them as
  written. Add any recent (2025-2026) reward-hacking / verification-horizon references you want to situate
  against - the draft describes that line in prose without inventing citations for it.
- **Author/affiliation block** (`\author{...}`) is a placeholder; set it as you want it to appear.
- **Framing is deliberate.** Numbers are presented as small-$N$ pilots, with an explicit Limitations
  section (small $N$, django-dominant, single agent model, property-derivable subset, no baseline
  comparison, not a resolved-rate). Keep that framing; do not upgrade the pilots into benchmark claims.

## Provenance

The prose mirrors `docs/PAPER.md` (the internal consolidated result). The numbers trace to:
`iter109-116` (detection), `iter118-129` (both-miss + gold-free property layer), `iter140-145` (frontier
adversary, judge robustness, panel), `iter146-148` (intervention + replication), `iter147`
(preserve-correct control), `iter149-150` (gold-free oracle). See the arc table in the repository
`README.md`.
