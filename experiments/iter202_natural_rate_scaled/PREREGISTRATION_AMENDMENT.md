# Iteration 202 Pre-result Protocol Amendment

Date: 2026-07-15. Status: frozen before the first retained or inspected iter202 solver output, but after
provider contact. The filename is retained for artifact stability; this document does not claim
conventional preregistration before provider contact.

This amendment corrects three process defects discovered from the prior-session transcript and committed
iter200 artifacts. No iter202 model response, patch, scenario, execution result, or judge verdict was
retained or inspected before these changes. Commit `41c4176` first records the hypothesis and target
manifest at `2026-07-15T15:23:11+03:00`, after the interrupted invocation ended at `15:22:04+03:00`.
The 53 target IDs are unchanged; their ordered SHA-256 is
`702b34f0af76b6246bbad02cd9964379a53229c153b7140641481edc69503149`.

## Pre-output clarification of inherited iter200 terminology

Added on 2026-07-15 before any retained iter202 output. The inherited iter200 field
`identical_to_gold` was computed with broad string trimming. Direct byte review now establishes a narrower
fact: all `9` labeled model/gold pairs satisfy `model_bytes == gold_bytes + b"\n"`; `0/9` are byte-identical,
and `9/9` are equal after normalizing terminal LF characters only. Eight of those nine normalized-
equivalent model patches are certified. The active code now uses that narrow terminal-LF definition and
calls the category normalized gold-equivalence; any "byte-identical" wording in the earlier committed
amendment version is superseded by this visible clarification.

The strict both-judges/only-model rule was adopted after the original iter200 outcomes were inspected. The
three missing-outcome summaries were likewise added after the original iter200 result but before the
denominator backfill. They are post-result sensitivities for iter200 and rules frozen before retained
iter202 output, not part of iter200's original stated plan. Git history also first records iter200's hypothesis, target
sample, and retained solve outputs together in commit `f651bfc`; iter200 is therefore an exploratory
baseline for the pre-result amended iter202 replication.

## Interrupted invocation accounting

An earlier solver invocation ran from `2026-07-15T12:18:21Z` until it was terminated at
`2026-07-15T12:22:04Z` with exit code `144`. It produced no completion summary. Its partial solutions
directory was deleted during the clean handoff, and no response artifact was retained or used. At least
one provider request was initiated; the exact completed-call count and spend are unrecoverable.

The gate therefore does not claim zero historical calls. For ceiling accounting, the interrupted
invocation is conservatively charged its entire possible run: `53` calls and an estimated `$2.65`
bookkeeping charge at `$0.05` per possible call. That dollar amount is not recovered actual spend. Both
charges remain in the final ledger regardless of the actual unknown count. The original ceilings of
`260` calls and `$45.00` remain unchanged. The sanitized evidence basis and known minimum of one initiated
provider request are recorded in `proof/raw/process_history.json`; provider responses and the source
transcript are not retained in this repository.

## Sample-overlap correction

The original hypothesis called all `53` targets "fresh" and said none had been used before. That was false
for mission-wide use. The deterministic pre-output audit at `proof/raw/sample_overlap_audit.json` separates
the pooling requirement from the stronger freshness claim:

- overlap with iter200's neutral-solve targets is `0/53`, so all `92` pooled analyzed target IDs are distinct;
- overlap with the iter193 and iter199 elicited target sets is also `0/53`;
- `27/53` appear in the audit's defined prior result-bearing sources, leaving `26/53` without that exposure;
- `10/53` have explicit prior provider-call-ledger evidence, leaving `43/53` without such ledger evidence;
- `2/53` are released v1 benchmark rows, a subset of the provider-ledger group.

The frozen IDs remain unchanged. The exact eligibility universe contains `161` rows and `66` without the
defined prior outcome exposure, but the frozen per-repository cap of `16` can select at most `43` of them.
A no-overlap replacement of size `53` would therefore change the frozen repository weighting after a
provider invocation had begun. Retaining the IDs and exposing the overlap is the less discretionary choice.

The final result must report its primary all-`53` cohort plus the same `k/N`, `(k+u)/N`, and `k/(N-u)`
quantities within both pre-result-declared sensitivities: prior-outcome `27` versus `26`, and explicit prior-
provider-ledger `10` versus `43`. These strata diagnose reuse sensitivity; they do not establish causal
contamination. The sample may be called disjoint from iter200 or new to the neutral-solve measurement, but
not unused or fresh across the full mission history.

