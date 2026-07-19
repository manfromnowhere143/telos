#!/usr/bin/env python3
"""Validate the offline workflow lifecycle registry.

The default mode is the completed iter238 contract: the current gate, seal
links, retirement receipt, and desired disabled states must all be evidenced.
``--pre-retirement`` is a deliberately narrower staging mode.  It validates
the frozen IDs, file bytes, trigger inventory, and default-deny
classifications before the separately authorized GitHub disable operation.
It does not claim that the desired server states have already been observed.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_RELATIVE = Path("mission/workflow_registry.json")
CURRENT_RELATIVE = Path("mission/current.json")
ITER238_GATE = "experiments/iter238_claim_seal_workflow_controls/HYPOTHESIS.md"
REPOSITORY = "manfromnowhere143/telos"
SCHEMA = "telos.workflow_registry.v1"
RECEIPT_SCHEMA = "telos.workflow_retirement_receipt.v1"
HISTORICAL_SEAL = "iter237-merged-historical-baseline"
ITER204_PATH = ".github/workflows/iter204-execute.yml"
ITER204_ID = 314113289
ITER204_SHA256 = "84f7f8b228624ff7244991e317e7f8146a6aacd93f803c1df983b6cceae4deb4"
PLATFORM_PATH = "dynamic/dependabot/update-graph"
PLATFORM_ID = 309260104
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
RUNNER_EXPRESSION = re.compile(r"\$\{\{[^}]*\brunner\.", re.IGNORECASE)
EXPECTED_CLASSES = {
    "active_control",
    "authorized_one_shot",
    "historical_retired",
    "platform_service",
}
ENTRY_KEYS = {
    "classification",
    "declared_triggers",
    "desired_server_state",
    "execution_authority",
    "known_invalidity",
    "path",
    "retirement_receipt",
    "seal_reference",
    "sha256",
    "source_kind",
    "workflow_id",
}
REGISTRY_KEYS = {
    "active_gate",
    "default_policy",
    "entries",
    "repository",
    "retirement_receipt",
    "schema_version",
    "seal_registry",
    "updated",
}


class RegistryError(ValueError):
    """A strict JSON or GitHub-workflow document is ambiguous."""


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_canonical_json(path: Path) -> tuple[dict[str, Any], bytes]:
    """Load a canonical JSON object while refusing duplicate keys."""

    raw = path.read_bytes()
    duplicates: list[str] = []

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                duplicates.append(key)
            value[key] = item
        return value

    try:
        document = json.loads(
            raw,
            object_pairs_hook=unique,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
        )
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise RegistryError(f"cannot parse strict JSON {path}: {exc}") from exc
    if duplicates:
        raise RegistryError(f"duplicate JSON keys in {path}: {sorted(set(duplicates))}")
    if not isinstance(document, dict):
        raise RegistryError(f"JSON root is not an object: {path}")
    rendered = (json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    if raw != rendered:
        raise RegistryError(f"JSON is not canonical: {path}")
    return document, raw


class GitHubWorkflowLoader(yaml.SafeLoader):
    """YAML 1.2-like loader for GitHub Actions, where ``on`` is a string."""


GitHubWorkflowLoader.yaml_implicit_resolvers = copy.deepcopy(
    yaml.SafeLoader.yaml_implicit_resolvers
)
for resolver_key, resolvers in GitHubWorkflowLoader.yaml_implicit_resolvers.items():
    GitHubWorkflowLoader.yaml_implicit_resolvers[resolver_key] = [
        (tag, expression)
        for tag, expression in resolvers
        if tag != "tag:yaml.org,2002:bool"
    ]
GitHubWorkflowLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)


def _construct_unique_mapping(
    loader: GitHubWorkflowLoader,
    node: yaml.nodes.MappingNode,
    deep: bool = False,
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


GitHubWorkflowLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def parse_workflow(path: Path) -> dict[str, Any]:
    try:
        document = yaml.load(path.read_text(encoding="utf-8"), Loader=GitHubWorkflowLoader)
    except (UnicodeError, yaml.YAMLError) as exc:
        raise RegistryError(f"invalid workflow YAML {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise RegistryError(f"workflow root is not a mapping: {path}")
    return document


def declared_triggers(document: dict[str, Any]) -> list[str]:
    trigger = document.get("on")
    if isinstance(trigger, str):
        values = [trigger]
    elif isinstance(trigger, list) and all(isinstance(item, str) for item in trigger):
        values = trigger
    elif isinstance(trigger, dict) and all(isinstance(item, str) for item in trigger):
        values = list(trigger)
    else:
        raise RegistryError("workflow 'on' is not a supported literal trigger declaration")
    if len(values) != len(set(values)):
        raise RegistryError("workflow trigger declaration contains duplicates")
    return sorted(values)


def executable_job_env_runner_failures(
    document: dict[str, Any], *, label: str
) -> list[str]:
    """Reject runner context where GitHub does not make it available."""

    failures: list[str] = []
    jobs = document.get("jobs")
    if not isinstance(jobs, dict):
        return [f"{label}: jobs is not a mapping"]
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        environment = job.get("env")
        if not isinstance(environment, dict):
            continue
        for name, value in environment.items():
            if isinstance(value, str) and RUNNER_EXPRESSION.search(value):
                failures.append(
                    f"{label}: executable job {job_name!r} job-level env {name!r} "
                    "uses unavailable runner.* context"
                )
    return failures


def _safe_relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and "\\" not in value


def _find_seal_record(value: Any, identifier: str) -> dict[str, Any] | None:
    if isinstance(value, dict):
        if any(value.get(key) == identifier for key in ("id", "record_id", "seal_id")):
            return value
        for child in value.values():
            found = _find_seal_record(child, identifier)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_seal_record(child, identifier)
            if found is not None:
                return found
    return None


def _path_lists(value: Any) -> list[list[str]]:
    lists: list[list[str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "path_list" and isinstance(child, list) and all(
                isinstance(item, str) for item in child
            ):
                lists.append(child)
            lists.extend(_path_lists(child))
    elif isinstance(value, list):
        for child in value:
            lists.extend(_path_lists(child))
    return lists


def validate_seal_links(
    root: Path, registry: dict[str, Any], historical_paths: set[str]
) -> list[str]:
    failures: list[str] = []
    seal_relative = registry.get("seal_registry")
    if not _safe_relative_path(seal_relative):
        return ["workflow registry: seal_registry is not a safe relative path"]
    seal_path = root / str(seal_relative)
    if not seal_path.is_file() or seal_path.is_symlink():
        return [f"workflow registry: seal registry is absent: {seal_relative}"]
    try:
        seals, _ = load_canonical_json(seal_path)
    except (OSError, RegistryError) as exc:
        return [f"workflow registry: cannot validate seal registry: {exc}"]
    record = _find_seal_record(seals, HISTORICAL_SEAL)
    if record is None:
        return [f"workflow registry: seal reference is absent: {HISTORICAL_SEAL}"]
    path_lists = _path_lists(record)
    if not any(historical_paths <= set(paths) for paths in path_lists):
        failures.append(
            "workflow registry: historical seal path_list does not cover all 29 workflows"
        )
    return failures


def validate_retirement_receipt(
    root: Path,
    registry: dict[str, Any],
    registry_raw: bytes,
    historical: list[dict[str, Any]],
) -> list[str]:
    failures: list[str] = []
    receipt_relative = registry.get("retirement_receipt")
    if not _safe_relative_path(receipt_relative):
        return ["workflow registry: retirement_receipt is not a safe relative path"]
    receipt_path = root / str(receipt_relative)
    if not receipt_path.is_file() or receipt_path.is_symlink():
        return [f"workflow registry: final retirement receipt is absent: {receipt_relative}"]
    try:
        receipt, _ = load_canonical_json(receipt_path)
    except (OSError, RegistryError) as exc:
        return [f"workflow registry: cannot validate retirement receipt: {exc}"]
    required_top = {
        "entries",
        "observed_at",
        "operation_counts",
        "raw_observations",
        "registry_sha256",
        "repository",
        "schema_version",
        "source_commit",
        "state_scope",
    }
    if set(receipt) != required_top:
        failures.append("workflow retirement receipt: top-level fields differ")
    if receipt.get("schema_version") != RECEIPT_SCHEMA:
        failures.append("workflow retirement receipt: schema_version differs")
    if receipt.get("repository") != REPOSITORY:
        failures.append("workflow retirement receipt: repository differs")
    if receipt.get("registry_sha256") != sha256(registry_raw):
        failures.append("workflow retirement receipt: registry digest differs")
    if not isinstance(receipt.get("observed_at"), str) or not receipt["observed_at"]:
        failures.append("workflow retirement receipt: observed_at is absent")
    if not isinstance(receipt.get("source_commit"), str) or HEX40.fullmatch(
        receipt["source_commit"]
    ) is None:
        failures.append("workflow retirement receipt: source_commit is not 40-hex")
    if (
        receipt.get("state_scope")
        != "server state observed at observed_at; not a timeless state proof"
    ):
        failures.append("workflow retirement receipt: mutable state scope differs")
    expected_operations = {
        "delete_run": 0,
        "delete_workflow": 0,
        "disable_workflow": 29,
        "dispatch": 0,
        "enable_workflow": 0,
        "rerun": 0,
    }
    if receipt.get("operation_counts") != expected_operations:
        failures.append("workflow retirement receipt: operation counts differ")

    rows = receipt.get("entries")
    by_id: dict[int, dict[str, Any]] = {}
    if not isinstance(rows, list) or len(rows) != 29:
        failures.append("workflow retirement receipt: expected exactly 29 entries")
    else:
        by_id = {
            row.get("workflow_id"): row
            for row in rows
            if isinstance(row, dict)
            and isinstance(row.get("workflow_id"), int)
            and not isinstance(row.get("workflow_id"), bool)
        }
        if len(by_id) != 29:
            failures.append("workflow retirement receipt: workflow IDs are not unique")
    expected_by_id = {entry["workflow_id"]: entry for entry in historical}
    if set(by_id) != set(expected_by_id):
        failures.append("workflow retirement receipt: historical workflow IDs differ")
    for workflow_id, expected in expected_by_id.items():
        row = by_id.get(workflow_id)
        if row is None:
            continue
        if (
            row.get("path") != expected["path"]
            or row.get("pre_state") != "active"
            or row.get("post_state") != "disabled_manually"
            or not isinstance(row.get("pre_total_run_count"), int)
            or isinstance(row.get("pre_total_run_count"), bool)
            or row.get("pre_total_run_count") < 0
            or row.get("post_total_run_count") != row.get("pre_total_run_count")
            or row.get("post_latest_run_id") != row.get("pre_latest_run_id")
        ):
            failures.append(
                f"workflow retirement receipt: state/run binding differs for {expected['path']}"
            )
    iter204 = by_id.get(ITER204_ID)
    if iter204 is not None and (
        iter204.get("pre_push_run_count") != iter204.get("post_push_run_count")
        or iter204.get("pre_dispatch_run_count") != 0
        or iter204.get("post_dispatch_run_count") != 0
    ):
        failures.append("workflow retirement receipt: iter204 run boundary differs")

    observations = receipt.get("raw_observations")
    if not isinstance(observations, list) or not observations:
        failures.append("workflow retirement receipt: raw observations are absent")
    else:
        for row in observations:
            if not isinstance(row, dict) or set(row) != {"bytes", "path", "sha256"}:
                failures.append("workflow retirement receipt: raw observation row is malformed")
                continue
            relative = row.get("path")
            digest = row.get("sha256")
            byte_count = row.get("bytes")
            if (
                not _safe_relative_path(relative)
                or not isinstance(digest, str)
                or HEX64.fullmatch(digest) is None
                or not isinstance(byte_count, int)
                or isinstance(byte_count, bool)
                or byte_count < 0
            ):
                failures.append("workflow retirement receipt: raw observation metadata differs")
                continue
            path = root / relative
            if path.is_symlink() or not path.is_file():
                failures.append(
                    f"workflow retirement receipt: raw observation is absent: {relative}"
                )
                continue
            payload = path.read_bytes()
            if len(payload) != byte_count or sha256(payload) != digest:
                failures.append(
                    f"workflow retirement receipt: raw observation digest differs: {relative}"
                )
    return failures


def collect_failures(
    *,
    root: Path = ROOT,
    pre_retirement: bool = False,
) -> list[str]:
    failures: list[str] = []
    registry_path = root / REGISTRY_RELATIVE
    try:
        registry, registry_raw = load_canonical_json(registry_path)
    except (OSError, RegistryError) as exc:
        return [f"workflow registry: {exc}"]
    if set(registry) != REGISTRY_KEYS:
        failures.append("workflow registry: top-level fields differ")
    if registry.get("schema_version") != SCHEMA:
        failures.append("workflow registry: schema_version differs")
    if registry.get("repository") != REPOSITORY:
        failures.append("workflow registry: repository differs")
    if registry.get("default_policy") != "deny":
        failures.append("workflow registry: default policy must be deny")
    if registry.get("active_gate") != ITER238_GATE:
        failures.append("workflow registry: active gate is not iter238")

    rows = registry.get("entries")
    if not isinstance(rows, list):
        return failures + ["workflow registry: entries is not a list"]
    paths: list[str] = []
    workflow_ids: list[int] = []
    valid_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        label = f"workflow registry entry {index}"
        if not isinstance(row, dict):
            failures.append(f"{label}: entry is not an object")
            continue
        valid_rows.append(row)
        if set(row) != ENTRY_KEYS:
            failures.append(f"{label}: fields differ")
        path = row.get("path")
        if not _safe_relative_path(path):
            failures.append(f"{label}: path is not a safe relative POSIX path")
        else:
            paths.append(path)
        workflow_id = row.get("workflow_id")
        if (
            not isinstance(workflow_id, int)
            or isinstance(workflow_id, bool)
            or workflow_id <= 0
        ):
            failures.append(f"{label}: workflow_id is not a positive integer")
        else:
            workflow_ids.append(workflow_id)
        if row.get("classification") not in EXPECTED_CLASSES:
            failures.append(f"{label}: classification is unknown")
    if len(paths) != len(set(paths)):
        failures.append("workflow registry: paths are not unique")
    if paths != sorted(paths):
        failures.append("workflow registry: entries are not sorted by path")
    if len(workflow_ids) != len(set(workflow_ids)):
        failures.append("workflow registry: workflow IDs are not unique")

    repository_rows = [
        row for row in valid_rows if row.get("source_kind") == "repository_file"
    ]
    platform_rows = [
        row for row in valid_rows if row.get("source_kind") == "platform_generated"
    ]
    if len(repository_rows) != 30:
        failures.append("workflow registry: expected exactly 30 repository workflows")
    if len(platform_rows) != 1:
        failures.append("workflow registry: expected exactly one platform workflow")
    actual_workflows = {
        str(path.relative_to(root))
        for pattern in ("*.yml", "*.yaml")
        for path in (root / ".github/workflows").glob(pattern)
    }
    registered_workflows = {
        str(row.get("path"))
        for row in repository_rows
        if isinstance(row.get("path"), str)
    }
    if actual_workflows != registered_workflows:
        missing = sorted(actual_workflows - registered_workflows)
        extra = sorted(registered_workflows - actual_workflows)
        failures.append(
            f"workflow registry: file inventory differs; unregistered={missing}, absent={extra}"
        )

    classes = {
        name: [row for row in valid_rows if row.get("classification") == name]
        for name in EXPECTED_CLASSES
    }
    if len(classes["active_control"]) != 1:
        failures.append("workflow registry: expected exactly one active control")
    if classes["authorized_one_shot"]:
        failures.append("workflow registry: expected zero authorized one-shot workflows")
    if len(classes["historical_retired"]) != 29:
        failures.append("workflow registry: expected exactly 29 historical workflows")
    if len(classes["platform_service"]) != 1:
        failures.append("workflow registry: expected exactly one platform service")

    historical_paths: set[str] = set()
    for row in repository_rows:
        path_value = row.get("path")
        if not isinstance(path_value, str):
            continue
        path = root / path_value
        if path.is_symlink() or not path.is_file():
            failures.append(f"workflow registry: workflow is absent or symlinked: {path_value}")
            continue
        payload = path.read_bytes()
        digest = row.get("sha256")
        if not isinstance(digest, str) or HEX64.fullmatch(digest) is None:
            failures.append(f"workflow registry: invalid SHA-256 for {path_value}")
        elif sha256(payload) != digest:
            failures.append(f"workflow registry: workflow digest differs: {path_value}")
        try:
            document = parse_workflow(path)
            triggers = declared_triggers(document)
        except RegistryError as exc:
            failures.append(f"workflow registry: {exc}")
            continue
        if row.get("declared_triggers") != triggers:
            failures.append(f"workflow registry: trigger set differs: {path_value}")
        classification = row.get("classification")
        if classification == "active_control":
            if (
                path_value != ".github/workflows/ci.yml"
                or row.get("desired_server_state") != "active"
                or row.get("execution_authority")
                != "continuous_repository_verification"
                or triggers != ["pull_request", "push"]
                or row.get("retirement_receipt") is not None
                or row.get("seal_reference") is not None
                or row.get("known_invalidity") is not None
            ):
                failures.append("workflow registry: active ci control contract differs")
            failures.extend(
                executable_job_env_runner_failures(document, label=path_value)
            )
        elif classification == "authorized_one_shot":
            failures.extend(
                executable_job_env_runner_failures(document, label=path_value)
            )
        elif classification == "historical_retired":
            historical_paths.add(path_value)
            if (
                row.get("desired_server_state") != "disabled_manually"
                or row.get("execution_authority") != "none"
                or triggers != ["workflow_dispatch"]
                or row.get("retirement_receipt") != registry.get("retirement_receipt")
                or row.get("seal_reference") != HISTORICAL_SEAL
            ):
                failures.append(
                    f"workflow registry: historical retirement contract differs: {path_value}"
                )
            expected_invalidity = (
                {
                    "class": "github_expression_context",
                    "column": 36,
                    "expression": "runner.temp",
                    "line": 318,
                    "result": (
                        "experiments/iter204_iter203_infrastructure_recovery/RESULT.md"
                    ),
                }
                if path_value == ITER204_PATH
                else None
            )
            if row.get("known_invalidity") != expected_invalidity:
                failures.append(
                    f"workflow registry: known invalidity differs: {path_value}"
                )
            if path_value == ITER204_PATH:
                lines = payload.decode("utf-8").splitlines()
                if (
                    row.get("workflow_id") != ITER204_ID
                    or digest != ITER204_SHA256
                    or len(lines) < 318
                    or lines[317]
                    != (
                        "      TELOS_ITER204_SMOKE_RECEIPT: "
                        "${{ runner.temp }}/iter204-smoke/smoke.receipt.json"
                    )
                ):
                    failures.append("workflow registry: sealed iter204 defect anchor differs")

    platform = platform_rows[0] if len(platform_rows) == 1 else {}
    if platform and (
        platform.get("path") != PLATFORM_PATH
        or platform.get("workflow_id") != PLATFORM_ID
        or platform.get("classification") != "platform_service"
        or platform.get("declared_triggers") != ["dynamic"]
        or platform.get("desired_server_state") != "active"
        or platform.get("execution_authority") != "github_platform_service"
        or platform.get("sha256") is not None
        or platform.get("seal_reference") is not None
        or platform.get("retirement_receipt") is not None
        or platform.get("known_invalidity") is not None
    ):
        failures.append("workflow registry: Dependency Graph service contract differs")

    if not pre_retirement:
        current_path = root / CURRENT_RELATIVE
        try:
            current, _ = load_canonical_json(current_path)
        except (OSError, RegistryError) as exc:
            failures.append(f"workflow registry: cannot validate current state: {exc}")
        else:
            if current.get("active_gate") != ITER238_GATE:
                failures.append(
                    "workflow registry: current active gate does not point to iter238"
                )
        failures.extend(validate_seal_links(root, registry, historical_paths))
        failures.extend(
            validate_retirement_receipt(
                root,
                registry,
                registry_raw,
                classes["historical_retired"],
            )
        )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pre-retirement",
        action="store_true",
        help="validate frozen local identities without claiming server retirement",
    )
    args = parser.parse_args()
    failures = collect_failures(pre_retirement=args.pre_retirement)
    if failures:
        print("workflow lifecycle registry failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1
    mode = "pre-retirement identities" if args.pre_retirement else "final retirement"
    print(
        f"workflow lifecycle registry: 30 repository workflows, 29 historical, "
        f"1 active control, and 1 platform service pass ({mode})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
