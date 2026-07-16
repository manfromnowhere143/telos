# Results

Canonical results are published in each experiment's version-controlled, correction-preserving `RESULT.md`
and proof directory, rather than duplicated here. The current standing result and correction ledger are
summarized in the root `README.md`; the manuscript source and status are in `paper/`.

The current construction ledger is correction-first. Iter192 is conservatively adjudicated `FAIL` on its
overbroad novelty interpretation; its literal v1-specific falsifier trigger is indeterminate because
iter151 retained no accepted patch bytes. Iter151 had already reported the same class-level `0/20`
test-suite precursor, and nineteen instance IDs overlap. The retrospective `40/40` unresolved count remains;
historical tarballs contain `139`
harness-resolved hack-tagged evaluations across `65` instance IDs, while disposition evidence binds only
`23` discarded iter152 IDs (`17` overlapping the harness-resolved set), not all `139`. Conceptual
firstness is withdrawn. Iter195 is strict protocol `FAIL`: its scenario generator received gold and variant hunks, produced one targeted
scenario rather than the registered 20-input validation, and did not satisfy the no-gold or raw-prompt bars.
Its `10` divergences remain exploratory reference-differential witnesses. Iter196 is partial and
protocol-blocked, iter198's original accuracy gate is superseded as `FAIL`, and iter199's additional `12`
witnesses follow a post-provider/pre-execution stated design that was not independently preregistered. The
released `22`-row corpus is therefore a constructed gold-assisted reference-differential artifact, not an
independently adjudicated semantic benchmark.

The unrepaired iter179 panel score is `17/40` from `240` score-producing calls with a conservative
estimated spend guard of `$13.128090`, not a provider invoice. The `$13.317840` iter175+iter178 whole-run
guard includes three excluded diagnostics, and the rounded `$13.59` through-iter181 total includes five
more excluded repair diagnostics; neither diagnostic stage is part of the primary score.

Iter202 is a preserved scenario-safety protocol/execution null, recorded in
[`RESULT.md`](../experiments/iter202_natural_rate_scaled/RESULT.md). Its provider stages completed `53` solver
and `39` eligible scenario calls, yielding `50` valid patches, `38` scenario programs, and one original
missing scenario. The frozen pre-execution guard admitted `29` programs and rejected `9` with `21`
findings; no scenario or certification execution occurred, so iter202 has no rate `N`, `k`, or `u`. A
separate interrupted invocation retained no outputs and is conservatively charged `53` calls and an estimated
`$2.65`; that bookkeeping charge is not part of the retained scientific corpus.

Iter203 is a separately disclosed execution-infrastructure null, published in
[`RESULT.md`](../experiments/iter203_iter202_safety_recovery/RESULT.md). Its sole canonical run `29460393525`
passed authorization and immutable-source checks, then returned raw Docker exit `125` on all `50/50` first
Docker `run` invocations across eight runners before any in-container command. The local logger used
`max-file=1` while compression remained on by default, a combination Docker `28.0.4` rejects at container
creation. Collection was skipped, zero workflow artifacts were uploaded, and zero official certification
or scenario programs executed. Iter203 therefore
has no rate `N`, `k`, or `u`. The runner deleted its hidden Docker stderr files, so the exact daemon message
is not retained; the root cause follows from the frozen option tuple and Docker's version-matched validation
source.

Iter204 is a separately disclosed pre-dispatch infrastructure null, published in
[`RESULT.md`](../experiments/iter204_iter203_infrastructure_recovery/RESULT.md). Approved source
`c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446` passed primary CI run `29465925393`, but the workflow could
not be parsed. Its exact closure snapshot contains two public `push` records: runs `29465584664` and
`29465924803`, both attempt `1`, conclusion `failure`, with zero jobs and zero artifacts; public log
download returns `404`. At least one locally observed authorized dispatch API request returned HTTP `422`
because line `318`, column `36` referenced `runner.temp` from job-level `env`. The exact request count is
not publicly auditable, so only the observed lower bound of one is claimed. The public `workflow_dispatch`
run count at closure was exactly zero. No provider, container, patch, certification, scenario,
adjudication, or judge process started, so iter204 has no `N`, `k`, or `u`.

Iter205 is a separately disclosed pre-dispatch admission-history null, published in
[`RESULT.md`](../experiments/iter205_iter204_workflow_context_recovery/RESULT.md). Its source merged as
`4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f` after green primary CI run `29468769187`. Workflow
`314141096` is active and its complete all-event and dispatch histories are empty. The dispatch request command was
never reached: the read-only preflight found four iter204 `push` parser records rather than the exact two
preregistered. The two additions were caused by iter205 branch and primary publication. No iter205 dispatch
request was issued, and no dispatch API response or rejection exists. No iter205 workflow run, provider
process, container, patch, certification, scenario, adjudication, or judge process occurred; iter205 has no
`N`, `k`, or `u`.

Iter206 was sealed locally but stopped as a pre-publication claim-integrity null before any remote or
scientific action; it has no `N`, `k`, or `u`. The active gate is
[`iter207`](../experiments/iter207_claim_integrity_and_admission_recovery/HYPOTHESIS.md), a separately
versioned claim-integrity and admission recovery over unchanged scientific bytes and runtime semantics. It
binds the correction ledger, preregisters one final branch push, an exact successful attempt-`1` branch-push
and pull-request CI pair, one exact two-parent merge, green primary CI, and an exact admission snapshot
containing the known four iter204 rows plus only the two publication rows structurally bound to that push and
merge. It also requires the complete iter205 and iter206 histories to remain empty. A missing, seventh, or
malformed iter204 row or any predecessor run closes the gate without dispatch; after every gate passes, at
most one dispatch request is permitted. Do not publish a scientific
or rate result until complete official-certification evidence, only safety-admitted scenario execution,
all required receipts, explicit missingness, and every current guard validate under the exact selection
rule.
