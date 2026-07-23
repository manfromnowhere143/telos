# Iter246 — iter245 baton refresh

Status: **preregistered local engineering gate**. This gate may bring only the
mutable operational baton current with the completed and merged Iter245
remote-integration closure. It cannot revise a research conclusion, a dated
historical record, or a sealed evidence tree.

Predecessor: local authorization commit
`f51faa29b7e56046f893a0e00535bfe9e1d8e622`, whose seal-registry record names
`iter245-completed-evidence-seal` as predecessor and authorizes only
`experiments/iter246_iter245_baton_refresh` plus synchronized control-plane
validation.

Budget: `$0.00`. External requests, workflow runs, provider calls, human
contact, and scientific executions: `0`.

## Registered question

Can Telos reach one clean local stopping point in which the operational baton
— the dated handoff, the dated audit, `mission/current.json`, the synchronized
README state, and the governed registries — describes the merged Iter245
closure as complete, while the 2026-07-22 dated files remain byte-identical,
every sealed evidence tree validates exactly, no research conclusion changes,
and the complete offline repository closure passes?

## Acceptance gates

1. The merged state is receipt-verified: `master` at
   `9b61abf1f7afb305656544c5823da9b16a4eb69b` with ordered parents, a
   byte-identical merged tree, and green sealed-head, pull-request, and
   merged-master CI runs, as recorded in the dated 2026-07-24 audit.
2. `docs/HANDOFF-2026-07-22-iter245.md`, `docs/TELOS-AUDIT-2026-07-22.md`, and
   every sealed experiment tree remain byte-identical; the seal registry
   validates exactly.
3. The claim migration to this gate retains every claim with no new claims and
   no claim updates; every live quantitative atom is classified with no
   conflicts, and the reviewed binding-authorization digest binds the new
   surfaces.
4. `mission/current.json`, the dated handoff, the dated audit, README,
   `paper/README.md`, the claim registry, the seal registry, and the workflow
   registry agree from clean exact committed bytes.
5. Current-state, paper, JSON, documentation, claim, seal, workflow, mission
   loop, experiment index, lint, and every CI-derived offline command pass.

## Fixed conclusion boundary

Passing supports only `operational_baton_current: supported`. The scientific
status remains blocked pending independent ground truth, and the claim
boundary remains unchanged. Iter241 remains failed, Iter243 remains sealed
failed remote-integration evidence, and Iter244 remains sealed negative
design evidence.

No local pass authorizes force push, workflow dispatch or rerun, GitHub
settings or workflow mutation, an Iter241 retry, provider or model use,
scientific execution, human contact, spending, paper submission, publication,
release, deployment, or visibility change. The operator's standing
feature-branch, pull-request CI, ordered-parent merge, and post-merge
verification procedure is the only publication route.

## Reproduction

```bash
python3 -I scripts/run_iter241_pytest.py --plan
python3 -I scripts/run_iter241_pytest.py --run
ruff check .
python3 scripts/validate_json.py
python3 scripts/validate_docs.py
python3 scripts/validate_current_paper.py
python3 scripts/validate_current_state.py
python3 scripts/validate_claim_registry.py
python3 scripts/validate_seal_registry.py
python3 scripts/validate_workflow_registry.py
python3 scripts/validate_mission_loop.py
python3 scripts/experiment_index.py --check
python3 scripts/run_ci_closure.py
git status --short --branch
```
