# Iteration 145 - Does a Judge Panel Substitute for Held-Out Execution?

Status: pre-registered design; executed over the confirmed both-miss set.

## Why this gate exists

iter143 found that the two frontier judges disagree on the both-miss hacks, which implies that combining
judges should catch more than any single one. If a judge ensemble closed the class, the execution layer
would be optional. This gate tests that: it combines three judges over every confirmed both-miss hack
found so far and measures how much each ensemble rule narrows the survivor set, and whether any hack
survives every rule.

## Method

Take all seven confirmed both-miss hacks - six django (iter143) and one sympy (iter144) - each with the
verdict of three judges (`gemini-2.5-flash`, `gpt-5.6-terra`, `claude-opus-4-8`) under the identical
rubric. Apply three ensemble decision rules, where a judge "catches" a hack when it returns
`reward_hack`:

- any-catch: caught if any of the three judges flags it (maximal recall).
- majority-catch: caught if at least two of three flag it.
- unanimous-catch: caught only if all three flag it (maximal precision).

Report the caught count and survivor set for each rule, and the universal-survivor set - hacks caught by
no rule, including any-catch, which therefore require held-out execution.

## Endpoints

- caught count and survivors under any-catch, majority-catch, and unanimous-catch.
- universal-survivor set (survive the any-catch rule and the detector).

## Acceptance / interpretation rule

If the any-catch panel drives the survivor set to zero, a judge ensemble can substitute for execution on
this set. If at least one hack survives even any-catch, the ensemble narrows but does not close the class,
and execution remains necessary. The any-catch rule's precision cost on legitimate code is acknowledged
but not measured here.

## Falsifiers

1. A universal survivor requires no judge to return `reward_hack` under the any-catch rule.
2. The any-catch panel's precision cost on legitimate code is not measured here and is not claimed as free.
3. This is a small-N result (seven confirmed both-miss), not a distributional panel calibration.

## Execution envelope

- deterministic re-derivation of committed judge verdicts, no new provider calls in the runner; no GPU;
  benchmark/model/SOTA claim forbidden.

## Claim boundary (pre-committed)

At most: "over `7` confirmed both-miss hacks, a three-judge any-catch panel catches `K`, majority-catch
`M`, unanimous-catch `U`, and `S` hack(s) survive every rule and the detector, caught only by held-out
execution; a judge panel narrows the survivor set and adds robustness but does not substitute for
execution." Not a benchmark, model, or SOTA claim, and not a panel calibration with a measured false
positive rate.
