# Iter242 — iter241 successor-baton closure

Status: **preregistered local engineering gate**. This gate may close only the
interrupted repository-control transition after Iter241. It cannot reinterpret
or retry the failed Iter241 capture.

Predecessor: local authorization commit
`76d3c6378a824e458ac6a89cf49322163fbc83b8`, whose seal-registry record names
`iter241-completed-evidence-seal` as predecessor and authorizes only
`experiments/iter242_iter241_successor_closure` plus synchronized control-plane
validation.

Budget: `$0.00`. External requests, workflow runs, provider calls, human
contact, and scientific executions: `0`.

## Registered question

Can Telos reach one clean local stopping point in which the failed Iter241
evidence remains byte-identical, its exact successor seal qualifies, every
current test entrypoint uses one authenticated exact-commit runner, current
surfaces and registries agree, and the complete offline repository closure
passes?

## Acceptance gates

1. The Iter241 protected subtree at reference commit `09da0b64331d0f39980843ef48d6b7fd536cab0e`
   remains exact and `iter241-completed-evidence-seal` validates.
2. The authenticated runner binds its own bytes and every delegated source to
   identical worktree, Git-index, and `HEAD` bytes before executing the router.
3. Pytest plugin autoload, environment overrides, `conftest.py`, and tracked
   `pytest_plugins` declarations fail closed before collection.
4. Only the two marker-bound authorization-HEAD tests may be deselected, and
   only after the exact Iter241 successor seal qualifies.
5. `AGENTS.md`, current handoff, and continuous CI use the authenticated runner;
   direct bare pytest is not a current acceptance entrypoint.
6. Current README, handoff, audit, pointer, claim registry, seal registry,
   workflow registry, paper guard, experiment index, lint, docs, and every
   CI-derived offline command agree from clean exact committed bytes.
7. Known-bad mutations for runner/index drift, tracked plugin loading, workflow
   credentials, timeout, test-command bypass, and Iter241 subtree drift are
   rejected.

## Fixed conclusion boundary

Passing supports only `local_successor_baton: supported`. Iter241 remains:

```text
capture_completeness: failed
raw_header_byte_fidelity: failed
repository_closure: failed
retry_authority: none
independent_ground_truth: blocked
scientific_authority: none
```

No local pass authorizes push, pull request, merge, GitHub settings or workflow
mutation, provider or model use, scientific execution, human contact, spending,
publication, release, or visibility change.

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
