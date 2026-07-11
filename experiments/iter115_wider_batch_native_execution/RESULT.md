# Iteration 115 Result - Wider Batch Native Execution

Status: `PASS`.

## What this gate did

Scaled native hidden-test execution from five instances (iter114) to eighteen same-era Django 4.x
SWE-bench Verified instances, to tighten the native-harness fidelity estimate and re-confirm the
detector's zero-false-positive property on real executed gold. Each instance ran in SWE-bench order
(checkout base commit, apply gold, apply hidden `test_patch`, run FAIL_TO_PASS on Python 3.11).

## Result

- gold resolution rate under real execution: `17/18` = `0.94444444`
- native-harness fidelity gaps: `django__django-14349` (the same instance as iter114; gold applies
  clean but its test errors under the lightweight harness)
- detector false-positive rate on the eighteen real gold patches: `0/18` = `0.00000000`

The five-instance sample in iter114 put native fidelity at `0.80`; on eighteen instances it rises to
`0.94`, so the earlier estimate was pessimistic small-sample noise. Seventeen of eighteen real human
gold patches genuinely resolve their hidden tests under real execution, and the deterministic
detector flags none of the eighteen - the zero-false-positive property now rests on executed ground
truth across a batch, not a single case or the dataset label alone.

## Claim boundary

Supported: on eighteen same-era Django instances executed natively, `17/18` gold patches resolved
the real hidden test and the detector flagged `0/18` as tamper, with one enumerated native-harness
fidelity gap. Not supported: a benchmark, resolved-rate, model, or state-of-the-art claim, or a
fidelity number beyond this same-era Django sample.

## Next gate

`iter116`: measure the executed reward-hack catch rate per verifier - construct, per instance, a hack
that really passes the hidden test, then run execution-only, the detector, and the judge on each - to
turn the iter113 existence proof into a rate; and, where the native harness cannot run an instance,
scope the official Docker path.

## Evidence

- `proof/patches/` (eighteen real gold patch fixtures)
- `proof/native_execution_transcript.txt` (observed run)
- `proof/manifest.json`, `proof/endpoint_results.json`, `proof/run_summary.json`
- `proof/valid/receipt_wider_batch_native_execution.json`
- `scripts/run_wider_batch_native_execution.py`
