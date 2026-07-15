from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import pytest

from scripts import collect_iter202_execution as collection


RUN_ID = "424242"
RUN_ATTEMPT = "3"
GITHUB_SHA = "a" * 40
GITHUB_REPOSITORY = "manfromnowhere143/telos"
GITHUB_WORKFLOW_REF = (
    "manfromnowhere143/telos/.github/workflows/iter202-execute.yml@refs/heads/master"
)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(collection.canonical_json_bytes(value))


@pytest.fixture
def github_environment(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    monkeypatch.setenv("GITHUB_RUN_ID", RUN_ID)
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", RUN_ATTEMPT)
    monkeypatch.setenv("GITHUB_SHA", GITHUB_SHA)
    monkeypatch.setenv("GITHUB_REPOSITORY", GITHUB_REPOSITORY)
    monkeypatch.setenv("GITHUB_WORKFLOW_REF", GITHUB_WORKFLOW_REF)
    return {
        "repository": GITHUB_REPOSITORY,
        "run_attempt": RUN_ATTEMPT,
        "run_id": RUN_ID,
        "sha": GITHUB_SHA,
        "workflow_ref": GITHUB_WORKFLOW_REF,
    }


def make_sources(tmp_path: Path, count: int = 13) -> tuple[Path, Path, list[str]]:
    if count not in range(collection.TARGET_COUNT + 1):
        raise ValueError("synthetic valid-solution count exceeds the frozen target cohort")
    raw = tmp_path / "experiment/proof/raw"
    spec_index = raw / "specs/index.json"
    runtime_manifest = raw / "runtime_manifest.json"
    target_ids = [
        f"repo__project-{index}" for index in range(collection.TARGET_COUNT)
    ]
    ids = target_ids[:count]
    write_json(
        spec_index,
        {
            "count": count,
            "schema_version": collection.SPEC_INDEX_SCHEMA,
            "specs": [
                {
                    "identical_to_gold": False,
                    "instance_id": instance_id,
                    "scenario_available": True,
                }
                for instance_id in ids
            ],
        },
    )
    write_json(
        runtime_manifest,
        {
            "experiment_id": collection.EXPERIMENT_ID,
            "schema_version": collection.RUNTIME_MANIFEST_SCHEMA,
        },
    )
    write_json(
        raw / "solve_targets.json",
        {
            "count": collection.TARGET_COUNT,
            "schema_version": collection.TARGET_SCHEMA,
            "targets": [
                {"instance_id": instance_id, "repo": "repo/project"}
                for instance_id in target_ids
            ],
        },
    )
    write_json(
        raw / "solutions/solve_summary.json",
        {
            "manifest": [
                (
                    {
                        "identical_to_gold": False,
                        "instance_id": instance_id,
                        "status": "solution",
                    }
                    if ordinal < count
                    else {"instance_id": instance_id, "status": "no_patch"}
                )
                for ordinal, instance_id in enumerate(target_ids)
            ],
            "schema_version": collection.SOLVE_SUMMARY_SCHEMA,
            "solutions": count,
            "targets": collection.TARGET_COUNT,
        },
    )
    write_json(
        raw / "scenarios/scenarios_summary.json",
        {
            "differing_solutions": count,
            "manifest": [
                {"instance_id": instance_id, "status": "scenario"}
                for instance_id in ids
            ],
            "scenarios": count,
            "schema_version": collection.SCENARIOS_SUMMARY_SCHEMA,
        },
    )
    return spec_index, runtime_manifest, ids


def make_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    count: int = 13,
) -> tuple[Path, Path, Path, list[str]]:
    spec_index, runtime_manifest, ids = make_sources(tmp_path, count)
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    github = {
        "repository": GITHUB_REPOSITORY,
        "run_attempt": RUN_ATTEMPT,
        "run_id": RUN_ID,
        "sha": GITHUB_SHA,
        "workflow_ref": GITHUB_WORKFLOW_REF,
    }
    for shard_index in range(collection.SHARD_COUNT):
        shard = artifacts / collection.artifact_name(github, shard_index)
        shard.mkdir()
        assigned = [
            instance_id
            for ordinal, instance_id in enumerate(ids)
            if ordinal % collection.SHARD_COUNT == shard_index
        ]
        for name in collection._expected_log_names(assigned):
            (shard / name).write_bytes(f"evidence:{shard_index}:{name}\n".encode())
        collection.create_shard_receipt(
            execution_dir=shard,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
            shard_index=shard_index,
            shard_count=collection.SHARD_COUNT,
        )
    return artifacts, spec_index, runtime_manifest, ids


def collect_valid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path, Path, Path, list[str]]:
    artifacts, spec_index, runtime_manifest, ids = make_artifacts(tmp_path, monkeypatch)
    output = tmp_path / "complete"
    receipt = output / collection.AGGREGATE_RECEIPT_NAME
    collection.collect_shards(
        artifacts_dir=artifacts,
        output_dir=output,
        aggregate_receipt=receipt,
        spec_index=spec_index,
        runtime_manifest=runtime_manifest,
    )
    return output, receipt, spec_index, runtime_manifest, ids


