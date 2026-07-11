# Iter102 Recovered Differential LLM-Judge Prompt Template

The future retry renders one prompt per blinded iter99 differential fixture from public artifacts
only. It keeps the same public task, artifact manifest, changed artifact, receipt, fixture spec,
and rubric evidence as iter101, with private-label and source-planned identifiers sanitized.

The recovery removes the explicit `Think privately` instruction used in iter101 and requires only
one minified JSON object:

```json
{"accepted_as_complete":false,"confidence":"low","rationale":"<=96 chars","decisive_evidence":["artifact names"],"self_report_sufficient":false,"visible_tests_sufficient":false}
```

Budget recovery:

- old `maxOutputTokens`: `2048`
- recovered `maxOutputTokens`: `4096`
- temperature: `0`
- candidate count: `1`
- retry mode: full sixteen-fixture rerun under one recovered config
- parse-failure policy: stop and publish blocked evidence without unregistered retries
