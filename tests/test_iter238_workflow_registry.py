from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_registry_root(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / ".github", tmp_path / ".github")
    (tmp_path / "mission").mkdir()
    shutil.copy2(
        ROOT / "mission/workflow_registry.json",
        tmp_path / "mission/workflow_registry.json",
    )
    shutil.copy2(ROOT / "mission/current.json", tmp_path / "mission/current.json")
    return tmp_path


def rewrite_canonical(path: Path, document: dict) -> None:
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def load_registry() -> dict:
    return json.loads((ROOT / "mission/workflow_registry.json").read_text(encoding="utf-8"))


def pre_retirement_inventory(registry: dict) -> dict:
    rows = []
    for entry in registry["entries"]:
        state = entry["desired_server_state"]
        if entry["classification"] == "historical_retired":
            state = "active"
        rows.append(
            {
                "id": entry["workflow_id"],
                "path": entry["path"],
                "state": state,
            }
        )
    return {"total_count": len(rows), "workflows": rows}


def iter204_projection() -> dict:
    return {
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
    }


def test_repository_workflow_registry_pre_retirement_contract_is_green() -> None:
    guard = load_script("validate_workflow_registry")
    assert guard.collect_failures(pre_retirement=True) == []


def test_repository_workflow_registry_final_contract_is_green() -> None:
    guard = load_script("validate_workflow_registry")
    assert guard.collect_failures(pre_retirement=False) == []


def test_retirement_registry_digest_must_match_source_commit_blob() -> None:
    guard = load_script("validate_workflow_registry")
    registry = load_registry()
    receipt, _ = guard.load_canonical_json(
        ROOT
        / "experiments/iter238_claim_seal_workflow_controls/proof/"
        "workflow_retirement_receipt.json"
    )

    failures = guard.registry_provenance_failures(
        root=ROOT,
        current_registry=registry,
        source_commit=receipt["source_commit"],
        expected_registry_sha256="0" * 64,
    )

    assert failures == [
        "workflow retirement receipt: registry digest does not match "
        "the source_commit Git blob"
    ]


def test_retirement_source_commit_must_be_an_ancestor() -> None:
    guard = load_script("validate_workflow_registry")

    failures = guard.registry_provenance_failures(
        root=ROOT,
        current_registry=load_registry(),
        source_commit="0" * 40,
        expected_registry_sha256="0" * 64,
    )

    assert failures == [
        "workflow retirement receipt: workflow retirement source_commit "
        "is not an ancestor of HEAD"
    ]


def test_only_active_ci_digest_may_evolve_after_retirement() -> None:
    guard = load_script("validate_workflow_registry")
    source = load_registry()
    current = deepcopy(source)
    active = next(
        row
        for row in current["entries"]
        if row["path"] == ".github/workflows/ci.yml"
    )
    active["sha256"] = "f" * 64

    assert guard.registry_evolution_failures(source, current) == []


def test_historical_entry_drift_fails_retirement_provenance() -> None:
    guard = load_script("validate_workflow_registry")
    source = load_registry()
    current = deepcopy(source)
    historical = next(
        row
        for row in current["entries"]
        if row["classification"] == "historical_retired"
    )
    historical["workflow_id"] += 1

    failures = guard.registry_evolution_failures(source, current)

    assert any(
        "retirement-authorized immutable entry changed" in failure
        for failure in failures
    )


def test_platform_entry_drift_fails_retirement_provenance() -> None:
    guard = load_script("validate_workflow_registry")
    source = load_registry()
    current = deepcopy(source)
    platform = next(
        row
        for row in current["entries"]
        if row["classification"] == "platform_service"
    )
    platform["desired_server_state"] = "disabled_manually"

    failures = guard.registry_evolution_failures(source, current)

    assert any(
        "retirement-authorized immutable entry changed" in failure
        for failure in failures
    )


def test_active_ci_non_digest_evolution_fails_retirement_provenance() -> None:
    guard = load_script("validate_workflow_registry")
    source = load_registry()
    current = deepcopy(source)
    active = next(
        row
        for row in current["entries"]
        if row["path"] == ".github/workflows/ci.yml"
    )
    active["execution_authority"] = "different_authority"

    failures = guard.registry_evolution_failures(source, current)

    assert any(
        "active ci.yml evolution exceeds the SHA-256 digest-only allowance"
        in failure
        for failure in failures
    )


def test_authority_top_level_evolution_fails_retirement_provenance() -> None:
    guard = load_script("validate_workflow_registry")
    source = load_registry()
    current = deepcopy(source)
    current["repository"] = "different/repository"

    failures = guard.registry_evolution_failures(source, current)

    assert any(
        "post-retirement top-level evolution exceeds" in failure
        for failure in failures
    )


