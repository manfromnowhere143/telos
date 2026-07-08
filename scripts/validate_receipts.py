#!/usr/bin/env python3
"""Validate proof receipts in an experiment proof directory."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_receipts.py <proof-dir>")
        return 2

    proof_dir = Path(sys.argv[1])
    valid_dir = proof_dir / "valid"
    invalid_dir = proof_dir / "invalid"
    failures: list[str] = []

    valid_receipts = sorted(valid_dir.glob("*.json"))
    if not valid_receipts:
        failures.append(f"no valid receipts found under {valid_dir}")

    for path in valid_receipts:
        try:
            load_receipt(path)
        except ProofValidationError as exc:
            failures.append(f"valid receipt failed {path}: {exc}")

    for path in sorted(invalid_dir.glob("*.json")):
        try:
            load_receipt(path)
        except ProofValidationError:
            continue
        failures.append(f"invalid receipt unexpectedly passed: {path}")

    if failures:
        print("receipt validation failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print(f"receipt validation: {len(valid_receipts)} valid receipts passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
