# Blinded Model-Judge Packets v1

This directory contains prompt-ready code-review packets for the frozen, historically misnamed
`reward_hack_benchmark_v1` rows. Iter192 established that these are not reward hacks: every row fails the
official grader. The packet artifact itself contains no model outputs, scores, rankings, or provider calls;
historical judge results live in their named experiment proof directories.

Each packet exposes only:

- repository and instance id,
- public SWE-bench task text,
- public target-test identifiers,
- candidate diff,
- neutral review instruction and required JSON output shape.

The prompt payload excludes official reports, report hashes, source split,
source experiment, prior static/model labels, detector outcomes, and any wording
that says a row is a known constructed both-miss case.

Primary files:

- `packets.jsonl`: 40 blinded packets.
- `schema.json`: packet schema.
- `manifest.json`: packet hashes, source hashes, coverage, and audit summary.
