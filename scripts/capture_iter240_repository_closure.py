#!/usr/bin/env python3
"""Perform iter241's single fixed, read-only GitHub closure capture."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import http.client
import importlib.util
import json
import os
from pathlib import Path
import shutil
import ssl
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter241_iter240_repository_closure"
PROOF = EXPERIMENT / "proof"
RAW_ROOT = PROOF / "raw/iter240_repository_closure"
RECEIPT = PROOF / "iter240_repository_closure.json"
ATTEMPT_FILENAME = "capture_attempt.json"
API_HOST = "api.github.com"
API_VERSION = "2026-03-10"
REPOSITORY = "manfromnowhere143/telos"
AUTHORIZATION_HEAD = "6a9a4f66ec331011c9dfbe14b3a22259a5b585d5"
MAX_RESPONSE_BYTES = 5 * 1024 * 1024

ENDPOINTS = (
    ("pull_request_88", f"/repos/{REPOSITORY}/pulls/88", "pull_request_88.json"),
    ("pull_request_88_timeline", f"/repos/{REPOSITORY}/issues/88/timeline?per_page=100&page=1", "pull_request_88_timeline.json"),
    ("pull_request_88_reviews", f"/repos/{REPOSITORY}/pulls/88/reviews?per_page=100&page=1", "pull_request_88_reviews.json"),
    ("sealed_push_run", f"/repos/{REPOSITORY}/actions/runs/29707762374", "sealed_push_run.json"),
    ("sealed_pr_run", f"/repos/{REPOSITORY}/actions/runs/29707871077", "sealed_pr_run.json"),
    ("sealed_tip_check_runs", f"/repos/{REPOSITORY}/commits/f954696c935ad0b733dcd613b553e1799a7b3810/check-runs?filter=all&per_page=100&page=1", "sealed_tip_check_runs.json"),
    ("gitguardian_check_run", f"/repos/{REPOSITORY}/check-runs/88247740246", "gitguardian_check_run.json"),
    ("merge_commit", f"/repos/{REPOSITORY}/git/commits/39e2484cba450fe5346349921572720b0e456fb7", "merge_commit.json"),
    ("merged_master_run", f"/repos/{REPOSITORY}/actions/runs/29708028160", "merged_master_run.json"),
    ("merged_master_check_runs", f"/repos/{REPOSITORY}/commits/39e2484cba450fe5346349921572720b0e456fb7/check-runs?filter=all&per_page=100&page=1", "merged_master_check_runs.json"),
    ("master_branch", f"/repos/{REPOSITORY}/branches/master", "master_branch.json"),
    ("ruleset", f"/repos/{REPOSITORY}/rulesets/19177100", "ruleset.json"),
    ("effective_rules", f"/repos/{REPOSITORY}/rules/branches/master?per_page=100&page=1", "effective_rules.json"),
)
MINIMUM_FREE_BYTES = MAX_RESPONSE_BYTES * len(ENDPOINTS) * 3

INSTRUMENT_PATHS = (
    "experiments/iter241_iter240_repository_closure/HYPOTHESIS.md",
    "experiments/iter241_iter240_repository_closure/fixtures/repository_closure_safe.json",
    "experiments/iter241_iter240_repository_closure/fixtures/repository_closure_known_bad.json",
    "scripts/capture_iter240_repository_closure.py",
    "scripts/validate_iter240_repository_closure.py",
    "scripts/validate_seal_registry.py",
    "tests/test_iter240_repository_closure.py",
)


class CaptureError(RuntimeError):
    """The one-shot capture failed or a prerequisite differs."""


def canonical_json(value: Any) -> bytes:
    try:
        return (
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CaptureError(f"cannot encode canonical JSON: {exc}") from exc


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def utc_second() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_directory(path: Path, *, label: str) -> None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CaptureError(f"{label} is unavailable: {path}") from exc
    if not path.is_dir() or path.is_symlink() or (metadata.st_mode & 0o022):
        raise CaptureError(f"{label} is not a nonsymlink directory without group/other write")


def _regular_0644(path: Path, *, label: str) -> bytes:
    try:
        metadata = path.lstat()
        raw = path.read_bytes()
    except OSError as exc:
        raise CaptureError(f"{label} is unavailable: {path}") from exc
    if not path.is_file() or path.is_symlink() or (metadata.st_mode & 0o777) != 0o644:
        raise CaptureError(f"{label} is not a regular nonsymlink 0644 file")
    return raw


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _load_validator() -> Any:
    path = ROOT / "scripts/validate_iter240_repository_closure.py"
    raw = _regular_0644(path, label="offline validator")
    try:
        code = compile(raw, str(path), "exec", dont_inherit=True)
    except (SyntaxError, UnicodeError, ValueError) as exc:
        raise CaptureError(f"offline validator cannot compile: {exc}") from exc
    spec = importlib.util.spec_from_file_location("telos_iter240_repository_closure_validator", path)
    if spec is None or spec.loader is None:
        raise CaptureError("cannot construct offline validator module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        exec(code, module.__dict__)
    except Exception as exc:
        sys.modules.pop(spec.name, None)
        raise CaptureError(f"offline validator cannot load: {exc}") from exc
    module.__exact_source_sha256__ = sha256_bytes(raw)
    module.__exact_source_byte_count__ = len(raw)
    return module


def request_plan() -> list[dict[str, str]]:
    return [
        {"method": "GET", "name": name, "request_path": request_path}
        for name, request_path, _filename in ENDPOINTS
    ]


def request_counts() -> dict[str, int]:
    return {"GET": len(ENDPOINTS), "POST": 0, "PUT": 0, "PATCH": 0, "DELETE": 0}


def require_unattempted() -> None:
    if os.path.lexists(RAW_ROOT) or os.path.lexists(RECEIPT):
        raise CaptureError("attempt marker or output already exists; rerun is forbidden")


def preflight() -> Any:
    require_unattempted()
    if ROOT.resolve() != ROOT:
        raise CaptureError("repository root is noncanonical")
    for path, label in (
        (ROOT, "repository root"),
        (ROOT / "scripts", "scripts directory"),
        (ROOT / "tests", "tests directory"),
        (ROOT / "experiments", "experiments directory"),
        (EXPERIMENT, "iter241 experiment directory"),
    ):
        _safe_directory(path, label=label)
    if os.path.lexists(PROOF):
        _safe_directory(PROOF, label="iter241 proof directory")
    if shutil.disk_usage(EXPERIMENT).free < MINIMUM_FREE_BYTES:
        raise CaptureError("insufficient free space for bounded staging and publication")
    validator = _load_validator()
    if tuple(validator.ENDPOINTS) != ENDPOINTS:
        raise CaptureError("capture and offline-validator endpoint plans differ")
    failures = validator.repository_failures(ROOT) + validator.fixture_failures(ROOT)
    if failures:
        raise CaptureError("offline preflight rejected before arming: " + "; ".join(failures))
    return validator


def build_marker(*, armed_at: str) -> dict[str, Any]:
    instruments: list[dict[str, Any]] = []
    for relative in INSTRUMENT_PATHS:
        raw = _regular_0644(ROOT / relative, label=f"capture instrument {relative}")
        instruments.append({"path": relative, "byte_count": len(raw), "sha256": sha256_bytes(raw)})
    plan = request_plan()
    return {
        "schema_version": "telos.iter241.iter240_repository_closure.attempt.v1",
        "repository": REPOSITORY,
        "api_version": API_VERSION,
        "authorization_head": AUTHORIZATION_HEAD,
        "armed_at": armed_at,
        "state": "armed_before_first_request",
        "request_plan": plan,
        "request_plan_sha256": sha256_bytes(canonical_json(plan)),
        "planned_request_counts": request_counts(),
        "instruments": instruments,
    }


def _arm(marker_raw: bytes) -> None:
    if not os.path.lexists(PROOF):
        PROOF.mkdir(mode=0o755)
        _fsync_directory(EXPERIMENT)
    raw_parent = RAW_ROOT.parent
    if not os.path.lexists(raw_parent):
        raw_parent.mkdir(mode=0o755)
        _fsync_directory(PROOF)
    RAW_ROOT.mkdir(mode=0o755)
    _fsync_directory(raw_parent)
    marker_path = RAW_ROOT / ATTEMPT_FILENAME
    with marker_path.open("xb") as handle:
        os.fchmod(handle.fileno(), 0o644)
        handle.write(marker_raw)
        handle.flush()
        os.fsync(handle.fileno())
    _fsync_directory(RAW_ROOT)


def _token() -> str:
    value = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if value and value.strip():
        return value.strip()
    try:
        completed = subprocess.run(
            ["gh", "auth", "token"],
            cwd=ROOT,
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
            env={
                "HOME": os.environ.get("HOME", ""),
                "PATH": os.environ.get("PATH", ""),
            },
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise CaptureError("cannot access the local GitHub credential") from exc
    value = completed.stdout.strip()
    if completed.returncode != 0 or not value:
        raise CaptureError("no GitHub credential is available")
    return value


def _header_document(headers: list[tuple[str, str]]) -> dict[str, Any]:
    rows: list[dict[str, str]] = []
    for name, value in headers:
        if not isinstance(name, str) or not isinstance(value, str) or "\n" in name + value or "\r" in name + value:
            raise CaptureError("unsafe response header")
        rows.append({"name": name, "value": value})
    return {"schema_version": "telos.iter241.github_response_headers.v1", "headers": rows}


def _attempt_binding(marker_raw: bytes) -> dict[str, Any]:
    return {
        "raw_body_path": "experiments/iter241_iter240_repository_closure/proof/raw/iter240_repository_closure/capture_attempt.json",
        "raw_body_byte_count": len(marker_raw),
        "raw_body_sha256": sha256_bytes(marker_raw),
    }


def _validate_staged(
    validator: Any,
    *,
    marker_raw: bytes,
    bodies: dict[str, bytes],
    headers: dict[str, bytes],
    receipt_raw: bytes,
) -> None:
    with tempfile.TemporaryDirectory(prefix="telos-iter241-repository-closure-") as temporary:
        staging = Path(temporary)
        raw_root = staging / "raw"
        raw_root.mkdir(mode=0o755)
        (raw_root / ATTEMPT_FILENAME).write_bytes(marker_raw)
        (raw_root / ATTEMPT_FILENAME).chmod(0o644)
        for _name, _request_path, filename in ENDPOINTS:
            (raw_root / filename).write_bytes(bodies[filename])
            (raw_root / filename).chmod(0o644)
            headers_filename = filename.removesuffix(".json") + ".headers.json"
            (raw_root / headers_filename).write_bytes(headers[headers_filename])
            (raw_root / headers_filename).chmod(0o644)
        receipt_path = staging / "iter240_repository_closure.json"
        receipt_path.write_bytes(receipt_raw)
        receipt_path.chmod(0o644)
        failures = validator.validate(
            root=ROOT,
            receipt_path=receipt_path,
            raw_root=raw_root,
            check_repository=True,
        )
    if failures:
        raise CaptureError("offline validator rejected staged one-shot bytes: " + "; ".join(failures))


def capture() -> None:
    validator = preflight()
    token = _token()
    started_at = utc_second()
    marker = build_marker(armed_at=started_at)
    validator_rows = [
        row for row in marker["instruments"]
        if row["path"] == "scripts/validate_iter240_repository_closure.py"
    ]
    if (
        len(validator_rows) != 1
        or validator_rows[0]["sha256"] != validator.__exact_source_sha256__
        or validator_rows[0]["byte_count"] != validator.__exact_source_byte_count__
    ):
        raise CaptureError("loaded validator differs from marker-bound bytes")
    marker_raw = canonical_json(marker)
    _arm(marker_raw)

    bodies: dict[str, bytes] = {}
    headers: dict[str, bytes] = {}
    documents: dict[str, Any] = {}
    inventory: list[dict[str, Any]] = []
    connection = http.client.HTTPSConnection(
        API_HOST,
        timeout=30,
        context=ssl.create_default_context(),
    )
    try:
        for name, request_path, filename in ENDPOINTS:
            connection.request(
                "GET",
                request_path,
                headers={
                    "Accept": "application/vnd.github+json",
                    "Accept-Encoding": "identity",
                    "Authorization": f"Bearer {token}",
                    "User-Agent": "telos-iter241-repository-closure/1",
                    "X-GitHub-Api-Version": API_VERSION,
                },
            )
            response = connection.getresponse()
            body_raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(body_raw) > MAX_RESPONSE_BYTES:
                raise CaptureError(f"response exceeds five-mebibyte cap: {name}")
            if response.status != 200:
                raise CaptureError(f"GET failed without retry: {name}: HTTP {response.status}")
            header_document = _header_document(response.getheaders())
            header_raw = canonical_json(header_document)
            selected = validator._selected_headers(header_document)
            if selected["api_version_selected"] != API_VERSION:
                raise CaptureError(f"GitHub selected a different API version: {name}")
            if selected["link"] is not None:
                raise CaptureError(f"unexpected pagination Link: {name}")
            try:
                document = validator.strict_json_bytes(body_raw, label=name)
            except Exception as exc:
                raise CaptureError(f"response is not strict JSON: {name}: {exc}") from exc
            headers_filename = filename.removesuffix(".json") + ".headers.json"
            bodies[filename] = body_raw
            headers[headers_filename] = header_raw
            documents[name] = document
            inventory.append(
                {
                    "name": name,
                    "method": "GET",
                    "request_path": request_path,
                    "http_status": response.status,
                    **selected,
                    "raw_headers_path": f"experiments/iter241_iter240_repository_closure/proof/raw/iter240_repository_closure/{headers_filename}",
                    "raw_headers_byte_count": len(header_raw),
                    "raw_headers_sha256": sha256_bytes(header_raw),
                    "raw_body_path": f"experiments/iter241_iter240_repository_closure/proof/raw/iter240_repository_closure/{filename}",
                    "raw_body_byte_count": len(body_raw),
                    "raw_body_sha256": sha256_bytes(body_raw),
                }
            )
    finally:
        connection.close()
        token = ""

    completed_at = utc_second()
    projection = validator.document_projection(documents)
    receipt = {
        "schema_version": "telos.iter241.iter240_repository_closure.v1",
        "repository": REPOSITORY,
        "api_version": API_VERSION,
        "capture": {
            "started_at": started_at,
            "completed_at": completed_at,
            "attempt_marker": _attempt_binding(marker_raw),
            "response_inventory": inventory,
        },
        "request_counts": request_counts(),
        "projection": projection,
        "limitations": validator.LIMITATIONS,
    }
    receipt_raw = canonical_json(receipt)
    _validate_staged(
        validator,
        marker_raw=marker_raw,
        bodies=bodies,
        headers=headers,
        receipt_raw=receipt_raw,
    )

    published: list[Path] = []
    try:
        for _name, _request_path, filename in ENDPOINTS:
            for destination, raw in (
                (RAW_ROOT / filename, bodies[filename]),
                (
                    RAW_ROOT / (filename.removesuffix(".json") + ".headers.json"),
                    headers[filename.removesuffix(".json") + ".headers.json"],
                ),
            ):
                with destination.open("xb") as handle:
                    os.fchmod(handle.fileno(), 0o644)
                    handle.write(raw)
                    handle.flush()
                    os.fsync(handle.fileno())
                published.append(destination)
        with RECEIPT.open("xb") as handle:
            os.fchmod(handle.fileno(), 0o644)
            handle.write(receipt_raw)
            handle.flush()
            os.fsync(handle.fileno())
        published.append(RECEIPT)
        _fsync_directory(RAW_ROOT)
        _fsync_directory(PROOF)
        failures = validator.validate(root=ROOT, receipt_path=RECEIPT, raw_root=RAW_ROOT, check_repository=True)
        if failures:
            raise CaptureError("published bytes failed offline revalidation: " + "; ".join(failures))
    except Exception:
        for path in reversed(published):
            path.unlink(missing_ok=True)
        _fsync_directory(RAW_ROOT)
        _fsync_directory(PROOF)
        raise
    print("iter240 repository closure retained: 13 GET, 0 writes; GitGuardian failure and zero reviews preserved")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="perform the single fixed thirteen-GET capture")
    args = parser.parse_args()
    if not args.capture:
        parser.error("live capture requires the explicit --capture flag")
    try:
        capture()
    except CaptureError as exc:
        print(f"iter240 repository closure capture failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
