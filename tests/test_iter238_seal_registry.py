"""Known-good and known-bad cases for the iter238 retrospective seal registry."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess

import pytest

from scripts import validate_seal_registry as guard


ROOT = Path(__file__).resolve().parents[1]


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        capture_output=True,
        check=True,
        text=True,
    )
    return result.stdout.strip()


def _write_json(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _temporary_registry(tmp_path: Path) -> tuple[Path, Path, dict]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "seal-test@example.invalid")
    _git(repo, "config", "user.name", "Seal Test")

    evidence = repo / "experiments/iter237_predecessor/evidence.bin"
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"sealed predecessor bytes\n")
    (repo / "README.md").write_text("mutable current surface\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "reference")
    reference = _git(repo, "rev-parse", "HEAD")

    selector = {"kind": "tree", "path": "experiments"}
    count, digest, _ = guard.build_manifest(repo, reference, selector, label="fixture")
    document = {
        "schema_version": guard.SCHEMA_VERSION,
        "claim_boundary": (
            "This fixture proves byte identity only; it does not establish semantic truth."
        ),
        "records": [
            {
                "seal_id": "fixture-baseline",
                "record_type": "retrospective_path_snapshot",
                "reference_commit": reference,
                "protected_sets": [
                    {
                        "set_id": "fixture-experiments",
                        "selector": selector,
                        "policy": "existing_tree_immutable_registered_additions",
                        "blob_count": count,
                        "manifest_sha256": digest,
                    }
                ],
                "allowed_additive_successors": [
                    {
                        "path": "experiments/iter238_controls",
                        "must_be_absent_at_reference": True,
                        "policy": "additions_only_until_successor_seal",
                    }
                ],
                "limitations": [
                    "This is a retrospective fixture.",
                    "Its digest proves byte identity only.",
                ],
            }
        ],
    }
    registry = repo / "mission/seal_registry.json"
    _write_json(registry, document)
    return repo, registry, document


def _validate_fixture(repo: Path, registry: Path) -> list[str]:
    return guard.validate(
        repo,
        registry,
        enforce_project_baseline=False,
        check_history=True,
    )


def test_committed_telos_seal_registry_passes() -> None:
    assert guard.validate() == []


def test_registered_additive_successor_passes(tmp_path: Path) -> None:
    repo, registry, _ = _temporary_registry(tmp_path)
    successor = repo / "experiments/iter238_controls/HYPOTHESIS.md"
    successor.parent.mkdir(parents=True)
    successor.write_text("prospective additive evidence\n", encoding="utf-8")
    _git(repo, "add", successor.relative_to(repo).as_posix())

    assert _validate_fixture(repo, registry) == []


def test_additive_successor_can_be_frozen_by_an_appended_snapshot(tmp_path: Path) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    _git(repo, "add", registry.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "register predecessor seal")

    successor = repo / "experiments/iter238_controls/RESULT.md"
    successor.parent.mkdir(parents=True)
    successor.write_text("completed additive evidence\n", encoding="utf-8")
    _git(repo, "add", successor.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "complete successor evidence")
    source = _git(repo, "rev-parse", "HEAD")
    selector = {"kind": "tree", "path": "experiments/iter238_controls"}
    count, digest, _ = guard.build_manifest(repo, source, selector, label="successor")
    document["records"].append(
        {
            "seal_id": "fixture-successor-seal",
            "record_type": "successor_path_snapshot",
            "predecessor_seal_id": "fixture-baseline",
            "reference_commit": source,
            "protected_sets": [
                {
                    "set_id": "fixture-successor-tree",
                    "selector": selector,
                    "policy": "exact_tree",
                    "blob_count": count,
                    "manifest_sha256": digest,
                }
            ],
            "limitations": [
                "This freezes only the additive successor bytes.",
                "It supplies no semantic truth.",
            ],
        }
    )
    _write_json(registry, document)

    assert _validate_fixture(repo, registry) == []


def test_mutable_readme_only_change_passes(tmp_path: Path) -> None:
    repo, registry, _ = _temporary_registry(tmp_path)
    (repo / "README.md").write_text("a corrected mutable current surface\n", encoding="utf-8")

    assert _validate_fixture(repo, registry) == []


def test_known_bad_sealed_byte_mutation_fails(tmp_path: Path) -> None:
    repo, registry, _ = _temporary_registry(tmp_path)
    (repo / "experiments/iter237_predecessor/evidence.bin").write_bytes(b"changed\n")

    failures = _validate_fixture(repo, registry)
    assert any("protected bytes changed" in failure for failure in failures)


@pytest.mark.parametrize("operation", ["delete", "rename", "chmod", "symlink"])
def test_known_bad_sealed_path_or_mode_change_fails(
    tmp_path: Path,
    operation: str,
) -> None:
    repo, registry, _ = _temporary_registry(tmp_path)
    protected = repo / "experiments/iter237_predecessor/evidence.bin"
    if operation == "delete":
        protected.unlink()
    elif operation == "rename":
        destination = repo / "experiments/iter238_controls/renamed.bin"
        destination.parent.mkdir(parents=True)
        protected.rename(destination)
    elif operation == "chmod":
        protected.chmod(protected.stat().st_mode | 0o111)
    else:
        protected.unlink()
        protected.symlink_to(repo / "README.md")

    failures = _validate_fixture(repo, registry)
    assert failures
    assert any(
        fragment in failures[0]
        for fragment in (
            "protected file is missing",
            "protected mode changed",
            "not a regular file",
        )
    )


def test_known_bad_addition_inside_predecessor_fails(tmp_path: Path) -> None:
    repo, registry, _ = _temporary_registry(tmp_path)
    added = repo / "experiments/iter237_predecessor/new-evidence.txt"
    added.write_text("not additive\n", encoding="utf-8")

    failures = _validate_fixture(repo, registry)
    assert any("unauthorized untracked addition" in failure for failure in failures)


def test_known_bad_lookalike_successor_prefix_fails(tmp_path: Path) -> None:
    repo, registry, _ = _temporary_registry(tmp_path)
    added = repo / "experiments/iter238_controls_evil/evidence.txt"
    added.parent.mkdir(parents=True)
    added.write_text("prefix collision\n", encoding="utf-8")

    failures = _validate_fixture(repo, registry)
    assert any("unauthorized untracked addition" in failure for failure in failures)


def test_known_bad_manifest_digest_fails(tmp_path: Path) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    document["records"][0]["protected_sets"][0]["manifest_sha256"] = "0" * 64
    _write_json(registry, document)

    failures = _validate_fixture(repo, registry)
    assert any("protected manifest differs" in failure for failure in failures)


def test_known_bad_committed_record_rewrite_fails(tmp_path: Path) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    _git(repo, "add", registry.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "add append-only registry")

    rewritten = deepcopy(document)
    rewritten["records"][0]["limitations"][0] = "Rewritten in place."
    _write_json(registry, rewritten)

    failures = _validate_fixture(repo, registry)
    assert any("rewritten or reordered" in failure for failure in failures)


def test_known_bad_committed_record_removal_fails(tmp_path: Path) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    _git(repo, "add", registry.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "add append-only registry")

    replacement = deepcopy(document)
    replacement["records"] = []
    _write_json(registry, replacement)

    failures = _validate_fixture(repo, registry)
    assert failures
    assert any(
        fragment in failures[0]
        for fragment in ("records are empty", "records were removed")
    )


def test_known_bad_unrelated_reference_fails(tmp_path: Path) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    unrelated = _git(
        repo,
        "commit-tree",
        "4b825dc642cb6eb9a060e54bf8d69288fbee4904",
        "-m",
        "unrelated",
    )
    document["records"][0]["reference_commit"] = unrelated
    _write_json(registry, document)

    failures = _validate_fixture(repo, registry)
    assert any("not an ancestor of HEAD" in failure for failure in failures)
