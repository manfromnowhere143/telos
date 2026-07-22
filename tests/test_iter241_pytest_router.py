"""Adversarial tests for iter241's authenticated pre-pytest routing boundary."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tomllib
from typing import Any

import pytest

from scripts import route_iter241_pytest as router
from scripts import run_iter241_pytest as runner
from scripts.validate_seal_registry import build_manifest


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class RoutingFixture:
    root: Path
    contract: router.RoutingContract
    execution_marker: Path


def _git(
    root: Path,
    *arguments: str,
    input_bytes: bytes | None = None,
) -> bytes:
    completed = subprocess.run(
        ["/usr/bin/git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        input=input_bytes,
    )
    return completed.stdout


def _commit_all(root: Path, message: str) -> str:
    _git(root, "add", "--all")
    _git(root, "commit", "-q", "-m", message)
    return _git(root, "rev-parse", "HEAD").decode("ascii").strip()


def _commit_tree(root: Path, tree: str, parents: tuple[str, ...], message: str) -> str:
    arguments = ["commit-tree", tree]
    for parent in parents:
        arguments.extend(("-p", parent))
    return _git(root, *arguments, input_bytes=f"{message}\n".encode()).decode("ascii").strip()


def _tree(root: Path, commit: str) -> str:
    return _git(root, "show", "-s", "--format=%T", commit).decode("ascii").strip()


def _write_json(path: Path, document: dict[str, Any]) -> bytes:
    raw = (json.dumps(document, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return raw


def _correction_receipt() -> dict[str, Any]:
    return {
        "schema_version": "telos.iter241.repository_closure_correction.v1",
        "adjudication": dict(router.EXPECTED_STATUS_ITEMS),
        "defect": {
            "retained_pull_request": {
                "contract_acceptance": False,
                "merge_commit_sha_classification": "omitted",
                "merge_commit_sha_member_present": False,
                "original_projection_value": None,
            },
            "retained_response_headers": {
                "capture_completeness": "failed",
                "contract_acceptance": False,
                "exact_header_section_bytes_reconstructible": False,
                "raw_header_byte_fidelity": "failed",
                "raw_header_section_bytes_retained": False,
                "retained_representation": "canonicalized_returned_header_pair_documents",
                "source_api": "http.client.HTTPResponse.getheaders",
            },
        },
        "original_attempt": {"retry_authority": "none"},
    }


def _delegate_source(marker: Path) -> bytes:
    return (
        "from pathlib import Path\n"
        "import os\n"
        "import subprocess\n"
        "root = Path(__file__).resolve().parents[1]\n"
        "git_dir = Path(os.environ['GIT_DIR'])\n"
        "expected = {\n"
        "    'GIT_ATTR_NOSYSTEM': '1',\n"
        "    'GIT_CONFIG_GLOBAL': '/dev/null',\n"
        "    'GIT_CONFIG_LOCAL': '/dev/null',\n"
        "    'GIT_CONFIG_NOSYSTEM': '1',\n"
        "    'GIT_CONFIG_SYSTEM': '/dev/null',\n"
        "    'GIT_CONFIG_WORKTREE': '/dev/null',\n"
        "    'GIT_NO_REPLACE_OBJECTS': '1',\n"
        "    'PATH': '/usr/bin:/bin',\n"
        "    'PYTHONNOUSERSITE': '1',\n"
        "}\n"
        "assert all(os.environ.get(key) == value for key, value in expected.items())\n"
        "assert os.environ['GIT_WORK_TREE'] == str(root)\n"
        "assert git_dir.is_absolute() and git_dir != root / '.git'\n"
        "assert git_dir.name.startswith('telos-iter241-git-')\n"
        "assert (git_dir / 'config').is_file()\n"
        "assert not ({'GIT_OBJECT_DIRECTORY', 'GIT_REPLACE_REF_BASE', 'PYTHONPATH'} "
        "& set(os.environ))\n"
        "subprocess.run(['git', 'rev-parse', 'HEAD'], check=True, capture_output=True)\n"
        "subprocess.run(['git', 'ls-files', '--stage'], check=True, capture_output=True)\n"
        "subprocess.run(['git', 'diff', '--name-status', 'HEAD^', 'HEAD'], "
        "check=True, capture_output=True)\n"
        f"Path({str(marker)!r}).write_text('executed\\n', encoding='utf-8')\n"
    ).encode()


def _authorization_record(
    *,
    seal_id: str,
    predecessor_id: str,
    reference: str,
    limitations: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "seal_id": seal_id,
        "record_type": "prospective_successor_authorization",
        "predecessor_seal_id": predecessor_id,
        "reference_commit": reference,
        "authorized_path": router.ITER241_PATH,
        "must_be_absent_at_reference": True,
        "policy": "additions_only_until_successor_seal",
        "closure_requirement": "exact_tree_successor_path_snapshot",
        "limitations": list(limitations),
    }


def _build_routing_fixture(tmp_path: Path, scenario: str = "valid") -> RoutingFixture:
    root = (tmp_path / "repo").resolve()
    root.mkdir()
    _git(root.parent, "init", "-q", str(root))
    _git(root, "config", "user.name", "Router Test")
    _git(root, "config", "user.email", "router@example.invalid")

    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    base = _commit_all(root, "base")
    base_tree = _tree(root, base)

    iter240 = root / "experiments/iter240_ground_truth_admission_design"
    iter240.mkdir(parents=True)
    (iter240 / "HYPOTHESIS.md").write_text("sealed iter240\n", encoding="utf-8")
    sealed = _commit_all(root, "sealed iter240")
    sealed_tree = _tree(root, sealed)
    sealed_subtree = (
        _git(root, "rev-parse", f"{sealed}:experiments/iter240_ground_truth_admission_design")
        .decode("ascii")
        .strip()
    )
    predecessor = _commit_tree(root, base_tree, (base,), "predecessor")
    governed_merge = _commit_tree(
        root,
        sealed_tree,
        (predecessor, sealed),
        "governed merge",
    )
    side_parent = _commit_tree(root, sealed_tree, (base,), "authorization side")
    authorization = _commit_tree(
        root,
        sealed_tree,
        (governed_merge, side_parent),
        "authorization merge",
    )
    _git(root, "reset", "--hard", authorization)

    iter241 = root / router.ITER241_PATH
    (iter241 / "proof").mkdir(parents=True)
    (iter241 / "HYPOTHESIS.md").write_text("failed attempt\n", encoding="utf-8")
    (iter241 / "RESULT.md").write_text(
        "capture_completeness failed; raw_header_byte_fidelity failed; retry none\n",
        encoding="utf-8",
    )
    receipt_raw = _write_json(root / router.CORRECTION_RECEIPT_PATH, _correction_receipt())

    execution_marker = root / "delegate-executed.txt"
    delegate_raw = _delegate_source(execution_marker)
    seal_validator = root / router.SEAL_VALIDATOR_PATH
    seal_validator.parent.mkdir(parents=True)
    seal_validator.write_bytes(delegate_raw)
    receipt_sealing = root / router.RECEIPT_SEALING_PATH
    receipt_sealing.write_text("# frozen receipt dependency\n", encoding="utf-8")
    correction_adjudicator = root / router.CORRECTION_ADJUDICATOR_PATH
    correction_adjudicator.write_bytes(delegate_raw)
    frozen_validator = root / router.FROZEN_VALIDATOR_PATH
    frozen_validator.write_text("# frozen validator\n", encoding="utf-8")
    frozen_test = root / router.FROZEN_TEST_PATH
    frozen_test.parent.mkdir(parents=True)
    frozen_test.write_text("# frozen exact-HEAD tests\n", encoding="utf-8")
    collection_test = root / "tests/test_expected_collection.py"
    collection_test.write_text(
        "def test_expected_collection():\n    assert True\n",
        encoding="utf-8",
    )
    pyproject = root / router.PYPROJECT_PATH
    pyproject.write_text("[tool.pytest.ini_options]\ntestpaths = ['tests']\n", encoding="utf-8")

    authorization_id = "fixture-iter241-authorization"
    authorization_predecessor = "fixture-iter240-seal"
    authorization_limitations = (
        "This fixture authorizes one absent iter241 path only.",
        "Authorization is not completion or scientific authority.",
    )
    authorization_record = _authorization_record(
        seal_id=authorization_id,
        predecessor_id=authorization_predecessor,
        reference=governed_merge,
        limitations=authorization_limitations,
    )
    registry_path = root / router.REGISTRY_PATH
    _write_json(
        registry_path,
        {
            "schema_version": "fixture.seal-registry.v1",
            "claim_boundary": "Byte identity is not semantic truth.",
            "records": [authorization_record],
        },
    )
    correction = _commit_all(root, "retain correction")
    reference = correction

    iter241_subtree = (
        _git(root, "rev-parse", f"{reference}:{router.ITER241_PATH}").decode("ascii").strip()
    )
    count, manifest, _blobs = build_manifest(
        root,
        reference,
        {"kind": "tree", "path": router.ITER241_PATH},
        label="fixture iter241",
    )
    successor_limitations = (
        "This fixture freezes exact bytes without establishing semantic truth.",
        "The failed capture remains failed and no retry is authorized.",
    )
    contract = router.RoutingContract(
        authorization_commit=authorization,
        authorization_tree=sealed_tree,
        authorization_parents=(governed_merge, side_parent),
        sealed_iter240_commit=sealed,
        sealed_iter240_parent=base,
        sealed_iter240_tree=sealed_tree,
        sealed_iter240_subtree=sealed_subtree,
        governed_merge=governed_merge,
        governed_merge_tree=sealed_tree,
        governed_merge_parents=(predecessor, sealed),
        correction_checkpoint=correction,
        correction_checkpoint_subtree=iter241_subtree,
        iter241_subtree=iter241_subtree,
        iter241_blob_count=count,
        correction_receipt_sha256=hashlib.sha256(receipt_raw).hexdigest(),
        correction_adjudicator_sha256=hashlib.sha256(delegate_raw).hexdigest(),
        seal_registry_validator_sha256=hashlib.sha256(delegate_raw).hexdigest(),
        receipt_sealing_sha256=hashlib.sha256(receipt_sealing.read_bytes()).hexdigest(),
        frozen_validator_sha256=hashlib.sha256(frozen_validator.read_bytes()).hexdigest(),
        frozen_test_sha256=hashlib.sha256(frozen_test.read_bytes()).hexdigest(),
        pyproject_sha256=hashlib.sha256(pyproject.read_bytes()).hexdigest(),
        authorization_seal_id=authorization_id,
        authorization_predecessor_id=authorization_predecessor,
        authorization_record_sha256=router._canonical_digest(authorization_record),
        authorization_limitations=authorization_limitations,
        successor_seal_id="fixture-iter241-completed-evidence-seal",
        successor_set_id="fixture-iter241-completed-evidence-tree",
        successor_limitations=successor_limitations,
        successor_limitations_sha256=router._canonical_digest(list(successor_limitations)),
    )

    if scenario == "unsealed_descendant":
        (root / "unsealed.txt").write_text("ancestry alone is insufficient\n", encoding="utf-8")
        _commit_all(root, "unsealed descendant")
        return RoutingFixture(root, contract, execution_marker)

    record_reference = reference
    if scenario == "non_descendant":
        record_reference = _commit_tree(
            root,
            _tree(root, reference),
            (reference,),
            "unmerged reference",
        )
    successor = {
        "seal_id": contract.successor_seal_id,
        "record_type": "successor_path_snapshot",
        "predecessor_seal_id": authorization_id,
        "reference_commit": record_reference,
        "protected_sets": [
            {
                "set_id": contract.successor_set_id,
                "selector": {"kind": "tree", "path": router.ITER241_PATH},
                "policy": "exact_tree",
                "blob_count": count,
                "manifest_sha256": manifest,
            }
        ],
        "limitations": list(successor_limitations),
    }
    if scenario == "wrong_predecessor":
        successor["predecessor_seal_id"] = "wrong-authorization"
    elif scenario == "wrong_seal_id":
        successor["seal_id"] = "wrong-successor-seal"
    elif scenario == "wrong_set_id":
        successor["protected_sets"][0]["set_id"] = "wrong-protected-set"
    elif scenario == "stale_manifest":
        successor["protected_sets"][0]["manifest_sha256"] = "0" * 64
    elif scenario == "missing_reference":
        successor["reference_commit"] = "0" * 40
    elif scenario == "wrong_record_type":
        successor["record_type"] = "prospective_successor_authorization"
    elif scenario == "contradictory_limitations":
        successor["limitations"][-1] = "Repository closure is supported and retry is authorized."
    records = [authorization_record, successor]
    if scenario == "wrong_authorization_field":
        records[0] = {**authorization_record, "must_be_absent_at_reference": False}
    if scenario == "ambiguous":
        duplicate = json.loads(json.dumps(successor))
        duplicate["seal_id"] = "fixture-duplicate-seal"
        records.append(duplicate)
    _write_json(
        registry_path,
        {
            "schema_version": "fixture.seal-registry.v1",
            "claim_boundary": "Byte identity is not semantic truth.",
            "records": records,
        },
    )
    _commit_all(root, "register successor seal")

    if scenario == "changed_subtree":
        (iter241 / "RESULT.md").write_text("rewritten result\n", encoding="utf-8")
        _commit_all(root, "drift iter241 subtree")
    elif scenario == "validator_drift":
        seal_validator.write_text(
            f"from pathlib import Path\nPath({str(execution_marker)!r}).write_text('bypass')\n",
            encoding="utf-8",
        )
    elif scenario == "dependency_drift":
        receipt_sealing.write_text(
            f"from pathlib import Path\nPath({str(execution_marker)!r}).write_text('bypass')\n",
            encoding="utf-8",
        )
    elif scenario == "registry_worktree_drift":
        registry_path.write_text("{}\n", encoding="utf-8")
    elif scenario == "object_indirection":
        alternates = root / ".git/objects/info/alternates"
        alternates.write_text("/tmp/untrusted-objects\n", encoding="utf-8")
    elif scenario == "replace_ref":
        replace_root = root / ".git/refs/replace"
        replace_root.mkdir(parents=True)
        (replace_root / correction).write_text(f"{base}\n", encoding="ascii")
    return RoutingFixture(root, contract, execution_marker)


def _qualify(fixture: RoutingFixture) -> router.SealQualification:
    return router._qualify(fixture.root, fixture.contract)


def _head(root: Path) -> str:
    return _git(root, "rev-parse", "HEAD^{commit}").decode("ascii").strip()


def test_current_default_contract_matches_exact_successor_state() -> None:
    result = router.seal_qualification(ROOT)
    registry = json.loads((ROOT / router.REGISTRY_PATH).read_text(encoding="utf-8"))
    successors = [
        record
        for record in registry["records"]
        if record.get("seal_id") == router.DEFAULT_CONTRACT.successor_seal_id
    ]
    if successors:
        assert result == router.SealQualification(
            True,
            "seal_qualified",
            successors[0]["reference_commit"],
            _head(ROOT),
        )
    else:
        assert result == router.SealQualification(
            False,
            "successor_record_absent_or_ambiguous",
            source_commit=_head(ROOT),
        )


def test_default_contract_exactly_binds_authorization_and_future_names() -> None:
    context = router._discover_git_context(ROOT)
    registry = router._strict_object(
        (ROOT / router.REGISTRY_PATH).read_bytes(),
        label="registry",
    )
    router._authorization_record(registry, router.DEFAULT_CONTRACT)
    assert router.DEFAULT_CONTRACT.successor_seal_id == "iter241-completed-evidence-seal"
    assert router.DEFAULT_CONTRACT.successor_set_id == "iter241-completed-evidence-tree"
    assert router._canonical_digest(list(router.SUCCESSOR_LIMITATIONS)) == (
        router.DEFAULT_CONTRACT.successor_limitations_sha256
    )
    assert router._tree_oid(
        context,
        router.DEFAULT_CONTRACT.correction_checkpoint,
        router.ITER241_PATH,
    ) == router.DEFAULT_CONTRACT.correction_checkpoint_subtree
    assert router.DEFAULT_CONTRACT.correction_checkpoint_subtree == (
        "75c90ec47db8b657f9926c33be3b8848d6df1052"
    )
    assert router.DEFAULT_CONTRACT.iter241_subtree == (
        "5b963e4824ae2b2b7e8ccc0d5cf9fd37c222db10"
    )


def test_valid_synthetic_successor_qualifies_before_pytest(tmp_path: Path) -> None:
    fixture = _build_routing_fixture(tmp_path)
    result = _qualify(fixture)
    assert result.qualified is True
    assert result.reason == "seal_qualified"
    assert result.source_commit == _head(fixture.root)
    assert fixture.execution_marker.read_text(encoding="utf-8") == "executed\n"
    argv = router.authoritative_pytest_argv(
        result,
        python_executable=sys.executable,
        root=fixture.root,
    )
    assert argv[-2:] == tuple(f"--deselect={nodeid}" for nodeid in router.FROZEN_EXACT_HEAD_NODEIDS)


@pytest.mark.parametrize(
    ("scenario", "reason"),
    (
        ("unsealed_descendant", "successor_record_absent_or_ambiguous"),
        ("wrong_predecessor", "successor_predecessor_mismatch"),
        ("wrong_seal_id", "successor_seal_id_mismatch"),
        ("wrong_set_id", "successor_protected_set_invalid"),
        ("stale_manifest", "successor_manifest_mismatch"),
        ("changed_subtree", "current_iter241_subtree_mismatch"),
        ("missing_reference", "successor_reference_missing"),
        ("non_descendant", "successor_reference_not_ancestor"),
        ("wrong_record_type", "successor_record_type_invalid"),
        ("contradictory_limitations", "successor_limitations_mismatch"),
        ("wrong_authorization_field", "authorization_record_mismatch"),
        ("ambiguous", "successor_record_absent_or_ambiguous"),
        ("registry_worktree_drift", "seal_registry_not_committed_clean"),
        ("object_indirection", "git_object_indirection"),
        ("replace_ref", "git_replace_ref_present"),
    ),
)
def test_known_bad_authority_state_fails_closed(
    tmp_path: Path,
    scenario: str,
    reason: str,
) -> None:
    fixture = _build_routing_fixture(tmp_path, scenario)
    expected_source = (
        None if scenario in {"object_indirection", "replace_ref"} else _head(fixture.root)
    )
    assert _qualify(fixture) == router.SealQualification(
        False,
        reason,
        source_commit=expected_source,
    )


def test_validator_drift_is_denied_before_execution(tmp_path: Path) -> None:
    fixture = _build_routing_fixture(tmp_path, "validator_drift")
    fixture.execution_marker.unlink(missing_ok=True)
    assert _qualify(fixture) == router.SealQualification(
        False,
        "seal_validator_identity_mismatch",
        source_commit=_head(fixture.root),
    )
    assert not fixture.execution_marker.exists()


def test_transitive_dependency_drift_is_denied_before_execution(tmp_path: Path) -> None:
    fixture = _build_routing_fixture(tmp_path, "dependency_drift")
    fixture.execution_marker.unlink(missing_ok=True)
    assert _qualify(fixture) == router.SealQualification(
        False,
        "receipt_sealing_identity_mismatch",
        source_commit=_head(fixture.root),
    )
    assert not fixture.execution_marker.exists()


def test_git_and_delegate_environment_poisoning_is_removed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _build_routing_fixture(tmp_path)
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_git_marker = tmp_path / "fake-git-executed"
    fake_git = fake_bin / "git"
    fake_git.write_text(
        f"#!/bin/sh\ntouch {fake_git_marker}\nexit 99\n",
        encoding="utf-8",
    )
    fake_git.chmod(0o755)
    poison_config = tmp_path / "poison.gitconfig"
    poison_config.write_text("[alias]\nshow = !false\n", encoding="utf-8")
    poison_object_dir = tmp_path / "objects"
    poison_object_dir.mkdir()
    config_exec_marker = tmp_path / "config-exec"
    config_exec = tmp_path / "config-exec.sh"
    config_exec.write_text(
        f"#!/bin/sh\ntouch {config_exec_marker}\nexit 91\n",
        encoding="utf-8",
    )
    config_exec.chmod(0o755)
    _git(fixture.root, "config", "core.fsmonitor", str(config_exec))
    _git(fixture.root, "config", "diff.external", str(config_exec))
    for key, value in {
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_GLOBAL": str(poison_config),
        "GIT_CONFIG_KEY_0": "alias.show",
        "GIT_CONFIG_VALUE_0": "!false",
        "GIT_DIR": str(tmp_path / "wrong-git-dir"),
        "GIT_EXEC_PATH": str(fake_bin),
        "GIT_OBJECT_DIRECTORY": str(poison_object_dir),
        "GIT_REPLACE_REF_BASE": "refs/poison/",
        "PATH": str(fake_bin),
        "PYTHONPATH": str(tmp_path / "poison-python"),
    }.items():
        monkeypatch.setenv(key, value)

    assert _qualify(fixture).qualified is True
    assert not fake_git_marker.exists()
    assert not config_exec_marker.exists()


def test_runner_authenticates_router_before_execution(tmp_path: Path) -> None:
    root = tmp_path / "candidate"
    root.mkdir()
    _git(root.parent, "init", "-q", str(root))
    _git(root, "config", "user.name", "Runner Authentication Test")
    _git(root, "config", "user.email", "runner-authentication@example.invalid")
    for relative in (runner.ROUTER_PATH, *runner.AUTHENTICATED_SOURCES):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    _commit_all(root, "retain authenticated sources")
    marker = tmp_path / "router-executed"
    (root / runner.ROUTER_PATH).write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n",
        encoding="utf-8",
    )
    with pytest.raises(runner.RunnerError, match="authenticated source differs"):
        runner.authenticate_before_router_execution(root)
    assert not marker.exists()


def test_runner_rejects_head_or_index_drift_before_router_execution(tmp_path: Path) -> None:
    root = tmp_path / "candidate"
    root.mkdir()
    _git(root.parent, "init", "-q", str(root))
    _git(root, "config", "user.name", "Runner Git Identity Test")
    _git(root, "config", "user.email", "runner-git-identity@example.invalid")
    for relative in (runner.ROUTER_PATH, *runner.AUTHENTICATED_SOURCES):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    _commit_all(root, "retain authenticated sources")

    router_path = root / runner.ROUTER_PATH
    router_raw = router_path.read_bytes()
    router_path.write_bytes(router_raw + b"\n# staged drift\n")
    _git(root, "add", runner.ROUTER_PATH)
    router_path.write_bytes(router_raw)
    with pytest.raises(runner.RunnerError, match="HEAD or Git index"):
        runner.authenticate_before_router_execution(root)

    _git(root, "reset", "--hard", "HEAD")
    router_path.write_bytes(b"# wrong committed router\n")
    _git(root, "add", runner.ROUTER_PATH)
    _git(root, "commit", "-q", "-m", "wrong committed router")
    router_path.write_bytes(router_raw)
    _git(root, "add", runner.ROUTER_PATH)
    with pytest.raises(runner.RunnerError, match="HEAD or Git index"):
        runner.authenticate_before_router_execution(root)


def test_fixed_command_rejects_routing_bypass_and_plugin_surfaces(tmp_path: Path) -> None:
    unqualified = router.SealQualification(False, "default_deny")
    qualified = router.SealQualification(True, "seal_qualified", "1" * 40)
    python = str(Path(sys.executable).resolve(strict=True))
    base = (
        python,
        "-I",
        "-m",
        "pytest",
        "-q",
        "-c",
        str(ROOT / router.PYPROJECT_PATH),
        f"--confcutdir={ROOT}",
        str(ROOT / router.TESTS_PATH),
    )
    assert (
        router.authoritative_pytest_argv(
            unqualified,
            python_executable=python,
            root=ROOT,
        )
        == base
    )
    qualified_argv = router.authoritative_pytest_argv(
        qualified,
        python_executable=python,
        root=ROOT,
    )
    assert qualified_argv[len(base) :] == tuple(
        f"--deselect={nodeid}" for nodeid in router.FROZEN_EXACT_HEAD_NODEIDS
    )
    pytest_environment = router.pytest_environment(python_executable=python)
    assert "PYTEST_ADDOPTS" not in pytest_environment
    assert "PYTEST_PLUGINS" not in pytest_environment
    assert "PYTHONPATH" not in pytest_environment

    plugin_root = tmp_path / "plugin-root"
    (plugin_root / "tests").mkdir(parents=True)
    (plugin_root / "conftest.py").write_text("raise RuntimeError\n", encoding="utf-8")
    assert router.no_pytest_plugin_surface(plugin_root) is False
    assert not (ROOT / "conftest.py").exists()

    tracked_plugin_root = tmp_path / "tracked-plugin-root"
    tracked_tests = tracked_plugin_root / "tests"
    tracked_tests.mkdir(parents=True)
    _git(tmp_path, "init", "-q", str(tracked_plugin_root))
    _git(tracked_plugin_root, "config", "user.name", "Tracked Plugin Test")
    _git(tracked_plugin_root, "config", "user.email", "tracked-plugin@example.invalid")
    (tracked_tests / "selection_plugin.py").write_text(
        "def pytest_collection_modifyitems(items):\n    items.clear()\n",
        encoding="utf-8",
    )
    (tracked_tests / "test_selection.py").write_text(
        "pytest_plugins = ('selection_plugin',)\n\ndef test_expected():\n    assert True\n",
        encoding="utf-8",
    )
    _commit_all(tracked_plugin_root, "retain explicit plugin surface")
    assert b"tests/test_selection.py" in _git(tracked_plugin_root, "ls-files")
    assert router.no_pytest_plugin_surface(tracked_plugin_root) is False


@pytest.mark.parametrize(
    ("config_name", "section"),
    (
        ("pytest.ini", "pytest"),
        ("tox.ini", "pytest"),
        ("setup.cfg", "tool:pytest"),
    ),
)
def test_authenticated_config_and_explicit_target_ignore_untracked_pytest_config(
    tmp_path: Path,
    config_name: str,
    section: str,
) -> None:
    fixture = _build_routing_fixture(tmp_path)
    (fixture.root / config_name).write_text(
        f"[{section}]\n"
        "addopts = --deselect=tests/test_expected_collection.py::test_expected_collection\n"
        "python_files = poison_*.py\n"
        "testpaths = poison_tests\n",
        encoding="utf-8",
    )
    poison_tests = fixture.root / "poison_tests"
    poison_tests.mkdir()
    (poison_tests / "poison_extra.py").write_text(
        "def test_poison_discovery():\n    assert False\n",
        encoding="utf-8",
    )
    untracked = set(
        _git(fixture.root, "ls-files", "--others", "--exclude-standard")
        .decode("utf-8")
        .splitlines()
    )
    assert {config_name, "poison_tests/poison_extra.py"} <= untracked

    qualification = _qualify(fixture)
    assert qualification.qualified is True
    assert qualification.source_commit is not None
    python = str(Path(sys.executable).resolve(strict=True))
    expected_pyproject = (fixture.root / router.PYPROJECT_PATH).read_bytes()
    with runner._materialized_repository(
        fixture.root,
        router,
        qualification.source_commit,
        expected_pyproject,
    ) as materialized:
        argv = router.authoritative_pytest_argv(
            qualification,
            python_executable=python,
            root=materialized.root,
        )
        assert argv[5:9] == (
            "-c",
            str(materialized.root / router.PYPROJECT_PATH),
            f"--confcutdir={materialized.root}",
            str(materialized.root / router.TESTS_PATH),
        )
        assert not (materialized.root / config_name).exists()
        assert not (materialized.root / "poison_tests").exists()
        completed = subprocess.run(
            argv,
            cwd=materialized.root,
            env=router.pytest_environment(python_executable=python),
            capture_output=True,
            check=False,
            text=True,
            timeout=120,
        )
        assert completed.returncode == 0, completed.stderr
        assert "1 passed" in completed.stdout
        assert "deselected" not in completed.stdout


def _run_fixture_snapshot(
    fixture: RoutingFixture,
    qualification: router.SealQualification,
) -> subprocess.CompletedProcess[str]:
    assert qualification.source_commit is not None
    python = str(Path(sys.executable).resolve(strict=True))
    with runner._materialized_repository(
        fixture.root,
        router,
        qualification.source_commit,
        (fixture.root / router.PYPROJECT_PATH).read_bytes(),
    ) as materialized:
        private_root = materialized.root.parent
        assert _head(materialized.root) == qualification.source_commit
        assert not materialized.root.is_relative_to(fixture.root)
        assert not any(fixture.root.glob("*iter241-pytest-*"))
        argv = router.authoritative_pytest_argv(
            qualification,
            python_executable=python,
            root=materialized.root,
        )
        completed = subprocess.run(
            argv,
            cwd=materialized.root,
            env=router.pytest_environment(python_executable=python),
            capture_output=True,
            check=False,
            text=True,
            timeout=120,
        )
    assert not private_root.exists()
    return completed


def test_untracked_explicit_pytest_plugin_cannot_rewrite_snapshot_selection(
    tmp_path: Path,
) -> None:
    fixture = _build_routing_fixture(tmp_path)
    (fixture.root / "tests/attack_plugin.py").write_text(
        "def pytest_collection_modifyitems(items):\n"
        "    items[:] = [item for item in items if item.name == 'test_attacker_only']\n",
        encoding="utf-8",
    )
    (fixture.root / "tests/test_attack.py").write_text(
        "pytest_plugins = ('attack_plugin',)\n\ndef test_attacker_only():\n    assert True\n",
        encoding="utf-8",
    )
    qualification = _qualify(fixture)
    assert qualification.qualified is True
    assert {
        "tests/attack_plugin.py",
        "tests/test_attack.py",
    } <= set(
        _git(fixture.root, "ls-files", "--others", "--exclude-standard")
        .decode("utf-8")
        .splitlines()
    )

    completed = _run_fixture_snapshot(fixture, qualification)
    assert completed.returncode == 0, completed.stderr
    assert "1 passed" in completed.stdout
    assert "attacker" not in completed.stdout


def test_source_test_mutation_after_materialization_cannot_change_selection(
    tmp_path: Path,
) -> None:
    fixture = _build_routing_fixture(tmp_path)
    qualification = _qualify(fixture)
    assert qualification.qualified is True
    assert qualification.source_commit is not None
    python = str(Path(sys.executable).resolve(strict=True))
    with runner._materialized_repository(
        fixture.root,
        router,
        qualification.source_commit,
        (fixture.root / router.PYPROJECT_PATH).read_bytes(),
    ) as materialized:
        (fixture.root / "tests/test_expected_collection.py").write_text(
            "pytest_plugins = ('post_plan_plugin',)\n",
            encoding="utf-8",
        )
        (fixture.root / "tests/post_plan_plugin.py").write_text(
            "def pytest_collection_modifyitems(items):\n    items.clear()\n",
            encoding="utf-8",
        )
        runner._verify_snapshot(
            materialized,
            router,
            (fixture.root / router.PYPROJECT_PATH).read_bytes(),
        )
        argv = router.authoritative_pytest_argv(
            qualification,
            python_executable=python,
            root=materialized.root,
        )
        completed = subprocess.run(
            argv,
            cwd=materialized.root,
            env=router.pytest_environment(python_executable=python),
            capture_output=True,
            check=False,
            text=True,
            timeout=120,
        )
    assert completed.returncode == 0, completed.stderr
    assert "1 passed" in completed.stdout


def test_git_filters_and_attributes_never_execute_during_direct_materialization(
    tmp_path: Path,
) -> None:
    fixture = _build_routing_fixture(tmp_path)
    marker = tmp_path / "materializer-command-executed"
    command = tmp_path / "poison-materializer.sh"
    command.write_text(
        f"#!/bin/sh\ntouch {marker}\ncat\n",
        encoding="utf-8",
    )
    command.chmod(0o755)
    _git(fixture.root, "config", "core.fsmonitor", str(command))
    _git(fixture.root, "config", "filter.evil.smudge", str(command))
    _git(fixture.root, "config", "uploadpack.packObjectsHook", str(command))
    (fixture.root / ".gitattributes").write_text(
        "*.py filter=evil eol=crlf working-tree-encoding=UTF-16\n",
        encoding="utf-8",
    )
    _git(fixture.root, "add", "--", ".gitattributes")
    _git(fixture.root, "commit", "-q", "-m", "add hostile checkout attributes")
    marker.unlink(missing_ok=True)
    qualification = _qualify(fixture)
    assert qualification.qualified is True
    assert qualification.source_commit is not None
    committed_test = _git(
        fixture.root,
        "show",
        f"{qualification.source_commit}:tests/test_expected_collection.py",
    )

    with runner._materialized_repository(
        fixture.root,
        router,
        qualification.source_commit,
        (fixture.root / router.PYPROJECT_PATH).read_bytes(),
    ) as materialized:
        assert (
            materialized.root / "tests/test_expected_collection.py"
        ).read_bytes() == committed_test
        assert not marker.exists()
    assert not marker.exists()


def test_snapshot_byte_mode_and_extra_directory_mutations_fail_reverification(
    tmp_path: Path,
) -> None:
    fixture = _build_routing_fixture(tmp_path)
    qualification = _qualify(fixture)
    assert qualification.qualified is True
    assert qualification.source_commit is not None
    expected_pyproject = (fixture.root / router.PYPROJECT_PATH).read_bytes()
    with runner._materialized_repository(
        fixture.root,
        router,
        qualification.source_commit,
        expected_pyproject,
    ) as materialized:
        target = materialized.root / "tests/test_expected_collection.py"
        original = target.read_bytes()
        replacement = bytes([original[0] ^ 1]) + original[1:]
        assert len(replacement) == len(original) and replacement != original
        target.write_bytes(replacement)
        with pytest.raises(runner.RunnerError, match="bytes differ"):
            runner._verify_snapshot(materialized, router, expected_pyproject)
        target.write_bytes(original)
        target.chmod(0o755)
        with pytest.raises(runner.RunnerError, match="mode differs"):
            runner._verify_snapshot(materialized, router, expected_pyproject)
        target.chmod(0o644)
        extra = materialized.root / "tests/empty-extra-directory"
        extra.mkdir()
        with pytest.raises(runner.RunnerError, match="path set differs"):
            runner._verify_snapshot(materialized, router, expected_pyproject)
        extra.rmdir()
        runner._verify_snapshot(materialized, router, expected_pyproject)


def test_private_snapshot_retains_head_history_and_supports_child_clone(tmp_path: Path) -> None:
    fixture = _build_routing_fixture(tmp_path)
    qualification = _qualify(fixture)
    assert qualification.qualified is True
    assert qualification.source_commit is not None
    with runner._materialized_repository(
        fixture.root,
        router,
        qualification.source_commit,
        (fixture.root / router.PYPROJECT_PATH).read_bytes(),
    ) as materialized:
        parent = _git(materialized.root, "rev-parse", "HEAD^").decode("ascii").strip()
        assert _git(materialized.root, "show", "-s", "--format=%H", parent) == (
            f"{parent}\n".encode("ascii")
        )
        child = tmp_path / "snapshot-child"
        _git(
            tmp_path,
            "clone",
            "-q",
            "--no-hardlinks",
            str(materialized.root),
            str(child),
        )
        assert _head(child) == qualification.source_commit


def test_source_head_drift_during_clone_denies_materialization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _build_routing_fixture(tmp_path)
    qualification = _qualify(fixture)
    assert qualification.qualified is True
    assert qualification.source_commit is not None
    original_run_git = runner._run_git
    mutated = False

    def mutate_after_clone(
        arguments: tuple[str, ...],
        *,
        cwd: Path,
        reason: str,
        timeout: int = 180,
    ) -> bytes:
        nonlocal mutated
        result = original_run_git(arguments, cwd=cwd, reason=reason, timeout=timeout)
        if "clone" in arguments and not mutated:
            mutated = True
            (fixture.root / "post-clone-head-drift.txt").write_text(
                "drift\n",
                encoding="utf-8",
            )
            _commit_all(fixture.root, "mutate source after private clone")
        return result

    monkeypatch.setattr(runner, "_run_git", mutate_after_clone)
    with pytest.raises(router.RoutingDenied, match="source_.*drift"):
        with runner._materialized_repository(
            fixture.root,
            router,
            qualification.source_commit,
            (fixture.root / router.PYPROJECT_PATH).read_bytes(),
        ):
            pass
    assert mutated is True
    assert not any(fixture.root.glob("*iter241-pytest-*"))


def test_runner_requires_isolated_python_and_rejects_extra_arguments(tmp_path: Path) -> None:
    without_isolation = subprocess.run(
        [sys.executable, str(ROOT / "scripts/run_iter241_pytest.py"), "--plan"],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )
    assert without_isolation.returncode == 2
    assert "requires an isolated Python invocation" in without_isolation.stderr
    bypass = subprocess.run(
        [
            sys.executable,
            "-I",
            str(ROOT / "scripts/run_iter241_pytest.py"),
            "--plan",
            "--deselect=tests/test_iter241_pytest_router.py",
        ],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )
    assert bypass.returncode == 2
    assert "unrecognized arguments" in bypass.stderr

    wrong_cwd = subprocess.run(
        [
            sys.executable,
            "-I",
            str(ROOT / "scripts/run_iter241_pytest.py"),
            "--plan",
        ],
        cwd=tmp_path,
        capture_output=True,
        check=False,
        text=True,
    )
    assert wrong_cwd.returncode == 2
    assert "repository root as its working directory" in wrong_cwd.stderr


def _copy_candidate_files(source: Path, target: Path) -> None:
    for relative in (
        "docs/EXPERIMENT_INDEX.md",
        "experiments/iter241_iter240_repository_closure/POSTCOMMIT_VERIFICATION_DESIGN.md",
        "scripts/route_iter241_pytest.py",
        "scripts/run_iter241_pytest.py",
        "tests/test_iter241_pytest_router.py",
    ):
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, destination)


def _append_real_successor_seal(root: Path, reference: str) -> str:
    registry_path = root / router.REGISTRY_PATH
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    count, manifest, _blobs = build_manifest(
        root,
        reference,
        {"kind": "tree", "path": router.ITER241_PATH},
        label="real-validator iter241",
    )
    registry["records"].append(
        {
            "seal_id": router.DEFAULT_CONTRACT.successor_seal_id,
            "record_type": "successor_path_snapshot",
            "predecessor_seal_id": router.DEFAULT_CONTRACT.authorization_seal_id,
            "reference_commit": reference,
            "protected_sets": [
                {
                    "set_id": router.DEFAULT_CONTRACT.successor_set_id,
                    "selector": {"kind": "tree", "path": router.ITER241_PATH},
                    "policy": "exact_tree",
                    "blob_count": count,
                    "manifest_sha256": manifest,
                }
            ],
            "limitations": list(router.DEFAULT_CONTRACT.successor_limitations),
        }
    )
    _write_json(registry_path, registry)
    return _commit_all(root, "register exact iter241 successor seal")


def test_real_validators_and_authenticated_runner_accept_exact_successor(
    tmp_path: Path,
) -> None:
    clone = (tmp_path / "real-validator-clone").resolve()
    _git(
        ROOT.parent,
        "clone",
        "-q",
        "--local",
        "--no-hardlinks",
        str(ROOT),
        str(clone),
    )
    _git(clone, "config", "user.name", "Real Validator Test")
    _git(clone, "config", "user.email", "real-validator@example.invalid")
    _copy_candidate_files(ROOT, clone)
    registry = json.loads((clone / router.REGISTRY_PATH).read_text(encoding="utf-8"))
    existing_successors = [
        record
        for record in registry["records"]
        if record.get("seal_id") == router.DEFAULT_CONTRACT.successor_seal_id
    ]
    if existing_successors:
        assert _git(clone, "status", "--porcelain") == b""
        reference = existing_successors[0]["reference_commit"]
    else:
        reference = (
            _commit_all(clone, "retain authenticated pytest router")
            if _git(clone, "status", "--porcelain")
            else _head(clone)
        )
        _append_real_successor_seal(clone, reference)

    environment = os.environ.copy()
    environment.update(
        {
            "GIT_DIR": str(tmp_path / "poison-git-dir"),
            "GIT_OBJECT_DIRECTORY": str(tmp_path / "poison-objects"),
            "PYTEST_ADDOPTS": "--deselect=tests/test_iter241_pytest_router.py",
            "PYTEST_PLUGINS": "poison_plugin",
            "PYTHONPATH": str(tmp_path / "poison-python"),
        }
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-I",
            str(clone / "scripts/run_iter241_pytest.py"),
            "--plan",
        ],
        cwd=clone,
        env=environment,
        capture_output=True,
        check=False,
        text=True,
        timeout=240,
    )
    assert completed.returncode == 0, completed.stderr
    plan = json.loads(completed.stdout)
    assert plan["qualified"] is True, plan
    assert plan["reason"] == "seal_qualified"
    assert plan["reference_commit"] == reference
    assert plan["source_commit"] == _head(clone)
    assert plan["source_tree"] == _tree(clone, plan["source_commit"])
    assert plan["schema_version"] == "telos.iter241.authenticated_pytest_plan.v2"
    assert plan["ephemeral_snapshot"] is True
    assert plan["executable_after_runner_exit"] is False
    snapshot = Path(plan["cwd"])
    assert snapshot.name == "repository"
    assert snapshot.parent.name.startswith("telos-iter241-pytest-")
    assert snapshot.parent.parent == router.TRUSTED_TEMP_ROOT
    assert not snapshot.is_relative_to(clone)
    assert plan["argv"][5:9] == [
        "-c",
        str(snapshot / router.PYPROJECT_PATH),
        f"--confcutdir={snapshot}",
        str(snapshot / router.TESTS_PATH),
    ]
    assert plan["argv"][-2:] == [
        f"--deselect={nodeid}" for nodeid in router.FROZEN_EXACT_HEAD_NODEIDS
    ]
    assert not snapshot.exists()


def test_frozen_lint_exception_and_guard_digests_remain_exact() -> None:
    configuration = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert configuration["tool"]["ruff"]["lint"]["per-file-ignores"] == {
        router.FROZEN_VALIDATOR_PATH: ["F401"]
    }
    expected = {
        router.CORRECTION_ADJUDICATOR_PATH: (router.DEFAULT_CONTRACT.correction_adjudicator_sha256),
        router.SEAL_VALIDATOR_PATH: router.DEFAULT_CONTRACT.seal_registry_validator_sha256,
        router.RECEIPT_SEALING_PATH: router.DEFAULT_CONTRACT.receipt_sealing_sha256,
        router.FROZEN_VALIDATOR_PATH: router.DEFAULT_CONTRACT.frozen_validator_sha256,
        router.FROZEN_TEST_PATH: router.DEFAULT_CONTRACT.frozen_test_sha256,
        router.PYPROJECT_PATH: router.DEFAULT_CONTRACT.pyproject_sha256,
    }
    for relative, digest in expected.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest


def test_runner_hash_exactly_authenticates_formatted_router() -> None:
    router_raw = (ROOT / runner.ROUTER_PATH).read_bytes()
    assert hashlib.sha256(router_raw).hexdigest() == runner.ROUTER_SHA256
    assert not stat.S_IMODE((ROOT / runner.ROUTER_PATH).stat().st_mode) & 0o022
