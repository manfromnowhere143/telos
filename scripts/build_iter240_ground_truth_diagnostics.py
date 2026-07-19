#!/usr/bin/env python3
"""Build the hardened post-freeze iter240 diagnostic evidence.

This instrument is deliberately downstream of the immutable selection commit
``46468639088509c65ab06af5d839b7d3a52722b5``.  It never re-freezes or edits
the selector.  It first proves that the selector, census, receipt, ancestry,
and source blobs are still the exact registered Git objects, then performs the
retrospective diagnostic reconstruction.

The frozen predecessor builder is used only for its byte-bound experiment
parsers.  Its mutable legacy ``preflight`` and ``build_all`` controls are
runtime-tripwired and never invoked; V2 derives its control boundary directly
from raw pinned commit headers.

No network, provider, model, container, GPU, target execution, adjudication,
human contact, or spending operation is reachable from this module.
"""

from __future__ import annotations

import argparse
import copy
from collections import Counter
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ITERATION = Path("experiments/iter240_ground_truth_admission_design")
PROOF = ITERATION / "proof"

PREDECESSOR = "b597b763f2eb52b2f4f2d36e7daaa31654be076b"
PREDECESSOR_TREE = "776f60e7c75616767ce6bb1e45a3eb7279f37a97"
PREDECESSOR_PARENTS = (
    "fb87af7eb15b5235a722a7bb3fd3a48962019188",
    "56fb78f5f8afcd8709fde1170e8422072626f367",
)
AUTHORIZATION = "cf809ac0e06f37127553e99a2ab9b0705f8e2fae"
AUTHORIZATION_TREE = "4e9b510907aef19219ba9ea217ca3cd6f618836b"
ACTIVATION = "63f5786b9b5c60d2bea90f2077208cfb745c31a2"
ACTIVATION_TREE = "351bf81beaf18686fb1dd89770b8f428d61962c4"
SELECTION_COMMIT = "46468639088509c65ab06af5d839b7d3a52722b5"
SELECTION_TREE = "957876c597b687babe4e9e21c1567d420e0f0fa5"
EXPECTED_SOURCE_BLOB_COUNT = 163

FRESH_RUNS = (
    "iter224_natural_rate_scale_n",
    "iter228_fresh_diverse_cohort",
)

FROZEN_BUILDER = Path("scripts/build_iter240_ground_truth_admission.py")
INDEPENDENT_VALIDATOR = Path("scripts/validate_iter240_ground_truth_diagnostics.py")
SELECTION_CENSUS = PROOF / "selection_census.json"
SELECTION_RECEIPT = PROOF / "selection_freeze_receipt.json"
ROLE_POLICY = PROOF / "role_view_policy.json"

OUTPUTS = {
    "missingness_manifest": PROOF / "missingness_manifest_v2.json",
    "availability_taxonomy": PROOF / "availability_taxonomy_v2.json",
    "ground_truth_frame": PROOF / "ground_truth_frame_v2.json",
    "decision_curves": PROOF / "decision_curves_v2.json",
}
RECEIPT = PROOF / "materialization_receipt_v2.json"

SUPERSEDES = {
    "authority": "post_freeze_v2_only",
    "reason": (
        "The unversioned v1 diagnostic layer did not pin the temporal selection "
        "commit, encoded unmeasured arms as false, and lacked independent field "
        "reconstruction. Only these post-freeze v2 artifacts are diagnostic authority."
    ),
    "superseded_paths": [
        (PROOF / "availability_taxonomy.json").as_posix(),
        (PROOF / "decision_curves.json").as_posix(),
        (PROOF / "ground_truth_frame.json").as_posix(),
        (PROOF / "materialization_receipt.json").as_posix(),
        (PROOF / "missingness_manifest.json").as_posix(),
    ],
}

MAX_SCENARIO_SECTION_BYTES = 65_536
MAX_RESULT_PAYLOAD_BYTES = 16_384
IMAGE_ID_RE = re.compile(r"^IMAGE_ID=(sha256:[0-9a-f]{64})$")
IMAGE_DIGEST_RE = re.compile(
    r"^IMAGE_REPO_DIGEST=([^\s@:]+(?:/[^\s@:]+)*@sha256:[0-9a-f]{64})$"
)
RESULT_RE = re.compile(r"^RESULT=(.+)$")
EXIT_RE = re.compile(r"^SCENARIO_EXIT=(-?[0-9]+)$")
EXCEPTION_RE = re.compile(
    r"(?:^|[\s.:])(?:[A-Za-z_][A-Za-z0-9_.]*"
    r"(?:Error|Exception))(?::|\s|$)"
)
WHOLE_FILE_FAILURE_MARKERS = (
    "APPLY_FAILED",
    "SETUP_FAILED",
    "CERT_TIMEOUT",
    "CERT_TRUNCATED",
    "SCENARIO_TIMEOUT",
    "EXECUTION_TIMEOUT",
    "SCENARIO_TRUNCATED",
    "EXECUTION_TRUNCATED",
    "LOG_TRUNCATED",
)


class DiagnosticError(ValueError):
    """A retained or derived byte violates the registered diagnostic contract."""


def _diagnostic_builder_boundary() -> dict[str, Any]:
    return {
        "legacy_build_all_invoked": False,
        "legacy_build_all_tripwire_installed": True,
        "legacy_preflight_invoked": False,
        "legacy_preflight_tripwire_installed": True,
        "mutable_seal_registry_read": False,
        "selected_rows_loaded_from_commit": SELECTION_COMMIT,
        "source_boundary_derivation": "raw_pinned_commit_headers",
    }


def _forbidden_legacy_control(*_args: Any, **_kwargs: Any) -> None:
    raise DiagnosticError(
        "mutable legacy build_all/preflight control is forbidden in V2 diagnostics"
    )


def _git_environment() -> dict[str, str]:
    env = os.environ.copy()
    for key in tuple(env):
        if key.startswith("GIT_"):
            env.pop(key)
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def _git(*args: str) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        env=_git_environment(),
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise DiagnosticError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    try:
        text = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise DiagnosticError(f"value is not canonical JSON: {exc}") from exc
    return (text + "\n").encode("utf-8")


def _reject_constant(token: str) -> None:
    raise DiagnosticError(f"non-finite JSON number is forbidden: {token}")


def _pairs_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DiagnosticError(f"duplicate JSON key is forbidden: {key!r}")
        result[key] = value
    return result


def _strict_json(data: bytes, *, source: str) -> Any:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DiagnosticError(f"{source}: JSON is not UTF-8") from exc
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs_object,
            parse_constant=_reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise DiagnosticError(f"{source}: malformed JSON: {exc}") from exc


def _relative(path: str | Path) -> Path:
    value = Path(path)
    if value.is_absolute() or value == Path(".") or ".." in value.parts:
        raise DiagnosticError(f"path is not repository-relative: {path}")
    return value


def _worktree_regular_bytes(path: str | Path) -> bytes:
    relative = _relative(path)
    cursor = ROOT
    for index, part in enumerate(relative.parts):
        cursor /= part
        try:
            metadata = cursor.lstat()
        except OSError as exc:
            raise DiagnosticError(f"missing worktree artifact: {relative}") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise DiagnosticError(f"symlink is forbidden in artifact path: {relative}")
        if index < len(relative.parts) - 1 and not stat.S_ISDIR(metadata.st_mode):
            raise DiagnosticError(f"non-directory ancestor in artifact path: {relative}")
    if not stat.S_ISREG(cursor.lstat().st_mode):
        raise DiagnosticError(f"artifact is not a regular file: {relative}")
    return cursor.read_bytes()


