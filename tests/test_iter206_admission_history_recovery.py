from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

import pytest

from scripts import build_iter206_runtime_manifest as runtime
from scripts import adjudicate_iter206_admission_history_recovery as adjudicator
from scripts import capture_iter206_runtime_host as host_capture
from scripts import collect_iter206_execution as collection
from scripts import prepare_iter206_output_directory as output_directory
from scripts import publish_iter206_runtime_diagnostic as diagnostic
from scripts import run_iter206_admission_history_recovery_blind_judge as blind_judge
from scripts import validate_iter205_pre_dispatch_null as null_guard
from scripts import validate_iter206_publication_safety as publication
from scripts import validate_iter206_runtime_recovery as contract


ROOT = Path(__file__).resolve().parents[1]
GITHUB = {
    "repository": collection.CANONICAL_REPOSITORY,
    "run_attempt": "1",
    "run_id": "42",
    "sha": "a" * 40,
    "workflow_ref": collection.CANONICAL_WORKFLOW_REF,
}


def runtime_host(github: dict[str, str] | None = None) -> dict[str, object]:
    side = {
        "api_version": "1.48",
        "architecture": "amd64",
        "git_commit": "abcdef0",
        "os": "linux",
        "version": "28.0.4",
    }
    return {
        "docker_client": side,
        "docker_server": side,
        "github": github or GITHUB,
        "runner_image": {
            "architecture": "X64",
            "image_os": "ubuntu24",
            "image_version": "20260713.1",
            "os": "Linux",
        },
        "schema_version": host_capture.SCHEMA,
        "statement": "observed_host_metadata_not_an_immutability_claim",
    }


def test_iter205_admission_null_and_frozen_runtime_are_exact() -> None:
    assert null_guard.validate() == {
        "provider_calls": 0,
        "dispatch_requests": 0,
        "iter204_push_parse_failures": 4,
        "iter205_workflow_runs": 0,
        "scientific_executions": 0,
    }
    for relative, expected in contract.FROZEN_ITER205.items():
        assert contract.sha256(ROOT / relative) == expected
    assert runtime.validate_frozen_iter205_manifest()["file_count"] == 180


def test_original_incompatible_local_logger_tuple_is_a_regression_failure() -> None:
    runner = contract.RUNNER.read_text()
    assert contract.validate_local_log_contract(runner, label="fixture") == []
    old_tuple = runner.replace("  --log-opt compress=false\n", "", 1)
    failures = "\n".join(contract.validate_local_log_contract(old_tuple, label="fixture"))
    assert "incompatible local/max-file=1/default-compression triple returned" in failures
    duplicate = runner.replace(
        "  --log-opt compress=false\n",
        "  --log-opt compress=false\n  --log-opt compress=false\n",
        1,
    )
    assert "must occur exactly once" in "\n".join(
        contract.validate_local_log_contract(duplicate, label="fixture")
    )


def test_runner_regression_rejects_deleting_the_sole_launch_diagnostic() -> None:
    runner = contract.RUNNER.read_text()
    assert contract.validate_runner_text(runner) == []
    deleted = runner.replace(
        '    echo "$iid CERTIFICATION_INFRA_FAIL exit=$variant_rc" >&2',
        '    echo "$iid CERTIFICATION_INFRA_FAIL exit=$variant_rc" >&2\n'
        '    rm -f "$variant_tmp"',
        1,
    )
    failures = "\n".join(contract.validate_runner_text(deleted))
    assert "delete the sole variant launch diagnostic" in failures
    removed_retention = runner.replace("retain_launch_diagnostic", "discard_diagnostic")
    assert "does not retain every declared failure phase" in "\n".join(
        contract.validate_runner_text(removed_retention)
    )


def test_smoke_is_no_science_and_precedes_all_shards() -> None:
    smoke = contract.SMOKE.read_text()
    workflow = contract.WORKFLOW.read_text()
    assert contract.validate_smoke_text(smoke) == []
    assert contract.validate_workflow_text(workflow) == []
    assert "needs: [authorize, smoke]" in workflow
    assert "$SOLS" not in smoke and "$SCEN" not in smoke
    assert not re.search(r"(?m)^\s*-v\s", smoke)
    assert "--entrypoint bash" in smoke


