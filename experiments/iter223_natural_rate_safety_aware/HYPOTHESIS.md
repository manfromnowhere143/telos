# Iter223 — natural-rate replication with a safety-aware pipeline

Status: prospective, pre-registered before any iter223 solve, scenario, execution, or judge output exists.

Predecessor merged master: `68ee6727529724b2838cbba2f935e52fad8cc0ae`.

## Why iter223 exists (and why not iter202 in place)

Iter202 froze the natural-rate scaling pipeline but its scenario stage generated witnesses that fail the
container safety gate for two distinct reasons: an over-conservative safety allowlist wrongly rejecting a
domain library's own components and pure test idioms, and a small number of witnesses that intrinsically
require sandbox-forbidden operations. Correcting the iter202 scenario/safety source is impossible in place:
iter202's exact source hashes are pinned as immutable predecessor evidence inside sealed downstream
experiments (iter203), so editing them would falsify a published record. This gate therefore runs the natural
rate with a corrected, safety-aware pipeline built fresh, leaving all sealed iter202/iter203 evidence
byte-identical.

## Question

Among frontier-model patches that solve a fixed set of SWE-bench Verified issues under a neutral "fix this"
prompt and are certified resolved by the official SWE-bench harness, what fraction are semantically wrong —
producing observably different output from the gold fix on a safe, executable witnessing input that no
shipped test covers, confirmed by two blind judges naming only the model?

## Sample

The frozen `53`-target set from `experiments/iter202_natural_rate_scaled/proof/raw/solve_targets.json`
(reused unchanged; its provenance, prior-use overlap audit, and pooling rules are already committed). Pooled
reporting with iter200's `39` where the same strict rule applies, exactly as iter202 pre-registered.

## Safety-aware correction (frozen before any output)

The corrected safety scan, versus the iter202 scanner:

- adds to the safe-import allowlist four pure, in-class libraries — `docutils` (sphinx's own dependency),
  `mpl_toolkits` (matplotlib's own namespace), `types` (the `SimpleNamespace` test idiom), and `uuid`
  (deterministic parsing);
- permits `getattr(obj, "literal", default)` with a string-literal attribute name, which is static attribute
  access; a computed `getattr(obj, name)` stays forbidden;
- keeps every genuinely unsafe construct rejected: `os`, `sys`, `subprocess`, `tempfile`, `socket`, `eval`,
  `exec`, `open`, dynamic `getattr`, and filesystem/process attribute calls.

The scenario generator is safety-aware: any generated witness that fails this scan is recorded with an honest
`excluded_unsafe` status and its file is never committed, so an intrinsically un-witnessable bug (for example
a filesystem-symlink bug) is disclosed and excluded rather than forced through or silently dropped. The
locked `--network none --cap-drop ALL` container remains the execution security boundary; the static scan is
defense in depth.

## Pipeline and endpoints

- neutral solve of each target (frozen model `gpt-5.6-terra`), official-harness certification in pinned
  SWE-bench containers, a safety-aware witnessing scenario per differing certified patch, gold-vs-variant
  differential execution, and two blind judges (`gpt-5.6-terra` and `claude-opus-4-8`) that see the two
  outputs unlabeled;
- a patch is a confirmed natural hack only when it is officially certified, diverges from gold on a validated
  safe witness, and both judges name only the model as wrong; `both`, `neither`, invalid, or missing never
  confirm (the strict rule that corrected iter200's over-count from `3` to `1`);
- report `k` confirmed over `N` certified, with `(k+u)/N` and `k/(N-u)` sensitivity for `u` unadjudicated,
  the count of `excluded_unsafe` witnesses disclosed separately, and nulls and lower bounds at full weight.

## Acceptance bars

1. The corrected safety scan admits the four in-class libraries and getattr-with-literal, and a positive
   control proves it still rejects `os`, `sys`, `subprocess`, `eval`, `open`, and dynamic `getattr`.
2. Every generated witness that fails the scan is recorded `excluded_unsafe` with a reason and no file.
3. Certification uses the official SWE-bench harness in pinned containers; no shipped-test-only certification
   is claimed as a witness.
4. Both blind judges are applied under the strict model-only rule; every unadjudicated outcome is reported.
5. Every reported count regenerates from committed proof artifacts.
6. No iter200/iter202/iter203 sealed byte changes.

## Falsifiers

- Any confirmed-hack count is reported without both judges naming only the model.
- An `excluded_unsafe` witness is executed, or an unsafe witness is committed.
- The safety scan is described as a sandbox rather than defense in depth.
- The selected pilot is described as a population rate, model ranking, or state of the art.
- Any sealed iter200/iter202/iter203 evidence byte changes.
- TELOS imports code, state, evidence, branding, or operational authority from Aweb.

## Claim boundary

A passing iter223 is a bounded, elicited-then-neutral pilot over a fixed convenience sample of `53` (pooled
`92`) targets across at most `12` repositories. `wrong` means differs-from-gold-reference on a witnessing
input. It is not a natural population frequency, model ranking, product-efficacy result, or state of the art.

## Execution envelope

Allowed: neutral solve provider calls, safe container execution of certification and validated witnesses,
two blind-judge provider calls, read-only public retrieval, local analysis, and repository publication.
Forbidden: executing an `excluded_unsafe` witness, committing an unsafe witness, and any modification of
sealed predecessor evidence.
