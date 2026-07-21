#!/usr/bin/env python3
"""Build the reviewed iter240 -> iter241 public-claim migration."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate_claim_registry.py"
PLAN = ROOT / "experiments/iter241_iter240_repository_closure/proof/claim_registry_migration.json"
REPORT = ROOT / "experiments/iter241_iter240_repository_closure/proof/claim_coverage_report.json"
REGISTRY = ROOT / "mission/claim_registry.json"

FROM_GATE = "experiments/iter240_ground_truth_admission_design/HYPOTHESIS.md"
TO_GATE = "experiments/iter241_iter240_repository_closure/HYPOTHESIS.md"
PRIOR_CANONICAL_SHA256 = "9af5484f892818190aaa357736dcd102af7aacf1c062e9a0a725a38b7f9be3bd"
PRIOR_EVIDENCE = {
    "commit": "f954696c935ad0b733dcd613b553e1799a7b3810",
    "registry_path": "mission/claim_registry.json",
    "registry_sha256": "e8afa4679b9dd6cd7804d98c754a940ffc11c5ca572b6627d212fc889a618924",
    "coverage_report_path": "experiments/iter240_ground_truth_admission_design/proof/claim_coverage_report.json",
    "coverage_report_sha256": "1c83825096a96f1c45ac7ca8c3b2341b86d53910c0486fb2efe32b71b62a3045",
    "report_seal_id": "iter240-completed-evidence-seal",
}
EXPECTED_AUTHORIZATION = (
    "50c6cd259ceb2ca1acf36ec8eb3819954b8eefc4ba0b628641e500f756e94965"
)
MIGRATION_LABEL = "iter241"
REPLACEABLE_REGISTRY_DESCRIPTION = (
    "the sealed iter240 authority nor an exact reviewed iter241 transition"
)
REPLACEABLE_REGISTRY_SHA256 = {
    "bd4dc790936518edbca6acf0b035e9f9e9d702c3a6c252b99e7224afc41f7933",
    "ee3c536bd89c0ede943f62291a50eac61af2b5f60d45127ba516f1aae55804bc",
    "aaf2b6a8bdd061a648e706a37f8cf274ce99966ee9c1ee4c388921cfd9342f4c",
}


def _load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("iter241_claim_validator", VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load claim-registry validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_sha256(value: Any) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _payload(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    candidate = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), 0o644)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(candidate, path)
    finally:
        candidate.unlink(missing_ok=True)


def _binding_key(normalized: Any, role: str, resolution: Any) -> str:
    return json.dumps(
        [normalized, role, resolution],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def build() -> tuple[dict[str, Any], dict[str, Any], str]:
    validator = _load_validator()
    prior = validator._prior_registry_from_evidence(
        ROOT,
        PRIOR_EVIDENCE,
        expected_active_gate=FROM_GATE,
    )
    if _canonical_sha256(prior) != PRIOR_CANONICAL_SHA256:
        raise RuntimeError("sealed prior-registry canonical digest differs")
    prior_bindings = {
        row["binding_id"]: row
        for row in prior["bindings"]
    }
    live_bindings = {
        row.binding_id: row
        for row in validator.extract_all_bindings(ROOT)
    }
    with tempfile.TemporaryDirectory(prefix="telos-iter241-prior-surfaces-") as temporary:
        prior_root = Path(temporary)
        for surface in prior["declared_surfaces"]:
            relative = surface["path"]
            completed = subprocess.run(
                ["git", "-C", str(ROOT), "show", f"{PRIOR_EVIDENCE['commit']}:{relative}"],
                capture_output=True,
                check=False,
            )
            if completed.returncode != 0:
                raise RuntimeError(f"cannot materialize sealed prior surface: {relative}")
            destination = prior_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(completed.stdout)
        prior_live_bindings = {
            row.binding_id: row
            for row in validator.extract_all_bindings(prior_root)
        }
    if set(prior_live_bindings) != set(prior_bindings):
        raise RuntimeError("sealed prior surface extraction differs from prior registry")
    prior_ids = set(prior_bindings)
    live_ids = set(live_bindings)

    material_updates: list[dict[str, Any]] = []
    for binding_id in sorted(prior_ids & live_ids):
        old = prior_bindings[binding_id]
        live = live_bindings[binding_id]
        expected_atom = {
            "text": live.atom.text,
            "normalized": live.atom.normalized,
        }
        expected_role = validator.atom_role(live)
        if old.get("atom") == expected_atom and old.get("role") == expected_role:
            continue
        resolution = validator.derive_nonclaim(live)
        if resolution is None:
            raise RuntimeError(
                "retained binding changed without exact nonclaim authority: "
                f"{binding_id}"
            )
        material_updates.append(
            {"binding_id": binding_id, "new_resolution": resolution}
        )

    removed_pool = sorted(prior_ids - live_ids)
    added_pool = sorted(live_ids - prior_ids)
    old_material: defaultdict[str, list[str]] = defaultdict(list)
    new_material: defaultdict[str, list[str]] = defaultdict(list)
    for binding_id in removed_pool:
        row = prior_bindings[binding_id]
        resolution = row.get("resolution")
        if isinstance(resolution, dict) and resolution.get("type") == "claim_projection":
            old_material[
                _binding_key(
                    row.get("atom", {}).get("normalized"),
                    row.get("role"),
                    resolution,
                )
            ].append(binding_id)
    for binding_id in added_pool:
        row = live_bindings[binding_id]
        if validator.derive_nonclaim(row) is None:
            structural_matches = [
                old_id
                for old_ids in old_material.values()
                for old_id in old_ids
                if prior_bindings[old_id].get("structural_anchor_sha256")
                == row.segment.anchor_sha256
                and prior_bindings[old_id].get("segment_ordinal")
                == row.segment.segment_ordinal
                and prior_bindings[old_id].get("atom_ordinal")
                == row.atom_ordinal
                and prior_bindings[old_id].get("atom", {}).get("normalized")
                == row.atom.normalized
                and prior_bindings[old_id].get("role")
                == validator.atom_role(row)
            ]
            if len(structural_matches) == 1:
                old_row = prior_bindings[structural_matches[0]]
                selected_key = _binding_key(
                    old_row["atom"]["normalized"],
                    old_row["role"],
                    old_row["resolution"],
                )
            else:
                parallel_resolutions = {
                    json.dumps(
                        prior_bindings[old_id]["resolution"],
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    )
                    for old_id in sorted(prior_ids)
                    if prior_live_bindings[old_id].segment.text == row.segment.text
                    and prior_live_bindings[old_id].atom_ordinal == row.atom_ordinal
                    and prior_live_bindings[old_id].atom.normalized
                    == row.atom.normalized
                    and validator.atom_role(prior_live_bindings[old_id])
                    == validator.atom_role(row)
                    and prior_bindings[old_id].get("resolution", {}).get("type")
                    == "claim_projection"
                }
                parallel_keys = [
                    key
                    for key in old_material
                    if json.dumps(
                        json.loads(key)[2],
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    )
                    in parallel_resolutions
                    and json.loads(key)[0] == row.atom.normalized
                    and json.loads(key)[1] == validator.atom_role(row)
                ]
                normalized_role_matches = [
                    key
                    for key in old_material
                    if json.loads(key)[0] == row.atom.normalized
                    and json.loads(key)[1] == validator.atom_role(row)
                ]
                if len(parallel_keys) == 1:
                    selected_key = parallel_keys[0]
                elif len(normalized_role_matches) != 1:
                    raise RuntimeError(
                        "new material atom has no unique predecessor resolution: "
                        f"{binding_id}: structural={structural_matches} "
                        f"parallel={parallel_keys} semantic={normalized_role_matches}"
                    )
                else:
                    selected_key = normalized_role_matches[0]
            if selected_key not in old_material:
                raise RuntimeError(
                    f"new material atom predecessor group is absent: {binding_id}"
                )
            new_material[selected_key].append(binding_id)

    rebindings: list[dict[str, str]] = []
    for key in sorted(set(old_material) | set(new_material)):
        old_ids = sorted(old_material.get(key, []))
        new_ids = sorted(new_material.get(key, []))
        if len(old_ids) != len(new_ids):
            raise RuntimeError(
                "material wording binding census changed: "
                f"old={old_ids} new={new_ids}"
            )
        rebindings.extend(
            {"old_binding_id": old_id, "new_binding_id": new_id}
            for old_id, new_id in zip(old_ids, new_ids, strict=True)
        )
    rebound_old = {row["old_binding_id"] for row in rebindings}
    rebound_new = {row["new_binding_id"] for row in rebindings}
    removed = sorted((prior_ids - live_ids) - rebound_old)
    additions = sorted((live_ids - prior_ids) - rebound_new)
    new_resolutions: dict[str, dict[str, Any]] = {}
    for binding_id in additions:
        resolution = validator.derive_nonclaim(live_bindings[binding_id])
        if resolution is None:
            raise RuntimeError(
                f"new atom lacks exact lexical classification: {binding_id}"
            )
        new_resolutions[binding_id] = resolution

    plan = {
        "schema_version": "telos.claim_registry_migration.v2",
        "prior_registry_canonical_sha256": PRIOR_CANONICAL_SHA256,
        "from_active_gate": FROM_GATE,
        "to_active_gate": TO_GATE,
        "plan_path": PLAN.relative_to(ROOT).as_posix(),
        "prior_registry_evidence": PRIOR_EVIDENCE,
        "rebindings": rebindings,
        "material_binding_updates": material_updates,
        "lineage_binding_reassignments": [],
        "removed_binding_ids": removed,
        "new_binding_resolutions": new_resolutions,
        "new_claims": {},
        "claim_updates": {},
    }
    candidate = validator.build_migration_candidate(
        ROOT,
        prior,
        plan,
        require_current_prior=False,
    )
    authorization = validator.binding_authorization_sha256(
        ROOT,
        registry=candidate,
        active_gate=TO_GATE,
    )
    return plan, candidate, authorization


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--print-authorization", action="store_true")
    action.add_argument("--write-plan", action="store_true")
    action.add_argument("--write-registry-and-report", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args()

    plan, candidate, authorization = build()
    if args.print_authorization:
        print(authorization)
        return 0
    if args.write_plan:
        if PLAN.exists() and PLAN.read_bytes() != _payload(plan):
            raise RuntimeError("refusing to replace a different migration plan")
        _atomic_write(PLAN, _payload(plan))
        print(f"wrote {PLAN.relative_to(ROOT)}")
        return 0
    if not PLAN.is_file() or PLAN.read_bytes() != _payload(plan):
        raise RuntimeError("retained migration plan does not regenerate")
    if EXPECTED_AUTHORIZATION != authorization:
        raise RuntimeError(
            "builder binding authorization differs: "
            f"expected={EXPECTED_AUTHORIZATION!r} actual={authorization}"
        )

    validator = _load_validator()
    if args.write_registry_and_report:
        prior = validator._prior_registry_from_evidence(
            ROOT,
            PRIOR_EVIDENCE,
            expected_active_gate=FROM_GATE,
        )
        current_registry_raw = REGISTRY.read_bytes()
        if (
            validator.read_json(REGISTRY) != prior
            and hashlib.sha256(current_registry_raw).hexdigest()
            not in REPLACEABLE_REGISTRY_SHA256
        ):
            raise RuntimeError(
                "refusing migration write: worktree registry is neither "
                f"{REPLACEABLE_REGISTRY_DESCRIPTION}"
            )
        if validator.AUTHORIZED_BINDING_INVENTORY_SHA256.get(TO_GATE) != authorization:
            raise RuntimeError("reviewed validator binding authorization is absent or differs")
        prior_bytes = current_registry_raw
        try:
            _atomic_write(REGISTRY, _payload(candidate))
            failures, report = validator.validate(root=ROOT, check_report=False)
            if failures:
                raise RuntimeError("candidate registry validation failed: " + "; ".join(failures))
            _atomic_write(REPORT, _payload(report))
        except Exception:
            _atomic_write(REGISTRY, prior_bytes)
            REPORT.unlink(missing_ok=True)
            raise
        print(f"wrote {REGISTRY.relative_to(ROOT)} and {REPORT.relative_to(ROOT)}")
        return 0

    if validator.read_json(REGISTRY) != candidate:
        raise RuntimeError("retained registry does not regenerate")
    failures, _report = validator.validate(root=ROOT)
    if failures:
        raise RuntimeError("claim registry validation failed: " + "; ".join(failures))
    print(
        f"{MIGRATION_LABEL} claim migration regenerates: "
        f"{len(plan['rebindings'])} material rebindings, "
        f"{len(plan['removed_binding_ids'])} retired typed bindings, "
        f"{len(plan['new_binding_resolutions'])} new typed bindings"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