def test_workflow_rejects_attempt_two_extra_history_and_non_exact_six() -> None:
    workflow = contract.WORKFLOW.read_text()
    for fragment in (
        'test "${GITHUB_RUN_ATTEMPT}" = "1"',
        '[row.get("id") for row in iter206_runs] != [current_run_id]',
        '[row.get("id") for row in iter206_dispatch_runs] != [current_run_id]',
        "iter204_workflow_id = 314113289",
        "len(iter204_runs) != 6",
        "set(run_numbers) != set(range(1, 7))",
        "29468669956",
        "29468768706",
        "expected_iter204_release_run_id",
        "expected_iter204_primary_run_id",
        "iter205 all-event and dispatch histories must remain empty",
        'iter206_workflow.get("name") != "iter206-execute"',
    ):
        assert fragment in workflow
    weakened = workflow.replace(
        '[row.get("id") for row in iter206_runs] != [current_run_id]',
        "current_run_id not in [row.get(\"id\") for row in iter206_runs]",
    )
    assert "missing contract fragment" in "\n".join(contract.validate_workflow_text(weakened))
    relaxed_six = workflow.replace(
        "len(iter204_runs) != 6",
        "len(iter204_runs) < 6",
        1,
    )
    assert "missing contract fragment" in "\n".join(contract.validate_workflow_text(relaxed_six))
    with pytest.raises(collection.ExecutionCollectionError, match="attempt 1"):
        collection._validate_github({**GITHUB, "run_attempt": "2"}, "fixture")
    assert collection.ARTIFACT_RE.fullmatch(
        "iter206-execution-run-42-attempt-1-shard-0-of-8"
    )
    assert collection.ARTIFACT_RE.fullmatch(
        "iter206-execution-run-42-attempt-2-shard-0-of-8"
    ) is None


def test_runner_context_is_forbidden_in_job_env_and_bound_only_at_step() -> None:
    workflow = contract.WORKFLOW.read_text()
    assert contract.validate_workflow_text(workflow) == []
    step_binding = (
        "      - name: Run iter206 execution shard\n"
        "        env:\n"
        "          TELOS_ITER206_SMOKE_RECEIPT: "
        "${{ runner.temp }}/iter206-smoke/smoke.receipt.json\n"
        "        run: bash scripts/ci_iter206_execute.sh"
    )
    invalid = workflow.replace(
        "      TELOS_ITER206_SHARD_INDEX: ${{ matrix.shard }}",
        "      TELOS_ITER206_SHARD_INDEX: ${{ matrix.shard }}\n"
        "      TELOS_ITER206_SMOKE_RECEIPT: "
        "${{ runner.temp }}/iter206-smoke/smoke.receipt.json",
        1,
    ).replace(
        step_binding,
        "      - name: Run iter206 execution shard\n"
        "        run: bash scripts/ci_iter206_execute.sh",
        1,
    )
    failures = "\n".join(contract.validate_workflow_text(invalid))
    assert "runner context in job-level env" in failures
    assert "not bound once in execution-step env" in failures
    inline = workflow.replace(
        "    env:\n"
        "      TELOS_ITER206_PRIMARY_CI_AUTHORIZATION: "
        "${{ needs.authorize.outputs.primary_ci_authorization }}",
        "    env: {BAD: '${{ runner.temp }}'}",
        1,
    )
    assert "runner context in job-level env" in "\n".join(
        contract.validate_workflow_text(inline)
    )


def test_allowed_delta_guard_rejects_any_scientific_or_collector_extension() -> None:
    assert contract.validate_cross_contract_identity() == []
    runner_tamper = contract.RUNNER.read_text().replace(
        "CERT_TIMEOUT_SECONDS=900",
        "CERT_TIMEOUT_SECONDS=901",
        1,
    )
    failures = "\n".join(
        contract.validate_cross_contract_identity({contract.RUNNER: runner_tamper})
    )
    assert "scientific runtime differs beyond iter206 identity" in failures
    collector_tamper = contract.COLLECTOR.read_text().replace(
        "_core._validate_authorization = _validate_authorization",
        "_core._validate_authorization = lambda value, github, label: value",
        1,
    )
    failures = "\n".join(
        contract.validate_cross_contract_identity(
            {contract.COLLECTOR: collector_tamper}
        )
    )
    assert "exact authorization extension" in failures
    assert "not inspectable" in failures
    assert "collector differs beyond" in failures