def _tree_record(
    reference: str,
    path: str | Path,
    *,
    require_present: bool = True,
) -> dict[str, Any] | None:
    relative = _relative(path)
    listing = _git(
        "ls-tree", "-z", reference, "--", relative.as_posix()
    )
    entries = [entry for entry in listing.split(b"\0") if entry]
    if not entries:
        if require_present:
            raise DiagnosticError(f"{relative}: absent at {reference}")
        return None
    if len(entries) != 1:
        raise DiagnosticError(f"{relative}: ambiguous tree entry at {reference}")
    try:
        prefix, listed_path = entries[0].split(b"\t", 1)
        mode, kind, oid = prefix.decode("ascii").split(" ")
        decoded_path = listed_path.decode("utf-8")
    except (ValueError, UnicodeError) as exc:
        raise DiagnosticError(f"{relative}: malformed Git tree entry") from exc
    if (
        decoded_path != relative.as_posix()
        or kind != "blob"
        or mode not in {"100644", "100755"}
    ):
        raise DiagnosticError(f"{relative}: not the expected regular Git blob")
    data = _git("cat-file", "blob", oid)
    return {
        "byte_count": len(data),
        "git_blob_oid": oid,
        "git_mode": mode,
        "path": relative.as_posix(),
        "reference_commit": reference,
        "sha256_file_bytes": _sha256(data),
    }


def _reject_history_overlays() -> None:
    for git_path in ("info/grafts", "shallow"):
        rendered = _git("rev-parse", "--git-path", git_path).decode("utf-8").strip()
        path = Path(rendered)
        if not path.is_absolute():
            path = ROOT / path
        if not os.path.lexists(path):
            continue
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise DiagnosticError(f"Git history overlay path is not regular: {git_path}")
        if metadata.st_size:
            raise DiagnosticError(f"nonempty Git history overlay is forbidden: {git_path}")


def _raw_commit_identity(reference: str) -> tuple[str, list[str]]:
    raw = _git("cat-file", "commit", reference)
    header, separator, _ = raw.partition(b"\n\n")
    if not separator:
        raise DiagnosticError(f"{reference}: malformed raw commit object")
    trees: list[str] = []
    parents: list[str] = []
    for line in header.splitlines():
        if line.startswith(b"tree "):
            trees.append(line[5:].decode("ascii"))
        elif line.startswith(b"parent "):
            parents.append(line[7:].decode("ascii"))
    if len(trees) != 1:
        raise DiagnosticError(f"{reference}: raw commit has {len(trees)} tree headers")
    return trees[0], parents


def _record_and_bytes(
    reference: str,
    path: str | Path,
    *,
    require_head_equal: bool,
    require_worktree_equal: bool,
) -> tuple[dict[str, Any], bytes]:
    record = _tree_record(reference, path)
    assert record is not None
    relative = _relative(path)
    data = _git("cat-file", "blob", record["git_blob_oid"])
    if require_head_equal:
        head = _tree_record("HEAD", relative)
        assert head is not None
        comparable = ("git_blob_oid", "git_mode", "path", "sha256_file_bytes")
        if any(head[key] != record[key] for key in comparable):
            raise DiagnosticError(f"{relative}: HEAD differs from {reference}")
    if require_worktree_equal and _worktree_regular_bytes(relative) != data:
        raise DiagnosticError(f"{relative}: worktree differs from {reference}")
    return record, data


def _verify_selection_authority() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    dict[str, Any],
]:
    _reject_history_overlays()
    if _git("replace", "-l").strip():
        raise DiagnosticError("Git replacement refs are forbidden")
    predecessor_tree, predecessor_parents = _raw_commit_identity(PREDECESSOR)
    authorization_tree, authorization_parents = _raw_commit_identity(AUTHORIZATION)
    activation_tree, activation_parents = _raw_commit_identity(ACTIVATION)
    selection_tree, selection_parents = _raw_commit_identity(SELECTION_COMMIT)
    if (
        predecessor_tree != PREDECESSOR_TREE
        or predecessor_parents != list(PREDECESSOR_PARENTS)
    ):
        raise DiagnosticError("merged predecessor raw commit identity changed")
    if authorization_parents != [PREDECESSOR]:
        raise DiagnosticError("authorization raw parent changed")
    if activation_parents != [AUTHORIZATION]:
        raise DiagnosticError("activation raw parent changed")
    if selection_parents != [ACTIVATION]:
        raise DiagnosticError("frozen selection commit parent changed")
    if authorization_tree != AUTHORIZATION_TREE:
        raise DiagnosticError("authorization raw tree changed")
    if activation_tree != ACTIVATION_TREE:
        raise DiagnosticError("activation raw tree changed")
    if selection_tree != SELECTION_TREE:
        raise DiagnosticError("frozen selection tree changed")
    try:
        subprocess.run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                SELECTION_COMMIT,
                "HEAD",
            ],
            cwd=ROOT,
            env=_git_environment(),
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise DiagnosticError("HEAD does not descend from the frozen selection") from exc

    frozen: dict[str, dict[str, Any]] = {}
    frozen_bytes: dict[str, bytes] = {}
    for name, path in (
        ("selector_builder", FROZEN_BUILDER),
        ("selection_census", SELECTION_CENSUS),
        ("selection_receipt", SELECTION_RECEIPT),
    ):
        record, data = _record_and_bytes(
            SELECTION_COMMIT,
            path,
            require_head_equal=True,
            require_worktree_equal=True,
        )
        frozen[name] = record
        frozen_bytes[name] = data

    receipt = _strict_json(
        frozen_bytes["selection_receipt"], source=SELECTION_RECEIPT.as_posix()
    )
    census = _strict_json(
        frozen_bytes["selection_census"], source=SELECTION_CENSUS.as_posix()
    )
    if not isinstance(receipt, dict) or not isinstance(census, dict):
        raise DiagnosticError("frozen selection artifacts must be JSON objects")
    if (
        receipt.get("builder_path") != FROZEN_BUILDER.as_posix()
        or receipt.get("builder_sha256")
        != frozen["selector_builder"]["sha256_file_bytes"]
        or receipt.get("selection_census", {}).get("sha256_file_bytes")
        != frozen["selection_census"]["sha256_file_bytes"]
        or receipt.get("selection_census", {}).get("byte_count")
        != frozen["selection_census"]["byte_count"]
        or receipt.get("source_reference_commit") != PREDECESSOR
    ):
        raise DiagnosticError("selection receipt does not bind the frozen artifacts")
    rows = census.get("selected_rows")
    if (
        census.get("selected_count") != 13
        or census.get("unique_task_count") != 13
        or not isinstance(rows, list)
        or len(rows) != 13
        or len(
            {
                (row.get("source_run"), row.get("instance_id"))
                for row in rows
                if isinstance(row, dict)
            }
        )
        != 13
    ):
        raise DiagnosticError("frozen census is not the registered 13-row census")

    source_records = receipt.get("source_inputs")
    if not isinstance(source_records, list) or len(source_records) != 2:
        raise DiagnosticError("selection receipt source ledger changed")
    for retained in source_records:
        if not isinstance(retained, dict):
            raise DiagnosticError("selection receipt source record is malformed")
        actual, _ = _record_and_bytes(
            PREDECESSOR,
            retained.get("path", ""),
            require_head_equal=True,
            require_worktree_equal=True,
        )
        for key in (
            "byte_count",
            "git_blob_oid",
            "git_mode",
            "path",
            "reference_commit",
            "sha256_file_bytes",
        ):
            if retained.get(key) != actual[key]:
                raise DiagnosticError(
                    f"selection source {retained.get('path')}: {key} drift"
                )

    authority = {
        "frozen_artifacts": frozen,
        "predecessor_commit": PREDECESSOR,
        "selection_commit": SELECTION_COMMIT,
        "selection_parent": ACTIVATION,
        "selection_tree": SELECTION_TREE,
    }
    immutable_source_boundary = {
        "commits": {
            "activation": {
                "commit": ACTIVATION,
                "parents": [AUTHORIZATION],
                "tree": ACTIVATION_TREE,
            },
            "authorization": {
                "commit": AUTHORIZATION,
                "parents": [PREDECESSOR],
                "tree": AUTHORIZATION_TREE,
            },
            "predecessor": {
                "commit": PREDECESSOR,
                "parents": list(PREDECESSOR_PARENTS),
                "tree": PREDECESSOR_TREE,
            },
            "selection": {
                "commit": SELECTION_COMMIT,
                "parents": [ACTIVATION],
                "tree": SELECTION_TREE,
            },
        },
        "derivation": "raw_git_commit_headers",
        "history_overlay_policy": (
            "replacement refs disabled and rejected; nonempty graft and shallow "
            "history files rejected; inherited Git configuration disabled"
        ),
        "source_artifact_policy": (
            "named regular nonsymlink Git blobs; HEAD and worktree bytes must equal "
            "the exact merged predecessor blob"
        ),
        "source_blob_count": EXPECTED_SOURCE_BLOB_COUNT,
    }
    return authority, copy.deepcopy(rows), immutable_source_boundary


