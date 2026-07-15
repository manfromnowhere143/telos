from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def image_lock_module():
    return load_script("build_iter202_image_lock.py")


@pytest.fixture
def safety_module():
    return load_script("validate_iter202_scenario_safety.py")


def synthetic_lock(module, target_raw: bytes) -> dict:
    ids = module._target_ids(target_raw)

    def digest(label: str) -> str:
        return "sha256:" + hashlib.sha256(label.encode()).hexdigest()

    images = []
    for iid in ids:
        repository = module.image_repository(iid)
        manifest_digest = digest("manifest:" + iid)
        images.append(
            {
                "instance_id": iid,
                "tag": module.image_tag(iid),
                "tag_manifest_digest": digest("tag:" + iid),
                "manifest_digest": manifest_digest,
                "manifest_media_type": (
                    "application/vnd.docker.distribution.manifest.v2+json"
                ),
                "image_id": digest("config:" + iid),
                "reference": f"{repository}@{manifest_digest}",
            }
        )
    return {
        "schema_version": module.SCHEMA,
        "source_targets": {
            "path": str(module.TARGETS.relative_to(module.ROOT)),
            "sha256": module.sha256(target_raw),
            "schema_version": module.TARGET_SCHEMA,
            "count": len(ids),
            "ordered_instance_ids_sha256": module.ordered_ids_sha256(ids),
        },
        "registry": {
            "host": module.REGISTRY,
            "namespace": module.NAMESPACE,
            "tag": module.TAG_NAME,
            "platform": "linux/amd64",
            "resolution_protocol": "docker-registry-http-api-v2-read-only",
        },
        "count": len(images),
        "images": images,
    }


def test_image_lock_binds_all_53_targets_offline(image_lock_module) -> None:
    raw = image_lock_module.TARGETS.read_bytes()
    lock = synthetic_lock(image_lock_module, raw)

    assert image_lock_module.validate_lock(lock, raw) == []
    assert len(lock["images"]) == 53
    assert [row["instance_id"] for row in lock["images"]] == image_lock_module._target_ids(raw)


@pytest.mark.parametrize("mutation", ["digest", "order", "reference", "extra"])
def test_image_lock_rejects_digest_order_reference_and_extra_fields(
    image_lock_module, mutation: str
) -> None:
    raw = image_lock_module.TARGETS.read_bytes()
    lock = synthetic_lock(image_lock_module, raw)
    if mutation == "digest":
        lock["images"][0]["manifest_digest"] = "UNAVAILABLE"
    elif mutation == "order":
        lock["images"][0], lock["images"][1] = lock["images"][1], lock["images"][0]
    elif mutation == "reference":
        lock["images"][0]["reference"] = "swebench/example@sha256:" + "0" * 64
    else:
        lock["images"][0]["unregistered"] = True

    assert image_lock_module.validate_lock(lock, raw)


def test_image_lock_rejects_source_byte_drift(image_lock_module) -> None:
    raw = image_lock_module.TARGETS.read_bytes()
    lock = synthetic_lock(image_lock_module, raw)
    changed = json.loads(raw)
    changed["targets"][0]["repo"] += "-drift"
    changed_raw = (json.dumps(changed, indent=2) + "\n").encode()

    assert "image lock source_targets binding mismatch" in image_lock_module.validate_lock(
        lock, changed_raw
    )


def test_image_lock_json_loader_rejects_duplicates_and_nonfinite_numbers(
    image_lock_module,
) -> None:
    with pytest.raises(image_lock_module.LockError, match="duplicate JSON key"):
        image_lock_module.load_json_strict(b'{"x": 1, "x": 2}', "mutation")
    with pytest.raises(image_lock_module.LockError, match="non-standard JSON"):
        image_lock_module.load_json_strict(b'{"x": NaN}', "mutation")


def test_committed_image_lock_is_strict_and_offline_valid(image_lock_module) -> None:
    assert image_lock_module.validate_committed_lock_bytes(
        image_lock_module.OUT.read_bytes(), image_lock_module.TARGETS.read_bytes()
    ) == []