def test_authorization_binds_exact_six_and_rejects_receipt_identity_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        collection,
        "_git_merge_parents",
        lambda _sha: (
            "4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f",
            "b" * 40,
        ),
    )
    checks = [
        {
            "app_slug": "github-actions",
            "conclusion": "success",
            "details_url": (
                f"https://github.com/{collection.CANONICAL_REPOSITORY}/"
                f"actions/runs/7/job/{identifier}"
            ),
            "id": identifier,
            "name": name,
            "status": "completed",
        }
        for identifier, name in ((11, "verify py3.11"), (12, "verify py3.12"))
    ]
    release_ci_runs = []
    for ordinal, event in enumerate(("push", "pull_request")):
        release_ci_runs.append(
            {
                "conclusion": "success",
                "event": event,
                "head_branch": collection.RELEASE_BRANCH,
                "head_repository": {
                    "full_name": collection.CANONICAL_REPOSITORY,
                },
                "head_sha": "b" * 40,
                "id": 20 + ordinal,
                "path": ".github/workflows/ci.yml",
                "required_jobs": [
                    {
                        "conclusion": "success",
                        "head_sha": "b" * 40,
                        "id": 30 + ordinal * 2 + job_ordinal,
                        "name": name,
                        "run_attempt": 1,
                        "status": "completed",
                    }
                    for job_ordinal, name in enumerate(
                        ("verify py3.11", "verify py3.12")
                    )
                ],
                "run_attempt": 1,
                "status": "completed",
            }
        )
    value = {
        "approved_commit_sha": GITHUB["sha"],
        "current_run_attempt": 1,
        "current_run_id": int(GITHUB["run_id"]),
        "iter204_admission_history_sha256": "",
        "iter204_dispatch_count": 0,
        "iter204_primary_run_id": 900002,
        "iter204_release_run_id": 900001,
        "iter204_workflow_id": 314113289,
        "iter205_all_event_count": 0,
        "iter205_dispatch_count": 0,
        "iter205_workflow_id": 314141096,
        "iter206_workflow_id": 314200000,
        "merge_first_parent": "4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f",
        "merge_second_parent": "b" * 40,
        "primary_ci_event": "push",
        "primary_ci_head_branch": "master",
        "primary_ci_run_attempt": 1,
        "primary_ci_run_id": 7,
        "primary_ci_workflow_path": ".github/workflows/ci.yml",
        "release_ci_head_sha": "b" * 40,
        "release_ci_runs": release_ci_runs,
        "required_checks": checks,
        "schema_version": collection.PRIMARY_CI_AUTHORIZATION_SCHEMA,
    }
    value["iter204_admission_history_sha256"] = collection._canonical_sha256(
        collection._expected_iter204_admission_projection(value)
    )
    assert collection._validate_authorization(value, GITHUB, "fixture") == value
    for key, bad in (
        ("current_run_attempt", 2),
        ("current_run_id", 43),
        ("primary_ci_run_attempt", 2),
        ("primary_ci_run_id", int(GITHUB["run_id"])),
        ("iter204_admission_history_sha256", "c" * 64),
        ("iter204_dispatch_count", 1),
        ("iter204_primary_run_id", 29465584664),
        ("iter204_release_run_id", 29465924803),
        ("iter204_workflow_id", 1),
        ("iter205_all_event_count", 1),
        ("iter205_dispatch_count", 1),
        ("iter205_workflow_id", 1),
        ("iter206_workflow_id", 314141096),
        ("merge_first_parent", "0" * 40),
        ("merge_second_parent", GITHUB["sha"]),
        ("release_ci_head_sha", "d" * 40),
        (
            "release_ci_runs",
            [
                {
                    **release_ci_runs[0],
                    "head_repository": {"full_name": "fork/telos"},
                },
                release_ci_runs[1],
            ],
        ),
        (
            "release_ci_runs",
            [
                {**release_ci_runs[0], "run_attempt": 2},
                release_ci_runs[1],
            ],
        ),
        ("schema_version", "telos.iter206.primary_ci_authorization.v1"),
        ("schema_version", "telos.iter205.primary_ci_authorization.v1"),
    ):
        with pytest.raises(collection.ExecutionCollectionError):
            collection._validate_authorization({**value, key: bad}, GITHUB, "fixture")

    with pytest.raises(
        collection.ExecutionCollectionError,
        match="does not reproduce the exact-six iter204 admission digest",
    ):
        collection._validate_authorization(
            {**value, "iter204_release_run_id": 900003},
            GITHUB,
            "fixture",
        )

    duplicated_checks = [checks[0], {**checks[1], "id": checks[0]["id"]}]
    duplicated_checks[1]["details_url"] = checks[0]["details_url"]
    with pytest.raises(
        collection.ExecutionCollectionError,
        match="Actions run and CI job identities are not exact and unique",
    ):
        collection._validate_authorization(
            {**value, "required_checks": duplicated_checks},
            GITHUB,
            "fixture",
        )

    monkeypatch.setattr(
        collection,
        "_git_merge_parents",
        lambda _sha: (
            "4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f",
            "d" * 40,
        ),
    )
    with pytest.raises(
        collection.ExecutionCollectionError,
        match="does not match the checked-out iter206 merge parents",
    ):
        collection._validate_authorization(value, GITHUB, "fixture")


