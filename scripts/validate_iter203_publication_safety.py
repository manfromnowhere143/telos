#!/usr/bin/env python3
"""Reproduce the iter203 secret/private-identifier and claim-safety audit.

The validator reports only file paths and pattern identifiers.  It never prints a
matched value.  The sealed iter202 inventory is scanned in full, along with every
iter203 experiment artifact except this validator's own derived receipt.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.validate_iter200_corrected_result import (  # noqa: E402
    SECRET_PATTERNS,
    forbidden_positive_claim_ids,
    standing_public_claim_scan,
)


EXP = ROOT / "experiments/iter203_iter202_safety_recovery"
INVENTORY = EXP / "proof/raw/safety_recovery_bridge/upstream_inventory.json"
AUDIT = EXP / "proof/pre_execution_publication_safety.json"
SCHEMA = "telos.iter203.pre_execution_publication_safety.v1"

UUID_RE = re.compile(
    r"(?<![0-9A-Fa-f])"
    r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-"
    r"[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}"
    r"(?![0-9A-Fa-f])"
)
PRIVATE_PATTERNS = {
    "private_email": re.compile(
        r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]{2,}@"
        r"[A-Za-z0-9.-]+\.(?:ai|app|biz|cloud|co|com|dev|edu|gov|info|io|me|net|org)\b",
        re.IGNORECASE,
    ),
    "local_home_path": re.compile(r"/(?:Users|home)/[^/\s\"']+"),
    "npm_token": re.compile(r"\bnpm_[A-Za-z0-9]{30,}\b"),
    "pypi_token": re.compile(r"\bpypi-[A-Za-z0-9_-]{30,}\b"),
    "slack_token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
}


class PublicationSafetyError(ValueError):
    """The publication-safety evidence is malformed or contains a hit."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PublicationSafetyError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def load_json_strict(path: Path) -> dict[str, Any]:
    def reject_constant(value: str) -> None:
        raise PublicationSafetyError(f"non-finite JSON constant: {value}")

    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PublicationSafetyError(f"cannot read strict JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PublicationSafetyError(f"JSON root must be an object: {path}")
    return value


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode(
        "utf-8"
    )


def inventory_paths() -> list[Path]:
    document = load_json_strict(INVENTORY)
    rows = document.get("files")
    if not isinstance(rows, list) or len(rows) != 324:
        raise PublicationSafetyError("sealed upstream inventory must contain exactly 324 files")
    result: list[Path] = []
    previous = ""
    for index, row in enumerate(rows):
        relative = row.get("path") if isinstance(row, dict) else None
        if (
            not isinstance(relative, str)
            or not relative
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or (previous and relative <= previous)
        ):
            raise PublicationSafetyError(f"malformed inventory path at row {index}")
        path = ROOT / relative
        if path.is_symlink() or not path.is_file():
            raise PublicationSafetyError(f"inventory path is missing or non-regular: {relative}")
        result.append(path)
        previous = relative
    return result


def scanned_paths() -> list[Path]:
    paths = set(inventory_paths())
    for path in EXP.rglob("*"):
        if path != AUDIT and path.is_file() and not path.is_symlink():
            paths.add(path)
    return sorted(paths, key=lambda path: path.relative_to(ROOT).as_posix())


def scan_text(text: str) -> tuple[list[str], list[str], int]:
    """Return pattern identifiers only; UUID tails are not account identifiers."""

    secret_hits: list[str] = []
    uuid_count = len(UUID_RE.findall(text))
    without_uuids = UUID_RE.sub("", text)
    for name, pattern in SECRET_PATTERNS.items():
        subject = without_uuids if name == "numeric_account_id" else text
        if pattern.search(subject):
            secret_hits.append(name)
    for name, pattern in PRIVATE_PATTERNS.items():
        if pattern.search(text):
            secret_hits.append(name)
    return sorted(set(secret_hits)), forbidden_positive_claim_ids(text), uuid_count


def build_audit(paths: Iterable[Path] | None = None) -> dict[str, Any]:
    selected = list(scanned_paths() if paths is None else paths)
    secret_hits: list[str] = []
    claim_hits: list[str] = []
    uuid_exclusions = 0
    suffix_counts: Counter[str] = Counter()
    for path in selected:
        if path.is_symlink() or not path.is_file():
            raise PublicationSafetyError(f"scan input is missing or non-regular: {path}")
        try:
            relative = path.relative_to(ROOT).as_posix()
        except ValueError as exc:
            raise PublicationSafetyError(f"scan input escapes repository root: {path}") from exc
        text = path.read_text(encoding="utf-8", errors="replace")
        file_secret_hits, file_claim_hits, file_uuid_count = scan_text(text)
        secret_hits.extend(f"{relative}:{name}" for name in file_secret_hits)
        claim_hits.extend(f"{relative}:{name}" for name in file_claim_hits)
        uuid_exclusions += file_uuid_count
        suffix_counts[path.suffix or "<none>"] += 1

    claim_hits.extend(standing_public_claim_scan())
    if secret_hits or claim_hits:
        diagnostics = sorted(set(secret_hits + claim_hits))
        raise PublicationSafetyError(
            "publication-safety scan failed (identifiers only): " + ", ".join(diagnostics)
        )

    return {
        "experiment_id": "iter203_iter202_safety_recovery",
        "forbidden_positive_claim_hit_count": 0,
        "scanned_file_count": len(selected),
        "scanned_file_suffix_counts": dict(sorted(suffix_counts.items())),
        "schema_version": SCHEMA,
        "sealed_upstream_inventory_file_count": 324,
        "secret_or_private_identifier_hit_count": 0,
        "structural_uuid_exclusion_count": uuid_exclusions,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        rendered = canonical_json_bytes(build_audit())
        if args.check:
            if AUDIT.is_symlink() or not AUDIT.is_file() or AUDIT.read_bytes() != rendered:
                raise PublicationSafetyError(
                    "committed iter203 publication-safety receipt differs from deterministic scan"
                )
        else:
            AUDIT.parent.mkdir(parents=True, exist_ok=True)
            AUDIT.write_bytes(rendered)
    except (OSError, PublicationSafetyError, ValueError) as exc:
        print(f"iter203 publication-safety guard failed: {exc}", file=sys.stderr)
        return 1
    document = json.loads(rendered)
    print(
        "iter203 publication-safety guard: "
        f"{document['scanned_file_count']} files, 0 secret/private hits, "
        "0 forbidden positive-claim hits"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
