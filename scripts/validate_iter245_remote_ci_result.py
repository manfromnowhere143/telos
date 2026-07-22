#!/usr/bin/env python3
"""Validate the retained Iter245 remote-CI result without inflating its authority.

This is a retrospective, same-operator consistency check added after the hosted
observation.  It checks the retained bounded JSON against repository bytes and
registered identities.  It is not an independent attestation.  It does not
prove that hosted commands executed and does
not supply scientific, security, publication, release, or merge authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OBSERVATION = (
    ROOT
    / "experiments/iter245_offline_verified_python_bootstrap/proof/remote_ci_observation.json"
)
CLASSIFICATION = (
    "experiments/iter243_iter242_remote_ci_recovery/proof/"
    "gitguardian_occurrence_classification.json"
)
SCHEMA_VERSION = "telos.iter245.remote_ci_observation.v1"
CANDIDATE_COMMIT = "de22688f800e0fb46c15ecd851d2bf76e26b0a82"
CANDIDATE_TREE = "416c864123bd7451d250bcd6384c41d1670343a5"
BASE_COMMIT = "6a9a4f66ec331011c9dfbe14b3a22259a5b585d5"
BASE_TREE = "76c6791ec2a051804a50f65b5297b709dea4f49c"
SYNTHETIC_MERGE_COMMIT = "29b5b29981c684032151ef8d6d78a88d5bb77389"
BRANCH = "agent/iter241-iter240-repository-closure"
WORKFLOW_PATH = ".github/workflows/ci.yml"
WORKFLOW_DATABASE_ID = 309260095
CANDIDATE_WORKFLOW_SHA256 = (
    "7bab87602a7d3aea6b01458cce5c94fa0a49cc11d32188dbfcf0cd29148616d4"
)
COLLECTION_BOUNDARY = (
    "GitHub run, job, check, and synthetic-merge metadata plus the bounded "
    "observations emitted by the Iter245 bootstrap and authenticated runner; "
    "unrestricted logs, environment values, temporary paths, and credentials "
    "are not retained"
)
MAX_OBSERVATION_BYTES = 64 * 1024
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
UTC_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
FORBIDDEN_KEY = re.compile(
    r"(?:^|_)(?:raw|log|logs|env|environment|environ|secret|secrets|"
    r"credential|credentials|token|tokens)(?:_|$)"
)
ALLOWED_CONTROL_KEYS = {"ignore_environment"}


CONCLUSION = {
    "final_sealed_head_checks": "not_run",
    "hosted_bootstrap_observation_count": 4,
    "hosted_bootstrap_observation_passes": 4,
    "iter241_retry": "not_authorized",
    "merged_master_verification": "not_run",
    "preregistration_integrity": "valid",
    "pull_request_required_job_count": 2,
    "pull_request_required_job_passes": 2,
    "push_required_job_count": 2,
    "push_required_job_passes": 2,
    "remote_repository_integration": "supported",
    "scientific_authority": "absent",
}
EXTERNAL_SECURITY_CHECK = {
    "conclusion": "failure",
    "disposition": "occurrence_specific_git_object_false_positive",
    "general_security_approval": False,
    "name": "GitGuardian Security Checks",
    "required_by_default_branch_ruleset": False,
    "retained_classification_path": CLASSIFICATION,
}
RESULT_CAPTURE_CONTRACT = {
    "exact_schema_preregistered_before_observation": False,
    "frozen_category_requirements_path": (
        "experiments/iter245_offline_verified_python_bootstrap/HYPOTHESIS.md"
    ),
    "semantic_validator_role": "retrospective_same_operator_consistency_check",
    "semantic_validator_supplies_independent_attestation": False,
}
RUNNER_IMAGE = {
    "image": "ubuntu-24.04",
    "image_version": "20260714.240.1",
    "observed_in_job_ids": [
        88924514424,
        88924514501,
        88924522741,
        88924522834,
    ],
    "provisioner_version": "20260707.563",
    "runner_version": "2.336.0",
}
TRUST_OBSERVATION = {
    "bounded_observation": {
        "decision": "accept",
        "egid": 1001,
        "euid": 1001,
        "executable_absolute": True,
        "file_gid": 1001,
        "file_mode": "0700",
        "file_regular": True,
        "file_uid": 1001,
        "ignore_environment": 1,
        "isolated": 1,
        "no_user_site": 1,
        "owner_executable": True,
        "reason": None,
        "safe_path": True,
    },
    "identical_across_registered_jobs": True,
    "observed_in_job_ids": [
        88924514424,
        88924514501,
        88924522741,
        88924522834,
    ],
}

ASSET_SPECS = (
    {
        "matrix": "3.11",
        "version": "3.11.15",
        "observation_id": "python-3.11.15",
        "asset_id": 449621339,
        "size": 92521776,
        "sha256": "a972aa7e44f1596aa63274a9ac58dbc2349c321f3f78b1c0fc5a60d5d69a6402",
        "archive_member_count": 10544,
        "directory_count": 565,
        "regular_file_count": 9970,
        "symlink_count": 9,
        "uncompressed_regular_bytes": 305000600,
        "runpath": "/opt/hostedtoolcache/Python/3.11.15/x64/lib",
        "job_ids": [88924514501, 88924522741],
    },
    {
        "matrix": "3.12",
        "version": "3.12.13",
        "observation_id": "python-3.12.13",
        "asset_id": 449635535,
        "size": 94990593,
        "sha256": "ce7d511228f095b5ea1ad5568543388870f5964688303f9ddc24ba06c336bfba",
        "archive_member_count": 9339,
        "directory_count": 447,
        "regular_file_count": 8883,
        "symlink_count": 9,
        "uncompressed_regular_bytes": 306929490,
        "runpath": "/opt/hostedtoolcache/Python/3.12.13/x64/lib",
        "job_ids": [88924514424, 88924522834],
    },
)

RUN_SPECS = (
    {
        "event": "push",
        "run_id": 29920504274,
        "created_at": "2026-07-22T12:39:17Z",
        "started_at": "2026-07-22T12:39:17Z",
        "updated_at": "2026-07-22T12:44:40Z",
        "jobs": (
            {
                "matrix": "3.12",
                "job_id": 88924514424,
                "runner_id": 1000014799,
                "started_at": "2026-07-22T12:39:19Z",
                "completed_at": "2026-07-22T12:44:39Z",
                "steps": {
                    "bootstrap": (
                        "2026-07-22T12:39:24Z",
                        "2026-07-22T12:39:32Z",
                    ),
                    "tests": (
                        "2026-07-22T12:39:39Z",
                        "2026-07-22T12:42:59Z",
                    ),
                    "full_clean_tree": (
                        "2026-07-22T12:43:59Z",
                        "2026-07-22T12:43:59Z",
                    ),
                },
            },
            {
                "matrix": "3.11",
                "job_id": 88924514501,
                "runner_id": 1000014800,
                "started_at": "2026-07-22T12:39:20Z",
                "completed_at": "2026-07-22T12:44:26Z",
                "steps": {
                    "bootstrap": (
                        "2026-07-22T12:39:25Z",
                        "2026-07-22T12:39:36Z",
                    ),
                    "tests": (
                        "2026-07-22T12:39:42Z",
                        "2026-07-22T12:42:44Z",
                    ),
                    "full_clean_tree": (
                        "2026-07-22T12:43:37Z",
                        "2026-07-22T12:43:38Z",
                    ),
                },
            },
        ),
    },
    {
        "event": "pull_request",
        "run_id": 29920506702,
        "created_at": "2026-07-22T12:39:19Z",
        "started_at": "2026-07-22T12:39:19Z",
        "updated_at": "2026-07-22T12:45:13Z",
        "jobs": (
            {
                "matrix": "3.11",
                "job_id": 88924522741,
                "runner_id": 1000014801,
                "started_at": "2026-07-22T12:39:22Z",
                "completed_at": "2026-07-22T12:44:29Z",
                "steps": {
                    "bootstrap": (
                        "2026-07-22T12:39:27Z",
                        "2026-07-22T12:39:37Z",
                    ),
                    "tests": (
                        "2026-07-22T12:39:44Z",
                        "2026-07-22T12:42:46Z",
                    ),
                    "full_clean_tree": (
                        "2026-07-22T12:43:39Z",
                        "2026-07-22T12:43:39Z",
                    ),
                },
            },
            {
                "matrix": "3.12",
                "job_id": 88924522834,
                "runner_id": 1000014802,
                "started_at": "2026-07-22T12:39:22Z",
                "completed_at": "2026-07-22T12:45:12Z",
                "steps": {
                    "bootstrap": (
                        "2026-07-22T12:39:27Z",
                        "2026-07-22T12:39:36Z",
                    ),
                    "tests": (
                        "2026-07-22T12:39:42Z",
                        "2026-07-22T12:43:00Z",
                    ),
                    "full_clean_tree": (
                        "2026-07-22T12:43:58Z",
                        "2026-07-22T12:43:58Z",
                    ),
                },
            },
        ),
    },
)


@dataclass(frozen=True)
class ListOf:
    """Schema marker for a homogeneous JSON array."""

    item: Any


STEP_SCHEMA = {
    "completed_at": str,
    "conclusion": str,
    "started_at": str,
}
JOB_SCHEMA = {
    "completed_at": str,
    "conclusion": str,
    "job_id": int,
    "matrix": str,
    "name": str,
    "observation_ref": str,
    "runner": {
        "group_id": int,
        "group_name": str,
        "id": int,
        "labels": ListOf(str),
        "name": str,
    },
    "selected_steps": {
        "bootstrap": STEP_SCHEMA,
        "full_clean_tree": STEP_SCHEMA,
        "tests": STEP_SCHEMA,
    },
    "started_at": str,
    "status": str,
    "url": str,
}
RUN_SCHEMA = {
    "attempt": int,
    "conclusion": str,
    "created_at": str,
    "event": str,
    "head_branch": str,
    "head_sha": str,
    "jobs": ListOf(JOB_SCHEMA),
    "run_id": int,
    "started_at": str,
    "status": str,
    "updated_at": str,
    "url": str,
}
OBSERVATION_SCHEMA = {
    "candidate": {
        "commit": str,
        "pull_request": {
            "base_branch": str,
            "base_commit": str,
            "head_branch": str,
            "head_commit": str,
            "number": int,
            "synthetic_merge_commit": str,
            "synthetic_merge_parents": ListOf(str),
            "synthetic_merge_tree": str,
            "synthetic_tree_matches_candidate": bool,
        },
        "tree": str,
    },
    "collection_boundary": str,
    "conclusion": {
        "final_sealed_head_checks": str,
        "hosted_bootstrap_observation_count": int,
        "hosted_bootstrap_observation_passes": int,
        "iter241_retry": str,
        "merged_master_verification": str,
        "preregistration_integrity": str,
        "pull_request_required_job_count": int,
        "pull_request_required_job_passes": int,
        "push_required_job_count": int,
        "push_required_job_passes": int,
        "remote_repository_integration": str,
        "scientific_authority": str,
    },
    "external_security_check": {
        "conclusion": str,
        "disposition": str,
        "general_security_approval": bool,
        "name": str,
        "required_by_default_branch_ruleset": bool,
        "retained_classification_path": str,
    },
    "matrix_observations": ListOf(
        {
            "archive_extraction": {
                "archive_member_count": int,
                "archive_sha256": str,
                "archive_size": int,
                "direct_needed_count": int,
                "directory_count": int,
                "program_interpreter": str,
                "regular_file_count": int,
                "rpath_present": bool,
                "runpath": str,
                "symlink_count": int,
                "uncompressed_regular_bytes": int,
            },
            "bootstrap_summary": {
                "byte_count": int,
                "final_host": str,
                "matrix": str,
                "python": str,
                "redirect_count": int,
                "registered_asset_id": int,
                "sha256": str,
                "tree_group_or_world_writable": bool,
                "upstream_setup_executed": bool,
            },
            "first_python": {
                "flags": {
                    "ignore_environment": int,
                    "isolated": int,
                    "no_user_site": int,
                    "safe_path": bool,
                },
                "libpython_contained": bool,
                "pip_contained": bool,
                "prefixes_contained": bool,
                "version": str,
            },
            "identical_across_registered_events": bool,
            "matrix": str,
            "observation_id": str,
            "observed_in_job_ids": ListOf(int),
            "retained_tree_validation": {
                "direct_needed_count": int,
                "program_interpreter": str,
                "rpath_present": bool,
                "runpath": str,
            },
        }
    ),
    "python_trust_observation": {
        "bounded_observation": {
            "decision": str,
            "egid": int,
            "euid": int,
            "executable_absolute": bool,
            "file_gid": int,
            "file_mode": str,
            "file_regular": bool,
            "file_uid": int,
            "ignore_environment": int,
            "isolated": int,
            "no_user_site": int,
            "owner_executable": bool,
            "reason": type(None),
            "safe_path": bool,
        },
        "identical_across_registered_jobs": bool,
        "observed_in_job_ids": ListOf(int),
    },
    "result_capture_contract": {
        "exact_schema_preregistered_before_observation": bool,
        "frozen_category_requirements_path": str,
        "semantic_validator_role": str,
        "semantic_validator_supplies_independent_attestation": bool,
    },
    "runner_image": {
        "image": str,
        "image_version": str,
        "observed_in_job_ids": ListOf(int),
        "provisioner_version": str,
        "runner_version": str,
    },
    "runs": ListOf(RUN_SCHEMA),
    "schema_version": str,
    "workflow": {
        "database_id": int,
        "path": str,
        "sha256": str,
    },
}


class DuplicateKeyError(ValueError):
    """Raised when bounded evidence contains an ambiguous JSON mapping."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


