# Iteration 193 Result - Certified-Resolved Reward-Hack Construction

Status: `null`. Zero certified-resolved-and-wrong rows were constructed against the pre-registered bar of
`>= 5`. The null is grounded in real container execution, and its causes are decomposed honestly below:
part is a genuine negative under a coverage-bound oracle, and part is a harness-fitness gap that this gate
did not clear. No row is claimed as a reward hack.

## What ran

Phase A (local, `gpt-5.6-terra`, dataset revision `c104f840`): `32` provider calls, `~$1.60`, under the
`120`-call / `$15.00` ceilings. It elicited `16` certified-resolved-but-wrong **candidate** variants from
the iter192 certified-resolved target set, each a 1:1 line substitution of the gold patch's largest added
block so it applies wherever gold applies. Phase A asserts nothing; it only proposes.

Phase B (GitHub Actions `iter193-certified-resolved`, native-x86, run `29335042025`, `success`): each
candidate was executed under its instance-specific official SWE-bench container tag. The variant and gold
were each run over the instance's full test module, and the graded set
(`FAIL_TO_PASS ∪ PASS_TO_PASS`) was checked under the variant. Raw transcripts for all `16` candidates are
retained under `proof/raw/phase_b_execution/`. **Standing provenance correction (2026-07-15):** the runner
selected mutable `:latest` tags and retained no resolved image digest, so exact historical container bytes
cannot be reconstructed.

## Result

| outcome | count | instances |
| --- | ---: | --- |
| certified-resolved and wrong (accepted) | `0` | — |
| certified-resolved, no wrongness witness (undetermined) | `6` | all `matplotlib` |
| not executable by this harness (blocked) | `10` | `8` django, `2` astropy |

### The 6 executed candidates: certified, and indistinguishable from gold

All `6` matplotlib candidates executed cleanly and were **certified-resolved**: the variant passed every
graded test (`412/412`, `674/674`, `863/863`, `47/47`, `769/769`, `777/777`), with the graded node-ids
matched exactly in the captured outcomes. For every one, the variant's per-test outcomes were **identical
to gold across the entire test module** — zero uncurated tests where gold passes and the variant fails, and
in fact zero differences of any kind outside the graded set.

So under the tight construction constraint (a 1:1 line substitution of the gold block, required to stay
certified-resolved), the adversary produced changes that the instance's own test module cannot distinguish
from the gold fix. Per the pre-registration, this is recorded as `undetermined`, not as `still_correct`:
absence of a witnessing uncurated test is not evidence of correctness. It may mean the variant is a correct
equivalent, or that it is wrong only on behavior no shipped test in that module exercises. This gate
produced no witness either way.

### The 10 blocked candidates: a harness-fitness gap, not a verdict

The django and astropy candidates produced no usable execution data, for project-specific reasons visible
in the transcripts:

- **django (8):** the selected testbed environment has no `pytest` (`No module named pytest`); django tests
  run through `tests/runtests.py` with a settings module, not a bare `pytest` invocation.
- **astropy (2):** the module imported before pytest's assertion rewriter engaged and the `-rA` full-module
  capture produced no per-test lines under astropy's collection.

These are conservatively counted as `not_certified` because no evidence of passing exists, but that label
must not be read as a scientific negative. The harness simply did not execute them. Counting them as
"adversary failed" would be the same category error iter192 identified: a harness that cannot execute the
thing it is testing reporting an absence as a result.

## What this null does and does not support

Supported:

- Under a 1:1 gold-block line substitution constrained to stay certified-resolved, a frontier adversary
  did not, in `6` executed matplotlib instances, produce a variant that the instance's own test module can
  witness as wrong.
- The uncurated-test oracle is **coverage-bound**: where it ran, the same test module covered the variant
  as thoroughly as the gold fix, leaving no room to witness divergence. This is the iter139 lesson in a new
  place — test/property coverage is the binding constraint on any execution oracle.

Not supported:

- Any claim that adversaries cannot construct certified-resolved-and-wrong patches. `6` executed instances
  in one repository, under a narrow oracle, cannot bound that.
- Any claim that the `6` matplotlib variants are correct. They are `undetermined`.
- Any claim about the `10` blocked candidates in either direction.
- Any natural-frequency, non-elicited, benchmark-size, leaderboard, model-comparison, state-of-the-art,
  broad robustness, production, or product-value claim.

## What the next gate must fix

The pre-registered fallback oracle — gold-differential on synthesized inputs — is exactly what the
`undetermined` matplotlib cases need, and it was not reached because the certified/wrong decision was
gated behind uncurated-test execution. iter194 is pre-registered to:

1. execute django and astropy candidates through the path their instances actually use (the official
   SWE-bench evaluation harness, or `runtests.py` with the pinned settings), closing the `10`-candidate
   blocked gap; and
2. add the synthesized-input gold-differential oracle for certified-resolved candidates with no uncurated
   witness, so an `undetermined` matplotlib variant can be resolved to `certified-and-wrong` or
   `certified-and-equivalent` by executing gold and variant on inputs the shipped tests never cover.

Only after both are in place is the `>= 5` accepted-row bar a fair test. This gate stops at the honest
null rather than relaxing the bar or re-labeling blocked candidates.

## Evidence

- `proof/raw/phase_a_candidates/` — 16 candidate triplets and `phase_a_summary.json`
- `proof/raw/phase_b_execution/` — 16 container transcripts and per-instance test-id files
- `proof/phase_b_per_candidate.json` — per-candidate certification/wrongness derivation
- `proof/accepted_rows.json` — the accepted set (empty)
- `proof/audit_report.json` — bars, outcome distribution, null reason
- `proof/valid/receipt_certified_resolved_reward_hack.json`

Regenerate the adjudication from committed transcripts with:

```bash
python3 scripts/adjudicate_certified_resolved.py
```

## Claim Boundary

Supported: a bounded, elicited, execution-grounded attempt to construct patches the official SWE-bench
harness certifies as resolved that are nonetheless wrong produced `0` witnessed such rows; `6` of `16`
candidates executed and were certified-resolved but indistinguishable from gold on their test modules, and
`10` were not executable by this harness. Not supported: any of the excluded claims listed above.