def test_committed_image_lock_aggregate_digest_rejects_valid_digest_mutation(
    image_lock_module,
) -> None:
    raw = image_lock_module.OUT.read_bytes()
    lock = image_lock_module.load_json_strict(raw, "iter202 image lock")
    lock["images"][0]["manifest_digest"] = "sha256:" + "0" * 64
    lock["images"][0]["reference"] = (
        image_lock_module.image_repository(lock["images"][0]["instance_id"])
        + "@sha256:"
        + "0" * 64
    )
    changed = image_lock_module.render(lock)

    assert "committed iter202 image lock aggregate sha256 mismatch" in (
        image_lock_module.validate_committed_lock_bytes(
            changed, image_lock_module.TARGETS.read_bytes()
        )
    )


@pytest.mark.parametrize(
    "source,needle",
    [
        ('import os\nprint("RESULT=x")', "unsafe import root: os"),
        ('import socket\nprint("RESULT=x")', "unsafe import root: socket"),
        ('exec("print(1)")\nprint("RESULT=x")', "unsafe dynamic/builtin call: exec"),
        ('open("probe", "w")\nprint("RESULT=x")', "unsafe dynamic/builtin call: open"),
        ('print("RESULT=../escape")', "parent-traversal path literal is forbidden"),
        ('import importlib\nprint("RESULT=x")', "unsafe import root: importlib"),
        (
            "from _pytest.capture import os\n"
            "print('RESULT=' + str(os.listdir(chr(46))))",
            "unsafe import root: _pytest",
        ),
        (
            "from _pytest.pytester import subprocess\n"
            "print('RESULT=' + str(subprocess.run(['id'], capture_output=True).returncode))",
            "unsafe imported member or alias: subprocess",
        ),
        ('from collections import os\nprint("RESULT=x")', "unsafe imported member or alias: os"),
    ],
)
def test_scenario_ast_rejects_network_process_filesystem_and_dynamic_execution(
    safety_module, source: str, needle: str
) -> None:
    assert any(needle in error for error in safety_module.scenario_ast_errors(source))


def write_target_fixture(path: Path) -> None:
    path.write_bytes(
        (
            ROOT
            / "experiments/iter202_natural_rate_scaled/proof/raw/solve_targets.json"
        ).read_bytes()
    )


def write_valid_scenario_state(safety_module, root: Path) -> tuple[Path, Path, Path]:
    target_path = root / "solve_targets.json"
    scenario_dir = root / "scenarios"
    scenario_dir.mkdir()
    write_target_fixture(target_path)
    iid, repo = next(
        iter(
            (
                (row["instance_id"], row["repo"])
                for row in json.loads(target_path.read_text())["targets"]
            )
        )
    )
    source = 'print("RESULT=ok")'
    digest = hashlib.sha256(source.encode()).hexdigest()
    scenario_path = scenario_dir / f"{iid}.scenario.py"
    scenario_path.write_text(source + "\n")
    summary = {
        "checkpoint_schema": {
            "finished": "telos.iter202.provider_attempt.finished.v2",
            "started": "telos.iter202.provider_attempt.started.v2",
        },
        "differing_solutions": 1,
        "estimated_spend_usd": 0.3,
        "manifest": [
            {
                "func": "probe",
                "instance_id": iid,
                "provider_attempt_id": "1" * 32,
                "provider_response_sha256": "2" * 64,
                "provider_usage": {},
                "repo": repo,
                "scenario_sha256": digest,
                "status": "scenario",
            }
        ],
        "model": safety_module.FROZEN_MODEL,
        "provider_calls": 1,
        "scenarios": 1,
        "schema_version": safety_module.SUMMARY_SCHEMA,
    }
    summary_path = scenario_dir / "scenarios_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return target_path, scenario_dir, scenario_path


def test_scenario_state_accepts_explicit_empty_pre_provider_state(
    safety_module, tmp_path: Path
) -> None:
    targets = tmp_path / "solve_targets.json"
    write_target_fixture(targets)
    status, errors = safety_module.scenario_state_errors(targets, tmp_path / "scenarios")
    assert (status, errors) == ("no-scenarios-yet", [])


def test_scenario_state_binds_summary_hash_and_rejects_drift(
    safety_module, tmp_path: Path
) -> None:
    targets, scenarios, scenario = write_valid_scenario_state(safety_module, tmp_path)
    assert safety_module.scenario_state_errors(targets, scenarios) == ("valid", [])

    scenario.write_text('print("RESULT=changed")\n')
    status, errors = safety_module.scenario_state_errors(targets, scenarios)
    assert status == "invalid"
    assert any("scenario summary hash mismatch" in error for error in errors)


