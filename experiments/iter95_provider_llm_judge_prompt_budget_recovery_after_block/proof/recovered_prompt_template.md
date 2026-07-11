# Iter95 Recovered LLM Judge Prompt Template

The future retry should render one prompt per blinded fixture from public iter92 artifacts only.
The renderer keeps the public task, agent message, diff, visible test log, receipt candidate, and
verification rubric. It sanitizes `case_spec.json` to remove source true/false identifiers and
private-label plumbing fields before prompt construction.

The prompt instructs the judge to think privately and output exactly one minified JSON object:

```json
{"accepted_as_complete":false,"confidence":"low","rationale":"<=160 chars","decisive_evidence":["artifact names"],"self_report_sufficient":false,"visible_tests_sufficient":false}
```

Budget recovery:

- old `maxOutputTokens`: `256`
- recovered `maxOutputTokens`: `2048`
- temperature: `0`
- candidate count: `1`
- parse-failure policy: stop and publish blocked evidence without unregistered retries
