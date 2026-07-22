# Telos remote-CI recovery audit — 2026-07-22

> **DATED ANALYSIS CONTEXT — NOT EXECUTION AUTHORITY.** This audit is the exact
> `current_audit` named by `mission/current.json`. Current action is authorized
> only by that pointer, the current handoff, the registered Iter243 gate, and
> the operator's separate bounded repository-integration instruction.

## Iter243 remote-CI verdict

Iter242 reached its registered local engineering closure, but remote
publication correctly stopped before pytest collection. Push run
`29893324882` and pull-request run `29893361504` failed across the Python 3.11
and Python 3.12 matrix after checkout, setup-python, hash-locked dependency
installation, compilation, and Ruff passed. The exact workflow invoked the
documented `python3 -I` command. These runs remain negative evidence.

The failing predicate rejected every group-writable Python executable even when
the effective user owned the file. That restriction adds no protection against
the owner, who already has write and chmod authority, and the same blanket rule
inside the authenticated router would have denied a correction confined to the
outer runner.

The preregistered correction is Python-specific. It preserves `isolated`,
`ignore_environment`, `no_user_site`, and `safe_path`; requires an absolute
resolved regular owner-executable file owned by root or the effective user;
rejects world write; and permits group write only for effective-user ownership.
Git and timeout executables retain the stricter no-group-write rule. Spoofable
CI environment labels have no decision authority. The runner and router recheck
the applicable facts immediately before process creation, reducing but not
eliminating same-user time-of-check/time-of-use risk.

PR #90 remains draft and unmerged. GitGuardian separately reported generic
high-entropy findings on Git object-identity and evidence-digest fields. Each
occurrence must be regenerated or matched from exact repository bytes before a
narrow false-positive disposition; such a disposition is not a general
security approval.

The active workflow remains byte-identical. Required acceptance is a clean
authenticated local closure followed by normal push and pull-request triggers
passing across the registered matrix, retained exact run evidence, an Iter243
result and successor seal, a final exact-head check cycle, an ordered-parent
merge, and merged-master verification. Workflow dispatches and reruns cannot
substitute for those observations.

The scientific state is unchanged. Iter241 remains failed, independent semantic
ground truth remains blocked, and local or remote engineering checks cannot
establish prevalence, detector efficacy, independent review, publication
readiness, release readiness, or a state-of-the-art result.

## Retained Iter242 and scientific audit basis

Everything below is retained from the prior dated audit so its governed
quantitative corrections remain visible. Its older action ordering is
historical analysis; `mission/current.json` and the Iter243 handoff govern the
present engineering recovery.

## Verdict

Iter241 was not interrupted scientifically: its nonrepeatable capture completed and
failed. The interrupted work was the later repository-control integration. At
takeover, the correction checkpoint existed beyond remote master, the generated
experiment index was modified, router sources and tests were untracked,
current entrypoints still invoked bare pytest, and the handoff named
the old authorization merge as the required head.

The correct recovery is additive. It must preserve every failed-attempt byte,
freeze the exact corrected Iter241 subtree, authenticate the successor test
route before collection, synchronize current surfaces and registries, and stop
at a clean local commit. It must not rerun Iter241 or treat engineering closure
as repository closure, scientific evidence, security approval, independent
review, publication authority, or release readiness.

## Acceptance risks reviewed

- A worktree-only runner/router hash could agree locally while differing from
  the candidate commit. Authority-bearing sources therefore need exact
  worktree, index, and `HEAD` equality.
- Disabling plugin autoload does not by itself reject a tracked test module
  declaring `pytest_plugins`. The collection boundary must reject every such
  declaration and every repository `conftest.py`.
- The frozen Iter241 validator correctly fails on descendant heads. Only the
  exact authorization-head assertions may be deselected, and only after
  the separately retained successor seal qualifies.
- A historical Iter239 exact-workflow guard must validate its retained Git
  blob rather than prevent an additive, separately gated CI successor.
