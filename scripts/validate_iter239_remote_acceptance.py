#!/usr/bin/env python3
"""Validate iter239's additive remote-acceptance receipt entirely offline."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = (
    ROOT
    / "experiments"
    / "iter240_ground_truth_admission_design"
    / "proof"
    / "iter239_remote_acceptance.json"
)
RAW_ROOT = RECEIPT.parent / "raw" / "iter239_remote_acceptance"
ATTEMPT_FILENAME = "capture_attempt.json"
REPOSITORY = "manfromnowhere143/telos"
API_VERSION = "2026-03-10"
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
HEX64 = re.compile(r"^[0-9a-f]{64}$")
UTC_SECOND = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

COMPLETED_EVIDENCE = "35a97b228afb7bd8eb44e71749986ee59020b25b"
COMPLETED_EVIDENCE_TREE = "16df636427548ffc3b0ed0a4afd9fc15d7c6f255"
CAPTURE_EVIDENCE_COMMIT = "2c71af94318cb9513d5ee9eb5b32b5075bc46991"
ITER239_EXPERIMENT_TREE = "bb4cac9b92c32d89d32d6d64509288022751142d"
SEALED_TIP = "56fb78f5f8afcd8709fde1170e8422072626f367"
SEALED_TIP_TREE = "776f60e7c75616767ce6bb1e45a3eb7279f37a97"
PREDECESSOR_MASTER = "fb87af7eb15b5235a722a7bb3fd3a48962019188"
MERGE_COMMIT = "b597b763f2eb52b2f4f2d36e7daaa31654be076b"
AUTHORIZATION_COMMIT = "cf809ac0e06f37127553e99a2ab9b0705f8e2fae"
ACTIVATION_COMMIT = "63f5786b9b5c60d2bea90f2077208cfb745c31a2"
HYPOTHESIS_SHA256 = "0f1924318e94a6155eaa1939fe7508746e82e4cdbe0ea8758fdb66f32d3b383d"
WORKFLOW_ID = 309260095
WORKFLOW_PATH = ".github/workflows/ci.yml"
INTEGRATION_ID = 15368
RULESET_ID = 19177100
REQUEST_POLICY_SHA256 = "7c8db8fe1104ccd86f6cb35701d83dda35786786641cbc3f3bfa3c2211da4038"
EFFECTIVE_RULES_SHA256 = "1c28e4a105d215452cfe1f718a8598fcf4036fbde642b6906b00019630ea9e68"
EXPECTED_LIMITATIONS = [
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
]

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

EXPECTED_CHECKS = (
    (
        "verify push py3.11",
        "push",
        29701167247,
        88230357876,
        SEALED_TIP,
    ),
    (
        "verify push py3.12",
        "push",
        29701167247,
        88230357837,
        SEALED_TIP,
    ),
    (
        "verify pull_request py3.11",
        "pull_request",
        29701168051,
        88230359868,
        SEALED_TIP,
    ),
    (
        "verify pull_request py3.12",
        "pull_request",
        29701168051,
        88230359882,
        SEALED_TIP,
    ),
    (
        "verify push py3.11",
        "push",
        29701305166,
        88230707891,
        MERGE_COMMIT,
    ),
    (
        "verify push py3.12",
        "push",
        29701305166,
        88230707870,
        MERGE_COMMIT,
    ),
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
POST_CAPTURE_EVOLVABLE_PATHS = frozenset(
    {
        "scripts/validate_iter239_remote_acceptance.py",
        "scripts/validate_iter239_repository_governance.py",
    }
)

TOP_KEYS = {
    "api_version",
    "capture",
    "conclusion",
    "limitations",
    "local_git",
    "projections",
    "repository",
    "request_counts",
    "retained_inputs",
    "schema_version",
}


class ValidationError(ValueError):
    """A retained receipt or response is ambiguous."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValidationError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _reject_nonfinite(value: str) -> None:
    raise ValidationError(f"non-finite JSON value: {value}")