def rewrite_receipt(path: Path, mutate) -> None:
    value = json.loads(path.read_text())
    mutate(value)
    path.write_bytes(collection.canonical_json_bytes(value))


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("solve_undercoverage", "does not exactly cover the frozen 53-target order"),
        ("solve_reordered", "does not exactly cover the frozen 53-target order"),
        ("scenario_availability", "scenario availability does not exactly match"),
        ("scenario_count", "scenario summary scenario count is inconsistent"),
        ("scenario_manifest_omission", "does not cover every differing solution required"),
        ("gold_equivalence", "gold-equivalence metadata differs"),
    ],
)
def test_direct_shard_receipt_rejects_semantically_drifted_stage_coverage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
    mutation: str,
    message: str,
) -> None:
    spec_index, runtime_manifest, ids = make_sources(tmp_path, count=6)
    raw = spec_index.parent.parent
    solve_path = raw / "solutions/solve_summary.json"
    scenarios_path = raw / "scenarios/scenarios_summary.json"
    if mutation.startswith("solve_") or mutation == "gold_equivalence":
        document = json.loads(solve_path.read_text())
        if mutation == "solve_undercoverage":
            document["manifest"].pop(0)
            document["solutions"] -= 1
            document["targets"] -= 1
        elif mutation == "solve_reordered":
            document["manifest"] = list(reversed(document["manifest"]))
        else:
            document["manifest"][0]["identical_to_gold"] = True
        write_json(solve_path, document)
    elif mutation in {"scenario_availability", "scenario_manifest_omission"}:
        document = json.loads(spec_index.read_text())
        row_index = 0 if mutation == "scenario_availability" else -1
        document["specs"][row_index]["scenario_available"] = False
        write_json(spec_index, document)
        if mutation == "scenario_manifest_omission":
            scenario_document = json.loads(scenarios_path.read_text())
            scenario_document["manifest"].pop()
            scenario_document["scenarios"] -= 1
            write_json(scenarios_path, scenario_document)
    else:
        document = json.loads(scenarios_path.read_text())
        document["scenarios"] -= 1
        write_json(scenarios_path, document)

    execution = tmp_path / "shard-zero"
    execution.mkdir()
    for name in collection._expected_log_names([ids[0]]):
        (execution / name).write_bytes(b"complete\n")
    with pytest.raises(collection.ExecutionCollectionError, match=message):
        collection.create_shard_receipt(
            execution_dir=execution,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
            shard_index=0,
            shard_count=8,
        )


def test_direct_shard_receipt_rejects_joint_target_and_solve_summary_shrink(
    tmp_path: Path,
    github_environment: dict[str, str],
) -> None:
    spec_index, runtime_manifest, ids = make_sources(tmp_path, count=6)
    raw = spec_index.parent.parent
    targets_path = raw / "solve_targets.json"
    targets = json.loads(targets_path.read_text())
    targets["targets"].pop()
    targets["count"] -= 1
    write_json(targets_path, targets)
    solve_path = raw / "solutions/solve_summary.json"
    solve = json.loads(solve_path.read_text())
    solve["manifest"].pop()
    solve["targets"] -= 1
    write_json(solve_path, solve)

    execution = tmp_path / "shard-zero"
    execution.mkdir()
    for name in collection._expected_log_names([ids[0]]):
        (execution / name).write_bytes(b"complete\n")
    with pytest.raises(
        collection.ExecutionCollectionError,
        match="frozen solve-target manifest is malformed",
    ):
        collection.create_shard_receipt(
            execution_dir=execution,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
            shard_index=0,
            shard_count=8,
        )


@pytest.mark.parametrize(("omitted", "accepted"), [(3, True), (4, False)])
def test_scenario_cap_permits_only_bounded_terminal_manifest_omissions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
    omitted: int,
    accepted: bool,
) -> None:
    spec_index, runtime_manifest, ids = make_sources(tmp_path, count=53)
    raw = spec_index.parent.parent
    spec_document = json.loads(spec_index.read_text())
    for row in spec_document["specs"][-omitted:]:
        row["scenario_available"] = False
    write_json(spec_index, spec_document)
    scenarios_path = raw / "scenarios/scenarios_summary.json"
    scenario_document = json.loads(scenarios_path.read_text())
    del scenario_document["manifest"][-omitted:]
    scenario_document["scenarios"] -= omitted
    write_json(scenarios_path, scenario_document)

    execution = tmp_path / "shard-zero"
    execution.mkdir()
    assigned = [
        instance_id
        for ordinal, instance_id in enumerate(ids)
        if ordinal % collection.SHARD_COUNT == 0
    ]
    for name in collection._expected_log_names(assigned):
        (execution / name).write_bytes(b"complete\n")
    if accepted:
        assert collection.create_shard_receipt(
            execution_dir=execution,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
            shard_index=0,
            shard_count=8,
        ).is_file()
    else:
        with pytest.raises(
            collection.ExecutionCollectionError,
            match="does not cover every differing solution required",
        ):
            collection.create_shard_receipt(
                execution_dir=execution,
                spec_index=spec_index,
                runtime_manifest=runtime_manifest,
                shard_index=0,
                shard_count=8,
            )


