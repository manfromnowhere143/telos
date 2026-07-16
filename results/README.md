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

Iter204 is now a separately disclosed pre-dispatch infrastructure null, published in
[`RESULT.md`](../experiments/iter204_iter203_infrastructure_recovery/RESULT.md). Approved source
`c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446` passed primary CI run `29465925393`, but the workflow could
not be parsed. Two public `push` records exist and must not be erased: runs `29465584664` and `29465924803`,
both attempt `1`, conclusion `failure`, with zero jobs and zero artifacts; public log download returns
`404`. At least one locally observed authorized dispatch API request returned HTTP `422` because line `318`,
column `36` referenced `runner.temp` from job-level `env`. The exact request count is not publicly auditable,
so only the observed lower bound of one is claimed. The public `workflow_dispatch` run count is exactly
zero. No provider, container, patch, certification, scenario, adjudication, or judge process started, so
iter204 has no `N`, `k`, or `u`.

The active gate is
[`iter205`](../experiments/iter205_iter204_workflow_context_recovery/HYPOTHESIS.md), a separately versioned
workflow-context recovery over the unchanged scientific bytes and exact row plan. It is not an iter204
retry. Do not publish a scientific or rate result until complete official-certification evidence, only
safety-admitted scenario execution, all required receipts, explicit missingness, and every current guard
validate under the new gate's exact selection rule.
