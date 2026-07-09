# Iteration 23 Review

The tail-semantics harness loaded the reconstructed `iter21` bot and ran local cases under the
explicit assumption `tail_remains_occupied`. The submitted bot excludes tails from both self and
opponent body checks, so the occupied-tail risk cases leave the forbidden tail move in the observed
safe-move list.

The non-tail controls still pass. The failure is narrow: it does not invalidate the `iter21`
non-tail body collision result, but it does falsify any broader claim that the submitted bot avoids
all occupied tail cells.

No provider call, API call, GPU, cloud runner, production deployment, live-domain check, leaderboard
run, or SWE-bench run occurred in this gate.