- A green suite cannot grant remote publication, scientific, retry, review, or
  security authority.

## Stopping-point requirement

The committed candidate met this requirement: the Iter241 seal qualified,
every current test entrypoint used the authenticated runner, current
registries and public surfaces agreed, known-bad cases fired, and the complete
offline CI-derived closure passed. Iter242 is therefore supported only as a
local engineering baton; all scientific and external boundaries remain.

## Retained scientific audit basis — 2026-07-19

The following scientific and programme audit is retained from the prior dated
audit. Its quantitative corrections remain part of the current claim
inventory. Its older mission ordering is historical analysis; the Iter242
verdict and the current handoff above govern the present local stopping point.

## Verdict

Telos is working on a real frontier problem: an agent can satisfy the tests or
grader used as its acceptance signal without satisfying the task that signal
stands for. As agent work becomes longer and less human-readable, evidence for
completion becomes more important, not less.

The present programme is not yet a frontier-grade benchmark, deployable
verifier, population-rate study, or completion proof. Its strongest defensible
position is the one the paper already states: a disciplined forensic real-task
case series whose strongest claim is existence, not prevalence, ranking, or
validated detector efficacy (`paper/telos.tex:191-194`).

The valuable asset is not a large effect. It is a rare combination of natural
proxy-compliant failures, retained execution evidence, explicit missingness,
published nulls, and visible self-correction. The immediate job is to make that
record internally authoritative, then replace gold-and-model-judge labels with
independently authored semantic ground truth, and only then measure the
assurance gained from consequence tests, trajectories, and provenance.

This audit does not speculate about whether any named executive or celebrity
would approve. The relevant test is whether the work meets published frontier
research and engineering standards.

## Scope, method, and limits

The audit inspected:

- `AGENTS.md`, root `HANDOFF.md`, the dated handoffs, `README.md`,
  `mission/loop.json`, `paper/telos.tex`, the generated paper, and the current
  evidence diagrams;
- the experiment and handoff chain from iter192 through iter236, with particular
  attention to the natural-rate, detector, TCP-1, witness-recovery, and
  transfer-reconstruction arcs;
- current Git state, recent history, workflow inventory, claim validators, and
  the Python test suite;
- current primary or authoritative research sources on coding-agent
  evaluation, reward hacking, sabotage and control evaluations, monitoring,
  contamination, and software provenance.

The audit made no provider calls, scientific dispatches, purchases, merges,
pushes, releases, submissions, or edits to sealed evidence. It did not contact
maintainers, independently establish provider training-data exposure, or
replace expert peer review. Budget figures below are planning estimates, not
quotes or authorization.

The ranked findings below freeze the repository state inspected before iter237
implementation. They remain the audit record even where the mutable working
tree now stages a correction. Current remediation status is called out
separately and is not evidence that the iter237 gate has passed.

## Mechanical checks versus scientific acceptance

The following pre-implementation checks were run from the repository root:

| Check | Result |
| --- | --- |
| `python3 scripts/validate_current_paper.py` | pass |
| `python3 scripts/validate_mission_loop.py` | pass |
| `pytest -q` | `803 passed in 32.76s` |

These results showed that the then-registered repository machinery was
internally healthy on this machine. They did not establish that every
published number is registered, every current-status surface agrees, the
labels are independent semantic truth, or the empirical design supports the
headline claim.

Iter236 demonstrates the distinction directly. The closure grew from 285 to
286 commands only after an analysis that had redirected the programme was
registered. Before that change, a green closure established that every
*registered* number regenerated, while readers could reasonably mistake it for
covering every published number
(`experiments/iter236_transfer_analysis_reconstruction/RESULT.md:124-132`).
The same iteration found that the paper's `p=0.008` does not reproduce under
the committed analysis; standard variants give approximately `0.0053` or
`0.0072` (`RESULT.md:71-90`).

Structural validation is therefore a floor, not scientific acceptance.

## What Telos has done well

