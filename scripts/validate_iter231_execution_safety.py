#!/usr/bin/env python3
"""Fail-closed evidence checks and defense-in-depth lint for the iter231 execution oracle.

Iter231 runs committed gold-free exercises against certified candidate patches in pinned SWE-bench
images. This guard enforces the pre-registered acceptance bars that can be checked offline:

1. the frozen iter230 benchmark sha is unchanged and its 13/54 denominators hold;
2. every benchmark row has exactly one exercise manifest entry, and every committed exercise is
   hash-bound and AST-safe under the corrected iter223 safety instrument;
3. no ``excluded_unsafe`` exercise is committed (executing one is a pre-registered falsifier);
4. the executor never mounts a gold patch, a hidden test, or the gold-differential witness;
5. the executor carries the container security flags, the bounded timeouts, the shard contract, and
   the wall-clock row ceiling that bounds the reproducible container-hang mode;
6. the workflow runs this guard before execution and shards eight ways without weakened failure
   semantics.

AST inspection is deliberately conservative and is not a Python sandbox. The isolated container
controls are the execution security boundary.
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
sys.path.insert(0, str(ROOT))

from scripts.validate_iter223_scenario_safety import scenario_ast_errors  # noqa: E402

EXP = ROOT / "experiments/iter231_gold_free_execution_oracle"
EVAL_SET = ROOT / "experiments/iter230_gold_free_detector_natural/proof/raw/eval_set.json"
EXERCISES = EXP / "proof/raw/exercises"
SUMMARY = EXERCISES / "exercises_summary.json"
RUNNER = ROOT / "scripts/ci_iter231_execute.sh"
WORKFLOW = ROOT / ".github/workflows/iter231-execute.yml"
GENERATOR = ROOT / "scripts/run_iter231_exercises.py"

# Acceptance bar 1. The benchmark is reused from iter230 unchanged.
FROZEN_EVAL_SET_SHA256 = "10dc898c3cdc6026aaedc57d469e546b279a982df3772ba3388c1dfb515b8928"
EVAL_SET_SCHEMA = "telos.iter230.natural_detector_eval.v1"
SUMMARY_SCHEMA = "telos.iter231.exercises_summary.v1"
FROZEN_GENERATOR_MODEL = "gpt-5.6-terra"
POSITIVES = 13
NEGATIVES = 54

INSTANCE_RE = re.compile(r"[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+")
RUN_RE = re.compile(r"[A-Za-z0-9_]+")
SHA_RE = re.compile(r"[0-9a-f]{64}")
MAX_EXERCISE_BYTES = 64 * 1024

MANIFEST_KEYS = {
    "no_exercise": {"instance_id", "label", "run", "status"},
    "provider_error": {"detail", "instance_id", "label", "run", "status"},
    "excluded_unsafe": {
        "exercise_sha256", "instance_id", "label", "run", "status", "unsafe_reason",
    },
    "exercise": {
        "exercise_sha256", "instance_id", "label", "provider_response_sha256", "repo", "run",
        "status",
    },
}
SUMMARY_KEYS = {
    "schema_version", "generator_model", "items", "exercises", "excluded_unsafe", "manifest",
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
    "--log-opt compress=false",
)
REQUIRED_EXECUTION_LIMITS = {
    "ITER231_APPLY_TIMEOUT_SECONDS": "120",
    "ITER231_EXERCISE_TIMEOUT_SECONDS": "180",
    "ITER231_KILL_GRACE_SECONDS": "10",
    "ITER231_EXERCISE_OUTPUT_LIMIT_BYTES": "262144",
    "ITER231_ROW_CEILING_SECONDS": "1200",
}
# The oracle container sees exactly two things: the candidate patch and the gold-free exercise.
# Any other mount could show it an accepted fix or a hidden test, a pre-registered falsifier. The
# check is an allowlist over real `-v` mount lines rather than a substring blacklist, so the files
# stay free to *describe* what they exclude without tripping their own guard.
ALLOWED_MOUNT_TARGETS = ("/telos/candidate.patch:ro", "/telos/exercise.py:ro")
MOUNT_RE = re.compile(r"^\s*-v\s+(?P<spec>\S+)", re.MULTILINE)
# Evidence a gold-free stage may never name in code (comments and docstrings are exempt: saying
# "we never read the gold patch" is honesty, not a leak).
FORBIDDEN_CODE_FRAGMENTS = (".gold.", "gold_patch", "eval_script", "witness", "PASS_TO_PASS")
ITER231_EXECUTION_SHARDS = 8


class SafetyError(ValueError):
    """An iter231 oracle evidence object is malformed or unsafe."""


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


def benchmark_rows(path: Path = EVAL_SET) -> list[dict[str, Any]]:
    """Return the ordered 67-row benchmark, failing closed if the frozen sha moved."""

    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise SafetyError(f"cannot read frozen benchmark: {exc}") from exc
    if hashlib.sha256(raw).hexdigest() != FROZEN_EVAL_SET_SHA256:
        raise SafetyError("frozen iter230 benchmark sha changed")
    data = load_json_strict(path)
    if data.get("schema_version") != EVAL_SET_SCHEMA:
        raise SafetyError("benchmark schema mismatch")
    positives = data.get("positives")
    negatives = data.get("negatives")
    if not isinstance(positives, list) or len(positives) != POSITIVES:
        raise SafetyError(f"benchmark positive denominator is not the frozen {POSITIVES}")
    if not isinstance(negatives, list) or len(negatives) != NEGATIVES:
        raise SafetyError(f"benchmark negative denominator is not the frozen {NEGATIVES}")
    if data.get("positive_count") != POSITIVES or data.get("negative_count") != NEGATIVES:
        raise SafetyError("benchmark declared counts disagree with its rows")
    rows = [dict(row, label="certified_yet_wrong") for row in positives]
    rows += [dict(row, label="certified_correct") for row in negatives]
    for index, row in enumerate(rows):
        iid = row.get("instance_id")
        run = row.get("run")
        if not isinstance(iid, str) or not INSTANCE_RE.fullmatch(iid):
            raise SafetyError(f"benchmark row {index} has an unsafe instance id")
        if not isinstance(run, str) or not RUN_RE.fullmatch(run):
            raise SafetyError(f"benchmark row {index} has an unsafe run id")
    return rows


def validate_exercise_file(path: Path, expected_sha256: str) -> list[str]:
    errors: list[str] = []
    if path.is_symlink():
        return [f"{path.name}: exercise symlinks are forbidden"]
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return [f"cannot read exercise file {path.name}: {exc}"]
    if not raw or len(raw) > MAX_EXERCISE_BYTES:
        return [f"{path.name}: exercise size is outside the safe bound"]
    if b"\x00" in raw or b"\r" in raw:
        errors.append(f"{path.name}: NUL/CR bytes are forbidden")
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        errors.append(f"{path.name}: exercise must have exactly one terminal LF")
        payload = raw.rstrip(b"\n")
    else:
        payload = raw[:-1]
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        errors.append(f"{path.name}: exercise summary hash mismatch")
    try:
        source = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        return errors + [f"{path.name}: exercise is not UTF-8: {exc}"]
    errors.extend(f"{path.name}: {error}" for error in scenario_ast_errors(source))
    return errors


def exercise_state_errors(
    eval_path: Path = EVAL_SET,
    exercise_dir: Path = EXERCISES,
) -> tuple[str, list[str]]:
    try:
        rows = benchmark_rows(eval_path)
    except SafetyError as exc:
        return "invalid", [str(exc)]
    summary_path = exercise_dir / "exercises_summary.json"
    if exercise_dir.is_symlink():
        return "invalid", ["iter231 exercise directory may not be a symlink"]
    actual_scripts = set(exercise_dir.glob("*.py")) if exercise_dir.is_dir() else set()
    if not summary_path.exists():
        if actual_scripts:
            return "invalid", ["exercise scripts exist without exercises_summary.json"]
        return "no-exercises-yet", []
    if summary_path.is_symlink() or not summary_path.is_file():
        return "invalid", ["exercises_summary.json is not a regular file"]

    try:
        summary = load_json_strict(summary_path)
    except SafetyError as exc:
        return "invalid", [str(exc)]
    errors: list[str] = []
    if set(summary) != SUMMARY_KEYS:
        errors.append("exercise summary has malformed or extra top-level fields")
    if summary.get("schema_version") != SUMMARY_SCHEMA:
        errors.append("exercise summary schema mismatch")
    if summary.get("generator_model") != FROZEN_GENERATOR_MODEL:
        errors.append("exercise summary generator is not the frozen gold-free generator")
    if summary.get("items") != len(rows):
        errors.append("exercise summary item count does not match the benchmark denominator")

    manifest = summary.get("manifest")
    if not isinstance(manifest, list):
        return "invalid", errors + ["exercise summary manifest must be a list"]
    if len(manifest) != len(rows):
        errors.append("exercise manifest does not cover every benchmark row")

    positions = {(row["run"], row["instance_id"]): index for index, row in enumerate(rows)}
    labels = {(row["run"], row["instance_id"]): row["label"] for row in rows}
    seen: set[tuple[str, str]] = set()
    expected_files: dict[Path, str] = {}
    last_position = -1
    exercise_rows = 0
    excluded_rows = 0
    for index, row in enumerate(manifest):
        label = f"exercise manifest row {index}"
        if not isinstance(row, dict):
            errors.append(f"{label} must be an object")
            continue
        status = row.get("status")
        expected_keys = MANIFEST_KEYS.get(status)
        if expected_keys is None or set(row) != expected_keys:
            errors.append(f"{label} has unknown status or malformed/extra fields")
            continue
        key = (row.get("run"), row.get("instance_id"))
        if key not in positions:
            errors.append(f"{label} is not indexed by the frozen benchmark")
            continue
        if key in seen:
            errors.append(f"exercise summary duplicates {key}")
        seen.add(key)
        if positions[key] <= last_position:
            errors.append("exercise manifest order differs from frozen benchmark order")
        last_position = positions[key]
        if row.get("label") != labels[key]:
            errors.append(f"{label} label disagrees with the frozen benchmark")

        stem = f"{key[0]}__{key[1].replace('/', '__')}"
        if status == "exercise":
            exercise_rows += 1
            digest = row.get("exercise_sha256")
            response_digest = row.get("provider_response_sha256")
            if not isinstance(digest, str) or not SHA_RE.fullmatch(digest):
                errors.append(f"{label} exercise_sha256 is invalid")
                continue
            if not isinstance(response_digest, str) or not SHA_RE.fullmatch(response_digest):
                errors.append(f"{label} provider response hash is invalid")
            if not isinstance(row.get("repo"), str) or not row["repo"]:
                errors.append(f"{label} repository is invalid")
            expected_files[exercise_dir / f"{stem}.exercise.py"] = digest
        elif status == "excluded_unsafe":
            excluded_rows += 1
            digest = row.get("exercise_sha256")
            if not isinstance(digest, str) or not SHA_RE.fullmatch(digest):
                errors.append(f"{label} excluded exercise_sha256 is invalid")
            if not isinstance(row.get("unsafe_reason"), str) or not row["unsafe_reason"]:
                errors.append(f"{label} excluded unsafe_reason is invalid")
            # A pre-registered falsifier: an unsafe exercise is never committed and never executed.
            if (exercise_dir / f"{stem}.exercise.py").exists():
                errors.append(f"{label} excluded_unsafe exercise is committed on disk")
        elif status == "provider_error":
            if not isinstance(row.get("detail"), str):
                errors.append(f"{label} provider error detail is invalid")

    if summary.get("exercises") != exercise_rows:
        errors.append("exercise summary count does not match its exercise manifest rows")
    if summary.get("excluded_unsafe") != excluded_rows:
        errors.append("exercise summary excluded_unsafe count does not match its manifest rows")
    if actual_scripts != set(expected_files):
        missing = sorted(path.name for path in set(expected_files) - actual_scripts)
        extra = sorted(path.name for path in actual_scripts - set(expected_files))
        errors.append(f"exercise file set mismatch; missing={missing}, extra={extra}")
    for path, digest in expected_files.items():
        if path.is_file():
            errors.extend(validate_exercise_file(path, digest))
    return ("valid" if not errors else "invalid"), errors


def runner_safety_errors(text: str) -> list[str]:
    """The executor must be gold-free, isolated, bounded, sharded, and hang-proof."""

    errors: list[str] = []
    for flag in REQUIRED_DOCKER_FLAGS:
        if flag not in text:
            errors.append(f"executor is missing container isolation flag: {flag}")
    for name, value in REQUIRED_EXECUTION_LIMITS.items():
        if f"{name}={value}" not in text:
            errors.append(f"executor does not pin {name}={value}")
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    mounts = [match.group("spec") for match in MOUNT_RE.finditer(code)]
    if not mounts:
        errors.append("executor declares no container mounts to check")
    for raw_spec in mounts:
        spec = raw_spec.strip("\"'")
        if not spec.endswith(ALLOWED_MOUNT_TARGETS):
            errors.append(f"executor mounts evidence outside the gold-free allowlist: {spec}")
    for fragment in FORBIDDEN_CODE_FRAGMENTS:
        if fragment in code:
            errors.append(f"executor code references gold/hidden-test evidence: {fragment}")
    if f'FROZEN_EVAL_SET_SHA256="{FROZEN_EVAL_SET_SHA256}"' not in text:
        errors.append("executor does not pin the frozen benchmark sha")
    if "IMAGE_PROVENANCE_INSPECTION_FAIL" not in text:
        errors.append("executor does not fail closed on missing image provenance")
    if 'image_id" =~ ^sha256:[0-9a-f]{64}$' not in text:
        errors.append("executor does not verify the Docker image id digest form")
    if "validate_iter231_execution_safety.py" not in text:
        errors.append("executor does not run the safety instrument before execution")
    # The reproducible-hang guard: an outer wall-clock ceiling plus per-row start/end stamps the
    # straggler monitor reads. Shard-count alone is not trusted.
    if "ROW_CEILING_EXCEEDED" not in text or "ITER231_ROW_CEILING_SECONDS}s" not in text:
        errors.append("executor lacks the bounded wall-clock row ceiling")
    for marker in ("ROW_START stem=", "ROW_END stem="):
        if marker not in text:
            errors.append(f"executor does not emit the straggler stamp: {marker}")
    if "telos.iter231.shard_progress.v1" not in text:
        errors.append("executor does not emit shard progress heartbeats")
    shard_contract = (
        'SHARD_INDEX_RAW="${TELOS_ITER231_SHARD_INDEX-0}"',
        'SHARD_COUNT_RAW="${TELOS_ITER231_SHARD_COUNT-1}"',
        'if ! validate_shard_config "$SHARD_INDEX_RAW" "$SHARD_COUNT_RAW"; then',
        "(( ordinal % SHARD_COUNT == SHARD_INDEX ))",
    )
    if any(text.count(fragment) != 1 for fragment in shard_contract):
        errors.append("executor shard-selection contract is missing or duplicated")
    return errors


def _code_strings(text: str) -> list[str]:
    """Every string literal in the module except docstrings.

    Docstrings are where a gold-free stage *documents* what it refuses to read; scanning them would
    punish the honesty note rather than a leak.
    """

    tree = ast.parse(text)
    docstrings = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    }
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
    ]


def generator_safety_errors(text: str) -> list[str]:
    """The exercise generator must remain gold-free at the prompt."""

    errors: list[str] = []
    try:
        literals = _code_strings(text)
    except SyntaxError as exc:
        return [f"generator is not valid Python: {exc}"]
    joined = "\n".join(literals)
    if "do NOT assert a specific correct value" not in joined:
        errors.append("generator prompt no longer forbids asserting a gold-derived value")
    for fragment in FORBIDDEN_CODE_FRAGMENTS:
        if fragment in joined:
            errors.append(f"generator references gold/hidden-test evidence: {fragment}")
    return errors


def workflow_safety_errors(text: str) -> list[str]:
    errors: list[str] = []
    safety = text.find("python3 scripts/validate_iter231_execution_safety.py")
    execute = text.find("bash scripts/ci_iter231_execute.sh")
    if safety < 0 or execute < 0:
        errors.append("iter231 workflow is missing the safety guard or the execution command")
    elif safety > execute:
        errors.append("iter231 workflow must run the safety guard before execution")
    required = (
        f"shard: [{', '.join(str(index) for index in range(ITER231_EXECUTION_SHARDS))}]",
        f"TELOS_ITER231_SHARD_COUNT: {ITER231_EXECUTION_SHARDS}",
        "TELOS_ITER231_SHARD_INDEX: ${{ matrix.shard }}",
        "fail-fast: false",
        "upload-artifact",
        "if-no-files-found: error",
    )
    for fragment in required:
        if fragment not in text:
            errors.append(f"iter231 workflow is missing: {fragment}")
    if "if: always()" in text or "continue-on-error:" in text:
        errors.append("iter231 workflow must not weaken failure semantics")
    return errors


def main() -> int:
    status, errors = exercise_state_errors()
    for path, checker, label in (
        (RUNNER, runner_safety_errors, "executor"),
        (GENERATOR, generator_safety_errors, "generator"),
        (WORKFLOW, workflow_safety_errors, "workflow"),
    ):
        try:
            text = path.read_text()
        except OSError as exc:
            errors.append(f"cannot inspect iter231 {label}: {exc}")
        else:
            errors.extend(checker(text))
    if errors:
        for error in errors:
            print(f"iter231 execution safety error: {error}", file=sys.stderr)
        return 1
    if status == "no-exercises-yet":
        print("iter231 execution safety: no-exercises-yet (explicit empty pre-generator state)")
    else:
        print(
            "iter231 execution safety: exercises are indexed, hash-bound, and AST-safe; the "
            "executor is gold-free, isolated, bounded, and sharded"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
