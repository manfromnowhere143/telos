#!/usr/bin/env python3
"""Build the additive iter203 bridge over immutable iter202 provider evidence.

This program is deliberately provider-free.  It validates the exact iter202
source/runtime provenance and retained checkpoint corpus, applies the unchanged
frozen ``scenario_ast_errors`` function uniformly to every generated scenario,
and creates an execution projection containing only scenarios accepted by that
classifier.  It never writes beneath the iter202 experiment.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_EXPERIMENT_ID = "iter202_natural_rate_scaled"
EXPERIMENT_ID = "iter203_iter202_safety_recovery"
UPSTREAM_SOURCE_COMMIT = "8b8809ed6b358d16eb08fe38f0f2edf4a284af0e"
UPSTREAM_RUNTIME_MANIFEST_SHA256 = (
    "dd935a6f5873940fca5768891bb74a6cc635ef86bb65cdf493dd2a8ffe043868"
)
UPSTREAM_CLASSIFIER_SHA256 = (
    "4ccec3626a3ce5661c0251b268e422bc208f1c32181a97711d84ee2ade771ee6"
)

UPSTREAM = ROOT / "experiments" / UPSTREAM_EXPERIMENT_ID
UPSTREAM_RAW = UPSTREAM / "proof/raw"
UPSTREAM_SOLUTIONS = UPSTREAM_RAW / "solutions"
UPSTREAM_SCENARIOS = UPSTREAM_RAW / "scenarios"
UPSTREAM_RUNTIME_MANIFEST = UPSTREAM_RAW / "runtime_manifest.json"
UPSTREAM_TARGETS = UPSTREAM_RAW / "solve_targets.json"
UPSTREAM_CLASSIFIER = ROOT / "scripts/validate_iter202_scenario_safety.py"
UPSTREAM_SCENARIO_HELPER = ROOT / "scripts/run_iter195_scenario_generator.py"

EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
RAW = EXPERIMENT / "proof/raw"
BRIDGE = RAW / "safety_recovery_bridge"
PROJECTED_SOLUTIONS = RAW / "solutions"
PROJECTED_SCENARIOS = RAW / "scenarios"

UPSTREAM_INVENTORY = BRIDGE / "upstream_inventory.json"
SCENARIO_DISPOSITION = BRIDGE / "scenario_disposition.json"
SAFE_SCENARIO_INDEX = BRIDGE / "safe_scenario_index.json"
SOLUTION_PROJECTION_INDEX = BRIDGE / "solution_projection_index.json"

INVENTORY_SCHEMA = "telos.iter203.upstream_inventory.v1"
DISPOSITION_SCHEMA = "telos.iter203.scenario_safety_disposition.v1"
SAFE_INDEX_SCHEMA = "telos.iter203.safe_scenario_index.v1"
SOLUTION_INDEX_SCHEMA = "telos.iter203.solution_projection_index.v1"
PROJECTED_SCENARIO_SCHEMA = "telos.iter203.scenarios_summary.v1"

STARTED_SCHEMA = "telos.iter202.provider_attempt.started.v2"
FINISHED_SCHEMA = "telos.iter202.provider_attempt.finished.v2"
SOLVE_SUMMARY_SCHEMA = "telos.iter200.solve_summary.v1"
SCENARIO_SUMMARY_SCHEMA = "telos.iter200.scenarios_summary.v1"
FROZEN_MODEL = "gpt-5.6-terra"

EXPECTED_SOLVER_ATTEMPTS = 53
EXPECTED_SOLUTIONS = 50
EXPECTED_SCENARIO_ATTEMPTS = 39
EXPECTED_GENERATED_SCENARIOS = 38
EXPECTED_SAFE_SCENARIOS = 29
EXPECTED_UNSAFE_SCENARIOS = 9
EXPECTED_NO_SCENARIO = 1
EXPECTED_SAFETY_FINDINGS = 21

SHA256_RE = re.compile(r"[0-9a-f]{64}")
ATTEMPT_ID_RE = re.compile(r"[0-9a-f]{32}")
INSTANCE_ID_RE = re.compile(r"[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+")
CHECKPOINT_NAME_RE = re.compile(
    r"(?P<sequence>[0-9]{4})-"
    r"(?P<instance_id>[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+)-"
    r"(?P<attempt_id>[0-9a-f]{32})\."
    r"(?P<kind>started|finished)\.json"
)

STARTED_KEYS = {
    "accounting",
    "attempt_id",
    "experiment_id",
    "instance_id",
    "model",
    "phase",
    "prompt_sha256",
    "runtime_manifest_sha256",
    "schema_version",
    "sequence",
}
FINISHED_RESPONSE_KEYS = {
    "attempt_id",
    "experiment_id",
    "instance_id",
    "outcome",
    "phase",
    "provider_usage",
    "raw_response",
    "raw_response_sha256",
    "schema_version",
    "sequence",
    "started_record_sha256",
}
FINISHED_ERROR_KEYS = {
    "attempt_id",
    "error",
    "experiment_id",
    "instance_id",
    "outcome",
    "phase",
    "schema_version",
    "sequence",
    "started_record_sha256",
}

BRIDGE_FILENAMES = {
    "upstream_inventory.json",
    "scenario_disposition.json",
    "safe_scenario_index.json",
    "solution_projection_index.json",
}


class RecoveryError(ValueError):
    """The upstream evidence or iter203 projection violates the bridge contract."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise RecoveryError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _reject_nonfinite(value: str) -> None:
    raise RecoveryError(f"non-finite JSON constant: {value}")