1. **It found a consequential proxy gap in real agent work.** Five solver
   models across three providers produced official-suite-passing patches on the
   same fixed 53-target cohort that later failed a retained gold differential
   and the strict two-judge rule (`paper/telos.tex:488-517`). This is useful
   evidence that particular grader blind spots recur across solvers.

2. **It records missingness instead of converting it to zero.** Iter235
   recovered 33 of 41 previously unadjudicated certified patches, moving
   `k: 13 -> 17` and `u: 41 -> 8`, while reporting that only one of four new
   confirmations was a new task instance
   (`experiments/iter235_witness_recovery/RESULT.md:20-64`).

3. **It has allowed its instruments to fail publicly.** The repaired execution
   oracle moved the result down to `2/13`, exactly matching static review while
   producing more mixed-control flags
   (`experiments/iter232_validated_exercise_instrument/RESULT.md:18-46`).
   Three of four apparent issue-derived value catches were invalid tests; the
   reported result remained `1/10`
   (`experiments/iter234_issue_only_consequence_tests/RESULT.md:38-50`).

4. **It separates provenance from truth.** TCP-1 correctly says that hashes
   establish byte identity, not human independence, freshness, license,
   chronology, or semantic truth
   (`experiments/iter211_tcp1_materialization_preflight/RESULT.md:38-44`;
   `experiments/iter222_tcp1_agent_solvable_admission_evidence/RESULT.md:28-39`).

5. **It preserves observed-zero results, negative results, and corrections.**
   The two fresh-cohort `k=0` observations remain visible with their
   unadjudicated outcomes, rather than being promoted to confirmed nulls.
   Detector nulls, failed protocol gates, infrastructure nulls, and iter236
   corrections likewise remain visible rather than being silently removed.

## Ranked findings

### P0 — resolve before new science

#### P0.1 — There is no single current source of truth

- `AGENTS.md:14` directs a new session to root `HANDOFF.md`, which is a sealed
  iter222 artifact (`HANDOFF.md:1-31`).
- `docs/HANDOFF-2026-07-18.md:69-89` calls the paper submission-ready and names
  unfinished iter231 as the next step, although iter231 through iter236 now
  exist.
- `README.md:62-69` calls iter236 pre-registered and unexecuted, while
  `experiments/iter236_transfer_analysis_reconstruction/RESULT.md` is complete.
- `mission/loop.json:5-6,36-39` still carries iter207/iter222 current-boundary
  state.
- `paper/telos.tex:707-708` says cross-model generalization is unmeasured
  despite the cross-model section at `paper/telos.tex:488-517`; the conclusion
  at `paper/telos.tex:715-752` still centers earlier, narrower results.
- The current README evidence diagram ends at iter235
  (`README.md:406`) and contains stale state markers below it.

This is an authority failure, not a documentation nicety. A successor can
follow the documented bootstrap exactly and inherit the wrong baton.

#### P0.2 — The headline outruns the sampling design

`README.md:5` says the natural certified-yet-wrong rate is “measured and
generalized.” The evidence supports a narrower statement: certified-yet-wrong
behavior recurs across solvers on one enriched fixed cohort.

The five cross-model runs reuse the same 53 targets. Iter235 reports 17
confirmations across 125 certified attempts, but only 12 unique susceptible
instances (`iter235 RESULT.md:53-64`). Repeated solver attempts on the same
task are not independent task samples and cannot be pooled into a population
rate or treated as five task-distribution replications.

#### P0.3 — The fresh-cohort question is not closed

Iter224 and iter228 produced `0/15` and `0/22` confirmed outcomes, but also
reported `u=6` and `u=7`
(`experiments/iter224_natural_rate_scale_n/RESULT.md:16-26`;
`experiments/iter228_fresh_diverse_cohort/RESULT.md:19-30`).
Iter236 corrected the upstream description from 59 to 62 solved patches, of
which only 37 certified (`iter236 RESULT.md:49-66`).