def strict_json(raw: bytes, *, label: str) -> Any:
    try:
        return json.loads(
            raw,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValidationError(f"{label} is not strict JSON: {exc}") from exc


def canonical_json(value: Any) -> bytes:
    try:
        rendered = json.dumps(
            value,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"cannot render canonical JSON: {exc}") from exc
    return (rendered + "\n").encode("utf-8")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def request_plan() -> list[dict[str, str]]:
    return [
        {
            "method": "GET",
            "name": name,
            "request_path": request_path,
        }
        for name, request_path, _filename in ENDPOINTS
    ]


def exact_keys(value: object, expected: set[str], *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{label} is not an object")
    missing = sorted(expected - set(value))
    extra = sorted(set(value) - expected)
    if missing or extra:
        raise ValidationError(
            f"{label} fields differ; missing={missing} unexpected={extra}"
        )
    return value


def is_int(value: object, *, minimum: int = 0) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def utc(value: object, *, label: str) -> datetime:
    if not isinstance(value, str) or UTC_SECOND.fullmatch(value) is None:
        raise ValidationError(f"{label} is not an RFC3339 UTC second")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValidationError(f"{label} is not a real timestamp") from exc
    return parsed.replace(tzinfo=timezone.utc)


def _git(root: Path, *arguments: str) -> bytes:
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=root,
            capture_output=True,
            check=False,
            timeout=30,
            env={
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_NO_REPLACE_OBJECTS": "1",
                "HOME": "/nonexistent/telos-offline-validator",
                "PATH": os.environ.get("PATH", ""),
            },
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValidationError(f"offline git command failed: {' '.join(arguments)}") from exc
    if completed.returncode != 0:
        diagnostic = (completed.stderr or completed.stdout).decode(
            "utf-8", errors="replace"
        ).strip()
        raise ValidationError(
            f"offline git command failed: {' '.join(arguments)}: {diagnostic}"
        )
    return completed.stdout


def git_commit(root: Path, commit: str) -> tuple[list[str], str]:
    raw = _git(root, "show", "-s", "--format=%P%n%T", commit)
    try:
        lines = raw.decode("ascii").splitlines()
    except UnicodeError as exc:
        raise ValidationError(f"Git commit metadata is non-ASCII: {commit}") from exc
    if len(lines) != 2:
        raise ValidationError(f"Git commit metadata is malformed: {commit}")
    return lines[0].split(), lines[1]


def regular_0644(path: Path, *, label: str) -> None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ValidationError(f"{label} is absent: {path}") from exc
    if (
        not stat.S_ISREG(metadata.st_mode)
        or path.is_symlink()
        or stat.S_IMODE(metadata.st_mode) != 0o644
    ):
        raise ValidationError(f"{label} is not a regular nonsymlink 0644 file")


def safe_directory(path: Path, *, label: str) -> None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ValidationError(f"{label} is absent: {path}") from exc
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or path.is_symlink()
        or stat.S_IMODE(metadata.st_mode) & 0o022
    ):
        raise ValidationError(
            f"{label} is not a nonsymlink directory without group/other write"
        )


def retained_capture_instrument_bytes(root: Path, relative: str) -> bytes:
    """Read the captured instrument, not an authorized later successor."""

    path = root / relative
    regular_0644(path, label=f"capture instrument {relative}")
    if relative in POST_CAPTURE_EVOLVABLE_PATHS:
        return _git(root, "show", f"{CAPTURE_EVIDENCE_COMMIT}:{relative}")
    return path.read_bytes()


def load_module(path: Path, name: str) -> Any:
    regular_0644(path, label=f"offline prerequisite {path.name}")
    try:
        raw = path.read_bytes()
        code = compile(raw, str(path), "exec", dont_inherit=True)
    except (OSError, SyntaxError, UnicodeError, ValueError) as exc:
        raise ValidationError(
            f"cannot compile exact offline prerequisite bytes: {path}: {exc}"
        ) from exc
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValidationError(f"cannot load offline prerequisite: {path}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name)
    sys.modules[name] = module
    try:
        exec(code, module.__dict__)
    except Exception:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
        raise
    module.__exact_source_sha256__ = sha256(raw)
    module.__exact_source_byte_count__ = len(raw)
    return module


def repository_failures(root: Path, receipt: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_git = {
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
        "iter240_hypothesis_sha256": HYPOTHESIS_SHA256,
    }
    if canonical_json(receipt.get("local_git")) != canonical_json(expected_git):
        failures.append("local_git projection differs")

    try:
        completed_parents, completed_tree = git_commit(root, COMPLETED_EVIDENCE)
        sealed_parents, sealed_tree = git_commit(root, SEALED_TIP)
        merge_parents, merge_tree = git_commit(root, MERGE_COMMIT)
        authorization_parents, _ = git_commit(root, AUTHORIZATION_COMMIT)
        activation_parents, _ = git_commit(root, ACTIVATION_COMMIT)
        experiment_tree = (
            _git(
                root,
                "rev-parse",
                f"{COMPLETED_EVIDENCE}:experiments/iter239_repository_governance",
            )
            .decode("ascii")
            .strip()
        )
        if completed_tree != COMPLETED_EVIDENCE_TREE:
            failures.append("completed-evidence tree differs")
        if completed_parents != ["f593b5048585052671276c03940ef4df9154724c"]:
            failures.append("completed-evidence parent differs")
        if sealed_parents != [COMPLETED_EVIDENCE] or sealed_tree != SEALED_TIP_TREE:
            failures.append("sealed-tip parent/tree differs")
        if merge_parents != [PREDECESSOR_MASTER, SEALED_TIP]:
            failures.append("merge parents or parent order differs")
        if merge_tree != SEALED_TIP_TREE:
            failures.append("merge tree does not equal sealed-tip tree")
        if experiment_tree != ITER239_EXPERIMENT_TREE:
            failures.append("iter239 completed experiment tree differs")
        if authorization_parents != [MERGE_COMMIT]:
            failures.append("iter240 authorization is not a direct child of the merge")
        if activation_parents != [AUTHORIZATION_COMMIT]:
            failures.append("iter240 activation is not a direct child of authorization")
        if (
            _git(
                root,
                "merge-base",
                "--is-ancestor",
                ACTIVATION_COMMIT,
                "HEAD",
            ).strip()
            != b""
        ):
            # A successful merge-base --is-ancestor has no stdout.
            failures.append("unexpected merge-base output")
        seal_delta = _git(
            root,
            "diff-tree",
            "--no-commit-id",
            "--name-status",
            "-r",
            COMPLETED_EVIDENCE,
            SEALED_TIP,
        ).decode("utf-8")
        if seal_delta != "M\tmission/seal_registry.json\n":
            failures.append("sealed-tip delta is not registry-only")
    except (UnicodeError, ValidationError) as exc:
        failures.append(str(exc))

    hypothesis = (
        root
        / "experiments"
        / "iter240_ground_truth_admission_design"
        / "HYPOTHESIS.md"
    )
    try:
        if sha256(hypothesis.read_bytes()) != HYPOTHESIS_SHA256:
            failures.append("iter240 hypothesis digest differs")
    except OSError as exc:
        failures.append(f"cannot read iter240 hypothesis: {exc}")

    expected_inputs = [
        {"path": path, "sha256": digest} for path, digest in RETAINED_INPUTS
    ]
    if receipt.get("retained_inputs") != expected_inputs:
        failures.append("retained input inventory differs")
    for relative, digest in RETAINED_INPUTS:
        path = root / relative
        try:
            regular_0644(path, label=f"retained input {relative}")
            if (
                relative not in POST_CAPTURE_EVOLVABLE_PATHS
                and sha256(path.read_bytes()) != digest
            ):
                failures.append(f"retained worktree input digest differs: {relative}")
            historical = _git(root, "show", f"{COMPLETED_EVIDENCE}:{relative}")
            if sha256(historical) != digest:
                failures.append(f"retained Git input digest differs: {relative}")
        except (OSError, ValidationError) as exc:
            failures.append(str(exc))

    for relative in sorted(POST_CAPTURE_EVOLVABLE_PATHS):
        path = root / relative
        try:
            regular_0644(path, label=f"current successor validator {relative}")
            committed = _git(root, "show", f"HEAD:{relative}")
            if path.read_bytes() != committed:
                failures.append(
                    f"current successor validator differs from HEAD: {relative}"
                )
        except (OSError, ValidationError) as exc:
            failures.append(str(exc))

    try:
        governance = load_module(
            root / "scripts/validate_iter239_repository_governance.py",
            "telos_iter239_governance_prerequisite",
        )
        failures.extend(
            f"iter239 prerequisite: {failure}"
            for failure in governance.collect_failures(
                root=root,
                require_complete=True,
            )
        )
    except Exception as exc:  # pragma: no cover - fail-closed import boundary
        failures.append(f"cannot run iter239 prerequisite validator: {exc}")
    try:
        seal = load_module(
            root / "scripts/validate_seal_registry.py",
            "telos_seal_prerequisite",
        )
        failures.extend(
            f"seal prerequisite: {failure}"
            for failure in seal.validate(root=root)
        )
    except Exception as exc:  # pragma: no cover - fail-closed import boundary
        failures.append(f"cannot run seal prerequisite validator: {exc}")
    return failures


def attempt_failures(
    receipt: dict[str, Any],
    *,
    root: Path,
    raw_root: Path,
) -> list[str]:
    failures: list[str] = []
    expected_names = {ATTEMPT_FILENAME} | {
        filename for _name, _request_path, filename in ENDPOINTS
    }
    try:
        safe_directory(raw_root, label="remote acceptance raw directory")
        observed_names = {path.name for path in raw_root.iterdir()}
        if observed_names != expected_names:
            failures.append(
                "remote acceptance raw file set differs; "
                f"missing={sorted(expected_names - observed_names)} "
                f"unexpected={sorted(observed_names - expected_names)}"
            )
    except (OSError, ValidationError) as exc:
        return [str(exc)]

    capture = receipt.get("capture")
    binding = capture.get("attempt_marker") if isinstance(capture, dict) else None
    try:
        binding = exact_keys(
            binding,
            {"raw_body_byte_count", "raw_body_path", "raw_body_sha256"},
            label="attempt-marker binding",
        )
    except ValidationError as exc:
        return [str(exc)]
    expected_path = (
        "experiments/iter240_ground_truth_admission_design/"
        "proof/raw/iter239_remote_acceptance/capture_attempt.json"
    )
    marker_path = raw_root / ATTEMPT_FILENAME
    try:
        regular_0644(marker_path, label="capture-attempt marker")
        marker_raw = marker_path.read_bytes()
    except (OSError, ValidationError) as exc:
        return [str(exc)]
    if (
        binding.get("raw_body_path") != expected_path
        or not is_int(binding.get("raw_body_byte_count"), minimum=1)
        or binding.get("raw_body_byte_count") != len(marker_raw)
        or len(marker_raw) > 1024 * 1024
        or not isinstance(binding.get("raw_body_sha256"), str)
        or HEX64.fullmatch(binding["raw_body_sha256"]) is None
        or binding["raw_body_sha256"] != sha256(marker_raw)
    ):
        failures.append("capture-attempt marker byte binding differs")
    try:
        marker = strict_json(marker_raw, label="capture-attempt marker")
        if marker_raw != canonical_json(marker):
            failures.append("capture-attempt marker is not canonical JSON")
        marker = exact_keys(
            marker,
            {
                "api_version",
                "armed_at",
                "instruments",
                "planned_request_counts",
                "repository",
                "request_plan",
                "request_plan_sha256",
                "schema_version",
                "state",
            },
            label="capture-attempt marker",
        )
    except ValidationError as exc:
        return [*failures, str(exc)]

    plan = request_plan()
    if (
        marker.get("schema_version")
        != "telos.iter239.remote_acceptance.attempt.v1"
        or marker.get("repository") != REPOSITORY
        or marker.get("api_version") != API_VERSION
        or marker.get("state") != "armed_before_first_request"
        or canonical_json(marker.get("request_plan")) != canonical_json(plan)
        or marker.get("request_plan_sha256") != sha256(canonical_json(plan))
        or canonical_json(marker.get("planned_request_counts"))
        != canonical_json(
            {
                "GET": len(ENDPOINTS),
                "POST": 0,
                "PUT": 0,
                "PATCH": 0,
                "DELETE": 0,
            }
        )
    ):
        failures.append("capture-attempt fixed plan differs")
    try:
        armed_at = utc(marker.get("armed_at"), label="capture attempt armed_at")
        started_at = utc(
            capture.get("started_at") if isinstance(capture, dict) else None,
            label="capture started_at",
        )
        if armed_at != started_at:
            failures.append("capture attempt time does not bind receipt start")
    except ValidationError as exc:
        failures.append(str(exc))

    expected_instrument_paths = [
        "scripts/capture_iter239_remote_acceptance.py",
        "scripts/validate_iter239_remote_acceptance.py",
        "scripts/validate_iter239_repository_governance.py",
        "scripts/validate_seal_registry.py",
    ]
    try:
        safe_directory(root, label="repository root")
        safe_directory(root / "scripts", label="capture instrument directory")
    except ValidationError as exc:
        failures.append(str(exc))
    instruments = marker.get("instruments")
    if (
        not isinstance(instruments, list)
        or [row.get("path") for row in instruments if isinstance(row, dict)]
        != expected_instrument_paths
        or len(instruments) != len(expected_instrument_paths)
    ):
        failures.append("capture-attempt instrument inventory differs")
        return failures
    for index, relative in enumerate(expected_instrument_paths):
        try:
            row = exact_keys(
                instruments[index],
                {"byte_count", "path", "sha256"},
                label=f"capture instrument {index}",
            )
            raw = retained_capture_instrument_bytes(root, relative)
            if (
                row.get("path") != relative
                or not is_int(row.get("byte_count"), minimum=1)
                or row.get("byte_count") != len(raw)
                or not isinstance(row.get("sha256"), str)
                or HEX64.fullmatch(row["sha256"]) is None
                or row["sha256"] != sha256(raw)
            ):
                failures.append(f"capture instrument byte binding differs: {relative}")
        except (OSError, ValidationError) as exc:
            failures.append(str(exc))
    return failures


def response_documents(
    receipt: dict[str, Any],
    *,
    raw_root: Path,
) -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    capture = receipt.get("capture")
    try:
        capture = exact_keys(
            capture,
            {
                "attempt_marker",
                "started_at",
                "completed_at",
                "response_inventory",
            },
            label="capture",
        )
    except ValidationError as exc:
        return {}, [str(exc)]
    inventory = capture.get("response_inventory")
    if not isinstance(inventory, list) or len(inventory) != len(ENDPOINTS):
        return {}, ["response inventory count differs"]

    documents: dict[str, Any] = {}
    request_ids: list[str] = []
    response_dates: list[datetime] = []
    entry_keys = {
        "api_version_selected",
        "etag",
        "github_request_id",
        "http_status",
        "link",
        "method",
        "name",
        "raw_body_byte_count",
        "raw_body_path",
        "raw_body_sha256",
        "request_path",
        "response_date",
    }
    for index, expected in enumerate(ENDPOINTS):
        name, request_path, filename = expected
        item = inventory[index]
        try:
            item = exact_keys(item, entry_keys, label=f"response inventory {index}")
        except ValidationError as exc:
            failures.append(str(exc))
            continue
        expected_relative = (
            "experiments/iter240_ground_truth_admission_design/"
            f"proof/raw/iter239_remote_acceptance/{filename}"
        )
        if (
            item.get("name") != name
            or item.get("method") != "GET"
            or item.get("request_path") != request_path
            or not is_int(item.get("http_status"))
            or item.get("http_status") != 200
            or item.get("api_version_selected") != API_VERSION
            or item.get("link") is not None
            or item.get("raw_body_path") != expected_relative
        ):
            failures.append(f"response inventory fixed metadata differs: {name}")
        if (
            not isinstance(item.get("github_request_id"), str)
            or not item["github_request_id"].strip()
            or any(ord(character) < 32 for character in item["github_request_id"])
        ):
            failures.append(f"response request ID is invalid: {name}")
        else:
            request_ids.append(item["github_request_id"])
        etag = item.get("etag")
        if etag is not None and (
            not isinstance(etag, str)
            or not etag
            or any(ord(character) < 32 for character in etag)
        ):
            failures.append(f"response ETag is invalid: {name}")
        try:
            response_dates.append(
                utc(item.get("response_date"), label=f"{name} response_date")
            )
        except ValidationError as exc:
            failures.append(str(exc))
        raw_path = raw_root / filename
        try:
            regular_0644(raw_path, label=f"raw response {name}")
            raw = raw_path.read_bytes()
            if (
                not is_int(item.get("raw_body_byte_count"), minimum=1)
                or item.get("raw_body_byte_count") != len(raw)
                or len(raw) > MAX_RESPONSE_BYTES
                or not isinstance(item.get("raw_body_sha256"), str)
                or HEX64.fullmatch(item["raw_body_sha256"]) is None
                or item["raw_body_sha256"] != sha256(raw)
            ):
                failures.append(f"raw response byte binding differs: {name}")
            documents[name] = strict_json(raw, label=f"raw response {name}")
        except (OSError, ValidationError) as exc:
            failures.append(str(exc))
    if len(set(request_ids)) != len(ENDPOINTS):
        failures.append("GitHub response request IDs are absent or duplicated")
    if (
        len(response_dates) != len(ENDPOINTS)
        or response_dates != sorted(response_dates)
    ):
        failures.append("GitHub response dates are absent or out of request order")
    return documents, failures


def run_projection(value: object, *, expected_id: int) -> dict[str, Any]:
    if (
        not isinstance(value, dict)
        or not is_int(value.get("id"))
        or value.get("id") != expected_id
    ):
        raise ValidationError(f"workflow run identity differs: {expected_id}")
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


def derive_checks(
    document: object,
    expected: tuple[tuple[str, str, int, int, str], ...],
) -> list[dict[str, Any]]:
    if not isinstance(document, dict):
        raise ValidationError("check-runs response is not an object")
    rows = document.get("check_runs")
    total = document.get("total_count")
    if (
        not isinstance(rows, list)
        or not is_int(total)
        or total != len(rows)
    ):
        raise ValidationError("check-runs response is incomplete")
    projections: list[dict[str, Any]] = []
    for name, event, run_id, check_id, head_sha in expected:
        name_matches = [
            row
            for row in rows
            if isinstance(row, dict)
            and row.get("name") == name
            and row.get("head_sha") == head_sha
            and isinstance(row.get("app"), dict)
            and row["app"].get("id") == INTEGRATION_ID
        ]
        if len(name_matches) != 1:
            raise ValidationError(
                f"required check is absent, duplicated, or from the wrong app: {name}"
            )
        row = name_matches[0]
        details = row.get("details_url")
        app = row.get("app")
        parsed = urlparse(details) if isinstance(details, str) else None
        expected_path = f"/{REPOSITORY}/actions/runs/{run_id}/job/{check_id}"
        if (
            not is_int(row.get("id"))
            or row.get("id") != check_id
            or not isinstance(app, dict)
            or not is_int(app.get("id"))
            or parsed is None
            or parsed.scheme != "https"
            or parsed.netloc != "github.com"
            or parsed.path != expected_path
            or parsed.params
            or parsed.query
            or parsed.fragment
        ):
            raise ValidationError(f"required check run/job binding differs: {name}")
        suite = row.get("check_suite")
        projections.append(
            {
                "name": name,
                "event": event,
                "run_id": run_id,
                "check_run_id": row.get("id"),
                "check_suite_id": (
                    suite.get("id") if isinstance(suite, dict) else None
                ),
                "app_id": app.get("id") if isinstance(app, dict) else None,
                "app_slug": app.get("slug") if isinstance(app, dict) else None,
                "status": row.get("status"),
                "conclusion": row.get("conclusion"),
                "head_sha": row.get("head_sha"),
                "details_url": details,
                "started_at": row.get("started_at"),
                "completed_at": row.get("completed_at"),
            }
        )
    return projections


def ruleset_request_projection(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or not isinstance(value.get("rules"), list):
        raise ValidationError("ruleset response is malformed")
    rules: list[dict[str, Any]] = []
    for row in value["rules"]:
        if not isinstance(row, dict):
            raise ValidationError("ruleset rule is malformed")
        clone = strict_json(canonical_json(row), label="ruleset rule clone")
        parameters = clone.get("parameters")
        if clone.get("type") == "pull_request" and isinstance(parameters, dict):
            if "required_reviewers" in parameters:
                if parameters["required_reviewers"] != []:
                    raise ValidationError("server-added required_reviewers is not inert")
                del parameters["required_reviewers"]
        rules.append(clone)
    return {
        "name": value.get("name"),
        "target": value.get("target"),
        "enforcement": value.get("enforcement"),
        "bypass_actors": value.get("bypass_actors"),
        "conditions": value.get("conditions"),
        "rules": rules,
    }


def effective_projection(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValidationError("effective rules response is not an array")
    rows: list[dict[str, Any]] = []
    for rule in value:
        if not isinstance(rule, dict):
            raise ValidationError("effective rule is malformed")
        item = {
            "ruleset_id": rule.get("ruleset_id"),
            "ruleset_source": rule.get("ruleset_source"),
            "ruleset_source_type": rule.get("ruleset_source_type"),
            "type": rule.get("type"),
        }
        if "parameters" in rule:
            item["parameters"] = rule.get("parameters")
        rows.append(item)
    return rows


def remote_failures(
    receipt: dict[str, Any],
    documents: dict[str, Any],
    *,
    root: Path,
) -> list[str]:
    failures: list[str] = []
    if set(documents) != {name for name, _, _ in ENDPOINTS}:
        return ["remote response document inventory is incomplete"]

    policy_path = root / "experiments/iter239_repository_governance/policy.json"
    try:
        policy = strict_json(policy_path.read_bytes(), label="retained policy")
        if not isinstance(policy, dict):
            raise ValidationError("retained policy is not an object")
        expected_request = policy.get("request_body")
        if policy.get("request_body_sha256") != REQUEST_POLICY_SHA256:
            failures.append("retained policy request-body digest differs")
    except (OSError, ValidationError) as exc:
        failures.append(str(exc))
        expected_request = None

    pull = documents["pull_request_87"]
    if not isinstance(pull, dict):
        failures.append("pull request response is not an object")
        return failures
    head = pull.get("head")
    base = pull.get("base")
    head_repo = head.get("repo") if isinstance(head, dict) else None
    base_repo = base.get("repo") if isinstance(base, dict) else None
    pull_projection = {
        "number": pull.get("number"),
        "state": pull.get("state"),
        "merged": pull.get("merged"),
        "merged_at": pull.get("merged_at"),
        "draft": pull.get("draft"),
        "head_sha": head.get("sha") if isinstance(head, dict) else None,
        "head_ref": head.get("ref") if isinstance(head, dict) else None,
        "head_repository": (
            head_repo.get("full_name") if isinstance(head_repo, dict) else None
        ),
        "base_sha": base.get("sha") if isinstance(base, dict) else None,
        "base_ref": base.get("ref") if isinstance(base, dict) else None,
        "base_repository": (
            base_repo.get("full_name") if isinstance(base_repo, dict) else None
        ),
    }
    expected_pull = {
        "number": 87,
        "state": "closed",
        "merged": True,
        "merged_at": "2026-07-19T19:48:19Z",
        "draft": False,
        "head_sha": SEALED_TIP,
        "head_ref": "agent/iter239-repository-governance",
        "head_repository": REPOSITORY,
        "base_sha": PREDECESSOR_MASTER,
        "base_ref": "master",
        "base_repository": REPOSITORY,
    }
    if canonical_json(pull_projection) != canonical_json(expected_pull):
        failures.append("pull-request merge projection differs")
    if pull.get("merge_commit_sha") not in {None, MERGE_COMMIT}:
        failures.append("REST merge_commit_sha conflicts with local merge authority")

    try:
        sealed_push = run_projection(
            documents["sealed_push_run"],
            expected_id=29701167247,
        )
        sealed_pr = run_projection(
            documents["sealed_pr_run"],
            expected_id=29701168051,
        )
        merged_run = run_projection(
            documents["merged_master_run"],
            expected_id=29701305166,
        )
        sealed_checks = derive_checks(
            documents["sealed_tip_check_runs"],
            tuple(row for row in EXPECTED_CHECKS if row[4] == SEALED_TIP),
        )
        merged_checks = derive_checks(
            documents["merged_master_check_runs"],
            tuple(row for row in EXPECTED_CHECKS if row[4] == MERGE_COMMIT),
        )
        expected_runs = (
            (
                sealed_push,
                29701167247,
                "push",
                SEALED_TIP,
                "agent/iter239-repository-governance",
            ),
            (
                sealed_pr,
                29701168051,
                "pull_request",
                SEALED_TIP,
                "agent/iter239-repository-governance",
            ),
            (
                merged_run,
                29701305166,
                "push",
                MERGE_COMMIT,
                "master",
            ),
        )
        for run, run_id, event, head_sha, branch in expected_runs:
            if (
                run["id"] != run_id
                or not is_int(run["workflow_id"])
                or run["workflow_id"] != WORKFLOW_ID
                or not is_int(run["attempt"], minimum=1)
                or run["attempt"] != 1
                or run["event"] != event
                or run["status"] != "completed"
                or run["conclusion"] != "success"
                or run["head_sha"] != head_sha
                or run["head_branch"] != branch
                or run["path"] != WORKFLOW_PATH
                or not is_int(run["check_suite_id"], minimum=1)
            ):
                failures.append(f"workflow run acceptance differs: {run_id}")
        run_by_id = {
            29701167247: sealed_push,
            29701168051: sealed_pr,
            29701305166: merged_run,
        }
        for check in [*sealed_checks, *merged_checks]:
            if (
                check["status"] != "completed"
                or check["conclusion"] != "success"
                or check["app_id"] != INTEGRATION_ID
                or check["app_slug"] != "github-actions"
                or not is_int(check["check_suite_id"], minimum=1)
                or check["check_suite_id"]
                != run_by_id[check["run_id"]]["check_suite_id"]
            ):
                failures.append(f"required check acceptance differs: {check['name']}")

        merged_time = utc(expected_pull["merged_at"], label="pull request merged_at")
        for run in (sealed_push, sealed_pr):
            created = utc(run["created_at"], label=f"run {run['id']} created_at")
            updated = utc(run["updated_at"], label=f"run {run['id']} updated_at")
            if not (created <= updated <= merged_time):
                failures.append(f"sealed run does not predate merge: {run['id']}")
        for check in sealed_checks:
            run = run_by_id[check["run_id"]]
            run_created = utc(
                run["created_at"],
                label=f"run {run['id']} created_at",
            )
            run_updated = utc(
                run["updated_at"],
                label=f"run {run['id']} updated_at",
            )
            started = utc(
                check["started_at"],
                label=f"check {check['check_run_id']} started_at",
            )
            completed = utc(
                check["completed_at"],
                label=f"check {check['check_run_id']} completed_at",
            )
            if not (run_created <= started <= completed <= run_updated <= merged_time):
                failures.append(
                    f"sealed check does not predate merge: {check['check_run_id']}"
                )
        merged_created = utc(
            merged_run["created_at"],
            label="merged run created_at",
        )
        merged_updated = utc(
            merged_run["updated_at"],
            label="merged run updated_at",
        )
        if not (merged_time < merged_created <= merged_updated):
            failures.append("merge and merged-master CI chronology differs")
        for check in merged_checks:
            started = utc(
                check["started_at"],
                label=f"check {check['check_run_id']} started_at",
            )
            completed = utc(
                check["completed_at"],
                label=f"check {check['check_run_id']} completed_at",
            )
            if not (merged_created <= started <= completed <= merged_updated):
                failures.append(
                    f"merged check chronology differs: {check['check_run_id']}"
                )
    except ValidationError as exc:
        failures.append(str(exc))
        sealed_push = {}
        sealed_pr = {}
        merged_run = {}
        sealed_checks = []
        merged_checks = []

    branch = documents["master_branch"]
    branch_sha = (
        branch.get("commit", {}).get("sha")
        if isinstance(branch, dict) and isinstance(branch.get("commit"), dict)
        else None
    )
    if (
        not isinstance(branch, dict)
        or branch.get("name") != "master"
        or branch.get("protected") is not True
        or branch_sha != MERGE_COMMIT
    ):
        failures.append("post-merge master branch projection differs")

    ruleset = documents["ruleset"]
    try:
        request_projection = ruleset_request_projection(ruleset)
        if canonical_json(request_projection) != canonical_json(expected_request):
            failures.append("post-merge ruleset request policy differs")
        request_digest = sha256(canonical_json(request_projection))
        if request_digest != REQUEST_POLICY_SHA256:
            failures.append("post-merge ruleset request-policy digest differs")
        if (
            not isinstance(ruleset, dict)
            or not is_int(ruleset.get("id"), minimum=1)
            or ruleset.get("id") != RULESET_ID
            or ruleset.get("source") != REPOSITORY
            or ruleset.get("source_type") != "Repository"
            or ruleset.get("current_user_can_bypass") != "never"
            or ruleset.get("bypass_actors") != []
            or ruleset.get("enforcement") != "active"
        ):
            failures.append("post-merge ruleset identity/enforcement differs")
        effective = effective_projection(documents["effective_rules"])
        effective_digest = sha256(canonical_json(effective))
        if effective_digest != EFFECTIVE_RULES_SHA256:
            failures.append("post-merge effective rules differ")
        if (
            len(effective) != 4
            or any(row.get("ruleset_id") != RULESET_ID for row in effective)
            or any(row.get("ruleset_source") != REPOSITORY for row in effective)
            or any(
                row.get("ruleset_source_type") != "Repository" for row in effective
            )
        ):
            failures.append("post-merge effective-rule provenance differs")
    except ValidationError as exc:
        failures.append(str(exc))
        request_digest = None
        effective_digest = None

    expected_projections = {
        "pull_request": expected_pull,
        "sealed_tip_ci": {
            "head_sha": SEALED_TIP,
            "runs": [sealed_push, sealed_pr],
            "required_checks": sealed_checks,
        },
        "merged_master_ci": {
            "head_sha": MERGE_COMMIT,
            "run": merged_run,
            "required_checks": merged_checks,
        },
        "governance": {
            "branch": "master",
            "branch_sha": branch_sha,
            "protected": branch.get("protected") if isinstance(branch, dict) else None,
            "ruleset_id": ruleset.get("id") if isinstance(ruleset, dict) else None,
            "ruleset_name": (
                ruleset.get("name") if isinstance(ruleset, dict) else None
            ),
            "enforcement": (
                ruleset.get("enforcement") if isinstance(ruleset, dict) else None
            ),
            "current_user_can_bypass": (
                ruleset.get("current_user_can_bypass")
                if isinstance(ruleset, dict)
                else None
            ),
            "request_policy_sha256": request_digest,
            "effective_rules_projection_sha256": effective_digest,
        },
    }
    if canonical_json(receipt.get("projections")) != canonical_json(
        expected_projections
    ):
        failures.append("receipt projections do not independently regenerate")

    expected_conclusion = {
        "engineering_closure": "supported",
        "technical_control": "supported",
        "independent_review": "blocked",
        "overall_governance": "blocked",
        "scientific_authority": "none",
    }
    if receipt.get("conclusion") != expected_conclusion:
        failures.append("receipt conclusion differs or overclaims")

    capture = receipt.get("capture")
    inventory = (
        capture.get("response_inventory") if isinstance(capture, dict) else None
    )
    try:
        started = utc(
            capture.get("started_at") if isinstance(capture, dict) else None,
            label="capture started_at",
        )
        completed = utc(
            capture.get("completed_at") if isinstance(capture, dict) else None,
            label="capture completed_at",
        )
        if completed < started or completed - started > timedelta(minutes=5):
            failures.append("capture window is reversed or exceeds five minutes")
        merged_at = utc(expected_pull["merged_at"], label="pull request merged_at")
        run_created = utc(merged_run.get("created_at"), label="merged run created_at")
        run_completed = utc(merged_run.get("updated_at"), label="merged run updated_at")
        if not (merged_at < run_created <= run_completed):
            failures.append("merge and merged-master CI chronology differs")
        if isinstance(inventory, list):
            for item in inventory:
                if not isinstance(item, dict):
                    continue
                response_date = utc(
                    item.get("response_date"),
                    label=f"{item.get('name')} response_date",
                )
                if response_date < run_completed:
                    failures.append(
                        f"final response predates merged-master CI: {item.get('name')}"
                    )
                if (
                    response_date < started - timedelta(minutes=5)
                    or response_date > completed + timedelta(minutes=5)
                ):
                    failures.append(
                        f"response date is outside capture window: {item.get('name')}"
                    )
    except ValidationError as exc:
        failures.append(str(exc))
    return failures


def validate(
    *,
    root: Path = ROOT,
    receipt_path: Path = RECEIPT,
    raw_root: Path = RAW_ROOT,
    check_repository: bool = True,
) -> list[str]:
    failures: list[str] = []
    try:
        regular_0644(receipt_path, label="remote acceptance receipt")
        raw = receipt_path.read_bytes()
        receipt = strict_json(raw, label="remote acceptance receipt")
        if not isinstance(receipt, dict):
            return ["remote acceptance receipt root is not an object"]
        if raw != canonical_json(receipt):
            failures.append("remote acceptance receipt is not canonical JSON")
        exact_keys(receipt, TOP_KEYS, label="remote acceptance receipt")
    except (OSError, ValidationError) as exc:
        return [str(exc)]

    if (
        receipt.get("schema_version") != "telos.iter239.remote_acceptance.v1"
        or receipt.get("repository") != REPOSITORY
        or receipt.get("api_version") != API_VERSION
    ):
        failures.append("remote acceptance receipt identity differs")
    expected_request_counts = {
        "GET": 9,
        "POST": 0,
        "PUT": 0,
        "PATCH": 0,
        "DELETE": 0,
    }
    if canonical_json(receipt.get("request_counts")) != canonical_json(
        expected_request_counts
    ):
        failures.append("remote acceptance request counts differ")
    if receipt.get("limitations") != EXPECTED_LIMITATIONS:
        failures.append("remote acceptance limitations differ")

    failures.extend(attempt_failures(receipt, root=root, raw_root=raw_root))
    documents, response_failures = response_documents(receipt, raw_root=raw_root)
    failures.extend(response_failures)
    if not response_failures:
        failures.extend(remote_failures(receipt, documents, root=root))
    if check_repository:
        failures.extend(repository_failures(root, receipt))
    return failures


def main() -> int:
    failures = validate()
    if failures:
        print("iter239 remote acceptance validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(
        "iter239 remote acceptance: supported engineering closure; "
        "independent review and scientific authority remain blocked"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
