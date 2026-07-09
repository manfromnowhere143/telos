# Iteration 65 Result - Receipt Schema Prompt Alignment

Status: `PASS`.

`iter65` diagnosed the `iter64` Telos-row receipt failure locally and produced a recovered
receipt-enforced prompt overlay. The iter64 receipt candidate is classified as
`schema_incomplete` because it omitted required Telos proof fields:
`agent_id, benchmark_id, evidence, receipt_id, sha256, stated_goal, status, task_id`.

Evidence:

- provider API calls: `0`
- provider spend: `$0.00`
- GPU used: `false`
- cloud runner started: `false`
- Sentinel-named resources modified: `false`
- recovered prompt required fields present: `true`
- recovered prompt digest rule present: `true`
- local valid fixture passed: `true`
- local malformed fixture failed: `true`
- redaction scan passed: `true`

Primary artifacts:

- `proof/receipt_failure_diagnosis.json`
- `proof/recovered_overlay/configs/mini/telos_vertex_gemini_receipt_enforced_agent.yaml`
- `proof/recovered_overlay/receipt_template.json`
- `proof/fixture_validation_report.json`
- `proof/receipt_schema_alignment_report.json`
- `proof/valid/receipt_receipt_schema_prompt_alignment.json`

It is not a benchmark result, SWE-bench result, leaderboard result, production/live-domain result,
model-superiority result, or state-of-the-art result. It only authorizes the claim that the local
Telos receipt prompt and fixtures now align with the committed proof validator before a future
pre-registered paid retry.
