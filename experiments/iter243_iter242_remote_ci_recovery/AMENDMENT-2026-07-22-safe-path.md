# Iter243 preregistration amendment — safe-path isolation

Status: **preregistered additive amendment**.

This amendment follows the immutable Iter243 hypothesis at commit
`0b49c1ffcaf885a774b014209aa9b078570ab03c`. It precedes every Iter243
diagnostic implementation, correction, remote push, and hosted observation.
No Iter243 outcome was observed between the hypothesis and this amendment.

## Added acceptance requirement

The Python isolation gate also requires `sys.flags.safe_path` to be true.
CPython `-I` implies this import-path control on the registered Python 3.11
and Python 3.12 matrix, so hosted-runner compatibility must not trade it away.

The bounded diagnostic and known-bad fixtures therefore cover four registered
flags: `isolated`, `ignore_environment`, `no_user_site`, and `safe_path`. A
missing or false value for any one of them is a hard denial and an Iter243
falsifier.

## Fixed boundary

This amendment only strengthens the original isolation condition. It does not
alter the executable-ownership policy, authorize a workflow dispatch or rerun,
authorize scientific execution, or widen the Iter243 conclusion boundary.
