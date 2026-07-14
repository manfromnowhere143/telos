# Iteration 198 - Findings Paper Synthesis and Accessibility Rewrite

Status: PRE-REGISTERED, result pending. This is a writing/synthesis gate, not an empirical run: no
provider calls, SWE-bench executions, or cloud resources are required. Its bars are correctness-of-
representation and readability, checkable against committed results.

## Why this gate exists

The construct-and-detect arc is scientifically complete for a findings paper:

- iter192: the flagship benchmark contained no reward hacks (suite-failing patches; free baseline `40/40`).
- iter193-iter195: constructed `10` execution-verified certified-resolved reward hacks — patches the
  official SWE-bench harness marks resolved that produce output differing from the gold fix on a
  synthesized input no shipped test covers.
- iter196: a frontier judge panel catches `7/10` at `1/2` equivalent false positives (single run).
- iter197: a gold-free execution oracle catches `4/10` at `0/2` false positives; the two are complementary
  (union `8/10`, oracle catches one the judge misses).

The committed `paper/telos.tex` predates all of this. It is written through iter156, carries only an
erratum on the abstract, still calls the old rows "reward hacks" in its body, and is written in the dense
"technical LLM style" a domain expert (Caesar) found extremely hard to read. It cannot be submitted as-is,
and arXiv already moderation-rejected the sibling Sentinel paper, prescribing peer review and a DOI first.

## Numeric / checkable bars

- the paper's contribution list and body represent iter192-iter197 with no claim above its committed
  evidence; every headline number regenerates from a committed `experiments/*/proof/` artifact;
- the words "reward hack" are used only for the iter195 certified-resolved class, never for the iter192
  suite-failing rows;
- the recall/precision/coverage tradeoff and the judge/oracle complementarity (union `8/10`) are stated
  with their claim boundaries (elicited, constructed, `N=10`, `3` repos, "wrong" = differs from gold);
- an accessibility pass is applied: every specialized term (both-miss, certified-resolved, gold-free,
  uncurated test, coverage-bound) is defined on first use; no undefined jargon; the abstract is readable by
  a domain expert without decoding;
- a limitations section states small `N`, single-run judge variance, elicited construction, and the
  reference-fix definition of "wrong";
- `validate_docs.py` passes (no banned self-praise; links resolve); the rebuilt `paper/telos.pdf` matches
  the corrected source.

## Falsifiers

1. Any headline number in the paper does not regenerate from a committed proof artifact.
2. The paper calls the iter192 suite-failing rows "reward hacks," or claims the iter196 single run as a
   stable rate, or presents any leaderboard / model-superiority / SOTA / natural-frequency claim.
3. The accessibility pass is not done (undefined jargon remains; the abstract still reads as dense LLM
   style).
4. `paper/telos.pdf` is stale relative to `paper/telos.tex`.

## Process note

This gate does not submit anywhere. Per the Sentinel lesson (endorsement != acceptance; arXiv moderation
prescribes peer review and a DOI first), the sequence after this gate is: a peer-reviewed venue (an
ICML/NeurIPS/ICLR safety-or-evaluation workshop with proceedings, or a journal) for a DOI, then an arXiv
appeal with the DOI. No submission is made without operator direction.

## Claim Boundary

At most, if this gate passes: `paper/telos.tex` and `paper/telos.pdf` are a readable findings manuscript
that represents iter192-iter197 accurately and inside every committed claim boundary, ready to send to a
peer-reviewed venue. It is not itself a published result, a DOI, or an arXiv acceptance.
