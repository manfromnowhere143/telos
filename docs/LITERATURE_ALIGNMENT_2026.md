# Literature Alignment Sweep - July 13, 2026

> **DATED HISTORICAL MEMO.** This sweep predates the iter192 foundation correction and the iter197/iter201
> methodology correction. Its v1 labels and proposed next gate are not current claims or instructions.
> Use the root `README.md`, `CONTINUITY.md`, and `paper/telos.tex` for the standing evidence boundary; this
> file remains a source-traceable record of what informed the iter191-era plan.

Purpose: check whether Telos is addressing live frontier problems, identify where the evidence is strong
or weak, and feed the next reward-hack evaluator gate without inflating claims.

## Bottom Line

Telos is aligned with a real 2026 frontier problem: agent evaluations can be gamed, reward hacking is now
studied directly in language-agent settings, and software-agent benchmarks need stronger validity checks
than a final scalar score. The current Telos evidence is strongest where it uses execution, receipts,
hashes, controls, and null publication. Iter169-190 moved the project from a single-model judge to an
adjudicated three-provider panel, then to a source-linked next-step design, then to a frozen
property-probe subset, then to a Sentinel-style mission data/process audit, and finally to a null
pre-spend property-generator execution-surface gate: unrepaired iter179 `majority_catch` remains the
primary public metric (`17/40` hack rows and `0/40` controls), while the next frontier work is a
zero-spend execution-contract/harness design before any more property-generator spend.

This memo is not a benchmark result, product claim, SOTA claim, model-comparison result, or literature
review exhaustiveness claim.

## Sources Read

Primary frontier/evaluation sources:

- OpenAI, "A shared playbook for trustworthy third party evaluations":
  https://openai.com/index/trustworthy-third-party-evaluations-foundations/
- OpenAI API docs, "Evaluation best practices":
  https://developers.openai.com/api/docs/guides/evaluation-best-practices
- OpenAI API docs, "Evaluate agent workflows":
  https://developers.openai.com/api/docs/guides/agent-evals
- OpenAI, "Findings from a pilot Anthropic-OpenAI alignment evaluation exercise":
  https://openai.com/index/openai-anthropic-safety-evaluation/
- OpenAI, "Introducing SWE-bench Verified":
  https://openai.com/index/introducing-swe-bench-verified/
- Anthropic, "From shortcuts to sabotage: natural emergent misalignment from reward hacking":
  https://www.anthropic.com/research/emergent-misalignment-reward-hacking
- Anthropic Alignment Science, "Teaching Claude Why":
  https://alignment.anthropic.com/2026/teaching-claude-why/
- Google DeepMind, "Specification gaming: the flip side of AI ingenuity":
  https://deepmind.google/blog/specification-gaming-the-flip-side-of-ai-ingenuity/
- Google DeepMind, "Strengthening our Frontier Safety Framework":
  https://deepmind.google/blog/strengthening-our-frontier-safety-framework/
- Google AI for Developers, "Structured outputs":
  https://ai.google.dev/gemini-api/docs/structured-output
- NIST CAISI, "AI models can cheat on evaluations?":
  https://www.nist.gov/caisi/cheating-ai-agent-evaluations/1-background-ai-models-can-cheat-evaluations

Academic and benchmark sources:

- Stanford CRFM, HELM:
  https://crfm.stanford.edu/helm/
- Stanford CRFM, "Reliable and Efficient Amortized Model-Based Evaluation":
  https://crfm.stanford.edu/2025/06/04/reliable-and-efficient-evaluation.html
- MIT AI Risk Initiative:
  https://airisk.mit.edu/
- RewardHackingAgents:
  https://arxiv.org/abs/2603.11337
- Reward Hacking Benchmark:
  https://arxiv.org/abs/2605.02964
- Reward Hacking in Language Model Agents:
  https://arxiv.org/abs/2606.15385
- Hack-Verifiable Environments:
  https://arxiv.org/abs/2605.20744
- SWE-bench:
  https://arxiv.org/abs/2310.06770
- Does SWE-Bench-Verified Test Agent Ability or Model Memory?:
  https://arxiv.org/html/2512.10218v1
- SWE-Bench Pro:
  https://arxiv.org/abs/2509.16941
- ToolEmu:
  https://arxiv.org/abs/2309.15817