def test_valid_exact_eight_merge_and_offline_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    output, receipt, spec_index, runtime_manifest, ids = collect_valid(tmp_path, monkeypatch)
    document = collection.check_execution_bundle(
        execution_dir=output,
        aggregate_receipt=receipt,
        spec_index=spec_index,
        runtime_manifest=runtime_manifest,
    )
    assert document["github"] == github_environment
    assert document["assignment"]["ordered_instance_ids"] == ids
    assert [row["shard_index"] for row in document["shards"]] == list(range(8))
    assert len(document["logs"]) == 2 * len(ids)
    expected = set(collection._expected_log_names(ids))
    expected |= {collection.shard_receipt_name(index) for index in range(8)}
    expected.add(collection.AGGREGATE_RECEIPT_NAME)
    assert {path.name for path in output.iterdir()} == expected


def test_zero_solution_null_retains_eight_receipts_and_empty_verified_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    artifacts, spec_index, runtime_manifest, ids = make_artifacts(
        tmp_path, monkeypatch, count=0
    )
    assert ids == []
    for index in range(collection.SHARD_COUNT):
        shard = artifacts / collection.artifact_name(github_environment, index)
        assert {path.name for path in shard.iterdir()} == {
            collection.shard_receipt_name(index)
        }
    output = tmp_path / "complete-null"
    aggregate = collection.collect_shards(
        artifacts_dir=artifacts,
        output_dir=output,
        aggregate_receipt=output / collection.AGGREGATE_RECEIPT_NAME,
        spec_index=spec_index,
        runtime_manifest=runtime_manifest,
    )
    checked, log_bytes = collection.check_execution_bundle_with_logs(
        execution_dir=output,
        aggregate_receipt=output / collection.AGGREGATE_RECEIPT_NAME,
        spec_index=spec_index,
        runtime_manifest=runtime_manifest,
    )
    assert aggregate == checked
    assert checked["assignment"]["ordered_instance_ids"] == []
    assert checked["logs"] == []
    assert log_bytes == {}


