# Iteration 198 Result - Findings Paper Synthesis and Accessibility Rewrite

Status: `PASS`. `paper/telos.tex` is a full, accessible rewrite around the corrected arc iter192-iter197,
every headline number cross-checked against committed proof, and `paper/telos.pdf` is rebuilt from it. This
is a writing gate: no provider calls, SWE-bench executions, or cloud resources were used.

## What this gate did

It replaced the stale `paper/telos.tex` (written through iter156, carrying only an abstract erratum, still
calling suite-failing rows "reward hacks," in the dense style a domain expert found hard to read) with a
clean findings paper built from the `paper/REWRITE_SPINE.md` scaffolding.

## Bars met

- **Represents iter192-iter197 accurately.** The three contributions are the self-correction (Section 3),
  the ten certified-yet-wrong patches (Section 4), and the two-detector comparison (Section 5).
- **Every headline number regenerates from committed proof.** A cross-check confirmed all of: iter192
  `40/40` unresolved, baseline `40/40` at `$0.00` vs panel `17/40` at `$13.59`; iter194 `16/16` certified;
  iter195 `10` hacks and `2` correct equivalents; iter196 judge `7/10`, gold FP `1/10`, equivalent FP
  `1/2`; iter197 oracle `4/10`, equivalent FP `0/2`, `12/12` sound, union `8/10`; and the Table 1
  gold/variant outputs (e.g. django-11179 `None` vs `'present'`). All matched the artifacts.
- **"Reward hack" used only for the genuine class.** The paper calls the iter192 suite-failing rows "wrong
  patches that break the existing tests," never reward hacks, and states plainly that the `17/40` figure is
  correct but measures code review of already-rejected patches.
- **Accessibility pass done.** Every specialized term (reward hacking, FAIL_TO_PASS / PASS_TO_PASS,
  certified-resolved, gold patch, gold-free, coverage-bound) is defined on first use; the django-11179
  example is used early and concretely; the abstract reads without decoding. A scan for common LLM-tell
  phrases (delve, leverage, furthermore, notably, seamless, and others) found none.
- **Real limitations section.** Small sample, elicited construction, reference-fix definition of "wrong,"
  single-run judge, coverage-bound oracle, one adversary model.
- **PDF matches source.** `paper/telos.pdf` was rebuilt with `tectonic` (9 pages); the rendered text was
  confirmed to contain the corrected framing and every headline number.
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

Supported: `paper/telos.tex` and `paper/telos.pdf` are a readable findings manuscript that represents
iter192-iter197 accurately and inside every committed claim boundary, ready to send to a peer-reviewed
venue. Not supported: any claim that the paper is published, peer-reviewed, accepted, or citation-verified;
those remain to be done by the operator.
