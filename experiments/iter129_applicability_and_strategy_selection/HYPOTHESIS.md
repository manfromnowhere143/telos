# Iteration 129 - Applicability Criterion and Automatic Strategy Selection

Status: pre-registered before evaluation. Frozen before the criterion and classifier were applied.

## Why this gate exists

Iter128 left `11276` as the last residual, called a "mis-targetable task." Inspecting it resolves the
question: its gold rewrites `django.utils.html.escape` to use the stdlib `html.escape`, and its
FAIL_TO_PASS spans many integration tests across template filters, forms, admin docs, and view tests -
not a single testable function. This gate refines the applicability criterion so such instances are
excluded up front rather than mis-targeted, and makes the property-strategy choice automatic.

## Method

1. Applicability criterion: a property-based candidate must expose a single testable function and have
   a narrow FAIL_TO_PASS (a small number of tests concentrated on that function). Apply it to the seven
   instances and record which are valid candidates.
2. Automatic strategy selection: classify each valid candidate's function as a parser/formatter with an
   inverse (name contains `parse`) versus a pure transform, and assign the inverse round-trip or the
   contract property accordingly. Check the assignment matches the strategy that was sound in
   iter122-iter128.

## Endpoints

- `valid_candidate_count` and which instances are excluded by the applicability criterion.
- `genuine_sound_rate_on_valid_candidates`.
- `strategy_assignment_correct`: whether the automatic classifier assigns every valid candidate the
   strategy that was sound.

## Acceptance / interpretation rule

If `11276` is excluded as a non-single-function instance and the remaining six are all genuine-sound
with correctly auto-assigned strategies, the property-based third layer is `6/6` on valid candidates,
and the applicability boundary is stated precisely: it verifies instances that expose one testable
function, not cross-cutting refactors.

## Falsifiers

1. If the applicability criterion excludes a genuine single-function candidate, it is too strict;
   record it.
2. If the automatic strategy classifier assigns a wrong strategy to any valid candidate, record the
   misassignment.

## Execution envelope

- pure evaluation over recorded results, no execution, no provider calls, no GPU, no cloud,
- production/live-domain mutation: forbidden, benchmark/model/SOTA claim: forbidden.

## Claim boundary (pre-committed)

At most: "under a single-testable-function applicability criterion, `11276` is excluded as a
cross-cutting refactor, the six valid candidates are all genuine-sound (`6/6`), and an automatic
function-type classifier assigns each the strategy that was sound." Not a benchmark, model, or SOTA
claim, and not a claim about instances beyond these seven.
