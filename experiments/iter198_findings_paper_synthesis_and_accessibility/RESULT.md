# Iteration 198 Result - Findings Paper Synthesis and Accessibility Rewrite

> **Standing accuracy correction (2026-07-16):** the original `PASS` and receipt are superseded. The rewrite
> inherited iter192's false novelty claim, treated iter195 as protocol-valid despite its no-gold and 20-input
> deviations, and carried an overstrong detector interpretation. The current paper is a later correction
> surface; it does not retroactively make iter198's frozen accuracy bar pass. Original artifacts remain
> preserved for provenance.

Status: `FAIL` against the writing gate's accuracy bar. The accessibility work and PDF build occurred, but
the claim that the manuscript represented iter192-iter197 accurately did not survive audit. This gate made
no provider calls, SWE-bench executions, or cloud-resource changes.

## What this gate did

It replaced the stale `paper/telos.tex` (written through iter156, carrying only an abstract erratum, still
calling suite-failing rows "reward hacks," in the dense style a domain expert found hard to read) with a
clean findings paper built from the `paper/REWRITE_SPINE.md` scaffolding.

## Original checks and their corrected disposition

- **Accuracy bar failed.** Iter192's factual construct correction remains, its overbroad conceptual novelty
  interpretation is conservatively adjudicated `FAIL`, and its literal v1-specific trigger is indeterminate;
  iter195's ten divergences are exploratory gold-assisted reference differentials from a failed protocol;
  iter196 is partial/protocol-blocked; and iter197 is a protocol failure with retained diagnostics.
- **Telos empirical quantities trace to committed proof, but traceability is not protocol validity.** The
  original cross-check confirmed all of: iter192
  `40/40` unresolved, baseline `40/40` at `$0.00` vs panel `17/40` with a `$13.128090` conservative
  score-producing spend guard; the rounded `$13.59` through-repair total includes excluded diagnostics.
  Iter194 retained `16/16` certified;
  iter195 `10` hacks and `2` correct equivalents; iter196 judge `7/10`, gold FP `1/10`, equivalent FP
  `1/2`; iter197 oracle `4/10`, equivalent FP `0/2`, `12/12` sound, union `8/10`; and the Table 1
  gold/variant outputs (e.g. django-11179 `None` vs `'present'`). Those values matched the artifacts, but the
  original prose assigned several of them unsupported protocol interpretations. External literature facts
  are source-attributed rather than locally regenerated.
- **"Reward hack" used only for the genuine class.** The paper calls the iter192 suite-failing rows "wrong
  patches that break the existing tests," never reward hacks, and states plainly that the `17/40` figure is
  correct but measures code review of already-rejected patches.
- **Accessibility pass done.** Every specialized term (reward hacking, FAIL_TO_PASS / PASS_TO_PASS,
  certified-resolved, gold patch, gold-free, coverage-bound) is defined on first use; the django-11179
  example is used early and concretely; the abstract reads without decoding. A scan for common LLM-tell
  phrases (delve, leverage, furthermore, notably, seamless, and others) found none.
- **Limitations section was incomplete.** It covered small samples, elicited construction, the
  reference-differential label, a single-run judge, and one adversary model, but omitted the decisive
  iter192 novelty-scope correction and iter195 protocol failure now recorded above.
- **PDF matches source.** `paper/telos.pdf` was rebuilt with `tectonic` (9 pages); the rendered text was
  confirmed to match the then-current source. That visual/source match does not validate the superseded
  scientific interpretations.
- **Guards pass.** `validate_docs.py` is clean (no banned self-praise; links resolve).

## Honesty notes

- The judge figure is a single stochastic run, stated as such in the abstract, Section 5, and Limitations.
- Three citations (Control Tax, DeepMind FSF v3.0, METR MALT) are marked "to be verified by hand" in the
  bibliography; the author must confirm author/year/venue before any submission.
- Self-criticism is kept in the paper, not smoothed away: Section 4 reports that the authors hand-judged
  django-11119 a correct equivalent and execution proved it a hack.

## What this gate does NOT do

It does not submit anywhere and it is not a published result, a DOI, or an arXiv acceptance. Per the
Sentinel lesson (an endorsement is not an acceptance; arXiv moderation prescribes peer review and a DOI
first), the next step is a peer-reviewed venue for a DOI, then an arXiv appeal with the DOI, and only under
operator direction.

## Evidence

- `paper/telos.tex` - the rewritten manuscript
- `paper/telos.pdf` - rebuilt from source with tectonic
- `paper/REWRITE_SPINE.md` - the scaffolding and numbers ledger
- `paper/README.md` - status and submission sequence
- `proof/valid/receipt_findings_paper_synthesis.json`

## Claim Boundary

Supported: iter198 produced an accessible manuscript rewrite and a rendered PDF from committed source.
Not supported: that iter198 passed its strict accuracy bar; that its original manuscript represented
iter192-iter197 inside every corrected claim boundary; that traceable numbers imply valid protocols; or that
the paper is published, peer-reviewed, accepted, submission-ready, or citation-verified.
