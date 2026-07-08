#!/usr/bin/env python3
"""Audit the iter12 Vertex model access recovery proof bundle."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


PROOF = Path("experiments/iter12_vertex_model_access_recovery/proof")
RESULT = Path("experiments/iter12_vertex_model_access_recovery/RESULT.md")
PROBE = PROOF / "probe.json"
CLOUD_STATE = PROOF / "cloud_state.json"
RECEIPT = PROOF / "valid" / "receipt_vertex_model_access_recovery.json"
SERIAL_LOG = PROOF / "raw" / "vertex_access_probe_serial.log"
SECRET_PATTERNS = [
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ya29\\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
    re.compile(r"ANTHROPIC_API_KEY\\s*=\\s*\\S+"),
    re.compile(r"OPENAI_API_KEY\\s*=\\s*\\S+"),
    re.compile(r"GOOGLE_API_KEY\\s*=\\s*\\S+"),
    re.compile(r"GEMINI_API_KEY\\s*=\\s*\\S+"),
    re.compile(r"GOOGLE_APPLICATION_CREDENTIALS\\s*=\\s*\\S+"),
    re.compile(r"sunlit-unison-[A-Za-z0-9-]+"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.gserviceaccount\\.com"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}"),
    re.compile(r"errorId=Ci"),
    re.compile(r'"error_info_id"\\s*:\\s*"Ci'),
]


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be an object")
    return data


def audit_probe(failures: list[str]) -> None:
    if not PROBE.exists():
        failures.append(f"missing probe: {PROBE}")
        return
    data = load_json(PROBE)
    expected = {
        "schema_version": "telos.vertex_access_probe.v1",
        "status": "pass",
        "runner": "ephemeral_gce_vm",
        "auth_surface": "ephemeral_gce_vm_dedicated_service_account_metadata_token",
        "service_account_short_id": "telos-vertex-runner",
        "selected_model": "gemini-3.1-pro-preview-customtools",
        "endpoint": "publishers/google/models/gemini-3.1-pro-preview-customtools:generateContent",
        "region": "global",
        "http_status": "200",
        "model_call_made": True,
        "benchmark_run_started": False,
        "codeclash_run_started": False,
        "usage_metadata_present": True,
        "successful_endpoint_access_evidenced": True,
        "cloud_vm_deleted": True,
        "credential_material_logged": False,
        "project_identifier_logged": False,
        "account_identifier_logged": False,
        "next_smoke_spend_ceiling_usd": 25,
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"probe {key} expected {value!r}, got {data.get(key)!r}")
    if data.get("candidate_count", 0) < 1:
        failures.append("probe must record at least one candidate")
    if data.get("total_token_count", 0) < 1:
        failures.append("probe must record a positive total token count")
    if data.get("provider_spend_bound_usd", 999) > 0.01:
        failures.append("probe spend bound must remain at or below $0.01")


def audit_cloud_state(failures: list[str]) -> None:
    if not CLOUD_STATE.exists():
        failures.append(f"missing cloud state: {CLOUD_STATE}")
        return
    data = load_json(CLOUD_STATE)
    expected = {
        "schema_version": "telos.vertex_model_access_recovery.cloud_state.v1",
        "status": "pass",
        "dedicated_runner_short_id": "telos-vertex-runner",
        "aiplatform_user_binding_visible_after_cleanup": True,
        "service_account_user_binding_visible_after_cleanup": True,
        "token_creator_binding_visible_after_cleanup": False,
        "ephemeral_vm_deleted": True,
        "full_service_account_identifier_committed": False,
        "project_identifier_committed": False,
        "account_identifier_committed": False,
        "credential_material_committed": False,
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"cloud_state {key} expected {value!r}, got {data.get(key)!r}")


def audit_receipt(failures: list[str]) -> None:
    try:
        receipt = load_receipt(RECEIPT)
    except ProofValidationError as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.status != "pass":
        failures.append("receipt status is not pass")
    evidence_kinds = {item.get("kind") for item in receipt.evidence}
    required = {"test", "artifact", "diff_scope", "adversarial_review", "live_check"}
    missing = required - evidence_kinds
    if missing:
        failures.append("receipt missing evidence kinds: " + ", ".join(sorted(missing)))
    for item in receipt.evidence:
        artifact = item.get("artifact")
        if artifact and not Path(artifact).exists():
            failures.append(f"receipt artifact path missing: {artifact}")


def audit_serial_log(failures: list[str]) -> None:
    if not SERIAL_LOG.exists():
        failures.append(f"missing serial log: {SERIAL_LOG}")
        return
    text = SERIAL_LOG.read_text(encoding="utf-8")
    for required in [
        "vm_created=true",
        "TELOS_ITER12_RESULT",
        '"status": "pass"',
        '"http_status": "200"',
        '"benchmark_run_started": false',
        "vm_deleted=true",
        "token_creator_binding_visible=false",
        "service_account_user_binding_visible=true",
        "aiplatform_user_binding_visible=true",
    ]:
        if required not in text:
            failures.append(f"serial log missing: {required}")


def audit_result_language(failures: list[str]) -> None:
    if not RESULT.exists():
        failures.append(f"missing result document: {RESULT}")
        return
    result = " ".join(RESULT.read_text(encoding="utf-8").split())
    required = [
        "Status: `PASS`",
        "No replacement model was selected.",
        "This is an access result, not a provider capability or benchmark result.",
        "No provider-model capability is claimed.",
        "No CodeClash run was started.",
        "No CodeClash leaderboard result is claimed.",
        "No SWE-bench result is claimed.",
        "No production/live-domain behavior changed.",
        "Full service-account email, active account email, Google Cloud project identifier, tokens, and credential JSON are not committed.",
    ]
    for phrase in required:
        if phrase not in result:
            failures.append(f"result document missing boundary: {phrase}")


def audit_secrets(failures: list[str]) -> None:
    checked = 0
    for path in PROOF.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        checked += 1
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"possible secret or account/project identifier in {path}")
    if checked == 0:
        failures.append("secret audit checked zero files")


def main() -> int:
    failures: list[str] = []
    audit_probe(failures)
    audit_cloud_state(failures)
    audit_receipt(failures)
    audit_serial_log(failures)
    audit_result_language(failures)
    audit_secrets(failures)

    if failures:
        print("vertex model access recovery audit failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("vertex model access recovery audit: clean pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
