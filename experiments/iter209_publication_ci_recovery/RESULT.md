# Iter209 result — Publication CI recovery

Status: PASS locally; remote publication gates pending.

Iter209 preserves the public iter208 seal and fixes two publication-only validator defects without changing
scientific evidence or claims.

## Corrected defects

- The iter65 receipt-schema audit now resolves its three recorded source digests from the exact iter65 Git
  commit. Evolved descendant source no longer creates a false historical-integrity failure, while an absent
  or mismatched historical blob still fails closed.
- The publication-lineage unit test now removes ambient GitHub Actions mode before testing local topology,
  then explicitly enables pull-request mode for its synthetic merge case.
- The iter208 validator now verifies its frozen receipt and every bound artifact from source commit
  `184883088336cbae834e812a8d1dce0b7b031821` when executed on a descendant.

## Evidence boundary

The exact remote failures, run identities, root causes, and zero-science action ledger are recorded in
`proof/ci_failure_diagnosis.json`. The companion v2 receipt binds the complete iter209 source correction.
Neither artifact proves semantic truth beyond this engineering recovery.

No provider request, GPU run, scientific container run, workflow dispatch, release, deployment, payment,
or scientific execution occurred. Iter209 contributes no scientific `N`, `k`, `u`, effect estimate,
benchmark score, model comparison, or state-of-the-art claim.

The failed iter208 branch remains unchanged. Iter209 may be published only on its fresh branch and merged
only after both non-scientific GitHub `ci` matrices pass at the exact sealed tip.
