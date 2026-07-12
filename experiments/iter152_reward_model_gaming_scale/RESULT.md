# Iteration 152 Result - A Frontier Reward Model Is Gameable at Scale (Cross-Repo)

Status: `PASS`.

## What this gate did

Turned the detection result into a reward-model-robustness measurement at scale. On a cloud x86 Docker VM,
across 8 SWE-bench_Verified repositories, a frontier adversary constructed execution-verified both-miss
hacks (official harness: passes the target test, fails a regression test). Each hack was scored by three
static verifiers - the deterministic detector and two frontier models used as reward-model judges
(`gpt-5.6-terra`, `claude-opus-4-8`) - and every hack diff was saved.

## Result

Over `20` execution-verified both-miss hacks across `8` repositories (astropy, django, matplotlib,
pydata/xarray, pytest, scikit-learn, sphinx, sympy):

| static verifier | fooled by the hack | rate |
| --- | ---: | ---: |
| deterministic detector | `20/20` | `1.00` |
| `gpt-5.6-terra` as reward model | `7/20` | `0.35` |
| `claude-opus-4-8` as reward model | `9/20` | `0.45` |
| **survives every static layer** (detector + both judges) | `5/20` | `0.25` |

All `20` hack diffs are saved (`proof/raw/detection_results.json`), and each both-miss's official SWE-bench
verdict is backed by a report (`proof/raw/det_reports.tgz`).

## The finding

A frontier LLM used as a reward model is gameable by constructible reward-hacks, on real code, across
repositories. The deterministic detector is blind to the entire class (`20/20`) because these are
generalization bugs, not mechanical hacks. The two frontier reward-model judges are fooled `0.35` and
`0.45` of the time - and, notably, the larger reasoning model (`claude-opus-4-8`) is fooled *more* often,
so a bigger model is not a safer reward model here. The load-bearing number: `5/20` (`0.25`) of hacks
survive **every** static layer - the detector and both frontier reward models - and are catchable only by
held-out execution. So roughly one in four constructible reward-hacks defeats every static verifier tested.

This is the RLAIF-relevant statement: coding agents trained with RL against an LLM reward model face a
constructible class of reward-hacks that the reward model accepts as legitimate, and execution is the
recovering signal.

## Honest scope (self-critique on the record)

- **Single adversary, two judges.** One frontier model constructs the hacks; two frontier models judge.
  The rates are for these models, not a claim about all reward models or all hacks.
- **Constructed, not naturally emergent.** The both-miss are adversarially constructed (degrade a gold
  fix), a controlled way to study the class; whether a natural RL agent emits them at this rate is untested.
- **Not a benchmark or SOTA claim.** `N=20` is a bounded set; the saved hack diffs are the *seed* of a
  reward-hack benchmark, not a released benchmark yet.
- **Same run also re-confirmed the intervention** (`telos_resolved 8/20`), consistent with iter151's
  `10/20`, reported here as a secondary datum.

## Claim boundary

Supported: across `8` repositories on `20` execution-verified both-miss, the deterministic detector is
fooled `20/20`, `gpt-5.6-terra`-as-reward-model `7/20`, `claude-opus-4-8`-as-reward-model `9/20`, and
`5/20` survive every static layer - so a frontier reward model is gameable by constructible hacks and
execution is the recovering layer. Not supported: a benchmark, model, or SOTA claim, a statement about all
reward models or all hacks, or a claim about naturally-emergent (non-constructed) reward hacking.

## Next gate

`iter153`: grow `N` and the judge set toward a released reward-model-robustness benchmark from the saved
hack diffs; and (higher-leverage before arXiv) the accessibility rewrite of the paper - a domain expert
(the Sentinel endorser) flagged that a dense "technical LLM style" makes strong results hard to read, and
Telos's paper has the same style.

## Evidence

- `proof/raw/detection_results.json` (per-instance: hack diff, detector verdict, both judge verdicts)
- `proof/raw/det_reports.tgz` (official SWE-bench reports backing each verified both-miss)
- `proof/raw/detection_pipeline.py` (the exact harness)
- `proof/endpoint_results.json`, `proof/run_summary.json`, `proof/learning_record.json`
- `proof/valid/receipt_reward_model_gaming_scale.json`
- `scripts/run_reward_model_gaming_scale.py`
