#!/usr/bin/env python3
"""Fail closed on drift in the iter204 infrastructure-recovery contract."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RUNNER = ROOT / "scripts/ci_iter204_execute.sh"
SMOKE = ROOT / "scripts/ci_iter204_smoke.sh"
WORKFLOW = ROOT / ".github/workflows/iter204-execute.yml"
COLLECTOR = ROOT / "scripts/collect_iter204_execution.py"
DIAGNOSTIC = ROOT / "scripts/publish_iter204_runtime_diagnostic.py"
HOST = ROOT / "scripts/capture_iter204_runtime_host.py"
OUTPUT_DIRECTORY = ROOT / "scripts/prepare_iter204_output_directory.py"

FROZEN_ITER203 = {
    "scripts/ci_iter203_execute.sh": "f2cccfe16f22707e8b2f53f9ea0140c52e68b4b2d8104042820d840b9235bef9",
    ".github/workflows/iter203-execute.yml": "808fa85dcbf4704d8901603d990d25ea4e4e53bd2112e9012b99c61779005261",
    "scripts/collect_iter203_execution.py": "8dcd5652cdaeaf5f6a613c4d2a31f99bc7024dd6ee91ea91f2e461cfc245d67c",
    "scripts/build_iter203_runtime_manifest.py": "a96d023800b34d7bdcee099c5885e8e817892425c4acca9fa2e35cc3b8e5be89",
    "experiments/iter203_iter202_safety_recovery/HYPOTHESIS.md": "c11970a62f8a76d77cdcb42c0e7e76d1a652306d71b0c2b1ae134171abb9e5eb",
    "experiments/iter203_iter202_safety_recovery/proof/raw/runtime_manifest.json": (
        "8beb0e845dbc9e3a4ce56832f28a62d4fd58ceac20adbc6bc06d6aef41be47e1"
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
    failures = validate_local_log_contract(text, label="iter204 runner")
    required = (
        'EXP="experiments/iter204_iter203_infrastructure_recovery"',
        'SOURCE_EXP="experiments/iter203_iter202_safety_recovery"',
        'LAUNCH_DIAGNOSTIC_LIMIT_BYTES=2162688',
        'ulimit -f "$((LAUNCH_DIAGNOSTIC_LIMIT_BYTES / 1024))"',
        'if [ "${GITHUB_RUN_ATTEMPT-}" != "1" ]',
        "scripts/build_iter204_runtime_manifest.py --check",
        "scripts/prepare_iter204_output_directory.py",
        "scripts/collect_iter204_execution.py smoke-check",
        "docker \"${create_args[@]}\"",
        '--entrypoint bash',
        '-v "$PWD/$SPECS/$stem.eval_script.sh:/specs/$stem.eval_script.sh:ro"',
        '-v "$PWD/$SPECS/$stem.spec.json:/specs/$stem.spec.json:ro"',
        '-v "$PWD/$SOLS/$stem.model.patch:/solutions/$stem.model.patch:ro"',
        '"scientific_container_launch_variant_cert"',
        '"scientific_container_launch_variant_behavior"',
        '"scientific_container_launch_gold_behavior"',
        '"incomplete_scientific_variant_evidence"',
        'scripts/publish_iter204_runtime_diagnostic.py',
        'scripts/collect_iter204_execution.py shard-receipt',
    )
    for fragment in required:
        if fragment not in text:
            failures.append(f"iter204 runner missing contract fragment: {fragment}")
    create_start = text.find("row_create_preflight()")
    create_end = text.find("marker_ordered()", create_start)
    create = text[create_start:create_end]
    if create_start < 0 or create_end < 0:
        failures.append("iter204 runner row-create preflight is not inspectable")
    else:
        if "docker start" in create or "$SCEN" in create or "scenario.py" in create:
            failures.append("row-create preflight may not start or mount a scenario")
        if "git apply" in create or "eval_script.sh:ro\"" not in create:
            failures.append("row-create preflight changed its inert certification-mount contract")
    if 'rm -f "$variant_tmp" "$gold_tmp"' in text or 'rm -f "$variant_tmp"' in text:
        failures.append("iter204 runner can delete the sole variant launch diagnostic")
    if text.count("retain_launch_diagnostic") < 7:
        failures.append("iter204 runner does not retain every declared failure phase")
    if text.count('ulimit -f "$((LAUNCH_DIAGNOSTIC_LIMIT_BYTES / 1024))"') != 2:
        failures.append("iter204 runner does not bound both create/run launch work files")
    if text.index("unset OPENAI_API_KEY ANTHROPIC_API_KEY") > text.index("docker "):
        failures.append("iter204 runner does not unset provider credentials before Docker")
    return failures


def validate_smoke_text(text: str) -> list[str]:
    failures = validate_local_log_contract(text, label="iter204 smoke")
    required = (
        "SMOKE_LIMIT_BYTES=65536",
        'ulimit -f "$((SMOKE_LIMIT_BYTES / 1024))"',
        'if [ "${GITHUB_RUN_ATTEMPT-}" != "1" ]',
        "plan_lines[0]",
        "--entrypoint bash",
        "TELOS_ITER204_LOG_DRIVER_SMOKE_OK",
        "scripts/capture_iter204_runtime_host.py --write",
        "scripts/publish_iter204_runtime_diagnostic.py",
        "scripts/prepare_iter204_output_directory.py",
        '"ordinal": 0',
        '"schema_version": "telos.iter204.no_science_smoke_receipt.v1"',
    )
    for fragment in required:
        if fragment not in text:
            failures.append(f"iter204 smoke missing contract fragment: {fragment}")
    if re.search(r"(?m)^\s*-v\s", text) or "$SOLS" in text or "$SCEN" in text:
        failures.append("iter204 global smoke exposes a scientific mount/input")
    if "git apply" in text or "/testbed" in text or "eval_script.sh" in text:
        failures.append("iter204 global smoke can execute a scientific command")
    if text.index("unset OPENAI_API_KEY ANTHROPIC_API_KEY") > text.index("docker "):
        failures.append("iter204 smoke does not unset provider credentials before Docker")
    return failures


def validate_workflow_text(text: str) -> list[str]:
    failures: list[str] = []
    required = (
        "name: iter204-execute",
        'test "${GITHUB_RUN_ATTEMPT}" = "1"',
        'current.get("run_attempt") != 1',
        "sorted(set(iter204_runs)) != [current_run_id]",
        "iter204 permits exactly one global workflow dispatch and attempt 1 only",
        "iter203_run_id = 29460393525",
        'iter203.get("run_attempt") != 1',
        'iter203.get("head_sha") != "5c409f79c9333206cff9ed80d59c08aa347110f6"',
        "historical_iter203_runs",
        "artifacts.get(\"total_count\") != 0",
        "needs: [authorize, smoke]",
        "iter204-no-science-smoke-${{ github.run_id }}-attempt-1",
        "iter204-execution-run-${{ github.run_id }}-attempt-1-shard-",
        "iter204-execution-complete-${{ github.run_id }}-attempt-1",
        "proof/raw/smoke/*.diagnostic.log",
        "proof/raw/runtime_diagnostics/*.diagnostic.log",
    )
    for fragment in required:
        if fragment not in text:
            failures.append(f"iter204 workflow missing contract fragment: {fragment}")
    if "rerun every job" in text or "github.run_attempt }}" in text:
        failures.append("iter204 workflow permits or names a later run attempt")
    if text.count("fetch-depth: 0") != 4:
        failures.append("iter204 workflow must use full history in exactly four jobs")
    return failures


def validate_source_contract() -> list[str]:
    failures: list[str] = []
    for relative, expected in FROZEN_ITER203.items():
        path = ROOT / relative
        if not path.is_file() or path.is_symlink() or sha256(path) != expected:
            failures.append(f"frozen iter203 byte drift: {relative}")
    runner = RUNNER.read_text(encoding="utf-8")
    smoke = SMOKE.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    failures.extend(validate_runner_text(runner))
    failures.extend(validate_smoke_text(smoke))
    failures.extend(validate_workflow_text(workflow))
    collector = COLLECTOR.read_text(encoding="utf-8")
    for fragment in (
        'run_attempt"] != "1"',
        "ARTIFACT_RE = re.compile",
        "attempt-(1)-shard",
        '"runtime_host", "smoke_gate"',
        '"runtime_hosts"',
        "shards bind different iter204 smoke receipts",
    ):
        if fragment not in collector:
            failures.append(f"iter204 collector missing provenance fragment: {fragment}")
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
            failures.append(f"iter204 diagnostic publisher missing: {fragment}")
    host = HOST.read_text(encoding="utf-8")
    for fragment in (
        '"docker_client"',
        '"docker_server"',
        '"runner_image"',
        "CANONICAL_WORKFLOW_REF",
        'runner[key] != "unavailable"',
    ):
        if fragment not in host:
            failures.append(f"iter204 host capture missing: {fragment}")
    output_directory = OUTPUT_DIRECTORY.read_text(encoding="utf-8")
    for fragment in (
        'getattr(os, "O_NOFOLLOW", 0)',
        "dir_fd=descriptor",
        "os.listdir(descriptor)",
        "output directory already exists",
        "output directory is not empty",
    ):
        if fragment not in output_directory:
            failures.append(f"iter204 output-directory guard missing: {fragment}")
    return failures


def validate_all() -> list[str]:
    failures = validate_source_contract()
    try:
        from scripts import build_iter204_runtime_manifest as runtime
        from scripts import validate_iter203_infrastructure_null as null_guard
        from scripts import validate_iter204_publication_safety as publication

        null_guard.validate()
        failures.extend(runtime.validate_committed_manifest())
        prior = publication.prior.validate_frozen_receipt()
        if prior.get("scanned_file_count") != 564:
            failures.append("frozen iter203 publication receipt no longer verifies")
        expected_publication = publication.canonical_json_bytes(publication.build_audit())
        if publication.AUDIT.read_bytes() != expected_publication:
            failures.append("iter204 current publication-safety receipt differs")
    except (OSError, ValueError) as exc:
        failures.append(f"iter204 evidence guard failed: {exc}")
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
            print(f"iter204 runtime-recovery guard failed: {failure}", file=sys.stderr)
        return 1
    print("iter204 runtime-recovery guard: source, null, smoke, provenance, and closure pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
