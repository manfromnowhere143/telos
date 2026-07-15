#!/usr/bin/env python3
"""Fail closed on mutable GitHub Actions and unlocked verification dependencies."""

from __future__ import annotations

from pathlib import Path
import re
import shlex
import sys
from typing import Any

from packaging.version import InvalidVersion, Version
import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github/workflows"
LOCK = ROOT / "requirements-ci.txt"
SWEBENCH_LOCK = ROOT / "requirements/iter200-swebench.txt"
LOCKS = (LOCK, SWEBENCH_LOCK)
KNOWN_WORKFLOW_LOCKS = {
    "requirements-ci.txt",
    "requirements/iter200-swebench.txt",
}
SHA_REF = re.compile(r"^[0-9a-f]{40}$")
EXACT_TOOL_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
HASH_PIN = re.compile(r"^\s*--hash=sha256:([0-9a-f]{64})(\s*\\)?\s*$")
PACKAGE_PIN = re.compile(r"^([a-z0-9]+(?:-[a-z0-9]+)*)==([^\s\\]+)\s*\\\s*$")
RUNNER_ALLOWLIST = {"ubuntu-24.04"}
SETUP_UV_ACTION = "astral-sh/setup-uv"
SETUP_PYTHON_ACTION = "actions/setup-python"
ITER200_BACKFILL = "iter200-denominator-backfill.yml"
PIP_OPERATION = re.compile(
    r"(?i)(?P<command>(?:[^\s;|&]*/)?python(?:3(?:\.\d+)*)?\s+-m\s+pip|"
    r"(?:[^\s;|&]*/)?pip(?:3(?:\.\d+)*)?)\s+"
    r"(?P<operation>download|install)\b(?P<arguments>[^\n;|&]*)"
)
SHELL_CONTINUATION = re.compile(r"\\\r?\n[ \t]*")
WHEELHOUSE_CREATION = re.compile(
    r'(?m)^\s*wheelhouse="\$\(mktemp -d /tmp/[a-zA-Z0-9._-]+\.XXXXXX\)"\s*$'
)
UNSAFE_DOWNLOAD_EXECUTION_PATTERNS = (
    re.compile(
        r"(?im)\b(?:curl|wget)\b[^\r\n]*\|\s*"
        r"(?:(?:sudo|env)\s+)*(?:/(?:usr/)?bin/)?(?:ba|da|k|z)?sh(?:\s|$)"
    ),
    re.compile(
        r"(?im)\b(?:ba|da|k|z)?sh\b[^\r\n]*"
        r"(?:<\(|\$\()\s*(?:curl|wget)\b"
    ),
    re.compile(
        r"(?ims)\b(?:curl|wget)\b.{0,2048}?"
        r"(?:\bchmod\s+[^\r\n]*\+x\b|"
        r"(?:^|\n)\s*(?:sudo\s+)?(?:ba|da|k|z)?sh\s+\S+|"
        r"(?:^|\n)\s*(?:sudo\s+)?\./\S+)"
    ),
)


class UniqueKeySafeLoader(yaml.SafeLoader):
    """Safe YAML loader that refuses ambiguous duplicate mapping keys."""


def _construct_unique_mapping(
    loader: UniqueKeySafeLoader, node: yaml.nodes.MappingNode, deep: bool = False
) -> dict[object, object]:
    loader.flatten_mapping(node)
    mapping: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable mapping key",
                key_node.start_mark,
            ) from exc
        if duplicate:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _option_value(tokens: list[str], names: tuple[str, ...]) -> str | None:
    for index, token in enumerate(tokens):
        for name in names:
            if token == name:
                if index + 1 < len(tokens):
                    return tokens[index + 1]
                return None
            if token.startswith(f"{name}="):
                return token.split("=", 1)[1]
            if name == "-r" and token.startswith("-r") and token != "-r":
                return token[2:]
            if name == "-d" and token.startswith("-d") and token != "-d":
                return token[2:]
    return None


