# Iter245 preregistration amendment — native-loader containment

Status: **preregistered additive clarification**.

This amendment follows the immutable Iter245 hypothesis at commit
`fd5ee0f99b24ef6a6106cd4f18172ad49ce108db`. A source and archive design review
occurred while an uncommitted implementation draft existed. The review
preceded every downloaded-interpreter command, implementation commit, remote
push, hosted observation, and acceptance decision. The draft has no authority;
only later committed bytes may become the candidate.

## Triggering design fact

At source commit `c2033aa6c313f068f4bde238bfaa5987ad4f2e79`,
`builders/ubuntu-python-builder.psm1` configures shared Python with an absolute
tool-cache prefix and linker rpath. `builders/python-builder.psm1` derives that
prefix from `RUNNER_TOOL_CACHE`. The pinned setup-python implementation
compensates by setting `LD_LIBRARY_PATH` to the extracted `lib` directory before
running upstream setup. Direct extraction without an equally explicit loader
boundary could therefore load `libpython` from the rejected preinstalled tree
or fail to start.

## Additive acceptance requirements

1. Before the first downloaded-interpreter command, a resolved root-owned,
   owner-executable, non-group/world-writable `/usr/bin/readelf` must inspect
   the exact extracted target. The ELF must use the registered x86-64 glibc
   interpreter, contain no `DT_RPATH`, contain exactly the expected absolute
   build-prefix `DT_RUNPATH`, and name the exact `libpython` soname through a
   slash-free `DT_NEEDED` entry. The contained extracted `libpython` target
   must be a regular effective-user-owned non-group/world-writable file.
2. `DT_RPATH`, a different or additional runpath, an absolute dependency name,
   a missing contained `libpython`, an untrusted program interpreter, or an
   unavailable trusted readelf is an Iter245 falsifier. Iter245 may not patch,
   rewrite, or relink an authenticated archive byte.
3. Every downloaded-interpreter command must start under a credential-stripped
   environment with exact `LD_LIBRARY_PATH=<extraction-root>/lib`. Inherited
   loader controls including `LD_PRELOAD`, `LD_AUDIT`, and inherited search
   paths are absent. The same exact library path is exported to later workflow
   steps; no preinstalled tool-cache path is added.
4. The first downloaded-interpreter observation must fail unless its resolved
   executable, `sys.prefix`, `sys.exec_prefix`, base prefixes, retained
   `sys.path`, pip module path, and runtime sysconfig installation paths are
   contained in the extraction root. On Linux it must also inspect
   `/proc/self/maps` and prove that the mapped `libpython` resolves inside that
   root and is not group/world writable.
5. Extraction assigns mode `0700` to every directory and only the exact target
   ELF. Every other regular archive file receives mode `0600`; archive special
   bits and executable bits are not restored. Shipped console scripts are
   never invoked. Dependency installation uses the contained interpreter as
   `python3 -I -P -m pip` against the existing hash-locked requirements.
6. The exact upstream packer archives from root `.`. Canonicalization therefore
   permits only the root record `.` and exactly one leading `./`, strips that
   prefix before duplicate and containment checks, and rejects every other dot
   segment, empty component, backslash, non-ASCII byte, or control character.
   Printable ASCII spaces in a component are retained because the frozen
   archive contains such a filename. Recognized GNU long-name or long-link
   transport metadata may be consumed by the isolated standard-library tar
   parser but is never materialized; the resulting member and link name still
   pass the complete normalized inventory checks.

These requirements make the native-loader compensation observable and
falsifiable. They do not establish complete transitive runtime provenance:
system glibc and other root-owned platform libraries remain outside the frozen
archive boundary. The registered asset identities, scientific boundary, and
external-action authority are unchanged.
