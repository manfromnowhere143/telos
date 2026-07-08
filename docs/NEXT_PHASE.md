# Next Phase

## Current Action

Run `iter03_codeclash_smoke` exactly as frozen in
[`../experiments/iter03_codeclash_smoke/HYPOTHESIS.md`](../experiments/iter03_codeclash_smoke/HYPOTHESIS.md).

The output is not a model score. It is a no-LLM public-run receipt:

- run the pinned CodeClash dummy tournament or publish the blocked infrastructure result,
- preserve tournament artifacts,
- produce a valid Telos receipt,
- keep model/API/GPU spend at zero.

## Infrastructure Discipline

Available cloud and sandbox resources are escalation tools, not default proof. The order is:

1. local receipt validation,
2. local CodeClash smoke under Docker,
3. E2B or sandboxed execution only when local Docker is blocked and the run stays no-LLM,
4. GPU or model cloud only when a later frozen gate names the spend and expected evidence.

No GPU or model run is authorized by `iter00`, `iter01`, `iter02`, or `iter03`.

## After The CodeClash Smoke Gate

If the smoke gate passes:

1. Publish the receipt and parsed artifacts.
2. Freeze the first model-agent run `HYPOTHESIS.md`.
3. Keep the first model run small enough to falsify receipt quality.
4. Escalate to sandbox/cloud only if the frozen run requires isolation or compute.

If the smoke gate fails:

1. Publish the failure.
2. Fix the concrete infrastructure gap or choose a narrower CodeClash slice.
3. Do not start a model run.
