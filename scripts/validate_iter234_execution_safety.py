#!/usr/bin/env python3
"""Fail-closed guard for iter234: the author is blind, the executor is not, and that asymmetry is the design.

Iter234 deliberately mounts the gold patch into the container, because the pre-registered gold-validated arm
needs to know whether a test passes on a correct implementation. That is not a leak. The integrity condition
is **authoring blindness**: the model that wrote the test saw only the issue text.

So this guard checks two different things about two different stages:

* **Author stage** (``run_iter234_tests.py``) - the prompt template has no field that could interpolate a
  patch, and no code path reads a gold patch, a witness, or a label. This is the bar that makes the
  experiment mean anything.
* **Executor stage** (``ci_iter234_execute.sh``) - isolation flags, bounded timeouts, the shard contract, the
  wall-clock row ceiling, and an allowlist over mounts that permits gold but nothing else.

Plus the usual evidence checks: every committed test is hash-bound and passes the iter232 stage A validity
gate.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.validate_iter232_exercise_validity import exercise_errors  # noqa: E402

EXP = ROOT / "experiments/iter234_issue_only_consequence_tests"
TESTS = EXP / "proof/raw/tests"
SUMMARY = TESTS / "tests_summary.json"
AUTHOR = ROOT / "scripts/run_iter234_tests.py"
RUNNER = ROOT / "scripts/ci_iter234_execute.sh"
WORKFLOW = ROOT / ".github/workflows/iter234-execute.yml"

SCHEMA = "telos.iter234.tests_summary.v1"
SHA_RE = re.compile(r"[0-9a-f]{64}")
MAX_TEST_BYTES = 64 * 1024
AUTHORS = ("openai", "anthropic", "google")

ALLOWED_MOUNT_SUFFIXES = (
    "/telos/candidate.patch:ro",
    "/telos/gold.patch:ro",
    ".test.py:/telos/test_${author}.py:ro",
)
# Match only real bind mounts: a source path, a container path, and an :ro suffix. A bare
# `-v` also appears on `git apply -v`, and a looser pattern captured that plus trailing shell
# syntax and reported both as unallowlisted mounts.
MOUNT_RE = re.compile(r"""-v\s+["']?(?P<spec>[^"'\s]+:/[^"'\s]+:ro)["']?""")
REQUIRED_DOCKER_FLAGS = (
    "--network none", "--cap-drop ALL", "--security-opt no-new-privileges=true",
    "--pids-limit 1024", "--memory 10g", "--cpus 4",
    "--log-driver local", "--log-opt max-size=3m", "--log-opt max-file=1",
    "--log-opt compress=false",
)
REQUIRED_LIMITS = {
    "ITER234_APPLY_TIMEOUT_SECONDS": "120",
    "ITER234_TEST_TIMEOUT_SECONDS": "180",
    "ITER234_KILL_GRACE_SECONDS": "10",
    "ITER234_OUTPUT_LIMIT_BYTES": "262144",
    "ITER234_ROW_CEILING_SECONDS": "2400",
}
# Evidence the AUTHOR must never touch. The executor may, and is checked separately.
AUTHOR_FORBIDDEN = (".gold.", "gold_patch", "gold.patch", "PASS_TO_PASS", "witness",
                    "divergence", "oracle_result", "answers.json", "eval_set\"")


def _code_strings(text: str) -> list[str]:
    tree = ast.parse(text)
    docstrings = {
        id(n.body[0].value) for n in ast.walk(tree)
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and n.body and isinstance(n.body[0], ast.Expr)
        and isinstance(n.body[0].value, ast.Constant) and isinstance(n.body[0].value.value, str)
    }
    return [
        n.value for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docstrings
    ]


def author_blindness_errors(text: str) -> list[str]:
    """The bar that makes iter234 mean anything: the test author saw only the issue."""

    errors: list[str] = []
    try:
        tree = ast.parse(text)
        literals = _code_strings(text)
    except SyntaxError as exc:
        return [f"author script does not parse: {exc}"]

    prompt = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "PROMPT" for t in node.targets
        ):
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                prompt = node.value.value
    if prompt is None:
        return ["author script has no literal PROMPT template"]

    # A format field named for the patch would let the patch reach the author. Escaped braces ({{ }})
    # are literal output, so only single-brace fields count.
    fields = set(re.findall(r"(?<!\{)\{([a-zA-Z_][a-zA-Z0-9_]*)[^{}]*\}(?!\})", prompt))
    for forbidden in ("patch", "gold", "diff", "candidate", "witness", "label"):
        if forbidden in fields:
            errors.append(f"author PROMPT can interpolate {forbidden!r}")
    if "problem" not in fields:
        errors.append("author PROMPT does not interpolate the issue text")
    if "You are NOT shown the change" not in prompt:
        errors.append("author PROMPT no longer states that the change is withheld")

    joined = "\n".join(literals)
    for fragment in AUTHOR_FORBIDDEN:
        if fragment in joined:
            errors.append(f"author script references withheld evidence: {fragment}")
    return errors


