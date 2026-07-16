#!/usr/bin/env python3
"""Fail closed on drift in the iter205 workflow-context recovery contract."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
import subprocess
import sys
import textwrap


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RUNNER = ROOT / "scripts/ci_iter205_execute.sh"
SMOKE = ROOT / "scripts/ci_iter205_smoke.sh"
WORKFLOW = ROOT / ".github/workflows/iter205-execute.yml"
COLLECTOR = ROOT / "scripts/collect_iter205_execution.py"
DIAGNOSTIC = ROOT / "scripts/publish_iter205_runtime_diagnostic.py"
HOST = ROOT / "scripts/capture_iter205_runtime_host.py"
OUTPUT_DIRECTORY = ROOT / "scripts/prepare_iter205_output_directory.py"

FROZEN_ITER204 = {
    ".github/workflows/iter204-execute.yml": (
        "84f7f8b228624ff7244991e317e7f8146a6aacd93f803c1df983b6cceae4deb4"
    ),
    "experiments/iter204_iter203_infrastructure_recovery/HYPOTHESIS.md": (
        "7f6b9e0ba0ba0077115e64e38239a6eeafb2b18797fdd160a3eb9c0297396dfd"
    ),
    "experiments/iter204_iter203_infrastructure_recovery/proof/raw/runtime_manifest.json": (
        "bf2062825e604d9439b0d29375d7e5219a1064ae4a33701efb74a62f81a59a45"
    ),
    "experiments/iter204_iter203_infrastructure_recovery/proof/pre_execution_publication_safety.json": (
        "8cdfdaa6139076b730556743ce1e9c8519fcc27782d2efd19b1645610ac91308"
    ),
    "scripts/ci_iter204_execute.sh": (
        "aa96c5ef5908d0d2df8c01d7b0fb9f9623491c3a8555152790aa1227c24ba424"
    ),
    "scripts/ci_iter204_smoke.sh": (
        "3bd7504e1eb2b31b2c2fa25e7d7ee13f94c8a1a7ed3f02375e34cdca89b1354e"
    ),
    "scripts/collect_iter204_execution.py": (
        "13789bfc14a0e943a40154e93071afbc37e1d0b51844222e89c1358dfc0d44b4"
    ),
    "scripts/capture_iter204_runtime_host.py": (
        "cf9da979edd25f1fb61770197635e4c9e49603d31943a5b993622bc96a28d5b9"
    ),
    "scripts/prepare_iter204_output_directory.py": (
        "19269c4143a493e08f781ea50dc9550550283d04f3d9a45e8637f3dd35e2bcd7"
    ),
    "scripts/publish_iter204_runtime_diagnostic.py": (
        "e93dcd8b1c3fbe6064ad3a9c87b3d631b5a13f1d568b57a240148ab4d9f1fae5"
    ),
    "scripts/adjudicate_iter204_infrastructure_recovery.py": (
        "3dd23a3afe9a27ede3e4ba0290b681e1e1a5f218c6cb3877a3714a505bc3c4e0"
    ),
    "scripts/run_iter204_infrastructure_recovery_blind_judge.py": (
        "d0a06e14d7c9b42b0588654317a96f40745cd362ebde08c6c597e095ed5ebe34"
    ),
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
    failures = validate_local_log_contract(text, label="iter205 runner")
    required = (
        'EXP="experiments/iter205_iter204_workflow_context_recovery"',
        'SOURCE_EXP="experiments/iter203_iter202_safety_recovery"',
        'LAUNCH_DIAGNOSTIC_LIMIT_BYTES=2162688',
        'ulimit -f "$((LAUNCH_DIAGNOSTIC_LIMIT_BYTES / 1024))"',
        'if [ "${GITHUB_RUN_ATTEMPT-}" != "1" ]',
        "scripts/build_iter205_runtime_manifest.py --check",
        "scripts/prepare_iter205_output_directory.py",
        "scripts/collect_iter205_execution.py smoke-check",
        "docker \"${create_args[@]}\"",
        '--entrypoint bash',
        '-v "$PWD/$SPECS/$stem.eval_script.sh:/specs/$stem.eval_script.sh:ro"',
        '-v "$PWD/$SPECS/$stem.spec.json:/specs/$stem.spec.json:ro"',
        '-v "$PWD/$SOLS/$stem.model.patch:/solutions/$stem.model.patch:ro"',
        '"scientific_container_launch_variant_cert"',
        '"scientific_container_launch_variant_behavior"',
        '"scientific_container_launch_gold_behavior"',
        '"incomplete_scientific_variant_evidence"',
        'scripts/publish_iter205_runtime_diagnostic.py',
        'scripts/collect_iter205_execution.py shard-receipt',
    )
    for fragment in required:
        if fragment not in text:
            failures.append(f"iter205 runner missing contract fragment: {fragment}")
    create_start = text.find("row_create_preflight()")
    create_end = text.find("marker_ordered()", create_start)
    create = text[create_start:create_end]
    if create_start < 0 or create_end < 0:
        failures.append("iter205 runner row-create preflight is not inspectable")
    else:
        if "docker start" in create or "$SCEN" in create or "scenario.py" in create:
            failures.append("row-create preflight may not start or mount a scenario")
        if "git apply" in create or "eval_script.sh:ro\"" not in create:
            failures.append("row-create preflight changed its inert certification-mount contract")
    if 'rm -f "$variant_tmp" "$gold_tmp"' in text or 'rm -f "$variant_tmp"' in text:
        failures.append("iter205 runner can delete the sole variant launch diagnostic")
    if text.count("retain_launch_diagnostic") < 7:
        failures.append("iter205 runner does not retain every declared failure phase")
    if text.count('ulimit -f "$((LAUNCH_DIAGNOSTIC_LIMIT_BYTES / 1024))"') != 2:
        failures.append("iter205 runner does not bound both create/run launch work files")
    if text.index("unset OPENAI_API_KEY ANTHROPIC_API_KEY") > text.index("docker "):
        failures.append("iter205 runner does not unset provider credentials before Docker")
    return failures


def validate_smoke_text(text: str) -> list[str]:
    failures = validate_local_log_contract(text, label="iter205 smoke")
    required = (
        "SMOKE_LIMIT_BYTES=65536",
        'ulimit -f "$((SMOKE_LIMIT_BYTES / 1024))"',
        'if [ "${GITHUB_RUN_ATTEMPT-}" != "1" ]',
        "plan_lines[0]",
        "--entrypoint bash",
        "TELOS_ITER205_LOG_DRIVER_SMOKE_OK",
        "scripts/capture_iter205_runtime_host.py --write",
        "scripts/publish_iter205_runtime_diagnostic.py",
        "scripts/prepare_iter205_output_directory.py",
        '"ordinal": 0',
        '"schema_version": "telos.iter205.no_science_smoke_receipt.v1"',
    )
    for fragment in required:
        if fragment not in text:
            failures.append(f"iter205 smoke missing contract fragment: {fragment}")
    if re.search(r"(?m)^\s*-v\s", text) or "$SOLS" in text or "$SCEN" in text:
        failures.append("iter205 global smoke exposes a scientific mount/input")
    if "git apply" in text or "/testbed" in text or "eval_script.sh" in text:
        failures.append("iter205 global smoke can execute a scientific command")
    if text.index("unset OPENAI_API_KEY ANTHROPIC_API_KEY") > text.index("docker "):
        failures.append("iter205 smoke does not unset provider credentials before Docker")
    return failures


def validate_workflow_text(text: str) -> list[str]:
    failures: list[str] = []
    required = (
        "name: iter205-execute",
        'test "${GITHUB_RUN_ATTEMPT}" = "1"',
        'current.get("run_attempt") != 1',
        "iter205_runs != [current_run_id]",
        "iter205_dispatch_runs != [current_run_id]",
        "dispatch history must contain exactly the current run",
        "iter205 permits exactly one global workflow dispatch and attempt 1 only",
        'iter205_workflow.get("name") != "iter205-execute"',
        "iter204_workflow_id = 314113289",
        "29465584664",
        "29465924803",
        "8342315dd2fa7ec865bd7c654ec4ec098675dfab",
        "c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446",
        "set(iter204_by_id) != set(expected_iter204_push_failures)",
        "len(all_iter204_runs) != len(expected_iter204_push_failures)",
        'row.get("event") != "push"',
        'jobs.get("total_count") != 0',
        'artifacts.get("total_count") != 0',
        'row.get("event") == "workflow_dispatch"',
        "zero workflow_dispatch runs before iter205",
        "scripts/validate_iter204_pre_dispatch_null.py",
        "needs: [authorize, smoke]",
        "iter205-no-science-smoke-${{ github.run_id }}-attempt-1",
        "iter205-execution-run-${{ github.run_id }}-attempt-1-shard-",
        "iter205-execution-complete-${{ github.run_id }}-attempt-1",
        "proof/raw/smoke/*.diagnostic.log",
        "proof/raw/runtime_diagnostics/*.diagnostic.log",
    )
    for fragment in required:
        if fragment not in text:
            failures.append(f"iter205 workflow missing contract fragment: {fragment}")
    all_event_start = text.find("          iter205_runs = []")
    dispatch_start = text.find("          iter205_dispatch_runs = []")
    all_event_block = text[all_event_start:dispatch_start]
    if (
        all_event_start < 0
        or dispatch_start < 0
        or dispatch_start <= all_event_start
        or '"event": "workflow_dispatch"' in all_event_block
    ):
        failures.append("iter205 all-event history can hide parser records")
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
                "iter205 workflow uses runner context in job-level env"
            )
    step_binding = (
        "      - name: Run iter205 execution shard\n"
        "        env:\n"
        "          TELOS_ITER205_SMOKE_RECEIPT: "
        "${{ runner.temp }}/iter205-smoke/smoke.receipt.json\n"
        "        run: bash scripts/ci_iter205_execute.sh"
    )
    if text.count(step_binding) != 1:
        failures.append("iter205 smoke receipt is not bound once in execution-step env")
    if text.count("TELOS_ITER205_SMOKE_RECEIPT:") != 1:
        failures.append("iter205 workflow has a duplicated smoke-receipt binding")
    if "rerun every job" in text or "github.run_attempt }}" in text:
        failures.append("iter205 workflow permits or names a later run attempt")
    if text.count("fetch-depth: 0") != 4:
        failures.append("iter205 workflow must use full history in exactly four jobs")
    if text.count("- name: Free disk") != 2:
        failures.append("iter205 workflow job steps are duplicated or missing")
    script = re.search(
        r"(?ms)^          python3 -I -S - <<'PY'\n(?P<body>.*?)^          PY$",
        text,
    )
    if script is None:
        failures.append("iter205 authorization Python is not inspectable")
    else:
        try:
            compile(textwrap.dedent(script.group("body")), "<iter205-authorize>", "exec")
        except SyntaxError as exc:
            failures.append(f"iter205 authorization Python is invalid: {exc}")
    return failures


def _normalize_iter205_shell(text: str) -> str:
    return (
        text.replace(
            "iter205_iter204_workflow_context_recovery",
            "iter204_iter203_infrastructure_recovery",
        )
        .replace("workflow_context_recovery", "infrastructure_recovery")
        .replace("workflow-context recovery", "infrastructure recovery")
        .replace("ITER205", "ITER204")
        .replace("Iter205", "Iter204")
        .replace("iter205", "iter204")
    )


def validate_cross_contract_identity(
    overrides: dict[Path, str] | None = None,
) -> list[str]:
    failures: list[str] = []
    replacements = overrides or {}

    def source(path: Path) -> str:
        return replacements.get(path, path.read_text())

    for successor, predecessor in (
        (RUNNER, ROOT / "scripts/ci_iter204_execute.sh"),
        (SMOKE, ROOT / "scripts/ci_iter204_smoke.sh"),
        (HOST, ROOT / "scripts/capture_iter204_runtime_host.py"),
        (OUTPUT_DIRECTORY, ROOT / "scripts/prepare_iter204_output_directory.py"),
        (DIAGNOSTIC, ROOT / "scripts/publish_iter204_runtime_diagnostic.py"),
        (
            ROOT / "scripts/adjudicate_iter205_workflow_context_recovery.py",
            ROOT / "scripts/adjudicate_iter204_infrastructure_recovery.py",
        ),
        (
            ROOT / "scripts/run_iter205_workflow_context_recovery_blind_judge.py",
            ROOT / "scripts/run_iter204_infrastructure_recovery_blind_judge.py",
        ),
    ):
        if _normalize_iter205_shell(source(successor)) != source(predecessor):
            failures.append(
                f"{successor.name}: scientific runtime differs beyond iter205 identity"
            )
    collector = _normalize_iter205_shell(source(COLLECTOR))
    authorization_keys = '''_core.AUTHORIZATION_KEYS = set(_core.AUTHORIZATION_KEYS) | {
    "iter204_dispatch_count",
    "iter204_primary_ci_run_id",
    "iter204_primary_sha",
    "iter204_workflow_id",
}
'''
    authorization_validator = '''_original_validate_authorization = _core._validate_authorization


def _validate_authorization(
    value: Any, github: dict[str, str], label: str
) -> dict[str, Any]:
    authorization = _original_validate_authorization(value, github, label)
    if (
        authorization.get("iter204_dispatch_count") != 0
        or authorization.get("iter204_primary_ci_run_id") != 29465925393
        or authorization.get("iter204_primary_sha")
        != "c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446"
        or authorization.get("iter204_workflow_id") != 314113289
    ):
        raise ExecutionCollectionError(
            f"{label} does not bind the exact iter204 pre-dispatch null"
        )
    return authorization


_core._validate_authorization = _validate_authorization


'''
    for allowed in (authorization_keys, authorization_validator):
        if collector.count(allowed) != 1:
            failures.append("iter205 collector exact authorization extension differs")
        collector = collector.replace(allowed, "", 1)
    if collector != source(ROOT / "scripts/collect_iter204_execution.py"):
        failures.append("iter205 collector differs beyond its exact authorization extension")
    try:
        from scripts import build_iter205_runtime_manifest as runtime
        from scripts import capture_iter205_runtime_host as host
        from scripts import collect_iter205_execution as collector
        from scripts import publish_iter205_runtime_diagnostic as diagnostic

        expected_workflow_ref = (
            "manfromnowhere143/telos/.github/workflows/"
            "iter205-execute.yml@refs/heads/master"
        )
        if {
            collector.CANONICAL_WORKFLOW_REF,
            host.CANONICAL_WORKFLOW_REF,
            diagnostic.CANONICAL_WORKFLOW_REF,
        } != {expected_workflow_ref}:
            failures.append("iter205 receipt producers bind different workflow identities")
        if collector.RUNTIME_MANIFEST_SCHEMA != runtime.SCHEMA:
            failures.append("iter205 collector/runtime manifest schemas differ")
        if (
            collector.AGGREGATE_RECEIPT_NAME
            != runtime.ITER205_AGGREGATE_RECEIPT_NAME
            or collector.AGGREGATE_SCHEMA
            != runtime.ITER205_AGGREGATE_RECEIPT_SCHEMA
            or collector.SHARD_SCHEMA != runtime.ITER205_SHARD_RECEIPT_SCHEMA
        ):
            failures.append("iter205 execution receipt identities drift across contracts")
        if collector.PRIMARY_CI_AUTHORIZATION_SCHEMA not in WORKFLOW.read_text():
            failures.append("iter205 workflow/collector authorization schemas differ")
    except (ImportError, AttributeError, OSError, RuntimeError) as exc:
        failures.append(f"iter205 cross-contract import failed: {exc}")
    for path in (RUNNER, SMOKE, COLLECTOR, DIAGNOSTIC, HOST):
        text = source(path)
        for stale in ("telos.iter204.", "_telos_iter204_", "iter204-execution-run-"):
            if stale in text:
                failures.append(f"{path.name}: stale receipt identity remains: {stale}")
    return failures


def validate_source_contract() -> list[str]:
    failures: list[str] = []
    for relative, expected in FROZEN_ITER204.items():
        path = ROOT / relative
        if not path.is_file() or path.is_symlink() or sha256(path) != expected:
            failures.append(f"frozen iter204 byte drift: {relative}")
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
        "shards bind different iter205 smoke receipts",
        '"iter204_dispatch_count"',
        '"iter204_primary_ci_run_id"',
        '"iter204_primary_sha"',
        '"iter204_workflow_id"',
        "does not bind the exact iter204 pre-dispatch null",
    ):
        if fragment not in collector:
            failures.append(f"iter205 collector missing provenance fragment: {fragment}")
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
            failures.append(f"iter205 diagnostic publisher missing: {fragment}")
    host = HOST.read_text(encoding="utf-8")
    for fragment in (
        '"docker_client"',
        '"docker_server"',
        '"runner_image"',
        "CANONICAL_WORKFLOW_REF",
        'runner[key] != "unavailable"',
    ):
        if fragment not in host:
            failures.append(f"iter205 host capture missing: {fragment}")
    output_directory = OUTPUT_DIRECTORY.read_text(encoding="utf-8")
    for fragment in (
        'getattr(os, "O_NOFOLLOW", 0)',
        "dir_fd=descriptor",
        "os.listdir(descriptor)",
        "output directory already exists",
        "output directory is not empty",
    ):
        if fragment not in output_directory:
            failures.append(f"iter205 output-directory guard missing: {fragment}")
    return failures


def validate_all() -> list[str]:
    failures = validate_source_contract()
    try:
        from scripts import build_iter205_runtime_manifest as runtime
        from scripts import validate_iter204_pre_dispatch_null as null_guard
        from scripts import validate_iter205_publication_safety as publication

        null_guard.validate()
        failures.extend(runtime.validate_committed_manifest())
        prior = publication.validate_frozen_iter204_receipt()
        if prior.get("scanned_file_count") != 381:
            failures.append("frozen iter204 publication receipt no longer verifies")
        expected_publication = publication.canonical_json_bytes(publication.build_audit())
        if publication.AUDIT.read_bytes() != expected_publication:
            failures.append("iter205 current publication-safety receipt differs")
    except (OSError, ValueError) as exc:
        failures.append(f"iter205 evidence guard failed: {exc}")
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
            print(f"iter205 workflow-context guard failed: {failure}", file=sys.stderr)
        return 1
    print(
        "iter205 workflow-context guard: source, admission null, smoke, "
        "provenance, and closure pass"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
