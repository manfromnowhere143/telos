#!/usr/bin/env python3
"""Fail-closed evidence checks and defense-in-depth lint for iter226 scenarios.

Iter225 is a single-variable cross-model replication of iter223: same frozen
53-target cohort, same witnessing generator (``gpt-5.6-terra``) and same blind
judges, with only the solver model changed to ``gpt-5.4``. This guard therefore
also asserts the solver-model invariant on the solve summary, so a run that used
any model other than ``gpt-5.4`` fails closed.

AST inspection is deliberately conservative and is not a Python sandbox. The
independent locked-image Docker controls are the execution security boundary.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/iter226_cross_model_generalization_gpt54"
TARGETS = EXP / "proof/raw/solve_targets.json"
SOLUTIONS = EXP / "proof/raw/solutions"
SOLVE_SUMMARY = SOLUTIONS / "solve_summary.json"
SCENARIOS = EXP / "proof/raw/scenarios"
SUMMARY = SCENARIOS / "scenarios_summary.json"
RUNNER = ROOT / "scripts/ci_iter200_execute.sh"
WORKFLOW = ROOT / ".github/workflows/iter226-execute.yml"

TARGET_SCHEMA = "telos.iter202.solve_targets.v1"
SUMMARY_SCHEMA = "telos.iter200.scenarios_summary.v1"
SOLVE_SUMMARY_SCHEMA = "telos.iter200.solve_summary.v1"
# The scenario/witness generator is held constant at iter223's model; only the
# solver changes. Both invariants are enforced.
FROZEN_MODEL = "gpt-5.6-terra"
SOLVER_MODEL = "gpt-5.4"
INSTANCE_RE = re.compile(r"[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+")
SHA_RE = re.compile(r"[0-9a-f]{64}")
ATTEMPT_RE = re.compile(r"[0-9a-f]{32}")
MAX_SCENARIO_BYTES = 64 * 1024
MAX_AST_NODES = 2_000

SUMMARY_KEYS = {
    "checkpoint_schema",
    "differing_solutions",
    "estimated_spend_usd",
    "manifest",
    "model",
    "provider_calls",
    "scenarios",
    "schema_version",
}
MANIFEST_KEYS = {
    "no_src": {"instance_id", "status"},
    "no_scenario": {"instance_id", "provider_attempt_id", "status"},
    "provider_error": {"detail", "instance_id", "provider_attempt_id", "status"},
    "excluded_unsafe": {"instance_id", "provider_attempt_id", "scenario_sha256", "status", "unsafe_reason"},
    "scenario": {
        "func",
        "instance_id",
        "provider_attempt_id",
        "provider_response_sha256",
        "provider_usage",
        "repo",
        "scenario_sha256",
        "status",
    },
}

# Scenario programs need project imports and a small set of deterministic pure
# dependencies. This allowlist and the call checks below reject obvious unsafe
# constructions as defense in depth; transitive Python objects cannot be proven
# safe by static AST inspection, so the locked, isolated container remains the
# security boundary.
SAFE_IMPORT_ROOTS = {
    "collections",
    "contextlib",
    "copy",
    "dataclasses",
    "datetime",
    "decimal",
    "django",
    "docutils",
    "enum",
    "fractions",
    "functools",
    "itertools",
    "json",
    "math",
    "matplotlib",
    "mpl_toolkits",
    "numpy",
    "operator",
    "packaging",
    "pandas",
    "pprint",
    "pytest",
    "pytz",
    "re",
    "scipy",
    "sklearn",
    "sphinx",
    "statistics",
    "sympy",
    "textwrap",
    "time",
    "types",
    "typing",
    "uuid",
    "warnings",
    "xarray",
}
FORBIDDEN_IMPORT_ROOTS = {
    "asyncio",
    "builtins",
    "ctypes",
    "fcntl",
    "ftplib",
    "glob",
    "http",
    "importlib",
    "marshal",
    "multiprocessing",
    "os",
    "pathlib",
    "pickle",
    "pip",
    "pty",
    "requests",
    "resource",
    "runpy",
    "select",
    "shelve",
    "shutil",
    "signal",
    "socket",
    "ssl",
    "subprocess",
    "sys",
    "tempfile",
    "urllib",
    "webbrowser",
}
FORBIDDEN_CALL_NAMES = {
    "__import__",
    "breakpoint",
    "compile",
    "eval",
    "exec",
    "getattr",
    "globals",
    "help",
    "input",
    "locals",
    "open",
    "vars",
}
FORBIDDEN_CALL_ATTRIBUTES = {
    "Popen",
    "bind",
    "check_call",
    "check_output",
    "chmod",
    "chown",
    "connect",
    "create_connection",
    "execv",
    "execve",
    "fork",
    "hardlink_to",
    "listen",
    "mkdir",
    "mount",
    "open",
    "popen",
    "recv",
    "remove",
    "rename",
    "rmdir",
    "send",
    "socket",
    "spawn",
    "symlink",
    "system",
    "touch",
    "unlink",
    "urlopen",
    "write_bytes",
    "write_text",
}
FORBIDDEN_DUNDER_ATTRIBUTES = {
    "__bases__",
    "__builtins__",
    "__class__",
    "__closure__",
    "__code__",
    "__func__",
    "__globals__",
    "__loader__",
    "__mro__",
    "__self__",
    "__spec__",
    "__subclasses__",
}

REQUIRED_DOCKER_FLAGS = (
    "--network none",
    "--cap-drop ALL",
    "--security-opt no-new-privileges=true",
    "--pids-limit 1024",
    "--memory 10g",
    "--cpus 4",
    "--log-driver local",
    "--log-opt max-size=3m",
    "--log-opt max-file=1",
)
REQUIRED_EXECUTION_LIMITS = {
    "ITER202_CERT_TIMEOUT_SECONDS": "900",
    "ITER202_SCENARIO_TIMEOUT_SECONDS": "180",
    "ITER202_KILL_GRACE_SECONDS": "10",
    "ITER202_CERT_OUTPUT_LIMIT_BYTES": "2097152",
    "ITER202_SCENARIO_OUTPUT_LIMIT_BYTES": "262144",
}
ITER202_EXECUTION_SHARDS = 8


class SafetyError(ValueError):
    """A generated scenario evidence object is malformed or unsafe."""


def _no_duplicate_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SafetyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite_constant(value: str) -> None:
    raise SafetyError(f"non-standard JSON numeric constant: {value}")


def load_json_strict(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_bytes(),
            object_pairs_hook=_no_duplicate_object,
            parse_constant=_reject_nonfinite_constant,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SafetyError(f"cannot read strict JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SafetyError(f"JSON root must be an object: {path}")
    return value


def target_rows(path: Path = TARGETS) -> tuple[list[str], dict[str, str]]:
    data = load_json_strict(path)
    rows = data.get("targets")
    if (
        data.get("schema_version") != TARGET_SCHEMA
        or data.get("count") != 53
        or not isinstance(rows, list)
        or len(rows) != 53
    ):
        raise SafetyError("frozen iter226 target manifest is malformed")
    ids: list[str] = []
    repos: dict[str, str] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != {"instance_id", "repo"}:
            raise SafetyError(f"frozen target row {index} has malformed or extra fields")
        iid = row.get("instance_id")
        repo = row.get("repo")
        if (
            not isinstance(iid, str)
            or not INSTANCE_RE.fullmatch(iid)
            or not isinstance(repo, str)
            or not repo
        ):
            raise SafetyError(f"frozen target row {index} has invalid values")
        if iid in repos:
            raise SafetyError(f"frozen target manifest duplicates {iid}")
        ids.append(iid)
        repos[iid] = repo
    return ids, repos


def solve_summary_errors(
    targets_path: Path = TARGETS,
    solve_summary_path: Path = SOLVE_SUMMARY,
) -> list[str]:
    """Enforce the iter226 single-changed-variable invariant: solver model is gpt-5.4.

    Runs only once a solve summary exists; before the solve stage this returns no
    errors so the pre-registration commit passes.
    """

    if not solve_summary_path.exists():
        return []
    try:
        ids, _ = target_rows(targets_path)
    except SafetyError as exc:
        return [str(exc)]
    try:
        summary = load_json_strict(solve_summary_path)
    except SafetyError as exc:
        return [str(exc)]
    errors: list[str] = []
    if summary.get("schema_version") != SOLVE_SUMMARY_SCHEMA:
        errors.append("solve summary schema mismatch")
    if summary.get("solver_model") != SOLVER_MODEL:
        errors.append(f"solve summary solver_model is not the pre-registered {SOLVER_MODEL}")
    if summary.get("targets") != 53:
        errors.append("solve summary target count is not the frozen 53")
    manifest = summary.get("manifest")
    if not isinstance(manifest, list):
        return errors + ["solve summary manifest must be a list"]
    positions = set(ids)
    for index, row in enumerate(manifest):
        if not isinstance(row, dict):
            errors.append(f"solve manifest row {index} must be an object")
            continue
        iid = row.get("instance_id")
        if not isinstance(iid, str) or iid not in positions:
            errors.append(f"solve manifest row {index} is not a frozen target")
        if row.get("status") == "solution" and row.get("solver_model") != SOLVER_MODEL:
            errors.append(f"solve manifest row {index} solver_model is not {SOLVER_MODEL}")
    return errors


def _call_name(node: ast.expr) -> tuple[str | None, str | None]:
    if isinstance(node, ast.Name):
        return node.id, None
    if isinstance(node, ast.Attribute):
        root: ast.expr = node
        while isinstance(root, ast.Attribute):
            root = root.value
        return (root.id if isinstance(root, ast.Name) else None), node.attr
    return None, None


def _getattr_name_is_string_literal(node: ast.Call) -> bool:
    """getattr(obj, "literal", default) is static attribute access; computed names stay forbidden."""

    if node.keywords or len(node.args) < 2:
        return False
    name_arg = node.args[1]
    return isinstance(name_arg, ast.Constant) and isinstance(name_arg.value, str)


def scenario_ast_errors(source: str) -> list[str]:
    errors: list[str] = []
    try:
        tree = ast.parse(source, mode="exec")
    except (SyntaxError, ValueError) as exc:
        return [f"scenario is not valid Python: {exc}"]
    nodes = list(ast.walk(tree))
    if len(nodes) > MAX_AST_NODES:
        errors.append(f"scenario AST exceeds {MAX_AST_NODES} nodes")

    imported_aliases: dict[str, str] = {}
    result_marker = False
    print_calls = 0
    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                bound = alias.asname or root
                imported_aliases[bound] = root
                if root in FORBIDDEN_IMPORT_ROOTS or root not in SAFE_IMPORT_ROOTS:
                    errors.append(f"unsafe import root: {root}")
                if bound in FORBIDDEN_IMPORT_ROOTS:
                    errors.append(f"unsafe import alias: {bound}")
        elif isinstance(node, ast.ImportFrom):
            if node.level != 0 or not node.module:
                errors.append("relative or malformed imports are forbidden")
                continue
            root = node.module.split(".", 1)[0]
            for alias in node.names:
                bound = alias.asname or alias.name
                imported_aliases[bound] = root
                if alias.name == "*":
                    errors.append("wildcard imports are forbidden")
                if alias.name in FORBIDDEN_IMPORT_ROOTS or bound in FORBIDDEN_IMPORT_ROOTS:
                    errors.append(f"unsafe imported member or alias: {bound}")
            if root in FORBIDDEN_IMPORT_ROOTS or root not in SAFE_IMPORT_ROOTS:
                errors.append(f"unsafe import root: {root}")
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            errors.append("global/nonlocal state mutation is forbidden")
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            if node.id == "print":
                errors.append("shadowing print is forbidden")
        elif isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_DUNDER_ATTRIBUTES:
            errors.append(f"unsafe interpreter attribute: {node.attr}")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            if "RESULT=" in value:
                result_marker = True
            if (
                value.startswith(("/", "~/", "file://"))
                or re.search(r"(?:^|[^A-Za-z0-9_.])\.\.(?:[/\\]|$)", value)
            ):
                errors.append("absolute or parent-traversal path literal is forbidden")
        elif isinstance(node, ast.Call):
            root, attr = _call_name(node.func)
            if root == "print" and attr is None:
                print_calls += 1
            if root in FORBIDDEN_CALL_NAMES and attr is None:
                if root == "getattr" and _getattr_name_is_string_literal(node):
                    pass
                else:
                    errors.append(f"unsafe dynamic/builtin call: {root}")
            if imported_aliases.get(root or "") in FORBIDDEN_IMPORT_ROOTS:
                errors.append(f"call through unsafe import alias: {root}")
            if attr in FORBIDDEN_CALL_ATTRIBUTES:
                errors.append(f"unsafe process/network/filesystem call: {attr}")

    if print_calls < 1 or not result_marker:
        errors.append("scenario must print a literal RESULT= observable")
    return sorted(set(errors))


def validate_scenario_file(path: Path, expected_sha256: str) -> list[str]:
    errors: list[str] = []
    if path.is_symlink():
        return [f"{path.name}: scenario symlinks are forbidden"]
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return [f"cannot read scenario file {path.name}: {exc}"]
    if not raw or len(raw) > MAX_SCENARIO_BYTES:
        errors.append(f"{path.name}: scenario size is outside the safe bound")
        return errors
    if b"\x00" in raw or b"\r" in raw:
        errors.append(f"{path.name}: NUL/CR bytes are forbidden")
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        errors.append(f"{path.name}: scenario must have exactly one terminal LF")
        payload = raw.rstrip(b"\n")
    else:
        payload = raw[:-1]
    actual = hashlib.sha256(payload).hexdigest()
    if actual != expected_sha256:
        errors.append(f"{path.name}: scenario summary hash mismatch")
    try:
        source = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        errors.append(f"{path.name}: scenario is not UTF-8: {exc}")
        return errors
    errors.extend(f"{path.name}: {error}" for error in scenario_ast_errors(source))
    return errors


def scenario_state_errors(
    targets_path: Path = TARGETS,
    scenario_dir: Path = SCENARIOS,
) -> tuple[str, list[str]]:
    try:
        ids, repos = target_rows(targets_path)
    except SafetyError as exc:
        return "invalid", [str(exc)]
    summary_path = scenario_dir / "scenarios_summary.json"
    if scenario_dir.is_symlink():
        return "invalid", ["iter226 scenario directory may not be a symlink"]
    actual_scripts = set(scenario_dir.glob("*.py")) if scenario_dir.is_dir() else set()
    if not summary_path.exists():
        if actual_scripts:
            return "invalid", ["scenario scripts exist without scenarios_summary.json"]
        return "no-scenarios-yet", []
    if summary_path.is_symlink() or not summary_path.is_file():
        return "invalid", ["scenarios_summary.json is not a regular file"]

    try:
        summary = load_json_strict(summary_path)
    except SafetyError as exc:
        return "invalid", [str(exc)]
    errors: list[str] = []
    if set(summary) != SUMMARY_KEYS:
        errors.append("scenario summary has malformed or extra top-level fields")
    if summary.get("schema_version") != SUMMARY_SCHEMA:
        errors.append("scenario summary schema mismatch")
    if summary.get("model") != FROZEN_MODEL:
        errors.append("scenario summary model is not the held-constant witness generator")
    if summary.get("checkpoint_schema") != {
        "finished": "telos.iter226.provider_attempt.finished.v1",
        "started": "telos.iter226.provider_attempt.started.v1",
    }:
        errors.append("scenario summary checkpoint schema is not frozen")
    manifest = summary.get("manifest")
    provider_calls = summary.get("provider_calls")
    scenario_count = summary.get("scenarios")
    differing = summary.get("differing_solutions")
    spend = summary.get("estimated_spend_usd")
    if not isinstance(manifest, list):
        errors.append("scenario summary manifest must be a list")
        manifest = []
    for label, value, ceiling in (
        ("provider_calls", provider_calls, 53),
        ("scenarios", scenario_count, 53),
        ("differing_solutions", differing, 53),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= ceiling:
            errors.append(f"scenario summary {label} is invalid")
    if (
        isinstance(spend, bool)
        or not isinstance(spend, (int, float))
        or not 0 <= float(spend) <= 15.0
    ):
        errors.append("scenario summary estimated_spend_usd is invalid")

    positions = {iid: index for index, iid in enumerate(ids)}
    last_position = -1
    seen: set[str] = set()
    expected_files: dict[Path, str] = {}
    attempted = 0
    scenario_rows = 0
    for index, row in enumerate(manifest):
        label = f"scenario manifest row {index}"
        if not isinstance(row, dict):
            errors.append(f"{label} must be an object")
            continue
        status = row.get("status")
        expected_keys = MANIFEST_KEYS.get(status)
        if expected_keys is None or set(row) != expected_keys:
            errors.append(f"{label} has unknown status or malformed/extra fields")
            continue
        iid = row.get("instance_id")
        if not isinstance(iid, str) or iid not in positions:
            errors.append(f"{label} is not indexed by the frozen target manifest")
            continue
        if iid in seen:
            errors.append(f"scenario summary duplicates {iid}")
        seen.add(iid)
        if positions[iid] <= last_position:
            errors.append("scenario manifest order differs from frozen target order")
        last_position = positions[iid]
        if status != "no_src":
            attempted += 1
            attempt_id = row.get("provider_attempt_id")
            if not isinstance(attempt_id, str) or not ATTEMPT_RE.fullmatch(attempt_id):
                errors.append(f"{label} provider_attempt_id is invalid")
        if status == "scenario":
            scenario_rows += 1
            digest = row.get("scenario_sha256")
            response_digest = row.get("provider_response_sha256")
            if not isinstance(digest, str) or not SHA_RE.fullmatch(digest):
                errors.append(f"{label} scenario_sha256 is invalid")
                continue
            if not isinstance(response_digest, str) or not SHA_RE.fullmatch(response_digest):
                errors.append(f"{label} provider response hash is invalid")
            if row.get("repo") != repos[iid]:
                errors.append(f"{label} repository does not match frozen target")
            if not isinstance(row.get("func"), str) or not row["func"]:
                errors.append(f"{label} function locator is invalid")
            if not isinstance(row.get("provider_usage"), dict):
                errors.append(f"{label} provider usage must be an object")
            expected_files[scenario_dir / f"{iid}.scenario.py"] = digest
        elif status == "provider_error":
            if not isinstance(row.get("detail"), str):
                errors.append(f"{label} provider error detail is invalid")
        elif status == "excluded_unsafe":
            digest = row.get("scenario_sha256")
            if not isinstance(digest, str) or not SHA_RE.fullmatch(digest):
                errors.append(f"{label} excluded scenario_sha256 is invalid")
            if not isinstance(row.get("unsafe_reason"), str) or not row["unsafe_reason"]:
                errors.append(f"{label} excluded unsafe_reason is invalid")

    if provider_calls != attempted:
        errors.append("scenario provider_calls does not match attempted manifest rows")
    if scenario_count != scenario_rows:
        errors.append("scenario count does not match scenario manifest rows")
    if actual_scripts != set(expected_files):
        missing = sorted(path.name for path in set(expected_files) - actual_scripts)
        extra = sorted(path.name for path in actual_scripts - set(expected_files))
        errors.append(f"scenario file set mismatch; missing={missing}, extra={extra}")
    for path, digest in expected_files.items():
        if path.is_file():
            errors.extend(validate_scenario_file(path, digest))
    return ("valid" if not errors else "invalid"), errors


def runner_safety_errors(text: str) -> list[str]:
    errors: list[str] = []
    # iter226 runs the same generic provenance-checked execution path as iter223/iter224. It
    # requires the runner to inspect real image provenance and to enforce the shard contract;
    # the iter202 immutable image lock is scoped to iter202 and is not required here.
    if 'IMAGE_PROVENANCE_INSPECTION_FAIL' not in text:
        errors.append("runner does not fail closed on missing image provenance")
    if 'image_id" =~ ^sha256:[0-9a-f]{64}$' not in text:
        errors.append("runner does not verify the Docker image id digest form")
    shard_contract = (
        'SHARD_INDEX_RAW="${TELOS_NAT_SHARD_INDEX-0}"',
        'SHARD_COUNT_RAW="${TELOS_NAT_SHARD_COUNT-1}"',
        'if ! validate_experiment_shard_config "$NAT_EXP" "$SHARD_INDEX_RAW" "$SHARD_COUNT_RAW"; then',
        '(( ordinal % SHARD_COUNT == SHARD_INDEX ))',
        'for ordinal in "${!ALL_IIDS[@]}"; do',
    )
    if any(text.count(fragment) != 1 for fragment in shard_contract):
        errors.append("runner shard-selection contract is missing or duplicated")
    return errors


def workflow_safety_errors(text: str) -> list[str]:
    errors: list[str] = []
    # iter226's execution workflow runs the corrected safety guard before execution, drives
    # the generic execution script under the iter226 experiment, shards eight ways, and
    # uploads per-shard evidence. Collection and adjudication run locally after download.
    safety = text.find("python3 scripts/validate_iter226_scenario_safety.py")
    execute = text.find("bash scripts/ci_iter200_execute.sh")
    if safety < 0 or execute < 0:
        errors.append("iter226 workflow is missing the safety guard or the execution command")
    elif safety > execute:
        errors.append("iter226 workflow must run the safety guard before execution")
    required = (
        "TELOS_NAT_EXP: iter226_cross_model_generalization_gpt54",
        "shard: [0, 1, 2, 3, 4, 5, 6, 7]",
        "TELOS_NAT_SHARD_COUNT: 8",
        "TELOS_NAT_SHARD_INDEX: ${{ matrix.shard }}",
        "fail-fast: false",
        "upload-artifact",
        "if-no-files-found: error",
    )
    for fragment in required:
        if fragment not in text:
            errors.append(f"iter226 workflow is missing: {fragment}")
    if "if: always()" in text or "continue-on-error:" in text:
        errors.append("iter226 workflow must not weaken failure semantics")
    return errors


def main() -> int:
    status, errors = scenario_state_errors()
    errors.extend(solve_summary_errors())
    try:
        runner_text = RUNNER.read_text()
        workflow_text = WORKFLOW.read_text()
    except OSError as exc:
        errors.append(f"cannot inspect iter226 execution surfaces: {exc}")
    else:
        errors.extend(runner_safety_errors(runner_text))
        errors.extend(workflow_safety_errors(workflow_text))
    if errors:
        for error in errors:
            print(f"iter226 scenario safety error: {error}", file=sys.stderr)
        return 1
    if status == "no-scenarios-yet":
        print("iter226 scenario safety: no-scenarios-yet (explicit empty pre-provider state)")
    else:
        print("iter226 scenario safety: generated scenarios are indexed, hash-bound, and AST-safe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
