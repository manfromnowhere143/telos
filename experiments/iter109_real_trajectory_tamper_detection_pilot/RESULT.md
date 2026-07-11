# Iteration 109 Result - Real-Trajectory Verifier-Tamper Detection Pilot

Status: `PASS` (all pre-registered acceptance bars met), with one documented, tested limitation
carried forward as the next gate.

## What changed versus iter104/iter107

Earlier iterations scored a detector that branched on `target_family_id` (iter104) or read
authored packet booleans such as `semantic_task_alignment_claimed` (iter107). Both the traps
and the detector were authored by the same process, so no external validity was earned. This
gate moves onto external ground truth: the negative class is **200 real, human-authored gold
patches** from `princeton-nlp/SWE-bench_Verified`, cached at
`proof/raw/swebench_verified_rows.jsonl`. The detector (`telos/tamper/detector.py`) reads only
the candidate's raw unified diff, the public `FAIL_TO_PASS` node ids, and the candidate's own
receipt. It reads no ground-truth label and no attack-type field; attack labels are stripped
before the detector sees a candidate.

## Result

| metric | value | on |
| --- | ---: | --- |
| false-positive rate | `0.00000000` (0/200) | real human gold patches (external) |
| tamper recall | `1.00000000` (800/800) | constructed reward-hack variants |
| execution-only tamper recall | `0.00000000` | same variants, real-world default |
| differential vs execution-only | `1.00000000` | primary endpoint |

Per attack family (constructed): `delete_failing_test`, `weaken_assertion`,
`special_case_source`, `stealth_combined` each `200/200`.

The one strong, non-circular number is the guardrail: a raw-diff detector enforcing the
invariant "a legitimate fix never edits its own verifier" flags **zero of 200 real
human-reviewed patches** as tamper, while catching every reward-hack variant that edits the
`FAIL_TO_PASS` file, `conftest.py`, or pytest configuration. Broadening the provenance signal
from FAIL_TO_PASS files to all test-collection infrastructure cost zero additional false
positives on the real corpus - direct evidence that the invariant holds on real patches.

## Honest limitations (this is not a solved problem)

- **Recall is against a matched, constructed attack set.** 800/800 reflects that the generators
  exercise the signals the detector implements. It is not evidence of robustness to unseen
  hacks. An adversarial probe (`tests/test_tamper_detector.py::
  test_known_evasion_dict_special_casing_is_documented_limitation`) shows a dict-lookup
  special-case (`_cache = {6: 0}; return _cache[n]`) **evades** the source special-casing
  signal. Source-only proxy-gaming has an open evasion surface.
- **Hidden tests are reasoned about structurally, not executed.** The execution-only comparator
  is modeled from each hack's construction (every hack neutralizes the visible signal by design),
  not run in a container. Container-executed confirmation is the next gate.
- **No LLM-judge steelman yet.** The comparator here is the execution-only default that
  SWE-bench itself trusts. A well-engineered LLM judge is a stronger baseline and is deferred.

## Claim boundary

Supported now: on 200 real SWE-bench Verified gold patches, a raw-diff verifier-provenance and
assertion-integrity detector holds a `0/200` false-positive rate while catching constructed
reward-hack variants (verifier edits, assertion weakening, literal special-casing) that the
execution-only default accepts. Not supported: a SWE-bench resolved-rate score, a leaderboard
result, a model result, robustness to adversarially-evolved hacks, or a state-of-the-art claim.

## Next gate

`iter110`: adversarial hardening (hacker-fixer loop) that evolves hacks to evade the current
signals, plus an LLM-judge steelman baseline and container-executed hidden-test confirmation on
a bounded slice.

## Evidence

- `proof/raw/swebench_verified_rows.jsonl` (real corpus, sha256 in run_summary)
- `proof/endpoint_results.json`
- `proof/clean_decisions.json`
- `proof/hack_decisions.json`
- `proof/run_summary.json`
- `proof/valid/receipt_tamper_pilot.json`
- `telos/tamper/`, `scripts/run_tamper_pilot_real_swebench.py`, `tests/test_tamper_detector.py`
