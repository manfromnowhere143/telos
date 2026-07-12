# Iteration 148 - Does the Protocol Effect Replicate on a Disjoint Sample?

Status: pre-registered design; executed as an independent replication.

## Why this gate exists

iter146 measured the protocol effect on one django sample: proxy gate `0/7` real completions, Telos gate
`5/7`. A single small sample is not enough to call the rate robust. This gate replicates the identical
gold-free gate-and-repair experiment on a disjoint, older django instance range and reports both the
replication rate and the pooled rate across the two runs, to test whether `5/7` was an artifact of the
original instance choice.

## Method

Run the identical harness as iter146 (obtain a both-miss start; compare a proxy gate that accepts on
visible pass against the Telos gate that rejects on held-out execution, returns a gold-free generic
generalize-signal, and repairs up to two rounds; a Telos real completion passes the target and all
held-out tests with visible preserved), over django instances in the `11000-12999` range - disjoint from
iter146's core set. Report the replication rate on the new instances and the pooled rate across iter146
and iter148, deduplicated by instance id.

## Endpoints

- replication real-completion rate (proxy vs Telos) on the disjoint sample.
- pooled real-completion rate across iter146 and iter148 (deduplicated).

## Acceptance / interpretation rule

If the disjoint sample reproduces a Telos rate comparable to iter146's `5/7` while the proxy baseline stays
`0`, the protocol effect is robust rather than a small-N artifact. The pooled figure is the headline
robust rate.

## Falsifiers

1. A Telos real completion requires the target and all held-out tests to pass with visible preserved.
2. The replication instances must be disjoint from iter146's core set.
3. The pooled figure must deduplicate any instance shared between the two runs.

## Execution envelope

- native django execution + `gpt-5.6-terra`, no GPU; production mutation forbidden; benchmark/model/SOTA
  claim forbidden. (The scale run was interrupted at `7` starts by a background time limit; `7` is a full
  independent replication and is reported as such, with the truncation disclosed.)

## Claim boundary (pre-committed)

At most: "the protocol effect replicates on a disjoint django sample (`0/7 -> 5/7`, matching iter146) and
pools to `0/N -> K/N` across django 11xxx-15xxx, so the intervention rate is robust." Not a benchmark,
model, or SOTA claim.
