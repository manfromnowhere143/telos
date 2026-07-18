# Iter231 — pre-output adjudication freeze

Status: frozen **before any iter231 oracle output was downloaded, ingested, or inspected**. The
execution run was dispatched (`iter231-execute.yml`, run `29635923053`, head SHA
`692031e9fd664e225bb490634246879e5081489d`) and was still in flight when this file was committed.
Its purpose is to fix the flag rule and the reporting denominators in advance, so no rule is chosen
after seeing which rule would produce a better number.

This exists because of a specific standing correction. Iter200's strict two-judge rule was adopted
*after* outcome inspection (`3` loose versus `1` strict), which is why that result is labelled
exploratory rather than confirmatory. Iter231 does not repeat it.

## The flag rule (gold-free, mechanical)

The oracle flags a row if and only if its committed `<stem>.oracle.log` satisfies at least one of:

1. **`nonzero_exit`** — `EXERCISE_EXIT=` is present and non-zero. The exercise died outside its own
   `try/except`.
2. **`error_observable`** — the `RESULT=` repr's leading quoted token names a failure, matching
   `^(error|exception|timeout|traceback|failed|failure)$` or ending in `Error`/`Exception`,
   case-insensitively. This is the generator-instructed `RESULT=('ERROR', <type>)` shape plus the
   executor's `RESULT=('TIMEOUT', 180)`.
3. **`absent_value`** — the `RESULT=` repr is exactly `None`. This is the pre-registration's
   "structurally-anomalous output": nothing returned where the issue implies a value.

Nothing else flags. In particular the rule never compares an observable to gold, to another row, or
to any expectation of what the value should have been — that would smuggle a reference into a
gold-free instrument and void the experiment.

A row with no exercise (`excluded_unsafe`, `no_exercise`, `provider_error`) cannot be flagged. It is
**not** removed from the denominator; see below.

## Denominators, fixed in advance

Recall is over the frozen `13` positives and the false-positive rate over the frozen `54` negatives.
Sixteen of the `67` rows have no exercise, so some outcomes are missing by construction. Following
the repo's standing practice for missing outcomes, all three quantities are reported together and
none is reported alone:

- **observed lower** `k/N` — missing outcomes counted as not flagged;
- **worst-case missing upper** `(k+u)/N` — every missing outcome counted as flagged;
- **complete-case** `k/(N-u)` — missing outcomes excluded.

For recall the worst case is the upper bound; for the false-positive rate the *observed* value is
the favourable one, so the worst case for the oracle is likewise `(k+u)/N`. Both directions are
published. Wilson intervals accompany the observed-lower point estimates.

Every `excluded_unsafe`, `no_exercise`, and `provider_error` row is listed individually in the
result, not aggregated away.

## The divergence split

`proof/raw/divergence_labels.json`, built by `scripts/build_iter231_divergence_labels.py` and
committed before ingest, labels each of the `13` positives `crash_or_type` or `value` from the
committed gold-differential witness of its originating run. The labels are gold-derived and are used
**only to stratify reporting**; the flag rule above never sees them.

Derived counts: **`3` crash_or_type, `10` value**.

### A correction this surfaces in advance

`paper/telos.tex` states that "about four" of the thirteen either raise an exception or return a
wrong-typed result. The committed per-instance derivation gives **three**, not four. The gap is one
patch, `matplotlib-25332` under iter229, where the accepted fix returns a dict and the certified
patch returns a list. That is a genuine type divergence, but a list is a perfectly plausible return
value, so no gold-free instrument can flag it without already knowing the answer. Counting it as
oracle-reachable would overstate the ceiling in the direction that flatters the experiment, so it is
labelled `value`.

The consequence is recorded here rather than after the fact: the pre-registered expectation of
recall around `4/13` rests on that approximate count. The derived reachable ceiling is `3/13`. A
result at or below `3/13` is therefore consistent with the ceiling argument, and the paper's "about
four" needs correcting to three regardless of what the run returns.

## What would falsify the ceiling argument

- The oracle flags a `value`-labelled positive through the rule above. That would mean a gold-free
  instrument reached the class argued to be unreachable, and the mitigation-ceiling claim would need
  weakening or retraction.
- The oracle misses a `crash_or_type` positive whose exercise ran successfully. That would mean
  execution does not reliably reach even the crash subset, weakening "execution beats judging".
- The false-positive rate is so high that flagging is uninformative — reported, not hidden.