def test_scenario_state_rejects_unindexed_extra_script(
    safety_module, tmp_path: Path
) -> None:
    targets, scenarios, _ = write_valid_scenario_state(safety_module, tmp_path)
    (scenarios / "unindexed__escape-1.scenario.py").write_text('print("RESULT=x")\n')

    status, errors = safety_module.scenario_state_errors(targets, scenarios)
    assert status == "invalid"
    assert any("scenario file set mismatch" in error for error in errors)


def test_scenario_state_rejects_malformed_extra_python_file(
    safety_module, tmp_path: Path
) -> None:
    targets, scenarios, _ = write_valid_scenario_state(safety_module, tmp_path)
    (scenarios / "escape.py").write_text('print("RESULT=x")\n')

    status, errors = safety_module.scenario_state_errors(targets, scenarios)
    assert status == "invalid"
    assert any("scenario file set mismatch" in error for error in errors)


def test_runner_contract_rejects_mutated_safety_flag(safety_module) -> None:
    text = safety_module.RUNNER.read_text()
    assert safety_module.runner_safety_errors(text) == []

    weakened = text.replace("--network none", "--network bridge", 1)
    assert "runner Docker safety argument set is incomplete or changed" in (
        safety_module.runner_safety_errors(weakened)
    )


def test_runner_contract_requires_complete_runtime_freeze_self_gate(safety_module) -> None:
    text = safety_module.RUNNER.read_text()
    command = "python3 scripts/validate_iter202_runtime_freeze.py --check"
    assert safety_module.runner_safety_errors(text) == []
    assert "complete runtime guards in order" in "\n".join(
        safety_module.runner_safety_errors(text.replace(command, "true", 1))
    )


def test_runner_contract_rejects_mutated_resource_limit(safety_module) -> None:
    text = safety_module.RUNNER.read_text()
    weakened = text.replace(
        "ITER202_CERT_TIMEOUT_SECONDS=900", "ITER202_CERT_TIMEOUT_SECONDS=901", 1
    )
    assert (
        "runner iter202 resource limit changed or duplicated: "
        "ITER202_CERT_TIMEOUT_SECONDS"
    ) in safety_module.runner_safety_errors(weakened)


def shell_function(safety_module, name: str) -> str:
    matches = re.findall(
        rf"^{re.escape(name)}\(\) \{{\n.*?^\}}$",
        safety_module.RUNNER.read_text(),
        flags=re.DOTALL | re.MULTILINE,
    )
    assert len(matches) == 1
    return matches[0]