def _load_frozen_builder() -> ModuleType:
    specification = importlib.util.spec_from_file_location(
        "_telos_iter240_frozen_admission", ROOT / FROZEN_BUILDER
    )
    if specification is None or specification.loader is None:
        raise DiagnosticError("cannot load the frozen admission builder")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _verify_source_ledger(records: list[dict[str, Any]]) -> None:
    if len(records) != EXPECTED_SOURCE_BLOB_COUNT:
        raise DiagnosticError(
            f"diagnostic source ledger has {len(records)} blobs; "
            f"expected {EXPECTED_SOURCE_BLOB_COUNT}"
        )
    paths: set[str] = set()
    for retained in records:
        path = retained.get("path")
        if not isinstance(path, str) or path in paths:
            raise DiagnosticError("diagnostic source ledger path is missing or duplicate")
        paths.add(path)
        actual, _ = _record_and_bytes(
            PREDECESSOR,
            path,
            require_head_equal=True,
            require_worktree_equal=True,
        )
        for key in (
            "byte_count",
            "git_blob_oid",
            "git_mode",
            "path",
            "reference_commit",
            "sha256_file_bytes",
        ):
            if retained.get(key) != actual[key]:
                raise DiagnosticError(f"{path}: source ledger {key} drift")


def _read_predecessor(path: str | Path) -> bytes:
    _, data = _record_and_bytes(
        PREDECESSOR,
        path,
        require_head_equal=True,
        require_worktree_equal=True,
    )
    return data


def _image_provenance(text: str, *, source: str) -> dict[str, str]:
    lines = text.splitlines()
    ids = [
        match.group(1)
        for line in lines
        if (match := IMAGE_ID_RE.fullmatch(line)) is not None
    ]
    digests = [
        match.group(1)
        for line in lines
        if (match := IMAGE_DIGEST_RE.fullmatch(line)) is not None
    ]
    raw_ids = [line for line in lines if line.startswith("IMAGE_ID=")]
    raw_digests = [line for line in lines if line.startswith("IMAGE_REPO_DIGEST=")]
    if not (
        len(ids) == len(digests) == len(raw_ids) == len(raw_digests) == 1
    ):
        raise DiagnosticError(f"{source}: malformed or ambiguous immutable image")
    if ":latest@" in digests[0] or digests[0].split("@", 1)[0].endswith(":latest"):
        raise DiagnosticError(f"{source}: mutable :latest is not an image identity")
    return {"image_id": ids[0], "image_repository_digest": digests[0]}


def _whole_file_failures(lines: list[str]) -> list[str]:
    found: set[str] = set()
    for line in lines:
        for marker in WHOLE_FILE_FAILURE_MARKERS:
            if line == marker or line.startswith(f"{marker} ") or line.startswith(
                f"{marker}="
            ):
                found.add(marker)
    return sorted(found)


def _bounded_scenario_body(lines: list[str]) -> tuple[list[str] | None, list[str]]:
    starts = [index for index, line in enumerate(lines) if line == ">>>>> Scenario Start"]
    ends = [index for index, line in enumerate(lines) if line == ">>>>> Scenario End"]
    problems: list[str] = []
    if len(starts) != 1 or len(ends) != 1:
        problems.append("missing_or_ambiguous_scenario_section")
        return None, problems
    if starts[0] >= ends[0]:
        problems.append("misordered_scenario_section")
        return None, problems
    body = lines[starts[0] + 1 : ends[0]]
    if len("\n".join(body).encode("utf-8")) > MAX_SCENARIO_SECTION_BYTES:
        problems.append("scenario_section_too_large")
    return body, problems


def _section_sentinels(body: list[str]) -> list[str]:
    text = "\n".join(body)
    found: set[str] = set()
    lowered = text.casefold()
    if "traceback (most recent call last):" in lowered:
        found.add("traceback")
    if EXCEPTION_RE.search(text):
        found.add("exception_or_error")
    if "timeout" in lowered or "timed out" in lowered:
        found.add("timeout")
    if "truncat" in lowered:
        found.add("truncation")
    if re.search(r"(?:^|\W)killed(?:\W|$)", lowered):
        found.add("killed")
    return sorted(found)


def _diagnose_evaluated_arm(
    text: str,
    arm: str,
    *,
    source: str,
) -> dict[str, Any]:
    lines = text.splitlines()
    provenance = _image_provenance(text, source=source)
    apply_ok = lines.count(f"APPLY_OK {arm}") == 1
    whole_failures = _whole_file_failures(lines)
    body, section_problems = _bounded_scenario_body(lines)

    exit_code: int | None = None
    exit_marker_count = 0
    result_count = 0
    result_like_count = 0
    result_byte_count: int | None = None
    result_payload_sha256: str | None = None
    section_byte_count: int | None = None
    section_sentinels: list[str] = []
    if body is not None:
        section_byte_count = len("\n".join(body).encode("utf-8"))
        section_sentinels = _section_sentinels(body)
        exit_matches = [
            match for line in body if (match := EXIT_RE.fullmatch(line)) is not None
        ]
        exit_marker_count = len(
            [line for line in body if line.startswith("SCENARIO_EXIT")]
        )
        if len(exit_matches) == 1 and exit_marker_count == 1:
            exit_code = int(exit_matches[0].group(1))
        result_like = [line for line in body if line.startswith("RESULT")]
        exact_results = [
            match for line in body if (match := RESULT_RE.fullmatch(line)) is not None
        ]
        result_like_count = len(result_like)
        result_count = len(exact_results)
        if len(exact_results) == 1 and result_like_count == 1:
            payload = exact_results[0].group(1).encode("utf-8")
            result_byte_count = len(payload)
            result_payload_sha256 = _sha256(payload)

    valid = (
        apply_ok
        and not whole_failures
        and not section_problems
        and not section_sentinels
        and exit_marker_count == 1
        and exit_code == 0
        and result_count == 1
        and result_like_count == 1
        and result_byte_count is not None
        and 0 < result_byte_count <= MAX_RESULT_PAYLOAD_BYTES
    )
    return {
        **provenance,
        "apply_ok": apply_ok,
        "exit_code": exit_code,
        "exit_marker_count": exit_marker_count,
        "result_byte_count": result_byte_count,
        "result_count": result_count,
        "result_like_line_count": result_like_count,
        "result_payload_sha256": result_payload_sha256,
        "scenario_section_byte_count": section_byte_count,
        "section_contract_failures": sorted(section_problems),
        "section_error_sentinels": section_sentinels,
        "valid": valid,
        "validity_state": "valid" if valid else "invalid",
        "whole_file_failure_sentinels": whole_failures,
    }


