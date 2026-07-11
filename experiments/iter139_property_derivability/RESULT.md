# Iteration 139 Result - Property Derivability Within the Applicable Set

Status: `PASS`.

## What this gate did

Turned the iter138 structural-applicability upper bound (`0.81`) into a property-derivability estimate
for sympy, the highest-applicability and property-proven repo, and cross-checked it against the
instances actually verified.

## Result

Over sympy's `67` structurally-applicable instances, `7` live in a property-rich domain -
`functions/elementary`, `functions/special`, `functions/combinatorial`, `geometry`, core arithmetic, or
`ntheory` - where clean gold-free metamorphic identities are derivable.

- property-derivability estimate (sympy): `7/67` = `0.1045`
- all three verified instances (coth, Min, Point.distance) fall in the property-rich domain: `true`

The heuristic is validated where it matters: every instance for which a gold-free property was actually
built and shown sound in a pinned container sits inside the property-rich domain the heuristic marks.

## The finding - the sharpened bound

The two numbers together give the honest picture of where the property-based layer works:

- structural applicability (single testable function) is broad: `0.81` of the whole dataset (iter138).
- property-derivability is narrow: even in sympy, the most math-heavy repo, only `~0.10` of applicable
  instances are in a property-rich domain.

So Layer 3's natural domain is math-identity functions - elementary and special functions, geometry,
arithmetic - not the structural and algorithmic majority (matrices, sets, polynomials, printing,
solvers). This is not a weakness to hide; it is the honest three-layer division of labour: the
deterministic detector and the LLM judge (Layers 1-2) apply universally to any diff, and the gold-free
property layer (Layer 3) is the specialist that recovers the both-miss class precisely where a function
admits a checkable identity.

## Claim boundary

Supported: within sympy, a domain heuristic estimates property-derivability at `7/67` = `0.1045` of the
applicable instances, with all three verified instances in the property-rich domain; Layer 3's natural
domain is narrow (math-identity functions) even where structural applicability is high. Not supported: a
benchmark, model, or state-of-the-art claim, or a verified derivability rate - the estimate is a domain
heuristic.

## Next gate

`iter140`: record the narrow-derivability finding in the paper's limitations and frame the three-layer
division of labour explicitly - Layers 1-2 as universal coverage, Layer 3 as the math-domain specialist.

## Evidence

- `proof/derivability.json` (frozen domain classification of sympy applicable instances)
- `proof/endpoint_results.json`, `proof/run_summary.json`, `proof/learning_record.json`
- `proof/valid/receipt_property_derivability.json`
- `scripts/run_property_derivability.py`
