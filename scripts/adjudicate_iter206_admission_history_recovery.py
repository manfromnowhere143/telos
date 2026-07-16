#!/usr/bin/env python3
"""Adjudicate only the aggregate bound to the iter206 attempt-1 runtime."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import collect_iter206_execution as collector  # noqa: E402


EXPERIMENT_ID = "iter206_iter205_admission_history_recovery"
UPSTREAM_BRIDGE_EXPERIMENT_ID = "iter203_iter202_safety_recovery"
EXP = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXP / "proof"
RAW = PROOF / "raw"
UPSTREAM_ITER203 = ROOT / "experiments/iter203_iter202_safety_recovery"


def _load_core() -> Any:
    path = ROOT / "scripts/adjudicate_iter203_safety_recovery.py"
    spec = importlib.util.spec_from_file_location("_telos_iter206_adjudicator_core", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load isolated iter203 adjudicator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_core = _load_core()
RecoveryEvidenceError = _core.RecoveryEvidenceError

_core.EXPERIMENT_ID = EXPERIMENT_ID
_core.EXP = EXP
_core.PROOF = PROOF
_core.RAW = RAW
_core.BRIDGE = UPSTREAM_ITER203 / "proof/raw/safety_recovery_bridge"
_core.INVENTORY = _core.BRIDGE / "upstream_inventory.json"
_core.DISPOSITION = _core.BRIDGE / "scenario_disposition.json"
_core.SAFE_INDEX = _core.BRIDGE / "safe_scenario_index.json"
_core.SOLUTION_PROJECTION_INDEX = _core.BRIDGE / "solution_projection_index.json"
_core.SPECS = UPSTREAM_ITER203 / "proof/raw/specs"
_core.SOLUTIONS = UPSTREAM_ITER203 / "proof/raw/solutions"
_core.SCENARIOS = UPSTREAM_ITER203 / "proof/raw/scenarios"
_core.EXECUTION = _core.RAW / "execution"
_core.RUNTIME_MANIFEST = _core.RAW / "runtime_manifest.json"
_core.AGGREGATE_RECEIPT = (
    _core.EXECUTION / "_telos_iter206_execution_complete.receipt.json"
)
_core.ADJUDICATION_SCHEMA = "telos.iter206.admission_history_recovery.adjudication.v1"
_core.DIVERGENCE_SCHEMA = "telos.iter206.admission_history_recovery.divergence_candidates.v1"
_core.AGGREGATE_SCHEMA = collector.AGGREGATE_SCHEMA
_core.RUNTIME_SCHEMA = collector.RUNTIME_MANIFEST_SCHEMA


def _with_upstream_bridge_identity(function: Any, *args: Any) -> Any:
    previous = _core.EXPERIMENT_ID
    _core.EXPERIMENT_ID = UPSTREAM_BRIDGE_EXPERIMENT_ID
    try:
        return function(*args)
    finally:
        _core.EXPERIMENT_ID = previous


_original_validate_inventory = _core.validate_inventory
_original_validate_disposition = _core.validate_disposition
_original_safe_index_ids = _core._safe_index_ids


def validate_inventory(document: dict[str, Any]) -> None:
    _with_upstream_bridge_identity(_original_validate_inventory, document)


def validate_disposition(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return _with_upstream_bridge_identity(_original_validate_disposition, document)


def safe_index_ids(
    document: dict[str, Any], dispositions: dict[str, dict[str, Any]]
) -> list[str]:
    return _with_upstream_bridge_identity(
        _original_safe_index_ids, document, dispositions
    )


_core.validate_inventory = validate_inventory
_core.validate_disposition = validate_disposition
_core._safe_index_ids = safe_index_ids


def require_runtime_manifest_closure() -> None:
    from scripts import build_iter206_runtime_manifest as builder

    errors = builder.validate_committed_manifest()
    if errors:
        raise RecoveryEvidenceError(
            "committed iter206 runtime manifest does not reproduce current bytes: "
            + "; ".join(errors)
        )


_core.require_runtime_manifest_closure = require_runtime_manifest_closure
_original_build = _core.build_adjudication_documents


def build_adjudication_documents() -> tuple[dict[str, Any], dict[str, Any]]:
    require_runtime_manifest_closure()
    previous = sys.modules.get("scripts.collect_iter203_execution")
    previous_requirement = _core.require_runtime_manifest_closure
    _core.require_runtime_manifest_closure = lambda: None
    sys.modules["scripts.collect_iter203_execution"] = collector
    try:
        return _original_build()
    finally:
        _core.require_runtime_manifest_closure = previous_requirement
        if previous is None:
            del sys.modules["scripts.collect_iter203_execution"]
        else:
            sys.modules["scripts.collect_iter203_execution"] = previous


load_json_strict = _core.load_json_strict
canonical_json_bytes = _core.canonical_json_bytes
classify_certified_outcome = _core.classify_certified_outcome
evidence_bindings = _core.evidence_bindings


def main() -> int:
    adjudication, divergence = build_adjudication_documents()
    _core._atomic_replace(
        _core.PROOF / "adjudication.json", canonical_json_bytes(adjudication)
    )
    _core._atomic_replace(
        _core.PROOF / "divergence_candidates.json", canonical_json_bytes(divergence)
    )
    certified = sum(row["certified_resolved"] for row in adjudication["rows"])
    missing = sum(
        row["status"] == "certified_unadjudicated" for row in adjudication["rows"]
    )
    print(
        f"iter206 adjudication: 50/50 certification rows, certified={certified}, "
        f"safe_divergences={divergence['count']}, witness_missing={missing}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
