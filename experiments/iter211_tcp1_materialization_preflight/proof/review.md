# Iter211 adversarial review

## Review question

Could a motivated operator or agent read this packet as permission to run TCP-1, or convert mechanical
reproducibility into scientific credibility the evidence does not yet possess?

Answer: not if the admission report and validators are obeyed. The local materialization layer is complete;
scientific execution remains blocked.

## Threat review

| Threat | Superficially reassuring evidence | Why that is insufficient | Required gate |
| --- | --- | --- | --- |
| Post-output test design | Hidden-test hash | A late-authored test can also be hashed | Two-author pre-output freeze plus external timestamp |
| Task contamination | Task timestamp after a stated cutoff | Cutoffs are documented boundaries, not proof of non-exposure | Model binding, source evidence, exposure review, bounded claim |
| Mutable runtime | Model or image name | Names and tags can resolve to different bytes | Weight, tokenizer, engine source, container, driver, and host digests |
| Hidden-test leakage | Separate directory | Paths, mounts, process state, network, or symlinks can cross directories | Hostile isolation rehearsal with retained denial logs |
| Self-authored truth | LLM or agent verdict | The system under study cannot define its own semantic ground truth | Two blinded humans plus independent adjudicator |
| Selective retention | Final patch and score | Failures, tool calls, exits, and resource records can disappear | Complete append-only trace custody and receipt closure |
| Receipt overclaim | Valid SHA-256 closure | Hashes prove bytes, not author, time, license, independence, or truth | Identity/time attestations plus semantic review |
| Statistical overclaim | Significant paired pilot test | A selected twelve-task cohort is not a population sample | Within-pilot estimand and forbidden population/model claims |
| Control leakage | Strong calibration performance | Controls can be recognized or pooled to inflate natural estimates | Blinded presentation and permanently separate denominators |
| Budget drift | Nominal 64-hour ceiling | Throughput uncertainty can consume the ceiling before completion | Two-hour preflight, ten-percent headroom, stop-before-allocation rule |

## Design judgments

The primary comparison is conditioned on independently adjudicated semantic failures that already pass the
visible proxy. Visible-only acceptance is therefore one for every eligible row. The effect is the fraction
for which TELOS withholds acceptance; the exact McNemar calculation is retained as the preregistered paired
test, while the Wilson interval on that reduction is the more directly interpretable simple-rate interval.
Reject and abstain both prevent an unsupported completion claim, but they remain separately counted.

The minimum-ten-failures rule is an interpretability bar, not a sampling guarantee. If the selected model
produces fewer, TCP-1 is a null/failure for detector comparison; controls cannot be substituted into that
denominator. Likewise, missing raw trajectory or grader evidence invalidates the protocol rather than
becoming a negative row.

Requiring five distinct humans is intentionally stricter than merely having three nominal roles. It blocks
task/test authors from relabeling their own constructions and keeps the disagreement adjudicator independent
of both first-pass labels. This costs coordination, but it buys the independence on which the semantic
ground truth claim rests.

## Open blockers

All nine blockers in `admission_report.json` are real external dependencies. None can be satisfied by filling
a placeholder, choosing a fashionable model from memory, treating repository publication as budget
approval, or calling a Git timestamp an external transparency proof.

## Verdict

Materialization preflight: `PASS`.

Scientific execution admission: `BLOCKED`.

No refinement inside iter211 may change that verdict. Any future evidence must enter a separately versioned
iteration so this zero-execution decision remains auditable.