def shard_partition(
    safety_module, *, index: int, count: int, total: int = 53
) -> list[int]:
    script = "\n".join(
        [
            shell_function(safety_module, "shard_member"),
            f"SHARD_INDEX={index}",
            f"SHARD_COUNT={count}",
            f"for (( ordinal=0; ordinal<{total}; ordinal++ )); do",
            '  if shard_member "$ordinal"; then printf "%s\\n" "$ordinal"; fi',
            "done",
        ]
    )
    completed = subprocess.run(
        ["bash", "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )
    return [int(value) for value in completed.stdout.splitlines()]


def test_eight_shards_cover_every_possible_valid_solution_row_once(
    safety_module,
) -> None:
    # Fifty-three is the frozen solve-target count and therefore the strict
    # upper bound on the ordered valid-solution/spec index being partitioned.
    partitions = [
        shard_partition(safety_module, index=index, count=8) for index in range(8)
    ]
    flattened = [ordinal for partition in partitions for ordinal in partition]
    assert sorted(flattened) == list(range(53))
    assert len(flattened) == len(set(flattened)) == 53
    assert [len(partition) for partition in partitions] == [7, 7, 7, 7, 7, 6, 6, 6]
    max_rows = max(map(len, partitions))
    certification_seconds = int(
        safety_module.REQUIRED_EXECUTION_LIMITS["ITER202_CERT_TIMEOUT_SECONDS"]
    )
    scenario_seconds = int(
        safety_module.REQUIRED_EXECUTION_LIMITS["ITER202_SCENARIO_TIMEOUT_SECONDS"]
    )
    kill_grace_seconds = int(
        safety_module.REQUIRED_EXECUTION_LIMITS["ITER202_KILL_GRACE_SECONDS"]
    )
    nominal_threshold_seconds = max_rows * (
        certification_seconds + 2 * scenario_seconds
    )
    possible_kill_grace_seconds = max_rows * 3 * kill_grace_seconds
    assert nominal_threshold_seconds == 147 * 60
    assert possible_kill_grace_seconds == 210  # 3.5 minutes
    assert nominal_threshold_seconds + possible_kill_grace_seconds == 9_030


def test_sharding_allows_a_deterministic_empty_partition(safety_module) -> None:
    assert shard_partition(safety_module, index=63, count=64) == []


@pytest.mark.parametrize(
    "index,count",
    [
        ("", "8"),
        ("00", "8"),
        ("-1", "8"),
        ("8", "8"),
        ("0", "0"),
        ("0", "08"),
        ("0", "257"),
        ("x", "8"),
    ],
)
def test_shard_config_rejects_noncanonical_or_out_of_range_values(
    safety_module, index: str, count: str
) -> None:
    script = shell_function(safety_module, "validate_shard_config")
    completed = subprocess.run(
        ["bash", "-c", script + '\nvalidate_shard_config "$1" "$2"', "--", index, count],
        check=False,
    )
    assert completed.returncode != 0


@pytest.mark.parametrize("index,count", [("0", "1"), ("7", "8"), ("255", "256")])
def test_shard_config_accepts_canonical_in_range_values(
    safety_module, index: str, count: str
) -> None:
    script = shell_function(safety_module, "validate_shard_config")
    completed = subprocess.run(
        ["bash", "-c", script + '\nvalidate_shard_config "$1" "$2"', "--", index, count],
        check=False,
    )
    assert completed.returncode == 0


def experiment_shard_config_result(
    safety_module, experiment: str, index: str, count: str
) -> subprocess.CompletedProcess[str]:
    script = "\n".join(
        (
            f'ITER202_EXP="{safety_module.EXP.name}"',
            shell_function(safety_module, "validate_shard_config"),
            shell_function(safety_module, "validate_experiment_shard_config"),
        )
    )
    return subprocess.run(
        [
            "bash",
            "-c",
            script + '\nvalidate_experiment_shard_config "$1" "$2" "$3"',
            "--",
            experiment,
            index,
            count,
        ],
        check=False,
    )


@pytest.mark.parametrize("index,count", [("0", "1"), ("0", "64"), ("8", "8")])
def test_iter202_runner_rejects_any_config_other_than_one_of_eight_shards(
    safety_module, index: str, count: str
) -> None:
    completed = experiment_shard_config_result(
        safety_module, safety_module.EXP.name, index, count
    )
    assert completed.returncode != 0


@pytest.mark.parametrize("index", ["0", "7"])
def test_iter202_runner_accepts_exactly_eight_shards(
    safety_module, index: str
) -> None:
    completed = experiment_shard_config_result(
        safety_module, safety_module.EXP.name, index, "8"
    )
    assert completed.returncode == 0


def test_runner_preserves_unsharded_legacy_defaults(safety_module) -> None:
    text = safety_module.RUNNER.read_text()
    assert 'SHARD_INDEX_RAW="${TELOS_NAT_SHARD_INDEX-0}"' in text
    assert 'SHARD_COUNT_RAW="${TELOS_NAT_SHARD_COUNT-1}"' in text
    completed = experiment_shard_config_result(
        safety_module, "iter200_natural_certified_yet_wrong_rate", "0", "1"
    )
    assert completed.returncode == 0


def bounded_function(safety_module) -> str:
    matches = re.findall(
        r"run_bounded\(\) \{\n.*?\n\}",
        safety_module.RUNNER.read_text(),
        flags=re.DOTALL,
    )
    assert len(matches) == 2
    assert matches[0] == matches[1]
    return matches[0]


def run_bounded_probe(safety_module, invocation: str) -> subprocess.CompletedProcess[str]:
    script = (
        bounded_function(safety_module)
        + "\npython() { python3 \"$@\"; }\nTELOS_KILL_GRACE_SECONDS=1\n"
        + invocation
        + "\nrc=$?\nprintf '\\nWRAPPER_RC=%s\\n' \"$rc\"\n"
    )
    return subprocess.run(
        ["bash", "-c", script],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )


def test_bounded_wrapper_preserves_command_pipestatus(safety_module) -> None:
    completed = run_bounded_probe(
        safety_module,
        "run_bounded 3 1024 bash -c 'printf payload; exit 7'",
    )
    assert completed.stdout == "payload\nWRAPPER_RC=7\n"


def test_bounded_wrapper_caps_output_and_fails_closed(safety_module) -> None:
    completed = run_bounded_probe(
        safety_module,
        'run_bounded 3 32 python3 -c \'import sys;sys.stdout.write("x"*64)\'',
    )
    assert completed.stdout.startswith("x" * 32)
    assert "TELOS_OUTPUT_TRUNCATED limit_bytes=32" in completed.stdout
    assert "SETUP_FAIL output_limit limit_bytes=32" in completed.stdout
    assert completed.stdout.endswith("WRAPPER_RC=125\n")


def test_bounded_wrapper_times_out_and_preserves_timeout_status(safety_module) -> None:
    completed = run_bounded_probe(
        safety_module,
        "run_bounded 1 1024 bash -c 'sleep 4'",
    )
    assert completed.stdout == "\nWRAPPER_RC=124\n"


def test_runner_applies_safety_args_to_both_variant_and_gold(safety_module) -> None:
    text = safety_module.RUNNER.read_text()
    assert text.count('"${DOCKER_SAFETY_ARGS[@]}" \\') == 2
    assert safety_module.runner_safety_errors(text) == []
    subprocess.run(["bash", "-n", str(safety_module.RUNNER)], check=True)


def test_workflow_guards_precede_execution(safety_module) -> None:
    text = safety_module.WORKFLOW.read_text()
    assert safety_module.workflow_safety_errors(text) == []
    weakened = text.replace(
        "python3 scripts/build_iter202_image_lock.py --check",
        "python3 scripts/build_iter202_image_lock.py --resolve",
    )
    assert safety_module.workflow_safety_errors(weakened)


def test_workflow_requires_all_eight_unique_shards(safety_module) -> None:
    text = safety_module.WORKFLOW.read_text()
    assert safety_module.workflow_safety_errors(text) == []
    assert safety_module.workflow_safety_errors(
        text.replace("shard: [0, 1, 2, 3, 4, 5, 6, 7]", "shard: [0, 1, 2, 3]", 1)
    )
    assert safety_module.workflow_safety_errors(
        text.replace(
            "iter202-execution-run-${{ github.run_id }}-attempt-${{ github.run_attempt }}-shard-${{ matrix.shard }}-of-8",
            "iter202-execution",
            1,
        )
    )


def test_runner_generates_bound_receipt_only_after_successful_reconciliation(
    safety_module,
) -> None:
    text = safety_module.RUNNER.read_text()
    failure_gate = text.index('if [ "$failures" -ne 0 ]; then')
    receipt = text.index("python3 scripts/collect_iter202_execution.py shard-receipt")
    completion = text.index(
        'echo "=== natural-rate execution logs complete for shard '
    )
    assert failure_gate < receipt < completion
    assert safety_module.runner_safety_errors(text) == []
    assert safety_module.runner_safety_errors(
        text.replace(
            "python3 scripts/collect_iter202_execution.py shard-receipt",
            "python3 scripts/collect_iter202_execution.py unchecked-receipt",
            1,
        )
    )


def test_workflow_separates_partial_debug_from_collector_eligible_artifacts(
    safety_module,
) -> None:
    text = safety_module.WORKFLOW.read_text()
    assert safety_module.workflow_safety_errors(text) == []
    assert (
        "pattern: iter202-execution-run-${{ github.run_id }}-attempt-"
        "${{ github.run_attempt }}-shard-*-of-8"
    ) in text
    assert (
        "iter202-execution-debug-${{ github.run_id }}-attempt-"
        "${{ github.run_attempt }}-shard-${{ matrix.shard }}-of-8"
    ) in text
    assert safety_module.workflow_safety_errors(
        text.replace("merge-multiple: false", "merge-multiple: true", 1)
    )
    assert safety_module.workflow_safety_errors(
        text.replace(
            "--runtime-manifest experiments/iter202_natural_rate_scaled/proof/raw/"
            "runtime_manifest.json",
            "--runtime-manifest unbound.json",
            1,
        )
    )
    assert safety_module.workflow_safety_errors(
        text.replace(
            "- name: Upload verified shard evidence\n        if: success()",
            "- name: Upload verified shard evidence\n        if: always()",
            1,
        )
    )
    assert safety_module.workflow_safety_errors(
        text.replace(
            "- name: Upload partial shard evidence for debugging only\n"
            "        if: failure()",
            "- name: Upload partial shard evidence for debugging only\n"
            "        if: success()",
            1,
        )
    )
