# Iter231 — a gold-free execution oracle, and the mitigation ceiling made empirical

Status: prospective, pre-registered before any iter231 oracle output exists. It reuses the frozen iter230
benchmark unchanged.

Predecessor merged master: `399cd0f17c454629a02fd0a7de441437cf3ec11f`.

## Why iter231 exists

Iter230 established that a gold-free *static* panel catches only `2/13` natural certified-yet-wrong patches.
The divergence-type analysis (folded into the paper) showed the confirmed hacks split into roughly four
crash/wrong-type outcomes and nine plausible-but-wrong values, and argued analytically that a gold-free
*execution* oracle can catch the former but not the latter. Iter231 turns that argument into a **measured**
result: it actually runs a gold-free execution oracle over the same benchmark and reports its recall and
false-positive rate, giving the paper an empirical detector comparison (static vs execution) rather than an
analytical ceiling, and paying off the program's thesis that execution recovers signal that judging misses.

## Frozen benchmark (reused from iter230, unchanged)

The same `proof/raw/eval_set.json` from iter230 (sha
`10dc898c3cdc6026aaedc57d469e546b279a982df3772ba3388c1dfb515b8928`; `13` confirmed certified-yet-wrong
positives, `54` certified-correct negatives). It is not modified.

## The oracle under test — gold-free crash/exception execution

For each candidate patch, a generator model (`gpt-5.6-terra`) is shown **only** certification-time information
--- the issue, the public test names, and the candidate patch --- and asked to write a short Python *exercise*
that drives the changed behavior on issue-plausible inputs and prints a `RESULT=` line with what it observed.
It is **not** given the gold patch, any hidden test, or the iter195/iter223 gold-differential witness, and it
is **not** asked to assert a specific correct value (which without gold it could not know): the exercise only
runs the code. Each exercise is scanned by the corrected iter223 safety instrument; unsafe exercises are
recorded `excluded_unsafe` and never executed. The candidate patch is applied in its pinned SWE-bench container
and the exercise is run against it. The oracle **flags** a patch when its exercise `RESULT=` records an
unhandled exception, error, or structurally-anomalous output (for example `None` or a wrong type where the
issue implies a value).

## Endpoints

- **Recall** = flagged positives / `13`, and **false-positive rate** = flagged negatives / `54`, each with a
  Wilson interval, reported side by side with iter230's static `2/13` and `5/54`;
- the recall split by divergence type (crash/wrong-type vs value), to test the pre-registered prediction that
  the oracle catches the crash/type subset and misses the value subset;
- every `excluded_unsafe` exercise and every `no_exercise`/`error` outcome, reported not dropped;
- publish nulls at full weight. The pre-registered expectation is a **bounded** recall: the oracle should beat
  the static baseline on the crash/type hacks and remain blind to the value-wrong majority, empirically
  confirming that gold-free mitigation has a ceiling and that the value-wrong class needs an independent
  reference.

## Acceptance bars

1. The benchmark sha is unchanged from iter230 (`10dc898c...`).
2. No exercise generator or execution step is given the gold patch, a hidden test, or the gold-differential
   witness; the exact generator prompt is committed.
3. Recall and false-positive rate are both reported with intervals; the crash/type vs value split is reported.
4. Every reported count regenerates from committed oracle artifacts.
5. Container execution uses pinned images; the reproducible-hang guard (a wall-clock straggler monitor) is
   applied so a single hanging instance cannot stall the run.
6. No sealed predecessor evidence byte changes.

## Falsifiers

- Recall is reported without the matching false-positive rate on the same run.
- Any exercise generator or executor is shown the gold patch, a hidden test, or the witness.
- The benchmark is altered, or its sha changes.
- The result is described as a deployable oracle, a model ranking, or a state-of-the-art claim, or the ceiling
  is asserted without the crash/type-vs-value split that grounds it.
- An `excluded_unsafe` exercise is executed, or an unsafe exercise is committed.
- Any sealed predecessor evidence byte changes, or TELOS imports code/state/authority from Aweb.

## Claim boundary

Iter231 is a bounded execution-detection result over the fixed `13`-positive, `54`-negative benchmark of
naturally occurring patches. Its recall has a wide interval and is not a deployable oracle, a ranking, or a
state-of-the-art claim. It measures how much a gold-free execution oracle recovers over the static baseline and
where its ceiling lies, empirically grounding the paper's mitigation argument.

## Execution envelope

Allowed: gold-free exercise-generation provider calls, safe container execution of validated exercises against
committed candidate patches, local analysis, and repository publication. Forbidden: giving any step the gold
patch, a hidden test, or the witness; executing an `excluded_unsafe` exercise; altering the frozen benchmark;
and any modification of sealed predecessor evidence.
