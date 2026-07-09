# Iteration 36 Review

The negative guard kept the real `iter35` self-coverage report passing and evaluated five generated
malformed report fixtures. The fixtures cover missing self-verification gates, stale artifact
hashes, hidden failed/null gates, changed-candidate/original-provider conflation, and forbidden
benchmark claims.

Fixture files are committed under proof artifacts and do not mutate the real self-coverage report
or source proof packets. This strengthens the self-coverage guard without adding behavior,
benchmark, production, or provider-model evidence.

No provider call, API call, GPU, cloud runner, production deployment, live-domain check, leaderboard
run, or SWE-bench run occurred in this gate.
