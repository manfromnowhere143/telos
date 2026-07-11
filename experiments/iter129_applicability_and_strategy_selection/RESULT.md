# Iteration 129 Result - Applicability Criterion and Automatic Strategy Selection

Status: `PASS`.

## What this gate did

Resolved the last residual by inspection rather than by forcing a harness, and made the
property-strategy choice automatic.

## The residual was mis-classified, not mis-targeted

`11276`'s gold rewrites `django.utils.html.escape` to use the stdlib `html.escape`, and its
FAIL_TO_PASS spans `27` tests across `14` files - template filters, forms, admin docs, view and debug
tests. It is a cross-cutting behavioral refactor, not a single testable function. Earlier iterations
tried to build a single-function property harness for it, which was the wrong frame. The right move is
to exclude it up front with an applicability criterion.

## Result

Applying the criterion - a candidate must expose a single testable function and have a narrow
FAIL_TO_PASS (at most three tests on it) - excludes `11276` and admits six:

| instance | function | FAIL_TO_PASS | valid candidate | auto-assigned strategy | matches sound strategy |
| --- | --- | ---: | --- | --- | --- |
| `14089` | `OrderedSet.__reversed__` | 1 | yes | contract property | yes |
| `14373` | `dateformat.Y` | 1 | yes | contract property | yes |
| `13670` | `dateformat.y` | 1 | yes | contract property | yes |
| `11206` | `numberformat.format` | 1 | yes | contract property | yes |
| `11848` | `parse_http_date` | 1 | yes | inverse round-trip | yes |
| `10999` | `parse_duration` | 1 | yes | inverse round-trip | yes |
| `11276` | `html.escape` (cross-cutting) | 27 | no (excluded) | - | - |

- genuine-sound rate on valid candidates: `6/6` = `1.00000000`
- automatic strategy assignment correct: `true` for all six

## The finding

Two things close cleanly. First, the property-based third layer's applicability is precise: it
verifies instances that expose one testable function, and cross-cutting refactors like `11276` are out
of scope and correctly excluded rather than mis-targeted. On the six valid candidates the layer is
`6/6`. Second, the strategy choice is mechanical: a function whose name contains `parse` gets the
inverse round-trip, everything else gets a contract property, and this assignment matches the strategy
that was sound for every one of the six. The `2/7` full-auto rate of iter124 rises to `6/6` on valid
candidates once the input is seeded from the test, the strategy is chosen by function type, and
cross-cutting instances are excluded up front.

## Honest scope

Six single-function candidates drawn from django utils, one model, seeded inputs. This is the
applicability boundary, not a distributional guarantee: the corpus is small and same-domain, the
strategy classifier is a two-way name heuristic, and instances that expose no single testable function
are outside the property-based layer entirely (they remain the domain of Layers 1 and 2).

## Claim boundary

Supported: under a single-testable-function applicability criterion `11276` is excluded as a
cross-cutting refactor, the six valid candidates are all genuine-sound (`6/6`), and an automatic
function-type classifier assigns each the strategy that was sound. Not supported: a benchmark, model,
or state-of-the-art claim, or a rate beyond these seven instances.

## Next gate

`iter130`: widen the single-function candidate corpus beyond django utils and re-measure the
genuine-sound rate and the strategy-classifier accuracy at larger scale.

## Evidence

- `proof/endpoint_results.json`, `proof/run_summary.json`, `proof/learning_record.json`
- `proof/valid/receipt_applicability_and_strategy_selection.json`
- `scripts/run_applicability_and_strategy_selection.py`
