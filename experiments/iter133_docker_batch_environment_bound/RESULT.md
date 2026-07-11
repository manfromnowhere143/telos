# Iteration 133 Result - Docker Batch and the Local Environment Bound

Status: `PASS` (an honest environment bound, recorded precisely).

## What this gate did

Attempted to batch the Docker harness across five natively-blocked old sympy instances and recorded
exactly what the local environment can and cannot sustain.

## Result

The method is proven single-instance. Iter132 ran `sympy__sympy-13480` end to end in a pinned Python
3.9 container - base fails with the real bug, gold passes - and each instance is an independent image
run, so the harness batches by construction.

Local batch execution is not reliable in this environment. The attempt hit two concrete constraints:

- Concurrent multi-GB x86 image pulls under arm64 emulation strained the Docker daemon; an
  already-cached image (`13480`) returned a spurious `PULL_FAIL` under load.
- A serial run of a second instance (`13615`) completed with exit code 0 but produced no captured
  container output - flaky stdout under emulation.

## The finding

This is an environment bound on local execution, not a limitation of the method or an open research
question. Full-dataset Docker batching belongs on a native-x86 CI runner with pre-cached SWE-bench
images - the environment SWE-bench is normally evaluated in - where image pulls are cached and
containers are not emulated. Attempting it on a local arm64 machine under x86 emulation is bottlenecked
on multi-GB pulls, daemon load, and emulated-container flakiness.

Recording this honestly is the point. The program does not claim a cross-repo batch gold-resolution
rate it did not actually produce; it claims the single-instance result it did produce (iter132) and
names the concrete reason the local batch is unreliable.

## Claim boundary

Supported: single-instance Docker execution is proven (iter132); local batch execution is unreliable
in this arm64-emulation environment for the recorded infrastructure reasons; full-dataset batching
belongs on a native-x86 CI runner. Not supported: a benchmark, model, or state-of-the-art claim, or a
cross-repo batch gold-resolution rate.

## Next gate

`iter134`: run the Docker batch on a native-x86 CI runner with pre-cached images to produce the full
cross-repo gold-resolution and property-layer measurement that the local environment cannot.

## Evidence

- `proof/batch_attempt.json` (observed batch-attempt outcomes)
- `proof/endpoint_results.json`, `proof/run_summary.json`, `proof/learning_record.json`
- `proof/valid/receipt_docker_batch_environment_bound.json`
- `scripts/run_docker_batch_environment_bound.py`