def validate_pip_operations(run: str, label: object, location: str) -> list[str]:
    failures: list[str] = []
    logical_run = SHELL_CONTINUATION.sub("", run)
    operations = list(PIP_OPERATION.finditer(logical_run))
    if not operations:
        return failures
    if run.count("export PIP_DISABLE_PIP_VERSION_CHECK=1") != 1:
        failures.append(
            f"{label}: {location} pip operations must disable the pip version check"
        )
    fresh_wheelhouse = WHEELHOUSE_CREATION.search(run) is not None
    for match in operations:
        operation = match.group("operation").lower()
        try:
            tokens = shlex.split(match.group("arguments"), posix=True)
        except ValueError as exc:
            failures.append(
                f"{label}: {location} pip {operation} arguments are not parseable: {exc}"
            )
            continue
        if any(
            token in {"--upgrade", "-U"} or token.startswith("--upgrade=")
            for token in tokens
        ):
            failures.append(f"{label}: {location} pip upgrades are forbidden")
        if "--require-hashes" not in tokens:
            failures.append(
                f"{label}: {location} pip {operation} must use --require-hashes"
            )
        if "--no-cache-dir" not in tokens:
            failures.append(
                f"{label}: {location} pip {operation} must use --no-cache-dir"
            )
        if "--only-binary=:all:" not in tokens:
            failures.append(
                f"{label}: {location} pip {operation} must use --only-binary=:all:"
            )
        requirement = _option_value(tokens, ("-r", "--requirement"))
        if requirement not in KNOWN_WORKFLOW_LOCKS:
            failures.append(
                f"{label}: {location} pip {operation} must use one validated repository lock"
            )
        if not fresh_wheelhouse:
            failures.append(
                f"{label}: {location} pip {operation} requires a fresh mktemp wheelhouse"
            )
        if operation == "download":
            destination = _option_value(tokens, ("--dest", "-d"))
            if destination != "$wheelhouse":
                failures.append(
                    f"{label}: {location} pip download destination must be the fresh wheelhouse"
                )
        else:
            if "--no-index" not in tokens:
                failures.append(
                    f"{label}: {location} pip install must use --no-index"
                )
            links = _option_value(tokens, ("--find-links", "-f"))
            if links != "$wheelhouse":
                failures.append(
                    f"{label}: {location} pip install must use the fresh wheelhouse"
                )
    return failures


