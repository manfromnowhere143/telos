# Iteration 14 Review

## Verdict

Pass.

The iter13 provider diff is reconstructable from committed artifacts, and it exposes one concrete
quality-bar change before further paid runs: unreferenced helper files must prevent a clean pass.

## Inputs Read

- `experiments/iter13_provider_model_pilot_retry_after_access_recovery/RESULT.md`
- `experiments/iter13_provider_model_pilot_retry_after_access_recovery/proof/run_summary.json`
- `experiments/iter13_provider_model_pilot_retry_after_access_recovery/proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708155545/players/p1/changes_r1.json`
- `experiments/iter13_provider_model_pilot_retry_after_access_recovery/proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708155545/players/p1/p1_r1.traj.json`
- `experiments/iter09_provider_model_pilot_smoke/proof/overlay/configs/test/telos_battlesnake_vertex_gemini_pilot.yaml`

No provider endpoint, model API, GPU, VM, or CodeClash rerun was used.

## Reconstruction

`changes_r1.json` records a `p1` full diff with these modified files:

- `README_agent.md`
- `main.py`
- `patch.py`

The `main.py` hunk implements the Step 1 boundary check by reading board width and height, then
marking `left`, `right`, `down`, and `up` unsafe when the snake head is already on the corresponding
edge. `p2` has an empty diff in the iter13 artifacts.

The prompt source is auditable, but the path has a presentation issue. Earlier hypotheses named
`configs/test/telos_battlesnake_vertex_gemini_pilot.yaml`; that file is not at repository root. The
committed source is the iter09 overlay config, and the same task text is present inside the iter13
trajectory. Future hypotheses should cite the committed overlay path when the root overlay is not
checked in.

## Quality Judgment

The `main.py` edit satisfies the local Step 1 intent for this smoke: avoid out-of-bounds moves on
the configured 11x11 board. This is a narrow task-quality judgment, not a game-performance claim.
It does not show that the bot is generally strong, that it handles self-collision, that it handles
opponents, or that the one-game score is meaningful.

`README_agent.md` is acceptable because the prompt explicitly asks the agent to document its
reasoning there.

`patch.py` is not acceptable for future clean-pass provider smokes. It is a root helper file used to
edit `main.py`, not task-facing game behavior or requested documentation. Keeping it in the
submitted diff pollutes the codebase and makes the receipt weaker. This did not invalidate iter13
because iter13 was a first provider execution smoke, but it becomes a quality-bar failure after this
review.

## Decision

Future provider-smoke receipts need an explicit diff-quality status:

- `clean`: changed files are task-facing or explicitly justified by the task.
- `quality_fail`: execution may have succeeded, but the diff contains unjustified helper, scratch,
  cache, generated, or secret-risk files.
- `blocked`: the committed artifacts are insufficient to judge quality without another model call or
  rerun.

For the next paid run, execution success plus `quality_fail` must not be reported as a clean pass.
