# Iter245 preregistration amendment — fail-closed archive boundary

Status: **preregistered additive clarification**.

This amendment follows the immutable Iter245 hypothesis at commit
`fd5ee0f99b24ef6a6106cd4f18172ad49ce108db` and the native-loader amendment at
commit `32dba1e5a85cb7dceb3e9cac3630f6b3544110f9`. An adversarial source review
occurred while an uncommitted implementation draft and synthetic local tests
existed. The review preceded every implementation commit, downloaded-
interpreter command, remote push, hosted observation, and acceptance decision.
The draft and its local passes have no authority.

## Triggering design facts

The draft authenticated a downloaded path in the shell, closed it, and then
reopened that path in the isolated extractor. A same-UID path replacement in
that interval could make the extractor parse bytes that were not authenticated
on its own descriptor. The draft also checked the archive's root-record count
only during its writing pass, admitted transport representations outside the
registered GNU boundary, and relied on shell `errexit` inside command
substitutions where Bash does not preserve it by default. These are design
failures, not hosted observations.

## Additive acceptance requirements

1. The isolated root-owned system-Python verifier must open the archive with
   no-follow semantics, verify regular-file type, ownership, non-writable mode,
   exact byte count, and exact SHA-256 on that same open descriptor, rewind that
   descriptor, and perform both parsing passes without reopening the pathname.
   A preliminary shell hash is not authority for the parser.
2. Structural preflight must require exactly one canonical root record `.` and
   the complete normalized inventory before the first destination write.
   Missing or duplicate root records, a digest mismatch, or an inventory
   mismatch must leave the fresh destination empty.
3. Symbolic-link names must be canonical printable ASCII relative names with
   no empty or dot component. PAX headers and GNU sparse members are rejected.
   The isolated standard-library parser may consume GNU long-name or long-link
   transport records only when the resulting retained name passes every
   ordinary normalized-inventory check.
4. Every shell denial must terminate its current shell context. Command-
   substitution validation must be explicitly checked and may not continue to
   a success print after a rejected predicate. The workflow source-binding
   commands use absolute trusted runner paths.
5. The registered download is one transfer attempt with at most one HTTPS
   redirect to the exact final host. Automatic transfer retries are disabled
   because a final curl observation does not attest earlier retry chains.
6. Downloaded-Python observations disable bytecode writes. After the final
   downloaded-Python observation, the isolated system verifier rechecks the
   complete retained tree and native-loader boundary before any success claim
   or workflow-environment export.
7. The Iter245 source guard is itself digest-bound by the workflow and has
   known-good and known-bad tests. Its output describes only source and
   contract validation; local execution must not imply that the hosted archive
   path, runner image, or remote matrix passed.
8. Runtime output distinguishes registered constants from observations. An
   asset ID that is not queried at runtime is labeled `registered_asset_id`;
   only the byte count and digest actually recomputed on the parser's descriptor
   are reported as authenticated observations.

These requirements tighten the already registered archive and workflow
boundary. They do not change the frozen assets, registered question, scientific
scope, conclusion boundary, budget, or external-action authority.
