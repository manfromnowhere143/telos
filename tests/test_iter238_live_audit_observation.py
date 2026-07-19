"""Retained-observation checks for the read-only iter238 live audit."""

import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from scripts import audit_workflow_server_state as audit
from scripts import validate_workflow_registry as lifecycle


ROOT = Path(__file__).resolve().parents[1]


def sample_observation() -> dict:
    return audit.build_observation(
        registry={"repository": "manfromnowhere143/telos"},
        registry_raw=b'{"registry":"bytes"}\n',
        inventory={
            "total_count": 1,
            "workflows": [
                {
                    "authorization": "Bearer must-not-be-retained",
                    "id": 1,
                    "path": ".github/workflows/ci.yml",
                    "state": "active",
                    "token": "must-not-be-retained",
                }
            ],
        },
        iter204_runs={
            "push": {"latest": None, "total_count": 0},
            "workflow_dispatch": {"latest": None, "total_count": 0},
        },
        observed_at="2026-07-19T12:00:00Z",
        head_commit="a" * 40,
        get_count=3,
    )


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        capture_output=True,
        check=True,
        text=True,
    )
    return result.stdout.strip()


def _write_canonical(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    path.chmod(0o644)


def _retained_fixture(
    tmp_path: Path,
) -> tuple[Path, dict, dict]:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "live-audit@example.invalid")
    _git(root, "config", "user.name", "Live Audit Test")
    _git(root, "commit", "--allow-empty", "-qm", "retirement authority")
    retirement_source = _git(root, "rev-parse", "HEAD")

    receipt_relative = (
        "experiments/iter238_claim_seal_workflow_controls/proof/"
        "workflow_retirement_receipt.json"
    )
    registry = json.loads(
        (ROOT / lifecycle.REGISTRY_RELATIVE).read_text(encoding="utf-8")
    )
    registry["retirement_receipt"] = receipt_relative
    registry_path = root / lifecycle.REGISTRY_RELATIVE
    _write_canonical(registry_path, registry)
    receipt = {
        "observed_at": "2026-07-19T09:30:43Z",
        "source_commit": retirement_source,
        "entries": [
            {
                "workflow_id": lifecycle.ITER204_ID,
                "post_dispatch_run_count": 0,
                "post_latest_run_id": 29680734026,
                "post_push_run_count": 170,
            }
        ]
    }
    _write_canonical(root / receipt_relative, receipt)
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "freeze observation authority")
    head = _git(root, "rev-parse", "HEAD")
    registry_raw = registry_path.read_bytes()
    observation = audit.build_observation(
        registry=registry,
        registry_raw=registry_raw,
        inventory={
            "total_count": len(registry["entries"]),
            "workflows": [
                {
                    "id": entry["workflow_id"],
                    "path": entry["path"],
                    "state": entry["desired_server_state"],
                }
                for entry in registry["entries"]
            ],
        },
        iter204_runs={
            "push": {
                "latest": {
                    "conclusion": "failure",
                    "created_at": "2026-07-19T08:58:04Z",
                    "event": "push",
                    "head_branch": "master",
                    "head_sha": "7307e0c1c4083443698cfde8f0ab20a27518717c",
                    "id": 29680734026,
                    "run_number": 170,
                    "status": "completed",
                },
                "total_count": 170,
            },
            "workflow_dispatch": {"latest": None, "total_count": 0},
        },
        observed_at="2026-07-19T12:00:00Z",
        head_commit=head,
        get_count=3,
    )
    _write_canonical(root / lifecycle.LIVE_OBSERVATION_RELATIVE, observation)
    result = root / lifecycle.ITER238_RESULT_RELATIVE
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text("completed evidence fixture\n", encoding="utf-8")
    result.chmod(0o644)
    _git(
        root,
        "add",
        lifecycle.LIVE_OBSERVATION_RELATIVE.as_posix(),
        lifecycle.ITER238_RESULT_RELATIVE.as_posix(),
    )
    _git(root, "commit", "-qm", "retain completed evidence")
    return root, registry, observation


def _rewrite_observation(root: Path, observation: dict) -> None:
    _write_canonical(
        root / lifecycle.LIVE_OBSERVATION_RELATIVE,
        observation,
    )