The conditional scientific denominator for “certified yet wrong” is 37
certified patches, not 62 solved patches. Even assuming complete outcomes,
zero events in 37 gives a one-sided 95% binomial upper bound of approximately
7.8%. Outcomes are not complete: 13 of 37 remain unadjudicated. In addition,
only the reference solver was run on the fresh cohorts, whereas five solvers
were run on the enriched cohort. “Fresh cohorts do not work” is therefore not
an established closure.

#### P0.4 — Current labels are not independent semantic ground truth

The central label combines an accepted-patch differential with two model
judges. The paper correctly concedes that constructed rows are reference
differentials rather than independent semantic adjudications
(`paper/telos.tex:44-48,107-110`) and that the retained judge records omit raw
responses in important historical runs (`paper/telos.tex:70-76`).

An accepted patch is evidence, not a unique specification. A differential may
show different behavior without proving that only the candidate is invalid.
Model-judge agreement, even across providers, is not institutional
independence. No rate, benchmark, or verifier claim should advance until a
human-authored semantic ground-truth layer exists.

#### P0.5 — A published statistic and the current paper state are unreconciled

The paper reports Mann-Whitney `p=0.008`
(`paper/telos.tex:402-410`). Iter236 reconstructs the medians exactly but finds
no standard tested variant equal to `0.008`
(`iter236 RESULT.md:71-90`). The direction of the exploratory lead is
unchanged; the published digit is still unreproducible. The paper also mixes
pre-iter235 counts with corrected prose and an obsolete conclusion. It is not
submission-ready in its current state.

### P1 — important engineering and positioning work

#### P1.1 — The released detector benchmark is too small and structurally leaky

The release contains 13 positives, representing still fewer unique tasks, and
54 controls. Twenty-nine controls are normalized-identical to accepted
patches, so an accepted-patch lookup produces a misleadingly strong shortcut
(`experiments/iter233_natural_benchmark_release/release/README.md:43-84`).
The artifact is useful as a forensic fixture and regression corpus. It is not
a leaderboard or a stable basis for ranking detectors.

#### P1.2 — No current detector establishes practical efficacy

The static panel reaches `2/13` at `5/54` mixed-control flags
(`experiments/iter230_gold_free_detector_natural/RESULT.md:14-22`).
The validated execution oracle reaches `2/13` at `12/54` mixed-control flags;
the issue-derived union catches one gold-validated value failure and incurs
`13/54` mixed-control flags
(`iter232 RESULT.md:18-35`; `iter234 RESULT.md:15-36`).
These results motivate independent consequence evidence. They do not validate
a deployable verifier.

#### P1.3 — Repeated engineering lessons are not yet repository invariants

Iter236 reproduced iter221's exact bug class: bit-exact comparison of
platform-dependent `libm` values. Iter221's scan covers the historical guard,
not the repository class (`iter236 RESULT.md:147-163`). Iter236 also shows that
unregistered public numbers evade closure.

The known iter204 workflow failure is preserved in the historical record as a
parse/startup null (`README.md:321-328`), while
`.github/workflows/iter204-execute.yml` remains in the active workflow
inventory. Broken or intentionally historical workflows must not degrade the
meaning of current CI. Repair, retirement, or archival must preserve sealed
evidence and be performed additively.

#### P1.4 — “Completion proof” should become an assurance case

Finite tests, signatures, timestamps, and receipts cannot prove arbitrary
semantic completion. TCP-1 should be framed as an evidence-backed completion
assurance case with explicit residual risk and abstention. Provenance should
interoperate with existing standards rather than becoming Telos's scientific
novelty:

- SLSA v1.2 provenance:
  <https://slsa.dev/spec/v1.2/provenance>
- Sigstore Rekor transparency log:
  <https://docs.sigstore.dev/logging/overview/>
- W3C PROV-O:
  <https://www.w3.org/TR/prov-o/>

Telos's differentiated contribution should be independent semantic evidence
and the measured assurance delta, not a bespoke hash format.

