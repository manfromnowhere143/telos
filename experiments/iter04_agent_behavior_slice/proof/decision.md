# Iteration 04 Decision

Selected:

```text
configs/test/battlesnake_pvp_test.yaml
```

## Rationale

The slice introduces real agent machinery without provider spend:

- `p1` uses CodeClash's Mini-SWE-Agent integration.
- `p1` uses `minisweagent.models.test_models.DeterministicModel`.
- The deterministic model emits the submit command through the same agent loop a model-backed agent
  would use.
- `p2` remains a dummy opponent.
- The run is one round and one simulation.

This gives Telos the next missing evidence type: trajectory and agent stats.

## Why Not Ladder Yet

The ladder smoke is valuable, but it adds branch initialization, ladder state, and more simulations
before the simpler Mini-SWE-Agent PvP receipt is proven.

## Why Not A Custom Deterministic Edit Agent Yet

A custom deterministic edit agent would produce non-empty diffs, but it would move away from public
CodeClash configs too early. The better order is:

1. public Mini-SWE-Agent deterministic submit,
2. public or minimal deterministic edit,
3. paid model only after receipt quality survives those gates.

## First-Run Falsifier

The next gate fails if the selected run does not produce:

- Mini-SWE-Agent trajectory for `p1`,
- agent stats with zero provider cost and at least one deterministic model invocation,
- CodeClash metadata and round result,
- diff-scope records for both players,
- a valid Telos receipt.
