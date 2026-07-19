# Mission-loop authority

This file is a historical compatibility pointer. It is not the current baton,
claim ledger, or execution authority.

Current operational recovery begins at
[`mission/current.json`](../mission/current.json), then follows its exact
`current_handoff`, `current_audit`, and active-gate paths. The current handoff
states the allowed and forbidden actions for that gate.

The root [`HANDOFF.md`](../HANDOFF.md), [`CONTINUITY.md`](../CONTINUITY.md),
and [`mission/loop.json`](../mission/loop.json) preserve earlier protocol
history. Their embedded “current” fields are sealed historical evidence and
must not be used as present authority.

The correction-preserving research record is indexed in
[`docs/EXPERIMENT_INDEX.md`](EXPERIMENT_INDEX.md). Each experiment directory
owns its own hypothesis, result, and retained proof. A later correction is
additive; it does not rewrite the earlier record.

The live loop is therefore:

- recover only from the canonical current pointer;
- preregister a bounded gate before action;
- execute only what that gate authorizes;
- retain raw evidence and explicit missingness;
- publish null, blocked, invalid, and corrected outcomes at full visibility;
- advance the current pointer only after the gate’s local, live, and remote
  acceptance bars are earned.

No statement in this compatibility page authorizes provider calls, spending,
workflow dispatch, publication, release, or scientific execution.
