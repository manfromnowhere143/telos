#!/usr/bin/env python3
"""Capture the bounded, read-only remote closure evidence for iter239.

This program has one deliberately explicit live mode.  It performs exactly
nine GET requests to fixed GitHub REST paths, performs no retry or redirect,
and publishes no partial acceptance artifact.  The separately implemented
offline validator is the authority for interpreting the retained bytes.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import http.client
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROOF = (
    ROOT
    / "experiments"
    / "iter240_ground_truth_admission_design"
    / "proof"
)
RAW_ROOT = PROOF / "raw" / "iter239_remote_acceptance"
RECEIPT = PROOF / "iter239_remote_acceptance.json"
ATTEMPT_FILENAME = "capture_attempt.json"
API_HOST = "api.github.com"
API_VERSION = "2026-03-10"
REPOSITORY = "manfromnowhere143/telos"
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
HEX40 = re.compile(r"^[0-9a-f]{40}$")

COMPLETED_EVIDENCE = "35a97b228afb7bd8eb44e71749986ee59020b25b"
COMPLETED_EVIDENCE_TREE = "16df636427548ffc3b0ed0a4afd9fc15d7c6f255"
ITER239_EXPERIMENT_TREE = "bb4cac9b92c32d89d32d6d64509288022751142d"
SEALED_TIP = "56fb78f5f8afcd8709fde1170e8422072626f367"
SEALED_TIP_TREE = "776f60e7c75616767ce6bb1e45a3eb7279f37a97"
PREDECESSOR_MASTER = "fb87af7eb15b5235a722a7bb3fd3a48962019188"
MERGE_COMMIT = "b597b763f2eb52b2f4f2d36e7daaa31654be076b"
AUTHORIZATION_COMMIT = "cf809ac0e06f37127553e99a2ab9b0705f8e2fae"
ACTIVATION_COMMIT = "63f5786b9b5c60d2bea90f2077208cfb745c31a2"
WORKFLOW_ID = 309260095
WORKFLOW_PATH = ".github/workflows/ci.yml"
INTEGRATION_ID = 15368
RULESET_ID = 19177100

ENDPOINTS = (
    (
        "pull_request_87",
        f"/repos/{REPOSITORY}/pulls/87",
        "pull_request_87.json",
    ),
    (
        "sealed_push_run",
        f"/repos/{REPOSITORY}/actions/runs/29701167247",
        "sealed_push_run.json",
    ),
    (
        "sealed_pr_run",
        f"/repos/{REPOSITORY}/actions/runs/29701168051",
        "sealed_pr_run.json",
    ),
    (
        "sealed_tip_check_runs",
        (
            f"/repos/{REPOSITORY}/commits/{SEALED_TIP}/check-runs"
            "?filter=all&per_page=100&page=1"
        ),
        "sealed_tip_check_runs.json",
    ),
    (
        "merged_master_run",
        f"/repos/{REPOSITORY}/actions/runs/29701305166",
        "merged_master_run.json",
    ),
    (
        "merged_master_check_runs",
        (
            f"/repos/{REPOSITORY}/commits/{MERGE_COMMIT}/check-runs"
            "?filter=all&per_page=100&page=1"
        ),
        "merged_master_check_runs.json",
    ),
    (
        "master_branch",
        f"/repos/{REPOSITORY}/branches/master",
        "master_branch.json",
    ),
    (
        "ruleset",
        f"/repos/{REPOSITORY}/rulesets/{RULESET_ID}",
        "ruleset.json",
    ),
    (
        "effective_rules",
        f"/repos/{REPOSITORY}/rules/branches/master?per_page=100&page=1",
        "effective_rules.json",
    ),
)
MINIMUM_FREE_BYTES = MAX_RESPONSE_BYTES * len(ENDPOINTS) * 3

EXPECTED_CHECKS = (
    {
        "name": "verify push py3.11",
        "event": "push",
        "run_id": 29701167247,
        "check_run_id": 88230357876,
        "head_sha": SEALED_TIP,
    },
    {
        "name": "verify push py3.12",
        "event": "push",
        "run_id": 29701167247,
        "check_run_id": 88230357837,
        "head_sha": SEALED_TIP,
    },
    {
        "name": "verify pull_request py3.11",
        "event": "pull_request",
        "run_id": 29701168051,
        "check_run_id": 88230359868,
        "head_sha": SEALED_TIP,
    },
    {
        "name": "verify pull_request py3.12",
        "event": "pull_request",
        "run_id": 29701168051,
        "check_run_id": 88230359882,
        "head_sha": SEALED_TIP,
    },
    {
        "name": "verify push py3.11",
        "event": "push",
        "run_id": 29701305166,
        "check_run_id": 88230707891,
        "head_sha": MERGE_COMMIT,
    },
    {
        "name": "verify push py3.12",
        "event": "push",
        "run_id": 29701305166,
        "check_run_id": 88230707870,
        "head_sha": MERGE_COMMIT,
    },
)

RETAINED_INPUTS = (
    (
        "experiments/iter239_repository_governance/policy.json",
        "c0cd140f004f760c568c02c3857c80d252c098fa1590453f3930480904b4531c",
    ),
    (
        "experiments/iter239_repository_governance/proof/after_state.json",
        "b8db7c38768c665d6d69488ecee780986baefde86cd56563813fd921ffcab530",
    ),
    (
        "experiments/iter239_repository_governance/proof/mutation_receipt.json",
        "86da5a78b891694bd969a8adc309c238bc2f32d00ed97f30a1f4522defdc5674",
    ),
    (
        "experiments/iter239_repository_governance/proof/operational_check.json",
        "6f861dd0c65f9009fb5adc796ce89fdb7f942980cf3dac3416d8f943dc8a7c61",
    ),
    (
        "experiments/iter239_repository_governance/RESULT.md",
        "8ffcde5bce96c40f8b49494806973e5e46a4e108e5a570b5a9765df6090d1a82",
    ),
    (
        "scripts/validate_iter239_repository_governance.py",
        "4d6a613a2d406c784f2c35175f707498f9cbcc773cc500ecf5cfd273c315c5b9",
    ),
)


class CaptureError(RuntimeError):
    """A fixed read-only capture precondition was not satisfied."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise CaptureError(f"duplicate JSON key in GitHub response: {key}")
        value[key] = item
    return value


