# Iter234 amendment — independence is not binary, so measure it

Status: **pre-data amendment.** No iter234 test has been generated, no provider call made, no output inspected.
Committed before `run_iter234_tests.py` exists, so the git record establishes it precedes any result.

## The question this answers

*Does a fresh agent session in the same workspace count as an independent author?*

**No** — and the reason is worth stating precisely, because it decomposes a question the iter212 gate treats as
binary.

Independence has three axes, and they are not the same thing:

| Axis | What it means | Can I provide it? |
| --- | --- | --- |
| **Information** | The author cannot see the patch, gold, hidden tests, labels, or witnesses. | **Yes**, verifiably by construction. |
| **Architectural** | The author's judgment is not correlated with the solver's by shared weights and training. | **Yes**, by using different model families. |
| **Institutional** | The author has no shared incentive, and conflict/independence can be attested by a distinct party. | **No.** Irreducible. |

A fresh session in this workspace fails **two** of the three. It can read `answers.json`, the witnesses, and
the labels, so it has no information independence unless deliberately sandboxed. And it is the same model
family reasoning about the same artifacts, so its blind spots are the solver's blind spots — two samples from
one distribution are not two independent judgments.

That second failure is the one that actually matters scientifically, and it is the one nobody has measured.

## The amendment

Iter234 as pre-registered used a single author (`gpt-5.6-terra`). It now uses **three architecturally distinct
authors across three providers**, each independently patch-blind:

- `gpt-5.6-terra` (OpenAI)
- `claude-opus-4-8` (Anthropic)
- `gemini-3.1-pro-preview` (Google)

Every original bar, arm, falsifier, and claim boundary carries over unchanged and applies per author.

### Why amend rather than run one author and extend later

Running one author, seeing the result, then deciding whether to add two more would make the panel design
**conditioned on the first author's outcome**. That is the shape of a post-hoc choice even when the intent is
innocent, and this repository already carries one standing correction for exactly that (iter200's strict rule,
adopted after outcome inspection, is why that result is exploratory rather than confirmatory).

Committing all three now costs roughly three times a small budget and removes the confound entirely.

## The new endpoint: what does independence actually buy?

This is the part that turns an assertion into a measurement.

For the `13` positives, and separately for the `value` subclass, report:

- **per-author recall** — three independent estimates of the same mechanism;
- **pairwise agreement** on which rows each author catches;
- **union (any-author) recall** versus the best single author;
- **unanimous recall**.

The interpretation is pre-committed:

> If the three authors catch **substantially the same rows**, then patch-blindness alone does not decorrelate
> judgment, the blind spots are shared across model families, and *institutional* independence — genuinely
> different minds with different priors, which is what TCP-1 buys and I cannot provide — is doing the real
> work. The union will barely exceed the best single author.
>
> If the three authors catch **substantially different rows**, then independence buys coverage cheaply, the
> union will materially exceed any single author, and the size of that gap is a direct empirical estimate of
> what additional independent authors are worth — including human ones.

Either outcome is informative, and neither is available by argument. **This is the honest way to answer "what
can a human do that I cannot": measure the marginal value of an independent author, and report it.**

## What this still does not do

It does not fill an iter212 gate. Architectural diversity is not institutional independence: three models
selected by one agent, prompted by one prompt, in one workspace, share a designer. The stop rule stands — LLM
judges do not replace external humans — and iter212 remains blocked and untouched.

What changes is that the *cost of not having humans* stops being an assertion and becomes a number.

## Budget

Three authors, `67` rows, up to three attempts each, bounded at `$75` total across all providers, inside the
operator-approved budget. Container execution runs on GitHub Actions at no provider cost.
