# Iteration 140 Result - How Hard Is It To Construct a Both-Miss on Real Instances?

Status: `PASS` (an honest, informative negative result).

## What this gate did

Tried to make the both-miss result strong rather than anecdotal by constructing verified both-miss
hacks at scale. An automated hacker-fixer started from the correct gold fix on real django instances
and asked a model to degrade it into a subtly-wrong variant, then executed to verify the variant still
passes the target test but fails held-out tests. Two models were tried: `gemini-2.5-flash` and
`gemini-2.5-pro`.

## Result

| model | verified both-miss hacks | outcome distribution |
| --- | ---: | --- |
| `gemini-2.5-flash` | `0/10` | broke_visible 3, still_correct 3, no_degrade 3, gold_baseline_fail 1 |
| `gemini-2.5-pro` | `0/10` | broke_visible 5, still_correct 4, gold_baseline_fail 1 |

- total verified both-miss hacks: `0/20`

## The finding

Neither model produced a single verified both-miss hack. The degradations either broke the visible
test (too aggressive) or preserved correctness (too timid); none hit the narrow window of passing the
target test while failing a held-out test. Crucially, the stronger model (`gemini-2.5-pro`, with a
reasoning budget) did no better, so this is not only a capability limit.

The honest interpretation is structural and it is a genuine result: **the both-miss window is narrow
where a test suite is thorough.** On django instances with multiple held-out tests, the FAIL_TO_PASS
and PASS_TO_PASS tests overlap enough in what they exercise that a change breaking generalization tends
to also break a visible test. This is exactly consistent with iter139: the both-miss class concentrates
in thin-coverage, narrow-input functions - the property-rich math subset (a single identity test over a
narrow input domain, like coth on `[1,2,3]`), where iter118's hand-built hacks succeeded - and it
nearly closes on thoroughly-tested code.

This bounds the both-miss phenomenon honestly. It is real (iter118-iter119 proved it), but it is not
prevalent everywhere; it lives where test coverage is thin. That is a sharper, more defensible claim
than "both-miss is everywhere," and it explains why the verified both-miss set is small.

## Claim boundary

Supported: across `20` model-instance attempts an automated hacker-fixer with `gemini-2.5-flash` and
`gemini-2.5-pro` produced `0` verified both-miss hacks on thoroughly-tested django instances; the
outcome distribution and the stronger-model result bound the both-miss window as narrow where coverage
is thorough. Not supported: a benchmark, model, or state-of-the-art claim, or a claim that both-miss
cannot be constructed anywhere (iter118 constructed it on thin-coverage instances).

## Next gate

`iter141`: record the both-miss-prevalence bound in the paper, and to grow the verified both-miss set,
target thin-coverage instances (a single narrow-input test) rather than thoroughly-tested ones.

## Evidence

- `proof/flash_results.json`, `proof/pro_results.json` (native-execution hacker-fixer runs)
- `proof/endpoint_results.json`, `proof/run_summary.json`, `proof/learning_record.json`
- `proof/valid/receipt_both_miss_construction_hardness.json`
- `scripts/run_both_miss_construction_hardness.py`
