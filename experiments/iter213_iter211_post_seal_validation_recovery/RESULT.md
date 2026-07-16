# Iter213 result — Iter211 post-seal validation recovery

Status: **PASS locally; remote publication gates pending**.

Iter213 preserves the exact iter211 A/B seal and repairs three descendant-compatibility defects found only
after the handoff replaced iter210's displayed state. Standing-claim extraction now recognizes both bounded
handoff title families without weakening marker presence. Iter210 and iter211 receipt/topology guards now
resolve exact immutable source and seal commits on later descendants, read source Git blobs, and never treat
new additive experiment paths as changes to a sealed predecessor.

Regression tests bind the exact source/seal identities and both handoff boundary titles. The TCP-1 protocol,
five deterministic seeds, `17` generated artifacts, `2` passing local-design gates, `9` blocked external
gates, and `execution_authorized=false` remain unchanged. Iter212 remains the prospective independent cohort
and custody gate; it is not activated or modified by this recovery.

Iter213 contributes no scientific `N`, `k`, `u`, trajectory, benchmark score, effect estimate, model
comparison, population estimate, product-efficacy result, deployment claim, priority claim, or
state-of-the-art claim.

No provider/model request, GPU allocation, accelerator-hour, scientific container, scientific trajectory,
workflow dispatch or rerun, deployment, payment, release, or pre-publication remote mutation occurred.

The exact observed failure is retained in `proof/post_seal_failure.json`. Publication remains conditional on
the source-plus-handoff seal, full local closure, local synthetic-merge simulation, and green exact-tip push
and pull-request CI.
