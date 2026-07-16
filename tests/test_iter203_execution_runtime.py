from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from scripts import build_iter203_runtime_manifest as runtime
from scripts import collect_iter203_execution as collection


RUN_ID = "424242"
RUN_ATTEMPT = "3"
GITHUB_SHA = "a" * 40
GITHUB_REPOSITORY = "manfromnowhere143/telos"
GITHUB_WORKFLOW_REF = (
    "manfromnowhere143/telos/.github/workflows/iter203-execute.yml@refs/heads/master"
)


def primary_ci_authorization(sha: str = GITHUB_SHA) -> dict:
    run_id = 123456
    return {
        "approved_commit_sha": sha,
        "primary_ci_event": "push",
        "primary_ci_head_branch": "master",
        "primary_ci_run_attempt": 1,
        "primary_ci_run_id": run_id,
        "primary_ci_workflow_path": ".github/workflows/ci.yml",
        "required_checks": [
            {
                "app_slug": "github-actions",
                "conclusion": "success",
                "details_url": (
                    f"https://github.com/{GITHUB_REPOSITORY}/actions/runs/{run_id}/job/{check_id}"
                ),
                "id": check_id,
                "name": name,
                "status": "completed",
            }
            for check_id, name in (
                (987650, "verify py3.11"),
                (987651, "verify py3.12"),
            )
        ],
        "schema_version": collection.PRIMARY_CI_AUTHORIZATION_SCHEMA,
    }


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(collection.canonical_json_bytes(value))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def github_environment(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    values = {
        "GITHUB_RUN_ID": RUN_ID,
        "GITHUB_RUN_ATTEMPT": RUN_ATTEMPT,
        "GITHUB_SHA": GITHUB_SHA,
        "GITHUB_REPOSITORY": GITHUB_REPOSITORY,
        "GITHUB_WORKFLOW_REF": GITHUB_WORKFLOW_REF,
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv(
        collection.PRIMARY_CI_AUTHORIZATION_ENV,
        collection._authorization_transport(primary_ci_authorization()),
    )
    return {
        "repository": GITHUB_REPOSITORY,
        "run_attempt": RUN_ATTEMPT,
        "run_id": RUN_ID,
        "sha": GITHUB_SHA,
        "workflow_ref": GITHUB_WORKFLOW_REF,
    }


def make_sources(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, list[str]]:
    experiment = tmp_path / "iter203"
    upstream = tmp_path / "iter202"
    bridge = experiment / "proof/raw/safety_recovery_bridge"
    raw = experiment / "proof/raw"
    ids = [f"repo__project-{index:02d}" for index in range(50)]
    target_ids = ids + [f"repo__empty-{index}" for index in range(3)]
    monkeypatch.setattr(collection, "EXP", experiment)
    monkeypatch.setattr(collection, "UPSTREAM", upstream)
    monkeypatch.setattr(collection, "BRIDGE", bridge)
    monkeypatch.setattr(collection, "ROOT", tmp_path)

    spec_index = raw / "specs/index.json"
    write_json(
        spec_index,
        {
            "count": 50,
            "schema_version": collection.SPEC_INDEX_SCHEMA,
            "specs": [
                {
                    "eval_script_sha256": "1" * 64,
                    "framework": "pytest",
                    "identical_to_gold": False,
                    "instance_id": instance_id,
                    "repo": "repo/project",
                    "scenario_available": ordinal < 29,
                }
                for ordinal, instance_id in enumerate(ids)
            ],
        },
    )
    write_json(
        raw / "solutions/solve_summary.json",
        {
            "manifest": [
                (
                    {"instance_id": instance_id, "status": "solution"}
                    if ordinal < 50
                    else {"instance_id": instance_id, "status": "empty_fix"}
                )
                for ordinal, instance_id in enumerate(target_ids)
            ],
            "schema_version": "telos.iter200.solve_summary.v1",
            "solutions": 50,
            "targets": 53,
        },
    )
    write_json(
        raw / "scenarios/scenarios_summary.json",
        {"schema_version": "telos.iter203.scenarios_summary.v1"},
    )
    write_json(
        bridge / "safe_scenario_index.json",
        {
            "count": 29,
            "scenarios": [{"instance_id": instance_id} for instance_id in ids[:29]],
            "schema_version": "telos.iter203.safe_scenario_index.v1",
        },
    )
    for name in (
        "scenario_disposition.json",
        "solution_projection_index.json",
        "upstream_inventory.json",
    ):
        write_json(bridge / name, {"schema_version": f"fixture.{name}"})
    write_json(
        upstream / "proof/raw/image_lock.json",
        {
            "count": 53,
            "images": [
                {
                    "image_id": "sha256:" + "2" * 64,
                    "instance_id": instance_id,
                    "manifest_digest": "sha256:" + "3" * 64,
                    "reference": f"repo/image@sha256:{'3' * 64}",
                    "tag": "repo/image:latest",
                }
                for instance_id in target_ids
            ],
            "schema_version": "telos.iter202.image_lock.v1",
        },
    )
    write_json(upstream / "proof/raw/solutions/solve_summary.json", {"fixture": "upstream"})
    upstream_runtime = upstream / "proof/raw/runtime_manifest.json"
    write_json(upstream_runtime, {"fixture": "v1"})
    upstream_runtime_sha = digest(upstream_runtime)
    monkeypatch.setattr(collection, "UPSTREAM_RUNTIME_SHA256", upstream_runtime_sha)

    paths = {
        "image_lock_sha256": upstream / "proof/raw/image_lock.json",
        "projected_scenarios_summary_sha256": raw / "scenarios/scenarios_summary.json",
        "projected_solve_summary_sha256": raw / "solutions/solve_summary.json",
        "safe_scenario_index_sha256": bridge / "safe_scenario_index.json",
        "scenario_disposition_sha256": bridge / "scenario_disposition.json",
        "solution_projection_index_sha256": bridge / "solution_projection_index.json",
        "upstream_inventory_sha256": bridge / "upstream_inventory.json",
        "upstream_runtime_manifest_sha256": upstream_runtime,
        "upstream_solve_summary_sha256": upstream / "proof/raw/solutions/solve_summary.json",
    }
    bridge_paths = sorted(
        [
            bridge / "safe_scenario_index.json",
            bridge / "scenario_disposition.json",
            bridge / "solution_projection_index.json",
            bridge / "upstream_inventory.json",
            raw / "scenarios/scenarios_summary.json",
            raw / "solutions/solve_summary.json",
        ]
    )
    bridge_records = [
        {
            "bytes": path.stat().st_size,
            "path": path.relative_to(tmp_path).as_posix(),
            "role": "fixture_bridge_input",
            "sha256": digest(path),
        }
        for path in bridge_paths
    ]
    bridge_sha = collection._records_closure(bridge_records)
    source = {key: digest(path) for key, path in paths.items()}
    source["input_bridge_sha256"] = bridge_sha
    source["spec_index_sha256"] = digest(spec_index)
    runtime_manifest = raw / "runtime_manifest.json"
    runtime_paths = sorted(set(bridge_paths + [spec_index, *paths.values()]))
    bridge_by_path = {record["path"]: record for record in bridge_records}
    runtime_records = [
        bridge_by_path.get(path.relative_to(tmp_path).as_posix())
        or {
            "bytes": path.stat().st_size,
            "path": path.relative_to(tmp_path).as_posix(),
            "role": "fixture_runtime_input",
            "sha256": digest(path),
        }
        for path in runtime_paths
    ]
    write_json(
        runtime_manifest,
        {
            "closure": {
                "algorithm": "SHA-256(path NUL role NUL file_sha256 NUL byte_count LF), path-sorted",
                "sha256": collection._records_closure(runtime_records),
            },
            "experiment_id": collection.EXPERIMENT_ID,
            "file_count": len(runtime_records),
            "files": runtime_records,
            "input_bridge": {
                "algorithm": "SHA-256(path NUL role NUL file_sha256 NUL byte_count LF), path-sorted",
                "file_count": len(bridge_records),
                "files": bridge_records,
                "sha256": bridge_sha,
            },
            "schema_version": collection.RUNTIME_MANIFEST_SCHEMA,
            "source_bindings": source,
            "upstream_runtime_manifest_sha256": upstream_runtime_sha,
            "upstream_source_commit": collection.UPSTREAM_SOURCE_COMMIT,
        },
    )
    return spec_index, runtime_manifest, ids


def make_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, github: dict[str, str]
) -> tuple[Path, Path, Path, list[str]]:
    spec_index, runtime_manifest, ids = make_sources(tmp_path, monkeypatch)
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    for index in range(8):
        shard = artifacts / collection.artifact_name(github, index)
        shard.mkdir()
        assigned = [iid for ordinal, iid in enumerate(ids) if ordinal % 8 == index]
        for name in collection._expected_log_names(assigned):
            (shard / name).write_bytes(f"evidence:{index}:{name}\n".encode())
        collection.create_shard_receipt(
            execution_dir=shard,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
            shard_index=index,
            shard_count=8,
        )
    return artifacts, spec_index, runtime_manifest, ids


def test_runner_has_exact_safe_stage_and_container_boundary() -> None:
    text = (collection.ROOT / "scripts/ci_iter203_execute.sh").read_text()
    assert "experiments/iter202_natural_rate_scaled/proof/raw/scenarios" not in text
    assert "$PWD/$SCEN/$stem.scenario.py:/scenario/scenario.py:ro" in text
    assert "$PWD/$SCEN:/" not in text
    assert "$PWD/$SPECS:/specs" not in text
    assert "$PWD/$SOLS:/solutions" not in text
    assert "$PWD/$SPECS/$stem.eval_script.sh:/specs/$stem.eval_script.sh:ro" in text
    assert "$PWD/$SPECS/$stem.spec.json:/specs/$stem.spec.json:ro" in text
    assert ("$PWD/$SOLS/$stem.$patch_name.patch:/solutions/$stem.$patch_name.patch:ro") in text
    assert text.count('-v "$PWD/$SOLS/') == 1
    assert '[ "$mode" = "gold-behavior" ] && patch_name="gold"' in text
    assert '[ "$mode" = "variant-behavior" ] || [ "$mode" = "gold-behavior" ]' in text
    for required in (
        "--network none",
        "--cap-drop ALL",
        "--security-opt no-new-privileges=true",
        "--pids-limit 1024",
        "--memory 10g",
        "--cpus 4",
    ):
        assert required in text
    assert "SCENARIO_NOT_EXECUTED disposition=no_safe_scenario" in text
    assert "unset OPENAI_API_KEY ANTHROPIC_API_KEY" in text
    assert "unset PYTHONHOME PYTHONINSPECT PYTHONPATH PYTHONSTARTUP PYTHONUSERBASE" in text
    assert '"$CONTROLLER_PYTHON" -I -S -c' in text
    assert "| python -c" not in text


def test_workflow_enforces_canonical_green_primary_dispatch_and_full_history() -> None:
    text = (collection.ROOT / ".github/workflows/iter203-execute.yml").read_text()
    assert "expected_primary_sha:" in text
    assert 'test "${GITHUB_REPOSITORY}" = "manfromnowhere143/telos"' in text
    assert 'test "${GITHUB_REF}" = "refs/heads/master"' in text
    assert "actions/workflows/ci.yml/runs" in text
    assert "commits/{expected_sha}/check-runs" in text
    assert 'required_names = ("verify py3.11", "verify py3.12")' in text
    assert "checks: read" in text
    assert "TELOS_ITER203_PRIMARY_CI_AUTHORIZATION" in text
    assert "first iter203 dispatch for the approved primary commit" in text
    assert text.count("fetch-depth: 0") == 3
    assert (
        "git cat-file -e 8b8809ed6b358d16eb08fe38f0f2edf4a284af0e^{commit}" in text
    )
    assert "cancel-in-progress: false" in text


def test_runner_shell_syntax_is_valid() -> None:
    subprocess.run(
        ["bash", "-n", str(collection.ROOT / "scripts/ci_iter203_execute.sh")],
        check=True,
    )


def test_exact_eight_shard_plan_covers_50_once_with_max_seven() -> None:
    partitions = [[ordinal for ordinal in range(50) if ordinal % 8 == index] for index in range(8)]
    assert [len(partition) for partition in partitions] == [7, 7, 6, 6, 6, 6, 6, 6]
    flattened = [ordinal for partition in partitions for ordinal in partition]
    assert sorted(flattened) == list(range(50))
    assert len(flattened) == len(set(flattened))


def test_source_lines_cover_every_patch_independent_of_safety_disposition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec_index, runtime_manifest, ids = make_sources(tmp_path, monkeypatch)
    lines = collection.source_lines(spec_index=spec_index, runtime_manifest=runtime_manifest)
    assert len(lines) == 50
    assert [line.split("\t")[0] for line in lines] == ids
    assert sum(line.endswith("\tsafe_scenario") for line in lines) == 29
    assert sum(line.endswith("\tno_safe_scenario") for line in lines) == 21


def test_github_provenance_requires_exact_canonical_repository_and_master_ref() -> None:
    canonical = {
        "repository": collection.CANONICAL_REPOSITORY,
        "run_attempt": "1",
        "run_id": "42",
        "sha": "a" * 40,
        "workflow_ref": collection.CANONICAL_WORKFLOW_REF,
    }
    assert collection._validate_github(canonical, "fixture") == canonical
    for field, replacement in (
        ("repository", "fork/telos"),
        (
            "workflow_ref",
            f"{collection.CANONICAL_REPOSITORY}/.github/workflows/iter203-execute.yml@refs/heads/feature",
        ),
    ):
        divergent = {**canonical, field: replacement}
        with pytest.raises(collection.ExecutionCollectionError, match="canonical repository/master"):
            collection._validate_github(divergent, "fixture")


def test_primary_ci_authorization_transport_and_parser_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    github = {
        "repository": collection.CANONICAL_REPOSITORY,
        "run_attempt": "1",
        "run_id": "42",
        "sha": GITHUB_SHA,
        "workflow_ref": collection.CANONICAL_WORKFLOW_REF,
    }
    authorization = primary_ci_authorization()
    encoded = collection._authorization_transport(authorization)
    assert collection._decode_authorization_transport(encoded) == authorization
    assert collection._validate_authorization(authorization, github, "fixture") == authorization

    for mutation in (
        {**authorization, "approved_commit_sha": "b" * 40},
        {
            **authorization,
            "required_checks": [
                {**authorization["required_checks"][0], "conclusion": "failure"},
                authorization["required_checks"][1],
            ],
        },
        {
            **authorization,
            "required_checks": list(reversed(authorization["required_checks"])),
        },
    ):
        with pytest.raises(collection.ExecutionCollectionError):
            collection._validate_authorization(mutation, github, "fixture")

    with pytest.raises(collection.ExecutionCollectionError, match="transport is invalid"):
        collection._decode_authorization_transport("not-base64!")
    duplicate_payload = (
        b'{"approved_commit_sha":"' + GITHUB_SHA.encode() + b'","approved_commit_sha":"'
        + GITHUB_SHA.encode()
        + b'"}'
    )
    duplicate_transport = base64.urlsafe_b64encode(duplicate_payload).decode()
    with pytest.raises(collection.ExecutionCollectionError, match="duplicate key"):
        collection._decode_authorization_transport(duplicate_transport)

    monkeypatch.delenv(collection.PRIMARY_CI_AUTHORIZATION_ENV, raising=False)
    with pytest.raises(collection.ExecutionCollectionError, match="authorization is required"):
        collection._authorization_from_environment(github=github, required=True)


def test_exact_eight_shard_collection_and_verified_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    artifacts, spec_index, runtime_manifest, ids = make_artifacts(
        tmp_path, monkeypatch, github_environment
    )
    output = tmp_path / "complete"
    aggregate = output / collection.AGGREGATE_RECEIPT_NAME
    document = collection.collect_shards(
        artifacts_dir=artifacts,
        output_dir=output,
        aggregate_receipt=aggregate,
        spec_index=spec_index,
        runtime_manifest=runtime_manifest,
    )
    checked, snapshot = collection.check_execution_bundle_with_logs(
        execution_dir=output,
        aggregate_receipt=aggregate,
        spec_index=spec_index,
        runtime_manifest=runtime_manifest,
    )
    assert checked == document
    assert checked["assignment"]["ordered_instance_ids"] == ids
    assert checked["authorization"] == primary_ci_authorization()
    assert len(checked["shards"]) == 8
    assert len(checked["logs"]) == len(snapshot) == 100


def test_collector_rejects_partial_or_extra_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    artifacts, spec_index, runtime_manifest, _ = make_artifacts(
        tmp_path, monkeypatch, github_environment
    )
    shutil.rmtree(artifacts / collection.artifact_name(github_environment, 7))
    with pytest.raises(collection.ExecutionCollectionError, match="exact shard indexes"):
        collection.collect_shards(
            artifacts_dir=artifacts,
            output_dir=tmp_path / "partial",
            aggregate_receipt=tmp_path / "partial" / collection.AGGREGATE_RECEIPT_NAME,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
        )
    extra = artifacts / "unexpected-debug-artifact"
    extra.mkdir()
    with pytest.raises(collection.ExecutionCollectionError, match="unexpected artifact"):
        collection.collect_shards(
            artifacts_dir=artifacts,
            output_dir=tmp_path / "extra",
            aggregate_receipt=tmp_path / "extra" / collection.AGGREGATE_RECEIPT_NAME,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
        )


def test_collector_rejects_mixed_attempts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    artifacts, spec_index, runtime_manifest, _ = make_artifacts(
        tmp_path, monkeypatch, github_environment
    )
    original = artifacts / collection.artifact_name(github_environment, 7)
    mixed = dict(github_environment)
    mixed["run_attempt"] = "4"
    original.rename(artifacts / collection.artifact_name(mixed, 7))
    with pytest.raises(collection.ExecutionCollectionError, match="mix GitHub runs or attempts"):
        collection.collect_shards(
            artifacts_dir=artifacts,
            output_dir=tmp_path / "mixed",
            aggregate_receipt=tmp_path / "mixed" / collection.AGGREGATE_RECEIPT_NAME,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
        )


def test_source_drift_invalidates_existing_receipts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    artifacts, spec_index, runtime_manifest, _ = make_artifacts(
        tmp_path, monkeypatch, github_environment
    )
    document = json.loads(spec_index.read_text())
    document["specs"][0]["framework"] = "changed"
    write_json(spec_index, document)
    shard = artifacts / collection.artifact_name(github_environment, 0)
    with pytest.raises(collection.ExecutionCollectionError, match="runtime closure file differs"):
        collection.create_shard_receipt(
            execution_dir=shard,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
            shard_index=0,
            shard_count=8,
        )


def test_runtime_protocol_binds_both_generations_and_all_certification() -> None:
    if not runtime.MANIFEST.is_file():
        pytest.skip("runtime manifest is written only after the locked 50-spec extraction")
    assert runtime.validate_committed_manifest() == []
    document = json.loads(runtime.MANIFEST.read_text())
    assert document["upstream_runtime_manifest_sha256"] == runtime.UPSTREAM_RUNTIME_SHA256
    assert document["source_bindings"]["input_bridge_sha256"] == document["input_bridge"]["sha256"]
    assert document["protocol"]["certification"] == {
        "all_valid_patches_independent_of_scenario_disposition": True,
        "expected_valid_patches": 50,
        "scenario_mount_during_certification": "none",
        "spec_index": "experiments/iter203_iter202_safety_recovery/proof/raw/specs/index.json",
    }
    assert (
        document["protocol"]["safe_witnesses"]["mount"] == "current_indexed_safe_scenario_file_only"
    )
    assert document["protocol"]["sharding"]["max_rows_per_shard"] == 7
    bound_paths = {row["path"] for row in document["files"]}
    assert {
        "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/swebench_verified_rows_snapshot.json",
        "experiments/iter200_natural_certified_yet_wrong_rate/proof/audit_report.json",
        "experiments/iter202_natural_rate_scaled/proof/raw/sample_overlap_audit.json",
        "scripts/adjudicate_iter203_safety_recovery.py",
        "scripts/run_iter203_safety_recovery_blind_judge.py",
        "telos/patch_normalization.py",
        "telos/secure_checkpoint_fs.py",
        "telos/swebench_log_parsers.py",
    }.issubset(bound_paths)
    assert document["protocol"]["dispatch_authorization"] == {
        "branch": "master",
        "canonical_run": "first_dispatch_for_preapproved_green_primary_commit",
        "repository": "manfromnowhere143/telos",
        "retry": "rerun_all_jobs_of_same_run_only",
        "workflow": ".github/workflows/iter203-execute.yml",
    }
    assert document["protocol"]["adjudication_and_judging"]["judge_missingness"] == (
        "unadjudicated_never_negative"
    )