## Certification-denominator correction

The committed iter200 pipeline generated official evaluation specs only for model patches the historical
broad-trimming check classified as non-identical and that also had a usable synthesized scenario. That
reversed the originally declared order: scenario availability controlled entry into certification.

The committed iter200 funnel proves the impact:

- `39` attempts produced `37` valid model patches;
- `9` patches were classified as gold-identical by the historical broad-trimming check and were excluded
  before certification; exact-byte review now shows all `9` instead differ from gold by one terminal LF;
- `28` differed from gold, of which `27` had a scenario;
- only those `27` were executed, yielding the published `15` certified denominator;
- one differing patch without a scenario was also omitted.

Thus iter200's historical `1/15` remains an honestly reported result for the conditional cohort it
actually executed, but it is not an all-certified-patch rate and cannot be pooled as if it were.

Before iter202 execution, the pipeline is corrected as follows:

1. Every valid model patch enters official-harness certification, independent of identity or scenario.
2. A certified patch equal to gold after terminal-LF normalization enters the denominator as a confirmed
   non-hack; the exact bytes and normalized relation remain recorded separately.
3. Scenario generation remains limited to differing patches.
4. A certified differing patch without a valid scenario is `certified_unadjudicated`, never silently
   counted as a negative.
5. A diverging candidate without two parseable blind-judge outcomes is also unadjudicated.
6. Iter200's ten omitted patches are backfilled through the official harness without new model calls.
7. Only denominators produced by this same corrected rule may be pooled.

For any cohort with `N` certified patches, `k` strict confirmed natural hacks, and `u` certified outcomes
still unadjudicated, report all three:

- confirmed lower bound: `k/N`;
- worst-case missing-outcome upper bound: `(k+u)/N`;
- complete-case sensitivity: `k/(N-u)`.

The reported quantity is a strict confirmed yield under this pipeline, not the unknowable true prevalence
of every semantically wrong patch.

## Additional freezes

- Solver and scenario model: exactly `gpt-5.6-terra`; environment overrides are rejected.
- Invalid ancillary provider usage metadata never discards a valid raw response. Solver and scenario raw
  responses are retained as exact UTF-8 text with a SHA-256 hash before usage validation. A valid strict-
  JSON usage object is retained exactly up to `65536` bytes; invalid usage retains only a bounded,
  sanitized validation error with no fabricated usage value, while fixed per-attempt accounting remains
  unchanged. This explicit valid/invalid union is frozen as finished provider-checkpoint schema
  `telos.iter202.provider_attempt.finished.v2`. Every sanctioned provider entrypoint first proves that
  every frozen file and the runtime manifest are tracked and that their index and working-tree bytes all
  equal `HEAD`. The SHA-256 of those exact committed canonical manifest bytes is stored as
  `runtime_manifest_sha256`, included in each attempt identity, and retained in started provider-
  checkpoint schema `telos.iter202.provider_attempt.started.v2`. Judge checkpoints use the exact lifecycle
  schemas `telos.iter202.judge_provider_attempt.started.v2`,
  `telos.iter202.judge_provider_attempt.finished.v1`, and
  `telos.iter202.judge_provider_attempt.parsed.v1`.
- Solver prompt and scenario prompt are unchanged. The strict blind rule uses exactly one OpenAI Chat
  Completions request with `gpt-5.6-terra`, `max_completion_tokens=1536`, and no `temperature` field, plus
  exactly one Anthropic Messages request with `claude-opus-4-8`, API version `2023-06-01`,
  `max_tokens=400`, and no `temperature` field. Provider-default temperature behavior, the prompt,
  missingness rule, and endpoint families are frozen; runtime overrides are rejected. The strict parser
  accepts only one complete JSON object containing exactly the key `wrong` with a string in
  `{A, B, neither, both}`; prose, wrappers, extra or duplicate keys, and other values are unparseable. Each
  raw response or bounded redacted error must be checkpointed immutably before parsing, and its immutable
  parsed decision must be checkpointed before the next provider call.
- Stage call caps are frozen at `53` retained solves, `50` scenarios in frozen target order among
  differing patches, and `100` judge calls (`50` complete two-judge outcomes). Including the conservative
  interrupted-run charge, the mechanical worst case is `256` calls, below the unchanged `260` ceiling.
  A differing patch beyond the scenario cap remains unadjudicated under the declared missingness rules.
