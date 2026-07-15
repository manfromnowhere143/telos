# Upstream iter202 protocol/execution null

The original iter202 provider stage completed under runtime-manifest SHA-256
`dd935a6f5873940fca5768891bb74a6cc635ef86bb65cdf493dd2a8ffe043868`: `53` solver calls produced `50`
model patches, and `39` scenario calls produced `38` extracted programs plus one `no_scenario` outcome.

Before any container execution, the frozen scenario guard returned `21` findings across `9` programs. The
original runtime is batch-fail-closed and requires the summary and files to reconstruct exactly from the
provider checkpoints. It cannot represent row-level safety rejection without changing runtime-bound code
and invalidating those checkpoints. Consequently:

- no official certification or behavioral execution was started;
- no rate, `N`, `k`, or `u` exists yet for iter202;
- this is a scenario-safety protocol/execution null, not a solve-yield null;
- the raw evidence remains scientifically useful only through the separately identified iter203 bridge
  and recovery protocol in `HYPOTHESIS.md`.

No iter202 scenario may be executed through the original runtime, and no iter202 provider artifact may be
rewritten, relabeled, regenerated, or replaced.
