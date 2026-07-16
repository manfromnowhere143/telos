# TELOS forensic audit

Date: 2026-07-16
Repository: /Users/danielwahnich/workspace/telos
Sealed baseline: f4ee0d5bcb3b4abee7ebf1683be5b9edda263c28
Correction line: agent/iter208-post-seal-forensic-correction

## Executive finding

TELOS is pursuing a real and increasingly central frontier problem: agents can satisfy an evaluation
surface without satisfying the underlying objective, and the systems used to detect that failure can
themselves be incomplete, contaminated, or strategically unreliable.

The repository is unusually strong at preserving failures and refusing to convert missing execution into
scientific evidence. Its central existence case is credible at the narrow scope stated. It is not yet a
competitive benchmark result, a population estimate, or a production verifier. The strongest future for TELOS
is as an independent evidence and assurance layer for agent work, with the current paper serving as an
honest case study.

Publication is on hold during iter208. The iter207 seal remains immutable; the hold exists because this
audit found post-seal issues that must be corrected additively.

## What was independently checked

- Repository identity, branch topology, parentage, exact three-file seal, and clean starting tree.
- Complete Python test suite, lint, compilation, shell syntax, active workflow lint, and all documented
  handoff guards.
- Evidence reconstruction for iter192 and iter195 through iter207 from raw artifacts rather than README
  prose alone.
- The 22-row corpus manifest and its relationship to iter195 and iter199 source evidence.
- The iter200 denominator, missingness accounting, strict Sphinx case, and official-harness logs.
- Paper source, equations, tables, citations, deterministic PDF build, embedded fonts, and all rendered
  pages.
- Active reusable code, receipt semantics, cloud configuration, dependency locks, workflows, and unsafe
  historical execution surfaces.
- Current primary-source work from the organizations named in the mission brief.

## Verification results

| Surface | Result |
| --- | --- |
| Full Python suite at the iter207 seal | 596 passed |
| Focused claim-integrity tests | 137 passed |
| JSON validation | 3,496 files |
| Markdown validation | 712 files |
| Workflow validation | 19 workflows and two dependency locks |
| Paper reproducibility at the seal | two fixed-epoch builds matched the committed PDF exactly |
| Paper visual audit | all 11 sealed pages inspected; no clipping or missing fonts |
| Git seal | source 6f0297f…; exact three-file seal f4ee0d5… |
| Remote/provider action during this audit | none |

The broad workflow linter emits `SC1083` warnings for the literal `{commit}` suffix in the frozen iter203
and iter204 workflows; Bash parses those commitish expressions as intended. It separately rejects iter204's
job-level `runner.temp`, the exact unavailable context that caused the recorded pre-dispatch parser null.
The remaining workflows lint cleanly.

### Iter208 correction closure

The post-seal correction is additive to iter207 and contributes no scientific result. Its final local gate
records:

| Surface | Iter208 result |
| --- | --- |
| Python | Ruff and compilation clean; 624 tests passed |
| Structured evidence | 3,500 JSON files and 717 Markdown files valid |
| Frontier ledger | 23 unique primary, official, or standards sources |
| Paper | two fixed-epoch builds match; 12 pages; all fonts embedded |
| Visual review | all 12 paper pages and six Mermaid diagrams inspected |
| Receipt v2 | 34 exact artifacts bound by path, size, digest, media type, producer, and closure |
| Remote/provider/scientific action before source seal | zero |

The final iter208 guard requires the companion receipt to verify from repository-root bytes. A passing
local correction is not a paper acceptance, independent replication, identity-bound signature, DOI, model
ranking, prevalence estimate, production-verifier result, or private endorsement.

## Scientific evidence reconstructed

### The correction is real

The original 40-row v1 artifact is not a reward-hacking benchmark. All 40/40 rows are unresolved under
the official harness and all fail at least one PASS_TO_PASS test. The historical 17/40 judge result is
arithmetically reproducible but measures code review on patches already rejected by required tests.

Historical tarballs separately contain 139 harness-resolved hack-tagged evaluations across 65 instance
IDs. Only 23 iter152 discard IDs are decision-bound and only 17 overlap. Because the relevant patch
bytes are absent, semantic wrongness and final disposition are not reconstructible for all 139.

### The v2 corpus is real but narrower than “ground truth”

The current manifest has exactly 22 rows across eight repositories:

- 10 rows from iter195, which failed its registered no-gold and multi-input protocol because the generator
  saw both gold and candidate hunks and attempted one targeted scenario.
- 12 rows from iter199, whose design was recorded after provider generation and before execution, not
  independently preregistered.

