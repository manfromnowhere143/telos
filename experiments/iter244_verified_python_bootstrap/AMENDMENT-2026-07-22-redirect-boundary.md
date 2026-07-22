# Iter244 preregistration amendment — release redirect boundary

Status: **preregistered additive clarification**.

This amendment follows the immutable Iter244 hypothesis at commit
`ff57eb8eee9782a69349ad49115a32a06d264386`. It precedes every Iter244
implementation, local execution, remote push, and hosted observation.

GitHub release downloads use an HTTPS redirect from the exact registered
`github.com/actions/python-versions/releases/download/...` URL to GitHub's
`release-assets.githubusercontent.com` delivery host. Acceptance gate 1 permits
only that HTTPS GitHub-to-GitHub release-asset redirect chain. A different
scheme, initial host, final host, tag, filename, or redirect class is denied.
The registered byte count and SHA-256 remain the final content authority.

This clarification changes no asset identity, executable policy, conclusion
boundary, or external-action authority.