def test_synthetic_iter239_current_pointer_transition_is_permitted(
    tmp_path: Path,
) -> None:
    guard = load_script("validate_workflow_registry")
    root = copy_registry_root(tmp_path)
    registry_path = root / "mission/workflow_registry.json"
    current_path = root / "mission/current.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    source = deepcopy(registry)
    current = json.loads(current_path.read_text(encoding="utf-8"))
    next_gate = "experiments/iter239_repository_governance_gate/HYPOTHESIS.md"
    registry["active_gate"] = next_gate
    registry["updated"] = "2026-07-20"
    current["active_gate"] = next_gate
    current["updated"] = "2026-07-20"
    gate = root / next_gate
    gate.parent.mkdir(parents=True)
    gate.write_text("# Iter239 synthetic gate\n", encoding="utf-8")
    rewrite_canonical(registry_path, registry)
    rewrite_canonical(current_path, current)

    assert guard.registry_evolution_failures(source, registry) == []
    assert guard.collect_failures(root=root, pre_retirement=True) == []


def test_current_pointer_transition_must_match_mission_current(
    tmp_path: Path,
) -> None:
    guard = load_script("validate_workflow_registry")
    root = copy_registry_root(tmp_path)
    registry_path = root / "mission/workflow_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    next_gate = "experiments/iter239_repository_governance_gate/HYPOTHESIS.md"
    registry["active_gate"] = next_gate
    registry["updated"] = "2026-07-20"
    gate = root / next_gate
    gate.parent.mkdir(parents=True)
    gate.write_text("# Iter239 synthetic gate\n", encoding="utf-8")
    rewrite_canonical(registry_path, registry)

    failures = "\n".join(
        guard.collect_failures(root=root, pre_retirement=True)
    )
    assert "active gate differs from mission/current.json" in failures
    assert "updated differs from mission/current.json" in failures


def test_raw_observation_must_bind_source_registry_digest() -> None:
    guard = load_script("validate_workflow_registry")
    receipt, _ = guard.load_canonical_json(
        ROOT
        / "experiments/iter238_claim_seal_workflow_controls/proof/"
        "workflow_retirement_receipt.json"
    )
    observation, _ = guard.load_canonical_json(
        ROOT / receipt["raw_observations"][0]["path"]
    )
    observation["registry_sha256"] = "0" * 64

    failures = guard.raw_observation_binding_failures(
        observation,
        expected_source_commit=receipt["source_commit"],
        expected_registry_sha256=receipt["registry_sha256"],
        label=receipt["raw_observations"][0]["path"],
    )

    assert failures == [
        "workflow retirement receipt: raw observation registry digest differs: "
        + receipt["raw_observations"][0]["path"]
    ]


def test_raw_observation_must_bind_source_commit() -> None:
    guard = load_script("validate_workflow_registry")
    receipt, _ = guard.load_canonical_json(
        ROOT
        / "experiments/iter238_claim_seal_workflow_controls/proof/"
        "workflow_retirement_receipt.json"
    )
    observation, _ = guard.load_canonical_json(
        ROOT / receipt["raw_observations"][0]["path"]
    )
    observation["source_commit"] = "0" * 40

    failures = guard.raw_observation_binding_failures(
        observation,
        expected_source_commit=receipt["source_commit"],
        expected_registry_sha256=receipt["registry_sha256"],
        label=receipt["raw_observations"][0]["path"],
    )

    assert failures == [
        "workflow retirement receipt: raw observation source_commit differs: "
        + receipt["raw_observations"][0]["path"]
    ]


def test_raw_post_snapshot_cannot_masquerade_as_pre() -> None:
    guard = load_script("validate_workflow_registry")
    registry = load_registry()
    receipt, _ = guard.load_canonical_json(
        ROOT
        / "experiments/iter238_claim_seal_workflow_controls/proof/"
        "workflow_retirement_receipt.json"
    )
    post, _ = guard.load_canonical_json(
        ROOT / receipt["raw_observations"][1]["path"]
    )
    post["phase"] = "pre_disable"
    failures, _, _ = guard.validate_retirement_snapshot(
        post,
        registry=registry,
        historical=[
            row
            for row in registry["entries"]
            if row["classification"] == "historical_retired"
        ],
        expected_phase="post_disable",
        expected_source_commit=receipt["source_commit"],
        expected_registry_sha256=receipt["registry_sha256"],
        label="known-bad post snapshot",
    )
    assert "known-bad post snapshot: raw snapshot phase differs" in failures


