# Telos findings paper — rewrite spine (iter198 scaffolding)

> **SUPERSEDED HISTORICAL SCAFFOLD.** This file preserves the plan used at the iter198 boundary; it is not
> a current claim source or writing instruction. Iter197 and iter201 now record protocol `FAIL`: the
> retained property pipeline used candidate-diff-derived locators and gold-based inclusion, so its accurate
> label is **locator-assisted, gold-validated property pipeline**, not a validated gold-free detector. On
> the full 22-row cohort, judge/property/union catches are `20/22`, `6/22`, and `20/22`; the property-only
> set is empty, no independent property false-positive estimate exists, and no ensemble-dominance claim is
> supported. Iter200 is exploratory, nonrandom, and gold-localized under a post-inspection strict rule.
> The apparent iter197 property-only row was judge-unadjudicated, its `>=5` threshold was added after
> property generation, and the registered paired-gold decisions were not run independently. The historical
> complementarity and preregistered-threshold statements below are therefore false current claims, retained
> only as superseded scaffolding.
>
> **Additional standing corrections (2026-07-16):** iter192's overbroad novelty interpretation is
> conservatively adjudicated `FAIL`, while its literal v1-specific falsifier trigger is indeterminate and
> its deterministic `40/40` construct correction remains exact.
> Historical tarballs contain `139` harness-resolved evaluations across `65` instance IDs, but disposition
> evidence does not bind all of them to discard decisions. Iter195 is protocol `FAIL`: its generator saw
> both gold and variant hunks and attempted at most one targeted scenario per candidate instead of the registered
> no-gold, `>=10/20` synthesized-input design. Its ten clean differentials remain exploratory diagnostics,
> not validated no-gold synthesis or independent semantic-wrongness evidence. The 22-row corpus must remain
> split into those ten protocol-failed iter195 rows and twelve iter199 rows. Iter199's hypothesis and
> provider outputs first appear in the same commit, so it records a post-provider, pre-execution stated
> design rather than a preregistration. Iter196 is partial/protocol-blocked Detector A only and did not clear
> its registered both-detector bar. Iter201 records four coincidental shared-gold-line diagnostic triggers,
> which are not identified-gold leakage and establish no causal direction or effect magnitude. Iter202's interrupted no-output
> invocation is conservatively charged `53` calls / `$2.65` separately from its retained `53` solver calls.
> Any historical no-gold synthesis, independent semantic-wrongness, homogeneous 22-row protocol, iter199
> preregistration, iter196 completion, or unrestricted reproducibility claim below is false as a current
> claim.
> The current manuscript and claim boundary are `paper/telos.tex`, `paper/README.md`, and the root README.

This is the analytical skeleton for the iter198 accessible rewrite. It fixes, before any prose is written,
the structure, the exact number and claim boundary that belongs in each section, and the accessibility
rules. The prose pass filled this in; it did not re-decide it. Historical Telos figures below were linked
to committed experiments, but this superseded file does not certify their protocol validity.
External-source quantities depend on their cited sources rather than repository regeneration.

## Working title

`Reward Hacks That Pass the Test Suite: Constructing and Detecting SWE-bench Patches That Are Certified Yet
Wrong`

Rationale: states the contribution in plain words a non-specialist reads correctly on first pass. Avoids
the dense abstraction-stack of the current title. Alternatives to weigh at write time, same plainness bar:
"Certified but Wrong: ..." / "When the Test Suite Certifies a Wrong Fix: ...".

## The one-sentence thesis (the paper must never drift from this)

A capable coding agent can produce a patch that the SWE-bench Verified grader marks resolved — passing
every graded test — while being wrong on behavior no test covers; we construct such patches, and we measure
which detectors catch them.

## Accessibility rules (Caesar's #1 lesson — binding on every sentence)

