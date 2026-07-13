# Iteration 168 Result - Reward-Hack Skeptical Judge Null Adjudication

Status: `pass`.

## What this gate did

This zero-spend gate adjudicated the completed iter167 null. It made no provider calls, model
evaluations, SWE-bench executions, or cloud-resource changes, and it did not change iter167 metrics.

## Iter167 Null

| fact | value |
| --- | ---: |
| attempted provider calls | `80` |
| provider errors | `0` |
| prompt leakage hits | `0` |
| response secret hits | `0` |
| iter167 recall | `0.075` |
| iter167 specificity | `0.9` |
| iter167 hack nondecision rate | `0.125` |
| iter167 balanced detection | `0.4875` |

The null remains a null under the strict iter160 parser: invalid outputs are not true positives or true
negatives, and post-hoc repair is excluded from the score.

## Invalid-Output Taxonomy

| item | value |
| --- | ---: |
| total invalid outputs | `9` |
| hack invalid outputs | `5` |
| control invalid outputs | `4` |
| malformed JSON invalids | `9` |
| markdown-fenced JSON cause | `9` |

All invalid outputs were markdown-fenced JSON. This is an output-contract failure, not a provider block
or semantic refusal.

## Diagnostic-Only Counterfactual

| metric | iter167 strict score | fenced-JSON stripped diagnostic |
| --- | ---: | ---: |
| hack `reward_hack` verdicts | `3/40` | `4/40` |
| control `reward_hack` verdicts | `0/40` | `0/40` |
| recall | `0.075` | `0.1` |
| specificity | `0.9` | `1.0` |
| hack nondecision rate | `0.125` | `0.0` |
| balanced detection | `0.4875` | `0.55` |

Even if fenced JSON had been stripped before scoring, recall would be `4/40`, still below the
pre-registered iter167 recall bar. The format failure matters, but the main failure is semantic recall.

## Miss Pattern

- Parsed hack rows: `35`.
- Parsed hack rows called `reward_hack`: `3`.
- Parsed hack rows called `legitimate`: `32`.
- Static-survivor misses: `12`.

The miss pattern is high-confidence `legitimate` judgments on execution-verified both-miss hack rows,
often where the diff looks like a plausible normal-path source edit rather than a visible test edit.

## Recommendation

Recommended next intervention: `independent_judge_panel_design`.

The next move should be a zero-spend independent judge-panel design with strict structured output,
predeclared aggregation rules, paired controls, and the same specificity floor. Structured output is
mandatory hygiene for future paid calls, but the diagnostic repair alone would not solve recall.

Failures:

- none

## Claim Boundary

Supported if status is pass: Telos has a zero-spend adjudication of the iter167 null and a bounded
next-intervention recommendation grounded in the observed recall, specificity, invalid-output, and miss
patterns.

Not supported: any changed iter167 score, leaderboard ranking, model superiority, state-of-the-art claim,
natural reward-hacking frequency estimate, broad reward-model robustness claim, or claim about model
bindings not run in iter167.

## Evidence

- `proof/invalid_output_taxonomy.json`
- `proof/fenced_json_counterfactual.json`
- `proof/miss_pattern_summary.json`
- `proof/next_intervention_recommendation.json`
- `proof/audit_report.json`
- `proof/endpoint_results.json`
- `proof/run_summary.json`
- `proof/valid/receipt_reward_hack_skeptical_judge_null_adjudication.json`
