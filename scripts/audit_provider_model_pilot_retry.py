#!/usr/bin/env python3
"""Audit the iter11 provider-model pilot retry proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


PROOF = Path("experiments/iter11_provider_model_pilot_retry/proof")
RESULT = Path("experiments/iter11_provider_model_pilot_retry/RESULT.md")
SUMMARY = PROOF / "run_summary.json"
RECEIPT = PROOF / "valid" / "receipt_provider_model_pilot_retry_blocked.json"
EVERYTHING_LOG = (
    PROOF
    / "raw"
    / "codeclash"
    / "PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708140449"
    / "everything.log"
)
SECRET_PATTERNS = [
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ya29\\."),
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
    re.compile(r"ANTHROPIC_API_KEY\\s*=\\s*\\S+"),
    re.compile(r"OPENAI_API_KEY\\s*=\\s*\\S+"),
    re.compile(r"GOOGLE_API_KEY\\s*=\\s*\\S+"),
    re.compile(r"GEMINI_API_KEY\\s*=\\s*\\S+"),
    re.compile(r"GOOGLE_APPLICATION_CREDENTIALS\\s*=\\s*\\S+"),
    re.compile(r"sunlit-unison-[A-Za-z0-9-]+"),
    re.compile(r"errorId=Ci"),
    re.compile(r'"error_info_id"\\s*:\\s*"Ci'),
]


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be an object")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_summary(failures: list[str]) -> None:
    if not SUMMARY.exists():
        failures.append(f"missing summary: {SUMMARY}")
        return
    data = load_json(SUMMARY)
    expected = {
        "schema_version": "telos.provider_model_pilot_retry.summary.v1",
        "status": "blocked",
        "runner": "ephemeral_gce_vm_iap",
        "setup_exit_code": 0,
        "run_exit_code": 124,
        "selected_model": "vertex_ai/gemini-3.1-pro-preview-customtools",
        "selected_budget_usd": 25,
        "provider_permission_denied": True,
        "provider_error_status": "PERMISSION_DENIED",
        "provider_error_reason": "IAM_PERMISSION_DENIED",
        "successful_provider_generation_evidenced": False,
        "p1_trajectory_present": False,
        "cloud_vm_deleted": True,
        "project_identifier_committed": False,
        "credential_material_committed": False,
        "production_or_live_domain_changed": False,
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {data.get(key)!r}")
    if data.get("provider_permission_denied_count", 0) < 1:
        failures.append("summary must record at least one provider permission denial")
    if data.get("model_cost_reported_usd") is not None:
        failures.append("blocked incomplete run must not report a model cost")
    if data.get("model_api_calls_reported") is not None:
        failures.append("blocked incomplete run must not report API-call stats")

    hashes = data.get("artifact_hashes", {})
    if not isinstance(hashes, dict) or not hashes:
        failures.append("summary artifact_hashes must be non-empty")
        return
    for rel, expected_hash in hashes.items():
        path = PROOF / rel
        if not path.exists():
            failures.append(f"hashed artifact missing: {rel}")
            continue
        actual = sha256(path)
        if actual != expected_hash:
            failures.append(f"hash mismatch for {rel}: expected {expected_hash}, got {actual}")


def audit_receipt(failures: list[str]) -> None:
    try:
        receipt = load_receipt(RECEIPT)
    except ProofValidationError as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.status != "blocked":
        failures.append("receipt status is not blocked")
    evidence_kinds = {item.get("kind") for item in receipt.evidence}
    required = {"artifact", "build", "test", "adversarial_review", "live_check"}
    missing = required - evidence_kinds
    if missing:
        failures.append("receipt missing evidence kinds: " + ", ".join(sorted(missing)))
    for item in receipt.evidence:
        artifact = item.get("artifact")
        if artifact and not Path(artifact).exists():
            failures.append(f"receipt artifact path missing: {artifact}")


def audit_result_language(failures: list[str]) -> None:
    if not RESULT.exists():
        failures.append(f"missing result document: {RESULT}")
        return
    result = " ".join(RESULT.read_text(encoding="utf-8").split())
    required = [
        "Status: `BLOCKED`",
        "This is a blocked result, not a model capability result.",
        "No provider-model capability is claimed.",
        "No CodeClash leaderboard result is claimed.",
        "No SWE-bench result is claimed.",
        "No production/live-domain change occurred.",
        "No token, credential JSON, account email, or Google Cloud project identifier is committed.",
    ]
    for phrase in required:
        if phrase not in result:
            failures.append(f"result document missing boundary: {phrase}")


def audit_logs(failures: list[str]) -> None:
    if not EVERYTHING_LOG.exists():
        failures.append(f"missing everything log: {EVERYTHING_LOG}")
        return
    text = EVERYTHING_LOG.read_text(encoding="utf-8", errors="ignore")
    if "Permission 'aiplatform.endpoints.predict' denied" not in text:
        failures.append("everything log must record Vertex predict permission denial")
    if "gemini-3.1-pro-preview-customtools" not in text:
        failures.append("everything log must name the selected model")
    if "<redacted-gcp-project>" not in text:
        failures.append("everything log must show project redaction marker")


def audit_secrets(failures: list[str]) -> None:
    checked = 0
    for path in PROOF.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        checked += 1
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"possible secret or project identifier in {path}")
    if checked == 0:
        failures.append("secret audit checked zero files")


def main() -> int:
    failures: list[str] = []
    audit_summary(failures)
    audit_receipt(failures)
    audit_result_language(failures)
    audit_logs(failures)
    audit_secrets(failures)

    if failures:
        print("provider model pilot retry audit failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("provider model pilot retry audit: clean blocked result")
    return 0


if __name__ == "__main__":
    sys.exit(main())