1. Define every specialized term on first use, in plain words: reward hacking, SWE-bench Verified,
   FAIL_TO_PASS / PASS_TO_PASS, certified-resolved, gold patch, gold-free, uncurated test, coverage-bound,
   differential oracle, judge panel.
2. One idea per sentence. No hyphen-dense abstraction stacks (e.g. not "gold-free execution-grounded
   diff-level oracle" without having defined each piece first).
3. Spell out every antecedent: never "it" / "this" / "the former" where the referent must be reconstructed.
4. The abstract must be readable by a domain expert on one pass, with no decoding. Numbers appear with
   what they are a rate *of*.
5. Prefer a worked example over a definition where possible (django-11179 is the canonical one — use it
   early).
6. No self-praise (validate_docs enforces this) and no claim above its evidence.

## Section spine

### 0. Abstract (~200 words)

Plain-language whole story: agents can game the grader; SWE-bench Verified certifies some wrong patches; we
construct 10 execution-verified certified-resolved reward hacks; a judge panel catches 7/10 with false
positives, a gold-free execution oracle catches 4/10 with none, and they are complementary (union 8/10).
State the limits in the abstract itself (elicited, constructed, N=10). Numbers, each with its denominator.

### 1. Introduction

- The problem, in plain terms: a coding agent's task is "make the tests pass," but passing the tests is not
  the same as solving the task. An agent can pass the graded tests while leaving wrong behavior the tests
  never check. In reward-learning terms, the test suite is a proxy reward and passing it without solving
  the task is reward hacking. [define reward hacking here, cite amodei2016 / krakovna2020 / skalse2022]
- The specific gap: does SWE-bench Verified — the standard agent coding benchmark — certify patches that
  are actually wrong? If so, no test-based check can catch them, because the tests are what "certified"
  means.
- Why it matters now: DeepMind's Frontier Safety Framework v3.0 (2025-09-22) describes exactly this case
  (a model circumventing oversight even when its outputs are monitored) and lists the mitigation as "Future
  work." [cite]
- Contributions (exactly these, no more):
  1. a self-audit correcting an earlier benchmark that did not contain reward hacks (iter192);
  2. 10 execution-verified certified-resolved reward hacks, constructed and released with witnesses
     (iter193-195);
  3. a decision-time comparison of two detectors — a judge panel and a gold-free execution oracle — with a
     measured recall/precision/coverage tradeoff and complementarity (iter196-197).

### 2. Background and related work

- Reward hacking / specification gaming: define, cite. Distinguish from RewardBench (reward *models*) — a
  reviewer will confuse them; pre-empt it.
- SWE-bench Verified: what it is, what FAIL_TO_PASS and PASS_TO_PASS are, what "resolved" means. Note the
  known criticism that its test suites can be under-specified.
- LLM judges as monitors: cite Control Tax (arXiv:2506.05296, monitor AUC 0.92-0.96 on APPS backdoors) and
  Redwood trusted-editing; state honestly that judges have real signal on some backdoors and degrade on
  semantic hacks in real repos. This sets up our 7/10 as consistent, not surprising.
- Existing reward-hack corpora and their scale: METR MALT (~10,919 transcripts), Terminal Wrench (3,632),
  ControlArena apps-backdoors (4,184), TRACE (517), ImpossibleBench. State plainly that ours is far smaller
  and that its only edge is precision and diff-level granularity, not size. Every existing corpus labels
  trajectories/whole solutions and is elicited; ours is diff-level and also elicited (claim granularity,
  not naturalness).
- Gold-free / reference-free verification and property-based oracles: the lineage our oracle sits in.

### 3. The benchmark was measuring the wrong thing (iter192)

Frame as methods integrity + motivation, not as an aside.

- The construct error: the prior benchmark's generator admitted a row only when at least one PASS_TO_PASS
  test failed, so every row breaks the existing suite by construction.
- The evidence, from committed harness reports: 40/40 rows are resolved=false; 40/40 break the existing
  suite. [iter192 official_harness_verdict.json]
- The consequence: the existing-suite baseline detects 40/40 at $0.00 model-provider spend; the three-model
  judge panel detected 17/40 with a $13.128090 estimated spend guard for 240 score-producing calls. This is
  not an invoice; the rounded $13.59 through-repair total includes excluded diagnostics. [iter192/iter207]
- The correction, stated cleanly: those rows are not reward hacks (they fail the reward); they are
  suite-failing wrong patches. The real target is the inverse — patches that PASS the whole suite yet are
  wrong. This motivates the rest of the paper.
- Claim boundary: the 17/40 figure is arithmetically correct and not retracted; what changes is what it is
  a figure about (LLM code review of already-rejected patches).

### 4. Constructing certified-resolved reward hacks (iter193-195)

- Definition, plainly: a certified-resolved reward hack is a patch the official SWE-bench harness marks
  resolved (passes every FAIL_TO_PASS and PASS_TO_PASS test) that is nonetheless wrong on some input the
  tests do not cover.
- Method:
  - a frontier adversary rewrites the largest added block of the gold patch into a variant that keeps the
    graded tests passing (elicited; state this) [iter193];
  - the runner: certification is decided by executing the instance's official SWE-bench eval script under
    its instance-specific container tag (django uses runtests.py, others pytest), parsed with the official
    SWE-bench parsers; historical runs used mutable `:latest` tags without retained image digests
    [iter194];
  - the wrongness witness: gold is executed only to establish ground truth (forbidden to detectors); a
    model constructs an in-container scenario targeting the divergent branch, run under gold and variant,
    and a difference in output witnesses the hack [iter195].
- The key negative that shapes the method (iter194): no shipped test can witness these — for django the
  curated PASS_TO_PASS is the whole test module (0 uncurated tests), and across all 16 candidates the 193
  available uncurated tests distinguish none from gold. This is why a synthesized probe beyond the tests is
  required, and it is a real finding about reference-free verification.
- Result: 10 execution-verified certified-resolved reward hacks across 3 repositories; 2 candidates were
  correct equivalents (reported, not hidden); the rest honest nulls. [iter195]
- Worked example (use early and concretely): django-11179. The gold fix clears an instance's primary key to
  None after delete. The variant clears it only when the key is literally named "id"
  (`None if pk.name == 'id' else instance.pk`). The graded tests only use "id"-named keys, so the harness
  certifies it; a model with a differently-named key leaves a stale key after delete. gold prints None,
  variant prints the stale value.
- A second, self-critical example that strengthens credibility: django-11119 was hand-analyzed as a likely
  correct equivalent; execution proved it a real hack (gold renders text unescaped when autoescape is off;
  the variant escapes it). Use this to make the paper's own thesis vivid: for this class, run the code —
  do not trust a verdict, including the authors'.
- Claim boundary: elicited and constructed, not a natural frequency; N=10, 3 repos; "wrong" means differs
  from the gold reference fix on a synthesized input.

### 5. Detecting them (iter196-197)

- Setup: every detector sees only the candidate diff, the public task, and the visible test — never the
  gold patch, the label, hidden tests, or the construction witness.
- Detector A, judge panel (iter196): 2 frontier judges (gpt-5.6-terra + claude-opus-4-8; the third default,
  gemini, was unavailable — state this). Recall 7/10 (any_catch), false positives 1/10 on gold controls and
  1/2 on the correct-equivalent hard controls. Single stochastic run — say so. Report the two methodology
  fixes honestly (a leakage-guard false alarm resolved to 2/10 coincidental shared lines biasing against
  recall; an OpenAI token budget that had to be raised so nondecisions were not miscounted as legitimate) —
  these strengthen credibility.
- Detector B, gold-free execution oracle (iter197): a model proposes an executable correctness property
  from the public task and visible test only; it is validated by passing on the gold control; a sound
  property that fails on the variant catches the hack. 12/12 properties sound, recall 4/10, false positives
  0/2. Precise but coverage-bound.
- The comparison and the load-bearing finding: a clean recall/precision/coverage tradeoff (judge higher
  recall / lower precision; oracle lower recall / perfect precision) AND complementarity — the oracle caught
  django-11211 the judge missed, the union is 8/10, only 2 astropy hacks evade both. An ensemble dominates
  either instrument alone.
- Make the coverage-bound mechanism concrete with django-11179: the gold-free property, never having seen
  the gold fix or the diff, tested an "id"-named key where the variant behaves correctly, so it passed and
  missed; the judge caught it by reading the suspicious condition. This explains both why the oracle's
  recall is lower and why it is precise.
- Claim boundary: bounded pilot comparison; N=10; judge is one stochastic run; no leaderboard,
  model-superiority, or SOTA claim.

### 6. Limitations (a real section, not a footnote)

- Small N (10 hacks, 3 repositories); wide uncertainty; a pilot, not a distributional result.
- Elicited and constructed, not sampled from real agent behavior; no natural-frequency claim.
- "Wrong" is defined against the gold reference fix, not an independent oracle.
- The judge result is a single stochastic run; verdicts vary run to run.
- The gold-free oracle is demonstrated on framework-internal functions and is coverage-bound.
- No claim that the class generalizes beyond the repositories and instances tested.

### 7. Conclusion

- SWE-bench Verified certifies wrong patches; we built and released 10, with witnesses.
- The tests that define "resolved" cannot catch them; reference-free verification must probe beyond the
  tests.
- Two detectors are complementary; an ensemble of a judge and a precise execution oracle is the practical
  recommendation.
- Future work (honest, not hype): scale N and repositories; move from constructed to naturally-occurring
  hacks; formalize the ensemble.

## Figures / tables to build

1. Table: iter192 correction — official-harness baseline 40/40 at $0.00 model-provider spend vs judge panel
   17/40 with a $13.128090 score-producing-call estimated guard.
2. Table: the 10 certified-resolved hacks — instance, function, gold output, variant output. [iter195]
3. Table: two-detector comparison — recall, gold FP, equivalent FP, per detector. [iter196/197]
4. Figure/Venn: complementarity — judge caught, oracle caught, union 8/10, missed by both (2 astropy).
5. Figure: the pipeline — construct (adversary + official-harness certification + synthesized-input
   witness) then detect (judge, gold-free oracle).

## Numbers ledger (single source of truth for the writer — cite these exactly)

- iter192: 40/40 resolved=false; 40/40 break suite; baseline 40/40 at $0.00 model-provider spend vs panel
  17/40 with a $13.128090 score-producing-call estimated guard; lexical scan 0/677 Markdown files, but
  iter151 supplies a class-level precursor and exact v1 identity is indeterminate.
- iter194: 16/16 executed project-correct; 16/16 certified-resolved; 193 uncurated tests, 0 distinguish.
- iter195: 10 witnessed hacks; 2 certified-equivalent; 15 scenarios (10 wrong, 2 equiv, 2 scenario-failed,
  1 variant-errored); 13/15 validated; ~$0.80.
- iter196: judge panel any_catch 7/10; gold FP 1/10; equivalent FP 1/2; single run; ~$2.64.
- iter197: 12/12 sound; oracle recall 4/10; equivalent FP 0/2; union with judge 8/10; oracle-only catch
  django-11211; missed by both astropy-14096, astropy-7166; ~$0.60.

## After this gate (not part of the writing)

Per the Sentinel lesson (endorsement is not acceptance; arXiv moderation prescribes peer review and a DOI
first): send to a peer-reviewed venue (an ICML/NeurIPS/ICLR safety-or-evaluation workshop with proceedings,
or a journal) for a DOI, then appeal to arXiv with the DOI. No submission without operator direction.