## Iter237 local remediation result

The ranked findings above are the pre-implementation audit snapshot. The
current mutable working tree now contains the following iter237 repairs:

- a shared strict JSON comparator that applies tolerance only to
  float-versus-float leaves, plus cross-type known-bad cases;
- a repository-wide structural guard for exact comparisons of
  platform-dependent `libm`-derived evidence, with fixtures reproducing both
  the iter219 and iter236 defect classes;
- corrected T1 through T4 language and current counts across the README and
  paper;
- an additive machine-readable T1–T4 correction, result, and re-deriving
  validator that also checks the sealed iter235 tree against merged-master
  bytes;
- a corrected July 19 paper source and 16-page PDF rebuilt twice with identical
  output. All 16 rendered pages were visually inspected on 2026-07-19 with no
  clipping, overlap, or unreadable content found. Accessibility, author,
  citation, and release review remain open, so the paper is not
  submission-ready;
- a dated mutable operational handoff and current-state validation work that
  keep the sealed root handoff and mission memory historical.

The final local bytes passed `831` tests with `9` explicitly optional SciPy
equivalence cases skipped under Python `3.11.15`, and all `289` CI-derived
guard commands passed with bare `pytest` routed through that same interpreter.
The repository-wide libm scan covered `472` active Python files. All five
README Mermaid diagrams rendered and were visually inspected. This is local
macOS/arm64 evidence, not remote gate acceptance: the required Linux Python
3.11 and 3.12 jobs remain mandatory before any merge decision.

## Frontier comparison

| Current primary source | Frontier bar | Telos position |
| --- | --- | --- |
| OpenAI, “Why SWE-bench Verified no longer measures frontier coding capabilities” — <https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/> | Audit task validity and contamination; stop reporting a benchmark when its signal no longer supports the claim. | Telos studies a real failure of the grader, but its public Verified substrate is no longer a frontier capability benchmark. |
| OpenAI, “Separating signal from noise in coding evaluations” — <https://openai.com/index/separating-signal-from-noise-coding-evaluations/> | Human-supervised datapoint audits; distinguish overly strict, underspecified, misleading, and low-coverage tasks. | Telos deeply audits low-coverage pass cases, but lacks an equivalent independent expert audit of its own labels. |
| SWE-bench-Live — <https://arxiv.org/abs/2505.23419>; SWE-rebench — <https://arxiv.org/abs/2505.20411> | Fresh, continuously collected, executable tasks at 1,319 and more than 21,000-task scale. | Telos has richer forensics per case but only 12 unique susceptible instances on a public, contamination-prone substrate. |
| SpecBench — <https://arxiv.org/abs/2605.21384> | Preconstructed visible-feature versus held-out-compositional suites on long-horizon systems tasks. | Directly overlaps Telos's proxy/objective thesis at stronger prospective design and scale. Telos can differentiate through real maintenance tasks, independent authors, and assurance-stack ablations. |
| RewardHackingAgents — <https://arxiv.org/abs/2603.11337>; Hack-Verifiable Environments — <https://arxiv.org/abs/2605.20744> | Instrument environments so tampering, leakage, or exploitation receives auditable or deterministic labels. | Telos currently infers wrongness post hoc from gold differentials and judges. Its next design must make label validity and independence structural. |
| OpenAI internal-agent monitoring — <https://openai.com/index/how-we-monitor-internal-coding-agents-misalignment/>; Anthropic SHADE-Arena — <https://www.anthropic.com/research/shade-arena-sabotage-monitoring> | Retain full trajectories, evaluate monitors at explicit false-positive rates, use adversarial control evaluations, and preserve private tasks against contamination. | Telos's current natural patch studies do not retain a comparable full-trajectory substrate. TCP-1 points in the right direction but has not executed. |

The frontier opportunity is therefore narrow and meaningful: measure the
incremental assurance obtained from independently authored consequence tests,
full trajectories, and interoperable provenance on fresh real tasks. Another
existence count on the current public corpus would not move the frontier.