def _not_evaluated_arm(
    text: str,
    *,
    source: str,
    reason: str,
) -> dict[str, Any]:
    return {
        **_image_provenance(text, source=source),
        "apply_ok": None,
        "exit_code": None,
        "exit_marker_count": None,
        "not_evaluated_reason": reason,
        "result_byte_count": None,
        "result_count": None,
        "result_like_line_count": None,
        "result_payload_sha256": None,
        "scenario_section_byte_count": None,
        "section_contract_failures": None,
        "section_error_sentinels": None,
        "valid": None,
        "validity_state": "not_evaluated",
        "whole_file_failure_sentinels": None,
    }


def _scenario_row(path: Path, pointer: str, *, instance_id: str) -> dict[str, Any]:
    match = re.fullmatch(r"/manifest/([0-9]+)", pointer)
    if match is None:
        raise DiagnosticError(f"{path}: unsupported scenario JSON pointer {pointer}")
    document = _strict_json(_read_predecessor(path), source=path.as_posix())
    if not isinstance(document, dict) or not isinstance(document.get("manifest"), list):
        raise DiagnosticError(f"{path}: malformed scenario summary")
    index = int(match.group(1))
    rows = document["manifest"]
    if index >= len(rows) or not isinstance(rows[index], dict):
        raise DiagnosticError(f"{path}: scenario pointer is out of bounds")
    row = rows[index]
    if row.get("instance_id") != instance_id:
        raise DiagnosticError(f"{path}: scenario pointer identity mismatch")
    return row


def _absence_proof(path: Path) -> dict[str, Any]:
    relative = _relative(path)
    cursor = ROOT
    for part in relative.parts[:-1]:
        cursor /= part
        try:
            metadata = cursor.lstat()
        except OSError as exc:
            raise DiagnosticError(
                f"{relative}: missing ancestor prevents worktree absence proof"
            ) from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise DiagnosticError(
                f"{relative}: unsafe ancestor prevents worktree absence proof"
            )
    if _tree_record(PREDECESSOR, path, require_present=False) is not None:
        raise DiagnosticError(f"{path}: supposedly absent scenario exists at predecessor")
    if _tree_record("HEAD", path, require_present=False) is not None:
        raise DiagnosticError(f"{path}: supposedly absent scenario exists at HEAD")
    if os.path.lexists(ROOT / path):
        raise DiagnosticError(f"{path}: supposedly absent scenario exists in worktree")
    return {
        "head_tree_entry": "absent",
        "path": path.as_posix(),
        "predecessor_commit": PREDECESSOR,
        "predecessor_tree_entry": "absent",
        "worktree_entry": "absent",
    }