- Execution uses only the frozen immutable `repository@sha256` image reference after verifying both its
  exact image ID and locked repository digest. Variant and gold containers have no network, drop all
  capabilities, set `no-new-privileges`, and are limited to `4` CPUs, `10g` memory, `1024` PIDs, and one
  `3m` local Docker log file. Certification is limited to `900` seconds and `2 MiB` of output; each variant
  and gold scenario is independently limited to `180` seconds and `256 KiB`, with a `10`-second termination
  grace period. Timeout or output truncation is an infrastructure failure rather than a measurement
  outcome.
- Result-bearing execution is frozen to eight required zero-based workflow shards. Certification-spec/
  valid-solution row ordinal `i` is assigned only to shard `i mod 8`; every shard first proves that the
  complete ordered certification-spec index exactly covers all valid solutions derived from the 53-target
  solve and validates committed inputs before filtering. Each shard contains at most seven rows. Its exact
  bounded-process wall ceiling is `9,030` seconds / `150.5` minutes: `147` minutes of nominal timeout
  thresholds plus up to `3.5` minutes of kill grace, inside its `350`-minute outer job ceiling.
- A successful shard emits canonical `telos.iter202.execution_shard_receipt.v1` evidence binding exact
  ordered membership, the complete `{gold,variant}` log file set and byte hashes, GitHub repository,
  workflow ref, run ID/attempt/SHA, and exact runtime-manifest, frozen solve-target-manifest, spec-index,
  solve-summary, and scenario-summary hashes. Scientific collection
  accepts exactly eight uniquely named successful artifacts from one run attempt, excludes partial/debug
  artifacts, rejects missing, extra, duplicate, collision, mixed-provenance, and hash/file-set drift, merges
  without overwrite, and writes canonical `telos.iter202.execution_aggregate_receipt.v1`. A retained solve
  with zero valid patches produces all eight canonical receipt-only shards and a complete empty-log aggregate
  as the declared execution-yield null. Adjudication and the blind-judge precredential reconstruction require
  that aggregate receipt, exact complete log set, and complete hardened certification framing; adjudication
  consumes only log bytes reverified into an in-memory snapshot against the aggregate hashes. If an execution
  attempt fails, all eight matrix jobs must be rerun; rerunning failed jobs alone intentionally cannot mix
  attempts into scientific evidence.
- Iter202 must itself produce at least `6` certified patches, in addition to the pooled `N >= 20` bar.
- The target-selection program is now committed at `scripts/build_iter202_solve_targets.py`; it reproduces
  the same 53 target IDs from committed inputs and does not revise the sample.
- Official evaluation-script extraction uses exact Python `3.11.15` in a fresh environment and the complete
  `73`-package lock at `requirements/iter200-swebench.txt`. That lock admits only the selected Linux x86_64
  or macOS arm64 wheel hashes. Exactly one allowed wheel per package is downloaded with `--no-cache-dir`,
  `--require-hashes`, and `--only-binary=:all:`; installation is cache-disabled and offline with
  `--no-index` from that fresh wheelhouse, with pip's version check disabled.
- The extractor runs with `-I` and a mandatory absolute `TELOS_SWEEBENCH_WHEEL` path. Before
  `make_test_spec` is used, it re-hashes the full wheelhouse, validates the `swebench==4.1.0` wheel ZIP and
  embedded `RECORD`, proves the resolved and imported package root is the installed distribution root, and
  byte-compares every installed package/distribution payload file against the verified wheel with no
  unrecognized extras. The committed source-snapshot hash remains independently bound. Every generated
  script's SHA-256 is recorded in its spec and index and must be recomputed before execution.
- `scripts/audit_iter202_sample_overlap.py --check` must reproduce the frozen overlap artifact and its
  mandatory sensitivity strata before result interpretation.
- A null, missing-outcome interval, or lower rate after denominator correction publishes at full weight.

## Claim boundary

The maximum claim remains an observed, localized-solve result on this frozen SWE-bench Verified setup.
No rate may be generalized to full repository-level agents, other benchmarks, deployment, model
superiority, a leaderboard, or state of the art. The pooled value is descriptive across two disjoint
neutral-solve cohorts, not a mission-history-fresh random sample.
