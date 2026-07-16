# Iter219 result — temporal consequence-test yield

Status: **NULL**. Sealed bar `2` fails. The screen finds no temporal signal.

Published at full weight under Standard 2. No sample rule, window, seed, qualification rule, or bar was
changed after observation.

## Result

Among `482` included SWE-bench Verified instances, test functions added within `365` days after a task's base
commit reference the task's touched symbols at `0.4066` (`196/482`, Wilson `95%` `[0.3637, 0.4511]`).

That number is meaningless on its own, and the two controls are why.

| Comparison at `Δ = 365` | Yield | Difference | One-sided exact conditional McNemar | Bar |
| --- | --- | --- | --- | --- |
| Primary (tests added after the task) | `0.4066` | — | — | — |
| Cross-repository control (`A2` v1) | `0.1660` | `+0.2407` | `p = 3.48e-24` | passes |
| Backward within-repository control (`A2` v2) | `0.4336` | `−0.0270` | `p = 0.925` | **fails** |

Tests added **before** the task existed reference its symbols slightly **more often** than tests added after.
Tests written before a fix cannot be consequence tests for it. The `0.4066` is therefore the repository's
baseline rate at which its own test suite mentions any given function, not evidence that later tests target
the task.

## The cross-repository control manufactured a false positive

Against the originally sealed v1 control alone, this experiment reports `0.4066` versus `0.1660`, a
`+24` percentage-point effect at `p = 3.48e-24`, with `132` discordant pairs favouring the primary and `16`
against. That is a result any reader would accept.

It is an artifact. Django symbols do not appear in SymPy tests for trivial vocabulary reasons, so the v1
control estimates "are these identifiers repository-specific", never "do later tests target this task". The
`A2` amendment predicted exactly this failure mode and was recorded before any instance was scored. Without
it, this repository would have published a false positive carrying a `10^-24` p-value.

The lesson generalises beyond this gate: **a control that cannot fail for the right reason manufactures
significance.** The p-value measured the control's weakness, not the hypothesis's strength.

## The null is not an exposure artifact

`L1` predicted that repositories mature, so forward windows would contain more added tests than backward
windows and inflate the forward side. **That prediction was wrong, and the recorded diagnostic shows it.**

| `Δ` | Forward added tests | Backward added tests | Ratio |
| --- | --- | --- | --- |
| `90` | `87,183` | `89,123` | `0.978` |
| `180` | `174,998` | `183,321` | `0.955` |
| `365` | `346,402` | `367,584` | `0.942` |
| `730` | `646,234` | `718,176` | `0.900` |

Exposure is close to balanced and, where it is not, it favours the **backward** side by `6%` at the primary
window while the backward yield exceeds the forward yield by `2.7` percentage points. The comparison is fair.
No instance had zero tests on either side. The null therefore reflects the absence of a temporal signal
rather than an imbalance in how many tests each side had to match against.

## Why the instrument is saturated

The median included instance touches exactly `1` symbol (`symbol_count_median = 1.0`) and its primary window
offers roughly `800` added tests (`forward_added_tests_median = 819.5`). Asking whether *any* of ~`800` tests
mentions one function name returns true about `40%` of the time regardless of intent, and returns true at the
same rate in both temporal directions.

The screen has a `~40%` noise floor and near-zero discriminating power at this granularity. A handful of
genuinely targeted consequence tests would be invisible inside it. The yield grows monotonically with window
size on both sides (`0.25 → 0.48` forward, `0.26 → 0.53` backward) because a wider window simply supplies
more tests, which is the behaviour of an exposure counter, not of a detector.

This extends `L4`. The pre-registered concern was **insensitivity**: real consequence tests exercise changed
code through a public API and never name the internal symbol. The observed failure is **non-specificity**: the
baseline vocabulary rate swamps any signal. Both point the same way. Symbol-name overlap at "any added test in
the window" granularity cannot answer this question.

## Bars