def validate_workflow(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    failures: list[str] = []
    try:
        label = path.relative_to(ROOT)
    except ValueError:
        label = path
    try:
        document = yaml.load(text, Loader=UniqueKeySafeLoader)
    except yaml.YAMLError as exc:
        failures.append(f"{label}: invalid YAML: {exc}")
        document = None
    if document is not None and not isinstance(document, dict):
        failures.append(f"{label}: workflow YAML root must be a mapping")
        document = None

    def validate_action(action: Any, location: str) -> None:
        if not isinstance(action, str):
            failures.append(f"{label}: {location} uses must be a literal string")
            return
        if action.startswith("./"):
            return
        if "@" not in action:
            failures.append(f"{label}: {location} action lacks ref: {action}")
            return
        ref = action.rsplit("@", 1)[1]
        if not SHA_REF.fullmatch(ref):
            failures.append(
                f"{label}: {location} action ref is not an immutable SHA: {action}"
            )

    def validate_run_block(run: Any, location: str) -> None:
        if not isinstance(run, str):
            failures.append(f"{label}: {location} run must be a literal string")
            return
        if any(pattern.search(run) for pattern in UNSAFE_DOWNLOAD_EXECUTION_PATTERNS):
            failures.append(
                f"{label}: {location} run contains an unsafe download-and-execute pattern"
            )
        failures.extend(validate_pip_operations(run, label, location))

    def validate_setup_uv(step: dict[Any, Any], location: str) -> None:
        action = step.get("uses")
        if not isinstance(action, str) or action.rsplit("@", 1)[0] != SETUP_UV_ACTION:
            return
        configuration = step.get("with")
        version = configuration.get("version") if isinstance(configuration, dict) else None
        if not isinstance(version, str) or EXACT_TOOL_VERSION.fullmatch(version) is None:
            failures.append(
                f"{label}: {location} setup-uv version must be an exact X.Y.Z string"
            )

    if document is not None:
        if document.get("permissions") != {"contents": "read"}:
            failures.append(
                f"{label}: top-level permissions must be exactly contents: read"
            )
        jobs = document.get("jobs")
        if not isinstance(jobs, dict) or not jobs:
            failures.append(f"{label}: jobs must be a non-empty mapping")
        else:
            for job_name, job in jobs.items():
                location = f"job {job_name!r}"
                if not isinstance(job, dict):
                    failures.append(f"{label}: {location} must be a mapping")
                    continue
                if "permissions" in job:
                    failures.append(f"{label}: {location} may not override permissions")
                if "uses" in job:
                    validate_action(job["uses"], location)
                runner = job.get("runs-on")
                if runner not in RUNNER_ALLOWLIST:
                    failures.append(
                        f"{label}: {location} runner must be one of "
                        f"{sorted(RUNNER_ALLOWLIST)}, got {runner!r}"
                    )
                steps = job.get("steps")
                if not isinstance(steps, list) or not steps:
                    failures.append(f"{label}: {location} steps must be a non-empty list")
                    continue
                for step_index, step in enumerate(steps):
                    step_location = f"{location} step {step_index}"
                    if not isinstance(step, dict):
                        failures.append(f"{label}: {step_location} must be a mapping")
                        continue
                    if "uses" in step:
                        validate_action(step["uses"], step_location)
                        validate_setup_uv(step, step_location)
                    if "run" in step:
                        validate_run_block(step["run"], step_location)
        if path.name == ITER200_BACKFILL:
            setup_python_versions: list[Any] = []
            run_blocks: list[str] = []
            jobs = document.get("jobs")
            if isinstance(jobs, dict):
                for job in jobs.values():
                    if not isinstance(job, dict) or not isinstance(job.get("steps"), list):
                        continue
                    for step in job["steps"]:
                        if not isinstance(step, dict):
                            continue
                        action = step.get("uses")
                        if (
                            isinstance(action, str)
                            and action.rsplit("@", 1)[0] == SETUP_PYTHON_ACTION
                        ):
                            configuration = step.get("with")
                            setup_python_versions.append(
                                configuration.get("python-version")
                                if isinstance(configuration, dict)
                                else None
                            )
                        if isinstance(step.get("run"), str):
                            run_blocks.append(step["run"])
            if setup_python_versions != ["3.11.15"]:
                failures.append(
                    f"{label}: backfill must use exactly one Python 3.11.15 setup action"
                )
            combined_run = "\n".join(run_blocks)
            required_fragments = (
                'TELOS_SWEEBENCH_WHEEL="$wheelhouse/'
                'swebench-4.1.0-py3-none-any.whl"',
                "/tmp/telos-swebench/bin/python -I scripts/extract_iter200_specs.py",
            )
            for fragment in required_fragments:
                if combined_run.count(fragment) != 1:
                    failures.append(
                        f"{label}: backfill provenance command missing or duplicated: {fragment}"
                    )
    return failures


def validate_lock(path: Path = LOCK) -> list[str]:
    failures: list[str] = []
    try:
        label = path.relative_to(ROOT)
    except ValueError:
        label = path
    numbered_lines = [
        (line_number, line)
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        )
        if line and not line.startswith("#")
    ]
    if not numbered_lines:
        return [f"{label}: expected exact package pins with wheel hashes"]
    index = 0
    package_names: list[str] = []
    while index < len(numbered_lines):
        line_number, package = numbered_lines[index]
        package_match = PACKAGE_PIN.fullmatch(package)
        if package_match is None:
            failures.append(
                f"{label}:{line_number}: dependency is not exactly pinned"
            )
            index += 1
            continue
        package_name, version_text = package_match.groups()
        if any(character in version_text for character in ";@[]="):
            failures.append(
                f"{label}:{line_number}: dependency is not exactly pinned"
            )
        else:
            try:
                version = Version(version_text)
            except InvalidVersion:
                failures.append(
                    f"{label}:{line_number}: dependency version is not PEP 440"
                )
            else:
                if str(version) != version_text:
                    failures.append(
                        f"{label}:{line_number}: dependency version is not canonical PEP 440"
                    )
        package_names.append(package_name)
        index += 1
        hashes: list[str] = []
        terminated = False
        while index < len(numbered_lines):
            hash_line_number, digest_line = numbered_lines[index]
            match = HASH_PIN.fullmatch(digest_line)
            if match is None:
                break
            hashes.append(match.group(1))
            index += 1
            if match.group(2) is None:
                terminated = True
                break
        if not hashes:
            failures.append(
                f"{label}:{line_number}: dependency hash is missing"
            )
        elif len(hashes) != len(set(hashes)):
            failures.append(
                f"{label}:{line_number}: dependency hashes are duplicated"
            )
        if hashes and not terminated:
            failures.append(
                f"{label}:{line_number}: final dependency hash must end the continuation"
            )
        if hashes != sorted(hashes):
            failures.append(
                f"{label}:{line_number}: dependency hashes are not sorted"
            )
    if len(package_names) != len(set(package_names)):
        failures.append(f"{label}: normalized package names must be unique")
    if package_names != sorted(package_names):
        failures.append(f"{label}: package blocks must be sorted by name")
    return failures


def collect_failures() -> list[str]:
    failures: list[str] = []
    for lock in LOCKS:
        failures.extend(validate_lock(lock))
    workflow_paths = sorted((*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")))
    if not workflow_paths:
        failures.append(".github/workflows: no workflows found")
    for path in workflow_paths:
        failures.extend(validate_workflow(path))
    return failures


def main() -> int:
    failures = collect_failures()
    if failures:
        print("supply-chain guard failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1
    count = len(tuple(WORKFLOWS.glob("*.yml"))) + len(tuple(WORKFLOWS.glob("*.yaml")))
    print(
        f"supply-chain guard: {count} workflows and {len(LOCKS)} dependency locks "
        "satisfy pinned-reference rules"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