def test_git_parent_binding_reads_one_exact_two_parent_commit() -> None:
    assert collection._git_merge_parents(
        "4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f"
    ) == (
        "c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446",
        "a336b4909329d392f6db5f6098792e07a17f28cb",
    )


def test_runtime_host_requires_canonical_attempt1_and_all_version_planes() -> None:
    assert host_capture.validate_document(runtime_host()) == runtime_host()
    for mutation in (
        {**runtime_host(), "github": {**GITHUB, "run_attempt": "2"}},
        {**runtime_host(), "github": {**GITHUB, "repository": "fork/telos"}},
        {
            **runtime_host(),
            "runner_image": {
                **runtime_host()["runner_image"],  # type: ignore[arg-type]
                "image_version": "unavailable",
            },
        },
    ):
        with pytest.raises(host_capture.RuntimeHostError):
            host_capture.validate_document(mutation)


def test_diagnostic_publication_is_bounded_bound_and_removes_no_last_copy_early(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "visible.work"
    source.write_bytes(b"x" * 100)
    destination = tmp_path / "diagnostic.log"
    metadata = tmp_path / "diagnostic.receipt.json"
    runtime_manifest = tmp_path / "runtime.json"
    runtime_manifest.write_bytes(b"{}\n")
    host = tmp_path / "host.json"
    host.write_bytes(host_capture.canonical_json_bytes(runtime_host()))
    for key, value in {
        "GITHUB_REPOSITORY": GITHUB["repository"],
        "GITHUB_RUN_ATTEMPT": GITHUB["run_attempt"],
        "GITHUB_RUN_ID": GITHUB["run_id"],
        "GITHUB_SHA": GITHUB["sha"],
        "GITHUB_WORKFLOW_REF": GITHUB["workflow_ref"],
    }.items():
        monkeypatch.setenv(key, value)
    truncated = diagnostic.publish(
        source,
        destination,
        metadata,
        64,
        phase="fixture",
        row_id="repo__task-1",
        image_ref="image@sha256:" + "b" * 64,
        image_id="sha256:" + "c" * 64,
        shard_index=0,
        exit_code=125,
        argv_sha256="d" * 64,
        runtime_manifest=runtime_manifest,
        runtime_host_receipt=host,
    )
    assert truncated is True
    assert not source.exists()
    assert destination.stat().st_size == 64
    receipt = json.loads(metadata.read_bytes())
    assert receipt["diagnostic"]["truncated"] is True
    assert receipt["runtime_host"]["docker_client"]["version"] == "28.0.4"
    assert receipt["image_id"] == "sha256:" + "c" * 64
    assert receipt["shard_index"] == 0


def test_diagnostic_metadata_failure_retains_bounded_visible_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    source.write_bytes(b"small")
    destination = tmp_path / "diagnostic.log"
    metadata = tmp_path / "diagnostic.receipt.json"
    runtime_manifest = tmp_path / "runtime.json"
    runtime_manifest.write_bytes(b"{}\n")
    host = tmp_path / "host.json"
    host.write_bytes(host_capture.canonical_json_bytes(runtime_host()))
    for key, value in {
        "GITHUB_REPOSITORY": GITHUB["repository"],
        "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_RUN_ID": "42",
        "GITHUB_SHA": GITHUB["sha"],
        "GITHUB_WORKFLOW_REF": GITHUB["workflow_ref"],
    }.items():
        monkeypatch.setenv(key, value)
    real_open = diagnostic.os.open

    def fail_metadata(path: object, *args: object, **kwargs: object) -> int:
        if Path(path) == metadata:
            raise OSError("fixture")
        return real_open(path, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(diagnostic.os, "open", fail_metadata)
    with pytest.raises(OSError):
        diagnostic.publish(
            source,
            destination,
            metadata,
            64,
            phase="fixture",
            row_id="repo__task-1",
            image_ref="image@sha256:" + "b" * 64,
            image_id="sha256:" + "c" * 64,
            shard_index=0,
            exit_code=125,
            argv_sha256="d" * 64,
            runtime_manifest=runtime_manifest,
            runtime_host_receipt=host,
        )
    assert destination.read_bytes() == b"small"
    assert not metadata.exists()
    assert source.exists()


def test_output_directories_reject_symlinks_broken_links_and_existing_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "real").mkdir()
    (tmp_path / "linked").symlink_to(tmp_path / "real", target_is_directory=True)
    with pytest.raises(output_directory.OutputDirectoryError):
        output_directory.prepare(Path("linked/evidence"), require_new=False)
    (tmp_path / "broken").symlink_to(tmp_path / "absent", target_is_directory=True)
    with pytest.raises(output_directory.OutputDirectoryError):
        output_directory.prepare(Path("broken/evidence"), require_new=False)
    output_directory.prepare(Path("safe/evidence"), require_new=True)
    assert (tmp_path / "safe/evidence").is_dir()
    with pytest.raises(output_directory.OutputDirectoryError, match="already exists"):
        output_directory.prepare(Path("safe/evidence"), require_new=True)
    (tmp_path / "safe/evidence/occupied").write_text("x")
    with pytest.raises(output_directory.OutputDirectoryError, match="not empty"):
        output_directory.prepare(Path("safe/evidence"), require_new=False)


def test_smoke_argv_digest_matches_the_exact_runner_tuple() -> None:
    image_ref = "image@sha256:" + "b" * 64
    args = [
        "--network", "none", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges=true", "--pids-limit", "1024",
        "--memory", "10g", "--cpus", "4", "--log-driver", "local",
        "--log-opt", "max-size=3m", "--log-opt", "max-file=1",
        "--log-opt", "compress=false",
    ]
    command = [
        "bash", "--noprofile", "--norc", "-c",
        'printf "%s\\n" TELOS_ITER206_LOG_DRIVER_SMOKE_OK',
    ]
    runner_argv = [
        "docker", "run", "--rm", *args, "--entrypoint", "bash", image_ref,
        *command[1:],
    ]
    manual = hashlib.sha256()
    for value in runner_argv:
        manual.update(value.encode())
        manual.update(b"\0")
    assert collection._argv_sha256(runner_argv) == manual.hexdigest()
    assert collection._argv_sha256(runner_argv) != collection._argv_sha256(
        [*runner_argv[:-4], "bash", *runner_argv[-4:]]
    )


def test_smoke_validation_rejects_self_consistent_diagnostic_or_argv_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_manifest = tmp_path / "runtime.json"
    runtime_payload = b'{"fixture":true}\n'
    runtime_manifest.write_bytes(runtime_payload)
    row_id = "repo__task-1"
    image_id = "sha256:" + "c" * 64
    image_ref = "image@sha256:" + "b" * 64
    monkeypatch.setattr(
        collection._core,
        "source_lines",
        lambda **_kwargs: [
            f"{row_id}\timage:tag\tsha256:{'b' * 64}\t{image_id}\t{image_ref}\tno_safe_scenario"
        ],
    )
    safety_args = [
        "--network", "none", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges=true", "--pids-limit", "1024",
        "--memory", "10g", "--cpus", "4", "--log-driver", "local",
        "--log-opt", "max-size=3m", "--log-opt", "max-file=1",
        "--log-opt", "compress=false",
    ]
    command = [
        "bash", "--noprofile", "--norc", "-c",
        'printf "%s\\n" TELOS_ITER206_LOG_DRIVER_SMOKE_OK',
    ]
    argv_digest = collection._argv_sha256(
        [
            "docker", "run", "--rm", *safety_args, "--entrypoint", "bash",
            image_ref, *command[1:],
        ]
    )
    stdout = b"TELOS_ITER206_LOG_DRIVER_SMOKE_OK\n"
    envelope = (
        b"TELOS_ITER206_SEPARATE_STREAMS_V1\n"
        + f"STDOUT_BYTES={len(stdout)}\nSTDERR_BYTES=0\n".encode()
        + b">>>>> STDOUT\n"
        + stdout
        + b">>>>> STDERR\n"
    )
    diagnostic_path = tmp_path / "smoke.diagnostic.log"
    metadata_path = tmp_path / "smoke.diagnostic.receipt.json"
    receipt_path = tmp_path / "smoke.receipt.json"
    diagnostic_path.write_bytes(envelope)
    metadata = {
        "argv_sha256": argv_digest,
        "diagnostic": {
            "bytes": len(envelope),
            "path": diagnostic_path.name,
            "sha256": hashlib.sha256(envelope).hexdigest(),
            "source_bytes": len(envelope),
            "truncated": False,
        },
        "exit_code": 0,
        "github": GITHUB,
        "image_id": image_id,
        "image_ref": image_ref,
        "phase": "global_no_science_log_driver_smoke",
        "row_id": row_id,
        "runtime_host": runtime_host(),
        "runtime_manifest_sha256": hashlib.sha256(runtime_payload).hexdigest(),
        "schema_version": diagnostic.SCHEMA,
        "shard_index": -1,
    }

    def write_metadata() -> bytes:
        payload = (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode()
        metadata_path.write_bytes(payload)
        return payload

    metadata_payload = write_metadata()
    receipt = {
        "argument_vector_sha256": argv_digest,
        "command": command,
        "diagnostic": {
            "bytes": len(envelope),
            "path": diagnostic_path.name,
            "receipt_sha256": hashlib.sha256(metadata_payload).hexdigest(),
            "sha256": hashlib.sha256(envelope).hexdigest(),
        },
        "docker_safety_args": safety_args,
        "exit_code": 0,
        "github": GITHUB,
        "image_id": image_id,
        "image_ref": image_ref,
        "ordinal": 0,
        "output_exact": True,
        "row_id": row_id,
        "runtime_host": runtime_host(),
        "runtime_manifest_sha256": hashlib.sha256(runtime_payload).hexdigest(),
        "schema_version": "telos.iter206.no_science_smoke_receipt.v1",
        "status": "pass",
        "streams": {
            "stderr": {"bytes": 0, "sha256": hashlib.sha256(b"").hexdigest()},
            "stdout": {"bytes": len(stdout), "sha256": hashlib.sha256(stdout).hexdigest()},
        },
    }
    receipt_path.write_text("fixture")
    assert collection._validate_smoke_gate(
        receipt,
        GITHUB,
        runtime_manifest=runtime_manifest,
        verify_siblings=True,
        receipt_path=receipt_path,
    ) == receipt

    with pytest.raises(collection.ExecutionCollectionError, match="exact contract|malformed"):
        collection._validate_smoke_gate(
            {**receipt, "argument_vector_sha256": "0" * 64},
            GITHUB,
            runtime_manifest=runtime_manifest,
        )

    tampered = b"TELOS_ITER206_SEPARATE_STREAMS_V1\nself-consistent-but-false\n"
    diagnostic_path.write_bytes(tampered)
    metadata["diagnostic"] = {
        **metadata["diagnostic"],
        "bytes": len(tampered),
        "sha256": hashlib.sha256(tampered).hexdigest(),
        "source_bytes": len(tampered),
    }
    tampered_metadata = write_metadata()
    tampered_receipt = json.loads(json.dumps(receipt))
    tampered_receipt["diagnostic"].update(
        {
            "bytes": len(tampered),
            "sha256": hashlib.sha256(tampered).hexdigest(),
            "receipt_sha256": hashlib.sha256(tampered_metadata).hexdigest(),
        }
    )
    with pytest.raises(collection.ExecutionCollectionError, match="malformed|differs"):
        collection._validate_smoke_gate(
            tampered_receipt,
            GITHUB,
            runtime_manifest=runtime_manifest,
            verify_siblings=True,
            receipt_path=receipt_path,
        )


def test_iter206_adjudicator_validates_actual_iter203_bridge_under_upstream_identity() -> None:
    inventory = adjudicator.load_json_strict(adjudicator._core.INVENTORY)
    disposition = adjudicator.load_json_strict(adjudicator._core.DISPOSITION)
    safe_index = adjudicator.load_json_strict(adjudicator._core.SAFE_INDEX)
    adjudicator.validate_inventory(inventory)
    dispositions = adjudicator.validate_disposition(disposition)
    assert len(adjudicator.safe_index_ids(safe_index, dispositions)) == 29
    assert adjudicator._core.EXPERIMENT_ID == adjudicator.EXPERIMENT_ID


def test_iter206_blind_audit_versions_the_recovery_component_without_relabeling_pool() -> None:
    rows = [
        {
            "certified_resolved": False,
            "instance_id": f"repo__task-{index}",
            "prior_outcome_exposed": index < 27,
            "prior_provider_call_ledger": index < 10,
            "status": "not_certified",
        }
        for index in range(50)
    ]
    audit = blind_judge.build_audit(
        {"rows": rows},
        [],
        {
            "iter200_corrected_audit_sha256": (
                blind_judge._core.ITER200_CORRECTED_AUDIT_SHA256
            )
        },
    )
    pooled = audit["pooled_corrected_iter200_plus_iter202_cohort"]
    assert audit["experiment_id"] == adjudicator.EXPERIMENT_ID
    assert "iter206" in pooled["attempts"] and "iter203" not in pooled["attempts"]
    assert "iter202_fixed_outputs_via_iter206_admission_history_recovery" in pooled[
        "components"
    ]


def test_smoke_receipt_is_bound_into_every_shard_and_aggregate() -> None:
    text = collection.Path(collection.__file__).read_text() if hasattr(collection, "Path") else COLLECTOR_TEXT
    assert '"runtime_host", "smoke_gate"' in text
    assert 'document["smoke_gate"] = smoke_gates[0]' in text
    assert "shards bind different iter206 smoke receipts" in text


COLLECTOR_TEXT = (ROOT / "scripts/collect_iter206_execution.py").read_text()


def test_additive_downstream_never_masquerades_as_iter203_execution() -> None:
    adjudicator = (ROOT / "scripts/adjudicate_iter206_admission_history_recovery.py").read_text()
    judge = (
        ROOT / "scripts/run_iter206_admission_history_recovery_blind_judge.py"
    ).read_text()
    assert 'EXPERIMENT_ID = "iter206_iter205_admission_history_recovery"' in adjudicator
    assert "_telos_iter206_execution_complete.receipt.json" in adjudicator
    assert "iter202_fixed_outputs_via_iter206_admission_history_recovery" in judge


def test_runtime_manifest_chain_of_custody_matches_iter206_collector_and_workflow() -> None:
    protocol = runtime.build_manifest()["protocol"]
    chain = protocol["execution_chain_of_custody"]
    assert chain == {
        "aggregate_receipt_name": collection.AGGREGATE_RECEIPT_NAME,
        "aggregate_receipt_schema": collection.AGGREGATE_SCHEMA,
        "collector_eligible_artifacts": (
            "successful_shards_from_one_github_run_and_attempt_only"
        ),
        "exact_log_set": "gold_and_variant_pair_for_each_of_50_spec_rows",
        "shard_receipt_name_pattern": runtime.ITER206_SHARD_RECEIPT_NAME_PATTERN,
        "shard_receipt_schema": collection.SHARD_SCHEMA,
        "verified_snapshot_api": (
            "scripts.collect_iter206_execution.check_execution_bundle_with_logs"
        ),
    }
    assert runtime.ITER206_AGGREGATE_RECEIPT_NAME == collection.AGGREGATE_RECEIPT_NAME
    assert runtime.ITER206_AGGREGATE_RECEIPT_SCHEMA == collection.AGGREGATE_SCHEMA
    assert runtime.ITER206_SHARD_RECEIPT_SCHEMA == collection.SHARD_SCHEMA
    for shard_index in range(8):
        assert runtime.ITER206_SHARD_RECEIPT_NAME_PATTERN.format(
            shard_index=shard_index
        ) == collection.shard_receipt_name(shard_index)

    workflow = (ROOT / ".github/workflows/iter206-execute.yml").read_text()
    aggregate_path = (
        "experiments/iter206_iter205_admission_history_recovery/proof/raw/execution/"
        f"{collection.AGGREGATE_RECEIPT_NAME}"
    )
    assert workflow.count(f"--aggregate-receipt {aggregate_path}") == 2
    assert (
        "name: iter206-execution-complete-${{ github.run_id }}-attempt-1"
        in workflow
    )
    assert "iter203" not in json.dumps(chain, sort_keys=True)
    assert "iter204" not in json.dumps(chain, sort_keys=True)
    recovery = protocol["admission_history_recovery"]
    assert recovery["allowed_delta"] == [
        "mechanical_iter205_to_separately_versioned_iter206_identities",
        (
            "add_exact_iter205_pre_dispatch_admission_null_"
            "evidence_and_guard"
        ),
        (
            "replace_only_the_iter205_exact_two_history_predicate_"
            "with_the_iter206_exact_six_publication_aware_predicate"
        ),
        (
            "bind_exact_iter205_active_workflow_object_and_empty_"
            "all_event_and_dispatch_histories"
        ),
    ]
    assert recovery["iter204_admission_snapshot"] == {
        "baseline_push_parse_failure_run_ids": [
            29465584664,
            29465924803,
            29468669956,
            29468768706,
        ],
        "canonical_sha256": (
            "SHA-256_of_UTF-8_JSON_sort_keys_true_"
            "separators_comma_colon_allow_nan_false"
        ),
        "dispatch_run_count": 0,
        "expected_push_parse_failure_count": 6,
        "future_primary_run": (
            "structurally_discovered_run_number_6_bound_to_approved_merge"
        ),
        "future_release_run": (
            "structurally_discovered_run_number_5_bound_to_merge_parent_2"
        ),
        "run_numbers": [1, 2, 3, 4, 5, 6],
        "temporal_scope": "authorization_time_snapshot_not_a_permanent_live_history_claim",
        "workflow_id": 314113289,
    }


def test_runtime_manifest_and_current_publication_receipt_reproduce() -> None:
    assert runtime.validate_committed_manifest() == []
    assert publication.validate_frozen_iter205_receipt()["scanned_file_count"] == 397
    expected = publication.canonical_json_bytes(publication.build_audit())
    assert publication.AUDIT.read_bytes() == expected
    assert contract.validate_all() == []


def test_runtime_manifest_covers_recursive_learning_guard_imports() -> None:
    document = runtime.build_manifest()

    assert runtime.local_python_import_gaps(document["files"]) == []
    required_package_closure = {
        "telos/agent_behavior_slice.py",
        "telos/public_slice.py",
        "telos/scorecard.py",
        "telos/survey.py",
    }
    paths = {record["path"] for record in document["files"]}
    assert required_package_closure.issubset(paths)

    for missing in required_package_closure:
        reduced = [record for record in document["files"] if record["path"] != missing]
        assert any(
            dependency == missing
            for _source, dependency in runtime.local_python_import_gaps(reduced)
        )
