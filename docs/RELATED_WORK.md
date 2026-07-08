# Related Work

This file is a target-survey input, not a claim of novelty. The first experiment decides which
benchmark family is strong enough for the first Telos result.

## Frontier Agent Direction

OpenAI has publicly described work on internal coding-agent monitoring and agentic work systems:

- OpenAI, "How we monitor internal coding agents for misalignment":
  https://openai.com/index/how-we-monitor-internal-coding-agents-misalignment/
- OpenAI, "How agents are transforming work":
  https://openai.com/index/how-agents-are-transforming-work/
- OpenAI, Agent Post-Training Research role:
  https://openai.com/careers/agent-post-training-research-san-francisco/

Anthropic has publicly described agent autonomy measurement and auditable scientific-agent
workflows:

- Anthropic, "Measuring agent autonomy":
  https://www.anthropic.com/research/measuring-agent-autonomy
- Anthropic, "Claude Science":
  https://www.anthropic.com/news/claude-science-ai-workbench

Google DeepMind has publicly described automated discovery systems where evaluators are central:

- Google DeepMind, AlphaEvolve:
  https://deepmind.google/blog/alphaevolve-impact/

## Candidate Benchmarks

SWE-bench and SWE-bench Verified are coding-agent anchors:

- SWE-bench leaderboard: https://www.swebench.com/
- SWE-bench Verified: https://www.swebench.com/verified.html
- OpenAI, "Introducing SWE-bench Verified":
  https://openai.com/index/introducing-swe-bench-verified/

METR RE-Bench is an AI R&D-agent anchor:

- METR blog: https://metr.org/blog/2024-11-22-evaluating-r-d-capabilities-of-llms/
- RE-Bench repository: https://github.com/METR/RE-Bench
- RE-Bench paper: https://arxiv.org/abs/2411.15114

tau-bench is a service-agent tool-use and policy-following anchor:

- tau-bench site: https://taubench.com/
- tau-bench repository: https://github.com/sierra-research/tau-bench
- tau-bench paper: https://arxiv.org/abs/2406.12045

AgentDojo is an adversarial tool-agent and prompt-injection anchor:

- AgentDojo site: https://agentdojo.spylab.ai/
- AgentDojo repository: https://github.com/ethz-spylab/agentdojo
- AgentDojo paper: https://arxiv.org/abs/2406.13352

## Positioning

The gap this repo targets is not ordinary benchmark success. It is completion proof: whether a
task's real objective is verified by independent artifacts and whether proxy success can be
separated from real completion.

The survey must decide whether an existing benchmark can carry that question directly or whether a
Telos overlay is required.
