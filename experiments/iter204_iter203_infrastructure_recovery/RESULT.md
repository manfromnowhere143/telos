# Iteration 204 Result - Pre-Dispatch Workflow-Parse Infrastructure Null

Status: **PRE-DISPATCH INFRASTRUCTURE NULL**. Iter204 is closed under its frozen no-retry rule. Its
approved source reached green primary-branch CI, but an authorized dispatch API request was rejected while
parsing the workflow and did not create a `workflow_dispatch` run. No provider, container, patch,
certification, scenario, adjudication, or judge process started.

## Approved source and public workflow records

The approved merge/source commit is `c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446`. Primary push CI run
[`29465925393`](https://github.com/manfromnowhere143/telos/actions/runs/29465925393), attempt `1`, completed
successfully with both required jobs: `verify py3.11` and `verify py3.12`.

The public API identifies workflow `314113289` as active. It also exposes two failed `push` workflow
records for the syntactically invalid iter204 workflow:

- branch publication run
  [`29465584664`](https://github.com/manfromnowhere143/telos/actions/runs/29465584664), attempt `1`, at
  `8342315dd2fa7ec865bd7c654ec4ec098675dfab`;
- primary-branch publication run
  [`29465924803`](https://github.com/manfromnowhere143/telos/actions/runs/29465924803), attempt `1`, at the
  approved merge commit.

Both records have event `push`, conclusion `failure`, zero jobs, and zero artifacts. Their log-download API
returns HTTP `404`, so no public job or run log is available. The workflow name falls back to its path,
`.github/workflows/iter204-execute.yml`, which is consistent with a workflow that could not be parsed.
These are real public workflow records and must not be described as absent. They are not
`workflow_dispatch` runs and did not execute iter204 jobs or science.

## Dispatch rejection

After the green primary CI result, at least one locally observed authorized iter204 dispatch API request
returned HTTP `422`:

```text
Invalid Argument - failed to parse workflow: (Line: 318, Col: 36): Unrecognized named-value: 'runner'. Located at position 1 within expression: runner.temp
```

That message is a locally observed API response. It has no public dispatch run or log and is therefore not
represented as a raw public workflow artifact. A subsequent read-only public API query returned exactly
zero iter204 `workflow_dispatch` runs. The normalized evidence combines that disclosed local observation
with canonicalized public workflow, run-list, push-record, job, artifact, and primary-CI metadata.

## Root cause and scientific boundary

Line `318`, column `36` uses `runner.temp` inside the `execute` job's job-level `env` mapping. The `runner`
context is unavailable there, so GitHub rejected the workflow before creating the requested dispatch run
or any job. The correction changes workflow-context plumbing and therefore requires a separately versioned
iteration under the frozen iter204 rule; it cannot be inserted into iter204 and retried.

Iter204 produced:

- `0` `workflow_dispatch` runs;
- `0` workflow jobs from any `workflow_dispatch` run;
- `0` provider calls;
- `0` Docker create/run invocations;
- `0` patch applications;
- `0` official certification executions;
- `0` scenario executions;
- `0` scientific artifacts.

Iter204 contributes no `N`, `k`, or `u`; those quantities are absent, not zero. The two public `push`
parse-failure records are infrastructure metadata only and cannot be interpreted as scientific attempts or
outcomes.

## Next gate and claim boundary

Recovery proceeds only under the separately versioned iter205 workflow-context protocol. The exact number
of rejected API requests is not auditable from public run metadata, so this result claims only the observed
lower bound of one. There is no iter204 retry, dispatch-created attempt `2`, provider regeneration, or
reinterpretation of either push record. The iter202/iter203 scientific corpus and the frozen iter204
hypothesis/runtime manifest remain unchanged.

Supported: the approved iter204 workflow was rejected at its dispatch parse boundary because it referenced
an unavailable context in job-level `env`; zero `workflow_dispatch` runs and zero scientific execution
resulted.

Not supported: any patch, certification, wrongness, missingness, rate, pooled, population-frequency,
model-comparison, leaderboard, deployment, state-of-the-art, or generalization claim.

## Evidence

- `proof/pre_dispatch_infrastructure_null.json` - normalized local rejection and public-metadata boundary;
- `proof/raw/public_dispatch_metadata/manifest.json` - hashes and retrieval paths for the public snapshots;
- `proof/raw/public_dispatch_metadata/workflow.json` - complete canonicalized public workflow metadata;
- `proof/raw/public_dispatch_metadata/dispatch_runs.json` - complete empty `workflow_dispatch` run list;
- `proof/raw/public_dispatch_metadata/push_validation_runs.json` - exact projected identities and empty
  job/artifact/log availability for both `push` records;
- `proof/raw/public_dispatch_metadata/primary_ci_projection.json` - approved source CI identity and required
  job conclusions;
- `HYPOTHESIS.md` and `proof/raw/runtime_manifest.json` - frozen iter204 protocol and runtime, preserved
  byte-for-byte.
