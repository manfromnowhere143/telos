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
    root = path.parents[1]
    _git(root, "add", path.relative_to(root).as_posix())


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
    _git(repo, "add", registry.relative_to(repo).as_posix())
    return repo, registry, document


def _validate_fixture(repo: Path, registry: Path) -> list[str]:
    return guard.validate(
        repo,
        registry,
        enforce_project_baseline=False,
        check_history=True,
    )


def _commit_successor_evidence(repo: Path) -> str:
    successor = repo / "experiments/iter238_controls"
    successor.mkdir(parents=True)
    hypothesis = successor / "HYPOTHESIS.md"
    result = successor / "RESULT.md"
    hypothesis.write_text("prospective additive gate\n", encoding="utf-8")
    result.write_text("completed additive evidence\n", encoding="utf-8")
    _git(repo, "add", successor.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "complete successor evidence")
    return _git(repo, "rev-parse", "HEAD")


def _append_successor_snapshot(
    repo: Path,
    registry: Path,
    document: dict,
    source: str,
    *,
    path: str = "experiments/iter238_controls",
    seal_id: str = "fixture-successor-seal",
    predecessor_seal_id: str = "fixture-baseline",
) -> None:
    selector = {"kind": "tree", "path": path}
    count, digest, _ = guard.build_manifest(repo, source, selector, label="successor")
    document["records"].append(
        {
            "seal_id": seal_id,
            "record_type": "successor_path_snapshot",
            "predecessor_seal_id": predecessor_seal_id,
            "reference_commit": source,
            "protected_sets": [
                {
                    "set_id": f"{seal_id}-tree",
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


def _append_prospective_authorization(
    registry: Path,
    document: dict,
    reference: str,
    *,
    path: str = "experiments/iter239_ground_truth_1",
    seal_id: str = "fixture-ground-truth-authorization",
    predecessor_seal_id: str = "fixture-successor-seal",
) -> dict:
    record = {
        "seal_id": seal_id,
        "record_type": "prospective_successor_authorization",
        "predecessor_seal_id": predecessor_seal_id,
        "reference_commit": reference,
        "authorized_path": path,
        "must_be_absent_at_reference": True,
        "policy": "additions_only_until_successor_seal",
        "closure_requirement": "exact_tree_successor_path_snapshot",
        "limitations": [
            "This authorizes one absent path; it does not establish completion.",
            "Only a later exact-tree successor seal closes the authorization.",
        ],
    }
    document["records"].append(record)
    _write_json(registry, document)
    return record


def _complete_first_successor(
    repo: Path,
    registry: Path,
    document: dict,
) -> str:
    _git(repo, "add", registry.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "register predecessor seal")
    source = _commit_successor_evidence(repo)
    _append_successor_snapshot(repo, registry, document, source)
    _git(repo, "add", registry.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "seal first successor")
    return _git(repo, "rev-parse", "HEAD")


def _commit_prospective_authorization(
    repo: Path,
    registry: Path,
    document: dict,
) -> str:
    reference = _complete_first_successor(repo, registry, document)
    _append_prospective_authorization(registry, document, reference)
    _git(repo, "add", registry.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "authorize exact future experiment")
    return _git(repo, "rev-parse", "HEAD")


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

    source = _commit_successor_evidence(repo)
    assert _validate_fixture(repo, registry) == []

    _append_successor_snapshot(repo, registry, document, source)
    assert _validate_fixture(repo, registry) == []

    _git(repo, "add", registry.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "seal successor evidence")

    assert _validate_fixture(repo, registry) == []

    (repo / "README.md").write_text("later mutable surface\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-qm", "advance after successor seal")

    assert _validate_fixture(repo, registry) == []


@pytest.mark.parametrize("missing", ("HYPOTHESIS.md", "RESULT.md"))
def test_known_bad_completed_successor_requires_hypothesis_and_result(
    tmp_path: Path,
    missing: str,
) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    _git(repo, "commit", "-qm", "register predecessor seal")
    successor = repo / "experiments/iter238_controls"
    successor.mkdir(parents=True)
    retained = (
        "RESULT.md" if missing == "HYPOTHESIS.md" else "HYPOTHESIS.md"
    )
    (successor / retained).write_text("only one lifecycle record\n", encoding="utf-8")
    _git(repo, "add", successor.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "incomplete successor evidence")
    source = _git(repo, "rev-parse", "HEAD")
    _append_successor_snapshot(repo, registry, document, source)

    failures = _validate_fixture(repo, registry)

    assert any(
        f"completed successor experiments/iter238_controls/{missing} "
        "is absent or is not one exact regular Git blob" in failure
        for failure in failures
    )


def test_prospective_authorization_opens_one_path_then_requires_exact_seal(
    tmp_path: Path,
) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    _git(repo, "add", registry.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "register predecessor seal")
    source = _commit_successor_evidence(repo)
    _append_successor_snapshot(repo, registry, document, source)
    _append_prospective_authorization(registry, document, source)

    assert _validate_fixture(repo, registry) == []

    _git(repo, "add", registry.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "seal current and authorize next successor")
    assert _validate_fixture(repo, registry) == []

    future = repo / "experiments/iter239_ground_truth_1/RESULT.md"
    future.parent.mkdir(parents=True)
    hypothesis = future.with_name("HYPOTHESIS.md")
    hypothesis.write_text("future prospective gate\n", encoding="utf-8")
    future.write_text("future experiment evidence\n", encoding="utf-8")
    assert _validate_fixture(repo, registry) == []

    _git(repo, "add", future.parent.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "complete authorized future experiment")
    future_source = _git(repo, "rev-parse", "HEAD")
    _append_successor_snapshot(
        repo,
        registry,
        document,
        future_source,
        path="experiments/iter239_ground_truth_1",
        seal_id="fixture-ground-truth-seal",
        predecessor_seal_id="fixture-ground-truth-authorization",
    )

    assert _validate_fixture(repo, registry) == []

    _git(repo, "add", registry.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "seal authorized future experiment")
    assert _validate_fixture(repo, registry) == []

    future.write_text("post-seal mutation\n", encoding="utf-8")
    failures = _validate_fixture(repo, registry)
    assert any("protected bytes changed" in failure for failure in failures)


def test_sealed_addition_survives_a_two_parent_integration_merge(
    tmp_path: Path,
) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    baseline = document["records"][0]["reference_commit"]
    _git(repo, "commit", "-qm", "register predecessor seal")
    source = _commit_successor_evidence(repo)
    _append_successor_snapshot(repo, registry, document, source)
    _append_prospective_authorization(registry, document, source)
    _git(repo, "add", registry.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "seal current and authorize next successor")
    sealed_tip = _git(repo, "rev-parse", "HEAD")

    _git(repo, "checkout", "-qb", "old-master", baseline)
    (repo / "README.md").write_text("concurrent mutable correction\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-qm", "advance old master independently")
    old_master = _git(repo, "rev-parse", "HEAD")

    _git(repo, "checkout", "-q", "-")
    assert _git(repo, "rev-parse", "HEAD") == sealed_tip
    _git(repo, "merge", "--no-ff", "-qm", "two-parent integration", old_master)

    assert len(_git(repo, "rev-list", "--parents", "-n", "1", "HEAD").split()) == 3
    assert _validate_fixture(repo, registry) == []


def test_known_bad_prospective_authorization_rejects_wildcard_path(
    tmp_path: Path,
) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    reference = _complete_first_successor(repo, registry, document)
    _append_prospective_authorization(
        registry,
        document,
        reference,
        path="experiments/iter239_*",
    )

    failures = _validate_fixture(repo, registry)
    assert any("must name one literal direct child of experiments" in failure for failure in failures)


def test_known_bad_prospective_authorization_rejects_lookalike_path(
    tmp_path: Path,
) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    reference = _complete_first_successor(repo, registry, document)
    _append_prospective_authorization(registry, document, reference)
    _git(repo, "add", registry.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "authorize one exact future path")

    lookalike = repo / "experiments/iter239_ground_truth_1_evil/RESULT.md"
    lookalike.parent.mkdir(parents=True)
    lookalike.write_text("prefix collision\n", encoding="utf-8")

    failures = _validate_fixture(repo, registry)
    assert any("unauthorized untracked addition" in failure for failure in failures)


def test_known_bad_unregistered_future_experiment_is_default_denied(
    tmp_path: Path,
) -> None:
    repo, registry, _ = _temporary_registry(tmp_path)
    unregistered = repo / "experiments/iter999_unregistered/RESULT.md"
    unregistered.parent.mkdir(parents=True)
    unregistered.write_text("not authorized\n", encoding="utf-8")

    failures = _validate_fixture(repo, registry)
    assert any("unauthorized untracked addition" in failure for failure in failures)


def test_known_bad_prospective_authorization_rejects_multiple_path_field(
    tmp_path: Path,
) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    reference = _complete_first_successor(repo, registry, document)
    record = _append_prospective_authorization(registry, document, reference)
    record["authorized_paths"] = [
        record.pop("authorized_path"),
        "experiments/iter240_second_path",
    ]
    _write_json(registry, document)

    failures = _validate_fixture(repo, registry)
    assert any("missing fields: authorized_path" in failure for failure in failures)


def test_known_bad_second_authorization_cannot_open_before_first_is_sealed(
    tmp_path: Path,
) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    reference = _complete_first_successor(repo, registry, document)
    _append_prospective_authorization(registry, document, reference)
    _append_prospective_authorization(
        registry,
        document,
        reference,
        path="experiments/iter240_second_path",
        seal_id="fixture-second-authorization",
    )

    failures = _validate_fixture(repo, registry)
    assert any(
        "must immediately follow and name the latest completed successor seal" in failure
        for failure in failures
    )


def test_known_bad_committed_authorization_is_append_only(tmp_path: Path) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    reference = _complete_first_successor(repo, registry, document)
    record = _append_prospective_authorization(registry, document, reference)
    _git(repo, "add", registry.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "authorize exact future experiment")

    record["authorized_path"] = "experiments/iter240_rewritten_path"
    _write_json(registry, document)

    failures = _validate_fixture(repo, registry)
    assert any(
        fragment in failure
        for failure in failures
        for fragment in (
            "record differs at its introducing history",
            "rewritten or reordered",
        )
    )


def test_known_bad_retroactive_prospective_authorization_fails(
    tmp_path: Path,
) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    _complete_first_successor(repo, registry, document)
    future = repo / "experiments/iter239_ground_truth_1/RESULT.md"
    future.parent.mkdir(parents=True)
    future.write_text("bytes created before authorization\n", encoding="utf-8")
    _git(repo, "add", future.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "create future path before authorization")
    retroactive_reference = _git(repo, "rev-parse", "HEAD")
    _append_prospective_authorization(registry, document, retroactive_reference)

    failures = _validate_fixture(repo, registry)
    assert any("path exists at reference" in failure for failure in failures)


def test_known_bad_transient_pre_authorization_path_fails(
    tmp_path: Path,
) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    _complete_first_successor(repo, registry, document)
    future = repo / "experiments/iter239_ground_truth_1/evidence.txt"
    future.parent.mkdir(parents=True)
    future.write_text("created before authorization\n", encoding="utf-8")
    _git(repo, "add", future.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "create unauthorized future path")
    future.unlink()
    _git(repo, "add", "-u", future.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "hide unauthorized future path")
    future.parent.rmdir()
    reference = _git(repo, "rev-parse", "HEAD")
    _append_prospective_authorization(registry, document, reference)

    failures = _validate_fixture(repo, registry)
    assert any(
        "protected history contains an unauthorized transition" in failure
        for failure in failures
    )


def test_prospective_authorization_does_not_weaken_baseline_bytes(
    tmp_path: Path,
) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    reference = _complete_first_successor(repo, registry, document)
    _append_prospective_authorization(registry, document, reference)
    _git(repo, "add", registry.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "authorize future experiment")

    protected = repo / "experiments/iter237_predecessor/evidence.bin"
    protected.write_bytes(b"changed despite prospective authorization\n")

    failures = _validate_fixture(repo, registry)
    assert any("protected bytes changed" in failure for failure in failures)


def test_open_authorization_allows_same_mode_preseal_revision(
    tmp_path: Path,
) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    _commit_prospective_authorization(repo, registry, document)
    successor = repo / "experiments/iter239_ground_truth_1"
    successor.mkdir(parents=True)
    hypothesis = successor / "HYPOTHESIS.md"
    result = successor / "RESULT.md"
    hypothesis.write_text("prospective protocol\n", encoding="utf-8")
    result.write_text("first retained result\n", encoding="utf-8")
    _git(repo, "add", successor.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "add authorized future evidence")

    result.write_text("reviewed replacement result\n", encoding="utf-8")
    _git(repo, "add", result.relative_to(repo).as_posix())
    assert _validate_fixture(repo, registry) == []

    _git(repo, "commit", "-qm", "correct authorized evidence before seal")
    assert _validate_fixture(repo, registry) == []

    source = _git(repo, "rev-parse", "HEAD")
    _append_successor_snapshot(
        repo,
        registry,
        document,
        source,
        path="experiments/iter239_ground_truth_1",
        seal_id="fixture-ground-truth-seal",
        predecessor_seal_id="fixture-ground-truth-authorization",
    )
    assert _validate_fixture(repo, registry) == []
    _git(repo, "commit", "-qm", "seal corrected authorized evidence")
    assert _validate_fixture(repo, registry) == []

    result.write_text("forbidden post-seal result\n", encoding="utf-8")
    _git(repo, "add", result.relative_to(repo).as_posix())
    failures = _validate_fixture(repo, registry)
    assert any(
        fragment in failure
        for failure in failures
        for fragment in (
            "protected index bytes changed",
            "protected bytes changed",
        )
    ), failures


@pytest.mark.parametrize("operation", ["delete", "rename", "chmod", "symlink"])
def test_known_bad_open_authorization_rejects_non_additive_transition(
    tmp_path: Path,
    operation: str,
) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    _commit_prospective_authorization(repo, registry, document)
    future = repo / "experiments/iter239_ground_truth_1/evidence.txt"
    future.parent.mkdir(parents=True)
    future.write_text("first retained bytes\n", encoding="utf-8")
    _git(repo, "add", future.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "add authorized future evidence")
    renamed = future.with_name("renamed.txt")

    if operation == "delete":
        future.unlink()
    elif operation == "rename":
        future.rename(renamed)
    elif operation == "chmod":
        future.chmod(future.stat().st_mode | 0o111)
    else:
        future.unlink()
        future.symlink_to(repo / "README.md")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", f"forbidden {operation} in open authorization")

    if operation == "rename":
        renamed.rename(future)
    elif operation == "chmod":
        future.chmod(future.stat().st_mode & ~0o111)
    else:
        if future.is_symlink():
            future.unlink()
        future.write_text("first retained bytes\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "restore authorized evidence endpoint")

    failures = _validate_fixture(repo, registry)
    assert any(
        "permits only regular-file additions and same-mode pre-seal revisions" in failure
        for failure in failures
    )


def test_known_bad_open_authorization_preregistration_rewrite_is_retained(
    tmp_path: Path,
) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    _commit_prospective_authorization(repo, registry, document)
    hypothesis = repo / "experiments/iter239_ground_truth_1/HYPOTHESIS.md"
    hypothesis.parent.mkdir(parents=True)
    hypothesis.write_text("original prospective protocol\n", encoding="utf-8")
    _git(repo, "add", hypothesis.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "preregister future experiment")

    hypothesis.write_text("transient rewritten protocol\n", encoding="utf-8")
    _git(repo, "add", hypothesis.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "rewrite preregistration")
    hypothesis.write_text("original prospective protocol\n", encoding="utf-8")
    _git(repo, "add", hypothesis.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "restore preregistration endpoint")

    failures = _validate_fixture(repo, registry)
    assert any("preregistration is immutable after introduction" in failure for failure in failures)


def test_known_bad_open_authorization_staged_preregistration_rewrite_fails(
    tmp_path: Path,
) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    _commit_prospective_authorization(repo, registry, document)
    hypothesis = repo / "experiments/iter239_ground_truth_1/HYPOTHESIS.md"
    hypothesis.parent.mkdir(parents=True)
    hypothesis.write_text("original prospective protocol\n", encoding="utf-8")
    _git(repo, "add", hypothesis.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "preregister future experiment")

    hypothesis.write_text("staged rewritten protocol\n", encoding="utf-8")
    _git(repo, "add", hypothesis.relative_to(repo).as_posix())

    failures = _validate_fixture(repo, registry)
    assert any("preregistration changed in the index" in failure for failure in failures)


@pytest.mark.parametrize("operation", ["delete", "rename", "chmod", "symlink"])
def test_known_bad_open_authorization_staged_non_additive_change_fails(
    tmp_path: Path,
    operation: str,
) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    _commit_prospective_authorization(repo, registry, document)
    future = repo / "experiments/iter239_ground_truth_1/evidence.txt"
    future.parent.mkdir(parents=True)
    future.write_text("first retained bytes\n", encoding="utf-8")
    _git(repo, "add", future.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "add authorized future evidence")

    if operation == "delete":
        future.unlink()
    elif operation == "rename":
        future.rename(future.with_name("renamed.txt"))
    elif operation == "chmod":
        future.chmod(future.stat().st_mode | 0o111)
    else:
        future.unlink()
        future.symlink_to(repo / "README.md")
    _git(repo, "add", "-A")

    failures = _validate_fixture(repo, registry)
    assert any(
        fragment in failure
        for failure in failures
        for fragment in (
            "committed additive path was deleted",
            "committed additive path mode changed in the index",
            "additive successor is not a regular file",
            "prospective path is not a regular file",
            "index contains a symlink, submodule, or non-regular entry",
        )
    ), failures


def test_known_bad_open_authorization_worktree_rewrite_fails(
    tmp_path: Path,
) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    _commit_prospective_authorization(repo, registry, document)
    future = repo / "experiments/iter239_ground_truth_1/evidence.txt"
    future.parent.mkdir(parents=True)
    future.write_text("first retained bytes\n", encoding="utf-8")
    _git(repo, "add", future.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "add authorized future evidence")
    future.write_text("uncommitted replacement bytes\n", encoding="utf-8")

    failures = _validate_fixture(repo, registry)
    assert any("committed addition protected bytes changed" in failure for failure in failures)


def test_known_bad_authorized_successor_requires_exact_tree_closure(
    tmp_path: Path,
) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    reference = _complete_first_successor(repo, registry, document)
    _append_prospective_authorization(registry, document, reference)
    _git(repo, "add", registry.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "authorize future experiment")

    future = repo / "experiments/iter239_ground_truth_1/RESULT.md"
    future.parent.mkdir(parents=True)
    hypothesis = future.with_name("HYPOTHESIS.md")
    hypothesis.write_text("future prospective gate\n", encoding="utf-8")
    future.write_text("future experiment evidence\n", encoding="utf-8")
    _git(repo, "add", future.parent.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "complete future experiment")
    source = _git(repo, "rev-parse", "HEAD")
    _append_successor_snapshot(
        repo,
        registry,
        document,
        source,
        path="experiments/iter239_ground_truth_1",
        seal_id="fixture-ground-truth-seal",
        predecessor_seal_id="fixture-ground-truth-authorization",
    )
    document["records"][-1]["protected_sets"][0]["policy"] = "exact_paths"
    _write_json(registry, document)

    failures = _validate_fixture(repo, registry)
    assert any("may contain exact_tree protected sets only" in failure for failure in failures)


def test_known_bad_successor_seal_is_not_direct_child_of_reference(
    tmp_path: Path,
) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    _git(repo, "add", registry.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "register predecessor seal")
    source = _commit_successor_evidence(repo)

    note = repo / "review-note.txt"
    note.write_text("intervening commit\n", encoding="utf-8")
    _git(repo, "add", note.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "intervene before seal")

    _append_successor_snapshot(repo, registry, document, source)
    _git(repo, "add", registry.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "seal successor too late")

    failures = _validate_fixture(repo, registry)
    assert any(
        "not the single-parent direct child of its reference" in failure
        for failure in failures
    )


def test_known_bad_successor_seal_commit_has_extra_file_delta(
    tmp_path: Path,
) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    _git(repo, "add", registry.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "register predecessor seal")
    source = _commit_successor_evidence(repo)

    _append_successor_snapshot(repo, registry, document, source)
    note = repo / "review-note.txt"
    note.write_text("mixed into the seal commit\n", encoding="utf-8")
    _git(
        repo,
        "add",
        registry.relative_to(repo).as_posix(),
        note.relative_to(repo).as_posix(),
    )
    _git(repo, "commit", "-qm", "seal successor with extra delta")

    failures = _validate_fixture(repo, registry)
    assert any(
        "introducing commit changes more than mission/seal_registry.json" in failure
        for failure in failures
    )


def test_mutable_readme_only_change_passes(tmp_path: Path) -> None:
    repo, registry, _ = _temporary_registry(tmp_path)
    (repo / "README.md").write_text("a corrected mutable current surface\n", encoding="utf-8")

    assert _validate_fixture(repo, registry) == []


def test_known_bad_sealed_byte_mutation_fails(tmp_path: Path) -> None:
    repo, registry, _ = _temporary_registry(tmp_path)
    (repo / "experiments/iter237_predecessor/evidence.bin").write_bytes(b"changed\n")

    failures = _validate_fixture(repo, registry)
    assert any("protected bytes changed" in failure for failure in failures)


def test_known_bad_transient_predecessor_rewrite_fails(tmp_path: Path) -> None:
    repo, registry, _ = _temporary_registry(tmp_path)
    _git(repo, "commit", "-qm", "register predecessor seal")
    protected = repo / "experiments/iter237_predecessor/evidence.bin"
    protected.write_bytes(b"transient forbidden rewrite\n")
    _git(repo, "add", protected.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "rewrite protected predecessor")
    protected.write_bytes(b"sealed predecessor bytes\n")
    _git(repo, "add", protected.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "restore protected predecessor")

    failures = _validate_fixture(repo, registry)
    assert any(
        "protected history contains an unauthorized transition" in failure
        for failure in failures
    )


def test_known_bad_transient_successor_rewrite_fails(tmp_path: Path) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    _git(repo, "commit", "-qm", "register predecessor seal")
    source = _commit_successor_evidence(repo)
    _append_successor_snapshot(repo, registry, document, source)
    _git(repo, "add", registry.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "seal successor evidence")

    protected = repo / "experiments/iter238_controls/RESULT.md"
    protected.write_text("transient forbidden rewrite\n", encoding="utf-8")
    _git(repo, "add", protected.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "rewrite sealed successor")
    protected.write_text("completed additive evidence\n", encoding="utf-8")
    _git(repo, "add", protected.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "restore sealed successor")

    failures = _validate_fixture(repo, registry)
    assert any(
        fragment in failure
        for failure in failures
        for fragment in (
            "protected history contains an unauthorized transition",
            "protected history changed",
        )
    )


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


def test_known_bad_protected_parent_symlink_fails(tmp_path: Path) -> None:
    repo, registry, _ = _temporary_registry(tmp_path)
    protected_parent = repo / "experiments/iter237_predecessor"
    external = tmp_path / "external-protected-tree"
    protected_parent.rename(external)
    protected_parent.symlink_to(external, target_is_directory=True)

    failures = _validate_fixture(repo, registry)
    assert any("parent component is not a real directory" in failure for failure in failures)


def test_known_bad_open_addition_parent_symlink_fails(tmp_path: Path) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    _commit_prospective_authorization(repo, registry, document)
    future_parent = repo / "experiments/iter239_ground_truth_1"
    future_parent.mkdir(parents=True)
    future = future_parent / "evidence.txt"
    future.write_text("first retained bytes\n", encoding="utf-8")
    _git(repo, "add", future.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "add authorized future evidence")
    external = tmp_path / "external-open-tree"
    future_parent.rename(external)
    future_parent.symlink_to(external, target_is_directory=True)

    failures = _validate_fixture(repo, registry)
    assert any("parent component is not a real directory" in failure for failure in failures)


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


def test_known_bad_registry_worktree_mode_fails(tmp_path: Path) -> None:
    repo, registry, _ = _temporary_registry(tmp_path)
    registry.chmod(registry.stat().st_mode | 0o111)

    failures = _validate_fixture(repo, registry)
    assert any("worktree mode must be 100644" in failure for failure in failures)


def test_known_bad_registry_parent_symlink_fails(tmp_path: Path) -> None:
    repo, registry, _ = _temporary_registry(tmp_path)
    mission = registry.parent
    external = tmp_path / "external-mission"
    mission.rename(external)
    mission.symlink_to(external, target_is_directory=True)

    failures = _validate_fixture(repo, registry)
    assert any("parent component is not a real directory" in failure for failure in failures)


def test_known_bad_unstaged_successor_seal_preflight_fails(
    tmp_path: Path,
) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    _git(repo, "commit", "-qm", "register predecessor seal")
    source = _commit_successor_evidence(repo)
    _append_successor_snapshot(repo, registry, document, source)
    _git(
        repo,
        "restore",
        "--staged",
        "--source=HEAD",
        "--",
        registry.relative_to(repo).as_posix(),
    )

    failures = _validate_fixture(repo, registry)
    assert any(
        "worktree bytes differ from the stage-0 index blob" in failure
        for failure in failures
    )


def test_known_bad_transition_registry_mode_is_retained_in_history(
    tmp_path: Path,
) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    reference = _complete_first_successor(repo, registry, document)
    _append_prospective_authorization(registry, document, reference)
    registry.chmod(registry.stat().st_mode | 0o111)
    _git(repo, "add", registry.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "authorize with executable registry")
    registry.chmod(registry.stat().st_mode & ~0o111)
    _git(repo, "add", registry.relative_to(repo).as_posix())
    _git(repo, "commit", "-qm", "restore registry mode")

    failures = _validate_fixture(repo, registry)
    assert any(
        "prospective authorization introducing registry Git mode must be 100644"
        in failure
        for failure in failures
    )


def test_known_bad_merge_side_registry_rewrite_is_retained(
    tmp_path: Path,
) -> None:
    repo, registry, document = _temporary_registry(tmp_path)
    _git(repo, "commit", "-qm", "register predecessor seal")
    main_branch = _git(repo, "branch", "--show-current")

    _git(repo, "checkout", "-qb", "rewrite-side")
    rewritten = deepcopy(document)
    rewritten["records"][0]["limitations"][0] = "Transient side-branch rewrite."
    _write_json(registry, rewritten)
    _git(repo, "commit", "-qm", "rewrite registry on side branch")
    _write_json(registry, document)
    _git(repo, "commit", "-qm", "restore registry on side branch")

    _git(repo, "checkout", "-q", main_branch)
    (repo / "README.md").write_text("independent mainline change\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-qm", "advance mainline")
    _git(repo, "merge", "--no-ff", "-qm", "merge restored side branch", "rewrite-side")

    failures = _validate_fixture(repo, registry)
    assert any("registry record 0 was rewritten or reordered" in failure for failure in failures)


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
