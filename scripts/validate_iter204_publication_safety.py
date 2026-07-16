#!/usr/bin/env python3
"""Scan all post-iter203-null/iter204 additions without rewriting the frozen scan."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import validate_iter203_publication_safety as prior  # noqa: E402
from scripts.validate_iter200_corrected_result import standing_public_claim_scan  # noqa: E402


EXPERIMENT_ID = "iter204_iter203_infrastructure_recovery"
EXP = ROOT / "experiments" / EXPERIMENT_ID
AUDIT = EXP / "proof/pre_execution_publication_safety.json"
RUNTIME_MANIFEST = EXP / "proof/raw/runtime_manifest.json"
SCHEMA = "telos.iter204.post_null_pre_execution_publication_safety.v1"
POST_NULL_ANCHOR_COMMIT = "5c409f79c9333206cff9ed80d59c08aa347110f6"
WORKSPACE_ONLY_EXCLUDED_PREFIXES = ("tmp/",)

SOURCE_PATHS = {
    ROOT / ".github/workflows/iter204-execute.yml",
    ROOT / "scripts/adjudicate_iter204_infrastructure_recovery.py",
    ROOT / "scripts/build_iter204_runtime_manifest.py",
    ROOT / "scripts/capture_iter204_runtime_host.py",
    ROOT / "scripts/ci_iter204_execute.sh",
    ROOT / "scripts/ci_iter204_smoke.sh",
    ROOT / "scripts/collect_iter204_execution.py",
    ROOT / "scripts/prepare_iter204_output_directory.py",
    ROOT / "scripts/publish_iter204_runtime_diagnostic.py",
    ROOT / "scripts/run_iter204_infrastructure_recovery_blind_judge.py",
    ROOT / "scripts/validate_iter203_infrastructure_null.py",
    ROOT / "scripts/validate_iter203_publication_safety.py",
    ROOT / "scripts/validate_iter204_publication_safety.py",
    ROOT / "scripts/validate_iter204_runtime_recovery.py",
    ROOT / "telos/proof.py",
}
SCANNER_IMPLEMENTATION_EXCLUSIONS = {
    ROOT / "scripts/validate_iter200_corrected_result.py",
}


class PublicationSafetyError(ValueError):
    """A current publication surface contains a secret/private or claim hit."""


def post_null_changed_paths() -> list[Path]:
    relative_paths: set[str] = set()
    commands = (
        [
            "git",
            "diff",
            "--name-only",
            "-z",
            "--diff-filter=ACMRT",
            POST_NULL_ANCHOR_COMMIT,
            "--",
        ],
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
    )
    for command in commands:
        try:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                check=True,
                capture_output=True,
                timeout=30,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise PublicationSafetyError("cannot enumerate post-null repository changes") from exc
        for raw in completed.stdout.split(b"\0"):
            if not raw:
                continue
            try:
                relative = raw.decode("utf-8")
            except UnicodeError as exc:
                raise PublicationSafetyError("post-null path is not UTF-8") from exc
            candidate = Path(relative)
            if (
                candidate.is_absolute()
                or ".." in candidate.parts
                or candidate.as_posix() != relative
            ):
                raise PublicationSafetyError("post-null path is not normalized and relative")
            if relative.startswith(WORKSPACE_ONLY_EXCLUDED_PREFIXES):
                continue
            relative_paths.add(relative)
    excluded = {AUDIT.relative_to(ROOT).as_posix(), RUNTIME_MANIFEST.relative_to(ROOT).as_posix()}
    paths = [ROOT / relative for relative in sorted(relative_paths - excluded)]
    invalid = [path for path in paths if path.is_symlink() or not path.is_file()]
    if invalid:
        raise PublicationSafetyError("post-null change set contains a missing or non-regular file")
    return paths


def post_null_change_closure(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        payload = path.read_bytes()
        relative = path.relative_to(ROOT).as_posix()
        digest.update(
            f"{relative}\0{hashlib.sha256(payload).hexdigest()}\0{len(payload)}\n".encode()
        )
    return digest.hexdigest()


def selected_paths() -> list[Path]:
    paths = set(prior.inventory_paths()) | SOURCE_PATHS | set(post_null_changed_paths())
    invalid_scanners = [
        path
        for path in SCANNER_IMPLEMENTATION_EXCLUSIONS
        if path.is_symlink() or not path.is_file()
    ]
    if invalid_scanners:
        raise PublicationSafetyError("publication scanner implementation is missing")
    iter203 = ROOT / "experiments/iter203_iter202_safety_recovery"
    additions = [
        iter203 / "RESULT.md",
        iter203 / "proof/infrastructure_null.json",
        iter203 / "proof/learning_record.json",
    ]
    additions.extend((iter203 / "proof/raw/public_workflow_logs").glob("*"))
    additions.extend((iter203 / "proof/raw/public_workflow_metadata").glob("*"))
    paths.update(additions)
    if EXP.exists():
        paths.update(
            path
            for path in EXP.rglob("*")
            if path.is_file() and path not in {AUDIT, RUNTIME_MANIFEST}
        )
    missing = [path for path in paths if path.is_symlink() or not path.is_file()]
    if missing:
        raise PublicationSafetyError(
            "current scan input is missing or non-regular: "
            + ", ".join(path.relative_to(ROOT).as_posix() for path in missing)
        )
    return sorted(paths, key=lambda path: path.relative_to(ROOT).as_posix())


def build_audit(paths: list[Path] | None = None) -> dict[str, Any]:
    selected = selected_paths() if paths is None else paths
    changed = post_null_changed_paths() if paths is None else [
        path for path in paths if path not in set(prior.inventory_paths())
    ]
    secret_hits: list[str] = []
    claim_hits: list[str] = []
    suffixes: Counter[str] = Counter()
    uuid_exclusions = 0
    hosted_runner_path_exclusions = 0
    claim_content_paths = set(prior.inventory_paths()) | SOURCE_PATHS
    iter203 = ROOT / "experiments/iter203_iter202_safety_recovery"
    for path in selected:
        relative = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        hosted_runner_path_exclusions += text.count("/home/runner")
        text = text.replace("/home/runner", "/hosted-runner")
        file_secrets, file_claims, uuids = prior.scan_text(text)
        secret_hits.extend(f"{relative}:{name}" for name in file_secrets)
        if (
            path in claim_content_paths
            or EXP in path.parents
            or path in {
                iter203 / "RESULT.md",
                iter203 / "proof/infrastructure_null.json",
                iter203 / "proof/learning_record.json",
            }
        ):
            claim_hits.extend(f"{relative}:{name}" for name in file_claims)
        uuid_exclusions += uuids
        suffixes[path.suffix or "<none>"] += 1
    claim_hits.extend(standing_public_claim_scan())
    if secret_hits or claim_hits:
        raise PublicationSafetyError(
            "current publication scan failed (identifiers only): "
            + ", ".join(sorted(set(secret_hits + claim_hits)))
        )
    return {
        "experiment_id": EXPERIMENT_ID,
        "forbidden_positive_claim_hit_count": 0,
        "frozen_iter203_receipt_sha256": prior.FROZEN_AUDIT_SHA256,
        "hosted_runner_path_exclusion_count": hosted_runner_path_exclusions,
        "post_null_anchor_commit": POST_NULL_ANCHOR_COMMIT,
        "post_null_change_closure_sha256": post_null_change_closure(changed),
        "post_null_changed_file_count": len(changed),
        "scanned_file_count": len(selected),
        "scanned_file_suffix_counts": dict(sorted(suffixes.items())),
        "scanner_implementation_exclusions": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in sorted(SCANNER_IMPLEMENTATION_EXCLUSIONS)
        ],
        "schema_version": SCHEMA,
        "sealed_upstream_inventory_file_count": 324,
        "secret_or_private_identifier_hit_count": 0,
        "structural_uuid_exclusion_count": uuid_exclusions,
        "workspace_only_excluded_prefixes": list(WORKSPACE_ONLY_EXCLUDED_PREFIXES),
    }


def canonical_json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        prior.validate_frozen_receipt()
        rendered = canonical_json_bytes(build_audit())
        if args.check:
            if AUDIT.is_symlink() or not AUDIT.is_file() or AUDIT.read_bytes() != rendered:
                raise PublicationSafetyError("committed iter204 publication receipt differs")
        elif args.write:
            if AUDIT.exists() or AUDIT.is_symlink():
                raise PublicationSafetyError("refusing to overwrite iter204 publication receipt")
            AUDIT.parent.mkdir(parents=True, exist_ok=True)
            AUDIT.write_bytes(rendered)
        else:
            sys.stdout.buffer.write(rendered)
    except (OSError, ValueError, PublicationSafetyError, prior.PublicationSafetyError) as exc:
        print(f"iter204 publication-safety guard failed: {exc}", file=sys.stderr)
        return 1
    document = json.loads(rendered)
    print(
        "iter204 current publication-safety guard: "
        f"{document['scanned_file_count']} files, 0 secret/private hits, "
        "0 forbidden positive-claim hits"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
