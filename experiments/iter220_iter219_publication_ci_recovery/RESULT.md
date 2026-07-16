# Iter220 result — iter219 publication CI recovery

Status: PASS locally; remote publication gates pending. Publication-only. No iter219 number changes.

## Result

Iter219's exact seal `11e335e82100319a4f5f47d86eaea0c8e81edbbc` was published unchanged on draft PR `#13`.
Push CI run `29539630378` and pull-request CI run `29539645041` both failed on Python 3.11 and 3.12 at the
same step, `Detector methodology-correction guard`, with one message:

```text
HANDOFF.md is missing corrected detector text: locator-assisted, gold-validated
```

All `729` tests, every other guard, and every iter219 receipt passed in each failed job. The iter219 branch
and PR remain unchanged, were not rerun, and must not be merged.

## The sentence was correct; the scanner could not read it

`HANDOFF.md` wraps the required phrase as `locator-assisted,\ngold-validated`.
`scripts/validate_detector_methodology_correction.py` matched raw substrings with no whitespace
normalization, so a correct sentence failed purely because of line width.

**This is the fourth occurrence of one bug class in this repository**, and the second on this exact phrase in
this exact file:

1. iter214's handoff seal, previous session — the same phrase wrapped and failed the same scanner;
2. iter219's own `A1` guard during development — a wrapped phrase defeated its required-phrase check;
3. iter219's `validate_current_paper` check — a blockquote marker normalized to `right > reason`;
4. iter219's publication CI — this failure.

Cases 2 and 3 were fixed at the root as they appeared. Case 1 was fixed by reflowing prose, which repaired
that instance and left the mechanism armed. It fired again here.

## The real defect is how a known bug reached CI

Iter219's local closure ran a hand-listed subset of guards written from memory.
`validate_detector_methodology_correction.py` was never in that list. CI declares `257` guard commands;
iter219 ran roughly `7` and called the result a full closure.

A verification set chosen by the same agent that wrote the change is not an independent check. It is
Standard 9 at local scale: the gate passes against the author's idea of the gate rather than the real one.
Reflowing the sentence would have repaired this instance and left that mechanism intact for the next gate.

## Corrections

`C1` — `validate_detector_methodology_correction.py` collapses whitespace runs and strips leading blockquote
markers before matching, reusing the normalizer already proven in `validate_current_paper.py`. Normalization
only ever makes a required phrase easier to find and a forbidden phrase easier to catch, so it cannot hide a
real defect. A positive control asserts the scan still fails when the methodology text is genuinely absent
rather than merely wrapped.

`C2` — `scripts/run_ci_closure.py` parses `.github/workflows/ci.yml` and runs every guard command it
declares, honouring the workflow's `env -u NAME VAR=value` prefixes so provider-free reuse and credential
stripping survive. The list is derived, never hand-maintained. On first execution it immediately caught a
guard the hand list had missed. If CI gains a guard, local closure gains it with no edit.

## Bars

| Bar | Requirement | Observed | Verdict |
| --- | --- | --- | --- |
| 1 | Scanner reads the wrapped sentence; still fails on genuine absence | both | pass |
| 2 | Closure derives from `ci.yml`, honours env overrides, reproduces the failure | `257` commands derived | pass |
| 3 | Every CI guard passes locally at the iter220 seal | `257/257` | pass |
| 4 | Iter219 evidence byte-identical | `4/4` files | pass |
| 5 | Iter219 branch and PR `#13` unchanged | unmutated, unrerun, unmerged | pass |
| 6 | Full suite and synthetic merge pass at the seal | verified | pass |
| 7 | No provider, GPU, container, dispatch, payment, release, or scientific claim | all zero | pass |

## Claim boundary

Iter220 contributes no scientific `N`, `k`, `u`, benchmark score, effect estimate, model comparison,
population estimate, or TCP-1 admission change. Iter219's null stands exactly as published: forward `0.4066`
against a backward within-repository control of `0.4336`, difference `-0.0270` at `p = 0.925`, with the
cross-repository control's `p = 3.48e-24` recorded as the false positive that a pre-data amendment averted.

TCP-1 admission remains `2/11` with `9` blocked and `execution_authorized=false`. Iter212 remains unchanged
and inactive.

## Zero-action boundary

`0` provider or model requests, `0` GPU allocations, `0` scientific containers, `0` repository test
executions, `0` workflow dispatches or reruns, `0` payments, `0` releases, and `$0.00` spent.

## Reproduction

```bash
python3 scripts/run_ci_closure.py
python3 scripts/validate_iter220_iter219_publication_ci_recovery.py
python3 scripts/build_iter220_receipt.py --check
```
