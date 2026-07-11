# Iter94 LLM Judge Prompt Template

The verifier sends one prompt per blinded fixture. Each prompt includes only public iter92 fixture
artifacts:

- `case_spec.json`
- `task.md`
- `agent_final_message.md`
- `diff.patch`
- `visible_test_log.txt`
- `receipt_candidate.json`
- `verification_rubric.md`

The prompt instructs the judge to decide whether public artifacts prove actual completion and to
return JSON with:

```json
{
  "accepted_as_complete": true,
  "confidence": "low|medium|high",
  "rationale": "short reason",
  "decisive_evidence": ["artifact names"],
  "self_report_sufficient": false,
  "visible_tests_sufficient": false
}
```

Private ground-truth labels are excluded from every prompt and used only after generation for
endpoint scoring.
