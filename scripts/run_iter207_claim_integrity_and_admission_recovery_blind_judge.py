#!/usr/bin/env python3
"""Run the frozen two-judge protocol only over iter207-bound evidence."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import adjudicate_iter207_claim_integrity_and_admission_recovery as adjudicator  # noqa: E402


def _load_core() -> Any:
    path = ROOT / "scripts/run_iter203_safety_recovery_blind_judge.py"
    spec = importlib.util.spec_from_file_location("_telos_iter207_blind_judge_core", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load isolated iter203 blind-judge implementation")
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get("scripts.adjudicate_iter203_safety_recovery")
    sys.modules["scripts.adjudicate_iter203_safety_recovery"] = adjudicator
    try:
        spec.loader.exec_module(module)
    finally:
        if previous is None:
            del sys.modules["scripts.adjudicate_iter203_safety_recovery"]
        else:
            sys.modules["scripts.adjudicate_iter203_safety_recovery"] = previous
    return module


_core = _load_core()
JudgeCheckpointError = _core.JudgeCheckpointError
EXPERIMENT_ID = adjudicator.EXPERIMENT_ID
EXP = adjudicator.EXP
PROOF = EXP / "proof"
RAW = PROOF / "raw"

_core.EXPERIMENT_ID = EXPERIMENT_ID
_core.EXP = EXP
_core.PROOF = PROOF
_core.RAW = RAW
_core.ATTEMPT_DIRNAME = "judge_provider_attempts"
_core.STARTED_SCHEMA = "telos.iter207.judge_provider_attempt.started.v1"
_core.FINISHED_SCHEMA = "telos.iter207.judge_provider_attempt.finished.v1"
_core.PARSED_SCHEMA = "telos.iter207.judge_provider_attempt.parsed.v1"
_core.VERDICTS_SCHEMA = "telos.iter207.blind_verdicts.v1"
_core.AUDIT_SCHEMA = "telos.iter207.claim_integrity_and_admission_recovery.audit.v1"

_original_build_audit = _core.build_audit


def build_audit(
    adjudication: Mapping[str, Any],
    verdicts: list[dict[str, Any]],
    bindings: Mapping[str, str],
    *,
    verdict_bundle_sha256: str | None = None,
    checkpoint_evidence_sha256: str | None = None,
) -> dict[str, Any]:
    document = _original_build_audit(
        adjudication,
        verdicts,
        bindings,
        verdict_bundle_sha256=verdict_bundle_sha256,
        checkpoint_evidence_sha256=checkpoint_evidence_sha256,
    )
    pooled = document["pooled_corrected_iter200_plus_iter202_cohort"]
    attempts = pooled["attempts"]
    attempts["iter207"] = attempts.pop("iter203")
    components = pooled["components"]
    components["iter202_fixed_outputs_via_iter207_claim_integrity_and_admission_recovery"] = (
        components.pop("iter202_fixed_outputs_via_iter203_recovery")
    )
    return document


_core.build_audit = build_audit
parse = _core.parse
order_ab = _core.order_ab
build_prompt = _core.build_prompt
prepare_work = _core.prepare_work
run_attempts = _core.run_attempts


def main() -> int:
    adjudication, candidates, snapshot, bindings = prepare_work()
    verdicts, checkpoint_evidence = run_attempts(
        candidates,
        snapshot,
        bindings,
        refuse_calls_if_derived_exists=True,
    )
    verdict_bundle = {
        "bindings": dict(sorted(bindings.items())),
        "checkpoint_evidence": checkpoint_evidence,
        "experiment_id": EXPERIMENT_ID,
        "schema_version": _core.VERDICTS_SCHEMA,
        "verdicts": verdicts,
    }
    verdict_bundle_sha256 = _core.digest_bytes(_core.canonical_bytes(verdict_bundle))
    audit = build_audit(
        adjudication,
        verdicts,
        bindings,
        verdict_bundle_sha256=verdict_bundle_sha256,
        checkpoint_evidence_sha256=checkpoint_evidence["evidence_sha256"],
    )
    _core._atomic_derived(PROOF / "blind_judge_verdicts.json", verdict_bundle)
    _core._atomic_derived(PROOF / "audit_report.json", audit)
    overall = audit["overall"]
    print(
        f"iter207 admission-history recovery: k={overall['k_strict_confirmed']} "
        f"N={overall['N_certified']} u={overall['u_unadjudicated']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
