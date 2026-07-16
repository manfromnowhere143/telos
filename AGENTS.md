# TELOS Agent Bootstrap

Canonical workspace: `/Users/danielwahnich/workspace/telos`.

## Project boundary

TELOS, Sentinel, Inbar, and Odeya are closely related projects. They are all separate from Aweb.
Do not import Aweb code, state, evidence, capability names, architecture, or branding into any of them.
Historical TELOS artifacts may contain legacy Aweb-era names; preserve those bytes and treat the names as
historical provenance, not as the current project boundary.

## Start of session

Read `HANDOFF.md`, then run:

```bash
git status --short
python3 scripts/validate_current_paper.py
python3 scripts/validate_mission_loop.py
pytest -q
```

## Evidence rules

- Preserve sealed experiments and raw evidence byte-for-byte. Correct a sealed result only in a new,
  additive iteration.
- A digest proves byte identity, not authorship, chronology, or truth. State those limits explicitly.
- Do not turn a protocol, infrastructure, admission, or publication null into a scientific outcome.
- Do not run a provider, container experiment, dispatch, push, merge, or release unless the active
  iteration explicitly authorizes it and every preceding gate is green.
- Keep README claims, paper claims, diagrams, machine-readable evidence, and the handoff synchronized.
