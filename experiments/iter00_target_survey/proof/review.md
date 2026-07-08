# Adversarial Review

## Objection 1 - A hybrid target may look weaker than choosing one benchmark.

Answer: valid risk. The mitigation is to make `iter01` a receipt dry run, not a headline result.
The first result tests the proof protocol on public artifacts. It does not claim benchmark
superiority.

## Objection 2 - SWE-bench Verified is already saturated.

Answer: accepted. That is why it was not selected alone. SWE-bench Verified remains useful as a
stable task and artifact source, but Telos should not chase `% Resolved` as the first headline.

## Objection 3 - CodeClash is newer and less settled.

Answer: accepted. It is still relevant because it directly targets goals rather than explicit
tickets, and its multi-round trajectories expose learning, drift, and over-editing. The first
experiment must use CodeClash as an anchor, not as a sole source of truth.

## Objection 4 - RE-Bench is the more important frontier target.

Answer: likely true for long-term value. It failed first-run cost discipline, not importance.
RE-Bench remains a second-stage target after the proof protocol works on cheaper software-agent
tasks.

## Objection 5 - The survey could be biased toward the repo author's coding-agent context.

Answer: possible. The scorecard penalized saturation and cost explicitly. tau2/tau3-bench and
AgentDojo remain viable follow-up lines; they were not rejected as low value.

## Decision After Review

Keep `HYBRID_OVERLAY_SELECTED`.

Hard constraint for the next step: `iter01` must be a small receipt-validity experiment. No claim
about model capability, benchmark improvement, or field-level superiority is allowed until receipts
validate cleanly.