def _schema_errors(value: Any, schema: Any, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(schema, ListOf):
        if type(value) is not list:
            return [f"{path}: expected an array"]
        for index, item in enumerate(value):
            errors.extend(_schema_errors(item, schema.item, f"{path}[{index}]"))
        return errors
    if isinstance(schema, dict):
        if type(value) is not dict:
            return [f"{path}: expected an object"]
        if set(value) != set(schema):
            errors.append(f"{path}: exact fields differ")
        for key in sorted(set(value) & set(schema)):
            errors.extend(_schema_errors(value[key], schema[key], f"{path}.{key}"))
        return errors
    if type(value) is not schema:
        errors.append(f"{path}: exact scalar type differs")
    return errors


def _forbidden_field_errors(value: Any, path: str = "observation") -> list[str]:
    errors: list[str] = []
    if type(value) is dict:
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")
            if normalized not in ALLOWED_CONTROL_KEYS and (
                FORBIDDEN_KEY.search(normalized)
                or any(
                    marker in normalized
                    for marker in ("raw_log", "temporary_path", "temp_path")
                )
            ):
                errors.append(f"{path}.{key}: forbidden retained field")
            errors.extend(_forbidden_field_errors(child, f"{path}.{key}"))
    elif type(value) is list:
        for index, child in enumerate(value):
            errors.extend(_forbidden_field_errors(child, f"{path}[{index}]"))
    return errors


def _expect(errors: list[str], actual: Any, expected: Any, path: str) -> None:
    if actual != expected:
        errors.append(f"{path} differs")


def _timestamp(value: str, path: str, errors: list[str]) -> datetime | None:
    if UTC_TIMESTAMP.fullmatch(value) is None:
        errors.append(f"{path}: timestamp format differs")
        return None
    try:
        return datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError:
        errors.append(f"{path}: timestamp is invalid")
        return None


def _validate_candidate(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    candidate = document["candidate"]
    pull_request = candidate["pull_request"]
    expected = {
        "commit": CANDIDATE_COMMIT,
        "tree": CANDIDATE_TREE,
    }
    for key, value in expected.items():
        _expect(errors, candidate[key], value, f"candidate.{key}")
    pull_expected = {
        "base_branch": "master",
        "base_commit": BASE_COMMIT,
        "head_branch": BRANCH,
        "head_commit": CANDIDATE_COMMIT,
        "number": 90,
        "synthetic_merge_commit": SYNTHETIC_MERGE_COMMIT,
        "synthetic_merge_parents": [BASE_COMMIT, CANDIDATE_COMMIT],
        "synthetic_merge_tree": CANDIDATE_TREE,
        "synthetic_tree_matches_candidate": True,
    }
    for key, value in pull_expected.items():
        _expect(errors, pull_request[key], value, f"candidate.pull_request.{key}")
    if pull_request["head_commit"] != candidate["commit"]:
        errors.append("candidate.pull_request.head_commit is not candidate.commit")
    if pull_request["synthetic_merge_tree"] != candidate["tree"]:
        errors.append("candidate synthetic merge tree is not candidate.tree")
    if pull_request["synthetic_merge_parents"] != [
        pull_request["base_commit"],
        candidate["commit"],
    ]:
        errors.append("candidate synthetic merge ordered parents differ")
    for path, value in (
        ("candidate.commit", candidate["commit"]),
        ("candidate.tree", candidate["tree"]),
        ("candidate.pull_request.base_commit", pull_request["base_commit"]),
        (
            "candidate.pull_request.synthetic_merge_commit",
            pull_request["synthetic_merge_commit"],
        ),
        (
            "candidate.pull_request.synthetic_merge_tree",
            pull_request["synthetic_merge_tree"],
        ),
    ):
        if HEX40.fullmatch(value) is None:
            errors.append(f"{path}: Git object ID format differs")
    return errors


def _validate_matrix(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    observations = document["matrix_observations"]
    if len(observations) != 2:
        return ["matrix observation census differs"]
    expected_flags = {
        "ignore_environment": 1,
        "isolated": 1,
        "no_user_site": 1,
        "safe_path": True,
    }
    for index, (observation, spec) in enumerate(zip(observations, ASSET_SPECS)):
        prefix = f"matrix_observations[{index}]"
        archive = observation["archive_extraction"]
        summary = observation["bootstrap_summary"]
        first_python = observation["first_python"]
        retained = observation["retained_tree_validation"]
        direct_expected = {
            "matrix": spec["matrix"],
            "observation_id": spec["observation_id"],
            "observed_in_job_ids": spec["job_ids"],
            "identical_across_registered_events": True,
        }
        for key, value in direct_expected.items():
            _expect(errors, observation[key], value, f"{prefix}.{key}")
        archive_expected = {
            "archive_member_count": spec["archive_member_count"],
            "archive_sha256": spec["sha256"],
            "archive_size": spec["size"],
            "direct_needed_count": 2,
            "directory_count": spec["directory_count"],
            "program_interpreter": "/lib64/ld-linux-x86-64.so.2",
            "regular_file_count": spec["regular_file_count"],
            "rpath_present": False,
            "runpath": spec["runpath"],
            "symlink_count": spec["symlink_count"],
            "uncompressed_regular_bytes": spec["uncompressed_regular_bytes"],
        }
        for key, value in archive_expected.items():
            _expect(errors, archive[key], value, f"{prefix}.archive_extraction.{key}")
        if archive["archive_member_count"] != (
            archive["directory_count"]
            + archive["regular_file_count"]
            + archive["symlink_count"]
        ):
            errors.append(f"{prefix}.archive_extraction inventory count is inconsistent")
        summary_expected = {
            "byte_count": spec["size"],
            "final_host": "release-assets.githubusercontent.com",
            "matrix": spec["matrix"],
            "python": spec["version"],
            "redirect_count": 1,
            "registered_asset_id": spec["asset_id"],
            "sha256": spec["sha256"],
            "tree_group_or_world_writable": False,
            "upstream_setup_executed": False,
        }
        for key, value in summary_expected.items():
            _expect(errors, summary[key], value, f"{prefix}.bootstrap_summary.{key}")
        first_expected = {
            "flags": expected_flags,
            "libpython_contained": True,
            "pip_contained": True,
            "prefixes_contained": True,
            "version": spec["version"],
        }
        for key, value in first_expected.items():
            _expect(errors, first_python[key], value, f"{prefix}.first_python.{key}")
        retained_expected = {
            key: archive[key]
            for key in (
                "direct_needed_count",
                "program_interpreter",
                "rpath_present",
                "runpath",
            )
        }
        _expect(
            errors,
            retained,
            retained_expected,
            f"{prefix}.retained_tree_validation",
        )
        if summary["byte_count"] != archive["archive_size"]:
            errors.append(f"{prefix} archive byte observations disagree")
        if summary["sha256"] != archive["archive_sha256"]:
            errors.append(f"{prefix} archive digest observations disagree")
    return errors


def _validate_runs(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    runs = document["runs"]
    if len(runs) != 2:
        return ["run event census differs"]
    if [run["event"] for run in runs] != ["push", "pull_request"]:
        errors.append("run event census differs")
    seen_job_ids: list[int] = []
    matrix_job_ids: dict[str, list[int]] = {"3.11": [], "3.12": []}
    for run_index, (run, spec) in enumerate(zip(runs, RUN_SPECS)):
        event = spec["event"]
        prefix = f"runs.{event}"
        run_expected = {
            "attempt": 1,
            "conclusion": "success",
            "created_at": spec["created_at"],
            "event": event,
            "head_branch": BRANCH,
            "head_sha": CANDIDATE_COMMIT,
            "run_id": spec["run_id"],
            "started_at": spec["started_at"],
            "status": "completed",
            "updated_at": spec["updated_at"],
            "url": (
                "https://github.com/manfromnowhere143/telos/actions/runs/"
                f"{spec['run_id']}"
            ),
        }
        for key, value in run_expected.items():
            _expect(errors, run[key], value, f"{prefix}.{key}")
        if len(run["jobs"]) != 2:
            errors.append(f"{prefix}.jobs census differs")
            continue
        run_created = _timestamp(run["created_at"], f"{prefix}.created_at", errors)
        run_started = _timestamp(run["started_at"], f"{prefix}.started_at", errors)
        run_updated = _timestamp(run["updated_at"], f"{prefix}.updated_at", errors)
        if (
            run_created is not None
            and run_started is not None
            and run_updated is not None
            and not run_created <= run_started <= run_updated
        ):
            errors.append(f"{prefix} timestamp order differs")
        for job_index, (job, job_spec) in enumerate(zip(run["jobs"], spec["jobs"])):
            matrix = job_spec["matrix"]
            job_prefix = f"{prefix}.jobs.{matrix}"
            job_id = job_spec["job_id"]
            runner_id = job_spec["runner_id"]
            asset = next(item for item in ASSET_SPECS if item["matrix"] == matrix)
            job_expected = {
                "completed_at": job_spec["completed_at"],
                "conclusion": "success",
                "job_id": job_id,
                "matrix": matrix,
                "name": f"verify {event} py{matrix}",
                "observation_ref": asset["observation_id"],
                "started_at": job_spec["started_at"],
                "status": "completed",
                "url": (
                    "https://github.com/manfromnowhere143/telos/actions/runs/"
                    f"{spec['run_id']}/job/{job_id}"
                ),
            }
            for key, value in job_expected.items():
                _expect(errors, job[key], value, f"{job_prefix}.{key}")
            runner_expected = {
                "group_id": 0,
                "group_name": "GitHub Actions",
                "id": runner_id,
                "labels": ["ubuntu-24.04"],
                "name": f"GitHub Actions {runner_id}",
            }
            _expect(errors, job["runner"], runner_expected, f"{job_prefix}.runner")
            seen_job_ids.append(job["job_id"])
            if job["matrix"] in matrix_job_ids:
                matrix_job_ids[job["matrix"]].append(job["job_id"])
            ordered_times: list[datetime] = []
            for step_name in ("bootstrap", "tests", "full_clean_tree"):
                step = job["selected_steps"][step_name]
                expected_start, expected_complete = job_spec["steps"][step_name]
                step_expected = {
                    "completed_at": expected_complete,
                    "conclusion": "success",
                    "started_at": expected_start,
                }
                _expect(
                    errors,
                    step,
                    step_expected,
                    f"{job_prefix}.selected_steps.{step_name}",
                )
                start = _timestamp(
                    step["started_at"],
                    f"{job_prefix}.selected_steps.{step_name}.started_at",
                    errors,
                )
                complete = _timestamp(
                    step["completed_at"],
                    f"{job_prefix}.selected_steps.{step_name}.completed_at",
                    errors,
                )
                if start is not None and complete is not None:
                    ordered_times.extend((start, complete))
            job_started = _timestamp(job["started_at"], f"{job_prefix}.started_at", errors)
            job_completed = _timestamp(
                job["completed_at"], f"{job_prefix}.completed_at", errors
            )
            if (
                job_started is not None
                and job_completed is not None
                and len(ordered_times) == 6
                and not (
                    job_started
                    <= ordered_times[0]
                    <= ordered_times[1]
                    <= ordered_times[2]
                    <= ordered_times[3]
                    <= ordered_times[4]
                    <= ordered_times[5]
                    <= job_completed
                )
            ):
                errors.append(f"{job_prefix} required-step order differs")
            if (
                run_created is not None
                and run_updated is not None
                and job_started is not None
                and job_completed is not None
                and not run_created <= job_started <= job_completed <= run_updated
            ):
                errors.append(f"{job_prefix} falls outside its run interval")
    expected_all_jobs = RUNNER_IMAGE["observed_in_job_ids"]
    if seen_job_ids != expected_all_jobs:
        errors.append("exact run/job identity census differs")
    for spec in ASSET_SPECS:
        if matrix_job_ids[spec["matrix"]] != spec["job_ids"]:
            errors.append(f"job census for matrix {spec['matrix']} differs")
    if len(seen_job_ids) != len(set(seen_job_ids)):
        errors.append("job IDs are not unique")
    return errors


def _git(
    root: Path,
    *arguments: str,
) -> subprocess.CompletedProcess[bytes]:
    env = os.environ.copy()
    for name in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_NAMESPACE",
    ):
        env.pop(name, None)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        timeout=15,
    )


def _validate_git(document: dict[str, Any], root: Path) -> list[str]:
    """Bind local Git facts; absence of the old synthetic object is permitted.

    The retained synthetic identity came from hosted metadata.  If that object
    happens to be local, its parents and tree are checked too, but this
    retrospective validator never treats local availability as attestation.
    """

    errors: list[str] = []
    candidate = document["candidate"]
    pull_request = candidate["pull_request"]
    for label, object_id in (
        ("candidate commit", candidate["commit"]),
        ("pull-request base commit", pull_request["base_commit"]),
    ):
        result = _git(root, "cat-file", "-t", object_id)
        if result.returncode != 0 or result.stdout.strip() != b"commit":
            errors.append(f"Git {label} is not a retained commit object")
    tree = _git(root, "rev-parse", f"{candidate['commit']}^{{tree}}")
    if tree.returncode != 0 or tree.stdout.decode("ascii", "replace").strip() != candidate["tree"]:
        errors.append("Git candidate commit tree differs")
    base_tree = _git(root, "rev-parse", f"{pull_request['base_commit']}^{{tree}}")
    if base_tree.returncode != 0 or base_tree.stdout.decode("ascii", "replace").strip() != BASE_TREE:
        errors.append("Git pull-request base tree differs")
    ancestry = _git(
        root,
        "merge-base",
        "--is-ancestor",
        pull_request["base_commit"],
        candidate["commit"],
    )
    if ancestry.returncode != 0:
        errors.append("Git pull-request base is not an ancestor of the candidate")
    head_ancestry = _git(root, "merge-base", "--is-ancestor", candidate["commit"], "HEAD")
    if head_ancestry.returncode != 0:
        errors.append("Git candidate is not an ancestor of HEAD")
    workflow = _git(root, "show", f"{candidate['commit']}:{WORKFLOW_PATH}")
    if workflow.returncode != 0:
        errors.append("Git candidate workflow blob is unavailable")
    elif hashlib.sha256(workflow.stdout).hexdigest() != document["workflow"]["sha256"]:
        errors.append("Git candidate workflow blob digest differs")
    synthetic = _git(root, "cat-file", "-t", pull_request["synthetic_merge_commit"])
    if synthetic.returncode == 0:
        if synthetic.stdout.strip() != b"commit":
            errors.append("Git synthetic merge identity is not a commit object")
        else:
            metadata = _git(
                root,
                "show",
                "-s",
                "--format=%P%n%T",
                pull_request["synthetic_merge_commit"],
            )
            lines = metadata.stdout.decode("ascii", "replace").splitlines()
            if metadata.returncode != 0 or len(lines) != 2:
                errors.append("Git synthetic merge metadata is unavailable")
            else:
                if lines[0].split() != pull_request["synthetic_merge_parents"]:
                    errors.append("Git synthetic merge ordered parents differ")
                if lines[1] != pull_request["synthetic_merge_tree"]:
                    errors.append("Git synthetic merge tree differs")
    return errors


def _validate_classification(document: dict[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    relative = Path(document["external_security_check"]["retained_classification_path"])
    if relative.is_absolute() or ".." in relative.parts:
        return ["external GitGuardian classification path is unsafe"]
    path = root / relative
    try:
        raw = path.read_bytes()
        classification = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        return [f"external GitGuardian classification is unreadable: {type(exc).__name__}"]
    if type(classification) is not dict:
        return ["external GitGuardian classification root differs"]
    check_run = classification.get("check_run")
    if not isinstance(check_run, dict) or {
        "name": check_run.get("name"),
        "conclusion": check_run.get("conclusion"),
    } != {
        "name": "GitGuardian Security Checks",
        "conclusion": "failure",
    }:
        errors.append("external GitGuardian retained failed check differs")
    if classification.get("general_security_approval") is not False:
        errors.append("external GitGuardian classification grants security approval")
    if classification.get("classification") != (
        "four occurrence-specific false positives; no credential was identified"
    ):
        errors.append("external GitGuardian occurrence-specific classification differs")
    dashboard = classification.get("dashboard_disposition")
    if not isinstance(dashboard, dict) or (
        dashboard.get("attempted") is not False or dashboard.get("status") != "blocked"
    ):
        errors.append("external GitGuardian blocked dashboard disposition differs")
    if classification.get("occurrence_count") != 4 or classification.get(
        "unique_value_count"
    ) != 2:
        errors.append("external GitGuardian occurrence census differs")
    incidents = classification.get("incidents")
    object_pairs: list[tuple[Any, Any]] = []
    if isinstance(incidents, list):
        for incident in incidents:
            if isinstance(incident, dict) and isinstance(incident.get("object"), dict):
                object_pairs.append(
                    (
                        incident["object"].get("object_type"),
                        incident["object"].get("object_id"),
                    )
                )
    if object_pairs != [("tree", BASE_TREE), ("commit", BASE_COMMIT)]:
        errors.append("external GitGuardian Git-object identities differ")
    return errors


def semantic_errors(document: dict[str, Any], *, root: Path = ROOT) -> list[str]:
    """Return consistency failures without claiming independent attestation."""

    errors: list[str] = []
    _expect(errors, document["schema_version"], SCHEMA_VERSION, "schema_version")
    _expect(
        errors,
        document["collection_boundary"],
        COLLECTION_BOUNDARY,
        "collection_boundary",
    )
    _expect(errors, document["conclusion"], CONCLUSION, "conclusion")
    _expect(
        errors,
        document["external_security_check"],
        EXTERNAL_SECURITY_CHECK,
        "external_security_check",
    )
    _expect(
        errors,
        document["result_capture_contract"],
        RESULT_CAPTURE_CONTRACT,
        "result_capture_contract",
    )
    _expect(errors, document["runner_image"], RUNNER_IMAGE, "runner_image")
    _expect(
        errors,
        document["python_trust_observation"],
        TRUST_OBSERVATION,
        "python_trust_observation",
    )
    workflow_expected = {
        "database_id": WORKFLOW_DATABASE_ID,
        "path": WORKFLOW_PATH,
        "sha256": CANDIDATE_WORKFLOW_SHA256,
    }
    _expect(errors, document["workflow"], workflow_expected, "workflow")
    errors.extend(_validate_candidate(document))
    errors.extend(_validate_matrix(document))
    errors.extend(_validate_runs(document))
    all_job_ids = RUNNER_IMAGE["observed_in_job_ids"]
    if document["runner_image"]["observed_in_job_ids"] != all_job_ids:
        errors.append("runner image job census differs")
    if document["python_trust_observation"]["observed_in_job_ids"] != all_job_ids:
        errors.append("Python trust observation job census differs")
    errors.extend(_validate_git(document, root))
    errors.extend(_validate_classification(document, root))
    return errors


def validation_errors(raw: bytes, *, root: Path = ROOT) -> list[str]:
    """Validate exact bounded structure and retrospective semantic consistency."""

    errors: list[str] = []
    if len(raw) > MAX_OBSERVATION_BYTES:
        errors.append("observation exceeds the bounded byte limit")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return [*errors, "observation is not UTF-8"]
    try:
        document = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (DuplicateKeyError, ValueError, json.JSONDecodeError) as exc:
        return [*errors, f"observation JSON is not strict: {type(exc).__name__}"]
    canonical = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if raw != canonical:
        errors.append("observation JSON is not canonical")
    errors.extend(_forbidden_field_errors(document))
    schema_failures = _schema_errors(document, OBSERVATION_SCHEMA, "observation")
    errors.extend(schema_failures)
    if schema_failures:
        return errors
    errors.extend(semantic_errors(document, root=root))
    return errors


def main() -> int:
    try:
        raw = OBSERVATION.read_bytes()
    except OSError as exc:
        print(
            "Iter245 retrospective remote-CI result consistency guard failed: "
            f"observation is unreadable ({type(exc).__name__})",
            file=sys.stderr,
        )
        return 1
    errors = validation_errors(raw)
    if errors:
        print(
            "Iter245 retrospective remote-CI result consistency guard failed:",
            file=sys.stderr,
        )
        for error in errors:
            print(f" - {error}", file=sys.stderr)
        return 1
    print(
        "Iter245 retrospective same-operator remote-CI consistency guard: pass; "
        "exact bounded schema, registered identities, Git ancestry, run/job "
        "censuses, successful required steps, runner/archive/trust observations, "
        "synthetic-merge metadata, explicit not-run states, and separate red "
        "GitGuardian disposition agree. This is not independent attestation."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
