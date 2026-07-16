#!/usr/bin/env python3
"""Fail closed on drift in the iter206 admission-history recovery contract."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import re
import subprocess
import sys
import textwrap


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RUNNER = ROOT / "scripts/ci_iter206_execute.sh"
SMOKE = ROOT / "scripts/ci_iter206_smoke.sh"
WORKFLOW = ROOT / ".github/workflows/iter206-execute.yml"
COLLECTOR = ROOT / "scripts/collect_iter206_execution.py"
DIAGNOSTIC = ROOT / "scripts/publish_iter206_runtime_diagnostic.py"
HOST = ROOT / "scripts/capture_iter206_runtime_host.py"
OUTPUT_DIRECTORY = ROOT / "scripts/prepare_iter206_output_directory.py"

FROZEN_ITER205 = {
    ".github/workflows/iter205-execute.yml": (
        "0bbc39c8b4abbe6ae7dcbd4f9dc5710f835ff06522d8c137b622a9ad6a5a0ad5"
    ),
    "experiments/iter205_iter204_workflow_context_recovery/HYPOTHESIS.md": (
        "2b00f43f581176eaf4e134c7e3e3b2a9981f0767545a1f1b21397458bb215395"
    ),
    "experiments/iter205_iter204_workflow_context_recovery/proof/raw/runtime_manifest.json": (
        "1d427fd8e778282127ee8d782c6eb6bb8d6d44e781edceb50ad078474968b04a"
    ),
    "experiments/iter205_iter204_workflow_context_recovery/proof/pre_execution_publication_safety.json": (
        "1ba7adbea2fb6cf12488e8cf9a3438daadd22809d3d9944ae331bc031587d7da"
    ),
    "scripts/ci_iter205_execute.sh": (
        "6d71debfc16947b12973906e261fb59762d9ad5c2e8fb097c01614de69a73634"
    ),
    "scripts/ci_iter205_smoke.sh": (
        "7bbfa72d05ef53f21054ba4a928a37822bdefc0530ab78cd4fd679a9d2160514"
    ),
    "scripts/collect_iter205_execution.py": (
        "62d31ff95554e16eb641b73f4219c0c3cbcc9dfe634c06696c6156d2d3eac39a"
    ),
    "scripts/capture_iter205_runtime_host.py": (
        "f9bd0f07fb9fdcdfe8d092466be1dc35190c8e50b088c7da1078bf800cb6740f"
    ),
    "scripts/prepare_iter205_output_directory.py": (
        "6bafac14dcbcf3e18a1adb5b4dbfaf739cd57e6172973fed2c0ff5feae429dbd"
    ),
    "scripts/publish_iter205_runtime_diagnostic.py": (
        "770be68fc9f5cdba5e408e8cc08e656a95e8554816f44675266649a5206c3eca"
    ),
    "scripts/adjudicate_iter205_workflow_context_recovery.py": (
        "0b75c8a5c4300cc111c2c25f28dad7ee7cfc461f4176e7c890fb866a0b96f2b8"
    ),
    "scripts/run_iter205_workflow_context_recovery_blind_judge.py": (
        "cd37263af9340a730fd3d4991781ebb6f93ed2f80f51af9374d6eb17f66b5357"
    ),
}

AUTHORIZATION_KEYS = {
    "approved_commit_sha",
    "current_run_attempt",
    "current_run_id",
    "iter204_admission_history_sha256",
    "iter204_dispatch_count",
    "iter204_primary_run_id",
    "iter204_release_run_id",
    "iter204_workflow_id",
    "iter205_all_event_count",
    "iter205_dispatch_count",
    "iter205_workflow_id",
    "iter206_workflow_id",
    "merge_first_parent",
    "merge_second_parent",
    "primary_ci_event",
    "primary_ci_head_branch",
    "primary_ci_run_attempt",
    "primary_ci_run_id",
    "primary_ci_workflow_path",
    "release_ci_head_sha",
    "release_ci_runs",
    "required_checks",
    "schema_version",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _array_body(text: str, name: str) -> str | None:
    match = re.search(rf"(?ms)^{re.escape(name)}=\(\n(?P<body>.*?)^\)", text)
    return match.group("body") if match else None


def validate_local_log_contract(text: str, *, label: str) -> list[str]:
    failures: list[str] = []
    body = _array_body(text, "DOCKER_SAFETY_ARGS")
    if body is None:
        return [f"{label}: missing DOCKER_SAFETY_ARGS array"]
    required = (
        "--log-driver local",
        "--log-opt max-size=3m",
        "--log-opt max-file=1",
        "--log-opt compress=false",
    )
    for option in required:
        if body.count(option) != 1:
            failures.append(f"{label}: logging option must occur exactly once: {option}")
    if (
        "--log-driver local" in body
        and "--log-opt max-file=1" in body
        and "--log-opt compress=false" not in body
    ):
        failures.append(
            f"{label}: incompatible local/max-file=1/default-compression triple returned"
        )
    return failures


def validate_runner_text(text: str) -> list[str]:
    failures = validate_local_log_contract(text, label="iter206 runner")
    required = (
        'EXP="experiments/iter206_iter205_admission_history_recovery"',
        'SOURCE_EXP="experiments/iter203_iter202_safety_recovery"',
        'LAUNCH_DIAGNOSTIC_LIMIT_BYTES=2162688',
        'ulimit -f "$((LAUNCH_DIAGNOSTIC_LIMIT_BYTES / 1024))"',
        'if [ "${GITHUB_RUN_ATTEMPT-}" != "1" ]',
        "scripts/build_iter206_runtime_manifest.py --check",
        "scripts/prepare_iter206_output_directory.py",
        "scripts/collect_iter206_execution.py smoke-check",
        "docker \"${create_args[@]}\"",
        '--entrypoint bash',
        '-v "$PWD/$SPECS/$stem.eval_script.sh:/specs/$stem.eval_script.sh:ro"',
        '-v "$PWD/$SPECS/$stem.spec.json:/specs/$stem.spec.json:ro"',
        '-v "$PWD/$SOLS/$stem.model.patch:/solutions/$stem.model.patch:ro"',
        '"scientific_container_launch_variant_cert"',
        '"scientific_container_launch_variant_behavior"',
        '"scientific_container_launch_gold_behavior"',
        '"incomplete_scientific_variant_evidence"',
        'scripts/publish_iter206_runtime_diagnostic.py',
        'scripts/collect_iter206_execution.py shard-receipt',
    )
    for fragment in required:
        if fragment not in text:
            failures.append(f"iter206 runner missing contract fragment: {fragment}")
    create_start = text.find("row_create_preflight()")
    create_end = text.find("marker_ordered()", create_start)
    create = text[create_start:create_end]
    if create_start < 0 or create_end < 0:
        failures.append("iter206 runner row-create preflight is not inspectable")
    else:
        if "docker start" in create or "$SCEN" in create or "scenario.py" in create:
            failures.append("row-create preflight may not start or mount a scenario")
        if "git apply" in create or "eval_script.sh:ro\"" not in create:
            failures.append("row-create preflight changed its inert certification-mount contract")
    if 'rm -f "$variant_tmp" "$gold_tmp"' in text or 'rm -f "$variant_tmp"' in text:
        failures.append("iter206 runner can delete the sole variant launch diagnostic")
    if text.count("retain_launch_diagnostic") < 7:
        failures.append("iter206 runner does not retain every declared failure phase")
    if text.count('ulimit -f "$((LAUNCH_DIAGNOSTIC_LIMIT_BYTES / 1024))"') != 2:
        failures.append("iter206 runner does not bound both create/run launch work files")
    if text.index("unset OPENAI_API_KEY ANTHROPIC_API_KEY") > text.index("docker "):
        failures.append("iter206 runner does not unset provider credentials before Docker")
    return failures


def validate_smoke_text(text: str) -> list[str]:
    failures = validate_local_log_contract(text, label="iter206 smoke")
    required = (
        "SMOKE_LIMIT_BYTES=65536",
        'ulimit -f "$((SMOKE_LIMIT_BYTES / 1024))"',
        'if [ "${GITHUB_RUN_ATTEMPT-}" != "1" ]',
        "plan_lines[0]",
        "--entrypoint bash",
        "TELOS_ITER206_LOG_DRIVER_SMOKE_OK",
        "scripts/capture_iter206_runtime_host.py --write",
        "scripts/publish_iter206_runtime_diagnostic.py",
        "scripts/prepare_iter206_output_directory.py",
        '"ordinal": 0',
        '"schema_version": "telos.iter206.no_science_smoke_receipt.v1"',
    )
    for fragment in required:
        if fragment not in text:
            failures.append(f"iter206 smoke missing contract fragment: {fragment}")
    if re.search(r"(?m)^\s*-v\s", text) or "$SOLS" in text or "$SCEN" in text:
        failures.append("iter206 global smoke exposes a scientific mount/input")
    if "git apply" in text or "/testbed" in text or "eval_script.sh" in text:
        failures.append("iter206 global smoke can execute a scientific command")
    if text.index("unset OPENAI_API_KEY ANTHROPIC_API_KEY") > text.index("docker "):
        failures.append("iter206 smoke does not unset provider credentials before Docker")
    return failures


def validate_workflow_text(text: str) -> list[str]:
    failures: list[str] = []
    input_block = re.search(
        r"(?ms)^    inputs:\n(?P<body>.*?)^concurrency:\n",
        text,
    )
    if input_block is None:
        failures.append("iter206 workflow dispatch inputs are not inspectable")
    else:
        input_names = set(
            re.findall(r"(?m)^      ([a-z0-9_]+):$", input_block.group("body"))
        )
        if input_names != {
            "expected_primary_sha",
            "expected_workflow_id",
            "expected_iter204_release_run_id",
            "expected_iter204_primary_run_id",
        }:
            failures.append("iter206 workflow dispatch input set differs")
    required = (
        "name: iter206-execute",
        "expected_workflow_id:",
        "expected_iter204_release_run_id:",
        "expected_iter204_primary_run_id:",
        'test "${GITHUB_RUN_ATTEMPT}" = "1"',
        '[[ "${EXPECTED_WORKFLOW_ID}" =~ ^[1-9][0-9]*$ ]]',
        '[[ "${EXPECTED_ITER204_RELEASE_RUN_ID}" =~ ^[1-9][0-9]*$ ]]',
        '[[ "${EXPECTED_ITER204_PRIMARY_RUN_ID}" =~ ^[1-9][0-9]*$ ]]',
        'test "$(git rev-list --parents -n 1 "${EXPECTED_PRIMARY_SHA}" | wc -w | tr -d \' \')" = "3"',
        'test "$(git rev-parse refs/remotes/origin/master)" = "${EXPECTED_PRIMARY_SHA}"',
        'current.get("run_attempt") != 1',
        'current.get("run_number") != 1',
        "[row.get(\"id\") for row in iter206_runs] != [current_run_id]",
        "[row.get(\"id\") for row in iter206_dispatch_runs] != [current_run_id]",
        "iter206 all-event history must contain only the current run",
        "iter206 dispatch history must contain only the current run",
        'iter206_workflow.get("name") != "iter206-execute"',
        "iter205_workflow_id = 314141096",
        'iter205_workflow.get("name") != "iter205-execute"',
        "iter205 all-event and dispatch histories must remain empty",
        "iter204_workflow_id = 314113289",
        "29465584664",
        "29465924803",
        "29468669956",
        "29468768706",
        "8342315dd2fa7ec865bd7c654ec4ec098675dfab",
        "c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446",
        "a336b4909329d392f6db5f6098792e07a17f28cb",
        "4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f",
        '"head_branch": "agent/iter206-iter205-admission-recovery"',
        '"id": expected_iter204_release_run_id',
        '"id": expected_iter204_primary_run_id',
        "payload[\"total_count\"] != len(rows)",
        "len(set(expected_ids)) != 6",
        "len(iter204_runs) != 6",
        "set(run_numbers) != set(range(1, 7))",
        'row.get("event") != "push"',
        'jobs.get("total_count") != 0',
        'artifacts.get("total_count") != 0',
        'require_http_404(f"actions/runs/{run_id}/logs")',
        "iter204 workflow_dispatch history must remain empty",
        "iter204_admission_history_sha256 = canonical_sha256(iter204_projection)",
        "len(ci_runs) != 1",
        "len(candidates) != 1",
        'len({job["id"] for job in required_jobs}) != 2',
        'selected_checks[0]["id"] == selected_checks[1]["id"]',
        '"iter204_admission_history_sha256": iter204_admission_history_sha256',
        '"iter205_all_event_count": len(iter205_runs)',
        '"iter205_dispatch_count": len(iter205_dispatch_runs)',
        '"merge_first_parent": merge_first_parent',
        '"merge_second_parent": merge_second_parent',
        "scripts/validate_iter205_pre_dispatch_null.py",
        "needs: [authorize, smoke]",
        "iter206-no-science-smoke-${{ github.run_id }}-attempt-1",
        "iter206-execution-run-${{ github.run_id }}-attempt-1-shard-",
        "iter206-execution-complete-${{ github.run_id }}-attempt-1",
        "proof/raw/smoke/*.diagnostic.log",
        "proof/raw/runtime_diagnostics/*.diagnostic.log",
    )
    for fragment in required:
        if fragment not in text:
            failures.append(f"iter206 workflow missing contract fragment: {fragment}")
    workflow_lines = text.splitlines()
    for index, line in enumerate(workflow_lines):
        if re.match(r"^    env\s*:", line) is None:
            continue
        block = [line]
        for following in workflow_lines[index + 1 :]:
            if following and len(following) - len(following.lstrip()) <= 4:
                break
            block.append(following)
        if "${{ runner." in "\n".join(block):
            failures.append(
                "iter206 workflow uses runner context in job-level env"
            )
    step_binding = (
        "      - name: Run iter206 execution shard\n"
        "        env:\n"
        "          TELOS_ITER206_SMOKE_RECEIPT: "
        "${{ runner.temp }}/iter206-smoke/smoke.receipt.json\n"
        "        run: bash scripts/ci_iter206_execute.sh"
    )
    if text.count(step_binding) != 1:
        failures.append("iter206 smoke receipt is not bound once in execution-step env")
    if text.count("TELOS_ITER206_SMOKE_RECEIPT:") != 1:
        failures.append("iter206 workflow has a duplicated smoke-receipt binding")
    if "rerun every job" in text or "github.run_attempt }}" in text:
        failures.append("iter206 workflow permits or names a later run attempt")
    if text.count("fetch-depth: 0") != 4:
        failures.append("iter206 workflow must use full history in exactly four jobs")
    if text.count("- name: Free disk") != 2:
        failures.append("iter206 workflow job steps are duplicated or missing")
    script = re.search(
        r"(?ms)^          python3 -I -S - <<'PY'\n(?P<body>.*?)^          PY$",
        text,
    )
    if script is None:
        failures.append("iter206 authorization Python is not inspectable")
    else:
        try:
            source = textwrap.dedent(script.group("body"))
            tree = ast.parse(source, filename="<iter206-authorize>", mode="exec")
        except SyntaxError as exc:
            failures.append(f"iter206 authorization Python is invalid: {exc}")
        else:
            authorization_dicts = [
                node.value
                for node in ast.walk(tree)
                if isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "authorization"
                    for target in node.targets
                )
                and isinstance(node.value, ast.Dict)
            ]
            if len(authorization_dicts) != 1:
                failures.append("iter206 authorization receipt is not uniquely inspectable")
            else:
                keys = authorization_dicts[0].keys
                if any(
                    not isinstance(key, ast.Constant) or not isinstance(key.value, str)
                    for key in keys
                ):
                    failures.append("iter206 authorization receipt has a dynamic key")
                elif {key.value for key in keys} != AUTHORIZATION_KEYS:
                    failures.append("iter206 workflow authorization key set differs")
    return failures


def _normalize_iter206_shell(text: str) -> str:
    return (
        text.replace(
            "iter206_iter205_admission_history_recovery",
            "iter205_iter204_workflow_context_recovery",
        )
        .replace("admission_history_recovery", "workflow_context_recovery")
        .replace("admission-history recovery", "workflow-context recovery")
        .replace("ITER206", "ITER205")
        .replace("Iter206", "Iter205")
        .replace("iter206", "iter205")
    )


def validate_cross_contract_identity(
    overrides: dict[Path, str] | None = None,
) -> list[str]:
    failures: list[str] = []
    replacements = overrides or {}

    def source(path: Path) -> str:
        return replacements.get(path, path.read_text())

    for successor, predecessor in (
        (RUNNER, ROOT / "scripts/ci_iter205_execute.sh"),
        (SMOKE, ROOT / "scripts/ci_iter205_smoke.sh"),
        (HOST, ROOT / "scripts/capture_iter205_runtime_host.py"),
        (OUTPUT_DIRECTORY, ROOT / "scripts/prepare_iter205_output_directory.py"),
        (DIAGNOSTIC, ROOT / "scripts/publish_iter205_runtime_diagnostic.py"),
        (
            ROOT / "scripts/adjudicate_iter206_admission_history_recovery.py",
            ROOT / "scripts/adjudicate_iter205_workflow_context_recovery.py",
        ),
        (
            ROOT / "scripts/run_iter206_admission_history_recovery_blind_judge.py",
            ROOT / "scripts/run_iter205_workflow_context_recovery_blind_judge.py",
        ),
    ):
        if _normalize_iter206_shell(source(successor)) != source(predecessor):
            failures.append(
                f"{successor.name}: scientific runtime differs beyond iter206 identity"
            )
    collector = _normalize_iter206_shell(source(COLLECTOR))
    predecessor_collector = source(ROOT / "scripts/collect_iter205_execution.py")
    for authorization_import, label in (
        ("import json\n", "JSON"),
        ("import subprocess\n", "subprocess"),
    ):
        if collector.count(authorization_import) != 1:
            failures.append(
                f"iter206 collector authorization {label} import is not exact"
            )
        else:
            collector = collector.replace(authorization_import, "", 1)
    successor_schema = (
        'PRIMARY_CI_AUTHORIZATION_SCHEMA = '
        '"telos.iter205.primary_ci_authorization.v2"'
    )
    predecessor_schema = (
        'PRIMARY_CI_AUTHORIZATION_SCHEMA = '
        '"telos.iter205.primary_ci_authorization.v1"'
    )
    if collector.count(successor_schema) != 1:
        failures.append("iter206 collector authorization v2 schema is not exact")
    else:
        collector = collector.replace(successor_schema, predecessor_schema, 1)
    release_ci_constants_pattern = (
        r"(?ms)^RELEASE_BRANCH = .*?"
        r"^RELEASE_CI_JOB_KEYS = \{\n.*?^}\n\n"
    )
    release_ci_constants = re.search(release_ci_constants_pattern, collector)
    if release_ci_constants is None:
        failures.append(
            "iter206 collector release-CI authorization constants are not inspectable"
        )
    else:
        collector = (
            collector[: release_ci_constants.start()]
            + collector[release_ci_constants.end() :]
        )
    section_patterns = (
        r"(?ms)^_core\.AUTHORIZATION_KEYS = .*?^}\n",
        (
            r"(?ms)^_original_validate_authorization = .*?"
            r"^_core\._validate_authorization = _validate_authorization\n"
        ),
    )
    for pattern in section_patterns:
        successor_match = re.search(pattern, collector)
        predecessor_match = re.search(pattern, predecessor_collector)
        if successor_match is None or predecessor_match is None:
            failures.append(
                "iter206 collector exact authorization extension differs: not inspectable"
            )
            continue
        collector = (
            collector[: successor_match.start()]
            + predecessor_match.group(0)
            + collector[successor_match.end() :]
        )
    if collector != predecessor_collector:
        failures.append("iter206 collector differs beyond its exact authorization extension")
    try:
        from scripts import build_iter206_runtime_manifest as runtime
        from scripts import capture_iter206_runtime_host as host
        from scripts import collect_iter206_execution as collector
        from scripts import publish_iter206_runtime_diagnostic as diagnostic

        expected_workflow_ref = (
            "manfromnowhere143/telos/.github/workflows/"
            "iter206-execute.yml@refs/heads/master"
        )
        if {
            collector.CANONICAL_WORKFLOW_REF,
            host.CANONICAL_WORKFLOW_REF,
            diagnostic.CANONICAL_WORKFLOW_REF,
        } != {expected_workflow_ref}:
            failures.append("iter206 receipt producers bind different workflow identities")
        if collector.RUNTIME_MANIFEST_SCHEMA != runtime.SCHEMA:
            failures.append("iter206 collector/runtime manifest schemas differ")
        if (
            collector.AGGREGATE_RECEIPT_NAME
            != runtime.ITER206_AGGREGATE_RECEIPT_NAME
            or collector.AGGREGATE_SCHEMA
            != runtime.ITER206_AGGREGATE_RECEIPT_SCHEMA
            or collector.SHARD_SCHEMA != runtime.ITER206_SHARD_RECEIPT_SCHEMA
        ):
            failures.append("iter206 execution receipt identities drift across contracts")
        if collector.PRIMARY_CI_AUTHORIZATION_SCHEMA not in WORKFLOW.read_text():
            failures.append("iter206 workflow/collector authorization schemas differ")
        if collector.PRIMARY_CI_AUTHORIZATION_SCHEMA != (
            "telos.iter206.primary_ci_authorization.v2"
        ):
            failures.append("iter206 authorization schema is not exact v2")
        if collector._core.AUTHORIZATION_KEYS != AUTHORIZATION_KEYS:
            failures.append("iter206 collector authorization key set differs")
    except (ImportError, AttributeError, OSError, RuntimeError) as exc:
        failures.append(f"iter206 cross-contract import failed: {exc}")
    for path in (RUNNER, SMOKE, COLLECTOR, DIAGNOSTIC, HOST):
        text = source(path)
        for stale in ("telos.iter205.", "_telos_iter205_", "iter205-execution-run-"):
            if stale in text:
                failures.append(f"{path.name}: stale receipt identity remains: {stale}")
    return failures


def validate_source_contract() -> list[str]:
    failures: list[str] = []
    for relative, expected in FROZEN_ITER205.items():
        path = ROOT / relative
        if not path.is_file() or path.is_symlink() or sha256(path) != expected:
            failures.append(f"frozen iter205 byte drift: {relative}")
    runner = RUNNER.read_text(encoding="utf-8")
    smoke = SMOKE.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    failures.extend(validate_runner_text(runner))
    failures.extend(validate_smoke_text(smoke))
    failures.extend(validate_workflow_text(workflow))
    failures.extend(validate_cross_contract_identity())
    collector = COLLECTOR.read_text(encoding="utf-8")
    for fragment in (
        'run_attempt"] != "1"',
        "ARTIFACT_RE = re.compile",
        "attempt-(1)-shard",
        '"runtime_host", "smoke_gate"',
        '"runtime_hosts"',
        "shards bind different iter206 smoke receipts",
        '"current_run_attempt"',
        '"current_run_id"',
        '"iter204_admission_history_sha256"',
        '"iter204_dispatch_count"',
        '"iter204_primary_run_id"',
        '"iter204_release_run_id"',
        '"iter204_workflow_id"',
        '"iter205_all_event_count"',
        '"iter205_dispatch_count"',
        '"iter205_workflow_id"',
        '"iter206_workflow_id"',
        '"merge_first_parent"',
        '"merge_second_parent"',
        'authorization.get("primary_ci_run_attempt") != 1',
        '"release_ci_head_sha"',
        '"release_ci_runs"',
        '"head_repository"',
        "_expected_iter204_admission_projection",
        "_git_merge_parents",
        "does not reproduce the exact-six iter204 admission digest",
        "does not match the checked-out iter206 merge parents",
        "release CI pair is incomplete",
        "Actions run and CI job identities are not exact and unique",
        "does not bind the exact-six iter206 admission contract",
    ):
        if fragment not in collector:
            failures.append(f"iter206 collector missing provenance fragment: {fragment}")
    diagnostic = DIAGNOSTIC.read_text(encoding="utf-8")
    for fragment in (
        "_read_regular_bounded",
        "runtime_host_receipt",
        "CANONICAL_WORKFLOW_REF",
        'github["run_attempt"] != "1"',
        "image_id",
        "shard_index",
        "metadata_destination.unlink",
        "host_capture.validate_document",
        'runtime_host["github"] != github',
    ):
        if fragment not in diagnostic:
            failures.append(f"iter206 diagnostic publisher missing: {fragment}")
    host = HOST.read_text(encoding="utf-8")
    for fragment in (
        '"docker_client"',
        '"docker_server"',
        '"runner_image"',
        "CANONICAL_WORKFLOW_REF",
        'runner[key] != "unavailable"',
    ):
        if fragment not in host:
            failures.append(f"iter206 host capture missing: {fragment}")
    output_directory = OUTPUT_DIRECTORY.read_text(encoding="utf-8")
    for fragment in (
        'getattr(os, "O_NOFOLLOW", 0)',
        "dir_fd=descriptor",
        "os.listdir(descriptor)",
        "output directory already exists",
        "output directory is not empty",
    ):
        if fragment not in output_directory:
            failures.append(f"iter206 output-directory guard missing: {fragment}")
    return failures


def validate_all() -> list[str]:
    failures = validate_source_contract()
    try:
        from scripts import build_iter206_runtime_manifest as runtime
        from scripts import validate_iter205_pre_dispatch_null as null_guard
        from scripts import validate_iter206_publication_safety as publication

        null_guard.validate()
        failures.extend(runtime.validate_committed_manifest())
        prior = publication.validate_frozen_iter205_receipt()
        if prior.get("scanned_file_count") != 397:
            failures.append("frozen iter205 publication receipt no longer verifies")
        expected_publication = publication.canonical_json_bytes(publication.build_audit())
        if publication.AUDIT.read_bytes() != expected_publication:
            failures.append("iter206 current publication-safety receipt differs")
    except (OSError, ValueError) as exc:
        failures.append(f"iter206 evidence guard failed: {exc}")
    for shell in (RUNNER, SMOKE):
        completed = subprocess.run(
            ["bash", "-n", str(shell)], capture_output=True, text=True, check=False
        )
        if completed.returncode != 0:
            failures.append(f"shell syntax invalid: {shell.relative_to(ROOT)}")
    return failures


def main() -> int:
    failures = validate_all()
    if failures:
        for failure in failures:
            print(f"iter206 admission-history guard failed: {failure}", file=sys.stderr)
        return 1
    print(
        "iter206 admission-history guard: source, admission null, smoke, "
        "provenance, and closure pass"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
