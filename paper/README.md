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

- **Compiled and committed.** `telos.pdf` (7 pages) is built with `tectonic` and committed alongside the
  source. It renders cleanly: title, abstract, the TikZ cascade figure, the three-layer table, all ten
  sections, and the references. Rebuild any time with `tectonic telos.tex`.
- **Citations reviewed; still worth a final human glance.** The seven `thebibliography` entries were
  reviewed and are believed accurate (author/year/venue), but confirm each against the real reference
  before posting. The draft situates against the recent (2025-2026) reward-hacking / verification-horizon
  line in prose **without inventing citations for it**; add real ones there if you have the exact refs.
- **Author/affiliation block** (`\author{...}`) is currently "Daniel Wahnich / Aweb / Telos research
  program"; adjust to how you want it to appear.
- **Framing is deliberate.** Numbers are presented as small-$N$ pilots, with an explicit Limitations
  section (small $N$, django-dominant, single agent model, property-derivable subset, no baseline
  comparison, not a resolved-rate). Keep that framing; do not upgrade the pilots into benchmark claims.

## Provenance

The prose mirrors `docs/PAPER.md` (the internal consolidated result). The numbers trace to:
`iter109-116` (detection), `iter118-129` (both-miss + gold-free property layer), `iter140-145` (frontier
adversary, judge robustness, panel), `iter146-148` (intervention + replication), `iter147`
(preserve-correct control), `iter149-150` (gold-free oracle). See the arc table in the repository
`README.md`.
