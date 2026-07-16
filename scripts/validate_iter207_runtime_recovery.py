#!/usr/bin/env python3
"""Fail closed on drift in iter207 claim-integrity/admission recovery."""

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
RUNNER = ROOT / "scripts/ci_iter207_execute.sh"
SMOKE = ROOT / "scripts/ci_iter207_smoke.sh"
WORKFLOW = ROOT / ".github/workflows/iter207-execute.yml"
COLLECTOR = ROOT / "scripts/collect_iter207_execution.py"
DIAGNOSTIC = ROOT / "scripts/publish_iter207_runtime_diagnostic.py"
HOST = ROOT / "scripts/capture_iter207_runtime_host.py"
OUTPUT_DIRECTORY = ROOT / "scripts/prepare_iter207_output_directory.py"

FROZEN_ITER206 = {
    ".github/workflows/iter206-execute.yml": (
        "2a81a356709db97884b535f82367794541b4bd4d8d77ec4c83760d3deea3f215"
    ),
    "experiments/iter206_iter205_admission_history_recovery/HYPOTHESIS.md": (
        "3e1185f5a79bf0cbd85ee046065ff9caf17fe7c1ccaa2c519be053510b1c4f26"
    ),
    "experiments/iter206_iter205_admission_history_recovery/proof/raw/runtime_manifest.json": (
        "749bad5d40f7117ddcfffce314c1d9fd390ec8663ec2226d8cbd158dc41a942b"
    ),
    "experiments/iter206_iter205_admission_history_recovery/proof/pre_execution_publication_safety.json": (
        "a6dbc9f8372311e8fc9594fde4b12f090940b105419b6733d8a665ed7291d8d9"
    ),
    "scripts/ci_iter206_execute.sh": (
        "be8dbb154f46f98a5eab80e2053ab995aef7c23b16ca3bf259272124f2f725bb"
    ),
    "scripts/ci_iter206_smoke.sh": (
        "ed2fee3d23568b9cf3e4c819d4cefeda7fc7d4a24ed115248da2f036f3462259"
    ),
    "scripts/collect_iter206_execution.py": (
        "d9a58de1ec9518a49c17aeed035c1fd59327eaa7823913ea79775e2c17622226"
    ),
    "scripts/capture_iter206_runtime_host.py": (
        "7482ff44692ce37800eaa84b5e5d25baee12638df8abdf8c431c8c3697d3a11e"
    ),
    "scripts/prepare_iter206_output_directory.py": (
        "499269a66c86ec0106e66b9760b39e62811f4269e3574302f0b776e81a8a87ae"
    ),
    "scripts/publish_iter206_runtime_diagnostic.py": (
        "b5da5975452c069d9fd33a2c4bcc46816c345e1a18f473db3438eac98fe8ae6c"
    ),
    "scripts/adjudicate_iter206_admission_history_recovery.py": (
        "abf27c085d2a17d48c5e6fd2c1a668403d4f55c9388efd9d296f8570b983b05a"
    ),
    "scripts/run_iter206_admission_history_recovery_blind_judge.py": (
        "249070ebabe62dc551b6b455bfb935c7da761b78ca3fe2dc3ec9b9fe28190237"
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
    "expected_iter206_workflow_id",
    "iter206_all_event_count",
    "iter206_dispatch_count",
    "iter207_workflow_id",
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
    failures = validate_local_log_contract(text, label="iter207 runner")
    required = (
        'EXP="experiments/iter207_claim_integrity_and_admission_recovery"',
        'SOURCE_EXP="experiments/iter203_iter202_safety_recovery"',
        'LAUNCH_DIAGNOSTIC_LIMIT_BYTES=2162688',
        'ulimit -f "$((LAUNCH_DIAGNOSTIC_LIMIT_BYTES / 1024))"',
        'if [ "${GITHUB_RUN_ATTEMPT-}" != "1" ]',
        "scripts/build_iter207_runtime_manifest.py --check",
        "scripts/prepare_iter207_output_directory.py",
        "scripts/collect_iter207_execution.py smoke-check",
        "docker \"${create_args[@]}\"",
        '--entrypoint bash',
        '-v "$PWD/$SPECS/$stem.eval_script.sh:/specs/$stem.eval_script.sh:ro"',
        '-v "$PWD/$SPECS/$stem.spec.json:/specs/$stem.spec.json:ro"',
        '-v "$PWD/$SOLS/$stem.model.patch:/solutions/$stem.model.patch:ro"',
        '"scientific_container_launch_variant_cert"',
        '"scientific_container_launch_variant_behavior"',
        '"scientific_container_launch_gold_behavior"',
        '"incomplete_scientific_variant_evidence"',
        'scripts/publish_iter207_runtime_diagnostic.py',
        'scripts/collect_iter207_execution.py shard-receipt',
    )
    for fragment in required:
        if fragment not in text:
            failures.append(f"iter207 runner missing contract fragment: {fragment}")
    create_start = text.find("row_create_preflight()")
    create_end = text.find("marker_ordered()", create_start)
    create = text[create_start:create_end]
    if create_start < 0 or create_end < 0:
        failures.append("iter207 runner row-create preflight is not inspectable")
    else:
        if "docker start" in create or "$SCEN" in create or "scenario.py" in create:
            failures.append("row-create preflight may not start or mount a scenario")
        if "git apply" in create or "eval_script.sh:ro\"" not in create:
            failures.append("row-create preflight changed its inert certification-mount contract")
    if 'rm -f "$variant_tmp" "$gold_tmp"' in text or 'rm -f "$variant_tmp"' in text:
        failures.append("iter207 runner can delete the sole variant launch diagnostic")
    if text.count("retain_launch_diagnostic") < 7:
        failures.append("iter207 runner does not retain every declared failure phase")
    if text.count('ulimit -f "$((LAUNCH_DIAGNOSTIC_LIMIT_BYTES / 1024))"') != 2:
        failures.append("iter207 runner does not bound both create/run launch work files")
    if text.index("unset OPENAI_API_KEY ANTHROPIC_API_KEY") > text.index("docker "):
        failures.append("iter207 runner does not unset provider credentials before Docker")
    return failures


def validate_smoke_text(text: str) -> list[str]:
    failures = validate_local_log_contract(text, label="iter207 smoke")
    required = (
        "SMOKE_LIMIT_BYTES=65536",
        'ulimit -f "$((SMOKE_LIMIT_BYTES / 1024))"',
        'if [ "${GITHUB_RUN_ATTEMPT-}" != "1" ]',
        "plan_lines[0]",
        "--entrypoint bash",
        "TELOS_ITER207_LOG_DRIVER_SMOKE_OK",
        "scripts/capture_iter207_runtime_host.py --write",
        "scripts/publish_iter207_runtime_diagnostic.py",
        "scripts/prepare_iter207_output_directory.py",
        '"ordinal": 0',
        '"schema_version": "telos.iter207.no_science_smoke_receipt.v1"',
    )
    for fragment in required:
        if fragment not in text:
            failures.append(f"iter207 smoke missing contract fragment: {fragment}")
    if re.search(r"(?m)^\s*-v\s", text) or "$SOLS" in text or "$SCEN" in text:
        failures.append("iter207 global smoke exposes a scientific mount/input")
    if "git apply" in text or "/testbed" in text or "eval_script.sh" in text:
        failures.append("iter207 global smoke can execute a scientific command")
    if text.index("unset OPENAI_API_KEY ANTHROPIC_API_KEY") > text.index("docker "):
        failures.append("iter207 smoke does not unset provider credentials before Docker")
    return failures


def validate_workflow_text(text: str) -> list[str]:
    failures: list[str] = []
    input_block = re.search(
        r"(?ms)^    inputs:\n(?P<body>.*?)^concurrency:\n",
        text,
    )
    if input_block is None:
        failures.append("iter207 workflow dispatch inputs are not inspectable")
    else:
        input_names = set(
            re.findall(r"(?m)^      ([a-z0-9_]+):$", input_block.group("body"))
        )
        if input_names != {
            "expected_primary_sha",
            "expected_workflow_id",
            "expected_iter206_workflow_id",
            "expected_iter204_release_run_id",
            "expected_iter204_primary_run_id",
        }:
            failures.append("iter207 workflow dispatch input set differs")
    required = (
        "name: iter207-execute",
        "expected_workflow_id:",
        "expected_iter206_workflow_id:",
        "host pre-dispatch confirmed both histories empty",
        "expected_iter204_release_run_id:",
        "expected_iter204_primary_run_id:",
        'test "${GITHUB_RUN_ATTEMPT}" = "1"',
        '[[ "${EXPECTED_WORKFLOW_ID}" =~ ^[1-9][0-9]*$ ]]',
        '[[ "${EXPECTED_ITER206_WORKFLOW_ID}" =~ ^[1-9][0-9]*$ ]]',
        '[[ "${EXPECTED_ITER204_RELEASE_RUN_ID}" =~ ^[1-9][0-9]*$ ]]',
        '[[ "${EXPECTED_ITER204_PRIMARY_RUN_ID}" =~ ^[1-9][0-9]*$ ]]',
        'test "$(git rev-list --parents -n 1 "${EXPECTED_PRIMARY_SHA}" | wc -w | tr -d \' \')" = "3"',
        'test "$(git rev-parse refs/remotes/origin/master)" = "${EXPECTED_PRIMARY_SHA}"',
        'current.get("run_attempt") != 1',
        'current.get("run_number") != 1',
        "[row.get(\"id\") for row in iter207_runs] != [current_run_id]",
        "[row.get(\"id\") for row in iter207_dispatch_runs] != [current_run_id]",
        "iter207 all-event history must contain only the current run",
        "iter207 dispatch history must contain only the current run",
        'iter207_workflow.get("name") != "iter207-execute"',
        "expected_iter206_workflow_id in {",
        "iter206 workflow ID collides with iter204, iter205, or iter207",
        'iter206_workflow.get("name") != "iter206-execute"',
        'iter206_workflow.get("path") != ".github/workflows/iter206-execute.yml"',
        "if iter206_runs != [] or iter206_dispatch_runs != []:",
        "iter206 all-event and dispatch histories must remain empty",
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
        '"head_branch": "agent/iter207-claim-integrity-admission-recovery"',
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
        '"expected_iter206_workflow_id": expected_iter206_workflow_id',
        '"iter206_all_event_count": len(iter206_runs)',
        '"iter206_dispatch_count": len(iter206_dispatch_runs)',
        '"merge_first_parent": merge_first_parent',
        '"merge_second_parent": merge_second_parent',
        "scripts/validate_iter205_pre_dispatch_null.py",
        "scripts/validate_iter206_pre_publication_null.py",
        "telos.iter207.claim_integrity_and_admission_recovery.primary_ci_authorization.v1",
        "needs: [authorize, smoke]",
        "iter207-no-science-smoke-${{ github.run_id }}-attempt-1",
        "iter207-execution-run-${{ github.run_id }}-attempt-1-shard-",
        "iter207-execution-complete-${{ github.run_id }}-attempt-1",
        "proof/raw/smoke/*.diagnostic.log",
        "proof/raw/runtime_diagnostics/*.diagnostic.log",
    )
    for fragment in required:
        if fragment not in text:
            failures.append(f"iter207 workflow missing contract fragment: {fragment}")
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
                "iter207 workflow uses runner context in job-level env"
            )
    step_binding = (
        "      - name: Run iter207 execution shard\n"
        "        env:\n"
        "          TELOS_ITER207_SMOKE_RECEIPT: "
        "${{ runner.temp }}/iter207-smoke/smoke.receipt.json\n"
        "        run: bash scripts/ci_iter207_execute.sh"
    )
    if text.count(step_binding) != 1:
        failures.append("iter207 smoke receipt is not bound once in execution-step env")
    if text.count("TELOS_ITER207_SMOKE_RECEIPT:") != 1:
        failures.append("iter207 workflow has a duplicated smoke-receipt binding")
    if "rerun every job" in text or "github.run_attempt }}" in text:
        failures.append("iter207 workflow permits or names a later run attempt")
    if text.count("fetch-depth: 0") != 4:
        failures.append("iter207 workflow must use full history in exactly four jobs")
    if text.count("- name: Free disk") != 2:
        failures.append("iter207 workflow job steps are duplicated or missing")
    script = re.search(
        r"(?ms)^          python3 -I -S - <<'PY'\n(?P<body>.*?)^          PY$",
        text,
    )
    if script is None:
        failures.append("iter207 authorization Python is not inspectable")
    else:
        try:
            source = textwrap.dedent(script.group("body"))
            tree = ast.parse(source, filename="<iter207-authorize>", mode="exec")
        except SyntaxError as exc:
            failures.append(f"iter207 authorization Python is invalid: {exc}")
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
                failures.append("iter207 authorization receipt is not uniquely inspectable")
            else:
                keys = authorization_dicts[0].keys
                if any(
                    not isinstance(key, ast.Constant) or not isinstance(key.value, str)
                    for key in keys
                ):
                    failures.append("iter207 authorization receipt has a dynamic key")
                elif {key.value for key in keys} != AUTHORIZATION_KEYS:
                    failures.append("iter207 workflow authorization key set differs")
    return failures


def _normalize_iter207_shell(text: str) -> str:
    return (
        text.replace(
            "adjudicate_iter207_claim_integrity_and_admission_recovery",
            "adjudicate_iter206_admission_history_recovery",
        )
        .replace(
            "iter202_fixed_outputs_via_iter207_claim_integrity_and_admission_recovery",
            "iter202_fixed_outputs_via_iter206_admission_history_recovery",
        )
        .replace(
            "iter207_claim_integrity_and_admission_recovery",
            "iter206_iter205_admission_history_recovery",
        )
        .replace(
            "agent/iter207-claim-integrity-admission-recovery",
            "agent/iter206-iter205-admission-recovery",
        )
        .replace(
            "claim_integrity_and_admission_recovery",
            "admission_history_recovery",
        )
        .replace("claim-integrity/admission recovery", "admission-history recovery")
        .replace("ITER207", "ITER206")
        .replace("Iter207", "Iter206")
        .replace("iter207", "iter206")
        .replace(
            '_core.ADJUDICATION_SCHEMA = (\n'
            '    "telos.iter206.admission_history_recovery.adjudication.v1"\n'
            ')',
            '_core.ADJUDICATION_SCHEMA = '
            '"telos.iter206.admission_history_recovery.adjudication.v1"',
        )
        .replace(
            '_core.DIVERGENCE_SCHEMA = (\n'
            '    "telos.iter206.admission_history_recovery.divergence_candidates.v1"\n'
            ')',
            '_core.DIVERGENCE_SCHEMA = '
            '"telos.iter206.admission_history_recovery.divergence_candidates.v1"',
        )
    )


def _normalize_iter207_workflow(text: str) -> str:
    """Remove registered iter207 workflow deltas, then map identity to iter206."""

    input_delta = (
        "      expected_iter206_workflow_id:\n"
        "        description: Server-assigned active iter206 workflow ID observed only "
        "after the host pre-dispatch confirmed both histories empty\n"
        "        required: true\n"
        "        type: string\n"
    )
    authorization_assignment = (
        "          expected_iter206_workflow_id = int(\n"
        '              os.environ["EXPECTED_ITER206_WORKFLOW_ID"]\n'
        "          )\n"
    )
    iter206_history_delta = (
        "          if expected_iter206_workflow_id in {\n"
        "              314113289,\n"
        "              iter205_workflow_id,\n"
        "              expected_workflow_id,\n"
        "          }:\n"
        '              raise SystemExit("iter206 workflow ID collides with '
        'iter204, iter205, or iter207")\n'
        '          iter206_workflow = get(f"actions/workflows/'
        '{expected_iter206_workflow_id}")\n'
        "          if (\n"
        '              iter206_workflow.get("id") != expected_iter206_workflow_id\n'
        '              or iter206_workflow.get("name") != "iter206-execute"\n'
        '              or iter206_workflow.get("path") != '
        '".github/workflows/iter206-execute.yml"\n'
        '              or iter206_workflow.get("state") != "active"\n'
        "          ):\n"
        '              raise SystemExit("the exact iter206 workflow identity differs")\n'
        "          iter206_runs = one_page_workflow_runs(\n"
        '              f"actions/workflows/{expected_iter206_workflow_id}/runs"\n'
        "          )\n"
        "          iter206_dispatch_runs = one_page_workflow_runs(\n"
        '              f"actions/workflows/{expected_iter206_workflow_id}/runs",\n'
        '              event="workflow_dispatch",\n'
        "          )\n"
        "          if iter206_runs != [] or iter206_dispatch_runs != []:\n"
        '              raise SystemExit("iter206 all-event and dispatch histories '
        'must remain empty")\n\n'
    )
    normalized = text.replace(input_delta, "", 1)
    normalized = normalized.replace(
        "          EXPECTED_ITER206_WORKFLOW_ID: "
        "${{ inputs.expected_iter206_workflow_id }}\n",
        "",
    )
    normalized = normalized.replace(
        '          [[ "${EXPECTED_ITER206_WORKFLOW_ID}" =~ ^[1-9][0-9]*$ ]]\n',
        "",
        1,
    )
    normalized = normalized.replace(authorization_assignment, "", 1)
    normalized = normalized.replace(iter206_history_delta, "", 1)
    normalized = normalized.replace(
        "      - name: Verify exact iter206 pre-publication claim-integrity null\n"
        "        run: python3 -I -S scripts/validate_iter206_pre_publication_null.py\n",
        "",
        1,
    )
    normalized = normalized.replace(
        "          python3 -I -S scripts/validate_iter205_pre_dispatch_null.py\n",
        "",
    )
    normalized = normalized.replace(
        "          python3 -I -S scripts/validate_iter206_pre_publication_null.py\n",
        "",
    )
    for receipt_line in (
        '              "expected_iter206_workflow_id": expected_iter206_workflow_id,\n',
        '              "iter206_all_event_count": len(iter206_runs),\n',
        '              "iter206_dispatch_count": len(iter206_dispatch_runs),\n',
    ):
        normalized = normalized.replace(receipt_line, "", 1)
    normalized = _normalize_iter207_shell(normalized)
    return normalized.replace(
        "telos.iter206.admission_history_recovery.primary_ci_authorization.v1",
        "telos.iter206.primary_ci_authorization.v2",
        1,
    )


def validate_cross_contract_identity(
    overrides: dict[Path, str] | None = None,
) -> list[str]:
    failures: list[str] = []
    replacements = overrides or {}

    def source(path: Path) -> str:
        return replacements.get(path, path.read_text())

    for successor, predecessor in (
        (RUNNER, ROOT / "scripts/ci_iter206_execute.sh"),
        (SMOKE, ROOT / "scripts/ci_iter206_smoke.sh"),
        (HOST, ROOT / "scripts/capture_iter206_runtime_host.py"),
        (OUTPUT_DIRECTORY, ROOT / "scripts/prepare_iter206_output_directory.py"),
        (DIAGNOSTIC, ROOT / "scripts/publish_iter206_runtime_diagnostic.py"),
        (
            ROOT / "scripts/adjudicate_iter207_claim_integrity_and_admission_recovery.py",
            ROOT / "scripts/adjudicate_iter206_admission_history_recovery.py",
        ),
        (
            ROOT / "scripts/run_iter207_claim_integrity_and_admission_recovery_blind_judge.py",
            ROOT / "scripts/run_iter206_admission_history_recovery_blind_judge.py",
        ),
    ):
        if _normalize_iter207_shell(source(successor)) != source(predecessor):
            failures.append(
                f"{successor.name}: scientific runtime differs beyond iter207 identity"
            )
    if _normalize_iter207_workflow(source(WORKFLOW)) != source(
        ROOT / ".github/workflows/iter206-execute.yml"
    ):
        failures.append(
            "iter207 workflow differs from frozen iter206 beyond the registered "
            "claim-integrity/iter206-null/empty-history deltas"
        )
    collector = _normalize_iter207_shell(source(COLLECTOR))
    predecessor_collector = source(ROOT / "scripts/collect_iter206_execution.py")
    schema_blocks = {
        r"(?ms)^PRIMARY_CI_AUTHORIZATION_SCHEMA = \(\n.*?^\)\n": (
            'PRIMARY_CI_AUTHORIZATION_SCHEMA = '
            '"telos.iter206.primary_ci_authorization.v2"\n'
        ),
        r"(?ms)^RUNTIME_MANIFEST_SCHEMA = \(\n.*?^\)\n": (
            'RUNTIME_MANIFEST_SCHEMA = "telos.iter206.execution_runtime_recovery.v1"\n'
        ),
        r"(?ms)^SHARD_SCHEMA = \(\n.*?^\)\n": (
            'SHARD_SCHEMA = "telos.iter206.execution_shard_receipt.v1"\n'
        ),
        r"(?ms)^AGGREGATE_SCHEMA = \(\n.*?^\)\n": (
            'AGGREGATE_SCHEMA = "telos.iter206.execution_aggregate_receipt.v1"\n'
        ),
    }
    for pattern, replacement in schema_blocks.items():
        collector, count = re.subn(pattern, replacement, collector, count=1)
        if count != 1:
            failures.append("iter207 collector claim-integrity schema is not exact")
    exact_deltas = (
        (
            '    "expected_iter206_workflow_id",\n'
            '    "iter206_all_event_count",\n'
            '    "iter206_dispatch_count",\n'
        ),
        (
            "    expected_iter206_workflow_id = authorization.get(\n"
            '        "expected_iter206_workflow_id"\n'
            "    )\n"
        ),
        (
            "    if (\n"
            "        not _core._plain_int(expected_iter206_workflow_id)\n"
            "        or expected_iter206_workflow_id < 1\n"
            "        or expected_iter206_workflow_id in {314113289, 314141096}\n"
            '        or authorization.get("iter206_all_event_count") != 0\n'
            '        or authorization.get("iter206_dispatch_count") != 0\n'
            "    ):\n"
            "        raise ExecutionCollectionError(\n"
            '            f"{label} does not bind the exact empty iter206 workflow '
            'histories"\n'
            "        )\n"
        ),
    )
    for delta in exact_deltas:
        if collector.count(delta) != 1:
            failures.append(
                "iter207 collector exact authorization extension differs: not inspectable"
            )
        else:
            collector = collector.replace(delta, "", 1)
    collision_delta = (
        "        or iter206_workflow_id\n"
        "        in {314113289, 314141096, expected_iter206_workflow_id}\n"
    )
    predecessor_collision = (
        "        or iter206_workflow_id in {314113289, 314141096}\n"
    )
    if collector.count(collision_delta) != 1:
        failures.append(
            "iter207 collector workflow-ID collision extension differs: not inspectable"
        )
    else:
        collector = collector.replace(collision_delta, predecessor_collision, 1)
    if collector != predecessor_collector:
        failures.append(
            "iter207 collector differs from frozen iter206 beyond its exact "
            "claim-integrity/empty-history authorization extension"
        )
    try:
        from scripts import build_iter207_runtime_manifest as runtime
        from scripts import capture_iter207_runtime_host as host
        from scripts import collect_iter207_execution as collector
        from scripts import publish_iter207_runtime_diagnostic as diagnostic

        expected_workflow_ref = (
            "manfromnowhere143/telos/.github/workflows/"
            "iter207-execute.yml@refs/heads/master"
        )
        if {
            collector.CANONICAL_WORKFLOW_REF,
            host.CANONICAL_WORKFLOW_REF,
            diagnostic.CANONICAL_WORKFLOW_REF,
        } != {expected_workflow_ref}:
            failures.append("iter207 receipt producers bind different workflow identities")
        if collector.RUNTIME_MANIFEST_SCHEMA != runtime.SCHEMA:
            failures.append("iter207 collector/runtime manifest schemas differ")
        if (
            collector.AGGREGATE_RECEIPT_NAME
            != runtime.ITER207_AGGREGATE_RECEIPT_NAME
            or collector.AGGREGATE_SCHEMA
            != runtime.ITER207_AGGREGATE_RECEIPT_SCHEMA
            or collector.SHARD_SCHEMA != runtime.ITER207_SHARD_RECEIPT_SCHEMA
        ):
            failures.append("iter207 execution receipt identities drift across contracts")
        if collector.PRIMARY_CI_AUTHORIZATION_SCHEMA not in WORKFLOW.read_text():
            failures.append("iter207 workflow/collector authorization schemas differ")
        if collector.PRIMARY_CI_AUTHORIZATION_SCHEMA != (
            "telos.iter207.claim_integrity_and_admission_recovery."
            "primary_ci_authorization.v1"
        ):
            failures.append("iter207 claim-integrity authorization schema is not exact")
        if collector._core.AUTHORIZATION_KEYS != AUTHORIZATION_KEYS:
            failures.append("iter207 collector authorization key set differs")
    except (ImportError, AttributeError, OSError, RuntimeError) as exc:
        failures.append(f"iter207 cross-contract import failed: {exc}")
    for path in (RUNNER, SMOKE, COLLECTOR, DIAGNOSTIC, HOST):
        text = source(path)
        for stale in ("telos.iter205.", "_telos_iter205_", "iter205-execution-run-"):
            if stale in text:
                failures.append(f"{path.name}: stale receipt identity remains: {stale}")
    return failures


def validate_source_contract() -> list[str]:
    failures: list[str] = []
    for relative, expected in FROZEN_ITER206.items():
        path = ROOT / relative
        if not path.is_file() or path.is_symlink() or sha256(path) != expected:
            failures.append(f"frozen iter206 byte drift: {relative}")
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
        "shards bind different iter207 smoke receipts",
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
        '"expected_iter206_workflow_id"',
        '"iter206_all_event_count"',
        '"iter206_dispatch_count"',
        '"iter207_workflow_id"',
        '"merge_first_parent"',
        '"merge_second_parent"',
        'authorization.get("primary_ci_run_attempt") != 1',
        '"release_ci_head_sha"',
        '"release_ci_runs"',
        '"head_repository"',
        "_expected_iter204_admission_projection",
        "_git_merge_parents",
        "does not reproduce the exact-six iter204 admission digest",
        "does not bind the exact empty iter206 workflow histories",
        "does not match the checked-out iter207 merge parents",
        "release CI pair is incomplete",
        "Actions run and CI job identities are not exact and unique",
        "does not bind the exact-six iter207 admission contract",
    ):
        if fragment not in collector:
            failures.append(f"iter207 collector missing provenance fragment: {fragment}")
    builder = (ROOT / "scripts/build_iter207_runtime_manifest.py").read_text(
        encoding="utf-8"
    )
    if '"retry": "forbidden_advance_to_iter208_after_any_failure"' not in builder:
        failures.append("iter207 failure policy does not advance to iter208")
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
            failures.append(f"iter207 diagnostic publisher missing: {fragment}")
    host = HOST.read_text(encoding="utf-8")
    for fragment in (
        '"docker_client"',
        '"docker_server"',
        '"runner_image"',
        "CANONICAL_WORKFLOW_REF",
        'runner[key] != "unavailable"',
    ):
        if fragment not in host:
            failures.append(f"iter207 host capture missing: {fragment}")
    output_directory = OUTPUT_DIRECTORY.read_text(encoding="utf-8")
    for fragment in (
        'getattr(os, "O_NOFOLLOW", 0)',
        "dir_fd=descriptor",
        "os.listdir(descriptor)",
        "output directory already exists",
        "output directory is not empty",
    ):
        if fragment not in output_directory:
            failures.append(f"iter207 output-directory guard missing: {fragment}")
    return failures


def validate_all() -> list[str]:
    failures = validate_source_contract()
    try:
        from scripts import build_iter207_runtime_manifest as runtime
        from scripts import validate_iter205_pre_dispatch_null as iter205_null
        from scripts import validate_iter206_pre_publication_null as iter206_null
        from scripts import validate_iter207_publication_safety as publication

        iter205_null.validate()
        iter206_null.validate()
        failures.extend(runtime.validate_committed_manifest())
        expected_publication = publication.canonical_json_bytes(publication.build_audit())
        if publication.AUDIT.read_bytes() != expected_publication:
            failures.append("iter207 current publication-safety receipt differs")
    except (OSError, ValueError) as exc:
        failures.append(f"iter207 evidence guard failed: {exc}")
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
            print(
                f"iter207 claim-integrity/admission guard failed: {failure}",
                file=sys.stderr,
            )
        return 1
    print(
        "iter207 claim-integrity/admission guard: frozen iter206 source, both "
        "nulls, smoke, provenance, and closure pass"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