def runner_safety_errors(text: str) -> list[str]:
    errors: list[str] = []
    for flag in REQUIRED_DOCKER_FLAGS:
        if flag not in text:
            errors.append(f"executor missing isolation flag: {flag}")
    for name, value in REQUIRED_LIMITS.items():
        if f"{name}={value}" not in text:
            errors.append(f"executor does not pin {name}={value}")
    code = "\n".join(ln for ln in text.splitlines() if not ln.lstrip().startswith("#"))
    mounts = [m.group("spec").strip("\"'") for m in MOUNT_RE.finditer(code)]
    if not mounts:
        errors.append("executor declares no mounts to check")
    for spec in mounts:
        if not spec.endswith(ALLOWED_MOUNT_SUFFIXES):
            errors.append(f"executor mounts outside the allowlist: {spec}")
    if "ROW_CEILING_EXCEEDED" not in text and "ITER234_ROW_CEILING_SECONDS}s" not in text:
        errors.append("executor lacks the bounded wall-clock row ceiling")
    if "IMAGE_PROVENANCE_INSPECTION_FAIL" not in text:
        errors.append("executor does not fail closed on missing image provenance")
    for fragment in (
        'SHARD_INDEX_RAW="${TELOS_ITER234_SHARD_INDEX-0}"',
        "(( o % SHARD_COUNT == SHARD_INDEX ))",
    ):
        if text.count(fragment) != 1:
            errors.append("executor shard contract missing or duplicated")
    # Both arms must actually run, or the gold-validated arm is unmeasurable.
    for fragment in ("run_arm candidate /telos/candidate.patch", "run_arm gold /telos/gold.patch"):
        if fragment not in text:
            errors.append(f"executor does not run: {fragment}")
    return errors


def test_state_errors() -> tuple[str, list[str]]:
    if not SUMMARY.exists():
        return ("no-tests-yet", [] if not list(TESTS.glob("*.py")) else
                ["test scripts exist without tests_summary.json"])
    summary = json.loads(SUMMARY.read_text())
    errors: list[str] = []
    if summary.get("schema_version") != SCHEMA:
        errors.append("tests summary schema mismatch")
    expected: dict[Path, str] = {}
    for index, row in enumerate(summary.get("manifest") or []):
        label = f"tests manifest row {index}"
        if row.get("author") not in AUTHORS:
            errors.append(f"{label} has an unknown author")
            continue
        stem = f"{row['author']}__{row['run']}__{row['instance_id'].replace('/', '__')}"
        if row.get("status") == "test":
            digest = row.get("test_sha256")
            if not isinstance(digest, str) or not SHA_RE.fullmatch(digest):
                errors.append(f"{label} test_sha256 is invalid")
                continue
            expected[TESTS / f"{stem}.test.py"] = digest
        elif row.get("status") == "no_valid_test":
            if (TESTS / f"{stem}.test.py").exists():
                errors.append(f"{label} uncovered row has a test committed on disk")
        else:
            errors.append(f"{label} has an unknown status")
    actual = set(TESTS.glob("*.test.py"))
    if actual != set(expected):
        missing = sorted(p.name for p in set(expected) - actual)
        extra = sorted(p.name for p in actual - set(expected))
        errors.append(f"test file set mismatch; missing={missing[:3]}, extra={extra[:3]}")
    for path, digest in expected.items():
        if not path.is_file():
            continue
        raw = path.read_bytes()
        if not raw or len(raw) > MAX_TEST_BYTES:
            errors.append(f"{path.name}: size outside the safe bound")
            continue
        payload = raw[:-1] if raw.endswith(b"\n") else raw
        if hashlib.sha256(payload).hexdigest() != digest:
            errors.append(f"{path.name}: summary hash mismatch")
        errors.extend(
            f"{path.name}: {e}" for e in exercise_errors(payload.decode("utf-8", "replace"))
        )
    return ("valid" if not errors else "invalid"), errors


def main() -> int:
    status, errors = test_state_errors()
    for path, checker, name in (
        (AUTHOR, author_blindness_errors, "author"),
        (RUNNER, runner_safety_errors, "executor"),
    ):
        try:
            errors.extend(checker(path.read_text()))
        except OSError as exc:
            errors.append(f"cannot inspect iter234 {name}: {exc}")
    if WORKFLOW.is_file():
        text = WORKFLOW.read_text()
        if "if: always()" in text or "continue-on-error:" in text:
            errors.append("iter234 workflow must not weaken failure semantics")
    if errors:
        for error in errors:
            print(f"iter234 safety error: {error}", file=sys.stderr)
        return 1
    print(
        f"iter234 safety: author is patch-blind, executor is isolated and bounded, tests {status}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
