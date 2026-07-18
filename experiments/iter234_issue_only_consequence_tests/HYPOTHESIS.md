# Iter234 — issue-only consequence tests: manufacturing a reference without gold

Status: prospective, pre-registered before any iter234 test, execution, or result exists. It reuses the frozen
iter230 benchmark unchanged.

Predecessor merged master: `ffbb044`.

## Why iter234 exists, and what it is not

Iter231 and iter232 measured two gold-free detectors on this benchmark. Both reach `0/10` on the
plausible-but-wrong-value class. The stated reason: *"a solver able to predict the correct value would not
have produced the wrong patch."*

That reason is about a specific question. Both detectors were asked **"is this patch wrong?"**, which requires
predicting the correct value from the patch. A test author asked **"what should this code do?"**, reading only
the issue and never the patch, is a different information channel. And the channel is not empty: `10` of the
`13` positives have an issue that states expected behavior explicitly.

An issue is certification-time information. Deriving assertions from it manufactures a reference **without
gold** — precisely the thing the ceiling argument says is required.

**This is not TCP-1.** `experiments/iter212_.../HYPOTHESIS.md` specifies human-authored hidden tests with five
conflict-screened reviewers and carries an explicit stop rule: *do not replace external humans with LLM
judges.* That gate remains blocked and untouched. Iter234 tests the **mechanism** TCP-1 rests on — that a
patch-blind author can produce a usable reference — using a model author. A positive result here would
motivate TCP-1, not substitute for it.

## The instrument

For each row, an author model (`gpt-5.6-terra`) sees **only**: the issue text, the repository and base commit,
and the public `FAIL_TO_PASS` test names (so it can aim past what the graded suite already covers). It is
**never** shown the candidate patch, the gold patch, any hidden test, or any witness.

It writes a short consequence test that asserts what the changed behavior *should* be, prints
`RESULT=('PASS',)` if every assertion holds and `RESULT=('FAIL', <detail>)` otherwise, and reports an
exception as `RESULT=('ERROR', <type>)`. Each test passes the iter232 stage A validity gate before being
committed. The test is then applied, unchanged, to the candidate patch in its pinned container.

The oracle **flags** a row when its test reports `FAIL`.

## Two arms, and why both are reported

**Gold-free arm (primary).** Every generated test counts. No gold is consulted anywhere in the pipeline. This
is the deployable configuration and its false-positive rate includes tests that are simply wrong.

**Gold-validated arm (diagnostic, not deployable).** Restricted to tests that PASS when run against the gold
patch. Gold is used *only* to check that a test correctly encodes the issue's intent; the author never sees
it. This isolates how far the mechanism reaches when the test itself is correct, and it is an upper bound on a
real system, not a measurement of one.

Reporting only the second would overstate a deployable capability; reporting only the first would confound the
mechanism with test-writing quality. Both are published, primary first.

## Endpoints

- Recall and false-positive rate for **both arms**, each with a Wilson interval and the full missing-outcome
  triple, reported beside iter230 `2/13`+`5/54`, iter231 `4/13`+`10/54`, and iter232 `2/13`+`12/54`.
- **Recall on the `value` subclass**, which is the entire point. Both prior instruments score `0/10`.
- Rates over the `25` non-gold-identical negatives as well as all `54`, because iter233 established the full
  negative set is half trivially separable.
- Every row without a valid test, and every test that fails on gold, listed individually.

## Pre-registered expectation

Stated before any data:

1. The gold-free arm will have a **high** false-positive rate — likely above `0.3` — because a test written
   from an issue alone is often simply wrong, and a wrong test fails on correct code.
2. The gold-validated arm will catch **more than `0/10`** on the value subclass. This is the falsifiable
   claim. Both prior instruments scored `0/10`; if an issue-derived reference reaches even `2/10`, the
   mechanism is real.
3. Recall will be **bounded by whether the issue states expected behavior**. Three of the thirteen positives
   have issues that do not, and those should be unreachable by this instrument for the same reason as before.

If expectation 2 fails — if a patch-blind, issue-derived reference also scores `0/10` — that is a strong
negative result and a genuine strengthening of the ceiling: the value-wrong class would then resist not only
patch inspection but issue-derived assertion, leaving only genuinely independent authorship with access to
information the issue does not contain.

## Consequence for the paper, either way

The paper currently states that no gold-free instrument can flag the value-wrong majority. If iter234's
gold-validated arm catches a meaningful share, that claim must be **narrowed** from "no gold-free instrument"
to "no gold-free instrument that reasons from the patch," and the ceiling repositioned as a property of
patch-inspecting detectors rather than of the class. That correction is pre-committed here so it cannot be
quietly avoided later.

## Acceptance bars

1. The benchmark sha is unchanged (`10dc898c…5b8928`), denominators `13`/`54`.
2. No test author is shown the candidate patch, the gold patch, a hidden test, or a witness. The exact prompt
   is committed and machine-checked for those channels.
3. Every committed test passes the iter232 stage A validity gate.
4. Both arms are reported, primary first, each with intervals and the missing-outcome triple.
5. Rates are reported over both the full `54` negatives and the `25` non-gold-identical ones.
6. Container execution uses pinned images under the iter231 isolation flags and the wall-clock row ceiling.
7. No sealed predecessor evidence byte changes; no runtime-manifest-pinned file is edited; iter212 is not
   touched.

## Falsifiers

- Any author stage is shown the candidate patch, gold, a hidden test, or a witness.
- The gold-validated arm is reported as the headline, or without the gold-free arm beside it.
- Recall is reported without the matching false-positive rate or the missing-outcome triple.
- Iter234 is described as TCP-1, as satisfying any iter212 gate, or as replacing human reviewers.
- The frozen benchmark is altered, or a manifest-pinned file is edited.

## Claim boundary

Iter234 measures one model-authored, issue-derived test instrument on a fixed `13`-positive, `54`-negative
benchmark. It is not TCP-1, not a deployable verification system, not a leaderboard, and not a
state-of-the-art claim. Intervals on `13` positives remain roughly `±0.2` wide. A positive result would say
the mechanism behind independently-authored consequence tests is real and worth the human investment TCP-1
requires; it would not establish that the human version works.

## Execution envelope

Allowed: patch-blind test-generation provider calls bounded at three attempts per row, safe container
execution of validated tests against committed candidate and gold patches, local analysis, repository
publication. Estimated provider spend under `$25`, well inside the operator-approved budget. Forbidden:
showing any author stage the patch, gold, a hidden test, or a witness; executing a test failing stage A;
altering the frozen benchmark; editing manifest-pinned or sealed files; and any claim that this fills an
iter212 gate.
