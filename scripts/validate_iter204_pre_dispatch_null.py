#!/usr/bin/env python3
"""Validate the bounded iter204 pre-dispatch workflow-parse null."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from telos.ledger import (  # noqa: E402
    latest_next_action,
    load_learning_record,
)


EXP = ROOT / "experiments/iter204_iter203_infrastructure_recovery"
NULL = EXP / "proof/pre_dispatch_infrastructure_null.json"
RESULT = EXP / "RESULT.md"
PENDING_LEARNING = EXP / "proof/learning_record.json"
TERMINAL_LEARNING = EXP / "proof/learning_record.pre_dispatch_null.json"
PUBLIC = EXP / "proof/raw/public_dispatch_metadata"
MANIFEST = PUBLIC / "manifest.json"
WORKFLOW = ROOT / ".github/workflows/iter204-execute.yml"
HYPOTHESIS = EXP / "HYPOTHESIS.md"
RUNTIME_MANIFEST = EXP / "proof/raw/runtime_manifest.json"

APPROVED_SHA = "c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446"
BRANCH_SHA = "8342315dd2fa7ec865bd7c654ec4ec098675dfab"
PRIMARY_CI_RUN_ID = 29465925393
PUSH_RUN_IDS = (29465584664, 29465924803)
WORKFLOW_ID = 314113289
WORKFLOW_SHA256 = "84f7f8b228624ff7244991e317e7f8146a6aacd93f803c1df983b6cceae4deb4"
HYPOTHESIS_SHA256 = "7f6b9e0ba0ba0077115e64e38239a6eeafb2b18797fdd160a3eb9c0297396dfd"
RUNTIME_MANIFEST_SHA256 = (
    "bf2062825e604d9439b0d29375d7e5219a1064ae4a33701efb74a62f81a59a45"
)
PENDING_LEARNING_SHA256 = (
    "0684f440f49b8c9660f4d95d1ebb03c0a001a3f8987372feba86b361ed32cb61"
)
PUBLIC_MANIFEST_SHA256 = (
    "8f20922002f3029e96d60078ace644e0cf56f758c692c3f35a07d5fe7f19081b"
)
ERROR_MESSAGE = (
    "Invalid Argument - failed to parse workflow: (Line: 318, Col: 36): "
    "Unrecognized named-value: 'runner'. Located at position 1 within expression: "
    "runner.temp"
)
TERMINAL_NEXT_ACTION = (
    "Do not dispatch or rerun iter204, and keep its frozen bytes unchanged. Complete "
    "and adversarially validate the separately versioned iter205 recovery, publish it "
    "through review, and require green primary CI. Only then may exact active-workflow "
    "and empty-history preflight authorize at most one iter205 dispatch request. Any "
    "confirmed iter205 rejection or execution failure closes iter205 and advances to "
    "iter206 without retry."
)
TERMINAL_INSIGHT = (
    "Iter204 closed before dispatch-run creation as an infrastructure null. Its two "
    "public workflow records are push parse failures with zero jobs and artifacts; the "
    "public workflow_dispatch history is empty; and no provider, container, patch, "
    "certification, scenario, adjudication, or judge process started. The immutable "
    "pre-result learning record remains retained for provenance but no longer supplies "
    "the current completed-record action."
)
PUBLIC_FILES = {
    "dispatch_runs.json": (
        46,
        "763f11efb3fd0695809422708bf5765dfad5d8438bfb9a7bad31f23ff74d3285",
    ),
    "primary_ci_projection.json": (
        1393,
        "43ace0a199f8b8fb4b445867d9a5385341957b22387bf3b02cb7fbb2ece2c548",
    ),
    "push_validation_runs.json": (
        1974,
        "ddca5408499db75be61ee81f17e7c27c53095922a4d18c911a03b93d457bf782",
    ),
    "workflow.json": (
        600,
        "c5daeb87763194bec571aa9073b78e8daf7c55024bdde0347847d69a0b6b8ce1",
    ),
}


class PreDispatchNullError(ValueError):
    """The normalized null or one of its public metadata snapshots differs."""


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_strict(path: Path) -> tuple[dict[str, Any], bytes]:
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
        value = json.loads(
            raw,
            object_pairs_hook=unique,
            parse_constant=lambda item: (_ for _ in ()).throw(ValueError(item)),
        )
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise PreDispatchNullError(f"cannot parse strict JSON {path}: {exc}") from exc
    if duplicates or not isinstance(value, dict):
        raise PreDispatchNullError(f"ambiguous JSON object: {path}")
    rendered = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    if raw != rendered:
        raise PreDispatchNullError(f"noncanonical JSON: {path}")
    return value, raw


def validate_frozen_source() -> None:
    frozen = {
        WORKFLOW: WORKFLOW_SHA256,
        HYPOTHESIS: HYPOTHESIS_SHA256,
        RUNTIME_MANIFEST: RUNTIME_MANIFEST_SHA256,
        PENDING_LEARNING: PENDING_LEARNING_SHA256,
    }
    for path, expected in frozen.items():
        if path.is_symlink() or not path.is_file() or sha256(path.read_bytes()) != expected:
            raise PreDispatchNullError(
                f"frozen iter204 source differs: {path.relative_to(ROOT)}"
            )
    lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
    if len(lines) < 318:
        raise PreDispatchNullError("iter204 workflow no longer reaches reported parse line")
    reported = lines[317]
    expression = "${{ runner.temp }}"
    if reported != (
        "      TELOS_ITER204_SMOKE_RECEIPT: "
        "${{ runner.temp }}/iter204-smoke/smoke.receipt.json"
    ) or reported.index(expression) + 1 != 36:
        raise PreDispatchNullError("iter204 line-318/column-36 parse anchor differs")


def validate_terminal_learning_record() -> None:
    document, _ = load_strict(TERMINAL_LEARNING)
    expected = {
        "evidence_paths": [
            "experiments/iter204_iter203_infrastructure_recovery/RESULT.md",
            (
                "experiments/iter204_iter203_infrastructure_recovery/proof/"
                "pre_dispatch_infrastructure_null.json"
            ),
            (
                "experiments/iter204_iter203_infrastructure_recovery/proof/raw/"
                "public_dispatch_metadata/manifest.json"
            ),
            "experiments/iter205_iter204_workflow_context_recovery/HYPOTHESIS.md",
        ],
        "experiment_id": (
            "iter204_iter203_infrastructure_recovery_pre_dispatch_null"
        ),
        "insight": TERMINAL_INSIGHT,
        "next_action": TERMINAL_NEXT_ACTION,
        "result_path": (
            "experiments/iter204_iter203_infrastructure_recovery/RESULT.md"
        ),
        "schema_version": "telos.learning_record.v1",
        "status": "null",
        "supersedes": (
            "experiments/iter204_iter203_infrastructure_recovery/proof/"
            "learning_record.json"
        ),
        "timing": (
            "post_iter204_pre_dispatch_infrastructure_null_and_before_any_"
            "iter205_dispatch"
        ),
    }
    if document != expected:
        raise PreDispatchNullError("iter204 terminal learning record differs")
    for relative in expected["evidence_paths"]:
        path = ROOT / relative
        if path.is_symlink() or not path.is_file():
            raise PreDispatchNullError(
                f"iter204 terminal learning evidence is absent: {relative}"
            )
    records = [
        load_learning_record(PENDING_LEARNING, root=ROOT),
        load_learning_record(TERMINAL_LEARNING, root=ROOT),
    ]
    if latest_next_action(records) != TERMINAL_NEXT_ACTION:
        raise PreDispatchNullError(
            "bounded iter204 learning records do not advance safely beyond iter204"
        )


def validate_public_metadata() -> dict[str, Any]:
    if MANIFEST.is_symlink() or sha256(MANIFEST.read_bytes()) != PUBLIC_MANIFEST_SHA256:
        raise PreDispatchNullError("iter204 public dispatch metadata manifest differs")
    manifest, _ = load_strict(MANIFEST)
    if (
        manifest.get("schema_version")
        != "telos.iter204.public_pre_dispatch_metadata.v1"
        or manifest.get("workflow_id") != WORKFLOW_ID
        or manifest.get("workflow_state") != "active"
        or manifest.get("workflow_total_run_count") != 2
        or manifest.get("workflow_push_run_count") != 2
        or manifest.get("workflow_workflow_dispatch_run_count") != 0
    ):
        raise PreDispatchNullError("iter204 public metadata manifest identity differs")
    rows = manifest.get("files")
    if not isinstance(rows, list) or len(rows) != len(PUBLIC_FILES):
        raise PreDispatchNullError("iter204 public metadata file inventory differs")
    by_name = {
        row.get("path"): row for row in rows if isinstance(row, dict)
    }
    if set(by_name) != set(PUBLIC_FILES):
        raise PreDispatchNullError("iter204 public metadata manifest paths differ")
    for name, (expected_bytes, expected_hash) in PUBLIC_FILES.items():
        path = PUBLIC / name
        row = by_name[name]
        if path.is_symlink() or not path.is_file():
            raise PreDispatchNullError(f"iter204 public metadata file is absent: {name}")
        payload = path.read_bytes()
        if (
            len(payload) != expected_bytes
            or sha256(payload) != expected_hash
            or row.get("bytes") != expected_bytes
            or row.get("sha256") != expected_hash
        ):
            raise PreDispatchNullError(f"iter204 public metadata hash/size differs: {name}")
        load_strict(path)
    if {path.name for path in PUBLIC.iterdir()} != set(PUBLIC_FILES) | {"manifest.json"}:
        raise PreDispatchNullError("iter204 public metadata directory has extra or missing files")

    workflow, _ = load_strict(PUBLIC / "workflow.json")
    if (
        workflow.get("id") != WORKFLOW_ID
        or workflow.get("state") != "active"
        or workflow.get("name") != ".github/workflows/iter204-execute.yml"
        or workflow.get("path") != ".github/workflows/iter204-execute.yml"
    ):
        raise PreDispatchNullError("iter204 public workflow metadata differs")
    dispatch, _ = load_strict(PUBLIC / "dispatch_runs.json")
    if dispatch != {"total_count": 0, "workflow_runs": []}:
        raise PreDispatchNullError("iter204 workflow_dispatch run list is not exact zero")
    return manifest


def validate_push_records() -> None:
    document, _ = load_strict(PUBLIC / "push_validation_runs.json")
    rows = document.get("runs")
    if document.get("total_count") != 2 or not isinstance(rows, list) or len(rows) != 2:
        raise PreDispatchNullError("iter204 push validation run count differs")
    by_id = {row.get("id"): row for row in rows if isinstance(row, dict)}
    if set(by_id) != set(PUSH_RUN_IDS):
        raise PreDispatchNullError("iter204 push validation run identities differ")
    expected_sources = {
        29465584664: ("agent/iter204-infrastructure-recovery", BRANCH_SHA, 1),
        29465924803: ("master", APPROVED_SHA, 2),
    }
    unavailable = {
        "documentation_url": (
            "https://docs.github.com/rest/actions/workflow-runs#download-workflow-run-logs"
        ),
        "http_status": 404,
        "message": "Not Found",
        "status": "404",
    }
    for run_id, (branch, source, number) in expected_sources.items():
        row = by_id[run_id]
        if (
            row.get("event") != "push"
            or row.get("run_attempt") != 1
            or row.get("run_number") != number
            or row.get("status") != "completed"
            or row.get("conclusion") != "failure"
            or row.get("head_branch") != branch
            or row.get("head_sha") != source
            or row.get("name") != ".github/workflows/iter204-execute.yml"
            or row.get("path") != ".github/workflows/iter204-execute.yml"
            or row.get("jobs_response") != {"jobs": [], "total_count": 0}
            or row.get("artifacts_response") != {"artifacts": [], "total_count": 0}
            or row.get("logs_download_response") != unavailable
        ):
            raise PreDispatchNullError(f"iter204 push validation record differs: {run_id}")


def validate_primary_ci() -> None:
    document, _ = load_strict(PUBLIC / "primary_ci_projection.json")
    run = document.get("run")
    jobs = document.get("jobs")
    if (
        document.get("total_count") != 2
        or not isinstance(run, dict)
        or run.get("id") != PRIMARY_CI_RUN_ID
        or run.get("run_attempt") != 1
        or run.get("event") != "push"
        or run.get("head_branch") != "master"
        or run.get("head_sha") != APPROVED_SHA
        or run.get("status") != "completed"
        or run.get("conclusion") != "success"
        or not isinstance(jobs, list)
        or {(row.get("name"), row.get("conclusion")) for row in jobs}
        != {("verify py3.11", "success"), ("verify py3.12", "success")}
        or {row.get("run_id") for row in jobs} != {PRIMARY_CI_RUN_ID}
        or {row.get("run_attempt") for row in jobs} != {1}
        or {row.get("head_sha") for row in jobs} != {APPROVED_SHA}
    ):
        raise PreDispatchNullError("iter204 approved primary CI evidence differs")


def validate_normalized_null() -> None:
    document, _ = load_strict(NULL)
    if (
        document.get("schema_version")
        != "telos.iter204.pre_dispatch_infrastructure_null.v1"
        or document.get("experiment_id") != "iter204_iter203_infrastructure_recovery"
        or document.get("status") != "pre_dispatch_infrastructure_null"
        or document.get("timing")
        != "post_merge_green_primary_ci_and_pre_workflow_dispatch_run"
        or document.get("public_dispatch_metadata_manifest_sha256")
        != PUBLIC_MANIFEST_SHA256
        or document.get("public_dispatch_metadata_manifest_path")
        != str(MANIFEST.relative_to(ROOT))
    ):
        raise PreDispatchNullError("iter204 normalized null identity differs")
    rejection = document.get("dispatch_api_rejection")
    if rejection != {
        "error_message": ERROR_MESSAGE,
        "http_status": 422,
        "locally_observed": True,
        "public_workflow_dispatch_job_log_exists": False,
        "public_workflow_dispatch_run_log_exists": False,
        "raw_response_committed": False,
        "request_count_exact": None,
        "request_count_lower_bound": 1,
        "workflow_dispatch_run_count_after_rejection": 0,
        "workflow_dispatch_run_created": False,
        "workflow_dispatch_run_id": None,
    }:
        raise PreDispatchNullError("iter204 bounded local dispatch-rejection claim differs")
    scientific = document.get("scientific_evidence")
    if scientific != {
        "certification_executions": 0,
        "container_create_or_run_invocations": 0,
        "k": None,
        "n": None,
        "patch_applications": 0,
        "scenario_executions": 0,
        "scientific_artifacts": 0,
        "u": None,
    }:
        raise PreDispatchNullError("iter204 scientific-null boundary differs")
    if document.get("provider_accounting") != {
        "judge_calls": 0,
        "scenario_calls": 0,
        "solver_calls": 0,
    }:
        raise PreDispatchNullError("iter204 zero-provider boundary differs")
    if document.get("next_gate") != {
        "path": "experiments/iter205_iter204_workflow_context_recovery/HYPOTHESIS.md",
        "status": "pending_separately_versioned_workflow_context_recovery",
    }:
        raise PreDispatchNullError("iter204 separately versioned successor differs")
    push = document.get("push_validation_records")
    if not isinstance(push, dict) or (
        push.get("run_count") != 2
        or push.get("run_ids") != list(PUSH_RUN_IDS)
        or push.get("run_attempts") != [1, 1]
        or push.get("event") != "push"
        or push.get("jobs_created") != 0
        or push.get("artifacts_uploaded") != 0
        or push.get("log_downloads_available") != 0
        or push.get("scientific_execution") != 0
        or push.get("workflow_name_fallback")
        != ".github/workflows/iter204-execute.yml"
    ):
        raise PreDispatchNullError("iter204 normalized push-record boundary differs")
    source = document.get("workflow_source")
    if not isinstance(source, dict) or (
        source.get("workflow_id") != WORKFLOW_ID
        or source.get("workflow_state") != "active"
        or source.get("path") != ".github/workflows/iter204-execute.yml"
        or source.get("sha256") != WORKFLOW_SHA256
        or source.get("frozen_hypothesis_sha256") != HYPOTHESIS_SHA256
        or source.get("frozen_runtime_manifest_sha256") != RUNTIME_MANIFEST_SHA256
        or source.get("parse_line") != 318
        or source.get("parse_column") != 36
        or source.get("parse_expression") != "runner.temp"
        or source.get("parse_rejection_cause")
        != "runner.temp is unavailable in a job-level env expression"
        or source.get("failure_class")
        != "workflow_parse_error_before_dispatch_run_creation"
    ):
        raise PreDispatchNullError("iter204 normalized workflow parse boundary differs")
    approved = document.get("approved_source")
    expected_jobs = {
        (87518936244, "verify py3.12", "success"),
        (87518936266, "verify py3.11", "success"),
    }
    if not isinstance(approved, dict) or (
        approved.get("head_sha") != APPROVED_SHA
        or approved.get("primary_ref") != "refs/heads/master"
        or approved.get("primary_ci", {}).get("run_id") != PRIMARY_CI_RUN_ID
        or approved.get("primary_ci", {}).get("conclusion") != "success"
        or approved.get("primary_ci", {}).get("run_attempt") != 1
        or {
            (row.get("id"), row.get("name"), row.get("conclusion"))
            for row in approved.get("primary_ci", {}).get("jobs", [])
            if isinstance(row, dict)
        }
        != expected_jobs
    ):
        raise PreDispatchNullError("iter204 normalized approved-source boundary differs")


def validate_result_surface() -> None:
    text = RESULT.read_text(encoding="utf-8")
    required = (
        "PRE-DISPATCH INFRASTRUCTURE NULL",
        APPROVED_SHA,
        str(PRIMARY_CI_RUN_ID),
        str(PUSH_RUN_IDS[0]),
        str(PUSH_RUN_IDS[1]),
        "Both records have event `push`",
        "zero iter204 `workflow_dispatch` runs",
        "at least one locally observed authorized iter204 dispatch API request",
        ERROR_MESSAGE,
        "no `N`, `k`, or `u`; those quantities are absent, not zero",
        "separately versioned iter205 workflow-context protocol",
    )
    missing = [fragment for fragment in required if fragment not in text]
    if missing:
        raise PreDispatchNullError(
            "iter204 result omits required bounded facts: " + ", ".join(missing)
        )
    forbidden = (
        "zero workflow runs",
        "no workflow run exists",
        "exactly one authorized iter204 dispatch API request",
    )
    hits = [fragment for fragment in forbidden if fragment in text]
    if hits:
        raise PreDispatchNullError(
            "iter204 result overstates the observable boundary: " + ", ".join(hits)
        )


def validate() -> dict[str, int]:
    validate_frozen_source()
    validate_terminal_learning_record()
    validate_public_metadata()
    validate_push_records()
    validate_primary_ci()
    validate_normalized_null()
    validate_result_surface()
    return {
        "provider_calls": 0,
        "push_validation_runs": 2,
        "scientific_executions": 0,
        "workflow_dispatch_runs": 0,
    }


def main() -> int:
    try:
        summary = validate()
    except (OSError, PreDispatchNullError) as exc:
        print(f"iter204 pre-dispatch-null guard failed: {exc}", file=sys.stderr)
        return 1
    print(
        "iter204 pre-dispatch-null guard: "
        f"{summary['push_validation_runs']} push parse-failure records, "
        f"{summary['workflow_dispatch_runs']} workflow_dispatch runs, "
        f"{summary['scientific_executions']} scientific executions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
