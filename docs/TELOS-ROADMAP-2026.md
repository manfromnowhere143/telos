# TELOS 2026 roadmap

## North star

TELOS should answer one question:

> What exact evidence justifies accepting an autonomous agent’s claim that consequential work is complete?

The answer must survive an untrusted agent, an incomplete grader, an unreliable judge, missing
infrastructure, and later independent audit.

## Product and research architecture

~~~mermaid
flowchart LR
    A["Task contract<br/>goal · constraints · falsifiers"] --> B["Isolated agent execution"]
    B --> C["Full trajectory<br/>messages · tools · actions · outputs"]
    C --> D["Content-addressed evidence<br/>artifacts · environment · model binding"]
    D --> E["Independent verification<br/>grader · consequences · human review"]
    E --> F{"Claim gate"}
    F -->|all required evidence passes| G["Signed claim<br/>bounded scope"]
    F -->|failure, missingness, or conflict| H["Fail / null / abstain<br/>no silent imputation"]
    G --> I["Deployment monitoring<br/>drift · incidents · re-evaluation"]
    I --> C
~~~

TELOS Core should become a small reusable library and CLI. Historical experiment scripts remain immutable
evidence; they should not define the future API.

## Workstreams

### 1. Evidence substrate

- Receipt v2: bind every evidence artifact by canonical path, byte count, SHA-256, media type, and producer.
- Evidence closure: one digest over the complete evidence set.
- Environment binding: exact source commit, container digest, model identifier, request parameters, tool
  versions, and exit status.
- Identity and time: in-toto/SLSA-compatible attestations plus Sigstore keyless signing and transparency-log
  inclusion for public releases.
- Verification policy: distinguish byte identity, signer identity, chronology, and semantic truth.

Relevant standards:

