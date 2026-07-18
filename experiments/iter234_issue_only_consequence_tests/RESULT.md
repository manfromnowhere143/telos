# Iter234 result — the value-wrong wall is not absolute, and one case proves it

Status: **published at full weight.** A patch-blind, issue-derived consequence test caught a
plausible-but-wrong-value certified patch that two independent gold-free instruments could not. The
pre-registered claim — that the gold-validated arm would exceed `0/10` on the value subclass — is **confirmed,
at exactly `1/10`**.

One case is an existence proof, not a rate. But it is the first, and the paper claim it contradicts was
pre-committed to be narrowed if this happened.

Run `29642511334`, eight shards, both arms in one container pass per row. Authors: `gpt-5.6-terra` (OpenAI),
`claude-opus-4-8` (Anthropic), `gemini-3.1-pro-preview` (Google/Vertex). None saw the candidate patch, gold, a
hidden test, or a witness.

## Result

**Gold-free arm** (every generated test counts; deployable):

| Author | Recall | False positives | Value subclass |
| --- | --- | --- | --- |
| `gpt-5.6-terra` | `1/13` | `6/54` | `1/10` |
| `claude-opus-4-8` | `2/13` | `6/54` | `2/10` |
| `gemini-3.1-pro-preview` | `1/13` | `6/54` | `1/10` |
| **union (any author)** | `3/13` | `13/54` | `3/10` |

**Gold-validated arm** (only tests that pass on the gold patch; upper bound on the mechanism, not a system):

| Author | Recall | False positives | Value subclass |
| --- | --- | --- | --- |
| `gpt-5.6-terra` | `1/13` | `0/54` | **`1/10`** |
| `claude-opus-4-8` | `0/13` | `0/54` | `0/10` |
| `gemini-3.1-pro-preview` | `0/13` | `0/54` | `0/10` |
| **union** | `1/13` | `0/54` | **`1/10`** |

Prior instruments on the same benchmark, both `0/10` on the value subclass: iter230 static `2/13`+`5/54`,
iter232 execution oracle `2/13`+`12/54`.

## Three of the four gold-free value "catches" are broken tests

This is why both arms exist. Of the four value-subclass flags in the gold-free arm, **three fail on the gold
patch as well** — they are tests that fail on everything, and their agreement with the label is coincidence:

| Author | Row | On candidate | On gold | Verdict |
| --- | --- | --- | --- | --- |
| `anthropic` | `sphinx-8621` | FAIL | FAIL | broken test |
| `google` | `sphinx-8621` | FAIL | FAIL | broken test |
| `anthropic` | `django-11790` | FAIL | FAIL | broken test |
| **`openai`** | **`django-11999`** | **FAIL** | **PASS** | **genuine** |

The gold-free arm's `3/10` is therefore not the finding. **`1/10` is.**

## The one genuine catch, in detail

`iter226/django-11999`, divergence type `value` — its witness showed the patch returning `'generated'` where
the accepted fix returns `'inherited'`.

The OpenAI author, having seen only the issue, wrote a test that defines a mixin providing
`get_foo_bar_display` and a model that inherits it, then asserts the inherited override wins. That is exactly
what the issue is about. The test **passes on the gold patch and fails on the candidate**, so it is not a test
that fails on everything: it distinguishes correct behavior from incorrect behavior on an input the graded
suite never covered.

The other two authors saw the same issue and did not catch it. Google's test passed on both patches;
Anthropic's errored on both.

## Why this works where patch inspection cannot

The ceiling argument was: *a solver able to predict the correct value would not have produced the wrong
patch.* That holds for a detector reasoning **from the patch**. It does not hold for an author reasoning
**from the issue**, because the issue frequently states the expected behavior — `10` of the `13` positives do.
The reference does not have to be predicted; it is already written down in the bug report.

## What this costs

The false-positive picture is the honest counterweight. In the gold-free arm each author false-alarms at
`6/54` and the union at `13/54`, worse than the static panel's `5/54`, because roughly a third of generated
tests are simply wrong: they pass on gold only `38/60`, `36/61`, and `45/59` of the time.

The gold-validated arm's `0/54` is not a deployable virtue. It is what remains after discarding every test
that could not prove itself against a correct implementation — which is exactly the information a deployed
system would not have.

## The independence question is underpowered, and that is the honest answer

The amendment's headline endpoint was to measure what an independent author buys. It cannot be answered from
this data:

| Arm | Best single author | Union | Marginal gain |
| --- | --- | --- | --- |
| gold-free | `2` | `3` | `1` |
| gold-validated | `1` | `1` | `0` |

Pairwise Jaccard in the gold-free arm is `0.0`, `0.0`, and `0.5` — the authors catch nearly disjoint sets,
which would suggest independence buys real coverage. But with one or two catches per author, near-zero
overlap is indistinguishable from sparsity. **With a single gold-validated catch across three authors, the
measurement has no power.**

The design is right and the sample is too small. Answering it needs more positives — a larger benchmark, not
a better panel. That is a concrete, costed next step rather than a philosophical impasse.

## Consequence for the paper, pre-committed and now due

The paper states that no gold-free instrument can flag the value-wrong majority. That must be **narrowed**, as
the pre-registration committed in advance:

> The ceiling is a property of gold-free detectors **that reason from the patch**, not of the value-wrong
> class itself. An instrument that derives its reference from the issue reached one of the ten, verified by
> passing on the accepted fix and failing on the certified-wrong one.

The mitigation argument survives and is sharpened rather than overturned: `1/10`, with a Wilson interval of
`[0.02, 0.40]`, at a false-alarm cost that makes the gold-free configuration unattractive. Independently
authored consequence tests remain the right direction — this is the first direct evidence the mechanism works
at all, which is what TCP-1 was always betting on.

## What this does not show

Not TCP-1, and it fills no iter212 gate: three models chosen by one agent, prompted by one prompt, in one
workspace share a designer, and the stop rule against replacing human reviewers with LLM judges stands
untouched. Not a deployable system, not a rate, not a leaderboard. `1/10` is one case. `13` positives keep
every interval near `±0.2` wide.

## Regenerating

```bash
python3 scripts/validate_iter234_execution_safety.py
python3 scripts/adjudicate_iter234.py --check
```
