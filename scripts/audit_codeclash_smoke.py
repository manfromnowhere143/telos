#!/usr/bin/env python3
"""Audit the iter03 CodeClash smoke proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


PROOF = Path("experiments/iter03_codeclash_smoke/proof")
SUMMARY = PROOF / "run_summary.json"
RECEIPT = PROOF / "valid" / "receipt_codeclash_smoke.json"
EXPECTED_COMMIT = "381cdfa05a35e8acd35853b9fc7e13005121b127"
EXPECTED_RUN_ID = 28935161907
SECRET_PATTERNS = [
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ANTHROPIC_API_KEY\\s*=\\s*\\S+"),
    re.compile(r"OPENAI_API_KEY\\s*=\\s*\\S+"),
    re.compile(r"GITHUB_TOKEN\\s*=\\s*\\S+"),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be an object")
    return data


def audit_summary(failures: list[str]) -> dict:
    if not SUMMARY.exists():
        failures.append(f"missing summary: {SUMMARY}")
        return {}
    summary = load_json(SUMMARY)

    if summary.get("github_run", {}).get("run_id") != EXPECTED_RUN_ID:
        failures.append("unexpected GitHub run id")
    if summary.get("github_run", {}).get("conclusion") != "success":
        failures.append("GitHub run conclusion is not success")
    if summary.get("codeclash", {}).get("commit") != EXPECTED_COMMIT:
        failures.append("CodeClash commit does not match frozen commit")

    tournament = summary.get("tournament", {})
    rounds = tournament.get("rounds")
    if not isinstance(rounds, list) or len(rounds) != 4:
        failures.append("expected exactly 4 parsed rounds")
    else:
        expected_rounds = [0, 1, 2, 3]
        actual_rounds = [round_data.get("round") for round_data in rounds]
        if actual_rounds != expected_rounds:
            failures.append(f"unexpected round sequence: {actual_rounds}")
        for round_data in rounds:
            if round_data.get("all_submissions_valid") is not True:
                failures.append(f"round {round_data.get('round')} has invalid submission")
            scores = round_data.get("scores")
            if not isinstance(scores, dict) or sorted(scores) != ["p1", "p2"]:
                failures.append(f"round {round_data.get('round')} has malformed scores")
            elif any(not isinstance(score, int) for score in scores.values()):
                failures.append(f"round {round_data.get('round')} scores are not integers")

    diff_scope = summary.get("diff_scope", {})
    if diff_scope.get("all_change_records_empty") is not True:
        failures.append("dummy-agent diff-scope records are not all empty")
    change_records = diff_scope.get("change_records")
    if not isinstance(change_records, list) or len(change_records) != 6:
        failures.append("expected 6 player change records")
    else:
        for record in change_records:
            if record.get("empty_diff") is not True:
                failures.append(f"non-empty dummy diff record: {record}")
            linked = PROOF / str(record.get("path", ""))
            if not linked.exists():
                failures.append(f"missing linked change record: {linked}")

    hashes = summary.get("artifact_hashes")
    if not isinstance(hashes, dict) or not hashes:
        failures.append("missing artifact_hashes")
    else:
        raw_files = {
            path.relative_to(PROOF).as_posix()
            for path in (PROOF / "raw").rglob("*")
            if path.is_file()
        }
        hashed_files = set(hashes)
        if raw_files != hashed_files:
            missing_hashes = sorted(raw_files - hashed_files)
            stale_hashes = sorted(hashed_files - raw_files)
            if missing_hashes:
                failures.append("raw files missing hashes: " + ", ".join(missing_hashes))
            if stale_hashes:
                failures.append("hash entries without raw files: " + ", ".join(stale_hashes))
        if summary.get("raw_artifact_file_count") != len(raw_files):
            failures.append("raw_artifact_file_count does not match raw file count")
        for relative, expected in hashes.items():
            path = PROOF / relative
            if not path.exists():
                failures.append(f"hashed artifact missing: {relative}")
                continue
            actual = sha256(path)
            if actual != expected:
                failures.append(f"hash mismatch for {relative}: {actual} != {expected}")

    return summary


def audit_receipt(failures: list[str]) -> None:
    try:
        receipt = load_receipt(RECEIPT)
    except ProofValidationError as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.status != "pass":
        failures.append("receipt status is not pass")

    evidence_kinds = {item.get("kind") for item in receipt.evidence}
    required = {"artifact", "test", "diff_scope", "adversarial_review", "live_check"}
    missing = required - evidence_kinds
    if missing:
        failures.append("receipt missing evidence kinds: " + ", ".join(sorted(missing)))

    for item in receipt.evidence:
        artifact = item.get("artifact")
        if artifact and not Path(artifact).exists():
            failures.append(f"receipt artifact path missing: {artifact}")


def audit_secrets(failures: list[str]) -> None:
    checked = 0
    for path in PROOF.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix in {".gz", ".png", ".jpg", ".jpeg", ".pdf"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        checked += 1
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"possible secret pattern in {path}")
    if checked == 0:
        failures.append("secret audit checked zero text files")


def main() -> int:
    failures: list[str] = []
    audit_summary(failures)
    audit_receipt(failures)
    audit_secrets(failures)

    if failures:
        print("codeclash smoke audit failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("codeclash smoke audit: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
