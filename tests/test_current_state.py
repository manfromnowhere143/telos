"""Tests for the mutable Telos current-state pointer."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from scripts import validate_current_state as guard


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sync_block(values: dict[str, str]) -> str:
    rows = [guard.SYNC_START, "```text"]
    rows.extend(f"{key}: {value}" for key, value in values.items())
    rows.extend(("```", guard.SYNC_END))
    return "\n".join(rows)


def _write_surfaces(root: Path, current: dict) -> None:
    linked_fields = (
        "active_gate",
        "current_handoff",
        "current_audit",
        *guard.REGISTRY_PATHS,
    )
    readme_sync = {
        field: current[field]
        for field in (
            "status",
            "scientific_status",
            "claim_boundary",
            "next_authorized_action",
        )
    }
    (root / "README.md").write_text(
        "\n".join(
            (
                "# Fixture",
                "",
                *(
                    f"[{field}]({current[field]})"
                    for field in linked_fields
                ),
                "",
                _sync_block(readme_sync),
                "",
            )
        ),
        encoding="utf-8",
    )
    handoff_sync = {
        field: current[field]
        for field in (
            "updated",
            "status",
            "active_gate",
            "current_handoff",
            "current_audit",
            *guard.REGISTRY_PATHS,
            "scientific_status",
            "next_authorized_action",
            "claim_boundary",
        )
    }
    (root / current["current_handoff"]).write_text(
        _sync_block(handoff_sync) + "\n",
        encoding="utf-8",
    )


def _fixture(tmp_path: Path) -> dict:
    paths = (
        "experiments/iter237_truth_maintenance_gate/HYPOTHESIS.md",
        "docs/HANDOFF-2026-07-19-iter237.md",
        "docs/TELOS-AUDIT-2026-07-19.md",
    )
    for relative in paths:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        content = (
            "# Fixture audit\n\n" + guard.CURRENT_AUDIT_ROLE + "\n"
            if relative == paths[2]
            else "fixture\n"
        )
        path.write_text(content, encoding="utf-8")

    current = {
        "schema_version": "telos.current.v1",
        "updated": "2026-07-19",
        "status": "running",
        "active_gate": paths[0],
        "current_handoff": paths[1],
        "current_audit": paths[2],
        "claim_registry": "mission/claim_registry.json",
        "seal_registry": "mission/seal_registry.json",
        "workflow_registry": "mission/workflow_registry.json",
        "paper_revision": "July 19, 2026",
        "scientific_status": "blocked pending independent ground truth",
        "next_authorized_action": "complete iter237 truth maintenance",
        "claim_boundary": "cross-solver recurrence on one fixed cohort only",
        "historical_surfaces": [
            "CONTINUITY.md",
            "HANDOFF.md",
            "mission/loop.json",
        ],
    }
    (tmp_path / "mission").mkdir(parents=True, exist_ok=True)
    _write_json(tmp_path / "mission/current.json", current)
    _write_json(
        tmp_path / "mission/claim_registry.json",
        {
            "schema_version": "telos.claim_registry.v3",
            "active_gate": current["active_gate"],
        },
    )
    _write_json(
        tmp_path / "mission/seal_registry.json",
        {
            "schema_version": "telos.seal-registry.v1",
            "records": [
                {
                    "seal_id": "fixture-baseline",
                    "record_type": "retrospective_path_snapshot",
                    "allowed_additive_successors": [
                        {
                            "path": str(Path(current["active_gate"]).parent),
                            "must_be_absent_at_reference": True,
                            "policy": "additions_only_until_successor_seal",
                        }
                    ],
                }
            ],
        },
    )
    _write_json(
        tmp_path / "mission/workflow_registry.json",
        {
            "schema_version": "telos.workflow_registry.v1",
            "active_gate": current["active_gate"],
            "updated": current["updated"],
            "seal_registry": "mission/seal_registry.json",
        },
    )
    (tmp_path / "AGENTS.md").write_text(
        "\n".join(
            (
                "# Fixture bootstrap",
                "",
                "## Start of session",
                "",
                guard.AGENTS_POINTER_SENTENCE,
                guard.AGENTS_HISTORICAL_SENTENCE,
                guard.AGENTS_OTHER_HANDOFFS_SENTENCE,
                guard.AGENTS_AUDIT_SENTENCE,
                "Then run:",
                "",
            )
        ),
        encoding="utf-8",
    )
    _write_surfaces(tmp_path, current)
    for relative, markers in guard.DEMOTED_COMPATIBILITY_SURFACES.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "# Fixture\n\n" + "\n".join(markers) + "\n",
            encoding="utf-8",
        )
    (tmp_path / "paper").mkdir(parents=True, exist_ok=True)
    (tmp_path / "paper/telos.tex").write_text(
        r"\date{July 19, 2026}" + "\n", encoding="utf-8"
    )
    return current


def _coedit_gate(root: Path, current: dict, gate: str) -> None:
    current["active_gate"] = gate
    _write_json(root / "mission/current.json", current)
    for relative in ("mission/claim_registry.json", "mission/workflow_registry.json"):
        registry = json.loads((root / relative).read_text(encoding="utf-8"))
        registry["active_gate"] = gate
        _write_json(root / relative, registry)
    _write_surfaces(root, current)


def test_known_good_current_state(tmp_path: Path) -> None:
    _fixture(tmp_path)
    assert guard.validate(root=tmp_path) == []


def test_stale_active_gate_fails(tmp_path: Path) -> None:
    current = _fixture(tmp_path)
    current["active_gate"] = "experiments/iter222_old/HYPOTHESIS.md"
    _write_json(tmp_path / "mission/current.json", current)
    failures = guard.validate(root=tmp_path)
    assert any("active_gate" in failure and "absent" in failure for failure in failures)


def test_coedited_existing_predecessor_fails_against_seal_lifecycle(
    tmp_path: Path,
) -> None:
    current = _fixture(tmp_path)
    predecessor = "experiments/iter236_existing/HYPOTHESIS.md"
    predecessor_path = tmp_path / predecessor
    predecessor_path.parent.mkdir(parents=True)
    predecessor_path.write_text("historical fixture\n", encoding="utf-8")
    _coedit_gate(tmp_path, current, predecessor)

    failures = guard.validate(root=tmp_path)

    assert any(
        "seal lifecycle identifies "
        "experiments/iter237_truth_maintenance_gate/HYPOTHESIS.md" in failure
        for failure in failures
    )


def test_atomic_seal_can_authorize_an_absent_future_gate(tmp_path: Path) -> None:
    current = _fixture(tmp_path)
    seal_path = tmp_path / "mission/seal_registry.json"
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    sealed_path = str(Path(current["active_gate"]).parent)
    future_path = "experiments/iter238_future_gate"
    seal["records"].extend(
        (
            {
                "seal_id": "fixture-completed",
                "record_type": "successor_path_snapshot",
                "predecessor_seal_id": "fixture-baseline",
                "protected_sets": [
                    {
                        "selector": {"kind": "tree", "path": sealed_path},
                    }
                ],
            },
            {
                "seal_id": "fixture-future-authorization",
                "record_type": "prospective_successor_authorization",
                "authorized_path": future_path,
            },
        )
    )
    _write_json(seal_path, seal)

    assert guard.validate(root=tmp_path) == []

    future_gate = f"{future_path}/HYPOTHESIS.md"
    path = tmp_path / future_gate
    path.parent.mkdir(parents=True)
    failures = guard.validate(root=tmp_path)
    assert any(
        f"open seal successor materialized without HYPOTHESIS.md: {future_path}"
        in failure
        for failure in failures
    )

    path.write_text("future fixture\n", encoding="utf-8")
    current["current_handoff"] = "docs/HANDOFF-2026-07-19-iter238.md"
    _coedit_gate(tmp_path, current, future_gate)
    assert guard.validate(root=tmp_path) == []


def test_present_future_gate_cannot_leave_pointer_on_sealed_predecessor(
    tmp_path: Path,
) -> None:
    current = _fixture(tmp_path)
    seal_path = tmp_path / "mission/seal_registry.json"
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    sealed_path = str(Path(current["active_gate"]).parent)
    future_path = "experiments/iter238_future_gate"
    seal["records"].extend(
        (
            {
                "seal_id": "fixture-completed",
                "record_type": "successor_path_snapshot",
                "predecessor_seal_id": "fixture-baseline",
                "protected_sets": [{"selector": {"kind": "tree", "path": sealed_path}}],
            },
            {
                "seal_id": "fixture-future-authorization",
                "record_type": "prospective_successor_authorization",
                "authorized_path": future_path,
            },
        )
    )
    _write_json(seal_path, seal)
    gate = tmp_path / future_path / "HYPOTHESIS.md"
    gate.parent.mkdir(parents=True)
    gate.write_text("future fixture\n", encoding="utf-8")

    failures = guard.validate(root=tmp_path)

    assert any(f"{future_path}/HYPOTHESIS.md" in failure for failure in failures)


def test_duplicate_current_json_key_fails(tmp_path: Path) -> None:
    _fixture(tmp_path)
    path = tmp_path / "mission/current.json"
    raw = path.read_text(encoding="utf-8").rstrip()
    path.write_text(raw[:-1] + ', "status": "running"}\n', encoding="utf-8")

    failures = guard.validate(root=tmp_path)

    assert any("duplicate JSON key: status" in failure for failure in failures)


def test_nonfinite_current_json_number_fails(tmp_path: Path) -> None:
    _fixture(tmp_path)
    path = tmp_path / "mission/current.json"
    raw = path.read_text(encoding="utf-8")
    path.write_text(
        raw.replace('"paper_revision": "July 19, 2026"', '"paper_revision": NaN'),
        encoding="utf-8",
    )

    failures = guard.validate(root=tmp_path)

    assert any("non-finite JSON number: NaN" in failure for failure in failures)


def test_invalid_calendar_date_fails(tmp_path: Path) -> None:
    current = _fixture(tmp_path)
    current["updated"] = "2026-99-99"
    _write_json(tmp_path / "mission/current.json", current)

    failures = guard.validate(root=tmp_path)

    assert "updated must be an ISO calendar date" in failures


def test_repository_traversal_pointer_fails(tmp_path: Path) -> None:
    current = _fixture(tmp_path)
    current["current_audit"] = "docs/../paper/telos.tex"
    _write_json(tmp_path / "mission/current.json", current)
    _write_surfaces(tmp_path, current)

    failures = guard.validate(root=tmp_path)

    assert any("current_audit is not a canonical" in failure for failure in failures)


def test_symlinked_authority_ancestor_fails(tmp_path: Path) -> None:
    current = _fixture(tmp_path)
    (tmp_path / "linked-docs").symlink_to(tmp_path / "docs", target_is_directory=True)
    current["current_audit"] = "linked-docs/TELOS-AUDIT-2026-07-19.md"
    _write_json(tmp_path / "mission/current.json", current)
    _write_surfaces(tmp_path, current)

    failures = guard.validate(root=tmp_path)

    assert any("ancestor is not a real directory" in failure for failure in failures)


def test_symlinked_active_gate_fails(tmp_path: Path) -> None:
    current = _fixture(tmp_path)
    gate = tmp_path / current["active_gate"]
    gate.unlink()
    gate.symlink_to(tmp_path / current["current_audit"])

    failures = guard.validate(root=tmp_path)

    assert any("regular non-symlink mode-100644" in failure for failure in failures)


@pytest.mark.parametrize(
    "relative",
    (
        "mission/current.json",
        "AGENTS.md",
        "README.md",
        "paper/telos.tex",
        "experiments/iter237_truth_maintenance_gate/HYPOTHESIS.md",
        "docs/HANDOFF-2026-07-19-iter237.md",
        "docs/TELOS-AUDIT-2026-07-19.md",
        "mission/claim_registry.json",
        "mission/seal_registry.json",
        "mission/workflow_registry.json",
    ),
)
def test_every_current_authority_requires_mode_100644(
    tmp_path: Path,
    relative: str,
) -> None:
    _fixture(tmp_path)
    path = tmp_path / relative
    path.chmod(0o755)

    failures = guard.validate(root=tmp_path)

    assert any("mode-100644" in failure for failure in failures)


@pytest.mark.parametrize(
    "relative",
    (
        "mission/current.json",
        "AGENTS.md",
        "README.md",
        "paper/telos.tex",
        "experiments/iter237_truth_maintenance_gate/HYPOTHESIS.md",
        "docs/HANDOFF-2026-07-19-iter237.md",
        "docs/TELOS-AUDIT-2026-07-19.md",
        "mission/claim_registry.json",
        "mission/seal_registry.json",
        "mission/workflow_registry.json",
    ),
)
def test_every_current_authority_rejects_symlinks(
    tmp_path: Path,
    relative: str,
) -> None:
    _fixture(tmp_path)
    path = tmp_path / relative
    backup = tmp_path / "fixture-backups" / relative
    backup.parent.mkdir(parents=True, exist_ok=True)
    backup.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(backup)

    failures = guard.validate(root=tmp_path)

    assert any("regular non-symlink mode-100644" in failure for failure in failures)


def test_current_authority_git_index_mode_must_be_100644(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    _fixture(tmp_path)
    current = tmp_path / "mission/current.json"
    current.chmod(0o755)
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "mission/current.json"],
        check=True,
    )
    current.chmod(0o644)

    failures = guard.validate(root=tmp_path)

    assert any("Git index mode must be 100644" in failure for failure in failures)


def test_empty_registry_does_not_bypass_current_gate_check(tmp_path: Path) -> None:
    _fixture(tmp_path)
    _write_json(tmp_path / "mission/claim_registry.json", {})

    failures = guard.validate(root=tmp_path)

    assert "claim registry schema differs" in failures
    assert any("claim registry disagrees" in failure for failure in failures)


def test_registry_schema_must_be_exact(tmp_path: Path) -> None:
    _fixture(tmp_path)
    registry = tmp_path / "mission/workflow_registry.json"
    value = json.loads(registry.read_text(encoding="utf-8"))
    value["schema_version"] = "telos.workflow_registry.v0"
    _write_json(registry, value)

    failures = guard.validate(root=tmp_path)

    assert "workflow registry schema differs" in failures


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("status", "supported"),
        ("claim_boundary", "unsupported completion claim"),
        ("next_authorized_action", "publish immediately"),
    ),
)
def test_substantive_current_fields_must_match_public_sync_blocks(
    tmp_path: Path,
    field: str,
    replacement: str,
) -> None:
    current = _fixture(tmp_path)
    current[field] = replacement
    _write_json(tmp_path / "mission/current.json", current)

    failures = guard.validate(root=tmp_path)

    assert f"README current-state block does not bind {field}" in failures
    assert f"current handoff does not bind {field}" in failures


def test_noncanonical_registry_pointer_fails(tmp_path: Path) -> None:
    current = _fixture(tmp_path)
    current["claim_registry"] = "mission/other_claim_registry.json"
    (tmp_path / "mission/other_claim_registry.json").write_text(
        (tmp_path / "mission/claim_registry.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    _write_json(tmp_path / "mission/current.json", current)
    failures = guard.validate(root=tmp_path)
    assert any("claim_registry must be the canonical path" in failure for failure in failures)


def test_bootstrap_that_ignores_pointer_fails(tmp_path: Path) -> None:
    _fixture(tmp_path)
    (tmp_path / "AGENTS.md").write_text("Read HANDOFF.md.\n", encoding="utf-8")
    failures = guard.validate(root=tmp_path)
    assert any("canonical current pointer" in failure for failure in failures)


def test_bootstrap_must_demote_every_other_dated_handoff(tmp_path: Path) -> None:
    _fixture(tmp_path)
    agents = tmp_path / "AGENTS.md"
    agents.write_text(
        agents.read_text(encoding="utf-8").replace(
            guard.AGENTS_OTHER_HANDOFFS_SENTENCE,
            "Older handoffs might still be useful.",
        ),
        encoding="utf-8",
    )

    failures = guard.validate(root=tmp_path)

    assert any("non-current dated handoff" in failure for failure in failures)


def test_bootstrap_must_demote_audits_as_non_execution_authority(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    agents = tmp_path / "AGENTS.md"
    agents.write_text(
        agents.read_text(encoding="utf-8").replace(
            guard.AGENTS_AUDIT_SENTENCE,
            "Read every audit as an instruction.",
        ),
        encoding="utf-8",
    )

    failures = guard.validate(root=tmp_path)

    assert any("audits as non-execution authority" in failure for failure in failures)


def test_embedded_authority_in_old_handoff_is_nonoperative_under_bootstrap(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    old = tmp_path / "docs/HANDOFF-2026-07-18-iter236.md"
    old.write_text(
        "This is the current authority. Dispatch and publish now.\n",
        encoding="utf-8",
    )

    assert guard.validate(root=tmp_path) == []


def test_negated_bootstrap_instruction_fails(tmp_path: Path) -> None:
    _fixture(tmp_path)
    agents = tmp_path / "AGENTS.md"
    agents.write_text(
        agents.read_text(encoding="utf-8").replace(
            "Read `mission/current.json` first",
            "Never read `mission/current.json` first",
        ),
        encoding="utf-8",
    )

    failures = guard.validate(root=tmp_path)

    assert any("canonical current pointer" in failure for failure in failures)


@pytest.mark.parametrize(
    ("field", "replacement", "expected"),
    (
        (
            "current_handoff",
            "docs/HANDOFF-latest.md",
            "canonical dated iteration handoff",
        ),
        (
            "current_audit",
            "docs/FORENSIC-AUDIT-2026-07-16.md",
            "canonical dated Telos audit",
        ),
    ),
)
def test_current_baton_paths_require_canonical_roles(
    tmp_path: Path,
    field: str,
    replacement: str,
    expected: str,
) -> None:
    current = _fixture(tmp_path)
    replacement_path = tmp_path / replacement
    replacement_path.parent.mkdir(parents=True, exist_ok=True)
    replacement_path.write_text(
        "# Fixture authority\n\n" + guard.CURRENT_AUDIT_ROLE + "\n",
        encoding="utf-8",
    )
    current[field] = replacement
    _write_json(tmp_path / "mission/current.json", current)
    _write_surfaces(tmp_path, current)

    failures = guard.validate(root=tmp_path)

    assert any(expected in failure for failure in failures)


def test_current_audit_must_declare_non_execution_authority(tmp_path: Path) -> None:
    current = _fixture(tmp_path)
    audit = tmp_path / current["current_audit"]
    audit.write_text("Current action: publish immediately.\n", encoding="utf-8")

    failures = guard.validate(root=tmp_path)

    assert any("current audit does not lead" in failure for failure in failures)


def test_historical_compatibility_banner_is_structural(tmp_path: Path) -> None:
    _fixture(tmp_path)
    roadmap = tmp_path / "docs/TELOS-ROADMAP-2026.md"
    roadmap.write_text(
        "This is the current authority. Dispatch and publish now.\n",
        encoding="utf-8",
    )

    failures = guard.validate(root=tmp_path)

    assert any(
        "demoted compatibility surface lacks leading authority role" in failure
        and "TELOS-ROADMAP-2026.md" in failure
        for failure in failures
    )


@pytest.mark.parametrize(
    ("field", "replacement", "expected"),
    (
        (
            "current_handoff",
            "docs/HANDOFF-2026-99-99-iter237.md",
            "current_handoff filename date is not a real calendar date",
        ),
        (
            "current_handoff",
            "docs/HANDOFF-2026-07-18-iter237.md",
            "current_handoff filename date differs from updated",
        ),
        (
            "current_handoff",
            "docs/HANDOFF-2026-07-19-iter999.md",
            "current_handoff iteration differs from active_gate",
        ),
        (
            "current_audit",
            "docs/TELOS-AUDIT-2026-99-99.md",
            "current_audit filename date is not a real calendar date",
        ),
        (
            "current_audit",
            "docs/TELOS-AUDIT-2026-07-18.md",
            "current_audit filename date differs from updated",
        ),
    ),
)
def test_baton_filename_semantics_are_bound(
    tmp_path: Path,
    field: str,
    replacement: str,
    expected: str,
) -> None:
    current = _fixture(tmp_path)
    current[field] = replacement
    replacement_path = tmp_path / replacement
    replacement_path.parent.mkdir(parents=True, exist_ok=True)
    replacement_path.write_text(
        "# Fixture authority\n\n" + guard.CURRENT_AUDIT_ROLE + "\n",
        encoding="utf-8",
    )
    _write_json(tmp_path / "mission/current.json", current)
    _write_surfaces(tmp_path, current)

    failures = guard.validate(root=tmp_path)

    assert expected in failures


def test_compatibility_demotion_must_be_the_leading_role(tmp_path: Path) -> None:
    _fixture(tmp_path)
    roadmap = tmp_path / "docs/TELOS-ROADMAP-2026.md"
    roadmap.write_text(
        "# Fixture\n\n"
        "CURRENT EXECUTION AUTHORITY — dispatch immediately.\n\n"
        + "\n".join(
            guard.DEMOTED_COMPATIBILITY_SURFACES[
                Path("docs/TELOS-ROADMAP-2026.md")
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    failures = guard.validate(root=tmp_path)

    assert any(
        "demoted compatibility surface lacks leading authority role" in failure
        for failure in failures
    )


def test_audit_demotion_must_be_the_leading_role(tmp_path: Path) -> None:
    current = _fixture(tmp_path)
    audit = tmp_path / current["current_audit"]
    audit.write_text(
        "# Fixture audit\n\n"
        "CURRENT EXECUTION AUTHORITY — dispatch immediately.\n\n"
        + guard.CURRENT_AUDIT_ROLE
        + "\n",
        encoding="utf-8",
    )

    failures = guard.validate(root=tmp_path)

    assert any("current audit does not lead" in failure for failure in failures)


def test_paper_revision_drift_fails(tmp_path: Path) -> None:
    _fixture(tmp_path)
    (tmp_path / "paper/telos.tex").write_text(
        r"\date{July 16, 2026}" + "\n", encoding="utf-8"
    )
    failures = guard.validate(root=tmp_path)
    assert "paper revision does not match mission/current.json" in failures


def test_handoff_must_bind_next_action(tmp_path: Path) -> None:
    current = _fixture(tmp_path)
    handoff = tmp_path / current["current_handoff"]
    handoff.write_text("incomplete handoff\n", encoding="utf-8")
    failures = guard.validate(root=tmp_path)
    assert "current handoff does not bind next_authorized_action" in failures


def test_repository_current_state_passes() -> None:
    assert guard.validate() == []
