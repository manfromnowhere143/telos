# Results

Canonical results are published in each experiment's version-controlled, correction-preserving `RESULT.md`
and proof directory, rather than duplicated here. The current standing result and correction ledger are
summarized in the root `README.md`; the manuscript source and status are in `paper/`.

Iter202 is a preserved scenario-safety protocol/execution null, recorded in
[`RESULT.md`](../experiments/iter202_natural_rate_scaled/RESULT.md). Its provider stages completed `53` solver
and `39` eligible scenario calls, yielding `50` valid patches, `38` scenario programs, and one original
missing scenario. The frozen pre-execution guard admitted `29` programs and rejected `9` with `21`
findings; no scenario or certification execution occurred, so iter202 has no rate `N`, `k`, or `u`.

The active gate is iter203, a separately disclosed post-provider recovery over the sealed iter202 bytes.
Do not publish or summarize an iter203 result until all `50` patches have complete official-certification
evidence, only the safety-admitted scenario copies have executed, all eight execution-shard receipts and
the single-run-attempt aggregate receipt validate, missing witnesses remain explicit, and the complete
evidence unit passes its guards. Partial or mixed-attempt evidence is invalid.
