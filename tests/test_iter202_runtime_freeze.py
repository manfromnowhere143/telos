from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess

import pytest

from scripts import validate_iter202_runtime_freeze as freeze


@pytest.fixture(scope="module")
def expected_manifest() -> dict:
    return freeze.build_manifest()


def test_committed_runtime_manifest_reproduces() -> None:
    assert freeze.validate_committed_manifest() == []


def test_runtime_manifest_is_deterministic_and_canonical(expected_manifest: dict) -> None:
    second = freeze.build_manifest()
    assert second == expected_manifest
    assert freeze.MANIFEST.read_bytes() == freeze.rendered_manifest_bytes(second)
    assert [row["path"] for row in second["files"]] == sorted(
        row["path"] for row in second["files"]
    )
    assert second["file_count"] == len(freeze.FROZEN_FILES) == len(second["files"])


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        ("missing", "missing frozen files"),
        ("extra", "extra frozen files"),
        ("hash", "frozen file metadata/hash mismatch"),
        ("protocol", "frozen protocol object mismatch"),
    ],
)
def test_runtime_manifest_rejects_inventory_and_protocol_drift(
    expected_manifest: dict,
    mutation: str,
    expected_error: str,
) -> None:
    actual = deepcopy(expected_manifest)
    if mutation == "missing":
        actual["files"].pop()
        actual["file_count"] -= 1
    elif mutation == "extra":
        actual["files"].append(
            {
                "bytes": 0,
                "path": "scripts/unregistered_runtime.py",
                "role": "undeclared",
                "sha256": "0" * 64,
            }
        )
        actual["file_count"] += 1
    elif mutation == "hash":
        actual["files"][0]["sha256"] = "0" * 64
    elif mutation == "protocol":
        actual["protocol"]["solver"]["model"] = "unfrozen-model"
    else:  # pragma: no cover - parameter list is exhaustive
        raise AssertionError(mutation)

    errors = freeze.manifest_errors(actual, expected_manifest)
    assert any(expected_error in error for error in errors)


def test_runtime_manifest_strict_json_rejects_duplicate_keys(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"schema_version":"one","schema_version":"two"}\n')
    with pytest.raises(freeze.RuntimeFreezeError, match="duplicate JSON key"):
        freeze.load_json_strict(duplicate)


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_runtime_manifest_strict_json_rejects_nonfinite_constants(
    tmp_path: Path, constant: str
) -> None:
    invalid = tmp_path / "nonfinite.json"
    invalid.write_text('{"value":' + constant + "}\n")
    with pytest.raises(freeze.RuntimeFreezeError, match="non-finite JSON constant"):
        freeze.load_json_strict(invalid)


def test_runtime_manifest_renderers_reject_nonfinite_values() -> None:
    with pytest.raises(ValueError, match="Out of range float values"):
        freeze.canonical_json_bytes({"value": float("nan")})
    with pytest.raises(ValueError, match="Out of range float values"):
        freeze.rendered_manifest_bytes({"value": float("inf")})


def test_local_dependency_discovery_covers_static_and_dynamic_imports(
    tmp_path: Path,
) -> None:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "telos").mkdir()
    (tmp_path / "scripts/dynamic.py").write_text("VALUE = 1\n")
    (tmp_path / "telos/helper.py").write_text("VALUE = 2\n")
    entry = tmp_path / "scripts/entry.py"
    entry.write_text(
        "from pathlib import Path\n"
        "from scripts import dynamic\n"
        "from telos.helper import VALUE\n"
        "ROOT = Path(__file__).resolve().parents[1]\n"
        'DYNAMIC = ROOT / "scripts" / "dynamic.py"\n'
        'LOADED = load_runtime("scripts/dynamic.py")\n'
    )
    assert freeze.local_python_dependencies(entry, tmp_path) == {
        "scripts/dynamic.py",
        "telos/helper.py",
    }