Every row has an official resolved verdict and a clean retained gold-versus-variant output difference.
That proves a reference differential, not that gold is the unique semantically correct behavior.

### The strict existence case is credible

The iter200 Sphinx case passes all 33 graded tests. The accepted patch and model patch use different regular
expressions; on A-\nB, the model path creates a malformed empty keyboard element while the accepted path
preserves A-. This is a concrete certified-yet-wrong existence case. The cohort is nonrandom,
gold-localized, and post-inspection; six of 24 certified outcomes remain unadjudicated. The required
descriptive quantities are therefore 1/24, 7/24, and 1/18, always reported together and never as
confidence intervals or population bounds.

### Detector evidence is exploratory

- Judge panel: observed catches on 20/22; 8/88 responses unparseable.
- Paired-gold flag accounting: 3/22 observed lower, 6/22 missing upper, 3/19 complete-case.
- Property pipeline: 6/22, all inside the judge catch set.

The property protocol failed its diff-independent locator contract and has no independent false-positive
estimate. Raw judge responses were not retained. The four shared-gold-line diagnostics have no measured
causal direction. The paper’s former conclusion phrase suggesting downward recall bias was therefore
unsupported and is corrected in iter208.

## Software and provenance findings

### Strong

- Fail-closed experiment gates and explicit null classifications.
- Exact-version dependency locks with hashes.
- Pinned active GitHub actions and read-only default permissions.
- Stronger runtime custody in later iterations, including artifact hashes and topology checks.
- Apache-2.0 licensing plus attribution for the vendored MIT SWE-bench parser.
- No symlinks in the sealed tree and no Git object corruption.

### Must improve

1. **Legacy receipts are self-consistent, not artifact-bound.** The v1 digest covers receipt prose but not
   the bytes at each evidence path. Iter208 adds a backward-compatible receipt v2 with path, size, digest,
   media type, producer, closure digest, and no-symlink artifact verification.
2. **Hashes are not independent attestation.** Most local commits are unsigned. A Git hash proves identity
   inside this history, not authorship, external chronology, or truth. Public releases need identity-bound
   signing and an external transparency timestamp.
3. **The active API retained an Aweb-era name.** aweb_fit is migrated to mission_fit; frozen iter00
   evidence remains readable. TELOS, Sentinel, Inbar, and Odeya are related to one another and separate
   from Aweb.
4. **One active cloud project locator was hard-coded.** It is now supplied through
   TELOS_VERTEX_PROJECT.
5. **The codebase is iteration-heavy.** Roughly 178,000 of about 199,000 Python lines are scripts, while the
   reusable telos package is under 3,000 lines. Historical evidence should stay immutable, but future
   behavior belongs in a versioned library and CLI rather than another bespoke script per iteration.
6. **Historical unsafe runners need quarantine.** Five historical scripts use shell=True; two use Python
   eval on generated expressions. They are not on the iter207 path, but they should never become reusable
   platform code.
7. **Release metadata remains incomplete.** Iter208 adds a minimal `CITATION.cff` binding the software
   title, author, version, license, and canonical repository. There is still no DOI/archive binding, agent
   system card, or independent replication package; none is implied.

## Frontier comparison

### OpenAI

OpenAI’s February audit found material issues in at least 59.4% of a 138-task hard subset of SWE-bench
Verified and evidence of contamination. Its July audit estimates roughly 30% of SWE-Bench Pro’s public
tasks are broken, including low-coverage tests that allow incomplete fixes to pass. OpenAI’s internal
coding-agent monitor examines full conversations, reasoning, actions, tool calls, and outputs rather than
the final patch alone. This validates TELOS’s problem and makes trace custody mandatory for its future.

