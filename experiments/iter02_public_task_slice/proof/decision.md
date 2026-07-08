# Iteration 02 Decision

Selected slice:

```text
codeclash_dummy_swebench_receipt_slice
```

## Why This Slice

The `iter00` target was not SWE-bench alone. It was a hybrid overlay: CodeClash for
goal-oriented software-engineering pressure, and SWE-bench Verified for a stable public evidence
surface.

The correct first slice therefore keeps CodeClash in the loop. The no-LLM CodeClash dummy
tournament is the cheapest public tournament path that can produce real run artifacts without
provider API calls. SWE-bench Verified row `astropy__astropy-12907` is used only as the receipt
field substrate: issue statement, base commit, patch hash, test-patch hash, and named tests.

## Why Not SWE-bench Alone

SWE-bench Verified alone is easier to run as metadata, but it would weaken the target selected by
the survey. Telos is testing completion proof under agent-workflow pressure, not only whether a
static issue row can be described.

## Why Not Full CodeClash PvP Yet

Full CodeClash PvP configs are model-vs-model benchmark runs. They introduce provider keys, model
spend, and more runtime variance before the receipt protocol has proven it can capture a small
public run. That would violate the cheap-first standard.

## Local Infrastructure Finding

`uv` and Python 3.11 are available after local setup. CodeClash's non-Docker dummy-arena unit tests
pass. Docker engine calls on this machine time out, so the tournament smoke is the next gate, not
an unverified claim inside this result.

## Next Gate

Run `iter03_codeclash_smoke`:

1. verify Docker readiness or use a pre-registered isolated sandbox,
2. run the no-LLM CodeClash dummy tournament,
3. convert logs into a Telos receipt,
4. reject the result if the receipt lacks artifact, test, or diff-scope evidence.