def test_runtime_dependency_discovery_covers_package_and_dynamic_loader_edges() -> None:
    assert freeze.local_python_dependencies(
        freeze.ROOT / "scripts/extract_iter200_specs.py"
    ) == {
        "scripts/run_iter200_scenarios.py",
        "scripts/validate_iter202_runtime_freeze.py",
    }
    assert freeze.local_python_dependencies(
        freeze.ROOT / "scripts/run_iter200_blind_judge.py"
    ) == {
        "scripts/adjudicate_iter200.py",
        "scripts/run_iter200_scenarios.py",
        "scripts/run_iter200_solver.py",
        "scripts/validate_iter202_runtime_freeze.py",
        "telos/secure_checkpoint_fs.py",
    }


def test_failed_only_rerun_guard_is_scoped_to_each_bash_fence() -> None:
    safe = (
        "```bash\npython3 -m pip check\n```\n\n"
        'If execution fails, use `gh run rerun "$RUN_ID"`; never use `--failed`.\n'
    )
    unsafe = '```bash\ngh run rerun "$RUN_ID" --failed\n```\n'
    unsafe_continued = '```bash\ngh run rerun "$RUN_ID" \\\n+  --failed\n```\n'

    assert freeze._has_forbidden_failed_only_rerun(safe) is False
    assert freeze._has_forbidden_failed_only_rerun(unsafe) is True
    assert freeze._has_forbidden_failed_only_rerun(unsafe_continued) is True


def _run_git(root: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _committed_provenance_fixture(root: Path) -> list[str]:
    _run_git(root, "init", "-q")
    _run_git(root, "config", "user.email", "runtime-freeze@example.invalid")
    _run_git(root, "config", "user.name", "Runtime Freeze Test")
    (root / "frozen.txt").write_text("frozen\n")
    (root / "manifest.json").write_text("{}\n")
    _run_git(root, "add", "--", "frozen.txt", "manifest.json")
    _run_git(root, "commit", "-qm", "freeze")
    return ["frozen.txt", "manifest.json"]


def test_provider_preflight_returns_committed_manifest_sha_without_semantic_recursion(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    frozen_path = tmp_path / "frozen.txt"
    manifest_path = tmp_path / "manifest.json"
    frozen_path.write_text("frozen\n")
    monkeypatch.setattr(freeze, "FROZEN_FILES", (("frozen.txt", "test_input"),))
    expected = freeze._assemble_manifest(freeze._file_records(tmp_path))
    manifest_path.write_bytes(freeze.rendered_manifest_bytes(expected))
    _run_git(tmp_path, "init", "-q")
    _run_git(tmp_path, "config", "user.email", "runtime-freeze@example.invalid")
    _run_git(tmp_path, "config", "user.name", "Runtime Freeze Test")
    _run_git(tmp_path, "add", "--", "frozen.txt", "manifest.json")
    _run_git(tmp_path, "commit", "-qm", "freeze")
    monkeypatch.setattr(
        freeze,
        "validate_runtime_semantics",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("provider preflight invoked aggregate semantics")
        ),
    )

    assert freeze.require_valid_runtime_freeze(tmp_path, manifest_path) == freeze.sha256(
        manifest_path.read_bytes()
    )


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        ("untracked", "Git provenance check failed"),
        ("staged", "staged/index drift"),
        ("staged_then_restored", "staged/index drift"),
        ("working_tree", "working-tree drift"),
    ],
)
def test_git_provenance_rejects_untracked_staged_and_worktree_drift(
    tmp_path: Path, mutation: str, expected_error: str
) -> None:
    paths = _committed_provenance_fixture(tmp_path)
    freeze._require_head_index_worktree_match(tmp_path, paths)
    if mutation == "untracked":
        (tmp_path / "untracked.json").write_text("{}\n")
        paths = ["frozen.txt", "manifest.json", "untracked.json"]
    elif mutation == "staged":
        (tmp_path / "frozen.txt").write_text("staged\n")
        _run_git(tmp_path, "add", "--", "frozen.txt")
    elif mutation == "staged_then_restored":
        (tmp_path / "frozen.txt").write_text("staged\n")
        _run_git(tmp_path, "add", "--", "frozen.txt")
        (tmp_path / "frozen.txt").write_text("frozen\n")
    elif mutation == "working_tree":
        (tmp_path / "frozen.txt").write_text("working tree\n")
    else:  # pragma: no cover - parameter list is exhaustive
        raise AssertionError(mutation)

    with pytest.raises(freeze.RuntimeFreezeError, match=expected_error):
        freeze._require_head_index_worktree_match(tmp_path, paths)


