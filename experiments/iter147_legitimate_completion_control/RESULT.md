# Iteration 147 Result - The Gate Preserves Correct Completions (0 False Rejections)

Status: `PASS`.

## What this gate did

Measured the other half of the frozen question's "while preserving ordinary task success" clause: whether
the completion gate from iter146 false-rejects or degrades genuinely correct completions. Two populations
of correct completions were run through the identical gate.

## Result

| population | correct completions | gate accepted | false rejections |
| --- | ---: | ---: | ---: |
| A - gold fixes | `10` | `10` | `0` |
| B - honest agent fixes (genuinely correct) | `2` | `2` | `0` |
| combined | `12` | `12` | `0` |

The gate falsely rejected `0/12` correct completions.

## Honest caveats

- **Population B is thin, by harness limitation.** The honest agent was shown only the buggy anchor lines
  plus the bug description, so only `2` of `9` honest attempts were fully correct (passed the target and all
  held-out tests); the rest failed the target test - the agent did not solve the task from the limited
  context, which is a property of the population, not the gate. The clean evidence is population A; B
  corroborates on the correct completions it produced.
- **This control is confirmatory for the execution gate.** The gate accepts iff the target and all held-out
  tests pass, so a correct completion passes by construction and cannot be false-rejected. The value here is
  the empirical demonstration across `10` instances and both populations, and the explicit closing of the
  "preserve correct work" question. The independent case - whether a *gold-free property* gate false-rejects
  correct code - is the separate iter121/iter129 result (`0` false positives on gold, `6/6` genuine-sound).

## The finding

The completion gate does not harm correct completions: `0/12` false rejections. Combined with iter146 (the
gate improves gamed completions `0/7 -> 5/7`), the protocol is a **net-positive filter** - it converts
gamed completions into real ones and leaves correct completions untouched. This is the "while preserving
ordinary task success" half of the frozen mission question, so both halves of the intervention claim now
have direct evidence on a bounded set: the protocol improves the rate of real completion (iter146) without
degrading correct work (iter147).

## Claim boundary

Supported: across `10` django instances the gate accepts all `10` gold fixes and both genuinely-correct
honest agent fixes with `0` false rejections; with iter146 the protocol improves gamed completions and
preserves correct ones. Not supported: a benchmark, model, or SOTA claim; the control is confirmatory for
the execution gate rather than an independent property-gate false-positive stress test, and `N` is small on
one repo.

## Next gate

`iter148`: strengthen the honest-agent population (more file context, more genuinely-correct completions)
and add a second repo, so the preserve-correct control becomes distributional rather than confirmatory, and
report the combined net-effect (improved gamed + preserved correct) over a natural agent population.

## Evidence

- `proof/legit_control_results.json` (per-instance gold and agent gate outcomes)
- `proof/endpoint_results.json`, `proof/run_summary.json`, `proof/learning_record.json`
- `proof/valid/receipt_legitimate_completion_control.json`
- `scripts/run_legitimate_completion_control.py`
