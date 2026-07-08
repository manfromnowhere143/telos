#!/usr/bin/env python3
"""Audit the iter09 blocked provider-model pilot smoke proof bundle."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


PROOF = Path("experiments/iter09_provider_model_pilot_smoke/proof")
RESULT = Path("experiments/iter09_provider_model_pilot_smoke/RESULT.md")
PREFLIGHT = PROOF / "preflight.json"
RECEIPT = PROOF / "valid" / "receipt_provider_model_pilot_smoke_blocked.json"
ADC_LOG = PROOF / "preflight" / "adc_check.log"
OVERLAY = PROOF / "overlay"
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
]


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be an object")
    return data


def audit_preflight(failures: list[str]) -> None:
    if not PREFLIGHT.exists():
        failures.append(f"missing preflight: {PREFLIGHT}")
        return
    data = load_json(PREFLIGHT)
    if data.get("schema_version") != "telos.provider_model_pilot_smoke_preflight.v1":
        failures.append("unexpected preflight schema_version")
    if data.get("status") != "blocked":
        failures.append("preflight status must be blocked")
    if data.get("model_call_made") is not False:
        failures.append("model_call_made must be false")
    if data.get("provider_spend_usd") != 0:
        failures.append("provider_spend_usd must be zero")
    if data.get("adc_access_token_available") is not False:
        failures.append("ADC access token must not be marked available")
    if data.get("adc_error_class") != "reauthentication_failed_non_interactive":
        failures.append("unexpected ADC error class")
    if data.get("project_identifier_logged") is not False:
        failures.append("project identifier must not be logged")
    if data.get("active_account_identifier_logged") is not False:
        failures.append("active account identifier must not be logged")
    if data.get("secret_values_logged") is not False:
        failures.append("secret values must not be logged")
    if data.get("selected_model_id") != "gemini-3.1-pro-preview-customtools":
        failures.append("unexpected selected model id")
    if data.get("selected_budget_usd") != 25:
        failures.append("unexpected selected budget")

    linked = Path(str(data.get("preflight_log", "")))
    if not linked.exists():
        failures.append(f"linked preflight log missing: {linked}")


def audit_receipt(failures: list[str]) -> None:
    try:
        receipt = load_receipt(RECEIPT)
    except ProofValidationError as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.status != "blocked":
        failures.append("receipt status is not blocked")
    evidence_kinds = {item.get("kind") for item in receipt.evidence}
    required = {"artifact", "test", "adversarial_review", "live_check"}
    missing = required - evidence_kinds
    if missing:
        failures.append("receipt missing evidence kinds: " + ", ".join(sorted(missing)))
    for item in receipt.evidence:
        artifact = item.get("artifact")
        if artifact and not Path(artifact).exists():
            failures.append(f"receipt artifact path missing: {artifact}")


def audit_overlay(failures: list[str]) -> None:
    required = [
        OVERLAY / "configs" / "mini" / "telos_vertex_gemini_agent.yaml",
        OVERLAY / "configs" / "mini" / "telos_vertex_gemini_3_1_pro_customtools.yaml",
        OVERLAY / "configs" / "mini" / "telos_litellm_cost_registry_entry.json",
        OVERLAY / "configs" / "test" / "telos_battlesnake_vertex_gemini_pilot.yaml",
    ]
    for path in required:
        if not path.exists():
            failures.append(f"missing overlay file: {path}")
    model_text = required[1].read_text(encoding="utf-8") if required[1].exists() else ""
    if "vertex_ai/gemini-3.1-pro-preview-customtools" not in model_text:
        failures.append("model overlay does not name selected Vertex model")
    registry = load_json(required[2]) if required[2].exists() else {}
    if "vertex_ai/gemini-3.1-pro-preview-customtools" not in registry:
        failures.append("cost registry missing selected model")


def audit_result_language(failures: list[str]) -> None:
    if not RESULT.exists():
        failures.append(f"missing result document: {RESULT}")
        return
    result = " ".join(RESULT.read_text(encoding="utf-8").split())
    required = [
        "No paid model call was made.",
        "No provider-model capability is claimed.",
        "No CodeClash leaderboard result is claimed.",
        "No SWE-bench result is claimed.",
        "No production/live-domain change occurred.",
        "No token, API key, credential JSON, account email, or Google Cloud project identifier is committed.",
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
                failures.append(f"possible secret pattern in {path}")
    if checked == 0:
        failures.append("secret audit checked zero text files")


def main() -> int:
    failures: list[str] = []
    audit_preflight(failures)
    audit_receipt(failures)
    audit_overlay(failures)
    audit_result_language(failures)
    audit_secrets(failures)

    if failures:
        print("provider model pilot smoke audit failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("provider model pilot smoke audit: clean blocked result")
    return 0


if __name__ == "__main__":
    sys.exit(main())
