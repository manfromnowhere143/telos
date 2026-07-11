# Iteration 139 - Property Derivability Within the Applicable Set

Status: pre-registered design; executed on the sympy applicable subset.

## Why this gate exists

Iter138 measured structural applicability (single testable function) at `0.81` across the dataset and
flagged it as an upper bound, because an applicable instance still needs a function with a derivable
gold-free property. This gate turns the upper bound into a property-derivability estimate for the
highest-applicability, property-proven repo (sympy), and cross-checks it against the instances actually
verified.

## Method

Over sympy's structurally-applicable instances, classify each by whether its source function lives in a
property-rich domain - `functions/elementary`, `functions/special`, `functions/combinatorial`,
`geometry`, core arithmetic (`core/numbers|power|mul|add|expr`), or `ntheory` - where clean gold-free
metamorphic identities are derivable, versus a structural domain (matrices, sets, polys, printing,
solvers) where they are not readily derivable. Report the property-rich fraction as a
derivability estimate, and confirm the three verified instances (coth, Min, Point.distance) fall in the
property-rich domain.

## Endpoints

- property-derivability estimate = property-rich domain count over applicable count, for sympy.
- confirmation that every verified property-sound instance is in the property-rich domain.

## Acceptance / interpretation rule

The estimate is a domain heuristic, not a verified rate. It is accepted as an estimate if the three
verified instances all fall in the property-rich domain (the heuristic does not exclude a known-derivable
case). The finding is the sharpened bound: structural applicability is broad but property-derivability is
narrow even in a math-heavy repo, so Layer 3 has a narrow natural domain while Layers 1-2 apply
universally.

## Falsifiers

1. If a verified property-sound instance is not in the property-rich domain, the heuristic is too strict;
   record it.
2. The estimate is a heuristic; it must not be presented as a verified property genuine-sound rate.

## Execution envelope

- dataset analysis only, no execution, no provider calls, no GPU, no cloud,
- production/live-domain mutation: forbidden, benchmark/model/SOTA claim: forbidden.

## Claim boundary (pre-committed)

At most: "within sympy, a domain heuristic estimates property-derivability at N/M of the applicable
instances, with all three verified instances in the property-rich domain; Layer 3's natural domain is
narrow (math-identity functions) even where structural applicability is high." Not a benchmark, model,
or SOTA claim, and not a verified derivability rate.
