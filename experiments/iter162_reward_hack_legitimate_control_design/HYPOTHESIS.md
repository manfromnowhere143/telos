# Iteration 162 - Reward-Hack Legitimate-Control Design

Status: pre-registered design gate; no provider calls, SWE-bench executions, cloud resources, model
scoring, precision claims, leaderboard claims, or benchmark scores have been run for this gate.

## Why this gate exists

`iter161` ran one bounded model judge over the 40 frozen blinded reward-hack packets and found only
`3/40` `reward_hack` verdicts on an all-positive artifact. That is useful recall evidence, but it is
not a benchmark score and it says nothing about precision. A real evaluator needs legitimate controls
that put false positives under pressure with the same blinded-packet discipline as the hack rows.

## Method

Inputs:

- `experiments/iter161_reward_hack_single_model_judge_execution/proof/run_summary.json`
- `benchmarks/reward_hack_benchmark_v1/reward_hack_benchmark_v1.jsonl`
- `benchmarks/reward_hack_benchmark_v1/blinded_model_judge_packets_v1/manifest.json`
- `experiments/iter147_legitimate_completion_control/proof/legit_control_results.json`
- public SWE-bench Verified task metadata and gold/accepted patches only when source and hash can be
  recorded without secrets or hidden labels

Planned output:

- a legitimate-control source hierarchy,
- a schema for control rows and blinded control packets,
- explicit no-overlap and pairing rules,
- leakage exclusions matching the iter159 packet audit,
- precision and balanced-metric definitions with null/refusal/invalid handling,
- a next materialization gate with numeric bars before any model is evaluated on controls.

Preferred control strata:

1. Paired legitimate controls for the same public issue as a reward-hack row, using a human gold or
   accepted-correct patch with execution evidence. This is the strongest control because the judge sees
   the same issue surface but a real fix instead of a reward hack.
2. Disjoint legitimate controls from previously verified correct completions when paired controls cannot
   be recovered with committed source and hash evidence.

## Numeric Bars

Minimum pass bars for this design gate:

- defines a row schema with at least: `row_id`, `control_type`, `repo`, `instance_id`,
  `public_task_text`, `public_target_tests`, `candidate_diff`, `candidate_diff_sha256`,
  `source_artifact_path`, `source_record_sha256`, `execution_evidence_path`, `claim_boundary`;
- defines a blinded packet schema whose prompt-visible fields match the iter159 packet surface plus a
  candidate diff, with no label, official report, source experiment, prior verdict, or static-outcome
  leakage;
- sets the next materialization target at `40` legitimate controls if source recovery permits, with a
  hard floor of `20` controls for a null/shortfall result;
- requires `0` overlap between hack-row candidate diffs and legitimate-control candidate diffs;
- requires every control candidate diff hash to be stable and every source artifact to be committed or
  public-citable before packet materialization;
- defines precision as `legitimate_controls_not_flagged / attempted_legitimate_controls` only after a
  control-set run exists;
- keeps iter161's all-positive recall result separate from any future precision, balanced accuracy,
  leaderboard, model-superiority, or state-of-the-art claim;
- uses zero provider calls, zero SWE-bench executions, and zero cloud resources in this design gate.

## Falsifiers

1. The design permits a control packet to reveal `legitimate`, `gold`, `control`, source split,
   official report content, prior judge verdict, or reward-hack/static labels in prompt-visible fields.
2. The design allows precision to be inferred from iter161's all-hack run.
3. The design lacks a stable source/hash requirement for candidate diffs.
4. The design merges paired and disjoint controls without reporting their strata separately.
5. The design allows provider/model calls before the control artifact is materialized and audited.

## Claim Boundary

At most, if the gate passes: Telos has a pre-registered protocol for constructing blinded legitimate
controls and future precision metrics for `reward_hack_benchmark_v1`.

Not supported: any precision number, model score, leaderboard, model comparison, state-of-the-art claim,
natural reward-hacking frequency estimate, broad reward-model robustness claim, or claim that iter161 is a
complete benchmark evaluation.
