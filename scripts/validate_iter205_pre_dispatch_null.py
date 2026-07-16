#!/usr/bin/env python3
"""Validate the bounded iter205 read-only admission-history null."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from telos.ledger import latest_next_action, load_learning_record  # noqa: E402
from scripts import validate_iter204_pre_dispatch_null as iter204_null  # noqa: E402


EXP = ROOT / "experiments/iter205_iter204_workflow_context_recovery"
NULL = EXP / "proof/pre_dispatch_admission_null.json"
RESULT = EXP / "RESULT.md"
PUBLIC = EXP / "proof/raw/public_admission_metadata"
MANIFEST = PUBLIC / "manifest.json"
WORKFLOW = ROOT / ".github/workflows/iter205-execute.yml"
HYPOTHESIS = EXP / "HYPOTHESIS.md"
RUNTIME_MANIFEST = EXP / "proof/raw/runtime_manifest.json"
PUBLICATION_SAFETY = EXP / "proof/pre_execution_publication_safety.json"
PENDING_LEARNING = EXP / "proof/learning_record.json"
TERMINAL_LEARNING = EXP / "proof/learning_record.pre_dispatch_admission_null.json"

FEATURE_SHA = "a336b4909329d392f6db5f6098792e07a17f28cb"
MERGE_SHA = "4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f"
PRIMARY_CI_RUN_ID = 29468769187
ITER205_WORKFLOW_ID = 314141096
ITER204_WORKFLOW_ID = 314113289
ITER204_RUN_IDS = (29465584664, 29465924803, 29468669956, 29468768706)
WORKFLOW_SHA256 = "0bbc39c8b4abbe6ae7dcbd4f9dc5710f835ff06522d8c137b622a9ad6a5a0ad5"
HYPOTHESIS_SHA256 = "2b00f43f581176eaf4e134c7e3e3b2a9981f0767545a1f1b21397458bb215395"
RUNTIME_MANIFEST_SHA256 = (
    "1d427fd8e778282127ee8d782c6eb6bb8d6d44e781edceb50ad078474968b04a"
)
PUBLICATION_SAFETY_SHA256 = (
    "1ba7adbea2fb6cf12488e8cf9a3438daadd22809d3d9944ae331bc031587d7da"
)
PENDING_LEARNING_SHA256 = (
    "f38c6443bc74a55ee73404d91e791aa048d77b7c545a02f5bf51e79476a690c7"
)
PUBLIC_MANIFEST_SHA256 = (
    "6d2216038c7e1f19337795be806bf77eb39150a9be119828bc2967ed160c72ba"
)
PUBLIC_FILES = {
    "all_runs.json": (
        46,
        "763f11efb3fd0695809422708bf5765dfad5d8438bfb9a7bad31f23ff74d3285",
    ),
    "dispatch_runs.json": (
        46,
        "763f11efb3fd0695809422708bf5765dfad5d8438bfb9a7bad31f23ff74d3285",
    ),
    "iter204_history.json": (
        4039,
        "a6b24cefb9527d0529cca94630f47341d49a8d6f8daf902f83a1009d8fd9dcea",
    ),
    "primary_ci_projection.json": (
        1423,
        "37df16b45a717397816d6f4013a462dacbe8977e8ba1216a3e83d137aed8371a",
    ),
    "publication_pr.json": (
        526,
        "2e1c8c7b6eeff49fcf8acf98381f4da6d9586b2fea9e9edb38792bae5dad4f94",
    ),
    "workflow.json": (
        424,
        "78f7ff355c4c4998adf5903fba04377bbe4794fad1d8d166a286b19e56a9133d",
    ),
}
TERMINAL_NEXT_ACTION = (
    "Do not dispatch or rerun iter205. Preserve its empty histories and frozen bytes. "
    "Pre-register iter206 to admit exactly the known four-row iter204 baseline plus the "
    "one final iter206 branch-publication row and one iter206 merge-publication row, "
    "while rejecting every unrelated or additional record. Publish iter206 exactly "
    "once, require green primary CI, and permit at most one iter206 dispatch request "
    "only after the complete exact-six admission gate passes."
)


class PreDispatchNullError(ValueError):
    """The normalized null or one of its public snapshots differs."""


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
    try:
        iter204_null.validate()
    except (OSError, iter204_null.PreDispatchNullError) as exc:
        raise PreDispatchNullError("frozen iter204 null no longer verifies") from exc
    frozen = {
        WORKFLOW: WORKFLOW_SHA256,
        HYPOTHESIS: HYPOTHESIS_SHA256,
        RUNTIME_MANIFEST: RUNTIME_MANIFEST_SHA256,
        PUBLICATION_SAFETY: PUBLICATION_SAFETY_SHA256,
        PENDING_LEARNING: PENDING_LEARNING_SHA256,
    }
    for path, expected in frozen.items():
        if path.is_symlink() or not path.is_file() or sha256(path.read_bytes()) != expected:
            raise PreDispatchNullError(
                f"frozen iter205 source differs: {path.relative_to(ROOT)}"
            )


def validate_public_metadata() -> dict[str, Any]:
    if MANIFEST.is_symlink() or sha256(MANIFEST.read_bytes()) != PUBLIC_MANIFEST_SHA256:
        raise PreDispatchNullError("iter205 public admission manifest differs")
    manifest, _ = load_strict(MANIFEST)
    if (
        manifest.get("schema_version")
        != "telos.iter205.public_pre_dispatch_admission_metadata.v1"
        or manifest.get("iter205_workflow_id") != ITER205_WORKFLOW_ID
        or manifest.get("iter205_workflow_state") != "active"
        or manifest.get("iter205_all_event_run_count") != 0
        or manifest.get("iter205_workflow_dispatch_run_count") != 0
        or manifest.get("iter204_workflow_id") != ITER204_WORKFLOW_ID
        or manifest.get("iter204_baseline_push_run_count") != 2
        or manifest.get("iter204_observed_push_run_count") != 4
        or manifest.get("iter204_workflow_dispatch_run_count") != 0
    ):
        raise PreDispatchNullError("iter205 public admission manifest identity differs")
    rows = manifest.get("files")
    if not isinstance(rows, list) or len(rows) != len(PUBLIC_FILES):
        raise PreDispatchNullError("iter205 public admission inventory differs")
    by_name = {row.get("path"): row for row in rows if isinstance(row, dict)}
    if set(by_name) != set(PUBLIC_FILES):
        raise PreDispatchNullError("iter205 public admission paths differ")
    for name, (expected_bytes, expected_hash) in PUBLIC_FILES.items():
        path = PUBLIC / name
        row = by_name[name]
        if path.is_symlink() or not path.is_file():
            raise PreDispatchNullError(f"iter205 public snapshot is absent: {name}")
        payload = path.read_bytes()
        if (
            len(payload) != expected_bytes
            or sha256(payload) != expected_hash
            or row.get("bytes") != expected_bytes
            or row.get("sha256") != expected_hash
        ):
            raise PreDispatchNullError(f"iter205 public snapshot differs: {name}")
        load_strict(path)
    if {path.name for path in PUBLIC.iterdir()} != set(PUBLIC_FILES) | {"manifest.json"}:
        raise PreDispatchNullError("iter205 public snapshot directory inventory differs")

    workflow, _ = load_strict(PUBLIC / "workflow.json")
    if (
        workflow.get("id") != ITER205_WORKFLOW_ID
        or workflow.get("name") != "iter205-execute"
        or workflow.get("path") != ".github/workflows/iter205-execute.yml"
        or workflow.get("state") != "active"
    ):
        raise PreDispatchNullError("iter205 public workflow object differs")
    expected_empty = {"total_count": 0, "workflow_runs": []}
    for name in ("all_runs.json", "dispatch_runs.json"):
        document, _ = load_strict(PUBLIC / name)
        if document != expected_empty:
            raise PreDispatchNullError(f"iter205 history is not exact zero: {name}")
    return manifest


def validate_iter204_history() -> None:
    document, _ = load_strict(PUBLIC / "iter204_history.json")
    rows = document.get("runs")
    if document.get("total_count") != 4 or not isinstance(rows, list) or len(rows) != 4:
        raise PreDispatchNullError("iter204 admission-time history count differs")
    by_id = {row.get("id"): row for row in rows if isinstance(row, dict)}
    if set(by_id) != set(ITER204_RUN_IDS):
        raise PreDispatchNullError("iter204 admission-time run identities differ")
    expected = {
        29465584664: (
            1,
            "agent/iter204-infrastructure-recovery",
            "8342315dd2fa7ec865bd7c654ec4ec098675dfab",
        ),
        29465924803: (2, "master", "c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446"),
        29468669956: (
            3,
            "agent/iter205-workflow-context-recovery",
            FEATURE_SHA,
        ),
        29468768706: (4, "master", MERGE_SHA),
    }
    unavailable = {
        "documentation_url": (
            "https://docs.github.com/rest/actions/workflow-runs#download-workflow-run-logs"
        ),
        "http_status": 404,
        "message": "Not Found",
        "status": "404",
    }
    for run_id, (number, branch, source) in expected.items():
        row = by_id[run_id]
        if (
            row.get("workflow_id") != ITER204_WORKFLOW_ID
            or row.get("event") != "push"
            or row.get("status") != "completed"
            or row.get("conclusion") != "failure"
            or row.get("run_attempt") != 1
            or row.get("run_number") != number
            or row.get("head_branch") != branch
            or row.get("head_sha") != source
            or row.get("name") != ".github/workflows/iter204-execute.yml"
            or row.get("path") != ".github/workflows/iter204-execute.yml"
            or row.get("jobs_response") != {"jobs": [], "total_count": 0}
            or row.get("artifacts_response") != {"artifacts": [], "total_count": 0}
            or row.get("logs_download_response") != unavailable
        ):
            raise PreDispatchNullError(f"iter204 admission-time row differs: {run_id}")


def validate_publication_and_ci() -> None:
    publication, _ = load_strict(PUBLIC / "publication_pr.json")
    if (
        publication.get("number") != 7
        or publication.get("merged") is not True
        or publication.get("state") != "closed"
        or publication.get("head")
        != {"ref": "agent/iter205-workflow-context-recovery", "sha": FEATURE_SHA}
        or publication.get("base", {}).get("ref") != "master"
        or publication.get("merge_commit_sha") != MERGE_SHA
    ):
        raise PreDispatchNullError("iter205 publication projection differs")
    ci, _ = load_strict(PUBLIC / "primary_ci_projection.json")
    run = ci.get("run")
    jobs = ci.get("jobs")
    if (
        ci.get("total_count") != 2
        or not isinstance(run, dict)
        or run.get("id") != PRIMARY_CI_RUN_ID
        or run.get("run_attempt") != 1
        or run.get("event") != "push"
        or run.get("head_branch") != "master"
        or run.get("head_sha") != MERGE_SHA
        or run.get("path") != ".github/workflows/ci.yml"
        or run.get("status") != "completed"
        or run.get("conclusion") != "success"
        or not isinstance(jobs, list)
        or {(row.get("id"), row.get("name"), row.get("conclusion")) for row in jobs}
        != {
            (87527499496, "verify py3.12", "success"),
            (87527499530, "verify py3.11", "success"),
        }
        or {row.get("run_id") for row in jobs} != {PRIMARY_CI_RUN_ID}
        or {row.get("run_attempt") for row in jobs} != {1}
        or {row.get("head_sha") for row in jobs} != {MERGE_SHA}
    ):
        raise PreDispatchNullError("iter205 primary CI projection differs")


def validate_normalized_null() -> None:
    document, _ = load_strict(NULL)
    mismatch = document.get("admission_mismatch")
    request = document.get("dispatch_request")
    if (
        document.get("schema_version") != "telos.iter205.pre_dispatch_admission_null.v1"
        or document.get("experiment_id") != "iter205_iter204_workflow_context_recovery"
        or document.get("status") != "pre_dispatch_admission_null"
        or document.get("timing")
        != "post_merge_green_primary_ci_and_read_only_pre_dispatch_admission"
        or document.get("public_admission_metadata_manifest_path")
        != str(MANIFEST.relative_to(ROOT))
        or document.get("public_admission_metadata_manifest_sha256")
        != PUBLIC_MANIFEST_SHA256
        or mismatch
        != {
            "added_iter204_push_parse_failure_run_ids": [29468669956, 29468768706],
            "expected_iter204_total_run_count": 2,
            "mismatch_class": (
                "upstream_append_only_push_parse_history_exceeded_exact_frozen_count"
            ),
            "observed_iter204_total_run_count": 4,
            "predicate_path": (
                "experiments/iter205_iter204_workflow_context_recovery/HYPOTHESIS.md"
            ),
            "preflight_stage": "read_only_before_any_iter205_dispatch_request",
            "workflow_dispatch_run_count_in_iter204": 0,
        }
        or request
        != {
            "attempted": False,
            "request_count": 0,
            "workflow_dispatch_job_count": 0,
            "workflow_dispatch_run_count": 0,
        }
    ):
        raise PreDispatchNullError("iter205 normalized admission-null identity differs")
    if document.get("provider_accounting") != {
        "judge_calls": 0,
        "scenario_calls": 0,
        "solver_calls": 0,
    }:
        raise PreDispatchNullError("iter205 zero-provider boundary differs")
    scientific = document.get("scientific_evidence")
    if scientific != {
        "adjudication_executions": 0,
        "certification_executions": 0,
        "container_create_or_run_invocations": 0,
        "judge_executions": 0,
        "k": None,
        "n": None,
        "patch_applications": 0,
        "scenario_executions": 0,
        "scientific_artifacts": 0,
        "u": None,
    }:
        raise PreDispatchNullError("iter205 scientific-null boundary differs")
    if document.get("next_gate") != {
        "path": "experiments/iter206_iter205_admission_history_recovery/HYPOTHESIS.md",
        "status": "pending_separately_versioned_admission_history_recovery",
    }:
        raise PreDispatchNullError("iter205 separately versioned successor differs")
    source = document.get("workflow_source")
    if not isinstance(source, dict) or (
        source.get("workflow_id") != ITER205_WORKFLOW_ID
        or source.get("workflow_state") != "active"
        or source.get("name") != "iter205-execute"
        or source.get("path") != ".github/workflows/iter205-execute.yml"
        or source.get("sha256") != WORKFLOW_SHA256
        or source.get("frozen_hypothesis_sha256") != HYPOTHESIS_SHA256
        or source.get("frozen_runtime_manifest_sha256") != RUNTIME_MANIFEST_SHA256
        or source.get("frozen_publication_safety_sha256")
        != PUBLICATION_SAFETY_SHA256
    ):
        raise PreDispatchNullError("iter205 normalized workflow source differs")


def validate_terminal_learning_record() -> None:
    document, _ = load_strict(TERMINAL_LEARNING)
    required = {
        "experiment_id": "iter205_iter204_workflow_context_recovery_pre_dispatch_admission_null",
        "next_action": TERMINAL_NEXT_ACTION,
        "result_path": "experiments/iter205_iter204_workflow_context_recovery/RESULT.md",
        "schema_version": "telos.learning_record.v1",
        "status": "null",
        "supersedes": (
            "experiments/iter205_iter204_workflow_context_recovery/proof/learning_record.json"
        ),
        "timing": "post_iter205_read_only_admission_null_and_before_any_iter206_dispatch",
    }
    if any(document.get(key) != value for key, value in required.items()):
        raise PreDispatchNullError("iter205 terminal learning record differs")
    evidence = document.get("evidence_paths")
    expected_evidence = [
        "experiments/iter205_iter204_workflow_context_recovery/RESULT.md",
        (
            "experiments/iter205_iter204_workflow_context_recovery/proof/"
            "pre_dispatch_admission_null.json"
        ),
        (
            "experiments/iter205_iter204_workflow_context_recovery/proof/raw/"
            "public_admission_metadata/manifest.json"
        ),
        "experiments/iter206_iter205_admission_history_recovery/HYPOTHESIS.md",
    ]
    if evidence != expected_evidence:
        raise PreDispatchNullError("iter205 terminal learning evidence differs")
    for relative in expected_evidence:
        path = ROOT / relative
        if path.is_symlink() or not path.is_file():
            raise PreDispatchNullError(f"iter205 terminal learning evidence is absent: {relative}")
    records = [
        load_learning_record(PENDING_LEARNING, root=ROOT),
        load_learning_record(TERMINAL_LEARNING, root=ROOT),
    ]
    if latest_next_action(records) != TERMINAL_NEXT_ACTION:
        raise PreDispatchNullError("bounded iter205 learning transition differs")


def validate_result_surface() -> None:
    text = " ".join(RESULT.read_text(encoding="utf-8").split())
    required = (
        "PRE-DISPATCH ADMISSION-HISTORY NULL",
        FEATURE_SHA,
        MERGE_SHA,
        str(PRIMARY_CI_RUN_ID),
        str(ITER205_WORKFLOW_ID),
        "complete all-event history is empty",
        "complete `workflow_dispatch` history is empty",
        "four records",
        "No iter205 dispatch request was issued",
        "no dispatch API response or rejection exists",
        "There was no iter205 workflow run ID, run attempt, job, or run log",
        "contributes no `N`, `k`, or `u`; those quantities are absent, not zero",
        "separately versioned iter206 admission-history protocol",
    )
    missing = [fragment for fragment in required if fragment not in text]
    if missing:
        raise PreDispatchNullError(
            "iter205 result omits required bounded facts: " + ", ".join(missing)
        )
    forbidden = (
        "iter205 dispatch API request returned",
        "There was no iter205 API request",
        "No iter205 request, API rejection",
        "iter205 attempt `1`",
        "zero workflow runs",
    )
    hits = [fragment for fragment in forbidden if fragment in text]
    if hits:
        raise PreDispatchNullError(
            "iter205 result overstates the boundary: " + ", ".join(hits)
        )


def validate() -> dict[str, int]:
    validate_frozen_source()
    validate_public_metadata()
    validate_iter204_history()
    validate_publication_and_ci()
    validate_normalized_null()
    validate_terminal_learning_record()
    validate_result_surface()
    return {
        "dispatch_requests": 0,
        "iter204_push_parse_failures": 4,
        "iter205_workflow_runs": 0,
        "provider_calls": 0,
        "scientific_executions": 0,
    }


def main() -> int:
    try:
        summary = validate()
    except (OSError, PreDispatchNullError) as exc:
        print(f"iter205 pre-dispatch-null guard failed: {exc}", file=sys.stderr)
        return 1
    print(
        "iter205 pre-dispatch-null guard: "
        f"{summary['iter204_push_parse_failures']} iter204 push parse failures, "
        f"{summary['iter205_workflow_runs']} iter205 runs, "
        f"{summary['dispatch_requests']} iter205 dispatch requests, "
        f"{summary['scientific_executions']} scientific executions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
