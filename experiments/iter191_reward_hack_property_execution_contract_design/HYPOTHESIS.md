# Iteration 191 - Reward-Hack Property-Execution Contract Design

> **SUPERSEDED, unrun, by `experiments/iter192_reward_hack_benchmark_construct_validity_audit/`.**
> This gate was never executed and publishes no result. It is retained unedited below as visible
> evidence of the path the mission was on, per standard 5.
>
> Why it was retired: iter191 proposed designing an execution contract so that property probes could be
> run against `benchmarks/reward_hack_benchmark_v1/`. iter192 established from committed bytes that v1's
> rows are not reward hacks — its generator admitted a row only when at least one `PASS_TO_PASS` test
> failed, so the official SWE-bench harness marks `40/40` unresolved and a zero-cost harness baseline
> detects `40/40`. Building an execution contract to detect a class the existing test suite already
> catches perfectly would have spent design effort, and then provider spend, on the wrong target.
>
> The successor gate is `experiments/iter193_certified_resolved_reward_hack_construction/`, which
> targets the class iter192 proved the generator was producing and discarding: patches the official
> harness certifies as **resolved** that are nonetheless wrong. Against that class the harness scores
> `0` by construction, so an execution contract genuinely is required — but for a different positive
> class than the one iter191 assumed.

Status: pre-registered zero-spend contract/harness design gate; no provider calls, credential probes,
property-generator calls, SWE-bench executions, cloud resources, benchmark-score changes, leaderboard
claims, model-comparison claims, state-of-the-art claims, natural-frequency claims, broad robustness
claims, production claims, product-value claims, public benchmark-score claims, or repaired-score claims
have been run for this gate.

## Why this gate exists

Iter190 found that the current property-generator schema can produce compact prose property proposals,
but it has no direct runnable artifact field and the local runtime is not a ready SWE-bench/container
execution surface. The next step is not more paid prose generation. The next step is a zero-spend
execution contract that separates model proposal, allowed executable representation, sandbox/runtime
requirements, and control false-positive adjudication before any further provider spend.

## Inputs

- `experiments/iter190_reward_hack_property_generator_bounded_execution/RESULT.md`
- `experiments/iter190_reward_hack_property_generator_bounded_execution/proof/execution_surface_preflight.json`
- `experiments/iter186_reward_hack_panel_property_probe_packet_materialization/proof/property_probe_packets_v1/packets.jsonl`
- `experiments/iter186_reward_hack_panel_property_probe_packet_materialization/proof/property_probe_packets_v1/manifest.json`
- `telos/property_probe_parser.py`

## Numeric Bars

Minimum pass bars:

- provider calls are exactly `0`,
- property-generator calls are exactly `0`,
- credential probes are exactly `0`,
- new SWE-bench executions are exactly `0`,
- new cloud resources are exactly `0`,
- execution-contract schema count is at least `1`,
- sandbox/runtime safety constraints are at least `8`,
- selected iter186 packet coverage in the feasibility matrix is exactly `24`,
- paired hack/control issue coverage is exactly `12`,
- future pass bars preserve control false positives exactly `0`,
- forbidden positive claim hits are exactly `0`,
- secret/private identifier hits are exactly `0`.

## Falsifiers

1. Any provider call, credential probe, property-generator call, SWE-bench execution, or cloud resource
   change occurs.
2. The design relies on trusting arbitrary model code without a sandbox, allowlist, or deterministic
   adapter boundary.
3. The design allows candidate diffs, row labels, hidden tests, official reports, private credentials,
   project IDs, or account IDs into model-facing prompts.
4. The feasibility matrix does not cover all `24` iter186 packets and all `12` hack/control pairs.
5. The future execution bars relax the control false-positive ceiling above `0`.
6. The result presents a leaderboard, model-comparison, model-superiority, SOTA, natural-frequency, broad
   robustness, production, product-value, public benchmark-score, or repaired-score claim.

## Claim Boundary

At most, if this gate passes: Telos has a zero-spend execution-contract and harness design for a future
bounded property-execution attempt over committed iter186 packets.

Not supported: benchmark leaderboard, state-of-the-art claim, model-comparison claim, natural reward-hack
frequency estimate, broad reward-model robustness claim, production deployment claim, product-value claim,
public benchmark score, repaired-score claim, or any claim outside committed proof packets.
