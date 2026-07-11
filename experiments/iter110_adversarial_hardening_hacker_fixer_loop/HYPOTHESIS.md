# Iteration 110 - Adversarial Hardening (Hacker-Fixer Loop)

Status: pre-registered, result pending. Frozen before the adversarial suite was run.

## Why this gate exists

Iter109 earned a `0/200` false-positive rate on real human gold patches and full recall on a
*matched* constructed attack set, but a probe showed a dict-lookup source special-case evades
detection. Recall against matched attacks is not robustness. This gate runs the hacker-fixer
loop from the 2026 verification literature: an adversary evolves reward-hack variants
specifically to evade the current detector; the detector is then hardened to close real gaps,
under the hard constraint that hardening may not raise the false-positive rate on the 200 real
patches.

## Method

1. Freeze the iter109 real corpus (200 gold patches) as the negative class.
2. Generate an adversarial positive class spanning evasion families the iter109 detector does
   not obviously match: dict/tuple membership special-casing, tautological assertions
   (`assert x or True`, `assert x is not None`), commented-out assertions, `unittest`/decorator
   skips, exception-swallowing around assertions, and source-side monkeypatching of the asserted
   symbol.
3. Measure iter109-detector recall on the adversarial class (expected to drop - that is the point).
4. Harden the detector signal-by-signal. After every change, re-measure the false-positive rate
   on the 200 real gold patches. Reject any hardening that pushes it above `0.05`.
5. Report recall before and after hardening, the residual evasions that survive, and the final
   false-positive rate. Residual evasions are expected and are the honest research frontier.

## Acceptance bars

1. Post-hardening false-positive rate on 200 real gold patches is at most `0.05`.
2. Post-hardening adversarial recall is at least `0.80` (strictly greater than pre-hardening).
3. Every surviving evasion is explicitly enumerated with a reproducing fixture.

## Falsifiers (a null is acceptable)

1. If no hardening can raise adversarial recall above the pre-hardening baseline without pushing
   the real-patch false-positive rate above `0.05`, publish a null: the provenance/assertion
   signals cannot be hardened against these evasions without harming real patches.
2. If hardening raises real-patch false positives above `0.05`, the tightened rule is invalid;
   revert it and record the tension.
3. If the detector reads any label or attack-type field, the run is invalid.

## Execution envelope

- provider model invocations: `0`, provider spend: `$0.00`, GPU: forbidden,
- production/live-domain mutation: forbidden, benchmark/model/SOTA claim: forbidden.

## Claim boundary (pre-committed)

At most: "after one hacker-fixer round, the detector's recall on adversarially-evolved reward
hacks rose from X to Y while the false-positive rate on 200 real human patches stayed at Z, with
the residual evasions enumerated." Not a benchmark, model, robustness-guarantee, or SOTA claim.
