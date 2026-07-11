# Iteration 131 Result - Symbolic Property Evaluation and Docker-Harness Scoping

Status: `PASS`.

## What this gate did

Executed the first iter130 lever - symbolic property evaluation - and scoped the second, the Docker
harness, as next-phase infrastructure.

## Symbolic evaluation removes the numeric artifact and is stronger

Each of the four hyperbolic identities was evaluated with a free `Symbol` via exact simplification
instead of numeric sampling:

| identity | `simplify(expr)` | sound |
| --- | --- | --- |
| `coth(-x) + coth(x)` | `0` | yes |
| `coth(x)*tanh(x) - 1` | `0` | yes |
| `cosh(-x) - cosh(x)` | `0` | yes |
| `cosh(x)**2 - sinh(x)**2 - 1` | `0` | yes |

- numeric result (iter130): `3/4`, with one float-precision false positive
- symbolic result: `4/4`, exact

Symbolic evaluation is not only more precise; it is a stronger check. A numeric harness samples
inputs and can miss a defect between samples or flag a precision artifact; symbolic simplification to
zero proves the identity holds for all `x`. For functions that support it, symbolic evaluation is the
correct property oracle.

## Docker-harness scope (recorded, not built)

The remaining scale lever is environment fidelity. The official SWE-bench Docker harness provides
pinned per-instance Python and dependencies, which resolves the failures measured natively: iter114's
`~0.94` same-era django fidelity, iter124's harness failures, and iter130's pre-3.10 sympy instances
that import removed stdlib and cannot run on Python 3.11. Its cost is a multi-GB image per instance
and x86 emulation on arm64 - a focused build, scoped here as next-phase infrastructure and not
implemented in this gate.

## The finding

Two of the layer's known weaknesses are now addressed: numeric imprecision is removed by symbolic
evaluation (adopted, `4/4`), and environment fidelity has a named resolution (the Docker harness,
scoped). What remains is engineering, not open research: prototype the Docker harness on one blocked
instance, and route symbolic-capable functions to symbolic evaluation.

## Claim boundary

Supported: symbolic evaluation makes `4/4` identities exactly sound, removing the numeric artifact and
proving each for all `x`; the Docker harness is scoped as the path to running the
environment-fidelity-blocked instances. Not supported: a benchmark, model, or state-of-the-art claim,
or a claim that the Docker harness is built.

## Next gate

`iter132`: prototype the official SWE-bench Docker harness on one environment-fidelity-blocked
instance to confirm it runs where the native harness cannot.

## Evidence

- `proof/symbolic_results.json` (observed symbolic simplifications on real sympy)
- `proof/endpoint_results.json`, `proof/run_summary.json`, `proof/learning_record.json`
- `proof/valid/receipt_symbolic_evaluation.json`
- `scripts/run_symbolic_evaluation.py`