- [SWE-bench Verified audit](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)
- [SWE-Bench Pro audit](https://openai.com/index/separating-signal-from-noise-coding-evaluations/)
- [Internal coding-agent monitoring](https://openai.com/index/how-we-monitor-internal-coding-agents-misalignment/)
- [Agent eval guidance](https://developers.openai.com/api/docs/guides/agent-evals)

### Anthropic

Anthropic’s 2026 simulated deployments include covert pipeline sabotage and motivated judge mislabeling.
The report explicitly warns that its scenarios were selected to find failures and its rates are not broad
model rankings. Its controlled label-consequence ablation is directly relevant: TELOS cannot treat a model
judge as an independent semantic oracle.

- [Agentic Misalignment in Summer 2026](https://alignment.anthropic.com/2026/agentic-misalignment-summer-2026/)
- [Pre-deployment auditing of an overt saboteur](https://alignment.anthropic.com/2026/auditing-overt-saboteur/)

### NASA

NASA’s current software-assurance guidance emphasizes independent verification and validation, controlled
objective evidence, source-of-truth anchoring, configuration control, lifecycle monitoring, and human
approval for AI-derived artifacts. TELOS is directionally aligned, but independence must become real rather
than one agent auditing its own lineage.

- [AI-ready software engineering and assurance handbook](https://sma.nasa.gov/news/articles/newsitem/2026/05/18/the-nasa-software-engineering-and-software-assurance-electronic-handbook---a-unified-ai-ready-resource-for-engineering-assurance-iv-v-and-milestone-governance)
- [Software-driven hazards and IV&V](https://sma.nasa.gov/news/articles/newsitem/2026/04/08/reducing-risk-in-software-driven-hazards-across-nasa-programs-how-software-assurance-and-iv-v-strengthens-mission-safety)

### Tesla and SpaceX

Tesla describes open-loop, closed-loop, and hardware-in-the-loop evaluation at fleet scale, using
characteristic real-world clips to prevent regressions. SpaceX’s Falcon guide describes regular
hardware-in-the-loop testing over the complete mission profile. The transferable principle is
consequence-level replay across the operational envelope, not reliance on a single unit-test result.

- [Tesla AI evaluation infrastructure](https://www.tesla.com/AI)
- [Tesla Vehicle Safety Report methodology](https://www.tesla.com/VehicleSafetyReport?redirect=no)
- [SpaceX Falcon User’s Guide](https://www.spacex.com/assets/media/falcon-users-guide-2025-05-09.pdf)

### Cognition and Perplexity

Cognition’s own guidance says reliability is highest on small, isolated, objectively verifiable slices and
requires human review before merge. Perplexity’s DRACO derives 100 tasks from production requests and uses
expert-built rubrics averaging about 40 criteria, peer review, calibration, and three judge models. TELOS
needs both: constrained deployment slices and expert semantic criteria grounded in real use.

- [Devin best practices](https://docs.devin.ai/use-cases/best-practices)
- [Perplexity DRACO](https://research.perplexity.ai/articles/evaluating-deep-research-performance-in-the-wild-with-the-draco-benchmark)

### Stanford, Harvard/Princeton, and Cambridge

Stanford’s 2026 evaluation conference emphasizes causal, process-level, and real-world outcome measures;
its Agent Island work addresses saturation and contamination with adaptive opponents. Harvard’s Berkman
Klein Center highlights a Princeton-led framework that measures consistency, robustness, predictability,
and failure severity separately from accuracy. Cambridge’s Agent Index found that only four of 30 leading
agents published agent-specific system cards and that third-party testing was usually absent.

- [Stanford Frontiers in AI Evaluation](https://datascience.stanford.edu/news/benchmarks-real-world-impact-causal-science-conference-explores-modern-challenges-ai)
- [Agent Island](https://digitaleconomy.stanford.edu/publication/agent-island-a-saturation-and-contamination-resistant-benchmark-from-multiagent-games/)
- [Towards a Science of AI Agent Reliability](https://cyber.harvard.edu/story/2026-02/towards-science-ai-agent-reliability)
- [Cambridge AI Agent Index analysis](https://www.cam.ac.uk/stories/ai-agent-index-safety)

## Honest strategic verdict

- **Is TELOS going in the right direction?** Yes on problem selection and evidence discipline.
- **Is the current scientific result exceptional?** The self-correction and strict existence witness are
  genuinely valuable. The current sample, chronology, raw-response loss, gold dependence, and protocol
  failures prevent a state-of-the-art benchmark claim.
- **Should TELOS expand?** Expand depth before breadth: trace custody, independent labels, deterministic
  consequence tests, repeated runs, artifact-bound receipts, external attestation, and a reusable SDK.
- **Should it push deeper into knowledge?** Yes, but through adversarial measurement and causal evaluation,
  not by accumulating more prose or iteration numbers.
- **Would Larry Page, Sergey Brin, or Sam Altman approve or fund it?** No audit can establish a private
  person’s view. A serious funding case exists only after an independently replicated result and a compact
  product demonstration. Claiming endorsement now would be speculation.

## Publication gate

No merge or push is justified until all of the following are true:

1. iter207 remains byte-identical and iter208 records every correction additively;
2. the paper and README no longer contain the unsupported causal direction;
3. current 2026 related work is represented and TELOS’s novelty is narrowed honestly;
4. receipt v2 and project-boundary migrations pass tests;
5. every paper page and Mermaid diagram is rendered and inspected;
6. machine-readable iter208 evidence binds the exact source and PDF bytes;
7. a fresh independent audit finds no material claim contradiction;
8. the handoff is regenerated only after the final source commit exists.