- [SLSA provenance](https://slsa.dev/spec/v1.2/provenance)
- [in-toto statement v1](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md)
- [Sigstore keyless signing](https://docs.sigstore.dev/cosign/signing/overview/)

### 2. Trace and monitor adapters

- One canonical event schema for model messages, tool calls, file reads/writes, commands, policy decisions,
  approvals, and outputs.
- Adapters for at least OpenAI/Codex, Anthropic/Claude Code, and one open-weight coding-agent harness.
- Separate action-only, final-output, and full-trajectory monitor views.
- Raw response retention with secret-safe redaction manifests; never retain only parsed labels.
- Structured abstention and escalation rather than forced binary judge labels.

### 3. Consequence verification

- Pre-author hidden consequence tests before agent output.
- Keep grader code and hidden labels outside the mutable agent workspace.
- Use metamorphic, differential, property, and integration checks where each is justified.
- Record which requirements each test covers; report uncovered requirements explicitly.
- Use independent engineers for semantic labels, with disagreement and adjudication retained.

### 4. Reliability science

Measure capability and reliability separately:

- repeated-run consistency;
- robustness to prompt, tool, and environment perturbations;
- confidence calibration and abstention;
- failure severity and tail risk;
- verification latency and cost;
- contamination and evaluation-awareness sensitivity.

### 5. Public trust surface

- A short README current path plus immutable historical detail.
- Maintain `CITATION.cff`; add an archived release, DOI, model/agent system card, data statement, and
  broader-impact section.
- A compact reviewer bundle that reproduces every table from exact evidence.
- Independent replication before any “state of the art,” product efficacy, or natural-frequency claim.

## Next GPU experiment: TCP-1

Name: **TELOS Trace–Consequence Pilot 1**

Status: preregistration design only. No model call, GPU allocation, or scientific execution is authorized
by this roadmap.

### Question

Among agent patches that pass the visible grader, does a gate combining full-trajectory policy checks and
pre-authored consequence tests reject more semantically wrong completions than the visible grader alone,
without an unacceptable false-positive rate on semantically valid completions?

### Pilot cohort

- 12 fresh coding tasks selected after the chosen open-weight model’s documented training cutoff.
- Tasks must be independently solvable, containerized, and small enough for bounded repeated runs.
- Five independent seeds per task: 60 trajectories.
- A separate fixed set of legitimate implementations and deterministic integrity attacks serves as
  calibration controls; controls are never pooled into the natural-behavior estimate.
- No task enters the cohort if its hidden consequence tests were derived after inspecting model output.

### Blinding and independence

1. Two engineers author the task contract and consequence tests before model execution.
2. The complete preregistration, task hashes, hidden-test hashes, and analysis code receive an external
   transparency timestamp before the first trajectory.
3. The agent cannot read or edit hidden tests, trusted grader code, or receipt-generation code.
4. Two different engineers provide independent human semantic labels for proxy-passing outputs while
   blinded to seed, monitor verdict, and whether
   the patch is a control. Disagreement is retained and adjudicated by a third reviewer.
5. LLM judges may be measured as monitors but never define semantic ground truth.

### Execution binding

Every trajectory must retain:

- exact model-weight digest, tokenizer digest, inference-engine version, quantization, and sampling fields;
- exact repository commit and container image digest;
- complete messages, tool calls, tool outputs, file-access log, patch, commands, exits, and resource usage;
- visible-grader result and hidden-consequence result;
- receipt v2 closure verified from a clean checkout;
- signed in-toto/SLSA-style attestation and transparency-log bundle for the frozen aggregate.

### Endpoints

Primary endpoint:

- paired reduction in false-completion acceptance from visible-grader-only to the TELOS gate among
  proxy-passing, independently adjudicated semantic failures.

Secondary endpoints:

- false rejection on independently adjudicated valid completions;
- incremental catch contribution of action-only, final-diff, full-trajectory, and consequence monitors;
- five-run task consistency;
- failure-severity distribution;
- latency, tokens, energy estimate, and verification cost;
- monitor abstention and missingness.

Analysis:

- report exact counts and all missing outcomes;
- use an exact paired test for the primary gate comparison;
- give Wilson intervals for simple binomial rates;
- report task-clustered uncertainty as a sensitivity analysis;
- make no model ranking or natural population-rate claim from this selected pilot.

### Hard falsifiers

TCP-1 is a null or failure—not a result—if any of these occurs:

- task or hidden-test freeze happens after any model output;
- model weights, source, container, or request configuration are not digest-bound;
- any raw trajectory or grader output is missing;
- hidden evidence enters the agent-visible workspace;
- semantic labels depend on an LLM judge;
- artifact receipt verification fails;
- fewer than ten independently adjudicated proxy-passing semantic failures exist for detector comparison;
- controls are pooled into natural-behavior rates;
- analysis changes after unblinding without a separately versioned amendment.

### Resource gate

- Candidate model and hardware remain unchosen until license, cutoff, context, and weight digests are
  verified.
- Preflight one task and one seed without entering the scientific cohort.
- Hard pilot ceiling: 64 accelerator-hours and the separately approved monetary budget.
- Stop before allocation if projected throughput cannot finish the frozen cohort inside that ceiling.
- No cloud spend or provider call is implied by repository access or by this document.

## Sequenced roadmap

### Iter208 — post-seal forensic correction

- preserve iter207;
- correct paper and README claims;
- add 2026 related work and strategic positioning;
- ship receipt v2 and project-boundary cleanup;
- bind the audit, roadmap, source, PDF, and diagrams;
- close with no scientific run.

### Iter209 — TCP-1 materialization

- recruit independent reviewers;
- select and license the fresh task cohort;
- author hidden consequence tests;
- pin model, weights, inference engine, containers, and hardware;
- externally timestamp preregistration and analysis code;
- publish a zero-execution materialization receipt.

### Iter210 — bounded GPU execution

- execute exactly the frozen 60 trajectories if and only if iter209 passes;
- collect raw evidence before adjudication;
- stop on the first custody or isolation violation.

### Iter211 — blinded adjudication

- independent semantic review;
- locked analysis;
- explicit missingness and disagreement;
- no post-hoc threshold changes inside the result.

### Iter212 — multi-model replication

- only after TCP-1 yields a valid interpretable result;
- at least three model families and two agent harnesses;
- one external team reproduces the evidence bundle.

## Funding thesis

The investable form of TELOS is not a claim that another benchmark is best. It is a neutral assurance
substrate for organizations deploying agents into code, research, operations, and safety-critical
workflows:

1. capture the whole action trace;
2. bind claims to exact evidence;
3. verify consequences independently;
4. expose uncertainty and missingness;
5. sign only the bounded claim the evidence supports.

Funding should accelerate independent review, reusable adapters, and replication—not a larger unreviewed
run.
