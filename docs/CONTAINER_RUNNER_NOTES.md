# Container runner notes

Operational findings about the SWE-bench container execution path. Read before re-running any
experiment that drives a container, and before "fixing" the shared runner.

## The shared runner is sealed evidence; do not edit it to fix a runtime break

`scripts/ci_iter200_execute.sh` is the certification + gold-differential runner for iter200,
iter223, iter225, iter226, iter227, and iter229. It is **hash-pinned into committed runtime
manifests**:

| Manifest | Pinned path | sha256 |
| --- | --- | --- |
| `experiments/iter202_natural_rate_scaled/proof/raw/runtime_manifest.json` | `scripts/ci_iter200_execute.sh` | `a7f95d11…5f799b` |
| `experiments/iter223_natural_rate_safety_aware/proof/raw/runtime_manifest.json` | `scripts/ci_iter200_execute.sh` | `a7f95d11…5f799b` |

Editing that file changes the sealed provenance of completed results. The binding is what lets a
reviewer say the committed numbers came from *that* runner. A drive-by edit to unbreak a run would
silently invalidate it.

**If the shared runner stops working on a current runner image, do not patch it in place.** Add a
new runner with its own manifest binding, as iter231 did with `scripts/ci_iter231_execute.sh`.

## Known break: the `local` log driver rejects `max-file=1` on current Docker

The first dispatched iter231 run (`29635923053`, 2026-07-18) failed all eight shards. Every row
returned `docker run` exit `125` before the container started:

```
failed to initialize logging driver: compression cannot be enabled when max file count is 1
```

The `local` driver compresses rotated files by default, and Docker rejects that at
`--log-opt max-file=1`. The fix is `--log-opt compress=false`, applied in
`scripts/ci_iter231_execute.sh`.

**The same three log flags are in the sealed shared runner.** Those experiments passed when they
executed, so a newer Docker on the `ubuntu-24.04` image tightened validation afterwards. The
consequence, stated plainly:

> Any re-run of iter200, iter223, iter225, iter226, iter227, or iter229 on a current runner image
> will fail this way, and the correct remedy is a new runner plus a new manifest — **not** an edit
> to the pinned file.

The completed results are unaffected: they were produced when the flag set was valid, and their
evidence is committed.

## `validate_iter202_runtime_freeze.py --check` does not pass on master

Independently observed while investigating the above, on unmodified `master`: the check fails
because iter202's committed scenarios use imports the *corrected* iter223 safety instrument rejects
(`types`, `uuid`, `sys`, `os`, `tempfile`, `mpl_toolkits`, `docutils`, `_pytest`, and a `getattr`
call).

This is a pre-existing condition, not a regression from iter231. The script is **not** in `ci.yml`
or `scripts/run_ci_closure.py`, which is why the 271-command closure is green while this check is
red. It means the historical scenarios predate the tightened instrument, and the freeze validator
applies today's instrument to yesterday's evidence.

Recorded rather than fixed: deciding whether to re-scope the validator to the instrument version
current at seal time, or to accept the divergence explicitly, is a claim-boundary decision, not a
mechanical repair. It is unresolved and should not be quietly closed by loosening the instrument.

## Diagnosing a failed shard cheaply

- `docker run` exit `125` is the daemon refusing to start the container — a malformed flag set. It
  is identical for every row, so `ci_iter231_execute.sh` aborts the shard on the first one.
- Exit `124`/`137` is the bounded timeout or kill — a hang, not a flag problem.
- On failure the workflow uploads a debug artifact containing the per-row logs; the daemon error is
  captured there, not in the job console.
- `scripts/watch_iter231_straggler.py` reports elapsed wall clock against each job's `startedAt`.
  Shard count is not a liveness signal. GitHub may report a `startedAt` slightly in the future for a
  just-scheduled job; those are counted as clock-skewed, never as running with a negative age.