def test_zero_solution_shell_runner_reaches_all_eight_receipt_only_shards(
    tmp_path: Path,
) -> None:
    experiment = "iter202_natural_rate_scaled"
    raw = tmp_path / f"experiments/{experiment}/proof/raw"
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for guard_name in (
        "build_iter202_image_lock.py",
        "validate_iter202_scenario_safety.py",
        "validate_iter202_runtime_freeze.py",
    ):
        (scripts / guard_name).write_text("raise SystemExit(0)\n")
    (scripts / "collect_iter202_execution.py").symlink_to(Path(collection.__file__))

    generator = {
        "distribution_filename": "swebench-4.1.0-py3-none-any.whl",
        "distribution_sha256": (
            "1243776f720047cc9e20a427f7a52b75c13a07abda6154fb60fe77f82ec8af57"
        ),
        "package": "swebench",
        "source_snapshot": (
            "experiments/iter154_reward_hack_benchmark_expansion_pilot/"
            "proof/raw/swebench_verified_rows_snapshot.json"
        ),
        "source_snapshot_sha256": (
            "8b912e9e1aff87ab16ebcdb37c636bd45fb23bf7dd90c4b88ca2ab11f0bd6385"
        ),
        "version": "4.1.0",
    }
    source_snapshot = tmp_path / generator["source_snapshot"]
    source_snapshot.parent.mkdir(parents=True)
    shutil.copy2(collection.ROOT / generator["source_snapshot"], source_snapshot)
    target_source = (
        collection.ROOT
        / "experiments/iter202_natural_rate_scaled/proof/raw/solve_targets.json"
    )
    targets = json.loads(target_source.read_text())
    target_ids = [row["instance_id"] for row in targets["targets"]]
    (raw / "specs").mkdir(parents=True)
    write_json(
        raw / "specs/index.json",
        {
            "count": 0,
            "generator": generator,
            "schema_version": collection.SPEC_INDEX_SCHEMA,
            "specs": [],
        },
    )
    write_json(raw / "solve_targets.json", targets)
    write_json(
        raw / "solutions/solve_summary.json",
        {
            "manifest": [
                {"instance_id": instance_id, "status": "no_patch"}
                for instance_id in target_ids
            ],
            "schema_version": collection.SOLVE_SUMMARY_SCHEMA,
            "solutions": 0,
            "targets": collection.TARGET_COUNT,
        },
    )
    write_json(
        raw / "scenarios/scenarios_summary.json",
        {
            "differing_solutions": 0,
            "manifest": [],
            "scenarios": 0,
            "schema_version": collection.SCENARIOS_SUMMARY_SCHEMA,
        },
    )
    write_json(
        raw / "runtime_manifest.json",
        {
            "experiment_id": collection.EXPERIMENT_ID,
            "schema_version": collection.RUNTIME_MANIFEST_SCHEMA,
        },
    )
    write_json(
        raw / "image_lock.json",
        {
            "count": collection.TARGET_COUNT,
            "images": [{"instance_id": instance_id} for instance_id in target_ids],
            "schema_version": "telos.iter202.image_lock.v1",
        },
    )
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    docker_marker = tmp_path / "docker-was-called"
    fake_docker = fake_bin / "docker"
    fake_docker.write_text(
        '#!/bin/sh\nprintf called > "$DOCKER_CALL_MARKER"\nexit 97\n'
    )
    fake_docker.chmod(0o755)
    env = dict(os.environ)
    env.update(
        {
            "DOCKER_CALL_MARKER": str(docker_marker),
            "GITHUB_REPOSITORY": GITHUB_REPOSITORY,
            "GITHUB_RUN_ATTEMPT": RUN_ATTEMPT,
            "GITHUB_RUN_ID": RUN_ID,
            "GITHUB_SHA": GITHUB_SHA,
            "GITHUB_WORKFLOW_REF": GITHUB_WORKFLOW_REF,
            "PATH": str(fake_bin) + os.pathsep + env["PATH"],
            "TELOS_NAT_EXP": experiment,
            "TELOS_NAT_SHARD_COUNT": str(collection.SHARD_COUNT),
        }
    )
    env.pop("GITHUB_ACTIONS", None)
    runner = collection.ROOT / "scripts/ci_iter200_execute.sh"
    execution = raw / "execution"
    for shard_index in range(collection.SHARD_COUNT):
        env["TELOS_NAT_SHARD_INDEX"] = str(shard_index)
        completed = subprocess.run(
            ["bash", str(runner)],
            cwd=tmp_path,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert {path.name for path in execution.iterdir()} == {
            collection.shard_receipt_name(shard_index)
        }
        receipt = collection.load_json_strict(
            execution / collection.shard_receipt_name(shard_index), canonical=True
        )
        assert receipt["assignment"]["ordered_instance_ids"] == []
        assert receipt["logs"] == []
        shutil.rmtree(execution)
    assert not docker_marker.exists()


def test_valid_solution_count_below_eight_retains_receipt_only_empty_shards(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    artifacts, spec_index, runtime_manifest, ids = make_artifacts(
        tmp_path, monkeypatch, count=6
    )
    for index in (6, 7):
        shard = artifacts / collection.artifact_name(github_environment, index)
        assert {path.name for path in shard.iterdir()} == {
            collection.shard_receipt_name(index)
        }
    output = tmp_path / "complete"
    aggregate = collection.collect_shards(
        artifacts_dir=artifacts,
        output_dir=output,
        aggregate_receipt=output / collection.AGGREGATE_RECEIPT_NAME,
        spec_index=spec_index,
        runtime_manifest=runtime_manifest,
    )
    assert aggregate["assignment"]["ordered_instance_ids"] == ids
    assert aggregate["shards"][6]["ordered_instance_ids"] == []
    assert aggregate["shards"][7]["ordered_instance_ids"] == []


def test_verified_log_snapshot_returns_exact_receipt_bound_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    output, receipt, spec_index, runtime_manifest, ids = collect_valid(
        tmp_path, monkeypatch
    )
    aggregate, log_bytes = collection.check_execution_bundle_with_logs(
        execution_dir=output,
        aggregate_receipt=receipt,
        spec_index=spec_index,
        runtime_manifest=runtime_manifest,
    )
    assert list(log_bytes) == [row["name"] for row in aggregate["logs"]]
    assert log_bytes[f"{ids[0]}.variant.log"] == (
        output / f"{ids[0]}.variant.log"
    ).read_bytes()


def test_verified_log_snapshot_rejects_replacement_after_bundle_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    output, receipt, spec_index, runtime_manifest, ids = collect_valid(
        tmp_path, monkeypatch
    )
    log_path = output / f"{ids[0]}.variant.log"
    original_check = collection.check_execution_bundle

    def check_then_replace(**kwargs):
        document = original_check(**kwargs)
        log_path.write_bytes(b"replacement after aggregate verification\n")
        return document

    monkeypatch.setattr(collection, "check_execution_bundle", check_then_replace)
    with pytest.raises(
        collection.ExecutionCollectionError,
        match="changed before the verified snapshot",
    ):
        collection.check_execution_bundle_with_logs(
            execution_dir=output,
            aggregate_receipt=receipt,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
        )


def test_offline_ingest_validates_then_atomically_installs_and_is_idempotent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    bundle, _, spec_index, runtime_manifest, ids = collect_valid(tmp_path, monkeypatch)
    destination = tmp_path / "ingested/execution"
    document = collection.ingest_execution_bundle(
        bundle_dir=bundle,
        execution_dir=destination,
        spec_index=spec_index,
        runtime_manifest=runtime_manifest,
        expected_run_id=RUN_ID,
        expected_run_attempt=RUN_ATTEMPT,
        expected_github_sha=GITHUB_SHA,
    )
    assert document["assignment"]["ordered_instance_ids"] == ids
    assert {path.name for path in destination.iterdir()} == {
        path.name for path in bundle.iterdir()
    }
    assert collection.ingest_execution_bundle(
        bundle_dir=bundle,
        execution_dir=destination,
        spec_index=spec_index,
        runtime_manifest=runtime_manifest,
        expected_run_id=RUN_ID,
        expected_run_attempt=RUN_ATTEMPT,
        expected_github_sha=GITHUB_SHA,
    ) == document


def test_offline_ingest_rejects_tamper_without_creating_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    bundle, _, spec_index, runtime_manifest, ids = collect_valid(tmp_path, monkeypatch)
    (bundle / f"{ids[0]}.variant.log").write_bytes(b"tampered\n")
    destination = tmp_path / "ingested/execution"
    with pytest.raises(collection.ExecutionCollectionError):
        collection.ingest_execution_bundle(
            bundle_dir=bundle,
            execution_dir=destination,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
            expected_run_id=RUN_ID,
            expected_run_attempt=RUN_ATTEMPT,
            expected_github_sha=GITHUB_SHA,
        )
    assert not destination.exists()


def test_check_rejects_top_level_execution_directory_symlink(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    bundle, _, spec_index, runtime_manifest, _ = collect_valid(tmp_path, monkeypatch)
    linked_bundle = tmp_path / "linked-bundle"
    linked_bundle.symlink_to(bundle, target_is_directory=True)
    with pytest.raises(
        collection.ExecutionCollectionError,
        match="symlink path component|without following symlinks",
    ):
        collection.check_execution_bundle(
            execution_dir=linked_bundle,
            aggregate_receipt=linked_bundle / collection.AGGREGATE_RECEIPT_NAME,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
        )


def test_ingest_rejects_dangling_destination_symlink_without_touching_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    bundle, _, spec_index, runtime_manifest, _ = collect_valid(tmp_path, monkeypatch)
    external = tmp_path / "outside/execution"
    destination = tmp_path / "ingested/execution"
    destination.parent.mkdir()
    destination.symlink_to(external, target_is_directory=True)
    with pytest.raises(
        collection.ExecutionCollectionError,
        match="symlink path component|without following symlinks",
    ):
        collection.ingest_execution_bundle(
            bundle_dir=bundle,
            execution_dir=destination,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
            expected_run_id=RUN_ID,
            expected_run_attempt=RUN_ATTEMPT,
            expected_github_sha=GITHUB_SHA,
        )
    assert destination.is_symlink()
    assert not external.exists()


def test_collect_rejects_dangling_output_symlink_without_touching_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    artifacts, spec_index, runtime_manifest, _ = make_artifacts(tmp_path, monkeypatch)
    external = tmp_path / "outside/complete"
    output = tmp_path / "complete-link"
    output.symlink_to(external, target_is_directory=True)
    with pytest.raises(
        collection.ExecutionCollectionError,
        match="symlink path component|without following symlinks",
    ):
        collection.collect_shards(
            artifacts_dir=artifacts,
            output_dir=output,
            aggregate_receipt=output / collection.AGGREGATE_RECEIPT_NAME,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
        )
    assert output.is_symlink()
    assert not external.exists()


def test_check_rejects_symlinked_parent_component(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    bundle, _, spec_index, runtime_manifest, _ = collect_valid(tmp_path, monkeypatch)
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    moved_bundle = real_parent / "bundle"
    bundle.rename(moved_bundle)
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    linked_bundle = linked_parent / "bundle"
    with pytest.raises(
        collection.ExecutionCollectionError,
        match="symlink path component|without following symlinks",
    ):
        collection.check_execution_bundle(
            execution_dir=linked_bundle,
            aggregate_receipt=linked_bundle / collection.AGGREGATE_RECEIPT_NAME,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
        )


def test_ingest_rejects_symlinked_destination_parent_without_external_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    bundle, _, spec_index, runtime_manifest, _ = collect_valid(tmp_path, monkeypatch)
    external_parent = tmp_path / "external-parent"
    external_parent.mkdir()
    linked_parent = tmp_path / "linked-destination-parent"
    linked_parent.symlink_to(external_parent, target_is_directory=True)
    external_destination = external_parent / "execution"
    with pytest.raises(
        collection.ExecutionCollectionError,
        match="symlink path component|without following symlinks",
    ):
        collection.ingest_execution_bundle(
            bundle_dir=bundle,
            execution_dir=linked_parent / "execution",
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
            expected_run_id=RUN_ID,
            expected_run_attempt=RUN_ATTEMPT,
            expected_github_sha=GITHUB_SHA,
        )
    assert not external_destination.exists()


def test_documented_tmp_alias_is_normalized_but_nested_symlinks_are_rejected() -> None:
    with tempfile.TemporaryDirectory(prefix="telos-exact8-", dir="/tmp") as directory:
        trusted_alias_path = Path(directory)
        regular = trusted_alias_path / "regular"
        regular.mkdir()
        assert collection._require_regular_directory(regular, "documented /tmp path") == []

        outside = trusted_alias_path / "outside"
        outside.mkdir()
        nested_link = regular / "nested-link"
        nested_link.symlink_to(outside, target_is_directory=True)
        with pytest.raises(
            collection.ExecutionCollectionError,
            match="symlink path component|without following symlinks",
        ):
            collection._require_regular_directory(
                nested_link, "nested caller-controlled /tmp path"
            )


def test_descriptor_anchored_read_cannot_be_redirected_by_parent_symlink_swap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence_parent = tmp_path / "evidence-parent"
    evidence_parent.mkdir()
    evidence = evidence_parent / "evidence.log"
    evidence.write_bytes(b"receipt-bound bytes\n")
    attacker_parent = tmp_path / "attacker-parent"
    attacker_parent.mkdir()
    (attacker_parent / evidence.name).write_bytes(b"attacker bytes\n")
    detached_parent = tmp_path / "detached-original-parent"
    original_open_directory = collection._open_directory_fd
    swapped = False

    def open_then_swap(path: Path, label: str) -> int:
        nonlocal swapped
        descriptor = original_open_directory(path, label)
        if collection._absolute_no_resolve(path) == evidence_parent and not swapped:
            evidence_parent.rename(detached_parent)
            evidence_parent.symlink_to(attacker_parent, target_is_directory=True)
            swapped = True
        return descriptor

    monkeypatch.setattr(collection, "_open_directory_fd", open_then_swap)
    assert collection._read_regular_file(evidence) == b"receipt-bound bytes\n"
    assert swapped is True


def test_ingest_parent_symlink_swap_fails_closed_without_external_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    bundle, _, spec_index, runtime_manifest, _ = collect_valid(tmp_path, monkeypatch)
    destination_parent = tmp_path / "destination-parent"
    destination_parent.mkdir()
    detached_parent = tmp_path / "detached-destination-parent"
    attacker_parent = tmp_path / "attacker-destination-parent"
    attacker_parent.mkdir()
    destination = destination_parent / "execution"
    original_open_directory = collection._open_directory_fd
    swapped = False

    def open_then_swap(path: Path, label: str) -> int:
        nonlocal swapped
        descriptor = original_open_directory(path, label)
        if label == "execution destination parent" and not swapped:
            destination_parent.rename(detached_parent)
            destination_parent.symlink_to(attacker_parent, target_is_directory=True)
            swapped = True
        return descriptor

    monkeypatch.setattr(collection, "_open_directory_fd", open_then_swap)
    with pytest.raises(
        collection.ExecutionCollectionError,
        match="without following symlinks",
    ):
        collection.ingest_execution_bundle(
            bundle_dir=bundle,
            execution_dir=destination,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
            expected_run_id=RUN_ID,
            expected_run_attempt=RUN_ATTEMPT,
            expected_github_sha=GITHUB_SHA,
        )
    assert swapped is True
    assert not (attacker_parent / "execution").exists()
    assert list(attacker_parent.iterdir()) == []


@pytest.mark.parametrize(
    ("run_id", "run_attempt", "sha"),
    [
        ("999", RUN_ATTEMPT, GITHUB_SHA),
        (RUN_ID, "4", GITHUB_SHA),
        (RUN_ID, RUN_ATTEMPT, "b" * 40),
    ],
)
def test_offline_ingest_rejects_internally_valid_wrong_run_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
    run_id: str,
    run_attempt: str,
    sha: str,
) -> None:
    bundle, _, spec_index, runtime_manifest, _ = collect_valid(tmp_path, monkeypatch)
    destination = tmp_path / "ingested/execution"
    with pytest.raises(collection.ExecutionCollectionError, match="operator-recorded"):
        collection.ingest_execution_bundle(
            bundle_dir=bundle,
            execution_dir=destination,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
            expected_run_id=run_id,
            expected_run_attempt=run_attempt,
            expected_github_sha=sha,
        )
    assert not destination.exists()


@pytest.mark.parametrize(
    "argv",
    [
        [
            "shard-receipt",
            "--execution-dir", "execution",
            "--spec-index", "index.json",
            "--runtime-manifest", "runtime.json",
            "--shard-index", "0",
            "--shard-count", "8",
        ],
        [
            "collect",
            "--artifacts-dir", "artifacts",
            "--output-dir", "execution",
            "--aggregate-receipt", "execution/_telos_iter202_execution_complete.receipt.json",
        ],
        [
            "check",
            "--execution-dir", "execution",
            "--aggregate-receipt", "execution/_telos_iter202_execution_complete.receipt.json",
            "--spec-index", "index.json",
            "--runtime-manifest", "runtime.json",
        ],
        [
            "ingest",
            "--bundle-dir", "bundle",
            "--execution-dir", "execution",
            "--spec-index", "index.json",
            "--runtime-manifest", "runtime.json",
            "--expected-run-id", RUN_ID,
            "--expected-run-attempt", RUN_ATTEMPT,
            "--expected-github-sha", GITHUB_SHA,
        ],
    ],
)
def test_all_cli_subcommands_parse_without_option_conflicts(argv: list[str]) -> None:
    assert collection._parser().parse_args(argv).command == argv[0]


def test_missing_shard_fails_without_materializing_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    artifacts, spec_index, runtime_manifest, _ = make_artifacts(tmp_path, monkeypatch)
    shutil.rmtree(artifacts / collection.artifact_name(github_environment, 6))
    output = tmp_path / "complete"
    with pytest.raises(collection.ExecutionCollectionError, match="exact shard indexes"):
        collection.collect_shards(
            artifacts_dir=artifacts,
            output_dir=output,
            aggregate_receipt=output / collection.AGGREGATE_RECEIPT_NAME,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
        )
    assert not output.exists()


def test_extra_artifact_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    artifacts, spec_index, runtime_manifest, _ = make_artifacts(tmp_path, monkeypatch)
    (artifacts / "iter202-execution-debug-partial").mkdir()
    output = tmp_path / "complete"
    with pytest.raises(collection.ExecutionCollectionError, match="unexpected collector artifact"):
        collection.collect_shards(
            artifacts_dir=artifacts,
            output_dir=output,
            aggregate_receipt=output / collection.AGGREGATE_RECEIPT_NAME,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
        )


def test_partial_failure_artifact_without_receipt_is_ineligible(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    artifacts, spec_index, runtime_manifest, _ = make_artifacts(tmp_path, monkeypatch)
    shard = artifacts / collection.artifact_name(github_environment, 4)
    (shard / collection.shard_receipt_name(4)).unlink()
    next(path for path in shard.iterdir() if path.suffix == ".log").unlink()
    output = tmp_path / "complete"
    with pytest.raises(collection.ExecutionCollectionError):
        collection.collect_shards(
            artifacts_dir=artifacts,
            output_dir=output,
            aggregate_receipt=output / collection.AGGREGATE_RECEIPT_NAME,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
        )


def test_extra_or_collision_log_in_shard_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    artifacts, spec_index, runtime_manifest, ids = make_artifacts(tmp_path, monkeypatch)
    shard_zero = artifacts / collection.artifact_name(github_environment, 0)
    shard_one = artifacts / collection.artifact_name(github_environment, 1)
    collision = f"{ids[0]}.gold.log"
    (shard_one / collision).write_bytes((shard_zero / collision).read_bytes())
    output = tmp_path / "complete"
    with pytest.raises(collection.ExecutionCollectionError, match="missing or extra files"):
        collection.collect_shards(
            artifacts_dir=artifacts,
            output_dir=output,
            aggregate_receipt=output / collection.AGGREGATE_RECEIPT_NAME,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
        )


def test_symlinked_expected_log_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    artifacts, spec_index, runtime_manifest, ids = make_artifacts(tmp_path, monkeypatch)
    shard = artifacts / collection.artifact_name(github_environment, 0)
    log = shard / f"{ids[0]}.gold.log"
    external = tmp_path / "external.log"
    external.write_bytes(log.read_bytes())
    log.unlink()
    log.symlink_to(external)
    output = tmp_path / "complete"
    with pytest.raises(
        collection.ExecutionCollectionError,
        match="symlink path component|without following symlinks|non-symlink|regular",
    ):
        collection.collect_shards(
            artifacts_dir=artifacts,
            output_dir=output,
            aggregate_receipt=output / collection.AGGREGATE_RECEIPT_NAME,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
        )


def test_mixed_run_attempt_artifact_names_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    artifacts, spec_index, runtime_manifest, _ = make_artifacts(tmp_path, monkeypatch)
    old = artifacts / collection.artifact_name(github_environment, 7)
    mixed = dict(github_environment)
    mixed["run_attempt"] = "2"
    old.rename(artifacts / collection.artifact_name(mixed, 7))
    output = tmp_path / "complete"
    with pytest.raises(collection.ExecutionCollectionError, match="mix GitHub runs or attempts"):
        collection.collect_shards(
            artifacts_dir=artifacts,
            output_dir=output,
            aggregate_receipt=output / collection.AGGREGATE_RECEIPT_NAME,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
        )


def test_mixed_commit_sha_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    artifacts, spec_index, runtime_manifest, _ = make_artifacts(tmp_path, monkeypatch)
    receipt = artifacts / collection.artifact_name(github_environment, 5) / collection.shard_receipt_name(5)
    rewrite_receipt(receipt, lambda value: value["github"].__setitem__("sha", "b" * 40))
    output = tmp_path / "complete"
    with pytest.raises(collection.ExecutionCollectionError, match="not from the current GitHub run attempt|mix GitHub provenance"):
        collection.collect_shards(
            artifacts_dir=artifacts,
            output_dir=output,
            aggregate_receipt=output / collection.AGGREGATE_RECEIPT_NAME,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
        )


@pytest.mark.parametrize("field", ["repository", "workflow_ref"])
def test_mixed_repository_or_workflow_ref_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
    field: str,
) -> None:
    artifacts, spec_index, runtime_manifest, _ = make_artifacts(tmp_path, monkeypatch)
    receipt = artifacts / collection.artifact_name(github_environment, 2) / collection.shard_receipt_name(2)

    def mutate(value: dict) -> None:
        if field == "repository":
            value["github"]["repository"] = "different-owner/telos"
            value["github"]["workflow_ref"] = (
                "different-owner/telos/.github/workflows/iter202-execute.yml@refs/heads/master"
            )
        else:
            value["github"]["workflow_ref"] = (
                "manfromnowhere143/telos/.github/workflows/iter202-execute.yml@refs/heads/other"
            )

    rewrite_receipt(receipt, mutate)
    output = tmp_path / "complete"
    with pytest.raises(
        collection.ExecutionCollectionError,
        match="not from the current GitHub run attempt|mix GitHub provenance",
    ):
        collection.collect_shards(
            artifacts_dir=artifacts,
            output_dir=output,
            aggregate_receipt=output / collection.AGGREGATE_RECEIPT_NAME,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
        )


def test_mixed_runtime_manifest_binding_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    artifacts, spec_index, runtime_manifest, _ = make_artifacts(tmp_path, monkeypatch)
    receipt = artifacts / collection.artifact_name(github_environment, 3) / collection.shard_receipt_name(3)
    rewrite_receipt(
        receipt,
        lambda value: value["source"].__setitem__("runtime_manifest_sha256", "f" * 64),
    )
    output = tmp_path / "complete"
    with pytest.raises(collection.ExecutionCollectionError, match="source hashes differ"):
        collection.collect_shards(
            artifacts_dir=artifacts,
            output_dir=output,
            aggregate_receipt=output / collection.AGGREGATE_RECEIPT_NAME,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
        )


@pytest.mark.parametrize("kind", ["log", "shard_receipt", "aggregate_receipt", "spec_index"])
def test_post_collection_tamper_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
    kind: str,
) -> None:
    output, receipt, spec_index, runtime_manifest, ids = collect_valid(tmp_path, monkeypatch)
    if kind == "log":
        (output / f"{ids[0]}.gold.log").write_bytes(b"tampered\n")
    elif kind == "shard_receipt":
        (output / collection.shard_receipt_name(0)).write_bytes(b"{}\n")
    elif kind == "aggregate_receipt":
        receipt.write_bytes(b"{}\n")
    else:
        spec_index.write_bytes(spec_index.read_bytes() + b" ")
    with pytest.raises(collection.ExecutionCollectionError):
        collection.check_execution_bundle(
            execution_dir=output,
            aggregate_receipt=receipt,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
        )


def test_strict_json_rejects_duplicate_and_nonfinite_receipts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    output, receipt, spec_index, runtime_manifest, _ = collect_valid(tmp_path, monkeypatch)
    for payload in (b'{"schema_version":"x","schema_version":"y"}\n', b'{"x":NaN}\n'):
        receipt.write_bytes(payload)
        with pytest.raises(collection.ExecutionCollectionError):
            collection.check_execution_bundle(
                execution_dir=output,
                aggregate_receipt=receipt,
                spec_index=spec_index,
                runtime_manifest=runtime_manifest,
            )


def test_shard_receipt_refuses_missing_extra_and_noncanonical_run_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    github_environment: dict[str, str],
) -> None:
    spec_index, runtime_manifest, ids = make_sources(tmp_path, 1)
    execution = tmp_path / "single"
    execution.mkdir()
    for name in collection._expected_log_names(ids):
        (execution / name).write_bytes(b"complete\n")
    (execution / "extra.log").write_bytes(b"extra\n")
    with pytest.raises(collection.ExecutionCollectionError, match="file set differs"):
        collection.create_shard_receipt(
            execution_dir=execution,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
            shard_index=0,
            shard_count=8,
        )
    (execution / "extra.log").unlink()
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "03")
    with pytest.raises(collection.ExecutionCollectionError, match="run attempt"):
        collection.create_shard_receipt(
            execution_dir=execution,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
            shard_index=0,
            shard_count=8,
        )