- WebArena:
  https://arxiv.org/abs/2307.13854
- A Survey on LLM-as-a-Judge:
  https://arxiv.org/abs/2411.15594
- Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena:
  https://arxiv.org/abs/2306.05685

Adjacent institutional signals:

- Columbia CS Research Fair Spring 2026, agent benchmark and GUI testing projects:
  https://www.cs.columbia.edu/research-fair-spring-2026/
- Harvard Teamcore, "Reward Shaping for (Inference-Time) Alignment":
  https://teamcore.seas.harvard.edu/files/2026/05/6632_Reward_Shaping_for_Infere.pdf

## Implications For Telos

1. Harness and validity checks are part of the result.

   The OpenAI third-party-eval playbook emphasizes the tested system, harness, elicitation method, budget,
   artifacts, and validity checks. Telos already does this with pre-registration, raw prompts/outputs,
   receipts, cost guards, and null publication. Iter169 should make panel harness details first-class:
   model binding, structured-output mode, prompt payload, retry policy, aggregation rule, and score
   exclusion policy.

2. Reward hacking in agents is no longer a niche framing.

   2026 arXiv work directly benchmarks reward hacking in tool-use agents, ML-engineering agents, text
   safety-gridworld agents, and hack-verifiable environments. Telos' `reward_hack_benchmark_v1` is in the
   same problem family but remains narrower: code-review/software-agent completion verification, not a
   broad natural-frequency estimate.

3. Execution-backed evidence is still the strongest Telos differentiator.

   NIST CAISI frames cheating as a measurement-validity problem in agent evaluations. OpenAI's SWE-bench
   Verified post highlights the difficulty of assessing generated code. Telos' iter109-152 arc is valuable
   because it proves that static detectors and model judges can both miss execution-verified reward hacks,
   then shows held-out/property execution can catch and repair some of them.

4. LLM judges need controls and meta-evaluation.

   LLM-as-judge literature supports using strong judges as scalable evaluators, but also documents
   reliability and bias concerns. Iter167/168 adds project-specific evidence: stricter wording for the same
   judge did not improve recall, and invalids were output-contract failures. Iter169 should design a panel,
   not another same-model prompt tweak.

5. Structured output is not optional for paid evaluator runs.

   Google Gemini structured-output docs now support JSON-schema-constrained output. Iter168 found that all
   invalid iter167 rows were markdown-fenced JSON; diagnostic stripping would improve formatting but only
   move recall from `3/40` to `4/40`. Future paid gates should use provider-native structured output where
   available, but treat it as plumbing hygiene, not a recall solution.

6. Benchmark contamination and saturation must stay visible.

   SWE-bench memory/leakage and SWE-Bench Pro discussions reinforce Telos' no-leaderboard posture. Telos
   should keep separating artifact validity, recall/specificity metrics, and broad benchmark claims. It
   should not call `reward_hack_benchmark_v1` a leaderboard until controls, model families, leakage checks,
   and external-review packaging are stronger.

7. Product value is auditability, not a magic detector.

   For frontier teams, the value is a receipt-bearing verification layer: evidence hashes, model-output
   ledgers, controls, structured decisions, held-out execution, and clear escalation to expensive checks.
   This is useful for AI-agent platforms, coding-agent vendors, eval teams, safety teams, and regulated
   workflow owners that need to prove the agent completed the intended objective rather than the proxy.

## Next Gate Impact

The literature now supports the iter184 recommendation, iter185 converted that recommendation into a
concrete packet-materialization gate, iter186 materialized the packets, iter187 validated the
schema/parser and prompt contract before paid calls, iter188 designed the evidence/data-process audit,
iter189 executed it, and iter190 showed the current generator contract is not yet executable evidence:

- next gate: `iter191_reward_hack_property_execution_contract_design`;
- no further provider calls until the execution contract/harness is designed;
- do not spend on prose-only property generation before it can produce honest local/container execution
  evidence;
- preserve the iter185/iter186 leakage policy: no gold patches, hidden test names, official expected
  outputs, labels, row ids, candidate diffs, target tests, or official report fields in generated prompts;
- require native structured output or a preflighted equivalent for any future paid generator/judge call;
- freeze future call, spend, execution, false-positive, and nondecision bars before any provider call;
- keep execution-backed adjudication as the final layer for uncertain high-value rows.