def test_derived_outputs_may_match_any_complete_checkpoint_prefix(
    tmp_path: Path,
) -> None:
    stage = tmp_path / "stage"
    stage.mkdir()
    artifact = stage / "demo.model.patch"
    prefix_zero = ({"provider_calls": 0}, {})
    prefix_one = ({"provider_calls": 1}, {artifact: b"patch\n"})

    (stage / "summary.json").write_text(
        json.dumps(prefix_zero[0], indent=2, sort_keys=True) + "\n"
    )
    assert (
        freeze._match_checkpoint_prefix_state(
            stage=stage,
            summary_name="summary.json",
            states=[prefix_zero, prefix_one],
            artifact_suffixes=(".model.patch",),
            label="test",
        )
        == prefix_zero[0]
    )

    (stage / "summary.json").write_text(
        json.dumps(prefix_one[0], indent=2, sort_keys=True) + "\n"
    )
    artifact.write_bytes(b"patch\n")
    assert (
        freeze._match_checkpoint_prefix_state(
            stage=stage,
            summary_name="summary.json",
            states=[prefix_zero, prefix_one],
            artifact_suffixes=(".model.patch",),
            label="test",
        )
        == prefix_one[0]
    )


def test_derived_output_mixture_outside_one_prefix_fails_closed(
    tmp_path: Path,
) -> None:
    stage = tmp_path / "stage"
    stage.mkdir()
    artifact = stage / "demo.model.patch"
    states = [
        ({"provider_calls": 0}, {}),
        ({"provider_calls": 1}, {artifact: b"expected\n"}),
    ]
    (stage / "summary.json").write_text(
        json.dumps(states[1][0], indent=2, sort_keys=True) + "\n"
    )
    artifact.write_bytes(b"tampered\n")
    with pytest.raises(freeze.RuntimeFreezeError, match="complete checkpoint prefix"):
        freeze._match_checkpoint_prefix_state(
            stage=stage,
            summary_name="summary.json",
            states=states,
            artifact_suffixes=(".model.patch",),
            label="test",
        )


def test_artifact_without_prefix_summary_fails_closed(tmp_path: Path) -> None:
    stage = tmp_path / "stage"
    stage.mkdir()
    (stage / "demo.model.patch").write_bytes(b"patch\n")
    with pytest.raises(freeze.RuntimeFreezeError, match="without a derived summary"):
        freeze._match_checkpoint_prefix_state(
            stage=stage,
            summary_name="summary.json",
            states=[({"provider_calls": 0}, {})],
            artifact_suffixes=(".model.patch",),
            label="test",
        )


