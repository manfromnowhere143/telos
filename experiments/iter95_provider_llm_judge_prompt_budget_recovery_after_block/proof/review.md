# Iteration 95 Review

Iter95 did not call a provider. It validated the iter94 blocked result, diagnosed the `MAX_TOKENS`
parse blocker, materialized recovered prompts from public fixture artifacts, scanned them for
private-label markers, and pre-registered a bounded paid retry gate.

The recovery directly addresses the iter94 failure: the old `256` output-token ceiling was almost
entirely consumed by hidden reasoning (`241` thoughts tokens plus `11` candidate tokens), leaving no
parseable JSON decision. The recovered design raises the output ceiling to `2048`, constrains the
visible response to minified JSON, and stops on any future parse failure without hidden retries.

No benchmark, model-superiority, production/live-domain, or state-of-the-art result is claimed.
