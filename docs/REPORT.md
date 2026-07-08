# Report

No model or benchmark result is claimed yet.

This file will become the technical report only after the first Telos proof experiment produces
agent-attempt evidence. The target survey result is published, but it is not an agent result.

Current evidence:

- `PREREGISTRATION.md` freezes the target-selection gate.
- `experiments/iter00_target_survey/RESULT.md` selects the first target family.
- `experiments/iter01_receipt_dry_run/RESULT.md` validates the receipt dry run.
- `experiments/iter02_public_task_slice/RESULT.md` selects the public task slice.
- `experiments/iter03_codeclash_smoke/RESULT.md` validates the CodeClash no-LLM smoke receipt.
- `experiments/iter04_agent_behavior_slice/RESULT.md` selects the deterministic agent-behavior
  slice.
- `experiments/iter05_agent_behavior_smoke/RESULT.md` validates deterministic Mini-SWE-Agent
  trajectory and stats capture.
- `experiments/iter06_deterministic_edit_slice/RESULT.md` selects the deterministic edit slice.
- `experiments/iter07_deterministic_edit_smoke/RESULT.md` validates deterministic non-empty diff
  capture through the CodeClash Mini-SWE-Agent path.
- `experiments/iter08_provider_model_pilot_slice/RESULT.md` selects the first paid-provider pilot
  without making a model-result claim.
- `experiments/iter09_provider_model_pilot_smoke/HYPOTHESIS.md` freezes the next paid smoke gate.
- `protocol/proof.schema.json` defines the initial receipt contract.
- `tests/` verifies the receipt validator and repository contract.

## Reporting Rule

When results exist, this report must lead with:

1. the exact benchmark target,
2. the baseline,
3. the primary metric,
4. the outcome with confidence intervals or exact counts,
5. the nulls and failed gates,
6. the limitations.

No result paragraph may outrun committed proof artifacts.
