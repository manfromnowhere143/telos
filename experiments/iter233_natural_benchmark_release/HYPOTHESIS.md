# Iter233 — release the natural certified-yet-wrong benchmark as a standard eval

Status: prospective, pre-registered before any release artifact exists. It reuses the frozen iter230
benchmark, the iter231 witnesses and divergence labels, and the iter232 validated exercises, all unchanged.

Predecessor merged master: `4d7ce55`.

## Why iter233 exists

The mission has produced something other people can use, and it is currently only usable by reading this
repository's experiment tree. Three measurements now exist on one fixed benchmark: a gold-free static panel at
`2/13` recall and `5/54` false positives, a gold-free execution oracle at `2/13` and `12/54`, and a value-wrong
subclass that neither reaches, `0/10` with no missing outcomes.

A benchmark is worth more than a result if others can run their own detector against it. Iter233 packages the
`13` confirmed certified-yet-wrong patches and `54` certified-correct patches, their gold-differential
witnesses, the validated exercises, and a scoring harness, so that a third party can measure their own
gold-free detector and compare against three committed baselines.

This is packaging, not a new measurement. It must produce no new number about any detector.

## The leakage split, which is the whole design problem

A benchmark that ships the answers alongside the inputs measures nothing. The release therefore separates two
directories with different contracts:

- **`inputs/`** — exactly what a gold-free detector is permitted to see: the issue text, the public
  `FAIL_TO_PASS` test names, and the candidate patch. Nothing else.
- **`answers/`** — the label, the gold-differential witness observables, and the divergence-type label. Needed
  to score, and sufficient to cheat.

The bar: **no file under `inputs/` may contain the gold patch, a hidden test name, a witness observable, or a
label.** This is machine-checked by a leakage scanner over the built artifact, not asserted in prose.

## Endpoints

- A built release under `experiments/iter233_natural_benchmark_release/release/` containing all `67` rows.
- A scoring harness that takes a detector's per-row flag decisions and reports recall, false-positive rate,
  Wilson intervals, the missing-outcome triple, and the crash/value divergence split — the same reporting
  contract the repository applies to itself.
- Three committed baselines reproduced *through the harness* from committed evidence: iter230 static, iter231
  oracle, iter232 oracle. If the harness cannot reproduce them, the harness is wrong.
- A release README stating the interval width, the contamination risk, and what the benchmark does not
  support.

## Acceptance bars

1. The benchmark sha is unchanged (`10dc898c…5b8928`), and the release contains exactly `13` positives and
   `54` negatives.
2. Zero leakage hits: no gold patch, hidden test name, witness observable, or label under `inputs/`.
3. Every row's candidate patch in the release hashes to the value committed in the frozen eval set.
4. The harness reproduces all three baselines exactly from committed evidence.
5. The release README states the `13`-positive interval width and the contamination limitation explicitly.
6. No sealed predecessor evidence byte changes, and no runtime-manifest-pinned file is edited.

## Falsifiers

- Any leakage hit under `inputs/`.
- The harness fails to reproduce a committed baseline, or reproduces it only after the baseline is adjusted.
- The release is described as a leaderboard, or as supporting a state-of-the-art or model-ranking claim.
- A new detector number is produced and published under cover of a packaging iteration.
- The frozen benchmark is altered, or a manifest-pinned file is edited.

## Claim boundary

Iter233 ships an artifact. It measures nothing new. The benchmark has `13` positives, so any recall measured
on it carries a Wilson interval roughly `±0.2` wide, and it cannot separate detectors whose true recall
differs by less than that. It is a fixed, small, naturally-occurring sample from six solver runs over one
cohort, not a population sample, and not a leaderboard.

The instances are public SWE-bench Verified rows and the candidate patches are committed in this repository,
so a model trained after this release may have seen them. That limitation is permanent and must be stated in
the release itself, not only here.

## Execution envelope

Allowed: building the release from committed evidence, running the scoring harness over committed baseline
decisions, local analysis, repository publication. Forbidden: any provider call, any new detector
measurement, any leaderboard or ranking claim, altering the frozen benchmark, and editing any
runtime-manifest-pinned or sealed file.
