# Telos paper

The findings paper is a research draft. Iter241's nonrepeatable read-only
iter240 repository-closure attempt failed its completeness contract because a
required response member was omitted and raw header-section bytes were never
retained. The retained canonicalized header-pair documents do not restore byte
fidelity: `capture_completeness: failed` and
`raw_header_byte_fidelity: failed`. The additive evidence correction is the
active engineering record and authorizes no retry. Iter237 rebuilt and rebound
the July 19 source and 16-page PDF; neither artifact has been submitted.

The manuscript's current scientific boundary is deliberately narrow:
cross-solver recurrence was observed on one reused convenience cohort;
fresh-cohort concentration is inconclusive under unresolved outcomes;
fix-size transfer is untested; and the released detector labels are
operational reference differentials rather than independent semantic ground
truth. The claim registry is the canonical reviewed resolution authority; the
active-gate coverage report is retained evidence that the declared surfaces
resolve against it:

- [`mission/claim_registry.json`](../mission/claim_registry.json)
- [`active gate`](../experiments/iter241_iter240_repository_closure/HYPOTHESIS.md)
- [`claim_coverage_report.json`](../experiments/iter241_iter240_repository_closure/proof/claim_coverage_report.json)

The manuscript and root README are current claim projections, while the
experiment index is the correction-preserving discovery surface:

- [`paper/telos.tex`](telos.tex)
- [`README.md`](../README.md)
- [`docs/EXPERIMENT_INDEX.md`](../docs/EXPERIMENT_INDEX.md)

Historical experiment records remain visible through the experiment index.
This page is a build and release guide, not a second empirical-results ledger.
It is itself a declared public claim surface, so any quantitative statement
left here must be classified by the claim registry.

## Reproducible build

The committed PDF is built from `telos.tex` with a fixed metadata epoch:

```bash
cd paper
SOURCE_DATE_EPOCH=1784419200 tectonic telos.tex
```

Two consecutive Tectonic builds must have identical SHA-256 digests. After a
source change, rebuild twice, refresh the source/PDF bindings, render every
page, and inspect the rendering before proposing acceptance.

## Release boundary

The paper is not submission-ready. External submission remains blocked on:

- independent author and affiliation confirmation;
- a fresh primary-source citation audit;
- accessibility review or an accessible companion artifact;
- exact claim-registry, source, PDF, and retained-evidence agreement;
- explicit operator authorization for publication.

A successful local validator, remote CI run, digest comparison, or visual
inspection is engineering evidence only. None establishes independent
semantic ground truth, a population rate, detector efficacy, transfer,
benchmark validity, or state-of-the-art performance.

No submission, release, provider call, scientific rerun, or purchase is
authorized by this file.
