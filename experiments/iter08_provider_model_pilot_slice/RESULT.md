# Iteration 08 - Provider Model Pilot Slice Result

Status: `PASS`

## Result

The selected first paid-provider pilot is:

```text
vertex_gemini_3_1_pro_customtools_codeclash_micro_edit
```

The pilot selects Google Vertex AI with the documented model endpoint
`gemini-3.1-pro-preview-customtools` for a tiny CodeClash BattleSnake provider-backed
Mini-SWE-Agent smoke.

This result does not run the model. It freezes the next paid run.

## Why This Pilot

The deterministic loop now has evidence for:

- CodeClash raw artifact retention,
- Mini-SWE-Agent trajectory capture,
- agent stats capture,
- diff-scope capture,
- non-empty diff auditing,
- receipt validation,
- CI enforcement.

The next missing evidence is provider-backed behavior under a hard budget. The selected pilot keeps
the proven CodeClash path and uses the only paid-provider surface currently visible without exposing
secrets: local Google Cloud authentication with Vertex and Generative Language services enabled.

## Candidate Scorecard

| candidate | score | decision |
|---|---:|---|
| `vertex_gemini_3_1_pro_customtools_codeclash_micro_edit` | 30 | selected |
| `openai_gpt_5_5_codeclash_micro_edit` | 24 | defer until secret path exists |
| `codeclash_portkey_gemini_existing_config` | 21 | defer until Portkey key exists |
| `swebench_verified_single_task_provider_overlay` | 19 | defer until first CodeClash paid smoke |

Raw scorecard: [`proof/scorecard.json`](proof/scorecard.json)

## Frozen Pilot

- Provider: Google Vertex AI.
- Model endpoint: `gemini-3.1-pro-preview-customtools`.
- Base model: `gemini-3.1-pro-preview`.
- Task: one-round, one-simulation CodeClash BattleSnake smoke.
- Agent under test: `p1`, provider-backed Mini-SWE-Agent.
- Control: `p2`, dummy.
- Maximum model invocations: `8`.
- Maximum output tokens per call: `4096`.
- Wall-clock ceiling: `45` minutes.
- Dollar ceiling: `$25`.
- Stop rule: stop and publish blocked/null if cost is missing or exceeds the ceiling.

Selected pilot spec: [`proof/selected_pilot.json`](proof/selected_pilot.json)

## Credential And Infrastructure Preflight

Secret-safe preflight found:

- no local OpenAI, Anthropic, Gemini API-key, Portkey, or Llama API environment variable,
- no GitHub Actions repo secrets,
- local `gcloud` is installed,
- a Google Cloud project is configured without logging its identifier into proof,
- `aiplatform.googleapis.com` is enabled,
- `generativelanguage.googleapis.com` is enabled.

Preflight: [`proof/preflight.json`](proof/preflight.json)

## What This Does Not Claim

- No provider-model capability is claimed yet.
- No CodeClash leaderboard result is claimed.
- No SWE-bench result is claimed.
- No production/live-domain change occurred.
- No paid model call was made by this gate.

## Next Gate

Run `iter09_provider_model_pilot_smoke` only under the frozen budget and evidence bars. If the
zero-spend preflight or provider-backed CodeClash config fails, publish the blocked/null result with
raw evidence instead of widening scope.

## Evidence

- Selected pilot: [`proof/selected_pilot.json`](proof/selected_pilot.json)
- Candidate scorecard: [`proof/scorecard.json`](proof/scorecard.json)
- Credential preflight: [`proof/preflight.json`](proof/preflight.json)
- Sources: [`proof/sources.md`](proof/sources.md)
- Review: [`proof/review.md`](proof/review.md)
- Learning record: [`proof/learning_record.json`](proof/learning_record.json)