def load_json_strict(path: Path) -> dict[str, Any]:
    raw = _regular_bytes(path, "JSON evidence")
    try:
        value = json.loads(
            raw,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RecoveryError(f"cannot parse strict JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RecoveryError(f"JSON root must be an object: {path}")
    return value


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _open_directory_nofollow(path: Path, label: str) -> int:
    """Pin an absolute directory one no-follow component at a time."""

    if not path.is_absolute() or ".." in path.parts or not path.parts:
        raise RecoveryError(f"{label} path is not absolute and canonical: {path}")
    if not hasattr(os, "O_NOFOLLOW"):
        raise RecoveryError("O_NOFOLLOW is required for iter203 bridge verification")
    flags = (
        os.O_RDONLY
        | os.O_NOFOLLOW
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        descriptor = os.open(path.parts[0], flags)
    except OSError as exc:
        raise RecoveryError(f"cannot anchor {label} at {path.parts[0]}: {exc}") from exc
    current = Path(path.parts[0])
    try:
        for component in path.parts[1:]:
            current /= component
            try:
                child = os.open(component, flags, dir_fd=descriptor)
            except OSError as exc:
                raise RecoveryError(
                    f"cannot traverse {label} without following symlinks at {current}: {exc}"
                ) from exc
            os.close(descriptor)
            descriptor = child
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _stable_stat_fields(metadata: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _regular_bytes(path: Path, label: str) -> bytes:
    """Read one stable regular file through a pinned no-follow parent."""

    if not path.is_absolute() or ".." in path.parts or not path.name:
        raise RecoveryError(f"{label} path is not absolute and canonical: {path}")
    parent_descriptor = _open_directory_nofollow(path.parent, f"{label} parent")
    try:
        try:
            named_before = os.stat(path.name, dir_fd=parent_descriptor, follow_symlinks=False)
        except OSError as exc:
            raise RecoveryError(f"cannot stat {label} {path}: {exc}") from exc
        if not stat.S_ISREG(named_before.st_mode):
            raise RecoveryError(f"{label} is missing, non-regular, or symlinked: {path}")
        flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        try:
            descriptor = os.open(path.name, flags, dir_fd=parent_descriptor)
        except OSError as exc:
            raise RecoveryError(f"cannot securely open {label} {path}: {exc}") from exc
        try:
            opened_before = os.fstat(descriptor)
            identity = _stable_stat_fields(opened_before)
            if not stat.S_ISREG(opened_before.st_mode) or identity != _stable_stat_fields(
                named_before
            ):
                raise RecoveryError(f"{label} changed before secure open: {path}")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            opened_after = os.fstat(descriptor)
        finally:
            os.close(descriptor)
        if identity != _stable_stat_fields(opened_after):
            raise RecoveryError(f"{label} changed while being read: {path}")
        try:
            named_after = os.stat(path.name, dir_fd=parent_descriptor, follow_symlinks=False)
        except OSError as exc:
            raise RecoveryError(f"cannot restat {label} {path}: {exc}") from exc
        if identity != _stable_stat_fields(named_after):
            raise RecoveryError(f"{label} path changed while being read: {path}")
        raw = b"".join(chunks)
        if len(raw) != opened_after.st_size:
            raise RecoveryError(f"short read for {label}: {path}")
        return raw
    finally:
        os.close(parent_descriptor)


def _relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError as exc:
        raise RecoveryError(f"path escapes the TELOS repository: {path}") from exc


def _safe_repo_relative(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise RecoveryError(f"{label} is not text")
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or not candidate.parts or ".." in candidate.parts:
        raise RecoveryError(f"{label} is not a safe repository-relative path: {value!r}")
    return value


def _git_bytes(*arguments: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), *arguments],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        raise RecoveryError(f"cannot execute Git provenance check: {exc}") from exc
    if result.returncode != 0:
        raise RecoveryError(
            "Git provenance check failed: " + " ".join(repr(item) for item in arguments)
        )
    return result.stdout


def _validate_upstream_source() -> dict[str, Any]:
    resolved = _git_bytes("rev-parse", f"{UPSTREAM_SOURCE_COMMIT}^{{commit}}")
    if resolved.decode("ascii").strip() != UPSTREAM_SOURCE_COMMIT:
        raise RecoveryError("upstream source commit does not resolve exactly")

    manifest_raw = _regular_bytes(UPSTREAM_RUNTIME_MANIFEST, "upstream runtime manifest")
    if sha256(manifest_raw) != UPSTREAM_RUNTIME_MANIFEST_SHA256:
        raise RecoveryError("upstream runtime manifest SHA-256 mismatch")
    manifest_path = _relative(UPSTREAM_RUNTIME_MANIFEST)
    if _git_bytes("show", f"{UPSTREAM_SOURCE_COMMIT}:{manifest_path}") != manifest_raw:
        raise RecoveryError("upstream runtime manifest differs from its source commit")

    manifest = load_json_strict(UPSTREAM_RUNTIME_MANIFEST)
    files = manifest.get("files")
    if (
        manifest.get("schema_version") != "telos.iter202.runtime_freeze.v1"
        or manifest.get("experiment_id") != UPSTREAM_EXPERIMENT_ID
        or not isinstance(files, list)
        or manifest.get("file_count") != len(files)
    ):
        raise RecoveryError("upstream runtime manifest has an invalid identity or inventory")

    seen: set[str] = set()
    classifier_record: dict[str, Any] | None = None
    for index, record in enumerate(files):
        if not isinstance(record, dict) or set(record) != {
            "bytes",
            "path",
            "role",
            "sha256",
        }:
            raise RecoveryError(f"upstream runtime file record {index} is malformed")
        relative = _safe_repo_relative(record.get("path"), f"runtime file record {index}")
        if relative in seen:
            raise RecoveryError(f"upstream runtime inventory duplicates {relative}")
        seen.add(relative)
        current = _regular_bytes(ROOT / relative, "frozen upstream source")
        if record.get("bytes") != len(current) or record.get("sha256") != sha256(current):
            raise RecoveryError(f"frozen upstream source hash mismatch: {relative}")
        if _git_bytes("show", f"{UPSTREAM_SOURCE_COMMIT}:{relative}") != current:
            raise RecoveryError(f"frozen upstream source differs from source commit: {relative}")
        if relative == _relative(UPSTREAM_CLASSIFIER):
            classifier_record = record

    if classifier_record is None or classifier_record.get("sha256") != UPSTREAM_CLASSIFIER_SHA256:
        raise RecoveryError("frozen scenario classifier is absent or has the wrong hash")
    return manifest


def _load_upstream_functions() -> tuple[Callable[[str], list[str]], Callable[[str], str]]:
    def load(path: Path, name: str) -> Any:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RecoveryError(f"cannot load frozen helper: {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    classifier = load(UPSTREAM_CLASSIFIER, "iter203_frozen_scenario_classifier")
    helper = load(UPSTREAM_SCENARIO_HELPER, "iter203_frozen_scenario_helper")
    if not callable(getattr(classifier, "scenario_ast_errors", None)):
        raise RecoveryError("frozen scenario_ast_errors is unavailable")
    if not callable(getattr(helper, "extract_code", None)):
        raise RecoveryError("frozen extract_code is unavailable")
    return classifier.scenario_ast_errors, helper.extract_code


def _canonical_checkpoint_bytes(data: dict[str, Any], path: Path) -> bytes:
    raw = canonical_json_bytes(data)
    if _regular_bytes(path, "provider checkpoint") != raw:
        raise RecoveryError(f"provider checkpoint is not canonical strict JSON: {path}")
    return raw


def _attempt_pairs(
    directory: Path,
    *,
    phase: str,
    expected_ids: list[str],
) -> list[dict[str, Any]]:
    directory_descriptor = _open_directory_nofollow(directory, f"{phase} checkpoint directory")
    try:
        names_before = sorted(os.listdir(directory_descriptor))
        for name in names_before:
            metadata = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
            if not stat.S_ISREG(metadata.st_mode):
                raise RecoveryError(
                    f"checkpoint directory contains a non-regular entry: {directory / name}"
                )
        if sorted(os.listdir(directory_descriptor)) != names_before:
            raise RecoveryError(f"{phase} checkpoint directory changed while enumerated")
    finally:
        os.close(directory_descriptor)
    paths = [directory / name for name in names_before]
    if len(paths) != 2 * len(expected_ids):
        raise RecoveryError(
            f"{phase} checkpoint file count mismatch: expected={2 * len(expected_ids)} actual={len(paths)}"
        )

    indexed: dict[tuple[int, str], Path] = {}
    for path in paths:
        match = CHECKPOINT_NAME_RE.fullmatch(path.name)
        if match is None:
            raise RecoveryError(f"unexpected {phase} checkpoint filename: {path.name}")
        key = (int(match.group("sequence")), match.group("kind"))
        if key in indexed:
            raise RecoveryError(f"duplicate {phase} checkpoint sequence/kind: {key}")
        indexed[key] = path

    pairs: list[dict[str, Any]] = []
    for sequence, expected_iid in enumerate(expected_ids, 1):
        started_path = indexed.get((sequence, "started"))
        finished_path = indexed.get((sequence, "finished"))
        if started_path is None or finished_path is None:
            raise RecoveryError(f"missing {phase} checkpoint pair at sequence {sequence}")
        started_match = CHECKPOINT_NAME_RE.fullmatch(started_path.name)
        finished_match = CHECKPOINT_NAME_RE.fullmatch(finished_path.name)
        assert started_match is not None and finished_match is not None
        if (
            started_match.group("instance_id") != expected_iid
            or finished_match.group("instance_id") != expected_iid
            or started_match.group("attempt_id") != finished_match.group("attempt_id")
        ):
            raise RecoveryError(f"{phase} checkpoint filename identity mismatch at {sequence}")

        started = load_json_strict(started_path)
        finished = load_json_strict(finished_path)
        started_raw = _canonical_checkpoint_bytes(started, started_path)
        finished_raw = _canonical_checkpoint_bytes(finished, finished_path)
        attempt_id = started_match.group("attempt_id")
        if (
            set(started) != STARTED_KEYS
            or started.get("schema_version") != STARTED_SCHEMA
            or started.get("experiment_id") != UPSTREAM_EXPERIMENT_ID
            or started.get("phase") != phase
            or started.get("model") != FROZEN_MODEL
            or started.get("runtime_manifest_sha256") != UPSTREAM_RUNTIME_MANIFEST_SHA256
            or started.get("sequence") != sequence
            or started.get("instance_id") != expected_iid
            or started.get("attempt_id") != attempt_id
            or not SHA256_RE.fullmatch(str(started.get("prompt_sha256", "")))
            or started.get("accounting")
            != {"estimated_spend_usd": 0.05, "provider_calls": 1}
        ):
            raise RecoveryError(f"malformed {phase} started checkpoint at {sequence}")

        outcome = finished.get("outcome")
        expected_finished_keys = (
            FINISHED_RESPONSE_KEYS if outcome == "response" else FINISHED_ERROR_KEYS
        )
        if (
            outcome not in {"response", "provider_error"}
            or set(finished) != expected_finished_keys
            or finished.get("schema_version") != FINISHED_SCHEMA
            or finished.get("experiment_id") != UPSTREAM_EXPERIMENT_ID
            or finished.get("phase") != phase
            or finished.get("sequence") != sequence
            or finished.get("instance_id") != expected_iid
            or finished.get("attempt_id") != attempt_id
            or finished.get("started_record_sha256") != sha256(started_raw)
        ):
            raise RecoveryError(f"malformed {phase} finished checkpoint at {sequence}")
        if outcome == "response":
            raw_response = finished.get("raw_response")
            if (
                not isinstance(raw_response, str)
                or not SHA256_RE.fullmatch(str(finished.get("raw_response_sha256", "")))
                or sha256(raw_response.encode("utf-8")) != finished["raw_response_sha256"]
                or not isinstance(finished.get("provider_usage"), dict)
            ):
                raise RecoveryError(f"invalid retained response at {phase} sequence {sequence}")
        else:
            if not isinstance(finished.get("error"), dict):
                raise RecoveryError(f"invalid retained provider error at {phase} sequence {sequence}")

        pairs.append(
            {
                "attempt_id": attempt_id,
                "finished": finished,
                "finished_path": finished_path,
                "finished_sha256": sha256(finished_raw),
                "instance_id": expected_iid,
                "sequence": sequence,
                "started": started,
                "started_path": started_path,
                "started_sha256": sha256(started_raw),
            }
        )
    return pairs


def _stage_entries(directory: Path) -> set[str]:
    descriptor = _open_directory_nofollow(directory, "upstream stage")
    try:
        try:
            names_before = sorted(os.listdir(descriptor))
        except OSError as exc:
            raise RecoveryError(f"cannot enumerate upstream stage {directory}: {exc}") from exc
        entries: set[str] = set()
        for name in names_before:
            try:
                metadata = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            except OSError as exc:
                raise RecoveryError(f"cannot stat upstream stage entry {directory / name}: {exc}") from exc
            if stat.S_ISDIR(metadata.st_mode):
                if name != "provider_attempts":
                    raise RecoveryError(
                        f"upstream stage contains unexpected directory: {directory / name}"
                    )
                child = _open_directory_nofollow(
                    directory / name, "upstream checkpoint directory"
                )
                os.close(child)
            elif not stat.S_ISREG(metadata.st_mode):
                raise RecoveryError(
                    f"upstream stage contains a non-regular entry: {directory / name}"
                )
            entries.add(name)
        if sorted(os.listdir(descriptor)) != names_before:
            raise RecoveryError(f"upstream stage changed while enumerated: {directory}")
        return entries
    finally:
        os.close(descriptor)


def _validate_upstream_evidence() -> dict[str, Any]:
    solve_summary = load_json_strict(UPSTREAM_SOLUTIONS / "solve_summary.json")
    scenario_summary = load_json_strict(UPSTREAM_SCENARIOS / "scenarios_summary.json")
    targets = load_json_strict(UPSTREAM_TARGETS)
    target_rows = targets.get("targets")
    if (
        targets.get("schema_version") != "telos.iter202.solve_targets.v1"
        or targets.get("count") != EXPECTED_SOLVER_ATTEMPTS
        or not isinstance(target_rows, list)
        or len(target_rows) != EXPECTED_SOLVER_ATTEMPTS
    ):
        raise RecoveryError("upstream target manifest is malformed")
    target_ids = [row.get("instance_id") if isinstance(row, dict) else None for row in target_rows]
    if (
        any(not isinstance(iid, str) or INSTANCE_ID_RE.fullmatch(iid) is None for iid in target_ids)
        or len(set(target_ids)) != len(target_ids)
    ):
        raise RecoveryError("upstream target IDs are malformed or duplicated")

    solve_manifest = solve_summary.get("manifest")
    if (
        set(solve_summary)
        != {
            "checkpoint_schema",
            "estimated_spend_usd",
            "manifest",
            "provider_calls",
            "schema_version",
            "solutions",
            "solver_model",
            "targets",
        }
        or solve_summary.get("schema_version") != SOLVE_SUMMARY_SCHEMA
        or solve_summary.get("checkpoint_schema")
        != {"finished": FINISHED_SCHEMA, "started": STARTED_SCHEMA}
        or solve_summary.get("solver_model") != FROZEN_MODEL
        or solve_summary.get("targets") != EXPECTED_SOLVER_ATTEMPTS
        or solve_summary.get("provider_calls") != EXPECTED_SOLVER_ATTEMPTS
        or solve_summary.get("solutions") != EXPECTED_SOLUTIONS
        or solve_summary.get("estimated_spend_usd") != 2.65
        or not isinstance(solve_manifest, list)
        or len(solve_manifest) != EXPECTED_SOLVER_ATTEMPTS
        or [row.get("instance_id") for row in solve_manifest if isinstance(row, dict)]
        != target_ids
    ):
        raise RecoveryError("upstream solve summary is malformed or out of frozen order")
    solution_rows = [row for row in solve_manifest if row.get("status") == "solution"]
    if (
        len(solution_rows) != EXPECTED_SOLUTIONS
        or sum(row.get("status") == "empty_fix" for row in solve_manifest) != 3
        or any(row.get("status") not in {"solution", "empty_fix"} for row in solve_manifest)
    ):
        raise RecoveryError("upstream solve status distribution changed")

    solver_attempts = _attempt_pairs(
        UPSTREAM_SOLUTIONS / "provider_attempts",
        phase="neutral_solver",
        expected_ids=target_ids,
    )
    solver_attempt_by_id = {row["instance_id"]: row for row in solver_attempts}
    for row in solve_manifest:
        attempt = solver_attempt_by_id[row["instance_id"]]
        if row.get("provider_attempt_id") != attempt["attempt_id"]:
            raise RecoveryError(f"solve summary/checkpoint attempt mismatch: {row['instance_id']}")
        if row.get("status") == "solution":
            finished = attempt["finished"]
            if (
                finished.get("outcome") != "response"
                or row.get("provider_response_sha256") != finished.get("raw_response_sha256")
            ):
                raise RecoveryError(f"solve summary/response mismatch: {row['instance_id']}")

    solution_ids = [row["instance_id"] for row in solution_rows]
    expected_solution_entries = {
        "provider_attempts",
        "solve_summary.json",
        *(f"{iid}.gold.patch" for iid in solution_ids),
        *(f"{iid}.model.patch" for iid in solution_ids),
    }
    actual_solution_entries = _stage_entries(UPSTREAM_SOLUTIONS)
    if actual_solution_entries != expected_solution_entries:
        raise RecoveryError(
            "upstream solution stage file set mismatch: "
            f"missing={sorted(expected_solution_entries - actual_solution_entries)} "
            f"extra={sorted(actual_solution_entries - expected_solution_entries)}"
        )
    for row in solution_rows:
        iid = row["instance_id"]
        model_raw = _regular_bytes(UPSTREAM_SOLUTIONS / f"{iid}.model.patch", "model patch")
        _regular_bytes(UPSTREAM_SOLUTIONS / f"{iid}.gold.patch", "gold patch")
        if (
            not model_raw.endswith(b"\n")
            or row.get("model_patch_sha256") != sha256(model_raw[:-1])
        ):
            raise RecoveryError(f"model patch hash mismatch: {iid}")

    scenario_manifest = scenario_summary.get("manifest")
    differing_ids = [
        row["instance_id"]
        for row in solve_manifest
        if row.get("status") == "solution" and not row.get("identical_to_gold")
    ]
    if (
        set(scenario_summary)
        != {
            "checkpoint_schema",
            "differing_solutions",
            "estimated_spend_usd",
            "manifest",
            "model",
            "provider_calls",
            "scenarios",
            "schema_version",
        }
        or scenario_summary.get("schema_version") != SCENARIO_SUMMARY_SCHEMA
        or scenario_summary.get("checkpoint_schema")
        != {"finished": FINISHED_SCHEMA, "started": STARTED_SCHEMA}
        or scenario_summary.get("model") != FROZEN_MODEL
        or scenario_summary.get("differing_solutions") != EXPECTED_SCENARIO_ATTEMPTS
        or scenario_summary.get("provider_calls") != EXPECTED_SCENARIO_ATTEMPTS
        or scenario_summary.get("scenarios") != EXPECTED_GENERATED_SCENARIOS
        or scenario_summary.get("estimated_spend_usd") != 1.95
        or not isinstance(scenario_manifest, list)
        or len(scenario_manifest) != EXPECTED_SCENARIO_ATTEMPTS
        or [row.get("instance_id") for row in scenario_manifest if isinstance(row, dict)]
        != differing_ids
    ):
        raise RecoveryError("upstream scenario summary is malformed or out of frozen order")
    scenario_rows = [row for row in scenario_manifest if row.get("status") == "scenario"]
    no_scenario_rows = [row for row in scenario_manifest if row.get("status") == "no_scenario"]
    if (
        len(scenario_rows) != EXPECTED_GENERATED_SCENARIOS
        or len(no_scenario_rows) != EXPECTED_NO_SCENARIO
        or any(row.get("status") not in {"scenario", "no_scenario"} for row in scenario_manifest)
    ):
        raise RecoveryError("upstream scenario status distribution changed")

    scenario_attempts = _attempt_pairs(
        UPSTREAM_SCENARIOS / "provider_attempts",
        phase="scenario_generation",
        expected_ids=differing_ids,
    )
    scenario_attempt_by_id = {row["instance_id"]: row for row in scenario_attempts}
    for row in scenario_manifest:
        attempt = scenario_attempt_by_id[row["instance_id"]]
        finished = attempt["finished"]
        if (
            row.get("provider_attempt_id") != attempt["attempt_id"]
            or finished.get("outcome") != "response"
        ):
            raise RecoveryError(f"scenario summary/checkpoint mismatch: {row['instance_id']}")
        if row.get("status") == "scenario" and row.get(
            "provider_response_sha256"
        ) != finished.get("raw_response_sha256"):
            raise RecoveryError(f"scenario response hash mismatch: {row['instance_id']}")

    scenario_ids = [row["instance_id"] for row in scenario_rows]
    expected_scenario_entries = {
        "provider_attempts",
        "scenarios_summary.json",
        *(f"{iid}.scenario.py" for iid in scenario_ids),
    }
    actual_scenario_entries = _stage_entries(UPSTREAM_SCENARIOS)
    if actual_scenario_entries != expected_scenario_entries:
        raise RecoveryError(
            "upstream scenario stage file set mismatch: "
            f"missing={sorted(expected_scenario_entries - actual_scenario_entries)} "
            f"extra={sorted(actual_scenario_entries - expected_scenario_entries)}"
        )

    return {
        "differing_ids": differing_ids,
        "scenario_attempts": scenario_attempts,
        "scenario_manifest": scenario_manifest,
        "scenario_summary": scenario_summary,
        "solution_rows": solution_rows,
        "solve_summary": solve_summary,
        "solver_attempts": solver_attempts,
    }


def _file_record(path: Path, role: str) -> dict[str, Any]:
    raw = _regular_bytes(path, role)
    return {
        "bytes": len(raw),
        "path": _relative(path),
        "role": role,
        "sha256": sha256(raw),
    }


def _inventory_records(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for attempt in evidence["solver_attempts"]:
        records.extend(
            (
                _file_record(attempt["started_path"], "solution_started_checkpoint"),
                _file_record(attempt["finished_path"], "solution_finished_checkpoint"),
            )
        )
    for row in evidence["solution_rows"]:
        iid = row["instance_id"]
        records.extend(
            (
                _file_record(UPSTREAM_SOLUTIONS / f"{iid}.gold.patch", "gold_patch"),
                _file_record(UPSTREAM_SOLUTIONS / f"{iid}.model.patch", "model_patch"),
            )
        )
    records.append(_file_record(UPSTREAM_SOLUTIONS / "solve_summary.json", "solve_summary"))
    for attempt in evidence["scenario_attempts"]:
        records.extend(
            (
                _file_record(attempt["started_path"], "scenario_started_checkpoint"),
                _file_record(attempt["finished_path"], "scenario_finished_checkpoint"),
            )
        )
    for row in evidence["scenario_manifest"]:
        if row["status"] == "scenario":
            records.append(
                _file_record(
                    UPSTREAM_SCENARIOS / f"{row['instance_id']}.scenario.py",
                    "scenario_script",
                )
            )
    records.append(
        _file_record(UPSTREAM_SCENARIOS / "scenarios_summary.json", "scenarios_summary")
    )
    return sorted(records, key=lambda row: row["path"])


def _inventory_closure(records: list[dict[str, Any]]) -> dict[str, str]:
    digest = hashlib.sha256()
    for row in records:
        digest.update(row["path"].encode("utf-8"))
        digest.update(b"\0")
        digest.update(row["role"].encode("utf-8"))
        digest.update(b"\0")
        digest.update(row["sha256"].encode("ascii"))
        digest.update(b"\0")
        digest.update(str(row["bytes"]).encode("ascii"))
        digest.update(b"\n")
    return {
        "algorithm": "SHA-256(path NUL role NUL file_sha256 NUL byte_count LF), path-sorted",
        "sha256": digest.hexdigest(),
    }


ERROR_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"^absolute or parent-traversal path literal is forbidden$"),
        "absolute_or_parent_traversal_path_literal",
    ),
    (re.compile(r"^call through unsafe import alias: (?P<subject>.+)$"), "call_through_unsafe_import_alias"),
    (re.compile(r"^unsafe dynamic/builtin call: (?P<subject>.+)$"), "unsafe_dynamic_or_builtin_call"),
    (re.compile(r"^unsafe import alias: (?P<subject>.+)$"), "unsafe_import_alias"),
    (re.compile(r"^unsafe import root: (?P<subject>.+)$"), "unsafe_import_root"),
    (
        re.compile(r"^unsafe process/network/filesystem call: (?P<subject>.+)$"),
        "unsafe_process_network_or_filesystem_call",
    ),
)


def canonical_finding(message: str) -> dict[str, str | None]:
    for pattern, code in ERROR_PATTERNS:
        match = pattern.fullmatch(message)
        if match is not None:
            return {
                "code": code,
                "message": message,
                "subject": match.groupdict().get("subject"),
            }
    raise RecoveryError(f"frozen classifier returned an unregistered safety finding: {message}")


def _scenario_dispositions(
    evidence: dict[str, Any],
    classifier: Callable[[str], list[str]],
    extractor: Callable[[str], str],
) -> tuple[list[dict[str, Any]], dict[str, bytes]]:
    attempts = {row["instance_id"]: row for row in evidence["scenario_attempts"]}
    dispositions: list[dict[str, Any]] = []
    safe_payloads: dict[str, bytes] = {}
    for sequence, summary_row in enumerate(evidence["scenario_manifest"], 1):
        iid = summary_row["instance_id"]
        attempt = attempts[iid]
        finished = attempt["finished"]
        raw_response = finished["raw_response"]
        base = {
            "finished_checkpoint_path": _relative(attempt["finished_path"]),
            "finished_checkpoint_sha256": attempt["finished_sha256"],
            "instance_id": iid,
            "provider_attempt_id": attempt["attempt_id"],
            "provider_response_sha256": finished["raw_response_sha256"],
            "sequence": sequence,
            "started_checkpoint_path": _relative(attempt["started_path"]),
            "started_checkpoint_sha256": attempt["started_sha256"],
        }
        extracted = extractor(raw_response)
        if summary_row["status"] == "no_scenario":
            if extracted.strip() and "RESULT=" in extracted:
                raise RecoveryError(f"no_scenario response now extracts as a scenario: {iid}")
            dispositions.append(
                {
                    **base,
                    "safe_copy_path": None,
                    "safety_finding_count": 0,
                    "safety_findings": [],
                    "scenario_payload_sha256": None,
                    "source_scenario_file_bytes": None,
                    "source_scenario_file_sha256": None,
                    "source_scenario_path": None,
                    "status": "no_scenario",
                }
            )
            continue

        scenario_path = UPSTREAM_SCENARIOS / f"{iid}.scenario.py"
        scenario_raw = _regular_bytes(scenario_path, "upstream scenario script")
        if (
            not scenario_raw.endswith(b"\n")
            or scenario_raw.endswith(b"\n\n")
            or b"\x00" in scenario_raw
            or b"\r" in scenario_raw
        ):
            raise RecoveryError(f"upstream scenario framing is invalid: {iid}")
        payload = scenario_raw[:-1]
        if (
            extracted.encode("utf-8") != payload
            or summary_row.get("scenario_sha256") != sha256(payload)
        ):
            raise RecoveryError(f"scenario script does not reproduce from provider response: {iid}")
        try:
            source = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RecoveryError(f"upstream scenario is not UTF-8: {iid}") from exc

        messages = classifier(source)
        if not isinstance(messages, list) or any(not isinstance(item, str) for item in messages):
            raise RecoveryError("frozen scenario classifier returned a malformed result")
        if messages != sorted(set(messages)):
            raise RecoveryError("frozen scenario classifier findings are not canonical and deduplicated")
        findings = [canonical_finding(message) for message in messages]
        status = "safe_scenario" if not findings else "unsafe_scenario"
        copy_path = PROJECTED_SCENARIOS / f"{iid}.scenario.py"
        if status == "safe_scenario":
            safe_payloads[iid] = scenario_raw
        dispositions.append(
            {
                **base,
                "safe_copy_path": _relative(copy_path) if status == "safe_scenario" else None,
                "safety_finding_count": len(findings),
                "safety_findings": findings,
                "scenario_payload_sha256": sha256(payload),
                "source_scenario_file_bytes": len(scenario_raw),
                "source_scenario_file_sha256": sha256(scenario_raw),
                "source_scenario_path": _relative(scenario_path),
                "status": status,
            }
        )
    return dispositions, safe_payloads


def _expected_counts(dispositions: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "generated_scenarios": sum(row["source_scenario_path"] is not None for row in dispositions),
        "no_scenario": sum(row["status"] == "no_scenario" for row in dispositions),
        "safe_scenarios": sum(row["status"] == "safe_scenario" for row in dispositions),
        "safety_findings": sum(row["safety_finding_count"] for row in dispositions),
        "scenario_attempts": len(dispositions),
        "unsafe_scenarios": sum(row["status"] == "unsafe_scenario" for row in dispositions),
    }


def _assert_expected_counts(counts: dict[str, int]) -> None:
    expected = {
        "generated_scenarios": EXPECTED_GENERATED_SCENARIOS,
        "no_scenario": EXPECTED_NO_SCENARIO,
        "safe_scenarios": EXPECTED_SAFE_SCENARIOS,
        "safety_findings": EXPECTED_SAFETY_FINDINGS,
        "scenario_attempts": EXPECTED_SCENARIO_ATTEMPTS,
        "unsafe_scenarios": EXPECTED_UNSAFE_SCENARIOS,
    }
    if counts != expected:
        raise RecoveryError(f"scenario safety disposition counts changed: {counts} != {expected}")


def build_artifacts(
    *,
    classifier: Callable[[str], list[str]] | None = None,
    extractor: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    """Validate immutable upstream state and return every deterministic output."""

    _validate_upstream_source()
    evidence = _validate_upstream_evidence()
    if classifier is None or extractor is None:
        frozen_classifier, frozen_extractor = _load_upstream_functions()
        classifier = classifier or frozen_classifier
        extractor = extractor or frozen_extractor

    records = _inventory_records(evidence)
    inventory = {
        "closure": _inventory_closure(records),
        "counts": {
            "gold_patches": EXPECTED_SOLUTIONS,
            "model_patches": EXPECTED_SOLUTIONS,
            "scenario_finished_checkpoints": EXPECTED_SCENARIO_ATTEMPTS,
            "scenario_scripts": EXPECTED_GENERATED_SCENARIOS,
            "scenario_stage_files": 117,
            "scenario_started_checkpoints": EXPECTED_SCENARIO_ATTEMPTS,
            "solution_finished_checkpoints": EXPECTED_SOLVER_ATTEMPTS,
            "solution_stage_files": 207,
            "solution_started_checkpoints": EXPECTED_SOLVER_ATTEMPTS,
        },
        "experiment_id": EXPERIMENT_ID,
        "files": records,
        "schema_version": INVENTORY_SCHEMA,
        "upstream_runtime_manifest_path": _relative(UPSTREAM_RUNTIME_MANIFEST),
        "upstream_runtime_manifest_sha256": UPSTREAM_RUNTIME_MANIFEST_SHA256,
        "upstream_source_commit": UPSTREAM_SOURCE_COMMIT,
    }
    inventory_raw = canonical_json_bytes(inventory)

    dispositions, safe_payloads = _scenario_dispositions(
        evidence, classifier, extractor
    )
    counts = _expected_counts(dispositions)
    _assert_expected_counts(counts)
    disposition = {
        "classifier": {
            "function": "scenario_ast_errors",
            "path": _relative(UPSTREAM_CLASSIFIER),
            "policy": "zero findings is safe_scenario; one or more findings is unsafe_scenario; no exceptions",
            "sha256": UPSTREAM_CLASSIFIER_SHA256,
        },
        "counts": counts,
        "dispositions": dispositions,
        "experiment_id": EXPERIMENT_ID,
        "schema_version": DISPOSITION_SCHEMA,
        "upstream_inventory_sha256": sha256(inventory_raw),
        "upstream_runtime_manifest_sha256": UPSTREAM_RUNTIME_MANIFEST_SHA256,
        "upstream_source_commit": UPSTREAM_SOURCE_COMMIT,
    }
    disposition_raw = canonical_json_bytes(disposition)

    by_disposition = {row["instance_id"]: row for row in dispositions}
    projected_scenario_manifest: list[dict[str, Any]] = []
    for row in evidence["scenario_manifest"]:
        disposition_row = by_disposition[row["instance_id"]]
        if disposition_row["status"] == "safe_scenario":
            projected_scenario_manifest.append(row)
        elif disposition_row["status"] == "unsafe_scenario":
            projected_scenario_manifest.append(
                {
                    "instance_id": row["instance_id"],
                    "provider_attempt_id": row["provider_attempt_id"],
                    "provider_response_sha256": row["provider_response_sha256"],
                    "scenario_sha256": row["scenario_sha256"],
                    "status": "unsafe_scenario",
                }
            )
        else:
            projected_scenario_manifest.append(row)
    projected_scenario_summary = {
        "checkpoint_schema": evidence["scenario_summary"]["checkpoint_schema"],
        "differing_solutions": EXPECTED_SCENARIO_ATTEMPTS,
        "estimated_spend_usd": evidence["scenario_summary"]["estimated_spend_usd"],
        "experiment_id": EXPERIMENT_ID,
        "manifest": projected_scenario_manifest,
        "model": FROZEN_MODEL,
        "no_scenario": EXPECTED_NO_SCENARIO,
        "provider_calls": EXPECTED_SCENARIO_ATTEMPTS,
        "safe_scenarios": EXPECTED_SAFE_SCENARIOS,
        "scenario_disposition_sha256": sha256(disposition_raw),
        "scenarios": EXPECTED_SAFE_SCENARIOS,
        "schema_version": PROJECTED_SCENARIO_SCHEMA,
        "source_schema_version": SCENARIO_SUMMARY_SCHEMA,
        "unsafe_scenarios": EXPECTED_UNSAFE_SCENARIOS,
        "upstream_runtime_manifest_sha256": UPSTREAM_RUNTIME_MANIFEST_SHA256,
        "upstream_source_commit": UPSTREAM_SOURCE_COMMIT,
    }
    projected_scenario_summary_raw = canonical_json_bytes(projected_scenario_summary)

    safe_index_rows: list[dict[str, Any]] = []
    for disposition_row in dispositions:
        if disposition_row["status"] != "safe_scenario":
            continue
        iid = disposition_row["instance_id"]
        raw = safe_payloads[iid]
        safe_index_rows.append(
            {
                "bytes": len(raw),
                "instance_id": iid,
                "path": disposition_row["safe_copy_path"],
                "provider_attempt_id": disposition_row["provider_attempt_id"],
                "provider_response_sha256": disposition_row["provider_response_sha256"],
                "scenario_payload_sha256": disposition_row["scenario_payload_sha256"],
                "sequence": disposition_row["sequence"],
                "sha256": sha256(raw),
                "upstream_path": disposition_row["source_scenario_path"],
                "upstream_sha256": disposition_row["source_scenario_file_sha256"],
            }
        )
    safe_index = {
        "count": len(safe_index_rows),
        "experiment_id": EXPERIMENT_ID,
        "scenario_disposition_sha256": sha256(disposition_raw),
        "scenarios": safe_index_rows,
        "schema_version": SAFE_INDEX_SCHEMA,
        "upstream_inventory_sha256": sha256(inventory_raw),
        "upstream_runtime_manifest_sha256": UPSTREAM_RUNTIME_MANIFEST_SHA256,
        "upstream_source_commit": UPSTREAM_SOURCE_COMMIT,
    }

    solution_projection_rows: list[dict[str, Any]] = []
    solve_manifest_positions = {
        row["instance_id"]: index
        for index, row in enumerate(evidence["solve_summary"]["manifest"], 1)
    }
    solution_payloads: dict[str, bytes] = {}
    for row in evidence["solution_rows"]:
        iid = row["instance_id"]
        model_upstream = UPSTREAM_SOLUTIONS / f"{iid}.model.patch"
        gold_upstream = UPSTREAM_SOLUTIONS / f"{iid}.gold.patch"
        model_raw = _regular_bytes(model_upstream, "upstream model patch")
        gold_raw = _regular_bytes(gold_upstream, "upstream gold patch")
        model_path = PROJECTED_SOLUTIONS / model_upstream.name
        gold_path = PROJECTED_SOLUTIONS / gold_upstream.name
        solution_payloads[model_upstream.name] = model_raw
        solution_payloads[gold_upstream.name] = gold_raw
        solution_projection_rows.append(
            {
                "gold_bytes": len(gold_raw),
                "gold_path": _relative(gold_path),
                "gold_sha256": sha256(gold_raw),
                "instance_id": iid,
                "model_bytes": len(model_raw),
                "model_path": _relative(model_path),
                "model_sha256": sha256(model_raw),
                "provider_attempt_id": row["provider_attempt_id"],
                "provider_response_sha256": row["provider_response_sha256"],
                "target_sequence": solve_manifest_positions[iid],
                "upstream_gold_path": _relative(gold_upstream),
                "upstream_gold_sha256": sha256(gold_raw),
                "upstream_model_path": _relative(model_upstream),
                "upstream_model_sha256": sha256(model_raw),
            }
        )
    solve_summary_raw = _regular_bytes(
        UPSTREAM_SOLUTIONS / "solve_summary.json", "upstream solve summary"
    )
    solution_index = {
        "count": len(solution_projection_rows),
        "experiment_id": EXPERIMENT_ID,
        "schema_version": SOLUTION_INDEX_SCHEMA,
        "solutions": solution_projection_rows,
        "solve_summary_path": _relative(PROJECTED_SOLUTIONS / "solve_summary.json"),
        "solve_summary_sha256": sha256(solve_summary_raw),
        "upstream_inventory_sha256": sha256(inventory_raw),
        "upstream_runtime_manifest_sha256": UPSTREAM_RUNTIME_MANIFEST_SHA256,
        "upstream_source_commit": UPSTREAM_SOURCE_COMMIT,
    }

    return {
        "bridge_documents": {
            "safe_scenario_index.json": safe_index,
            "scenario_disposition.json": disposition,
            "solution_projection_index.json": solution_index,
            "upstream_inventory.json": inventory,
        },
        "projected_scenario_summary": projected_scenario_summary,
        "projected_scenario_summary_raw": projected_scenario_summary_raw,
        "safe_payloads": safe_payloads,
        "solution_payloads": solution_payloads,
        "solve_summary_raw": solve_summary_raw,
    }


def _require_directory(path: Path, label: str) -> None:
    descriptor = _open_directory_nofollow(path, label)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISDIR(metadata.st_mode):
            raise RecoveryError(f"{label} is missing, non-directory, or symlinked: {path}")
    finally:
        os.close(descriptor)


def _reject_existing_extras(directory: Path, allowed: set[str], label: str) -> None:
    if not directory.exists():
        return
    _require_directory(directory, label)
    actual = {path.name for path in directory.iterdir()}
    extras = sorted(actual - allowed)
    if extras:
        raise RecoveryError(f"{label} contains unexpected entries: {extras}")
    for path in directory.iterdir():
        if path.is_symlink() or (path.name in allowed and not path.is_file()):
            raise RecoveryError(f"{label} contains a non-regular or symlinked artifact: {path}")


def _mkdir_regular(path: Path) -> None:
    if path.exists():
        _require_directory(path, "output directory")
        return
    path.mkdir(parents=True, exist_ok=False)
    _require_directory(path, "output directory")


def _atomic_write(path: Path, raw: bytes) -> None:
    if path.exists() and (path.is_symlink() or not path.is_file()):
        raise RecoveryError(f"refusing to replace non-regular output: {path}")
    _mkdir_regular(path.parent)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _output_expectations(bundle: dict[str, Any]) -> dict[Path, bytes]:
    expected: dict[Path, bytes] = {}
    for filename, document in bundle["bridge_documents"].items():
        expected[BRIDGE / filename] = canonical_json_bytes(document)
    expected[PROJECTED_SOLUTIONS / "solve_summary.json"] = bundle["solve_summary_raw"]
    for filename, raw in bundle["solution_payloads"].items():
        expected[PROJECTED_SOLUTIONS / filename] = raw
    expected[PROJECTED_SCENARIOS / "scenarios_summary.json"] = bundle[
        "projected_scenario_summary_raw"
    ]
    for iid, raw in bundle["safe_payloads"].items():
        expected[PROJECTED_SCENARIOS / f"{iid}.scenario.py"] = raw
    return expected


def write_artifacts(bundle: dict[str, Any]) -> None:
    expected = _output_expectations(bundle)
    _reject_existing_extras(BRIDGE, BRIDGE_FILENAMES, "iter203 bridge directory")
    _reject_existing_extras(
        PROJECTED_SOLUTIONS,
        {path.name for path in expected if path.parent == PROJECTED_SOLUTIONS},
        "iter203 projected solution directory",
    )
    _reject_existing_extras(
        PROJECTED_SCENARIOS,
        {path.name for path in expected if path.parent == PROJECTED_SCENARIOS},
        "iter203 projected scenario directory",
    )
    for path, raw in sorted(expected.items(), key=lambda item: str(item[0])):
        _atomic_write(path, raw)
    check_artifacts(bundle)


def check_artifacts(bundle: dict[str, Any]) -> None:
    expected = _output_expectations(bundle)
    for directory, allowed, label in (
        (BRIDGE, BRIDGE_FILENAMES, "iter203 bridge directory"),
        (
            PROJECTED_SOLUTIONS,
            {path.name for path in expected if path.parent == PROJECTED_SOLUTIONS},
            "iter203 projected solution directory",
        ),
        (
            PROJECTED_SCENARIOS,
            {path.name for path in expected if path.parent == PROJECTED_SCENARIOS},
            "iter203 projected scenario directory",
        ),
    ):
        _require_directory(directory, label)
        actual = {path.name for path in directory.iterdir()}
        if actual != allowed:
            raise RecoveryError(
                f"{label} file set mismatch: missing={sorted(allowed - actual)} "
                f"extra={sorted(actual - allowed)}"
            )
    for path, raw in expected.items():
        if _regular_bytes(path, "iter203 bridge projection") != raw:
            raise RecoveryError(f"iter203 bridge output drift: {path}")

    # Parse every generated JSON strictly after exact-byte comparison.
    for path in (
        UPSTREAM_INVENTORY,
        SCENARIO_DISPOSITION,
        SAFE_SCENARIO_INDEX,
        SOLUTION_PROJECTION_INDEX,
        PROJECTED_SCENARIOS / "scenarios_summary.json",
        PROJECTED_SOLUTIONS / "solve_summary.json",
    ):
        load_json_strict(path)

    disposition = bundle["bridge_documents"]["scenario_disposition.json"]
    unsafe_names = {
        f"{row['instance_id']}.scenario.py"
        for row in disposition["dispositions"]
        if row["status"] == "unsafe_scenario"
    }
    projected_names = {path.name for path in PROJECTED_SCENARIOS.glob("*.scenario.py")}
    if unsafe_names & projected_names:
        raise RecoveryError("unsafe scenario bytes entered the iter203 execution projection")


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    try:
        bundle = build_artifacts()
        if arguments.write:
            write_artifacts(bundle)
            action = "wrote and verified"
        else:
            check_artifacts(bundle)
            action = "verified"
    except RecoveryError as exc:
        print(f"iter203 safety recovery error: {exc}", file=sys.stderr)
        return 1
    counts = bundle["bridge_documents"]["scenario_disposition.json"]["counts"]
    print(
        f"iter203 safety recovery {action}: "
        f"{counts['safe_scenarios']} safe, {counts['unsafe_scenarios']} unsafe, "
        f"{counts['no_scenario']} absent, {counts['safety_findings']} findings"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
