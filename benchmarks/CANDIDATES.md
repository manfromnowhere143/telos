# Candidate Benchmarks

This registry is input to the frozen target survey. Scores are not filled here; they belong in
`experiments/iter00_target_survey/RESULT.md` after the survey runs.

## SWE-bench Verified / Coding Agents

Source:

- https://www.swebench.com/verified.html
- https://openai.com/index/introducing-swe-bench-verified/

Why it may fit:

- real GitHub issues,
- clear patch artifact,
- tests and diff scope can be inspected,
- strong fit for completion receipts.

Risk:

- leaderboard saturation may reduce signal,
- hidden test pass can still miss broader acceptance criteria.

## METR RE-Bench / AI R&D Agents

Source:

- https://metr.org/blog/2024-11-22-evaluating-r-d-capabilities-of-llms/
- https://github.com/METR/RE-Bench

Why it may fit:

- long-horizon research engineering tasks,
- direct relevance to automated AI R&D capability,
- human comparison data.

Risk:

- longer attempts are more expensive,
- evidence standard may require careful artifact normalization.

## tau-bench / Service Agents

Source:

- https://taubench.com/
- https://github.com/sierra-research/tau-bench

Why it may fit:

- tool-use agents with policies and database state,
- real-world interaction shape,
- final world-state checks are stronger than transcript grading.

Risk:

- simulated users introduce judge/model dependence,
- completion proof may need a policy-violation receipt layer.

## AgentDojo / Adversarial Tool Agents

Source:

- https://agentdojo.spylab.ai/
- https://github.com/ethz-spylab/agentdojo

Why it may fit:

- explicit utility/security tradeoff,
- adversarial prompt-injection pressure,
- useful for proxy-pass versus real-policy-compliance distinctions.

Risk:

- security focus may narrow the first Telos result,
- not all tasks produce code-like verification artifacts.

## Completion-Proof Overlay

Source:

- This repo's protocol: [`../protocol/proof.schema.json`](../protocol/proof.schema.json)

Why it may fit:

- directly tests the intended protocol,
- can wrap public coding, tool-use, or research tasks,
- exposes missing evidence as a measurable failure.

Risk:

- must avoid looking like a private benchmark,
- needs a public anchor and a reproducible task set.