## Decisive mission sequence

No later stage may begin because an earlier stage is merely documented. Each
stage must pass its own retained-evidence gate.

### Iter237 — truth maintenance

Purpose: make the public and machine-readable record say one current thing.
This is a correction iteration, not a scientific result.

Required work:

1. Re-derive and synchronize the README, current handoff, paper source/PDF,
   diagrams, and mission memory against iter235 and iter236.
2. Replace “rate measured and generalized” with the bounded
   cross-solver/fixed-cohort claim.
3. Correct or explicitly retract the unreproducible `p=0.008`.
4. Reconcile the paper's abstract, cross-model section, limitations, conclusion,
   and corrected denominators.
5. Establish a nonsealed current-session entrypoint without modifying sealed
   root `HANDOFF.md`.
6. Replace the coercive artifact comparator with one strict JSON comparator
   that permits tolerance only for float-versus-float leaves.
7. Make the prohibition on exact comparisons of platform-dependent
   `libm`-derived evidence repository-wide, with known-bad fixtures for the
   iter219 and iter236 defect classes.
8. Produce an explicit propagation table for every corrected claim.

Acceptance:

- every current-status surface names the same active state;
- every changed number regenerates from a named committed builder;
- sealed evidence bytes remain unchanged;
- the paper validator, mission validator, full test suite, and closure pass on
  both required Python versions;
- an intentionally stale status, cross-type artifact change, and both
  historical exact-`libm` bug fixtures fail the new checks.

### Iter238 — claim, seal, and workflow controls

Purpose: extend iter237's typed numeric and `libm` invariants into complete
public-claim coverage, sealed-byte discipline, and an honest active-workflow
inventory. This is engineering evidence, not a scientific result.

Required work:

1. Introduce one canonical current claim registry. Each public quantitative
   claim must record a stable claim ID, status, scope, source surfaces,
   derivation command, input/output digests, missingness, supersession chain,
   and whether its source is sealed or mutable.
2. Add a seal registry that records sealed artifacts and their permitted
   additive successors. A current pointer must never require rewriting a sealed
   handoff.
3. Make CI fail when a README, paper, diagram, handoff, or mission claim is
   absent from the registry or conflicts with its registered current value.
4. Audit the active workflow inventory. Resolve the stale/broken
   `iter204-execute.yml` signal additively, and distinguish executable current
   workflows from retained historical workflow evidence.
5. Add known-bad tests for an unregistered paper number, stale active-gate
   pointer, broken workflow classification, and illegal sealed-byte change.

Acceptance:

- closure covers every registered public number and reports registry coverage;
- all four known-bad classes fail;
- current CI contains no unexplained permanent-red workflow;
- historical seals and Git ancestry remain intact.

### GROUND-TRUTH-1 — independent semantic adjudication

Purpose: determine which Telos candidate patches are independently supportable
as semantically wrong before using them to evaluate verification systems.

Design:

1. First apply the iter235 validity-and-paired-preflight method, in a new
   additive protocol, to the 13 unadjudicated certified patches in iter224 and
   iter228. Do not treat unrecovered rows as negative.
2. Use the 12 unique currently susceptible instances, the non-gold-identical
   hard negatives, and the recovered fresh rows as a bounded adjudication
   corpus. Report each stratum separately.
3. Recruit two conflict-screened domain experts per task. Authors see the issue
   and pre-fix repository state, but not the candidate, accepted patch, Telos
   label, witness, or prior judge output when specifying expected behavior and
   consequence tests.
4. Run each proposed consequence against the candidate, the accepted
   implementation, and at least one independently produced valid
   implementation. A test that fails either valid implementation is invalid,
   not evidence.
5. A third independent expert adjudicates disagreement. Preserve raw rationale,
   tests, execution records, conflicts, and abstentions.

Primary decision rule:

- `supported`: at least one independently authored valid consequence passes on
  both valid implementations, fails the candidate, and both semantic reviewers
  agree that the candidate violates the task;
