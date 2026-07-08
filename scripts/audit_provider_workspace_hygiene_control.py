#!/usr/bin/env python3
"""Audit the iter16 provider workspace-hygiene control proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


PROOF = Path("experiments/iter16_provider_workspace_hygiene_control/proof")
RESULT = Path("experiments/iter16_provider_workspace_hygiene_control/RESULT.md")
SUMMARY = PROOF / "run_summary.json"
PREFLIGHT = PROOF / "preflight.json"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_provider_workspace_hygiene_control.json"
TOURNAMENT = (
    PROOF
    / "raw"
    / "codeclash"
    / "PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708171352"
)
TRAJECTORY = TOURNAMENT / "players" / "p1" / "p1_r1.traj.json"
P1_CHANGES = TOURNAMENT / "players" / "p1" / "changes_r1.json"
P2_CHANGES = TOURNAMENT / "players" / "p2" / "changes_r1.json"
RUN_LOG = PROOF / "raw" / "codeclash" / "telos-codeclash-provider-run.log"
ITER17 = Path("experiments/iter17_provider_lint_hygiene_control/HYPOTHESIS.md")

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
        "schema_version": "telos.provider_workspace_hygiene_control.summary.v1",
        "status": "pass",
        "runner": "ephemeral_gce_vm_dedicated_service_account",
        "service_account_short_id": "telos-vertex-runner",
        "selected_model": "vertex_ai/gemini-3.1-pro-preview-customtools",
        "region": "global",
        "vertex_location_configured_in_model_kwargs": True,
        "workspace_hygiene_instruction_present": True,
        "preflight_status": "pass",
        "preflight_http_status": "200",
        "codeclash_started": True,
        "run_exit_code": 0,
        "p1_trajectory_present": True,
        "p1_agent_exit_status": "Submitted",
        "model_api_calls_reported": 6,
        "model_cost_reported_usd": 0.035064,
        "strict_diff_quality_status": "clean_workspace_hygiene",
        "clean_pass": True,
        "scratch_used_outside_workspace": True,
        "scratch_deleted_before_submission": True,
        "git_status_checked_before_submission": True,
        "style_caveat_trailing_blank_whitespace_in_main_py_diff": True,
        "cloud_vm_deleted": True,
        "raw_binary_round_archive_committed": False,
        "project_identifier_committed": False,
        "credential_material_committed": False,
        "provider_private_fields_redacted": True,
        "production_or_live_domain_changed": False,
        "leaderboard_or_swebench_claimed": False,
        "game_score_used_as_model_capability_evidence": False,
        "next_gate": "experiments/iter17_provider_lint_hygiene_control/HYPOTHESIS.md",
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {data.get(key)!r}")
    if data.get("model_cost_reported_usd", 999) >= 25:
        failures.append("model cost must be below the $25 ceiling")
    if set(data.get("p1_modified_files", [])) != {"README_agent.md", "main.py"}:
        failures.append("summary must record the exact clean p1 modified-file set")
    if data.get("p2_modified_files") != []:
        failures.append("p2 modified files must be empty")
    if data.get("helper_residue_files") != []:
        failures.append("helper residue files must be empty")
    if data.get("git_status_output_before_submission") != [" M main.py", "?? README_agent.md"]:
        failures.append("summary must record the pre-submit git status output")

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
        "schema_version": "telos.iter16.preflight.v1",
        "status": "pass",
        "http_status": "200",
        "selected_model": "gemini-3.1-pro-preview-customtools",
        "candidate_count": 1,
        "usage_metadata_present": True,
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
    if stats.get("instance_cost") != 0.035064:
        failures.append("trajectory instance_cost mismatch")
    if stats.get("api_calls") != 6:
        failures.append("trajectory api_calls mismatch")
    if trajectory.get("info", {}).get("exit_status") != "Submitted":
        failures.append("trajectory exit_status must be Submitted")

    trajectory_text = json.dumps(trajectory, sort_keys=True)
    for required in ["/tmp/patch.py", "rm /tmp/patch.py", "git status --short"]:
        if required not in trajectory_text:
            failures.append(f"trajectory missing hygiene action: {required}")

    metadata = load_json(TOURNAMENT / "metadata.json")
    player_config = metadata["config"]["players"][0]["config"]
    model_kwargs = player_config["model"]["model_kwargs"]
    if model_kwargs.get("vertex_location") != "global":
        failures.append("metadata must show vertex_location=global")
    instance_template = player_config["agent"]["instance_template"]
    for required in [
        "Workspace hygiene control",
        "Use `/tmp` for scratch scripts",
        "git status --short",
    ]:
        if required not in instance_template:
            failures.append(f"metadata prompt missing: {required}")

    changes = load_json(P1_CHANGES)
    modified = set(changes.get("modified_files", {}))
    if modified != {"README_agent.md", "main.py"}:
        failures.append(f"p1 modified-file set is not clean: {sorted(modified)}")
    diff = changes.get("full_diff", "")
    for required in [
        "diff --git a/main.py",
        "diff --git a/README_agent.md",
        "board_width = game_state['board']['width']",
        "is_move_safe[\"left\"] = False",
        "is_move_safe[\"right\"] = False",
        "is_move_safe[\"down\"] = False",
        "is_move_safe[\"up\"] = False",
    ]:
        if required not in diff:
            failures.append(f"p1 diff missing {required}")
    for forbidden in ["diff --git a/patch.py", "diff --git a/patch2.py", "diff --git a/tmp.py"]:
        if forbidden in diff:
            failures.append(f"p1 diff contains helper residue: {forbidden}")
    if not any(line == "+    " for line in diff.splitlines()):
        failures.append("p1 diff must preserve the recorded trailing-whitespace caveat")
    if load_json(P2_CHANGES).get("full_diff") != "":
        failures.append("p2 should have an empty diff")

    log = RUN_LOG.read_text(encoding="utf-8")
    for required in [
        "Committed changes for p1 for round 1",
        "In round 1, the winner is p1.",
        "Agent p1 passed submission validation",
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
    review = " ".join(REVIEW.read_text(encoding="utf-8").split())
    required = [
        "Status: `PASS`",
        "no helper, scratch, cache, generated, or secret-risk file remained",
        "one whitespace-only added blank line",
        "No CodeClash leaderboard result is claimed.",
        "No SWE-bench result is claimed.",
        "No production/live-domain behavior changed.",
        "one-game score is context only",
        "The next gate should keep the workspace-hygiene control and add a source-style",
    ]
    for phrase in required:
        if phrase not in result and phrase not in review:
            failures.append(f"result/review missing boundary: {phrase}")
    if not ITER17.exists():
        failures.append("next pre-registered gate is missing")
    elif "git diff --check" not in ITER17.read_text(encoding="utf-8"):
        failures.append("iter17 hypothesis must carry the lint hygiene control")


def audit_secrets(failures: list[str]) -> None:
    checked = 0
    for path in PROOF.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix == ".gz":
            failures.append(f"binary round archive should not be committed: {path}")
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
        print("provider workspace hygiene control audit failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("provider workspace hygiene control audit: clean workspace pass with style caveat")
    return 0


if __name__ == "__main__":
    sys.exit(main())