def test_raw_snapshot_rejects_negative_get_count_and_empty_inventory() -> None:
    guard = load_script("validate_workflow_registry")
    registry = load_registry()
    receipt, _ = guard.load_canonical_json(
        ROOT
        / "experiments/iter238_claim_seal_workflow_controls/proof/"
        "workflow_retirement_receipt.json"
    )
    post, _ = guard.load_canonical_json(
        ROOT / receipt["raw_observations"][1]["path"]
    )
    post["get_request_count"] = -1
    post["workflow_inventory"] = {"total_count": 0, "workflows": []}
    failures, _, _ = guard.validate_retirement_snapshot(
        post,
        registry=registry,
        historical=[
            row
            for row in registry["entries"]
            if row["classification"] == "historical_retired"
        ],
        expected_phase="post_disable",
        expected_source_commit=receipt["source_commit"],
        expected_registry_sha256=receipt["registry_sha256"],
        label="known-bad post snapshot",
    )
    joined = "\n".join(failures)
    assert "get_request_count is not a positive integer" in joined
    assert "workflow inventory IDs differ from the registry" in joined


def test_raw_snapshot_rejects_conflicting_iter204_projections() -> None:
    guard = load_script("validate_workflow_registry")
    registry = load_registry()
    receipt, _ = guard.load_canonical_json(
        ROOT
        / "experiments/iter238_claim_seal_workflow_controls/proof/"
        "workflow_retirement_receipt.json"
    )
    post, _ = guard.load_canonical_json(
        ROOT / receipt["raw_observations"][1]["path"]
    )
    iter204_projection = next(
        row
        for row in post["historical_run_projections"]
        if row["workflow_id"] == guard.ITER204_ID
    )
    iter204_projection["latest_run_id"] += 1
    failures, _, _ = guard.validate_retirement_snapshot(
        post,
        registry=registry,
        historical=[
            row
            for row in registry["entries"]
            if row["classification"] == "historical_retired"
        ],
        expected_phase="post_disable",
        expected_source_commit=receipt["source_commit"],
        expected_registry_sha256=receipt["registry_sha256"],
        label="known-bad post snapshot",
    )
    assert (
        "known-bad post snapshot: iter204 event and historical projections conflict"
        in failures
    )