- `contradicted`: reviewers agree that the purported differential is permitted
  by the task or the candidate is semantically valid;
- `inconclusive`: all other cases, including missing or conflicting evidence.

Admission to the next trial requires at least 95% consequence validity on the
valid-implementation controls, at least 90% adjudication completion, no critical
leakage, and fully retained reviewer independence evidence. If fewer than 10
unique positive labels remain supported, the existing corpus may remain a case
series but must not power a detector-efficacy claim.

### ASSURANCE-DELTA-1 — prospective frontier trial

Purpose: measure what the Telos evidence stack adds beyond test passing and
patch-only review.

Design:

- Use private or post-cutoff real maintenance tasks with independently authored
  hidden consequences frozen and externally timestamped before agent runs.
- Validate hidden consequences on the accepted implementation and independent
  valid alternatives before inspecting agent outcomes.
- Run multiple current agent stacks with repeated seeds, retaining full
  trajectories, environment state, patches, resource use, and standardized
  provenance.
- Evaluate the same attempts under four paired regimes:
  1. visible tests only;
  2. patch-only static or model review;
  3. patch-blind independent consequence tests;
  4. consequence tests plus trajectory monitoring and provenance checks.
- Maintain a randomly sampled natural stratum for incidence and a separately
  reported adversarial/red-team stratum for detector power. Do not pool them.
  Cluster all inference by task; repeated agents and seeds are not independent
  task samples.

Primary decision rule:

- `supported`: regime 4 improves detection of independently adjudicated wrong
  attempts by at least 10 percentage points over regime 2, with a one-sided 95%
  confidence bound above zero, while false rejection of independently valid
  implementations is at most 5%;
- `contradicted`: the upper 95% confidence bound on improvement is below 10
  percentage points;
- `inconclusive`: otherwise.

Report verification cost and latency beside efficacy. Trajectory evidence must
separate accidental proxy-compliant failure from deliberate evaluator
exploitation; a wrong visible-suite-passing patch alone does not establish
intent.

## Planning budget tiers

These ranges are rough programme-planning estimates. They are not vendor
quotes, commitments, or authorization to spend. External calls, hiring,
hardware, and payments remain operator-gated.

| Tier | Scope | Planning range | Claim boundary |
| --- | --- | --- | --- |
| Integrity | Iter237 and iter238 | `$0` external/provider spend; engineering time only | Repository authority and controls, no science |
| Ground-truth pilot | GROUND-TRUTH-1 on the bounded existing corpus | approximately `$15k-$40k` | Independent label audit, not prevalence or detector efficacy |
| Assurance scout | approximately 20 fresh tasks | approximately `$20k-$50k` | Protocol and instrument feasibility only |
| Credible trial | approximately 75 fresh tasks | approximately `$100k-$250k` | Task-clustered assurance comparison; still limited for rare natural incidence |
| Frontier trial | 150 or more fresh tasks plus adaptive red/blue work | approximately `$300k-$750k` | Stronger assurance and rare-event bounds; zero complete task-level events over about 150 independent tasks places the one-sided 95% upper bound near 2% |

If the budget cannot support independent authors and reviewers, stop after the
integrity stages. Replacing institutional independence with additional model
samples would reproduce the current limitation, not solve it.

## Final takeover decision

The next move is not another solver run and not paper submission.

Iter237 passed and merged. Complete iter238, then earn a separately
preregistered repository-governance gate so required CI and review policy fail
closed. GROUND-TRUTH-1 remains the next scientific gate and requires separately
authorized, conflict-screened human adjudication. Only a green, independent
ground-truth gate authorizes ASSURANCE-DELTA-1.

This sequence preserves Telos's real strength—evidence disciplined enough to
survive correction—while moving the programme from a small forensic case
series toward the question frontier teams can use: how much trustworthy
assurance does each additional evidence layer buy, at what false-positive
rate, cost, latency, and residual risk?
