#!/usr/bin/env python3
"""Build the reviewed iter239 -> iter240 public-claim migration.

This builder is deliberately specific.  It preserves eighteen reviewed
quantitative bindings across the dated-handoff transition, accepts only exact
lexically derived classifications for every other new atom, and refuses any
unreviewed material claim change.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate_claim_registry.py"
PLAN = (
    ROOT
    / "experiments/iter240_ground_truth_admission_design/proof/"
    "claim_registry_migration.json"
)
REPORT = (
    ROOT
    / "experiments/iter240_ground_truth_admission_design/proof/"
    "claim_coverage_report.json"
)
REGISTRY = ROOT / "mission/claim_registry.json"

FROM_GATE = "experiments/iter239_repository_governance/HYPOTHESIS.md"
TO_GATE = "experiments/iter240_ground_truth_admission_design/HYPOTHESIS.md"
PRIOR_CANONICAL_SHA256 = (
    "cd307ecbb70422de6b1583208531ec443b4bd4a28943fad5e581cd65fdb61548"
)
PRIOR_EVIDENCE = {
    "commit": "35a97b228afb7bd8eb44e71749986ee59020b25b",
    "registry_path": "mission/claim_registry.json",
    "registry_sha256": (
        "320fee8f9ac34c63b59c425e66b6d4008b8f4f64e3ec00eff297f64756493659"
    ),
    "coverage_report_path": (
        "experiments/iter239_repository_governance/proof/"
        "claim_coverage_report.json"
    ),
    "coverage_report_sha256": (
        "4b1562364c5de12bd047852f413e5b0b6b33ce7fba2907b3504f041732aeb6ef"
    ),
    "report_seal_id": "iter239-completed-evidence-seal",
}

REBINDINGS = {
    "docs/HANDOFF-2026-07-19-iter239.md:1267322abeffb52c9617:0:1":
        "docs/HANDOFF-2026-07-19-iter240.md:c07016f7bad73187829b:0:1",
    "docs/HANDOFF-2026-07-19-iter239.md:14fb13d629e397cb2123:0:0":
        "docs/HANDOFF-2026-07-19-iter240.md:ada11cda936ec9946f40:0:0",
    "docs/HANDOFF-2026-07-19-iter239.md:18e108599cb1e2683d03:0:0":
        "docs/HANDOFF-2026-07-19-iter240.md:a950cda1385ec06eacdd:0:0",
    "docs/HANDOFF-2026-07-19-iter239.md:18e108599cb1e2683d03:0:1":
        "docs/HANDOFF-2026-07-19-iter240.md:a950cda1385ec06eacdd:0:1",
    "docs/HANDOFF-2026-07-19-iter239.md:2f16dd7ff47f67bf709a:0:0":
        "docs/HANDOFF-2026-07-19-iter240.md:84042713a682413ab38d:0:0",
    "docs/HANDOFF-2026-07-19-iter239.md:3d9faa97dd5f750a15ee:0:0":
        "docs/HANDOFF-2026-07-19-iter240.md:9bd3bca7add9dfd2d8e0:0:0",
    "docs/HANDOFF-2026-07-19-iter239.md:3d9faa97dd5f750a15ee:0:1":
        "docs/HANDOFF-2026-07-19-iter240.md:9bd3bca7add9dfd2d8e0:0:1",
    "docs/HANDOFF-2026-07-19-iter239.md:4dfc2cc3382b8b348df1:0:0":
        "docs/HANDOFF-2026-07-19-iter240.md:53ff5320de415de1a176:0:1",
    "docs/HANDOFF-2026-07-19-iter239.md:762d80b171e21d285dcb:0:0":
        "docs/HANDOFF-2026-07-19-iter240.md:aa38dc7de263c74aaf35:0:0",
    "docs/HANDOFF-2026-07-19-iter239.md:762d80b171e21d285dcb:0:1":
        "docs/HANDOFF-2026-07-19-iter240.md:aa38dc7de263c74aaf35:0:1",
    "docs/HANDOFF-2026-07-19-iter239.md:85ad53ec1a3e743dbfb5:0:0":
        "docs/HANDOFF-2026-07-19-iter240.md:5a100e8a20d2e430e498:0:0",
    "docs/HANDOFF-2026-07-19-iter239.md:85ad53ec1a3e743dbfb5:0:2":
        "docs/HANDOFF-2026-07-19-iter240.md:5a100e8a20d2e430e498:0:2",
    "docs/HANDOFF-2026-07-19-iter239.md:ca06a09ef92aafd1a555:0:0":
        "docs/HANDOFF-2026-07-19-iter240.md:ca250b03cf164c603e99:0:0",
    "docs/HANDOFF-2026-07-19-iter239.md:d5bac9b3f95686ce2084:0:1":
        "docs/HANDOFF-2026-07-19-iter240.md:3a05edad1178429a617c:0:1",
    "docs/HANDOFF-2026-07-19-iter239.md:d7ff6b54ba44515a3d81:0:3":
        "docs/HANDOFF-2026-07-19-iter240.md:3e30d654712bfc081c9e:0:3",
    "docs/HANDOFF-2026-07-19-iter239.md:da9225f69e9ed21d2556:0:1":
        "docs/HANDOFF-2026-07-19-iter240.md:1acc2ecec223a21711e3:0:1",
    "docs/HANDOFF-2026-07-19-iter239.md:f6dceb25d97e92b8351e:0:0":
        "docs/HANDOFF-2026-07-19-iter240.md:6bd0719dd3ab7fdcd7d7:0:0",
    "docs/HANDOFF-2026-07-19-iter239.md:f6dceb25d97e92b8351e:0:1":
        "docs/HANDOFF-2026-07-19-iter240.md:6bd0719dd3ab7fdcd7d7:0:1",
}
MATERIAL_TYPED_UPDATES = (
    "README.md:be5eec3fe01a240c573a:0:1",
    "README.md:be5eec3fe01a240c573a:0:3",
    "mission/current.json:60e1a005ff3b8987db91:0:1",
)


def _load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "iter240_claim_validator",
        VALIDATOR,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load claim-registry validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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
        item["binding_id"]: item
        for item in prior["bindings"]
    }
    live_bindings = {
        item.binding_id: item
        for item in validator.extract_all_bindings(ROOT)
    }
    prior_ids = set(prior_bindings)
    live_ids = set(live_bindings)
    old_rebindings = set(REBINDINGS)
    new_rebindings = set(REBINDINGS.values())

    if len(REBINDINGS) != 18 or len(new_rebindings) != 18:
        raise RuntimeError("reviewed wording rebindings are not one-to-one")
    if not old_rebindings <= prior_ids or old_rebindings & live_ids:
        raise RuntimeError("reviewed predecessor rebindings are not exactly retired")
    if not new_rebindings <= live_ids or new_rebindings & prior_ids:
        raise RuntimeError("reviewed successor rebindings are not exactly new")

    for old_id, new_id in REBINDINGS.items():
        old = prior_bindings[old_id]
        new = live_bindings[new_id]
        if (
            old["atom"]["normalized"] != new.atom.normalized
            or old["role"] != validator.atom_role(new)
        ):
            raise RuntimeError(
                f"reviewed wording rebind changes atom or role: {old_id}"
            )

    removed = sorted((prior_ids - live_ids) - old_rebindings)
    additions = sorted((live_ids - prior_ids) - new_rebindings)
    if len(removed) != 42 or len(additions) != 50:
        raise RuntimeError(
            "public surface changed outside reviewed transition: "
            f"removed={len(removed)} additions={len(additions)}"
        )

    new_resolutions: dict[str, dict[str, Any]] = {}
    for binding_id in additions:
        resolution = validator.derive_nonclaim(live_bindings[binding_id])
        if resolution is None:
            raise RuntimeError(
                f"new atom lacks exact lexical classification: {binding_id}"
            )
        new_resolutions[binding_id] = resolution

    material_updates: list[dict[str, Any]] = []
    for binding_id in MATERIAL_TYPED_UPDATES:
        if binding_id not in prior_ids or binding_id not in live_ids:
            raise RuntimeError(
                f"reviewed retained typed binding is absent: {binding_id}"
            )
        resolution = validator.derive_nonclaim(live_bindings[binding_id])
        if resolution is None:
            raise RuntimeError(
                f"retained typed binding lost lexical authority: {binding_id}"
            )
        material_updates.append(
            {"binding_id": binding_id, "new_resolution": resolution}
        )

    plan = {
        "schema_version": "telos.claim_registry_migration.v2",
        "prior_registry_canonical_sha256": PRIOR_CANONICAL_SHA256,
        "from_active_gate": FROM_GATE,
        "to_active_gate": TO_GATE,
        "plan_path": PLAN.relative_to(ROOT).as_posix(),
        "prior_registry_evidence": PRIOR_EVIDENCE,
        "rebindings": [
            {"old_binding_id": old_id, "new_binding_id": REBINDINGS[old_id]}
            for old_id in sorted(REBINDINGS)
        ],
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

    validator = _load_validator()
    if args.write_registry_and_report:
        prior = validator._prior_registry_from_evidence(
            ROOT,
            PRIOR_EVIDENCE,
            expected_active_gate=FROM_GATE,
        )
        if validator.read_json(REGISTRY) != prior:
            raise RuntimeError(
                "refusing migration write: worktree registry is not "
                "the sealed iter239 authority"
            )
        expected = validator.AUTHORIZED_BINDING_INVENTORY_SHA256.get(TO_GATE)
        if expected != authorization:
            raise RuntimeError(
                "reviewed binding authorization is absent or differs: "
                f"expected={expected!r} actual={authorization}"
            )
        prior_bytes = REGISTRY.read_bytes()
        try:
            _atomic_write(REGISTRY, _payload(candidate))
            failures, report = validator.validate(
                root=ROOT,
                check_report=False,
            )
            if failures:
                raise RuntimeError(
                    "candidate registry validation failed: "
                    + "; ".join(failures)
                )
            _atomic_write(REPORT, _payload(report))
        except Exception:
            _atomic_write(REGISTRY, prior_bytes)
            REPORT.unlink(missing_ok=True)
            raise
        print(f"wrote {REGISTRY.relative_to(ROOT)} and {REPORT.relative_to(ROOT)}")
        return 0

    retained_registry = validator.read_json(REGISTRY)
    if retained_registry != candidate:
        raise RuntimeError("retained registry does not regenerate")
    failures, _ = validator.validate(root=ROOT)
    if failures:
        raise RuntimeError("claim registry validation failed: " + "; ".join(failures))
    print(
        "iter240 claim migration regenerates: "
        f"{len(REBINDINGS)} rebindings, "
        f"{len(plan['removed_binding_ids'])} retired typed bindings, "
        f"{len(plan['new_binding_resolutions'])} new typed bindings"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
