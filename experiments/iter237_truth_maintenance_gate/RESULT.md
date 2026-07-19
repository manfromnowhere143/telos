# Iter237 result — restoring claim boundaries before further science

Status: **corrected locally; remote Python 3.11 and 3.12 CI remains required
before merge.**

This was a `$0` integrity correction over committed bytes. It made no provider
call, changed no scientific numerator, ran no container experiment, dispatched
no workflow, and did not modify the sealed iter235 predecessor. The retained
machine-readable result is
[`proof/correction.json`](proof/correction.json); its guard rebuilds the
quantities below from predecessor builders and evidence.

## Corrected verdicts

- T1 — transfer: `untested`. Iter236 reconstructs selectors for `447`
  held-out rows, but its registered transfer records contain no candidate-patch
  susceptibility endpoint or outcome labels. The three selector prevalences
  regenerate; predictive enrichment does not.
- T2 — fresh-cohort concentration: `inconclusive`. Iter224 contributes
  `k=0,N=15,u=6`; iter228 contributes `k=0,N=22,u=7`. Together the
  least-favourable accounting is `13/37`, which is not below the reused
  reference-solver result `5/29` with `u=0`.
- T3 — cross-solver recurrence: `supported`, within its narrow scope. The
  corrected fixed-cohort runs are `5/29`, `2/25`, `3/17`, `4/14`, and `1/16`,
  with `u=0,2,2,2,1`. Across all six measured runs, `17` patch-level positives
  correspond to `12` unique task identities. This is recurrence on one reused
  convenience cohort, not population generalization, model independence, a
  population rate, or a model ranking.
- T4 — benchmark labels: `operational_reference_differential`. The frozen
  detector set has `13` operational positives and `54` mixed controls:
  `29` normalized-identical controls and `25` one-witness no-divergence controls.
  Without independent semantic adjudication, detector results over those
  controls are flag rates, not validated false-positive rates.

The exploratory within-cohort fix-size comparison regenerates as
Mann–Whitney `U=331` with asymptotic two-sided `p=0.005347305449293553`
using tie and continuity correction. It was selected after inspection and is
not a validated transfer result.

## Evidence and falsifier

`scripts/validate_iter237_truth_maintenance.py` re-derives T1 from the iter236
builder, T2 from the iter224/iter228 audit reports, T3 from the iter235 target
builder plus retained original and recovery verdicts, and T4 from the frozen
iter230 evaluation manifest. It also checks every path under iter235 against
merged-master commit `27e8f5ab44db637be24eb8eee96b283cc2cf0da4`.

The same guard requires `added_source_lines` to obtain its per-file inclusion
decision by executing the imported `adv.one_src` predicate and rejects the
known-bad fixture that restates the historical `"/test"` / `"test_"` string
conditions.

The known-bad fixture promotes selector prevalence to “supported transfer.”
The focused test requires the typed artifact comparator to reject that
mutation. This demonstrates that the new gate fires on the inference error it
was created to prevent.

## Local verification

The final local working-tree bytes passed:

- `831` tests under Python `3.11.15`, with `9` explicitly optional SciPy
  equivalence cases skipped because SciPy is not in the locked CI environment;
- all `289` guard commands derived from `.github/workflows/ci.yml`, with bare
  `pytest` routed through the same Python `3.11.15` interpreter;
- the repository-wide libm guard across `472` active Python files;
- the JSON, documentation, current-paper, current-state, mission-loop,
  supply-chain, iter200 predecessor/successor, and iter237 correction guards;
- a twice-identical 16-page PDF build at `SOURCE_DATE_EPOCH=1784419200`, with
  source SHA-256
  `0bccdec8397f085e0d9a981f51403780c2c346aab0a2eb1cd8c38e7b64d6ae58`
  and PDF SHA-256
  `21a3505d1819b913e0159f73a29a1a0329f43c8bc58a63734d49e68b8cecfed8`;
- visual inspection of all 16 PDF pages and all five README Mermaid diagrams,
  with no clipping, overlap, or unreadable content found; and
- a byte-identical iter235 tree against merged-master commit
  `27e8f5ab44db637be24eb8eee96b283cc2cf0da4`.

This is local macOS/arm64 evidence. It does not certify the required Linux
Python 3.11 and 3.12 CI jobs, which remain mandatory before merge.

## Boundary and next gate

This result corrects inference over operational labels. It supplies no new
provider result, population rate, independent semantic ground truth, or
validated transfer measurement. A green closure covers registered CI commands
and the registered claims they check; it is not evidence that every number in
all prose has a builder until a separate complete claim registry exists.

The next scientific gate is **GROUND-TRUTH-1**: independent, blinded human
semantic adjudication at unique-task level, including the frozen benchmark and
the thirteen missing fresh-cohort outcomes. No new solver purchase is
authorized by iter237.

## Regenerating

```bash
python3 scripts/validate_iter237_truth_maintenance.py
pytest -q tests/test_iter237_truth_maintenance.py
```
