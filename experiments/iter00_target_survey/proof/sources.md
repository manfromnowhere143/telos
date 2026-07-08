# Sources

Captured 2026-07-08. These are survey sources, not benchmark results produced by Telos.

## Frontier Agent Evidence

- OpenAI, internal coding-agent monitoring:
  https://openai.com/index/how-we-monitor-internal-coding-agents-misalignment/
  - Relevance: OpenAI describes monitoring real internal coding agents in tool-rich workflows,
    including actions inconsistent with user intent and future synchronous blocking controls.
- Anthropic, measuring agent autonomy:
  https://www.anthropic.com/research/measuring-agent-autonomy
  - Relevance: Anthropic reports Claude Code autonomy, clarification, and human interruption
    behavior over complex tasks.
- Anthropic, Claude Science:
  https://www.anthropic.com/news/claude-science-ai-workbench
  - Relevance: Anthropic describes specialist agents composing evidence state across scientific
    sources and reusable tools.
- Google DeepMind, AlphaEvolve:
  https://deepmind.google/blog/alphaevolve-impact/
  - Relevance: automated discovery depends on executable evaluators and verifiers, not only
    final prose.

## Candidate Benchmark Evidence

- SWE-bench Verified:
  https://www.swebench.com/verified.html
  - Human-validated 500-instance subset for coding agents and language models.
- SWE-bench leaderboards:
  https://www.swebench.com/
  - Public `% Resolved` metric, 500 Verified instances, and 2025 CodeClash news link.
- CodeClash:
  https://codeclash.ai/
  - Goal-oriented software engineering benchmark with open trajectories, multi-round codebase
    evolution, arenas, and leaderboard ELO.
- METR RE-Bench blog:
  https://metr.org/blog/2024-11-22-evaluating-r-d-capabilities-of-llms/
  - Seven AI R&D research-engineering environments, human expert comparison, long time budgets.
- METR RE-Bench repository:
  https://github.com/METR/RE-Bench
  - Public task suite, METR task standard, task family scores, and setup material.
- tau-bench repository:
  https://github.com/sierra-research/tau-bench
  - Public tool-agent-user benchmark, but the repository now warns that its tasks are outdated.
- tau2/tau3-bench repository and release notes:
  https://github.com/sierra-research/tau2-bench
  https://github.com/sierra-research/tau2-bench/releases
  - Current line adds voice, knowledge, and new domains; setup is heavier.
- AgentDojo:
  https://agentdojo.spylab.ai/
  https://github.com/ethz-spylab/agentdojo
  - Public adversarial tool-agent benchmark and runnable package.
