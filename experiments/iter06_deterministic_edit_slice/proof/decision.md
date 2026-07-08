# Iteration 06 Decision

Selected:

```text
codeclash_overlay_battlesnake_python_marker_edit_slice
```

## Rationale

`iter05` proved that Telos can capture Mini-SWE-Agent trajectory and stats for deterministic submit.
The next missing evidence type is a real non-empty diff. The selected slice keeps the same public
CodeClash BattleSnake path and changes only the deterministic model output:

1. append a marker comment to `codeclash/arenas/battlesnake/battlesnake.py`,
2. submit.

That should produce a non-empty `p1` change record while keeping provider cost at zero.

## Why This Is Better Than A Local Fixture

A local fixture would be cheaper to run, but it would move away from the CodeClash agent path just
after that path became auditable. The overlay approach keeps the public harness, the Docker
environment, the Mini-SWE-Agent trajectory, and CodeClash diff-scope records.

## Why Not Paid Models Yet

Paid models are authorized by the operator, but this gate does not need them. A provider-model run
would be premature until the receipt loop proves that non-empty diffs are captured and audited for
a deterministic agent.

## Next Gate

Run `iter07_deterministic_edit_smoke`:

- apply the overlay into the pinned CodeClash checkout,
- run the selected config,
- verify `p1` changed `codeclash/arenas/battlesnake/battlesnake.py`,
- preserve raw artifacts,
- publish a Telos receipt or a null result.
