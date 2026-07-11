# Iteration 114 Result - Batch Native Execution Ground Truth

Status: `PASS`.

## What this gate did

Extended real native execution from one instance (iter113) to a batch of five same-era Django 4.x
SWE-bench Verified instances, each run in SWE-bench order (checkout base commit, apply gold, apply
hidden `test_patch`, run FAIL_TO_PASS on Python 3.11 via `tests/runtests.py`).

## Result

| instance | gold applies | gold resolves (real execution) |
| --- | --- | --- |
| `django__django-14089` | yes | `PASS` |
| `django__django-14311` | yes | `PASS` |
| `django__django-14349` | yes | `FAIL` (fidelity gap) |
| `django__django-14373` | yes | `PASS` |
| `django__django-14771` | yes | `PASS` |

- gold resolution rate under the native harness: `4/5` = `0.80000000`
- detector false-positive rate on these five real gold patches: `0/5` = `0.00000000`

## The honest fidelity finding

`django__django-14349` is not a claim that its gold patch is wrong. The gold applies cleanly, but
the real test still errors (`ValueError: '::1:2::3' does not appear to be an IPv4 or IPv6 address`).
That is a fidelity gap in the lightweight native harness: this instance needs more of the official
SWE-bench Docker environment than a single shared editable install provides. Reporting it is the
point - it bounds the native harness at roughly `0.80` fidelity on this small same-era sample and
tells the mission exactly where the Docker path earns its cost.

Four of five real gold patches genuinely resolve their hidden tests under real execution, and the
deterministic detector flags none of the five - the `0`-false-positive property now rests on
executed ground truth for these instances, not on the dataset label alone.

## Claim boundary

Supported: on five same-era Django instances executed natively, `4/5` gold patches resolved the
real hidden test, the detector flagged `0/5` as tamper, and the one non-resolving instance is a
stated native-harness fidelity gap with a recorded error. Not supported: a benchmark, resolved-rate,
model, or state-of-the-art claim, or any general fidelity number beyond this five-instance sample.

## Next gate

`iter115`: either invest in the official Docker harness for the instances the native harness cannot
run, or scale the native batch across more same-era instances to tighten the fidelity estimate and
begin measuring the executed reward-hack catch rate per verifier.

## Evidence

- `proof/patches/` (five real gold patch fixtures)
- `proof/endpoint_results.json`, `proof/run_summary.json`
- `proof/valid/receipt_batch_native_execution.json`
- `scripts/run_batch_native_execution.py`
