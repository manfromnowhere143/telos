# Iteration 15 Review

The provider run itself recovered after the Vertex location was made explicit as `global`. The preflight returned HTTP `200`, CodeClash exited `0`, `p1` submitted, and the provider trajectory records `5` model API calls with `$0.037882` reported cost.

The strict clean-pass bar failed. `p1` changed `README_agent.md` and `main.py`, but also left `patch.py` and `patch2.py` in the root workspace. Those helper files were not requested by the task and are not part of the final bot. Under the iter14 quality bar, this is a quality failure, not a clean pass.

The `main.py` edit added out-of-bounds and self-collision checks and passed the game submission validation in this smoke. That does not override the diff-hygiene failure, and the one-game score is not evidence of model superiority.

No leaderboard result, SWE-bench result, production/live-domain verification, or general model capability claim is made. The next gate should test whether an explicit workspace-hygiene control can produce the same provider-backed completion without helper-file residue.
