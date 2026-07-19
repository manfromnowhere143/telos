#!/usr/bin/env python3
"""Accept only iter239's preregistered CI job-display-name substitution.

The repository's required checks will bind to pull-request-specific job names.
That distinction is meaningful only if the workflow otherwise remains the
reviewed predecessor workflow.  This guard therefore derives the sole allowed
candidate from the exact workflow bytes in the iter239 activation commit and
rejects every other byte or parsed-structure change.

The current workflow is intentionally not modified to invoke this script:
adding a step would violate the exact-delta contract.  The already-required
``pytest -q`` step executes the focused tests that apply this guard to the
committed workflow and to known-bad variants.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import subprocess
import sys
from typing import Any

import yaml
from yaml.constructor import ConstructorError


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = Path(".github/workflows/ci.yml")
PREDECESSOR_COMMIT = "746f225f6c3718a1c2190dc00496386600fb2c5c"
PREDECESSOR_SHA256 = "c7a39ffa4c41df14fe91b968d1560bdbdf4792f0ad529eb441fd5610e0dac9a9"
EXPECTED_SHA256 = "befe8d6e9ca5228d5d8d694ee343ca9f93cb2b912470f358f4aca1ee1b8f1267"

OLD_JOB_NAME = "verify py${{ matrix.python-version }}"
NEW_JOB_NAME = "verify ${{ github.event_name }} py${{ matrix.python-version }}"
OLD_JOB_NAME_LINE = f"    name: {OLD_JOB_NAME}\n".encode()
NEW_JOB_NAME_LINE = f"    name: {NEW_JOB_NAME}\n".encode()
PATH_FILTER_KEYS = {"paths", "paths-ignore"}


class _StrictBaseLoader(yaml.BaseLoader):
    """Keep GitHub's ``on`` key scalar and reject duplicate YAML keys."""

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        if not isinstance(node, yaml.MappingNode):
            raise ConstructorError(
                None,
                None,
                f"expected a mapping node, but found {node.id}",
                node.start_mark,
            )
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                duplicate = key in mapping
            except TypeError as exc:
                raise ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    "found an unhashable key",
                    key_node.start_mark,
                ) from exc
            if duplicate:
                raise ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"found duplicate key {key!r}",
                    key_node.start_mark,
                )
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_predecessor_workflow(root: Path = ROOT) -> bytes:
    """Read the pinned predecessor blob from Git, never from mutable worktree bytes."""

    result = subprocess.run(
        ["git", "show", f"{PREDECESSOR_COMMIT}:{WORKFLOW_PATH.as_posix()}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(f"cannot read pinned predecessor workflow: {detail}")
    return result.stdout


def expected_workflow(predecessor: bytes) -> bytes:
    """Derive the only allowed workflow from exact predecessor bytes."""

    digest = sha256(predecessor)
    if digest != PREDECESSOR_SHA256:
        raise ValueError(
            "pinned predecessor workflow digest mismatch: "
            f"expected {PREDECESSOR_SHA256}, observed {digest}"
        )
    if predecessor.count(OLD_JOB_NAME_LINE) != 1:
        raise ValueError("pinned predecessor does not contain exactly one old job-name line")
    if NEW_JOB_NAME_LINE in predecessor:
        raise ValueError("pinned predecessor already contains the iter239 job-name line")
    expected = predecessor.replace(OLD_JOB_NAME_LINE, NEW_JOB_NAME_LINE, 1)
    digest = sha256(expected)
    if digest != EXPECTED_SHA256:
        raise ValueError(
            "derived iter239 workflow digest mismatch: "
            f"expected {EXPECTED_SHA256}, observed {digest}"
        )
    return expected


def _parse_workflow(raw: bytes, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return None, [f"{label} workflow is not UTF-8: {exc}"]
    try:
        document = yaml.load(text, Loader=_StrictBaseLoader)
    except yaml.YAMLError as exc:
        return None, [f"{label} workflow does not parse as strict YAML: {exc}"]
    if not isinstance(document, dict):
        return None, [f"{label} workflow root is not a mapping"]
    return document, []


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _steps(job: dict[str, Any]) -> list[dict[str, Any]]:
    value = job.get("steps")
    if not isinstance(value, list):
        return []
    return [step if isinstance(step, dict) else {} for step in value]


def _contains_path_filter(value: Any) -> bool:
    if isinstance(value, dict):
        return bool(PATH_FILTER_KEYS & set(value)) or any(
            _contains_path_filter(child) for child in value.values()
        )
    if isinstance(value, list):
        return any(_contains_path_filter(child) for child in value)
    return False


def _semantic_drift_errors(
    predecessor: dict[str, Any],
    candidate: dict[str, Any],
) -> list[str]:
    """Name the fail-closed classes in addition to the exact-byte verdict."""

    errors: list[str] = []
    expected = deepcopy(predecessor)
    expected_jobs = _mapping(expected.get("jobs"))
    expected_verify = _mapping(expected_jobs.get("verify"))
    expected_verify["name"] = NEW_JOB_NAME

    predecessor_triggers = predecessor.get("on")
    candidate_triggers = candidate.get("on")
    if _contains_path_filter(candidate_triggers):
        errors.append("trigger drift introduces a path filter")
    if candidate_triggers != predecessor_triggers:
        errors.append("trigger drift changes push or pull-request coverage")

    if candidate.get("permissions") != predecessor.get("permissions"):
        errors.append("permission drift changes workflow permissions")

    predecessor_jobs = _mapping(predecessor.get("jobs"))
    candidate_jobs = _mapping(candidate.get("jobs"))
    if set(candidate_jobs) != set(predecessor_jobs):
        errors.append("job-set drift changes the workflow job inventory")

    predecessor_verify = _mapping(predecessor_jobs.get("verify"))
    candidate_verify = _mapping(candidate_jobs.get("verify"))
    if candidate_verify.get("name") != NEW_JOB_NAME:
        errors.append("job-name drift does not emit the exact event-specific context")
    if candidate_verify.get("runs-on") != predecessor_verify.get("runs-on"):
        errors.append("runner drift changes the pinned runner")
    if candidate_verify.get("strategy") != predecessor_verify.get("strategy"):
        errors.append("matrix or strategy drift changes interpreter coverage or failure semantics")
    if candidate_verify.get("permissions") != predecessor_verify.get("permissions"):
        errors.append("permission drift changes job permissions")
    if candidate_verify.get("if") != predecessor_verify.get("if"):
        errors.append("job-level condition drift can skip the required job")
    if candidate_verify.get("continue-on-error") != predecessor_verify.get(
        "continue-on-error"
    ):
        errors.append("job-level continue-on-error drift weakens failure semantics")

    predecessor_steps = _steps(predecessor_verify)
    candidate_steps = _steps(candidate_verify)
    if len(candidate_steps) != len(predecessor_steps):
        errors.append("step-set drift changes the executable CI closure")
    for index, (before, after) in enumerate(
        zip(predecessor_steps, candidate_steps, strict=False)
    ):
        label = after.get("name") or before.get("name") or f"step {index}"
        if after.get("if") != before.get("if"):
            errors.append(f"step-level condition drift can skip {label!r}")
        if after.get("continue-on-error") != before.get("continue-on-error"):
            errors.append(
                f"step-level continue-on-error drift weakens {label!r}"
            )
        if after.get("uses") != before.get("uses") or after.get("with") != before.get(
            "with"
        ):
            errors.append(f"action or dependency drift changes {label!r}")
        if after.get("run") != before.get("run"):
            errors.append(f"command or dependency drift changes {label!r}")
        if after.get("name") != before.get("name"):
            errors.append(f"step metadata drift changes step {index}")

    if candidate != expected:
        errors.append("parsed workflow structure differs outside the exact job-name substitution")
    return errors


def validation_errors(predecessor: bytes, candidate: bytes) -> list[str]:
    """Return every detected violation of the iter239 exact-delta contract."""

    errors: list[str] = []
    try:
        expected = expected_workflow(predecessor)
    except ValueError as exc:
        return [str(exc)]

    if candidate != expected:
        errors.append(
            "workflow byte delta is not exactly the preregistered job-name substitution "
            f"(expected sha256 {EXPECTED_SHA256}, observed {sha256(candidate)})"
        )

    predecessor_document, predecessor_errors = _parse_workflow(predecessor, "predecessor")
    candidate_document, candidate_errors = _parse_workflow(candidate, "candidate")
    errors.extend(predecessor_errors)
    errors.extend(candidate_errors)
    if predecessor_document is not None and candidate_document is not None:
        errors.extend(_semantic_drift_errors(predecessor_document, candidate_document))
    return errors


def validate_current(root: Path = ROOT) -> list[str]:
    try:
        predecessor = load_predecessor_workflow(root)
        candidate = (root / WORKFLOW_PATH).read_bytes()
    except OSError as exc:
        return [f"cannot read iter239 CI workflow input: {exc}"]
    except RuntimeError as exc:
        return [str(exc)]
    return validation_errors(predecessor, candidate)


def main() -> int:
    errors = validate_current()
    if errors:
        for error in errors:
            print(f"iter239 CI exact-delta error: {error}", file=sys.stderr)
        return 1
    print(
        "iter239 CI exact-delta: only the event-specific job-name substitution "
        f"is present ({EXPECTED_SHA256})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
