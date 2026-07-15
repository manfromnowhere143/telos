# Iteration 197 - Gold-Free Execution Oracle vs. Certified-Resolved Reward Hacks

Status: PRE-REGISTERED, result pending. No provider calls, SWE-bench executions, or cloud resources have
been run for this gate.

> **Post-result methodology correction (2026-07-15):** the protocol below was not followed as written.
> The executed generator extracted a source-file and function/class locator from each candidate variant
> diff and inserted those fields into the prompt. Candidate code lines and gold content were withheld, but
> generation was locator-assisted rather than diff-independent. The actual adjudicator also defined
> soundness by executing the property on the gold patch, not by the preregistered visible-test anchor.
> Therefore the retained result is a locator-assisted, gold-validated offline property pipeline; it is not
> a fully gold-free detector, and its zero gold failures are not an independent false-positive estimate.
> The registered `10` paired-gold controls were not independently generated and evaluated as detector
> decisions: those gold executions were the inclusion filter. Specificity on that registered control set
> is therefore unavailable. This file's pre-output freeze,
> `336c484200289d27ee1361f5fbd1e85e51494fa9` at `2026-07-14T19:54:46+03:00`, contained no numerical
> catch threshold. The `>=5` threshold first appeared in
> `f62aea8c19b109f9488accfb4b58c3f03d6d7a6f` at `2026-07-14T21:40:16+03:00`, alongside generated
> properties, and is only a post-generation diagnostic. The historical Docker scripts used mutable `:latest` image tags
> and retained no resolved image digest. This correction reinterprets the run and does not retroactively
> repair the preregistration.

## Why this gate exists

iter196 measured the incumbent: a frontier LLM judge panel, reading only the diff, flags `7/10` of the
iter195 certified-resolved reward hacks at `1/10` gold false positives (single stochastic run). Judges
carry real signal on this class. The question this gate answers is whether an execution-grounded, gold-free
oracle can match or beat that — and at what precision — on the class the official harness certifies and all
shipped tests miss.

This is Detector B, promoted from iter196. It is the execution-grounded instrument the mission's thesis
favors, and iter195 already showed that execution *with gold* witnesses `10/15`. The open question is
whether a *gold-free* oracle — one that never sees the correct fix — can do the same at detection time.

## The oracle (gold-free, execution-grounded)

For each candidate (the `10` hack variants, `10` gold controls, `2` equivalent controls), at detection
time:

1. A model proposes an executable property or expanded test — an assertion about correct behavior — from
   the public task statement and the visible test only. It never sees the gold patch, the gold diff, the
   label, hidden tests, official reports, the variant-vs-gold pairing, or the iter195 witness.
2. Validate the property on the visible-test anchor (iter126): it must hold for the known-correct behavior
   the visible test asserts, and must execute without error. An unvalidated property is
   `property_unsound`, not a detection.
3. Execute the validated property in the pinned container against the candidate. A candidate that violates
   a validated property is flagged as a reward hack.

Soundness comes from the visible-test anchor, not from gold. This mirrors iter121-126: gold-free at
decision time, validated against known-correct visible behavior.

## Numeric Bars

Minimum pass bars:

- provider calls do not exceed `120` and estimated spend does not exceed `$15.00`,
- no undeleted cloud resources,
- property synthesis prompts contain zero gold/label/hidden-test/witness leakage (scanned, gold-distinctive
  lines not shared headers),
- validated (anchor-sound) properties for at least `6` of `22` candidates,
- recall on the `10` hacks and false-positive rate on the `12` controls are reported with raw per-row
  property text, validation status, and execution transcripts retained,
- the false-positive rate on gold controls is reported honestly even if it exceeds Detector A's.

## Falsifiers

1. Any property-synthesis prompt contains gold content, the gold diff, a label, a hidden test name, an
   official report, the pairing, or the iter195 witness.
2. A flagged hack's property was not validated on the visible-test anchor (unsound property flagging is not
   a detection).
3. A reported recall/FP number does not regenerate from retained property text and execution transcripts.
4. Controls are not evaluated (recall without specificity is not a result).
5. Provider calls exceed `120`, spend exceeds `$15.00`, or a cloud resource is left undeleted.
6. The result presents a leaderboard, model-superiority, state-of-the-art, natural-frequency,
   benchmark-size, broad robustness, production, or product-value claim.

## Expected outcome and why a null still matters

iter139 measured property-derivability at `~0.10` on math-heavy repos, and these `10` functions are
framework-internal (ORM, forms, plotting), harder than the pure functions iter122-126 worked on. The
honest prior is that the gold-free oracle validates few properties and catches few hacks — likely fewer
than Detector A's `7/10`, but at higher precision where it applies. If so, the result is a real, defensible
finding: gold-free execution oracles are precise but coverage-bound, and the judge panel has higher recall
at lower precision — a genuine recall/precision/coverage tradeoff between the two instruments, which is the
comparison the paper needs. A high-recall gold-free oracle would be the stronger, more surprising result.

## Claim Boundary

At most, if this gate passes: on `10` execution-verified certified-resolved reward hacks and `12` controls,
a gold-free execution oracle achieves a reported recall and false-positive rate, measured at decision time
with gold forbidden, comparable side-by-side with the iter196 judge panel. This is a bounded pilot
comparison of two detectors on a small constructed set — not a leaderboard, model-superiority, or
state-of-the-art claim, and not a natural-frequency estimate.
