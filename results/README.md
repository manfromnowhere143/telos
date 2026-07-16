# Results

Canonical results are published in each experiment's version-controlled, correction-preserving `RESULT.md`
and proof directory, rather than duplicated here. The current standing result and correction ledger are
summarized in the root `README.md`; the manuscript source and status are in `paper/`.

Iter202 is a preserved scenario-safety protocol/execution null, recorded in
[`RESULT.md`](../experiments/iter202_natural_rate_scaled/RESULT.md). Its provider stages completed `53` solver
and `39` eligible scenario calls, yielding `50` valid patches, `38` scenario programs, and one original
missing scenario. The frozen pre-execution guard admitted `29` programs and rejected `9` with `21`
findings; no scenario or certification execution occurred, so iter202 has no rate `N`, `k`, or `u`.

Iter203 is a separately disclosed execution-infrastructure null, published in
[`RESULT.md`](../experiments/iter203_iter202_safety_recovery/RESULT.md). Its sole canonical run `29460393525`
passed authorization and immutable-source checks, then returned raw Docker exit `125` on all `50/50` first
Docker `run` invocations across eight runners before any in-container command. The local logger used
`max-file=1` while compression remained on by default, a combination Docker `28.0.4` rejects at container
creation. Collection was skipped, zero workflow artifacts were uploaded, and zero official certification
or scenario programs executed. Iter203 therefore
has no rate `N`, `k`, or `u`. The runner deleted its hidden Docker stderr files, so the exact daemon message
is not retained; the root cause follows from the frozen option tuple and Docker's version-matched validation
source. It was not an authentication, billing, credit, or quota failure.

The active gate is
[`iter204`](../experiments/iter204_iter203_infrastructure_recovery/HYPOTHESIS.md), a separately identified
pre-scientific-output runtime recovery over the same
sealed bytes and exact row plan. Do not publish a scientific or rate result until all `50` patches have
complete official-certification evidence, only safety-admitted scenario copies have executed, all eight
shard receipts and the single-run-attempt aggregate receipt validate, missing witnesses remain explicit,
and the complete evidence unit passes its guards. A smoke failure or incomplete execution must still be
published as an infrastructure null; its bounded failure evidence is valid for that null but ineligible for
certification, scenario, denominator, adjudication, or rate claims. Only the first global iter204 dispatch
and run attempt `1` are eligible; any failure requires a new iteration, never a rerun or second dispatch.
Mixed-attempt evidence is invalid.