def test_live_observation_is_canonical_and_credential_free() -> None:
    document = sample_observation()
    payload = audit.canonical_observation_bytes(document)
    assert payload == (
        json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    lowered = payload.lower()
    assert b"token" not in lowered
    assert b"authorization" not in lowered
    assert b"must-not-be-retained" not in lowered
    assert document["workflow_inventory"] == {
        "total_count": 1,
        "workflows": [
            {
                "id": 1,
                "path": ".github/workflows/ci.yml",
                "state": "active",
            }
        ],
    }
    assert document["request_counts"] == {
        "delete_run": 0,
        "delete_workflow": 0,
        "disable": 0,
        "dispatch": 0,
        "enable": 0,
        "get": 3,
        "rerun": 0,
    }


def test_live_observation_round_trips_through_snapshot_loader(
    tmp_path: Path,
) -> None:
    path = tmp_path / "observation.json"
    path.write_bytes(audit.canonical_observation_bytes(sample_observation()))
    inventory, iter204 = audit.load_snapshot(path)
    assert inventory["total_count"] == 1
    assert iter204["workflow_dispatch"]["total_count"] == 0


def test_tracked_live_observation_is_never_rewritten(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(audit, "observation_path_is_tracked", lambda _root: True)
    with pytest.raises(
        audit.LiveAuditError,
        match="refusing to rewrite the tracked",
    ):
        audit.write_observation(sample_observation(), root=tmp_path)


def test_existing_untracked_live_observation_is_never_rewritten(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(audit, "observation_path_is_tracked", lambda _root: False)
    destination = tmp_path / audit.OBSERVATION_RELATIVE
    destination.parent.mkdir(parents=True)
    destination.write_text("first observation\n", encoding="utf-8")

    with pytest.raises(
        audit.LiveAuditError,
        match="refusing to overwrite an existing",
    ):
        audit.write_observation(sample_observation(), root=tmp_path)
    assert destination.read_text(encoding="utf-8") == "first observation\n"


def test_live_observation_writer_creates_mode_0644(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(audit, "observation_path_is_tracked", lambda _root: False)

    destination = audit.write_observation(sample_observation(), root=tmp_path)

    assert destination.stat().st_mode & 0o777 == 0o644


def test_live_observation_rejects_json_scalar_masquerades() -> None:
    document = sample_observation()
    document["request_counts"]["dispatch"] = False
    document["request_counts"]["get"] = 3.0
    failures = "\n".join(audit.validate_live_observation_document(document))
    assert "request counts differ" in failures


def test_live_observation_rejects_invalid_timestamp() -> None:
    document = sample_observation()
    document["observed_at"] = "2026-99-99T12:00:00Z"
    failures = "\n".join(audit.validate_live_observation_document(document))
    assert "observed_at is not an exact UTC timestamp" in failures


def test_live_observation_requires_head_committed_registry_bytes(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    (repository / "mission").mkdir(parents=True)
    registry_path = repository / audit.REGISTRY_RELATIVE
    registry_path.write_text('{"version":1}\n', encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=repository,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Telos Test"],
        cwd=repository,
        check=True,
    )
    subprocess.run(["git", "add", "."], cwd=repository, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "freeze registry"],
        cwd=repository,
        check=True,
    )
    registry_path.write_text('{"version":2}\n', encoding="utf-8")

    with pytest.raises(
        audit.LiveAuditError,
        match="registry bytes differ from the HEAD blob",
    ):
        audit.current_head_for_registry(
            registry_path.read_bytes(),
            root=repository,
        )


def test_retained_live_observation_reverifies_offline(
    tmp_path: Path,
) -> None:
    root, registry, _ = _retained_fixture(tmp_path)

    assert lifecycle.retained_live_observation_failures(
        root=root,
        registry=registry,
    ) == []


def test_completed_result_requires_retained_live_observation(
    tmp_path: Path,
) -> None:
    root, registry, _ = _retained_fixture(tmp_path)
    (root / lifecycle.LIVE_OBSERVATION_RELATIVE).unlink()

    failures = lifecycle.retained_live_observation_failures(
        root=root,
        registry=registry,
    )

    assert any("required completed-evidence artifact is absent" in failure for failure in failures)


def test_completed_result_rejects_untracked_live_observation(
    tmp_path: Path,
) -> None:
    root, registry, _ = _retained_fixture(tmp_path)
    observation = root / lifecycle.LIVE_OBSERVATION_RELATIVE
    original = observation.read_bytes()
    _git(root, "rm", "-q", observation.relative_to(root).as_posix())
    _git(root, "commit", "-qm", "remove retained observation")
    observation.parent.mkdir(parents=True, exist_ok=True)
    observation.write_bytes(original)
    observation.chmod(0o644)

    failures = lifecycle.retained_live_observation_failures(
        root=root,
        registry=registry,
    )

    assert any(
        "completed evidence requires a staged or tracked artifact" in failure
        for failure in failures
    )


def test_tracked_live_observation_must_equal_its_introducing_blob(
    tmp_path: Path,
) -> None:
    root, registry, observation = _retained_fixture(tmp_path)
    observation["observed_at"] = "2026-07-19T12:00:01Z"
    _rewrite_observation(root, observation)

    failures = lifecycle.retained_live_observation_failures(
        root=root,
        registry=registry,
    )

    assert any(
        "current bytes differ from the introducing Git blob" in failure
        for failure in failures
    )


def test_live_observation_introduction_must_directly_follow_recorded_head(
    tmp_path: Path,
) -> None:
    root, registry, observation = _retained_fixture(tmp_path)
    evidence_commit = _git(root, "rev-parse", "HEAD")
    recorded_head = observation["head_commit"]
    _git(root, "reset", "--soft", f"{recorded_head}^")
    _git(root, "commit", "-qm", "retain evidence after an intervening parent")
    assert _git(root, "rev-parse", "HEAD") != evidence_commit

    failures = lifecycle.retained_live_observation_failures(
        root=root,
        registry=registry,
    )

    assert any(
        "introducing commit is not the single-parent direct child" in failure
        for failure in failures
    )


def test_live_observation_must_strictly_postdate_retirement(
    tmp_path: Path,
) -> None:
    root, registry, observation = _retained_fixture(tmp_path)
    observation["observed_at"] = "2026-07-19T09:30:43Z"
    _rewrite_observation(root, observation)

    failures = lifecycle.retained_live_observation_failures(
        root=root,
        registry=registry,
    )

    assert any(
        "observation does not postdate the retirement receipt" in failure
        for failure in failures
    )


def test_live_observation_rejects_invalid_retirement_source_commit(
    tmp_path: Path,
) -> None:
    root, registry, _ = _retained_fixture(tmp_path)
    receipt_path = root / registry["retirement_receipt"]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["source_commit"] = "not-a-commit"
    _write_canonical(receipt_path, receipt)

    failures = lifecycle.retained_live_observation_failures(
        root=root,
        registry=registry,
    )

    assert any(
        "retirement receipt source_commit is not 40-hex" in failure
        for failure in failures
    )


def test_fabricated_hex_head_binding_fails_offline(
    tmp_path: Path,
) -> None:
    root, registry, observation = _retained_fixture(tmp_path)
    observation["head_commit"] = "f" * 40
    _rewrite_observation(root, observation)

    failures = lifecycle.retained_live_observation_failures(
        root=root,
        registry=registry,
    )

    assert any("head_commit is not an ancestor of HEAD" in failure for failure in failures)


def test_real_nonancestor_head_binding_fails_offline(
    tmp_path: Path,
) -> None:
    root, registry, observation = _retained_fixture(tmp_path)
    base = _git(root, "rev-parse", "HEAD")
    _git(root, "checkout", "-qb", "unrelated-observation-head", base)
    (root / "side.txt").write_text("side history\n", encoding="utf-8")
    _git(root, "add", "side.txt")
    _git(root, "commit", "-qm", "side history")
    side = _git(root, "rev-parse", "HEAD")
    _git(root, "checkout", "-qb", "current-history", base)
    (root / "current.txt").write_text("current history\n", encoding="utf-8")
    _git(root, "add", "current.txt")
    _git(root, "commit", "-qm", "current history")
    observation["head_commit"] = side
    _rewrite_observation(root, observation)

    failures = lifecycle.retained_live_observation_failures(
        root=root,
        registry=registry,
    )

    assert any("head_commit is not an ancestor of HEAD" in failure for failure in failures)


def test_wrong_recorded_registry_blob_digest_fails_offline(
    tmp_path: Path,
) -> None:
    root, registry, observation = _retained_fixture(tmp_path)
    assert observation["registry_sha256"] == hashlib.sha256(
        (root / lifecycle.REGISTRY_RELATIVE).read_bytes()
    ).hexdigest()
    observation["registry_sha256"] = "0" * 64
    _rewrite_observation(root, observation)

    failures = lifecycle.retained_live_observation_failures(
        root=root,
        registry=registry,
    )

    assert any(
        "registry_sha256 differs from the recorded head blob" in failure
        for failure in failures
    )


def test_recorded_head_registry_authority_cannot_be_arbitrary(
    tmp_path: Path,
) -> None:
    root, registry, observation = _retained_fixture(tmp_path)
    registry_path = root / lifecycle.REGISTRY_RELATIVE
    malicious = json.loads(registry_path.read_text(encoding="utf-8"))
    historical = next(
        entry
        for entry in malicious["entries"]
        if entry["classification"] == "historical_retired"
    )
    historical["desired_server_state"] = "active"
    _write_canonical(registry_path, malicious)
    _git(root, "add", lifecycle.REGISTRY_RELATIVE.as_posix())
    _git(root, "commit", "-qm", "introduce arbitrary recorded authority")
    malicious_head = _git(root, "rev-parse", "HEAD")
    malicious_digest = hashlib.sha256(registry_path.read_bytes()).hexdigest()
    _write_canonical(registry_path, registry)
    _git(root, "add", lifecycle.REGISTRY_RELATIVE.as_posix())
    _git(root, "commit", "-qm", "restore current lifecycle authority")
    observation["head_commit"] = malicious_head
    observation["registry_sha256"] = malicious_digest
    _rewrite_observation(root, observation)

    failures = lifecycle.retained_live_observation_failures(
        root=root,
        registry=registry,
    )

    assert any(
        "recorded-head workflow registry: retirement-authorized immutable "
        "entry changed" in failure
        for failure in failures
    )
    assert any(
        "identity/state differs from recorded-head lifecycle registry" in failure
        for failure in failures
    )


def test_altered_retained_inventory_state_fails_offline(
    tmp_path: Path,
) -> None:
    root, registry, observation = _retained_fixture(tmp_path)
    observation["workflow_inventory"]["workflows"][0]["state"] = (
        "disabled_manually"
    )
    _rewrite_observation(root, observation)

    failures = lifecycle.retained_live_observation_failures(
        root=root,
        registry=registry,
    )

    assert any(
        "identity/state differs from current lifecycle registry for "
        ".github/workflows/ci.yml" in failure
        for failure in failures
    )
