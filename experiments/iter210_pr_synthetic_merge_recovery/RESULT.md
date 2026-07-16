# Iter210 result — Pull-request synthetic-merge recovery

Status: PASS locally; remote publication gates pending.

Iter210 preserves the exact iter209 seal and corrects one pull-request-only topology error. Iter209's push
matrix was green; its PR matrix failed because the validator treated GitHub's synthetic merge `HEAD` as the
branch handoff commit. Iter210 resolves the sealed iter209 target directly when it is in the current history
and derives its own source/seal topology from the handoff and exact Git parents.

The iter209 receipt checker now validates exact source Git blobs on descendants and refuses sealed rewrites.
Regression coverage checks both sealed receipt custody and descendant target selection.

The exact remote observations and zero-action ledger are recorded in
`proof/pr_synthetic_merge_failure.json`. The companion v2 receipt binds every iter210 source artifact.

No provider request, GPU run, scientific container run, workflow dispatch, release, deployment, payment, or
scientific execution occurred. Iter210 contributes no scientific `N`, `k`, `u`, benchmark score, effect
estimate, model comparison, or state-of-the-art claim.

Publication remains blocked until both fresh GitHub `ci` matrices pass at the unchanged sealed iter210 tip.
