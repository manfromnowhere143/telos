# TELOS Agent Bootstrap

Canonical workspace: `/Users/danielwahnich/workspace/telos`.

## Project boundary

TELOS, Sentinel, Inbar, and Odeya are closely related projects. They are all separate from Aweb.
Do not import Aweb code, state, evidence, capability names, architecture, or branding into any of them.
Historical TELOS artifacts may contain legacy Aweb-era names; preserve those bytes and treat the names as
historical provenance, not as the current project boundary.

## Start of session

Read `mission/current.json` first, then read the dated handoff named by its
`current_handoff` field. `HANDOFF.md`, `CONTINUITY.md`, and
`mission/loop.json` are sealed historical TCP-1 artifacts; they remain required
evidence inputs but are not the current operational baton.

Every other `docs/HANDOFF-*.md` is a historical baton; embedded current,
active, next, or authority wording is non-operative. The exact
`current_audit` is dated analysis context, not execution authority; every other
dated audit is historical and non-operative.

Then run:

```bash
git status --short
python3 scripts/validate_current_paper.py
python3 scripts/validate_current_state.py
python3 scripts/validate_mission_loop.py
python3 -I scripts/run_iter241_pytest.py --run
```

## Evidence rules

- Preserve sealed experiments and raw evidence byte-for-byte. Correct a sealed result only in a new,
  additive iteration.
- A digest proves byte identity, not authorship, chronology, or truth. State those limits explicitly.
- Do not turn a protocol, infrastructure, admission, or publication null into a scientific outcome.
- Do not run a provider, container experiment, dispatch, push, merge, or release unless the active
  iteration explicitly authorizes it and every preceding gate is green.
- Keep README claims, paper claims, diagrams, machine-readable evidence, and the handoff synchronized.
