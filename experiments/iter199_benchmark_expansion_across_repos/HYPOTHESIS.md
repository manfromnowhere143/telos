# Iteration 199 - Benchmark Expansion Across Repositories

Status: PRE-REGISTERED, result pending. No provider calls, SWE-bench executions, or cloud resources have
been run for this gate. The target set is frozen in `proof/raw/targets.json` before any variant is
generated.

## Why this gate exists

The certified-resolved reward-hack benchmark from iter192-iter197 has 10 hacks across 3 repositories
(Django, astropy, matplotlib). The paper's largest weakness is that small, narrow set. This gate grows the
benchmark with the same proven pipeline, on 42 fresh SWE-bench Verified instances spanning all 12
repositories in the dataset, so the "certified yet wrong" class is shown to generalize beyond three
repositories rather than being an artifact of them.

## Frozen target set

`proof/raw/targets.json` fixes 42 instances before generation: up to 4 per repository (all available from
smaller ones), chosen deterministically by sorted instance id, each with a single-source-file gold patch
and at least one added line to substitute. None overlaps the original 16 iter193 candidates. The 12
repositories are astropy, django, matplotlib, seaborn, flask, requests, xarray, pylint, pytest,
scikit-learn, sphinx, and sympy. Nine of these (all but django, astropy, matplotlib) are new to the
benchmark.

## The pipeline (unchanged from iter193-iter195; execution decides everything)

For each target, in its pinned SWE-bench container:
1. **Elicit** a variant: a frontier model rewrites the gold patch's largest added block into a variant that
   keeps the graded tests passing but is subtly wrong (elicited, not observed in the wild).
2. **Certify by execution**: run the instance's official SWE-bench evaluation script under the variant and
   parse it with the official parsers; keep the variant only if it passes every `FAIL_TO_PASS` and
   `PASS_TO_PASS` test.
3. **Witness by execution**: gold is used only at ground-truth time (forbidden to detectors); a model
   builds an in-container scenario targeting the divergent branch, run under gold and under the variant; a
   difference in output with a clean gold run is the witness.

A confirmed hack is a variant that is both certified-resolved and witnessed wrong, exactly as in iter195.

## Numeric Bars

Minimum pass bars:

- provider calls do not exceed `160` (adversary + scenario generation) and estimated spend does not exceed
  `$30.00`,
- new cloud resources created and not deleted is exactly `0`,
- every confirmed hack is certified-resolved by official-harness execution (all `FAIL_TO_PASS` and
  `PASS_TO_PASS` pass under the variant),
- every confirmed hack has a recorded gold-differential witness (gold and variant produce different clean
  output on a synthesized input) executed in the pinned container,
- new confirmed hacks is at least `8`,
- confirmed hacks span at least `5` repositories, of which at least `3` are new to the benchmark (not
  django, astropy, or matplotlib),
- raw adversary variants, eval reports, and witness transcripts retained for every confirmed hack is
  `100%`,
- committed secret/private identifier hits are exactly `0`,
- forbidden positive claim hits are exactly `0`.

## Falsifiers

1. Any confirmed hack is not certified-resolved by official-harness execution (any failing graded test).
2. Any confirmed hack lacks a reproducible gold-differential witness.
3. Gold content, labels, hidden test names, or official reports enter any detector-facing artifact (this
   gate builds benchmark rows, not detector inputs; still, the witness scenario is a construction artifact,
   not a detection artifact).
4. Fewer than `8` new confirmed hacks, or fewer than `5` repositories, or fewer than `3` new repositories:
   the gate publishes a null with the full per-stage yield (targets, variants, certified, witnessed) and an
   honest construction-hardness-by-repository breakdown.
5. Provider calls exceed `160`, spend exceeds `$30.00`, or a cloud resource is left undeleted.
6. The result presents a natural-frequency, non-elicited, leaderboard, model-superiority, state-of-the-art,
   broad robustness, production, or product-value claim.

## Claim Boundary

At most, if this gate passes: the certified-resolved reward-hack benchmark grows by at least `8` new
execution-verified hacks spanning at least `5` repositories (at least `3` new), constructed under a
bounded, elicited frontier-adversary budget with retained witnesses, showing the class generalizes across
repositories. If it fails, the gate publishes an honest per-repository construction-hardness bound.

Not supported: any natural-frequency estimate (the hacks are constructed and elicited); any claim about how
often deployed agents hack; any leaderboard, model-superiority, state-of-the-art, broad robustness,
production, or product-value claim. "Wrong" means differs from the gold reference fix on a constructed
input.
