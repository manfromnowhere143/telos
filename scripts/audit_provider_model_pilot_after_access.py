#!/usr/bin/env python3
"""Audit the iter13 provider-model pilot after access recovery proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


PROOF = Path("experiments/iter13_provider_model_pilot_retry_after_access_recovery/proof")
RESULT = Path("experiments/iter13_provider_model_pilot_retry_after_access_recovery/RESULT.md")
SUMMARY = PROOF / "run_summary.json"
PREFLIGHT = PROOF / "preflight.json"
RECEIPT = PROOF / "valid" / "receipt_provider_model_pilot_after_access.json"
TOURNAMENT = (
    PROOF
    / "raw"
    / "codeclash"
    / "PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708155545"
)
TRAJECTORY = TOURNAMENT / "players" / "p1" / "p1_r1.traj.json"
P1_CHANGES = TOURNAMENT / "players" / "p1" / "changes_r1.json"
P2_CHANGES = TOURNAMENT / "players" / "p2" / "changes_r1.json"
RUN_LOG = PROOF / "raw" / "codeclash" / "telos-codeclash-provider-run.log"
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
    re.compile(r"errorId=Ci"),
    re.compile(r'"error_info_id"\\s*:\\s*"Ci'),
    re.compile(r"thought_signature['\"]?\\s*[:=]\\s*['\"](?!<redacted-provider-thought-signature>)"),
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
        "schema_version": "telos.provider_model_pilot_after_access.summary.v1",
        "status": "pass",
        "runner": "ephemeral_gce_vm_dedicated_service_account",
        "service_account_short_id": "telos-vertex-runner",
        "selected_model": "vertex_ai/gemini-3.1-pro-preview-customtools",
        "region": "global",
        "preflight_status": "pass",
        "preflight_http_status": "200",
        "codeclash_started": True,
        "run_exit_code": 0,
        "p1_trajectory_present": True,
        "p1_agent_exit_status": "Submitted",
        "successful_provider_generation_evidenced": True,
        "model_api_calls_reported": 5,
        "model_cost_reported_usd": 0.030392000000000002,
        "round0_winner": "p1",
        "round1_winner": "p1",
        "cloud_vm_deleted": True,
        "raw_binary_round_archive_committed": False,
        "project_identifier_committed": False,
        "credential_material_committed": False,
        "production_or_live_domain_changed": False,
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {data.get(key)!r}")
    if data.get("model_cost_reported_usd", 999) >= 25:
        failures.append("model cost must be below the $25 ceiling")
    if set(data.get("p1_modified_files", [])) != {"README_agent.md", "main.py", "patch.py"}:
        failures.append("summary must record the exact p1 modified-file set")
    diff = data.get("diff_summary", {})
    if diff.get("p1_left_patch_helper_file") is not True:
        failures.append("summary must record the patch.py hygiene issue")

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


def audit_preflight(failures: list[str]) -> None:
    data = load_json(PREFLIGHT)
    expected = {
        "schema_version": "telos.iter13.preflight.v1",
        "status": "pass",
        "http_status": "200",
        "candidate_count": 1,
        "usage_metadata_present": True,
        "total_token_count": 5,
        "credential_material_logged": False,
        "project_identifier_logged": False,
        "account_identifier_logged": False,
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"preflight {key} expected {value!r}, got {data.get(key)!r}")


def audit_raw_artifacts(failures: list[str]) -> None:
    for path in [TRAJECTORY, P1_CHANGES, P2_CHANGES, RUN_LOG, TOURNAMENT / "metadata.json"]:
        if not path.exists():
            failures.append(f"missing raw artifact: {path}")

    trajectory = load_json(TRAJECTORY)
    stats = trajectory.get("info", {}).get("model_stats", {})
    if stats.get("instance_cost") != 0.030392000000000002:
        failures.append("trajectory instance_cost mismatch")
    if stats.get("api_calls") != 5:
        failures.append("trajectory api_calls mismatch")
    if trajectory.get("info", {}).get("exit_status") != "Submitted":
        failures.append("trajectory exit_status must be Submitted")

    changes = load_json(P1_CHANGES)
    diff = changes.get("full_diff", "")
    for required in ["diff --git a/main.py", "README_agent.md", "patch.py", "is_move_safe"]:
        if required not in diff:
            failures.append(f"p1 diff missing {required}")
    if load_json(P2_CHANGES).get("full_diff") != "":
        failures.append("p2 should have an empty diff")

    log = RUN_LOG.read_text(encoding="utf-8")
    for required in [
        "Committed changes for p1 for round 1",
        "In round 1, the winner is p1.",
        "Cleaned up BattleSnake game",
    ]:
        if required not in log:
            failures.append(f"run log missing: {required}")


def audit_receipt(failures: list[str]) -> None:
    try:
        receipt = load_receipt(RECEIPT)
    except ProofValidationError as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.status != "pass":
        failures.append("receipt status is not pass")
    evidence_kinds = {item.get("kind") for item in receipt.evidence}
    required = {"test", "build", "artifact", "diff_scope", "adversarial_review", "live_check"}
    missing = required - evidence_kinds
    if missing:
        failures.append("receipt missing evidence kinds: " + ", ".join(sorted(missing)))
    for item in receipt.evidence:
        artifact = item.get("artifact")
        if artifact and not Path(artifact).exists():
            failures.append(f"receipt artifact path missing: {artifact}")


def audit_result_language(failures: list[str]) -> None:
    result = " ".join(RESULT.read_text(encoding="utf-8").split())
    required = [
        "Status: `PASS`",
        "This is a provider-smoke result, not a leaderboard, SWE-bench, production, or general model capability result.",
        "The agent left `patch.py`, the helper script it used to edit `main.py`.",
        "No CodeClash leaderboard result is claimed.",
        "No SWE-bench result is claimed.",
        "No production/live-domain behavior changed.",
        "The one-game score is context only, not evidence of model superiority.",
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
                failures.append(f"possible secret or unredacted provider field in {path}")
    if checked == 0:
        failures.append("secret audit checked zero files")


def main() -> int:
    failures: list[str] = []
    audit_summary(failures)
    audit_preflight(failures)
    audit_raw_artifacts(failures)
    audit_receipt(failures)
    audit_result_language(failures)
    audit_secrets(failures)

    if failures:
        print("provider model pilot after access audit failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("provider model pilot after access audit: clean pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