def _build_taxonomy_v2(
    legacy_manifest: dict[str, Any],
    legacy_taxonomy: dict[str, Any],
    authority: dict[str, Any],
    immutable_source_boundary: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = copy.deepcopy(legacy_manifest)
    manifest["diagnostic_builder_boundary"] = _diagnostic_builder_boundary()
    manifest["immutable_source_boundary"] = immutable_source_boundary
    manifest["schema_version"] = "telos.iter240.missingness_manifest.v2"
    manifest["selection_authority"] = authority
    manifest["supersedes"] = SUPERSEDES
    manifest["diagnostic_validity_contract"] = {
        "max_result_payload_bytes": MAX_RESULT_PAYLOAD_BYTES,
        "max_scenario_section_bytes": MAX_SCENARIO_SECTION_BYTES,
        "result_grammar": "^RESULT=(.+)$",
        "unmeasured_arm_encoding": {
            "valid": None,
            "validity_state": "not_evaluated",
        },
    }

    manifest_by_key = {
        (row["source_run"], row["instance_id"]): row
        for row in manifest["selected_rows"]
    }
    rebuilt_rows: list[dict[str, Any]] = []
    for retained in legacy_taxonomy["rows"]:
        row = copy.deepcopy(retained)
        key = (row["source_run"], row["instance_id"])
        manifest_row = manifest_by_key.get(key)
        if manifest_row is None:
            raise DiagnosticError(f"taxonomy row is absent from manifest: {key}")
        pointer = row["scenario_pointer"]
        path = Path(pointer["path"])
        scenario = _scenario_row(
            path,
            pointer["json_pointer"],
            instance_id=row["instance_id"],
        )
        scenario_status = scenario.get("status")
        if scenario_status not in {"scenario", "excluded_unsafe", "no_scenario"}:
            raise DiagnosticError(f"{key}: unsupported scenario status {scenario_status!r}")

        artifacts = manifest_row["artifacts"]
        candidate_path = Path(artifacts["candidate_execution_log"]["path"])
        accepted_path = Path(artifacts["gold_execution_log"]["path"])
        candidate_text = _read_predecessor(candidate_path).decode("utf-8")
        accepted_text = _read_predecessor(accepted_path).decode("utf-8")
        scenario_path = (
            Path("experiments")
            / row["source_run"]
            / "proof/raw/scenarios"
            / f"{row['instance_id']}.scenario.py"
        )

        if scenario_status == "scenario":
            if "historical_scenario" not in artifacts:
                raise DiagnosticError(f"{key}: scenario artifact is missing")
            candidate = _diagnose_evaluated_arm(
                candidate_text,
                "variant",
                source=candidate_path.as_posix(),
            )
            accepted = _diagnose_evaluated_arm(
                accepted_text,
                "gold",
                source=accepted_path.as_posix(),
            )
            if (
                candidate["image_id"] != accepted["image_id"]
                or candidate["image_repository_digest"]
                != accepted["image_repository_digest"]
            ):
                raise DiagnosticError(f"{key}: scenario arms use different images")
            absence = None
            if candidate["valid"] and accepted["valid"]:
                availability = (
                    "paired_valid_judged"
                    if row["retained_blind_verdict_count"]
                    else "paired_valid_unjudged"
                )
            elif not candidate["valid"] and not accepted["valid"]:
                availability = "paired_invalid_both_arms"
            elif not candidate["valid"] and accepted["valid"]:
                availability = "paired_invalid_candidate_only"
            else:
                availability = "source_inconsistent"
        else:
            absence = _absence_proof(scenario_path)
            candidate = _not_evaluated_arm(
                candidate_text,
                source=candidate_path.as_posix(),
                reason=scenario_status,
            )
            accepted = _not_evaluated_arm(
                accepted_text,
                source=accepted_path.as_posix(),
                reason=scenario_status,
            )
            availability = scenario_status

        row["arm_summaries"] = {
            "accepted": accepted,
            "candidate": candidate,
        }
        row["availability_state"] = availability
        row.pop("historical_outcome_exposed", None)
        row["diagnostic_state_exposed"] = True
        row["historical_scenario_outcome_exposed"] = scenario_status == "scenario"
        row["future_primary_endpoint_eligible"] = False
        row["scenario_absence_proof"] = absence
        row["scenario_status"] = scenario_status
        rebuilt_rows.append(row)

    counts = dict(
        sorted(Counter(row["availability_state"] for row in rebuilt_rows).items())
    )
    expected = {
        "excluded_unsafe": 7,
        "no_scenario": 1,
        "paired_invalid_both_arms": 3,
        "paired_invalid_candidate_only": 2,
    }
    if counts != expected:
        raise DiagnosticError(f"v2 taxonomy contradicts the frozen disclosure: {counts}")
    if any(
        row["arm_summaries"][arm]["validity_state"] == "not_evaluated"
        and row["arm_summaries"][arm]["valid"] is not None
        for row in rebuilt_rows
        for arm in ("accepted", "candidate")
    ):
        raise DiagnosticError("an unmeasured arm was converted into a boolean")

    taxonomy = {
        "availability_counts": counts,
        "claim_boundary": (
            "Retrospective availability diagnosis only. Absence and exceptions remain "
            "unresolved; historical exposed scenarios cannot be future primary endpoints."
        ),
        "future_primary_endpoint_rows": 0,
        "paired_valid_rows": 0,
        "retained_evidence_recovery": "blocked",
        "rows": rebuilt_rows,
        "schema_version": "telos.iter240.availability_taxonomy.v2",
        "selected_count": len(rebuilt_rows),
        "diagnostic_builder_boundary": _diagnostic_builder_boundary(),
        "immutable_source_boundary": immutable_source_boundary,
        "selection_authority": authority,
        "supersedes": SUPERSEDES,
    }
    return manifest, taxonomy


def _role_policy_binding() -> tuple[dict[str, Any], dict[str, Any]]:
    data = _worktree_regular_bytes(ROLE_POLICY)
    policy = _strict_json(data, source=ROLE_POLICY.as_posix())
    if not isinstance(policy, dict) or not isinstance(policy.get("roles"), dict):
        raise DiagnosticError("role policy is missing its role map")
    return {
        "byte_count": len(data),
        "path": ROLE_POLICY.as_posix(),
        "schema_version": policy.get("schema_version"),
        "sha256_file_bytes": _sha256(data),
    }, policy


def _leaf_pointers(value: Any, prefix: str = "") -> list[str]:
    if isinstance(value, dict):
        pointers: list[str] = []
        for key in sorted(value):
            escaped = key.replace("~", "~0").replace("/", "~1")
            pointers.extend(_leaf_pointers(value[key], f"{prefix}/{escaped}"))
        return pointers
    if isinstance(value, list):
        return [prefix]
    return [prefix]


def _visibility_policy_field(pointer: str) -> str:
    parts = pointer.lstrip("/").split("/")
    top = parts[0]
    if top in {"candidate_row_id", "future_candidate_unit_id"}:
        return "/instance_id"
    if top in {
        "candidate_pointer",
        "eval_set_pointer",
        "recovery_target_pointer",
        "recovery_witness_pointer",
    }:
        return "/source_path"
    if top in {"instance_id", "task_id"}:
        return "/instance_id"
    if top == "repo":
        return "/repository"
    if top == "source_run":
        return "/source_run"
    if top in {"label_pointer", "label_provenance"}:
        return "/candidate_operational_label"
    if top == "missing_outcome":
        return "/missingness_state"
    if top == "operational_stratum":
        return "/operational_stratum"
    if top in {"cross_stratum_overlap", "task_strata"}:
        return "/task_cluster"
    if top == "independent_semantic_label":
        return "/locked_semantic_labels"
    if top == "patch":
        if len(parts) > 1 and parts[1] == "path":
            return "/source_path"
        return "/implementation_digests"
    if top == "recovery_witness":
        return "/prior_witness"
    if top == "recovery_execution":
        return "/historical_outcome"
    raise DiagnosticError(f"frame field lacks a visibility mapping: {pointer}")


def _build_frame_v2(
    legacy_frame: dict[str, Any],
    authority: dict[str, Any],
    immutable_source_boundary: dict[str, Any],
) -> dict[str, Any]:
    role_binding, role_policy = _role_policy_binding()
    roles = role_policy["roles"]
    field_catalog = role_policy.get("field_catalog")
    if not isinstance(field_catalog, dict):
        raise DiagnosticError("role policy is missing its field catalogue")
    allowed_by_field: dict[str, list[str]] = {}
    for role_name, role in roles.items():
        if not isinstance(role, dict) or not isinstance(
            role.get("allowed_view_fields"), list
        ):
            raise DiagnosticError(f"role {role_name}: malformed allowed view")
        for field in role["allowed_view_fields"]:
            allowed_by_field.setdefault(field, []).append(role_name)
    for names in allowed_by_field.values():
        names.sort()

    frame = copy.deepcopy(legacy_frame)
    profiles: dict[str, dict[str, Any]] = {}
    row_ids: set[str] = set()
    for row in frame["rows"]:
        identity = [
            "telos.iter240.frame-row.v2",
            row["operational_stratum"],
            row["source_run"],
            row["instance_id"],
            row["patch"]["sha256_file_bytes"],
        ]
        row_id = _sha256(
            json.dumps(identity, ensure_ascii=False, separators=(",", ":")).encode(
                "utf-8"
            )
        )
        if row_id in row_ids:
            raise DiagnosticError(f"duplicate v2 frame row ID: {row_id}")
        row_ids.add(row_id)
        row["candidate_row_id"] = row_id
        future_unit_identity = [
            "telos.iter240.future-candidate-unit.v1",
            row["task_id"],
            row["patch"]["sha256_file_bytes"],
        ]
        row["future_candidate_unit_id"] = _sha256(
            json.dumps(
                future_unit_identity,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        )

        permissions: list[dict[str, Any]] = []
        for pointer in sorted(_leaf_pointers(row)):
            policy_field = _visibility_policy_field(pointer)
            if policy_field not in field_catalog:
                raise DiagnosticError(
                    f"frame field {pointer}: unregistered role-policy field {policy_field}"
                )
            allowed = allowed_by_field.get(policy_field, [])
            if pointer in {"/candidate_row_id", "/future_candidate_unit_id"} and allowed:
                raise DiagnosticError(
                    "content-derived internal IDs cannot be visible to a future role"
                )
            permissions.append(
                {
                    "allowed_future_roles": allowed,
                    "any_future_role_permitted": bool(allowed),
                    "frame_field_pointer": pointer,
                    "policy_field": policy_field,
                }
            )
        profile_id = _sha256(_canonical_bytes(permissions))
        profiles.setdefault(profile_id, {"field_permissions": permissions})
        row["row_visibility_profile_id"] = profile_id

    task_patch_groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in frame["rows"]:
        key = (row["task_id"], row["patch"]["sha256_file_bytes"])
        task_patch_groups.setdefault(key, []).append(row)
    unique_patch_digests = {
        row["patch"]["sha256_file_bytes"] for row in frame["rows"]
    }
    duplicate_groups: list[dict[str, Any]] = []
    for (task_id, patch_sha), members in sorted(task_patch_groups.items()):
        if len(members) <= 1:
            continue
        unit_ids = {row["future_candidate_unit_id"] for row in members}
        if len(unit_ids) != 1:
            raise DiagnosticError("duplicate task+patch rows do not share one future unit")
        source_rows = sorted(
            (
                {
                    "candidate_row_id": row["candidate_row_id"],
                    "operational_stratum": row["operational_stratum"],
                    "source_run": row["source_run"],
                }
                for row in members
            ),
            key=lambda item: (
                item["operational_stratum"],
                item["source_run"],
                item["candidate_row_id"],
            ),
        )
        strata = sorted({row["operational_stratum"] for row in members})
        duplicate_groups.append(
            {
                "candidate_patch_sha256_file_bytes": patch_sha,
                "candidate_row_ids": sorted(
                    row["candidate_row_id"] for row in members
                ),
                "cross_stratum": len(strata) > 1,
                "future_candidate_unit_id": next(iter(unit_ids)),
                "member_count": len(members),
                "operational_strata": strata,
                "source_rows": source_rows,
                "task_id": task_id,
            }
        )

    expected_strata = {
        "fresh_missing": {
            "operational_rows": 13,
            "unique_candidate_patch_byte_digests": 13,
            "unique_task_candidate_patch_units": 13,
            "unique_task_identities": 13,
        },
        "hard_control": {
            "operational_rows": 25,
            "unique_candidate_patch_byte_digests": 21,
            "unique_task_candidate_patch_units": 21,
            "unique_task_identities": 14,
        },
        "operational_positive": {
            "operational_rows": 17,
            "unique_candidate_patch_byte_digests": 17,
            "unique_task_candidate_patch_units": 17,
            "unique_task_identities": 12,
        },
    }
    strata: dict[str, dict[str, int]] = {}
    for name in expected_strata:
        rows = [
            row for row in frame["rows"] if row["operational_stratum"] == name
        ]
        strata[name] = {
            "operational_rows": len(rows),
            "unique_candidate_patch_byte_digests": len(
                {row["patch"]["sha256_file_bytes"] for row in rows}
            ),
            "unique_task_candidate_patch_units": len(
                {
                    (row["task_id"], row["patch"]["sha256_file_bytes"])
                    for row in rows
                }
            ),
            "unique_task_identities": len({row["task_id"] for row in rows}),
        }
    if (
        len(frame["rows"]) != 55
        or len({row["task_id"] for row in frame["rows"]}) != 37
        or len(task_patch_groups) != 50
        or len(unique_patch_digests) != 50
        or len(duplicate_groups) != 5
        or strata != expected_strata
    ):
        raise DiagnosticError("future candidate-unit accounting changed")
    cross_stratum_duplicates = [
        group for group in duplicate_groups if group["cross_stratum"]
    ]
    if (
        len(cross_stratum_duplicates) != 1
        or cross_stratum_duplicates[0]["task_id"] != "pydata__xarray-7233"
        or cross_stratum_duplicates[0]["candidate_patch_sha256_file_bytes"]
        != "5e91e5de8f09c72c3afda6bc4410a016419d882ed58f2d8596c4eb380f161573"
    ):
        raise DiagnosticError("registered exact cross-stratum duplicate changed")
    exact_cross_stratum = {
        "candidate_patch_sha256_file_bytes": cross_stratum_duplicates[0][
            "candidate_patch_sha256_file_bytes"
        ],
        "candidate_row_ids": cross_stratum_duplicates[0]["candidate_row_ids"],
        "count": 1,
        "future_candidate_unit_id": cross_stratum_duplicates[0][
            "future_candidate_unit_id"
        ],
        "operational_strata": cross_stratum_duplicates[0]["operational_strata"],
        "task_id": cross_stratum_duplicates[0]["task_id"],
    }

    frame["diagnostic_builder_boundary"] = _diagnostic_builder_boundary()
    frame["duplicate_task_candidate_patch_group_count"] = len(duplicate_groups)
    frame["duplicate_task_candidate_patch_groups"] = duplicate_groups
    frame["cross_stratum_exact_duplicate"] = exact_cross_stratum
    frame["future_semantic_adjudication"] = {
        "candidate_packet_count": len(task_patch_groups),
        "candidate_unit_count": len(task_patch_groups),
        "candidate_unit_identity_fields": [
            "task_id",
            "candidate_patch.sha256_file_bytes",
        ],
        "duplicate_operational_rows_share_one_candidate_packet": True,
        "inferential_cluster": "unique_task_identity",
        "operational_rows_retained_for": [
            "provenance",
            "witness_discordance",
        ],
        "semantic_adjudication_unit": "unique_task_identity_plus_candidate_patch_bytes",
        "task_level_endpoint_aggregation": {
            "reason": (
                "Multiple distinct candidate patches may occur within one task; no "
                "task-level endpoint aggregation rule has been prospectively frozen."
            ),
            "status": "blocked_unresolved",
        },
    }
    frame["immutable_source_boundary"] = immutable_source_boundary
    frame["role_policy_binding"] = role_binding
    frame["packetization_contract"] = {
        "candidate_unit_id_role_visibility": "none",
        "candidate_row_id_role_visibility": "none",
        "candidate_row_id_use": "internal_evidence_linkage_only",
        "future_candidate_unit_id_use": "internal_grouping_only",
        "one_future_candidate_packet_per_candidate_unit": True,
        "future_packet_id_requirement": (
            "broker-generated opaque unlinkable identifier independent of candidate "
            "row content, source identity, task identity, stratum, and patch digest"
        ),
    }
    frame["row_visibility_profiles"] = dict(sorted(profiles.items()))
    frame["schema_version"] = "telos.iter240.ground_truth_frame.v2"
    frame["selection_authority"] = authority
    frame["strata"] = strata
    frame["supersedes"] = SUPERSEDES
    frame["unique_candidate_patch_byte_digest_count"] = len(unique_patch_digests)
    frame["unique_task_candidate_patch_unit_count"] = len(task_patch_groups)
    return frame


def _decimal_18(numerator: int, denominator: int) -> str:
    with localcontext() as context:
        context.prec = 80
        value = Decimal(numerator) / Decimal(denominator)
        quantum = Decimal(1).scaleb(-18)
        return format(
            value.quantize(quantum, rounding=ROUND_HALF_EVEN),
            ".18f",
        )


def _fresh_acquisition_identity_contract() -> dict[str, Any]:
    cohorts: list[dict[str, Any]] = []
    attempted_sets: list[set[str]] = []
    certified_sets: list[set[str]] = []
    all_attempted: set[str] = set()
    all_solutions: set[str] = set()
    all_certified: set[str] = set()
    for run in FRESH_RUNS:
        root = Path("experiments") / run / "proof"
        solve_path = root / "raw/solutions/solve_summary.json"
        candidate_path = root / "iter200_per_candidate.json"
        solve = _strict_json(_read_predecessor(solve_path), source=solve_path.as_posix())
        candidates_document = _strict_json(
            _read_predecessor(candidate_path),
            source=candidate_path.as_posix(),
        )
        if not isinstance(solve, dict) or not isinstance(candidates_document, dict):
            raise DiagnosticError(f"{run}: acquisition sources must be JSON objects")
        manifest = solve.get("manifest")
        candidates = candidates_document.get("candidates")
        if (
            not isinstance(manifest, list)
            or any(not isinstance(row, dict) for row in manifest)
            or not isinstance(candidates, list)
            or any(not isinstance(row, dict) for row in candidates)
        ):
            raise DiagnosticError(f"{run}: acquisition rows are malformed")
        attempted_ids = [row.get("instance_id") for row in manifest]
        solution_ids = [
            row.get("instance_id")
            for row in manifest
            if row.get("status") == "solution"
        ]
        candidate_ids = [row.get("instance_id") for row in candidates]
        certified_ids: list[str] = []
        for index, row in enumerate(candidates):
            certified = row.get("certified_resolved")
            if type(certified) is not bool:
                raise DiagnosticError(
                    f"{candidate_path}#/candidates/{index}: certified flag is not boolean"
                )
            if certified:
                certified_ids.append(row.get("instance_id"))
        for label, values in (
            ("attempted", attempted_ids),
            ("solution", solution_ids),
            ("candidate", candidate_ids),
            ("certified", certified_ids),
        ):
            if any(not isinstance(value, str) or not value for value in values):
                raise DiagnosticError(f"{run}: {label} task identity is malformed")
            if len(values) != len(set(values)):
                raise DiagnosticError(f"{run}: {label} task identities are not unique")
        attempted = set(attempted_ids)
        solutions = set(solution_ids)
        candidate_set = set(candidate_ids)
        certified = set(certified_ids)
        if (
            solve.get("targets") != len(attempted)
            or solve.get("solutions") != len(solutions)
            or candidate_set != solutions
            or not certified <= attempted
        ):
            raise DiagnosticError(f"{run}: acquisition identity accounting changed")
        attempted_sets.append(attempted)
        certified_sets.append(certified)
        if all_attempted & attempted:
            raise DiagnosticError("fresh attempted cohorts are not disjoint")
        all_attempted.update(attempted)
        all_solutions.update(solutions)
        all_certified.update(certified)
        cohorts.append(
            {
                "attempted_task_count": len(attempted),
                "attempted_task_ids": sorted(attempted),
                "attempted_task_ids_unique": True,
                "certified_task_count": len(certified),
                "certified_task_ids": sorted(certified),
                "certified_task_ids_subset_attempted": certified <= attempted,
                "certified_task_ids_unique": True,
                "pointers": {
                    "attempted_tasks": {
                        "json_pointer": "/manifest",
                        "path": solve_path.as_posix(),
                    },
                    "certification_rows": {
                        "json_pointer": "/candidates",
                        "path": candidate_path.as_posix(),
                    },
                },
                "solution_patch_task_count": len(solutions),
                "source_run": run,
            }
        )
    cohorts_disjoint = not (attempted_sets[0] & attempted_sets[1])
    certified_cohorts_disjoint = not (certified_sets[0] & certified_sets[1])
    if (
        len(all_attempted) != 64
        or len(all_solutions) != 62
        or len(all_certified) != 37
        or not cohorts_disjoint
        or not certified_cohorts_disjoint
        or not all_certified <= all_attempted
    ):
        raise DiagnosticError("aggregate fresh acquisition identities changed")
    return {
        "attempted_task_count": len(all_attempted),
        "attempted_task_ids": sorted(all_attempted),
        "attempted_task_ids_unique": True,
        "certification_yield_fraction": {
            "denominator": len(all_attempted),
            "numerator": len(all_certified),
        },
        "certified_task_count": len(all_certified),
        "certified_task_ids": sorted(all_certified),
        "certified_task_ids_subset_attempted": all_certified <= all_attempted,
        "certified_task_ids_unique": True,
        "certified_task_cohorts_pairwise_disjoint": certified_cohorts_disjoint,
        "cohorts": cohorts,
        "cohorts_pairwise_disjoint": cohorts_disjoint,
        "interpretation": "retrospective_point_observation",
        "solution_patch_task_count": len(all_solutions),
        "stable_estimate": False,
    }


def _build_curves_v2(
    legacy_curves: dict[str, Any],
    authority: dict[str, Any],
    immutable_source_boundary: dict[str, Any],
) -> dict[str, Any]:
    curves = copy.deepcopy(legacy_curves)
    for branch in curves["missingness_branches"]:
        x = branch["fresh_operational_positive_count"]
        legacy_comparison = branch.pop("registered_strict_concentration_holds")
        exact_comparison = 29 * x < 185
        if legacy_comparison is not exact_comparison:
            raise DiagnosticError("legacy rate comparison differs from exact integers")
        branch["fresh_rate_strictly_below_reused_rate"] = exact_comparison
        fisher = branch["exploratory_fisher"]
        fisher["decimal_display"] = _decimal_18(
            fisher["numerator"], fisher["denominator"]
        )
    curves["missingness_rate_comparison_contract"] = {
        "exact_integer_condition": "29 * x < 185",
        "interpretation": (
            "Whether x/37 is strictly below 5/29 for each complete missingness "
            "assignment; this is not a concentration or population claim."
        ),
        "registered_x_domain": {
            "maximum": 13,
            "minimum": 0,
        },
    }

    zero_event = curves.pop("zero_event_upper_bounds")
    zero_event["acquisition_connection"] = {
        "blockers": [
            "task_level_endpoint_aggregation",
            "supported_label_yield",
            "consequence_validity",
            "adjudication_completion",
        ],
        "status": "blocked_disconnected",
        "unlock_condition": (
            "all blockers prospectively frozen from independent ground-truth "
            "measurements before any acquisition calculation"
        ),
    }
    zero_event["assumptions"] = {
        "common_event_probability_across_tasks": True,
        "completed_independently_adjudicated_endpoint_per_unique_task": 1,
        "endpoint_type": "Bernoulli",
        "independent_bernoulli_task_endpoints": True,
        "model": "iid_binomial",
        "population_inference_for_current_convenience_cohorts": False,
    }
    zero_event["interpretation"] = (
        "Binomial-model sensitivity only; current operational convenience cohorts "
        "do not satisfy or establish the population-sampling assumptions."
    )
    curves["binomial_model_sensitivity"] = zero_event

    legacy_acquisition = curves["acquisition_sensitivity"]
    retrospective = _fresh_acquisition_identity_contract()
    illustrative_points: list[dict[str, Any]] = []
    expected_yield_grid = [
        (2, 5),
        (1, 2),
        (37, 64),
        (3, 5),
        (2, 3),
        (3, 4),
        (4, 5),
    ]
    if len(legacy_acquisition["rows"]) != len(expected_yield_grid):
        raise DiagnosticError("illustrative yield grid must contain seven points")
    for point_index, row in enumerate(legacy_acquisition["rows"]):
        point = copy.deepcopy(row)
        yield_record = point["certification_yield"]
        numerator = yield_record["numerator"]
        denominator = yield_record["denominator"]
        if (
            type(numerator) is not int
            or type(denominator) is not int
            or not 0 < numerator <= denominator
            or (numerator, denominator) != expected_yield_grid[point_index]
        ):
            raise DiagnosticError("illustrative certification-yield point changed")
        matches_observation = point.pop("historical_fresh_input")
        expected_match = yield_record == {
            "denominator": 64,
            "numerator": 37,
        }
        if matches_observation is not expected_match:
            raise DiagnosticError("historical illustrative-yield marker changed")
        point["matches_retrospective_point_observation"] = expected_match
        if len(point["targets"]) != 4:
            raise DiagnosticError("illustrative target grid must contain four counts")
        for target_index, target in enumerate(point["targets"]):
            target_count = target["target_unique_certified_tasks"]
            if target_count != (29, 59, 149, 299)[target_index]:
                raise DiagnosticError("illustrative target grid changed")
            retained_threshold = target.pop(
                "required_solve_attempts"
            )
            exact_threshold = (
                target_count * denominator + numerator - 1
            ) // numerator
            if retained_threshold != exact_threshold:
                raise DiagnosticError("expected-count threshold arithmetic changed")
            target["expected_count_threshold_solve_attempts"] = exact_threshold
        illustrative_points.append(point)
    curves["acquisition_sensitivity"] = {
        "authority": "planning_sensitivity_only_not_purchase_authority",
        "blockers": [
            "task_level_endpoint_aggregation",
            "supported_label_yield",
            "consequence_validity",
            "adjudication_completion",
            "certification_yield_uncertainty",
            "cohort_shift",
        ],
        "conditional_solution_patch_diagnostic": legacy_acquisition[
            "conditional_solution_patch_diagnostic"
        ],
        "future_unique_task_acquisition_contract": {
            "attempted_task_id_sampling": "without_replacement",
            "attempted_task_ids_unique_required": True,
            "certified_task_ids_must_be_subset_of_attempted": True,
            "cross_cohort_task_reuse_allowed": False,
            "unit": "unique_task_identity",
        },
        "illustrative_post_hypothesis_grid": {
            "completeness_claim": False,
            "point_count": len(illustrative_points),
            "points": illustrative_points,
            "rationale": (
                "Seven exact arithmetic stress points spanning 2/5 through 4/5, "
                "including the retrospective 37/64 point, were chosen during "
                "post-hypothesis implementation; they were not preregistered and "
                "are neither exhaustive nor estimates."
            ),
            "status": "illustrative_post_hypothesis_grid",
        },
        "retrospective_fresh_point_observation": retrospective,
        "symbolic_expected_count_rule": {
            "domain": "0 < y <= 1",
            "expected_count": "n * y",
            "fixed_point_yield_assumption": True,
            "positive_y_threshold_rule": "ceil(target_unique_certified_tasks / y)",
            "quantity": (
                "minimum integer n whose expected certified count reaches the "
                "target under one fixed point yield y"
            ),
            "yield_symbol": "y",
            "yield_zero_boundary": {
                "disposition_for_positive_target": "unattainable",
                "y": "0",
            },
            "not_a": [
                "probability_guarantee",
                "power_calculation",
                "stable_yield_estimate",
                "independent_label_count",
                "purchase_authority",
            ],
        },
    }
    readiness = curves["assurance_delta_readiness"]
    readiness["missing_measured_inputs"] = [
        "task_level_endpoint_aggregation",
        "supported_label_yield",
        "consequence_validity",
        "adjudication_completion",
        "within_task_discordance",
        "control_false_rejection_behavior",
        "certification_yield_uncertainty",
        "cohort_shift",
    ]
    curves["numeric_contract"] = {
        "fisher_authority": "exact_integer_numerator_and_denominator",
        "fisher_decimal_display": "18-place half-even Decimal at precision 80",
        "libm_bit_exact_comparison_forbidden": True,
        "binomial_model_sensitivity_authority": (
            "Decimal natural-log/exponential at precision 80 plus exact threshold "
            "crossing inequality"
        ),
        "binomial_display_absolute_tolerance": "0.0000000000000000005",
    }
    curves["claim_boundary"] = (
        "Complete missingness and arithmetic sensitivity grids for design only. "
        "Rate comparisons are exact operational fractions, binomial values require "
        "iid task endpoints with one common probability, and expected-count thresholds "
        "are not guarantees, power, estimates, independent-label counts, or spend authority."
    )
    curves["diagnostic_builder_boundary"] = _diagnostic_builder_boundary()
    curves["immutable_source_boundary"] = immutable_source_boundary
    curves["schema_version"] = "telos.iter240.decision_curves.v2"
    curves["selection_authority"] = authority
    curves["supersedes"] = SUPERSEDES
    return curves


def _instrument_record(path: Path) -> dict[str, Any]:
    data = _worktree_regular_bytes(path)
    return {
        "byte_count": len(data),
        "path": path.as_posix(),
        "sha256_file_bytes": _sha256(data),
    }


def _build_receipt(
    outputs: dict[str, dict[str, Any]],
    source_records: list[dict[str, Any]],
    authority: dict[str, Any],
    immutable_source_boundary: dict[str, Any],
) -> dict[str, Any]:
    output_records = []
    for name, path in OUTPUTS.items():
        data = _canonical_bytes(outputs[name])
        output_records.append(
            {
                "byte_count": len(data),
                "path": path.as_posix(),
                "sha256_file_bytes": _sha256(data),
            }
        )
    output_records.sort(key=lambda row: row["path"])
    role_record = _instrument_record(ROLE_POLICY)
    return {
        "claim_boundary": (
            "Byte materialization receipt for the post-freeze offline diagnostic "
            "layer. It is not semantic ground truth or execution, acquisition, "
            "publication, provider, human-contact, GPU, or spend authority."
        ),
        "control_inputs": {
            "diagnostic_builder": _instrument_record(
                Path("scripts/build_iter240_ground_truth_diagnostics.py")
            ),
            "independent_validator": _instrument_record(INDEPENDENT_VALIDATOR),
            "role_policy": role_record,
        },
        "diagnostic_builder_boundary": _diagnostic_builder_boundary(),
        "external_actions": {
            "cohort_acquisitions": 0,
            "gpu_allocations": 0,
            "human_contacts": 0,
            "model_judgment_calls": 0,
            "provider_calls": 0,
            "scientific_containers": 0,
            "spend_usd": "0.00",
            "target_executions": 0,
        },
        "immutable_source_boundary": immutable_source_boundary,
        "outputs": output_records,
        "result_status": {
            "cohort_acquisition": "not_authorized",
            "design_preflight": "supported",
            "independent_ground_truth": "blocked",
            "retained_evidence_recovery": "blocked",
        },
        "schema_version": "telos.iter240.materialization_receipt.v2",
        "selection_authority": authority,
        "source_count": len(source_records),
        "source_inputs": source_records,
        "source_reference_commit": PREDECESSOR,
        "supersedes": SUPERSEDES,
    }


def build_all() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    authority, frozen_rows, immutable_source_boundary = (
        _verify_selection_authority()
    )
    legacy = _load_frozen_builder()
    legacy.build_all = _forbidden_legacy_control
    legacy.preflight = _forbidden_legacy_control
    tracker = legacy.SourceTracker()
    legacy_manifest, legacy_taxonomy, _, acquisition_inputs = (
        legacy.build_missingness(
            tracker,
            immutable_source_boundary,
            frozen_rows,
        )
    )
    legacy_frame = legacy.build_frame(tracker, frozen_rows)
    legacy_curves = legacy.build_decision_curves(tracker, acquisition_inputs)
    source_records = tracker.ledger()
    _verify_source_ledger(source_records)

    observed = [
        (row["source_run"], row["instance_id"])
        for row in legacy_manifest["selected_rows"]
    ]
    expected = [
        (row["source_run"], row["instance_id"]) for row in frozen_rows
    ]
    if observed != expected:
        raise DiagnosticError("post-freeze diagnostic rows differ from frozen census")

    manifest, taxonomy = _build_taxonomy_v2(
        legacy_manifest,
        legacy_taxonomy,
        authority,
        immutable_source_boundary,
    )
    frame = _build_frame_v2(
        legacy_frame,
        authority,
        immutable_source_boundary,
    )
    curves = _build_curves_v2(
        legacy_curves,
        authority,
        immutable_source_boundary,
    )
    outputs = {
        "availability_taxonomy": taxonomy,
        "decision_curves": curves,
        "ground_truth_frame": frame,
        "missingness_manifest": manifest,
    }
    receipt = _build_receipt(
        outputs,
        source_records,
        authority,
        immutable_source_boundary,
    )
    return outputs, receipt


def _write(path: Path, value: Any) -> None:
    absolute = ROOT / path
    absolute.parent.mkdir(parents=True, exist_ok=True)
    absolute.write_bytes(_canonical_bytes(value))


def _check(path: Path, expected: Any) -> list[str]:
    absolute = ROOT / path
    if not absolute.is_file():
        return [f"{path}: missing"]
    expected_bytes = _canonical_bytes(expected)
    actual_bytes = _worktree_regular_bytes(path)
    if actual_bytes != expected_bytes:
        return [
            f"{path}: byte drift "
            f"(actual {_sha256(actual_bytes)}, expected {_sha256(expected_bytes)})"
        ]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        outputs, receipt = build_all()
        if args.write:
            for name, path in OUTPUTS.items():
                _write(path, outputs[name])
            _write(RECEIPT, receipt)
            print(
                "iter240 post-freeze diagnostics: wrote 5 v2 artifacts; "
                "k=0,N=37,u=13 unchanged; external actions=0"
            )
            return 0
        problems: list[str] = []
        for name, path in OUTPUTS.items():
            problems.extend(_check(path, outputs[name]))
        problems.extend(_check(RECEIPT, receipt))
        if problems:
            print("iter240 post-freeze diagnostics: artifacts do not rebuild")
            for problem in problems:
                print(f"  {problem}")
            return 1
        print(
            "iter240 post-freeze diagnostics: exact v2 rebuild passes; "
            "retained recovery blocked; ground truth blocked; acquisition not authorized"
        )
        return 0
    except (
        DiagnosticError,
        OSError,
        UnicodeError,
        subprocess.CalledProcessError,
        ValueError,
    ) as exc:
        print(f"iter240 post-freeze diagnostics: FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