def test_protocol_digest_binds_exact_provider_configuration(
    expected_manifest: dict,
) -> None:
    protocol = expected_manifest["protocol"]
    assert protocol["solver"]["model"] == "gpt-5.6-terra"
    assert protocol["scenario_generation"]["call_ceiling"] == 50
    assert protocol["judges"]["call_ceiling"] == 100
    assert protocol["judges"]["checkpoint_lifecycle"] == [
        "started",
        "finished_raw_or_error",
        "parsed",
    ]
    assert protocol["judges"]["parsed_schema"] == (
        "telos.iter202.judge_provider_attempt.parsed.v1"
    )
    assert protocol["judges"]["parser_contract"] == freeze.JUDGE_PARSER_CONTRACT
    assert protocol["judges"]["decision_contract"] == freeze.JUDGE_DECISION_CONTRACT
    assert protocol["judges"]["resume_policy"] == (
        "parse_retained_raw_offline_before_loading_credentials"
    )
    assert protocol["certification"]["execution_limits"] == {
        "certification_output_bytes": 2_097_152,
        "certification_timeout_seconds": 900,
        "kill_grace_seconds": 10,
        "scenario_output_bytes": 262_144,
        "scenario_timeout_seconds": 180,
        "timeout_or_truncation": "infrastructure_failure",
    }
    assert protocol["certification"]["execution_chain_of_custody"] == {
        "adjudication_requires_valid_aggregate_receipt": True,
        "adjudication_uses_verified_in_memory_log_snapshot": True,
        "aggregate_receipt_name": (
            "_telos_iter202_execution_complete.receipt.json"
        ),
        "aggregate_receipt_schema": "telos.iter202.execution_aggregate_receipt.v1",
        "collector_eligible_artifacts": (
            "successful_shards_from_one_github_run_and_attempt_only"
        ),
        "debug_or_partial_artifacts": "excluded_from_scientific_collection",
        "github_provenance_fields": [
            "repository",
            "run_attempt",
            "run_id",
            "sha",
            "workflow_ref",
        ],
        "log_set": "exact_gold_and_variant_pair_for_every_certification_spec",
        "offline_ingest": (
            "validate_then_fsync_stage_and_atomically_install_without_"
            "divergent_overwrite"
        ),
        "offline_ingest_requires_explicit_identity": [
            "expected_run_id",
            "expected_run_attempt",
            "expected_github_sha",
        ],
        "shard_receipt_schema": "telos.iter202.execution_shard_receipt.v1",
        "source_hash_bindings": [
            "runtime_manifest",
            "scenarios_summary",
            "solve_summary",
            "solve_targets",
            "spec_index",
        ],
        "union_rule": "eight_disjoint_shards_exactly_cover_spec_index",
        "zero_valid_solution_result": (
            "eight_receipt_only_shards_and_complete_empty_log_aggregate"
        ),
    }
    assert protocol["certification"]["execution_sharding"] == {
        "all_shards_required": True,
        "artifact_name_template": (
            "iter202-execution-run-{run_id}-attempt-{run_attempt}-shard-{index}-of-8"
        ),
        "assignment": "zero_based_ordered_certification_spec_ordinal_modulo_8",
        "bounded_process_wall_ceiling_minutes_per_shard": 150.5,
        "bounded_process_wall_ceiling_seconds_per_shard": 9_030,
        "fail_fast": False,
        "filtering_order": "validate_complete_spec_index_and_inputs_before_partition",
        "indexes": list(range(8)),
        "max_rows_per_shard": 7,
        "nominal_timeout_threshold_minutes_per_shard": 147,
        "partial_rerun_policy": "fail_collection_and_rerun_all_eight_shards",
        "possible_kill_grace_minutes_per_shard": 3.5,
        "same_workflow_run_and_attempt_required": True,
        "shard_count": 8,
        "workflow_timeout_minutes": 350,
    }
    assert protocol["judges"]["providers"] == [
        {
            "api_version": None,
            "endpoint": "https://api.openai.com/v1/chat/completions",
            "model": "gpt-5.6-terra",
            "provider": "openai",
            "temperature_omitted": True,
            "token_limit_field": "max_completion_tokens",
            "token_limit_value": 1536,
        },
        {
            "api_version": "2023-06-01",
            "endpoint": "https://api.anthropic.com/v1/messages",
            "model": "claude-opus-4-8",
            "provider": "anthropic",
            "temperature_omitted": True,
            "token_limit_field": "max_tokens",
            "token_limit_value": 400,
        },
    ]
    assert expected_manifest["protocol_sha256"] == freeze.sha256(
        freeze.canonical_json_bytes(protocol)
    )
    # Ensure the manifest stays plain JSON data rather than a Python-only encoding.
    assert json.loads(freeze.rendered_manifest_bytes(expected_manifest)) == expected_manifest
