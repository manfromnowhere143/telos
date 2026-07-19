from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_driver():
    path = ROOT / "scripts/retire_historical_workflows.py"
    spec = importlib.util.spec_from_file_location("retire_historical_workflows", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeGitHubClient:
    def __init__(
        self,
        driver,
        registry: dict,
        *,
        ambiguous_applied: set[int] | None = None,
        ambiguous_unapplied: set[int] | None = None,
    ) -> None:
        self.driver = driver
        self.repository = registry["repository"]
        self.token = None
        self.get_count = 0
        self.disable_puts = 0
        self.disable_calls: list[int] = []
        self.allowed_ids = frozenset(
            row["workflow_id"]
            for row in registry["entries"]
            if row["classification"] == "historical_retired"
        )
        self.ambiguous_applied = ambiguous_applied or set()
        self.ambiguous_unapplied = ambiguous_unapplied or set()
        self.workflows = {
            row["workflow_id"]: {
                "id": row["workflow_id"],
                "name": row["path"],
                "path": row["path"],
                "state": "active",
            }
            for row in registry["entries"]
        }
        self.run_counts: dict[int, tuple[int, int | None]] = {}
        for index, workflow_id in enumerate(sorted(self.allowed_ids)):
            count = index % 4
            latest = 80000000000 + workflow_id if count else None
            self.run_counts[workflow_id] = (count, latest)
        self.run_counts[driver.ITER204_ID] = (172, 29681435632)

    def get(self, path: str, parameters: dict[str, object] | None = None):
        self.get_count += 1
        if path == "actions/workflows":
            rows = [self.workflows[key].copy() for key in sorted(self.workflows)]
            return {"total_count": len(rows), "workflows": rows}
        parts = path.split("/")
        assert parts[:2] == ["actions", "workflows"]
        workflow_id = int(parts[2])
        if len(parts) == 3:
            return self.workflows[workflow_id].copy()
        assert parts[3] == "runs"
        event = (parameters or {}).get("event")
        if workflow_id == self.driver.ITER204_ID and event == "workflow_dispatch":
            return {"total_count": 0, "workflow_runs": []}
        count, latest = self.run_counts[workflow_id]
        rows = [] if latest is None else [{"id": latest}]
        if workflow_id == self.driver.ITER204_ID and event == "push":
            rows = (
                []
                if latest is None
                else [
                    {
                        "conclusion": "failure",
                        "created_at": "2026-07-19T09:21:39Z",
                        "event": "push",
                        "head_branch": "agent/iter238-claim-seal-workflow-controls",
                        "head_sha": "bd5595fe03ee7784c8257205b1285eafc66b7584",
                        "id": latest,
                        "run_number": count,
                        "status": "completed",
                    }
                ]
            )
        return {"total_count": count, "workflow_runs": rows}

    def disable(self, workflow_id: int) -> None:
        if workflow_id not in self.allowed_ids:
            raise self.driver.RetirementError("uncommitted ID")
        self.disable_puts += 1
        self.disable_calls.append(workflow_id)
        if workflow_id in self.ambiguous_unapplied:
            raise self.driver.AmbiguousDisableError("ambiguous and not applied")
        self.workflows[workflow_id]["state"] = "disabled_manually"
        if workflow_id in self.ambiguous_applied:
            raise self.driver.AmbiguousDisableError("ambiguous but applied")


def registry_document() -> dict:
    return json.loads((ROOT / "mission/workflow_registry.json").read_text(encoding="utf-8"))


def test_registry_must_equal_its_head_blob_and_iter204_is_first() -> None:
    driver = load_driver()
    registry, raw, head = driver.load_committed_registry(ROOT)
    assert driver.sha256(raw) == (
        "f9b41f0d0b79a9056982d4e556e6ccf95f0f69e15643eba8af8d39bbfa6e6f55"
    )
    assert len(head) == 40
    ordered = driver.historical_entries(registry)
    assert len(ordered) == 29
    assert ordered[0]["workflow_id"] == driver.ITER204_ID


def test_mutation_client_exposes_only_allowlisted_disable_put() -> None:
    driver = load_driver()
    source = (ROOT / "scripts/retire_historical_workflows.py").read_text(
        encoding="utf-8"
    )
    assert 'method="PUT"' in source
    assert 'f"{workflow_id}/disable"' in source
    for forbidden in (
        'f"{workflow_id}/dispatches"',
        'f"{workflow_id}/rerun"',
        'f"{workflow_id}/enable"',
        'f"{workflow_id}/cancel"',
    ):
        assert forbidden not in source
    client = driver.GitHubWorkflowMutationClient(
        repository=driver.REPOSITORY,
        allowed_ids={1},
    )
    with pytest.raises(driver.RetirementError, match="uncommitted workflow ID"):
        client.disable(2)
    assert client.disable_puts == 0


def test_default_dry_run_performs_gets_but_no_puts_or_writes(tmp_path: Path) -> None:
    driver = load_driver()
    registry = registry_document()
    client = FakeGitHubClient(driver, registry)
    result = driver.execute_retirement(
        client=client,
        root=ROOT,
        output_root=tmp_path,
        execute=False,
    )
    assert result is None
    assert client.get_count > 0
    assert client.disable_puts == 0
    assert client.disable_calls == []
    assert list(tmp_path.rglob("*")) == []


def test_execute_disables_only_committed_ids_and_writes_canonical_evidence(
    tmp_path: Path,
) -> None:
    driver = load_driver()
    registry = registry_document()
    client = FakeGitHubClient(driver, registry)
    receipt = driver.execute_retirement(
        client=client,
        root=ROOT,
        output_root=tmp_path,
        execute=True,
    )
    assert receipt is not None
    assert len(client.disable_calls) == 29
    assert client.disable_calls[0] == driver.ITER204_ID
    assert set(client.disable_calls) == set(client.allowed_ids)
    assert all(
        client.workflows[workflow_id]["state"] == "disabled_manually"
        for workflow_id in client.allowed_ids
    )
    assert receipt["operation_counts"] == {
        "delete_run": 0,
        "delete_workflow": 0,
        "disable_puts": 29,
        "dispatch": 0,
        "enable": 0,
        "rerun": 0,
    }
    assert receipt["entries"][0]["workflow_id"] == driver.ITER204_ID
    iter204 = receipt["entries"][0]
    assert iter204["pre_push_run_count"] == 172
    assert iter204["post_push_run_count"] == 172
    assert iter204["pre_dispatch_run_count"] == 0
    assert iter204["post_dispatch_run_count"] == 0
    for relative in (driver.PRE_RELATIVE, driver.POST_RELATIVE, driver.RECEIPT_RELATIVE):
        path = tmp_path / relative
        assert path.is_file()
        document = json.loads(path.read_text(encoding="utf-8"))
        assert path.read_bytes() == driver.canonical_bytes(document)


def test_ambiguous_applied_disable_is_resolved_by_get(tmp_path: Path) -> None:
    driver = load_driver()
    registry = registry_document()
    client = FakeGitHubClient(
        driver,
        registry,
        ambiguous_applied={driver.ITER204_ID},
    )
    receipt = driver.execute_retirement(
        client=client,
        root=ROOT,
        output_root=tmp_path,
        execute=True,
    )
    assert receipt is not None
    assert client.disable_puts == 29
    assert receipt["operation_counts"]["disable_puts"] == 29


def test_ambiguous_unapplied_disable_fails_closed_without_receipt(
    tmp_path: Path,
) -> None:
    driver = load_driver()
    registry = registry_document()
    client = FakeGitHubClient(
        driver,
        registry,
        ambiguous_unapplied={driver.ITER204_ID},
    )
    with pytest.raises(driver.RetirementError, match="did not prove disabled_manually"):
        driver.execute_retirement(
            client=client,
            root=ROOT,
            output_root=tmp_path,
            execute=True,
        )
    assert client.disable_calls == [driver.ITER204_ID]
    assert (tmp_path / driver.PRE_RELATIVE).is_file()
    assert not (tmp_path / driver.POST_RELATIVE).exists()
    assert not (tmp_path / driver.RECEIPT_RELATIVE).exists()


def test_mid_sequence_failure_retains_only_pre_snapshot(tmp_path: Path) -> None:
    driver = load_driver()
    registry = registry_document()
    second_id = driver.historical_entries(registry)[1]["workflow_id"]
    client = FakeGitHubClient(
        driver,
        registry,
        ambiguous_unapplied={second_id},
    )
    with pytest.raises(driver.RetirementError, match="did not prove disabled_manually"):
        driver.execute_retirement(
            client=client,
            root=ROOT,
            output_root=tmp_path,
            execute=True,
        )
    assert client.disable_calls == [driver.ITER204_ID, second_id]
    assert (tmp_path / driver.PRE_RELATIVE).is_file()
    assert not (tmp_path / driver.POST_RELATIVE).exists()
    assert not (tmp_path / driver.RECEIPT_RELATIVE).exists()


def test_allowlist_mismatch_fails_before_any_get_or_put(tmp_path: Path) -> None:
    driver = load_driver()
    registry = registry_document()
    client = FakeGitHubClient(driver, registry)
    client.allowed_ids = frozenset(set(client.allowed_ids) | {999999999})
    with pytest.raises(driver.RetirementError, match="allowlist differs"):
        driver.execute_retirement(
            client=client,
            root=ROOT,
            output_root=tmp_path,
            execute=True,
        )
    assert client.get_count == 0
    assert client.disable_puts == 0


def test_existing_evidence_fails_before_any_get_or_put(tmp_path: Path) -> None:
    driver = load_driver()
    registry = registry_document()
    client = FakeGitHubClient(driver, registry)
    target = tmp_path / driver.RECEIPT_RELATIVE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("do not overwrite\n", encoding="utf-8")
    with pytest.raises(driver.RetirementError, match="refusing to overwrite"):
        driver.execute_retirement(
            client=client,
            root=ROOT,
            output_root=tmp_path,
            execute=True,
        )
    assert client.get_count == 0
    assert client.disable_puts == 0
    assert target.read_text(encoding="utf-8") == "do not overwrite\n"


def test_cli_execute_rejects_noncanonical_output_root(tmp_path: Path) -> None:
    driver = load_driver()
    with pytest.raises(driver.RetirementError, match="exact registered successor"):
        driver.validate_cli_output_root(execute=True, output_root=tmp_path)
    driver.validate_cli_output_root(execute=False, output_root=tmp_path)
    driver.validate_cli_output_root(
        execute=True,
        output_root=driver.DEFAULT_OUTPUT_ROOT,
    )


def test_registry_descendant_change_fails_head_blob_equality(tmp_path: Path) -> None:
    driver = load_driver()
    repository = tmp_path / "repo"
    (repository / "mission").mkdir(parents=True)
    shutil.copy2(
        ROOT / "mission/workflow_registry.json",
        repository / "mission/workflow_registry.json",
    )
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
    subprocess.run(["git", "add", "mission/workflow_registry.json"], cwd=repository, check=True)
    subprocess.run(["git", "commit", "-qm", "freeze registry"], cwd=repository, check=True)
    path = repository / "mission/workflow_registry.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["updated"] = "2099-01-01"
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(driver.RetirementError, match="differ from the HEAD blob"):
        driver.load_committed_registry(repository)