def _reject_nonfinite(value: str) -> None:
    raise CaptureError(f"non-finite JSON value in GitHub response: {value}")


def strict_json(raw: bytes, *, label: str) -> Any:
    try:
        return json.loads(
            raw,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise CaptureError(f"invalid JSON response for {label}: {exc}") from exc


def canonical_json(value: Any) -> bytes:
    try:
        rendered = json.dumps(
            value,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise CaptureError(f"cannot render canonical JSON: {exc}") from exc
    return (rendered + "\n").encode("utf-8")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def local_git_projection() -> dict[str, Any]:
    return {
        "completed_evidence_commit": COMPLETED_EVIDENCE,
        "completed_evidence_tree": COMPLETED_EVIDENCE_TREE,
        "iter239_experiment_tree": ITER239_EXPERIMENT_TREE,
        "sealed_tip_commit": SEALED_TIP,
        "sealed_tip_parent": COMPLETED_EVIDENCE,
        "sealed_tip_tree": SEALED_TIP_TREE,
        "predecessor_master": PREDECESSOR_MASTER,
        "merge_commit": MERGE_COMMIT,
        "merge_parents": [PREDECESSOR_MASTER, SEALED_TIP],
        "merge_tree": SEALED_TIP_TREE,
        "iter240_authorization_commit": AUTHORIZATION_COMMIT,
        "iter240_authorization_parent": MERGE_COMMIT,
        "iter240_activation_commit": ACTIVATION_COMMIT,
        "iter240_activation_parent": AUTHORIZATION_COMMIT,
        "iter240_hypothesis_sha256": (
            "0f1924318e94a6155eaa1939fe7508746e82e4cdbe0ea8758fdb66f32d3b383d"
        ),
    }


def retained_input_projection() -> list[dict[str, str]]:
    return [{"path": path, "sha256": digest} for path, digest in RETAINED_INPUTS]


def request_plan() -> list[dict[str, str]]:
    return [
        {
            "method": "GET",
            "name": name,
            "request_path": request_path,
        }
        for name, request_path, _filename in ENDPOINTS
    ]


def regular_0644(path: Path, *, label: str) -> None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CaptureError(f"{label} is unavailable: {path}") from exc
    if (
        not path.is_file()
        or path.is_symlink()
        or (metadata.st_mode & 0o777) != 0o644
    ):
        raise CaptureError(f"{label} is not a regular nonsymlink 0644 file")


def safe_directory(path: Path, *, label: str) -> None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CaptureError(f"{label} is unavailable: {path}") from exc
    if not path.is_dir() or path.is_symlink() or (metadata.st_mode & 0o022):
        raise CaptureError(
            f"{label} is not a nonsymlink directory without group/other write"
        )


def fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def load_exact_source_module(path: Path, name: str) -> Any:
    regular_0644(path, label=f"exact-source module {path.name}")
    try:
        raw = path.read_bytes()
        code = compile(raw, str(path), "exec", dont_inherit=True)
    except (OSError, SyntaxError, UnicodeError, ValueError) as exc:
        raise CaptureError(f"cannot compile exact source bytes: {path}: {exc}") from exc
    spec = importlib.util.spec_from_file_location(
        name,
        path,
    )
    if spec is None or spec.loader is None:
        raise CaptureError(f"cannot create exact-source module: {path}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name)
    sys.modules[name] = module
    try:
        exec(code, module.__dict__)
    except Exception as exc:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
        raise CaptureError(f"cannot execute exact source bytes: {path}: {exc}") from exc
    module.__exact_source_sha256__ = sha256(raw)
    module.__exact_source_byte_count__ = len(raw)
    return module


def _load_offline_validator() -> Any:
    return load_exact_source_module(
        ROOT / "scripts/validate_iter239_remote_acceptance.py",
        "telos_iter239_remote_acceptance_preflight",
    )


def require_unattempted() -> None:
    if os.path.lexists(RECEIPT) or os.path.lexists(RAW_ROOT):
        raise CaptureError(
            "remote acceptance attempt/output already exists; refusing any rerun"
        )


def preflight_capture() -> Any:
    require_unattempted()
    if RECEIPT.parent != PROOF or RAW_ROOT.parent.parent != PROOF:
        raise CaptureError("remote acceptance output paths differ from the fixed plan")
    if ROOT.resolve() != ROOT:
        raise CaptureError("repository root is a symlink or noncanonical path")
    for path, label in (
        (ROOT, "repository root"),
        (ROOT / "scripts", "scripts directory"),
        (ROOT / "experiments", "experiments directory"),
        (PROOF.parent, "iter240 experiment directory"),
        (PROOF, "iter240 proof directory"),
    ):
        safe_directory(path, label=label)
    raw_parent = RAW_ROOT.parent
    if os.path.lexists(raw_parent):
        safe_directory(raw_parent, label="raw evidence parent")
    if shutil.disk_usage(PROOF).free < MINIMUM_FREE_BYTES:
        raise CaptureError("insufficient free space for bounded staging and publication")

    capture_path = ROOT / "scripts/capture_iter239_remote_acceptance.py"
    validator_path = ROOT / "scripts/validate_iter239_remote_acceptance.py"
    regular_0644(capture_path, label="capture instrument")
    regular_0644(validator_path, label="offline validator")
    if not all(
        HEX40.fullmatch(value)
        for value in (
            COMPLETED_EVIDENCE,
            SEALED_TIP,
            PREDECESSOR_MASTER,
            MERGE_COMMIT,
            AUTHORIZATION_COMMIT,
            ACTIVATION_COMMIT,
        )
    ):
        raise CaptureError("a frozen Git identity is malformed")

    validator = _load_offline_validator()
    failures = validator.repository_failures(
        ROOT,
        {
            "local_git": local_git_projection(),
            "retained_inputs": retained_input_projection(),
        },
    )
    if failures:
        raise CaptureError(
            "local preflight rejected before one-shot arming: " + "; ".join(failures)
        )
    return validator


def build_attempt_marker(*, started_at: str) -> dict[str, Any]:
    instruments = []
    for relative in (
        "scripts/capture_iter239_remote_acceptance.py",
        "scripts/validate_iter239_remote_acceptance.py",
        "scripts/validate_iter239_repository_governance.py",
        "scripts/validate_seal_registry.py",
    ):
        path = ROOT / relative
        regular_0644(path, label=f"capture instrument {relative}")
        raw = path.read_bytes()
        instruments.append(
            {
                "path": relative,
                "byte_count": len(raw),
                "sha256": sha256(raw),
            }
        )
    plan = request_plan()
    return {
        "schema_version": "telos.iter239.remote_acceptance.attempt.v1",
        "repository": REPOSITORY,
        "api_version": API_VERSION,
        "armed_at": started_at,
        "state": "armed_before_first_request",
        "request_plan": plan,
        "request_plan_sha256": sha256(canonical_json(plan)),
        "planned_request_counts": {
            "GET": len(ENDPOINTS),
            "POST": 0,
            "PUT": 0,
            "PATCH": 0,
            "DELETE": 0,
        },
        "instruments": instruments,
    }


def loaded_validator_matches_marker(validator: Any, marker: dict[str, Any]) -> None:
    matches = [
        row
        for row in marker.get("instruments", [])
        if isinstance(row, dict)
        and row.get("path") == "scripts/validate_iter239_remote_acceptance.py"
    ]
    if (
        len(matches) != 1
        or matches[0].get("sha256")
        != getattr(validator, "__exact_source_sha256__", None)
        or matches[0].get("byte_count")
        != getattr(validator, "__exact_source_byte_count__", None)
    ):
        raise CaptureError(
            "loaded offline validator does not match the bytes armed for capture"
        )


def attempt_binding(marker_bytes: bytes) -> dict[str, Any]:
    return {
        "raw_body_path": (
            "experiments/iter240_ground_truth_admission_design/"
            "proof/raw/iter239_remote_acceptance/capture_attempt.json"
        ),
        "raw_body_byte_count": len(marker_bytes),
        "raw_body_sha256": sha256(marker_bytes),
    }


def arm_attempt(marker_bytes: bytes) -> None:
    raw_parent = RAW_ROOT.parent
    if not os.path.lexists(raw_parent):
        raw_parent.mkdir(mode=0o755)
        fsync_directory(PROOF)
    safe_directory(raw_parent, label="raw evidence parent")
    RAW_ROOT.mkdir(mode=0o755)
    fsync_directory(raw_parent)
    marker_path = RAW_ROOT / ATTEMPT_FILENAME
    with marker_path.open("xb") as handle:
        os.fchmod(handle.fileno(), 0o644)
        handle.write(marker_bytes)
        handle.flush()
        os.fsync(handle.fileno())
    fsync_directory(RAW_ROOT)


def utc_second() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def http_date_to_utc(value: str) -> str:
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError) as exc:
        raise CaptureError(f"invalid GitHub Date header: {value!r}") from exc
    if parsed.tzinfo is None:
        raise CaptureError("GitHub Date header has no timezone")
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def token_from_environment_or_gh() -> str:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        return token.strip()
    try:
        completed = subprocess.run(
            ["gh", "auth", "token"],
            cwd=ROOT,
            capture_output=True,
            check=False,
            timeout=10,
            text=True,
            env={
                "HOME": os.environ.get("HOME", ""),
                "PATH": os.environ.get("PATH", ""),
            },
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise CaptureError("cannot read the local GitHub credential") from exc
    token = completed.stdout.strip()
    if completed.returncode != 0 or not token:
        raise CaptureError("no GitHub credential is available")
    return token


def selected_headers(headers: list[tuple[str, str]]) -> dict[str, str | None]:
    grouped: dict[str, list[str]] = {}
    for name, value in headers:
        grouped.setdefault(name.lower(), []).append(value.strip())
    required = ("date", "x-github-api-version-selected", "x-github-request-id")
    for name in required:
        if len(grouped.get(name, [])) != 1 or not grouped[name][0]:
            raise CaptureError(f"required GitHub response header is ambiguous: {name}")
    for name in ("etag", "link"):
        if len(grouped.get(name, [])) > 1:
            raise CaptureError(f"GitHub response header is duplicated: {name}")
    content_types = grouped.get("content-type", [])
    if len(content_types) != 1 or "application/json" not in content_types[0].lower():
        raise CaptureError("GitHub response Content-Type is not unambiguous JSON")
    return {
        "response_date": http_date_to_utc(grouped["date"][0]),
        "api_version_selected": grouped["x-github-api-version-selected"][0],
        "github_request_id": grouped["x-github-request-id"][0],
        "etag": grouped.get("etag", [None])[0],
        "link": grouped.get("link", [None])[0],
    }


def exact_keys(value: object, keys: set[str], *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise CaptureError(f"{label} fields differ")
    return value


def run_projection(value: object, *, expected_id: int) -> dict[str, Any]:
    if (
        not isinstance(value, dict)
        or type(value.get("id")) is not int
        or value.get("id") != expected_id
    ):
        raise CaptureError(f"workflow run identity differs: {expected_id}")
    return {
        "id": value.get("id"),
        "workflow_id": value.get("workflow_id"),
        "attempt": value.get("run_attempt"),
        "event": value.get("event"),
        "status": value.get("status"),
        "conclusion": value.get("conclusion"),
        "head_sha": value.get("head_sha"),
        "head_branch": value.get("head_branch"),
        "path": value.get("path"),
        "check_suite_id": value.get("check_suite_id"),
        "created_at": value.get("created_at"),
        "updated_at": value.get("updated_at"),
    }


def expected_check_projection(
    check_document: object,
    expected_rows: tuple[dict[str, Any], ...],
) -> list[dict[str, Any]]:
    if not isinstance(check_document, dict):
        raise CaptureError("check-runs response is not an object")
    rows = check_document.get("check_runs")
    total = check_document.get("total_count")
    if (
        type(total) is not int
        or not isinstance(rows, list)
        or type(total) is bool
        or total != len(rows)
    ):
        raise CaptureError("check-runs total_count is incomplete")
    result: list[dict[str, Any]] = []
    for expected in expected_rows:
        matches = [
            row
            for row in rows
            if isinstance(row, dict)
            and row.get("name") == expected["name"]
            and row.get("head_sha") == expected["head_sha"]
            and isinstance(row.get("app"), dict)
            and row["app"].get("id") == INTEGRATION_ID
        ]
        if len(matches) != 1:
            raise CaptureError(
                "required check is absent or ambiguous: "
                f"{expected['head_sha']} {expected['name']}"
            )
        row = matches[0]
        details_url = row.get("details_url")
        expected_url = (
            f"https://github.com/{REPOSITORY}/actions/runs/"
            f"{expected['run_id']}/job/{expected['check_run_id']}"
        )
        if row.get("id") != expected["check_run_id"] or details_url != expected_url:
            raise CaptureError(f"required check run/job binding differs: {expected['name']}")
        if (
            type(row.get("id")) is not int
            or type(row["app"].get("id")) is not int
        ):
            raise CaptureError(f"required check numeric identity is ambiguous: {expected['name']}")
        result.append(
            {
                "name": expected["name"],
                "event": expected["event"],
                "run_id": expected["run_id"],
                "check_run_id": row.get("id"),
                "check_suite_id": (
                    row.get("check_suite", {}).get("id")
                    if isinstance(row.get("check_suite"), dict)
                    else None
                ),
                "app_id": row["app"].get("id"),
                "app_slug": row["app"].get("slug"),
                "status": row.get("status"),
                "conclusion": row.get("conclusion"),
                "head_sha": row.get("head_sha"),
                "details_url": details_url,
                "started_at": row.get("started_at"),
                "completed_at": row.get("completed_at"),
            }
        )
    return result


def request_policy_projection(ruleset: object) -> dict[str, Any]:
    if not isinstance(ruleset, dict):
        raise CaptureError("ruleset response is not an object")
    rules = ruleset.get("rules")
    if not isinstance(rules, list):
        raise CaptureError("ruleset response has no rules array")
    normalized_rules: list[dict[str, Any]] = []
    for row in rules:
        if not isinstance(row, dict):
            raise CaptureError("ruleset rule is not an object")
        normalized = json.loads(json.dumps(row))
        parameters = normalized.get("parameters")
        if (
            normalized.get("type") == "pull_request"
            and isinstance(parameters, dict)
            and parameters.get("required_reviewers") == []
        ):
            del parameters["required_reviewers"]
        normalized_rules.append(normalized)
    return {
        "name": ruleset.get("name"),
        "target": ruleset.get("target"),
        "enforcement": ruleset.get("enforcement"),
        "bypass_actors": ruleset.get("bypass_actors"),
        "conditions": ruleset.get("conditions"),
        "rules": normalized_rules,
    }


def effective_rules_projection(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise CaptureError("effective rules response is not an array")
    projection: list[dict[str, Any]] = []
    for row in value:
        if not isinstance(row, dict):
            raise CaptureError("effective rule is not an object")
        item = {
            "ruleset_id": row.get("ruleset_id"),
            "ruleset_source": row.get("ruleset_source"),
            "ruleset_source_type": row.get("ruleset_source_type"),
            "type": row.get("type"),
        }
        if "parameters" in row:
            item["parameters"] = row.get("parameters")
        projection.append(item)
    return projection


def build_receipt(
    documents: dict[str, Any],
    inventory: list[dict[str, Any]],
    *,
    started_at: str,
    completed_at: str,
    marker_bytes: bytes,
) -> dict[str, Any]:
    policy = strict_json(
        (ROOT / "experiments/iter239_repository_governance/policy.json").read_bytes(),
        label="retained policy",
    )
    if not isinstance(policy, dict):
        raise CaptureError("retained policy is not an object")
    request_body = policy.get("request_body")
    request_body_sha = policy.get("request_body_sha256")
    projected_request = request_policy_projection(documents["ruleset"])
    if canonical_json(projected_request) != canonical_json(request_body):
        raise CaptureError("live ruleset request-policy projection differs")
    if sha256(canonical_json(projected_request)) != request_body_sha:
        raise CaptureError("live ruleset request-policy digest differs")

    sealed_checks = expected_check_projection(
        documents["sealed_tip_check_runs"],
        tuple(row for row in EXPECTED_CHECKS if row["head_sha"] == SEALED_TIP),
    )
    merged_checks = expected_check_projection(
        documents["merged_master_check_runs"],
        tuple(row for row in EXPECTED_CHECKS if row["head_sha"] == MERGE_COMMIT),
    )
    effective = effective_rules_projection(documents["effective_rules"])

    pull_request = documents["pull_request_87"]
    if not isinstance(pull_request, dict):
        raise CaptureError("pull request response is not an object")
    head = pull_request.get("head")
    base = pull_request.get("base")
    if not isinstance(head, dict) or not isinstance(base, dict):
        raise CaptureError("pull request head/base is malformed")

    branch = documents["master_branch"]
    ruleset = documents["ruleset"]
    if not isinstance(branch, dict) or not isinstance(ruleset, dict):
        raise CaptureError("branch or ruleset response is malformed")

    return {
        "schema_version": "telos.iter239.remote_acceptance.v1",
        "repository": REPOSITORY,
        "api_version": API_VERSION,
        "capture": {
            "started_at": started_at,
            "completed_at": completed_at,
            "attempt_marker": attempt_binding(marker_bytes),
            "response_inventory": inventory,
        },
        "request_counts": {
            "GET": len(ENDPOINTS),
            "POST": 0,
            "PUT": 0,
            "PATCH": 0,
            "DELETE": 0,
        },
        "local_git": local_git_projection(),
        "retained_inputs": retained_input_projection(),
        "projections": {
            "pull_request": {
                "number": pull_request.get("number"),
                "state": pull_request.get("state"),
                "merged": pull_request.get("merged"),
                "merged_at": pull_request.get("merged_at"),
                "draft": pull_request.get("draft"),
                "head_sha": head.get("sha"),
                "head_ref": head.get("ref"),
                "head_repository": (
                    head.get("repo", {}).get("full_name")
                    if isinstance(head.get("repo"), dict)
                    else None
                ),
                "base_sha": base.get("sha"),
                "base_ref": base.get("ref"),
                "base_repository": (
                    base.get("repo", {}).get("full_name")
                    if isinstance(base.get("repo"), dict)
                    else None
                ),
            },
            "sealed_tip_ci": {
                "head_sha": SEALED_TIP,
                "runs": [
                    run_projection(
                        documents["sealed_push_run"],
                        expected_id=29701167247,
                    ),
                    run_projection(
                        documents["sealed_pr_run"],
                        expected_id=29701168051,
                    ),
                ],
                "required_checks": sealed_checks,
            },
            "merged_master_ci": {
                "head_sha": MERGE_COMMIT,
                "run": run_projection(
                    documents["merged_master_run"],
                    expected_id=29701305166,
                ),
                "required_checks": merged_checks,
            },
            "governance": {
                "branch": branch.get("name"),
                "branch_sha": (
                    branch.get("commit", {}).get("sha")
                    if isinstance(branch.get("commit"), dict)
                    else None
                ),
                "protected": branch.get("protected"),
                "ruleset_id": ruleset.get("id"),
                "ruleset_name": ruleset.get("name"),
                "enforcement": ruleset.get("enforcement"),
                "current_user_can_bypass": ruleset.get("current_user_can_bypass"),
                "request_policy_sha256": sha256(canonical_json(projected_request)),
                "effective_rules_projection_sha256": sha256(canonical_json(effective)),
            },
        },
        "conclusion": {
            "engineering_closure": "supported",
            "technical_control": "supported",
            "independent_review": "blocked",
            "overall_governance": "blocked",
            "scientific_authority": "none",
        },
        "limitations": [
            (
                "This is a time-bounded observation of mutable GitHub state; "
                "it does not prove that the state cannot later drift."
            ),
            (
                "Digests and GitHub request identifiers bind retained bytes but "
                "do not establish authorship, external chronology, semantic "
                "truth, or scientific correctness."
            ),
            (
                "The zero write counts cover only this fixed capture instrument, "
                "not every action by every actor."
            ),
            (
                "The ruleset requires zero approvals; its technical control is "
                "not independent review assurance."
            ),
            (
                "This engineering closure authorizes no scientific claim, "
                "provider or model call, container, GPU, spending, release, or "
                "publication."
            ),
        ],
    }


def validate_staged_receipt(
    validator: Any,
    *,
    marker_bytes: bytes,
    bodies: dict[str, bytes],
    receipt_bytes: bytes,
) -> None:
    with tempfile.TemporaryDirectory(
        prefix="telos-iter239-remote-acceptance-"
    ) as temporary:
        staging = Path(temporary)
        raw_root = staging / "raw"
        raw_root.mkdir(mode=0o755)
        staged_marker = raw_root / ATTEMPT_FILENAME
        staged_marker.write_bytes(marker_bytes)
        staged_marker.chmod(0o644)
        for _, _, filename in ENDPOINTS:
            path = raw_root / filename
            path.write_bytes(bodies[filename])
            path.chmod(0o644)
        receipt_path = staging / "iter239_remote_acceptance.json"
        receipt_path.write_bytes(receipt_bytes)
        receipt_path.chmod(0o644)
        failures = validator.validate(
            root=ROOT,
            receipt_path=receipt_path,
            raw_root=raw_root,
            check_repository=True,
        )
    if failures:
        raise CaptureError(
            "independent offline acceptance rejected the one-shot bytes: "
            + "; ".join(failures)
        )


def capture() -> None:
    validator = preflight_capture()
    token = token_from_environment_or_gh()
    started_at = utc_second()
    marker = build_attempt_marker(started_at=started_at)
    loaded_validator_matches_marker(validator, marker)
    marker_bytes = canonical_json(marker)
    arm_attempt(marker_bytes)

    context = ssl.create_default_context()
    connection = http.client.HTTPSConnection(
        API_HOST,
        timeout=30,
        context=context,
    )
    documents: dict[str, Any] = {}
    bodies: dict[str, bytes] = {}
    inventory: list[dict[str, Any]] = []
    try:
        for name, request_path, filename in ENDPOINTS:
            connection.request(
                "GET",
                request_path,
                headers={
                    "Accept": "application/vnd.github+json",
                    "Accept-Encoding": "identity",
                    "Authorization": f"Bearer {token}",
                    "User-Agent": "telos-iter239-remote-acceptance/1",
                    "X-GitHub-Api-Version": API_VERSION,
                },
            )
            response = connection.getresponse()
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise CaptureError(f"GitHub response exceeds size cap: {name}")
            if response.status != 200:
                raise CaptureError(
                    f"GitHub GET failed without retry: {name}: HTTP {response.status}"
                )
            safe = selected_headers(response.getheaders())
            if safe["api_version_selected"] != API_VERSION:
                raise CaptureError(f"GitHub selected a different API version: {name}")
            if safe["link"] is not None:
                raise CaptureError(f"unexpected pagination Link; capture is incomplete: {name}")
            document = strict_json(raw, label=name)
            documents[name] = document
            bodies[filename] = raw
            inventory.append(
                {
                    "name": name,
                    "method": "GET",
                    "request_path": request_path,
                    "http_status": response.status,
                    **safe,
                    "raw_body_path": (
                        "experiments/iter240_ground_truth_admission_design/"
                        f"proof/raw/iter239_remote_acceptance/{filename}"
                    ),
                    "raw_body_byte_count": len(raw),
                    "raw_body_sha256": sha256(raw),
                }
            )
    finally:
        connection.close()
        token = ""

    completed_at = utc_second()
    receipt = build_receipt(
        documents,
        inventory,
        started_at=started_at,
        completed_at=completed_at,
        marker_bytes=marker_bytes,
    )
    receipt_bytes = canonical_json(receipt)
    validate_staged_receipt(
        validator,
        marker_bytes=marker_bytes,
        bodies=bodies,
        receipt_bytes=receipt_bytes,
    )

    published: list[Path] = []
    try:
        for _, _, filename in ENDPOINTS:
            destination = RAW_ROOT / filename
            with destination.open("xb") as handle:
                os.fchmod(handle.fileno(), 0o644)
                handle.write(bodies[filename])
                handle.flush()
                os.fsync(handle.fileno())
            published.append(destination)
        with RECEIPT.open("xb") as handle:
            os.fchmod(handle.fileno(), 0o644)
            handle.write(receipt_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        published.append(RECEIPT)
        fsync_directory(RAW_ROOT)
        fsync_directory(RECEIPT.parent)
        final_failures = validator.validate(
            root=ROOT,
            receipt_path=RECEIPT,
            raw_root=RAW_ROOT,
            check_repository=True,
        )
        if final_failures:
            raise CaptureError(
                "published bytes failed offline revalidation: "
                + "; ".join(final_failures)
            )
    except Exception:
        for path in reversed(published):
            path.unlink(missing_ok=True)
        fsync_directory(RAW_ROOT)
        fsync_directory(RECEIPT.parent)
        raise

    print(
        "iter239 remote acceptance capture retained: "
        f"{len(ENDPOINTS)} GET, 0 writes"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--capture",
        action="store_true",
        help="perform the one fixed nine-GET capture and publish new evidence",
    )
    args = parser.parse_args()
    if not args.capture:
        parser.error("live capture requires the explicit --capture flag")
    try:
        capture()
    except CaptureError as exc:
        print(f"iter239 remote acceptance capture failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