| Bar | Requirement | Observed | Verdict |
| --- | --- | --- | --- |
| 1 | `Y(365) ≥ 0.20`, Wilson lower `≥ 0.10` | `0.4066`, lower `0.3637` | pass |
| 2 | Primary beats **both** controls, `p < 0.01`, diff `≥ 0.10` | cross-repo passes; backward `−0.0270` at `p = 0.925` | **fail** |
| 3 | No repository above `50%` of qualifying instances | `0.4439` (django) | pass, uninformative |
| 4 | Symbol extraction `≥ 90%` | `1.0` | pass |
| 5 | Every exclusion reported by exact reason | `18/18` | pass |
| 6 | Reproduces from committed instrument and recorded SHAs | yes | pass |
| 7 | No provider, GPU, container, or repository test execution | all zero | pass |

Bar `2` fails, so the screen is a null. Bar `3` passes and is uninformative exactly as `L3` recorded before
observation: django is `231/500` of the sample and contributes `44.4%` of hits, which is approximately its
sample share.

## Sample and missingness

`500` instances seen, `482` included, `18` excluded, every exclusion by exact machine-readable reason:

- `15` `no_enclosing_symbol` — the gold patch changes only module-level code, so no enclosing definition exists;
- `3` `window_commit_unresolvable` — no first-parent commit at the window boundary descends from the base commit.

Symbol extraction succeeded on `100%` of included instances. No instance was dropped for a discretionary
reason, and no absence was scored as either a zero or a one.

## What this establishes, and what it does not

This falsifies **static symbol-name matching as a detector of temporal consequence-test targeting**. That
instrument is dead at this granularity and should not be rebuilt.

Per the inference rule fixed in `proof/analysis_amendment.json` before any observation, this result does
**not** falsify the underlying idea that maintainers' later-added tests could serve as independently authored
hidden consequence tests. This screen cannot see a consequence test that drives changed code through a public
API without naming the changed symbol, and `psf__requests-1142` was verified as exactly that shape before any
aggregate existed. A null here must not be reported as evidence that maintainer consequence tests are absent,
and does not by itself justify purchasing human annotators.

It establishes no model behaviour, no benchmark score, no effect estimate for any completion-verification
gate, no claim about TCP-1's admission, and no rate for any population. SWE-bench Verified's `12`
repositories are a nonrandom sample of mature Python projects. The gold patch stands in for the task's code
region because no agent patch exists; that proxy is a limitation, not a finding.

The question of whether harvested tests can supply TCP-1's hidden consequence evidence remains open and
requires an instrument that observes executed coverage rather than token overlap. That is a separate,
container-bound gate. This iteration does not authorize it.

## Zero-action boundary

`0` provider or model requests, `0` GPU allocations, `0` accelerator-hours, `0` scientific containers, `0`
repository test executions, `0` trajectories, `0` workflow dispatches, `0` payments, `0` releases, and `$0.00`
spent. The instrument performed read-only public dataset retrieval and read-only repository clones pinned to
recorded head SHAs.

Iter219 contributes no scientific `N`, `k`, `u`, benchmark score, effect estimate, model comparison,
population estimate, or deployment claim to TCP-1. TCP-1 admission remains `2/11` gates with `9` blocked and
`execution_authorized=false`. Iter212 remains unchanged and inactive.

## Reproduction

```bash
python3 scripts/measure_iter219_temporal_yield.py
python3 scripts/validate_iter219_temporal_consequence_test_yield.py
python3 scripts/build_iter219_receipt.py --check
```

Dataset `princeton-nlp/SWE-bench_Verified` split `test`, rows SHA-256
`449d9a59a9db191930249eead5ee01193441b945d000bf9c66ac27c1828adc09` as recorded in
`proof/yield_report.json`, with each repository's analyzed head SHA recorded in the same file.

## Next gate

The honest successor is not a retuned version of this screen. Token overlap has been falsified at this
granularity, and widening or narrowing its threshold would be fitting the instrument to a known answer.

An executed-coverage gate — running a later-added test against the task's base commit and its gold patch and
observing whether the changed lines are exercised and whether the verdict differs — would answer the question
this screen could not. It requires containers and per-instance environments, is materially more expensive than
this iteration, and is not authorized here.