def test_coedited_raw_substitution_and_receipt_fail_closed(
    tmp_path: Path,
) -> None:
    guard = load_script("validate_workflow_registry")
    repository = tmp_path / "repo"
    subprocess.run(
        ["git", "clone", "-q", "--no-hardlinks", str(ROOT), str(repository)],
        check=True,
    )
    receipt_path = (
        repository
        / "experiments/iter238_claim_seal_workflow_controls/proof/"
        "workflow_retirement_receipt.json"
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    pre_path = repository / receipt["raw_observations"][0]["path"]
    post_path = repository / receipt["raw_observations"][1]["path"]
    payload = pre_path.read_bytes()
    post_path.write_bytes(payload)
    receipt["raw_observations"][1]["bytes"] = len(payload)
    receipt["raw_observations"][1]["sha256"] = guard.sha256(payload)
    rewrite_canonical(receipt_path, receipt)

    failures = "\n".join(
        guard.collect_failures(root=repository, pre_retirement=False)
    )
    assert "current bytes differ from the introducing Git blob" in failures
    assert "raw snapshot phase differs" in failures


def test_receipt_scalar_types_and_timestamp_are_strict(
    tmp_path: Path,
) -> None:
    guard = load_script("validate_workflow_registry")
    repository = tmp_path / "repo"
    subprocess.run(
        ["git", "clone", "-q", "--no-hardlinks", str(ROOT), str(repository)],
        check=True,
    )
    receipt_path = (
        repository
        / "experiments/iter238_claim_seal_workflow_controls/proof/"
        "workflow_retirement_receipt.json"
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["operation_counts"]["dispatch"] = False
    receipt["operation_counts"]["disable_puts"] = 29.0
    receipt["observed_at"] = "timeless"
    rewrite_canonical(receipt_path, receipt)

    failures = "\n".join(
        guard.collect_failures(root=repository, pre_retirement=False)
    )
    assert "operation counts differ" in failures
    assert "observed_at is not an exact UTC timestamp" in failures


def test_github_yaml_loader_preserves_on_as_a_string_key() -> None:
    guard = load_script("validate_workflow_registry")
    document = guard.parse_workflow(ROOT / ".github/workflows/ci.yml")
    assert "on" in document
    assert True not in document
    assert guard.declared_triggers(document) == ["pull_request", "push"]


def test_known_bad_executable_job_env_runner_context_fails() -> None:
    guard = load_script("validate_workflow_registry")
    fixture = (
        ROOT
        / "tests/fixtures/iter238_workflow_registry/active_job_env_runner_context.yml"
    )
    document = guard.parse_workflow(fixture)
    failures = guard.executable_job_env_runner_failures(
        document, label=str(fixture.relative_to(ROOT))
    )
    assert len(failures) == 1
    assert "job-level env" in failures[0]
    assert "unavailable runner.* context" in failures[0]


def test_registry_rejects_an_unregistered_workflow(tmp_path: Path) -> None:
    guard = load_script("validate_workflow_registry")
    root = copy_registry_root(tmp_path)
    surprise = root / ".github/workflows/surprise.yml"
    surprise.write_text(
        "name: surprise\non:\n  workflow_dispatch:\npermissions:\n  contents: read\n"
        "jobs:\n  test:\n    runs-on: ubuntu-24.04\n    steps:\n      - run: 'true'\n",
        encoding="utf-8",
    )
    failures = "\n".join(guard.collect_failures(root=root, pre_retirement=True))
    assert "unregistered=['.github/workflows/surprise.yml']" in failures


def test_registry_and_workflow_modes_must_be_regular_0644(
    tmp_path: Path,
) -> None:
    guard = load_script("validate_workflow_registry")
    root = copy_registry_root(tmp_path)
    (root / "mission/workflow_registry.json").chmod(0o755)
    (root / ".github/workflows/ci.yml").chmod(0o755)

    failures = "\n".join(
        guard.collect_failures(root=root, pre_retirement=True)
    )
    assert "workflow registry: current path is not" in failures
    assert ".github/workflows/ci.yml: current path is not" in failures


def test_registry_symlink_fails_even_when_target_bytes_are_valid(
    tmp_path: Path,
) -> None:
    guard = load_script("validate_workflow_registry")
    root = copy_registry_root(tmp_path)
    registry_path = root / "mission/workflow_registry.json"
    target = root / "mission/workflow_registry-target.json"
    shutil.copy2(registry_path, target)
    registry_path.unlink()
    registry_path.symlink_to(target.name)

    failures = "\n".join(
        guard.collect_failures(root=root, pre_retirement=True)
    )
    assert "workflow registry: current path is not" in failures


def test_registry_rejects_iter204_as_executable(tmp_path: Path) -> None:
    guard = load_script("validate_workflow_registry")
    root = copy_registry_root(tmp_path)
    path = root / "mission/workflow_registry.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    iter204 = next(
        row
        for row in document["entries"]
        if row["path"] == ".github/workflows/iter204-execute.yml"
    )
    iter204["classification"] = "active_control"
    iter204["desired_server_state"] = "active"
    iter204["execution_authority"] = "continuous_repository_verification"
    iter204["retirement_receipt"] = None
    iter204["seal_reference"] = None
    rewrite_canonical(path, document)

    failures = "\n".join(guard.collect_failures(root=root, pre_retirement=True))
    assert "unavailable runner.* context" in failures
    assert "expected exactly 29 historical workflows" in failures


def test_final_mode_requires_retirement_receipt(tmp_path: Path) -> None:
    guard = load_script("validate_workflow_registry")
    root = copy_registry_root(tmp_path)
    failures = "\n".join(guard.collect_failures(root=root, pre_retirement=False))
    assert "final retirement receipt is absent" in failures


def test_live_pre_retirement_observation_accepts_exact_inventory() -> None:
    audit = load_script("audit_workflow_server_state")
    registry = load_registry()
    failures = audit.audit_observation(
        registry=registry,
        inventory=pre_retirement_inventory(registry),
        iter204_runs=iter204_projection(),
        pre_retirement=True,
    )
    assert failures == []


def test_live_observation_rejects_unknown_server_workflow() -> None:
    audit = load_script("audit_workflow_server_state")
    registry = load_registry()
    inventory = pre_retirement_inventory(registry)
    inventory["workflows"].append(
        {"id": 999999999, "path": "dynamic/unknown", "state": "active"}
    )
    inventory["total_count"] += 1
    failures = "\n".join(
        audit.audit_observation(
            registry=registry,
            inventory=inventory,
            iter204_runs=iter204_projection(),
            pre_retirement=True,
        )
    )
    assert "unknown=[999999999]" in failures


def test_live_observation_rejects_nonzero_iter204_dispatch_history() -> None:
    audit = load_script("audit_workflow_server_state")
    registry = load_registry()
    projection = iter204_projection()
    projection["workflow_dispatch"] = {
        "latest": {"id": 123, "event": "workflow_dispatch"},
        "total_count": 1,
    }
    failures = "\n".join(
        audit.audit_observation(
            registry=registry,
            inventory=pre_retirement_inventory(registry),
            iter204_runs=projection,
            pre_retirement=True,
        )
    )
    assert "iter204 dispatch history is not exact zero" in failures


def test_current_pointer_parser_does_not_require_registry_key_order(
    tmp_path: Path,
) -> None:
    guard = load_script("validate_workflow_registry")
    current = tmp_path / "current.json"
    current.write_text(
        '{"schema_version":"telos.current.v1","active_gate":'
        '"experiments/iter238_claim_seal_workflow_controls/HYPOTHESIS.md"}\n',
        encoding="utf-8",
    )

    assert guard.load_unique_json_object(current)["schema_version"] == "telos.current.v1"
