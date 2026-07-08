#!/usr/bin/env python3
"""Audit the iter21 provider opponent-collision control proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter21_opponent_collision_control")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
PREFLIGHT = PROOF / "preflight.json"
RAW_SUMMARY = PROOF / "raw_summary.json"
REPORT = PROOF / "semantic_report.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_opponent_collision_control.json"
TOURNAMENT = (
    PROOF
    / "raw"
    / "codeclash"
    / "PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708192510"
)
CHANGES = TOURNAMENT / "players" / "p1" / "changes_r1.json"
TRAJECTORY = TOURNAMENT / "players" / "p1" / "p1_r1.traj.json"
RECONSTRUCTED_MAIN = PROOF / "reconstructed" / "main.py"
RECONSTRUCTED_README = PROOF / "reconstructed" / "README_agent.md"
ITER22 = Path("experiments/iter22_semantic_mutation_guard/HYPOTHESIS.md")

EXPECTED_CASES = {
    "boundary-left": ("left", ["up", "down"]),
    "boundary-right": ("right", ["up", "down"]),
    "boundary-down": ("down", ["left", "right"]),
    "boundary-up": ("up", ["left", "right"]),
    "self-left": ("left", ["up", "right"]),
    "self-right": ("right", ["up", "left"]),
    "self-down": ("down", ["up", "right"]),
    "self-up": ("up", ["down", "right"]),
    "opponent-left": ("left", ["up", "right"]),
    "opponent-right": ("right", ["up", "left"]),
    "opponent-down": ("down", ["up", "right"]),
    "opponent-up": ("up", ["down", "right"]),
}

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
    re.compile(
        r"thought_signature['\"]?\\s*[:=]\\s*['\"]"
        r"(?!<redacted-provider-thought-signature>)"
    ),
]


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be an object")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command_sequence(trajectory: dict) -> list[str]:
    commands: list[str] = []
    for message in trajectory.get("messages", []):
        for call in message.get("tool_calls", []) or []:
            function = call.get("function", {})
            if function.get("name") != "bash":
                continue
            try:
                args = json.loads(function.get("arguments", "{}"))
            except json.JSONDecodeError:
                continue
            command = args.get("command")
            if isinstance(command, str):
                commands.append(command)
    return commands


def audit_summary(failures: list[str]) -> None:
    data = load_json(SUMMARY)
    expected = {
        "schema_version": "telos.opponent_collision_control.summary.v1",
        "status": "pass",
        "experiment_id": "iter21_opponent_collision_control",
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
        "model_api_calls_reported": 5,
        "model_cost_reported_usd": 0.043329999999999994,
        "scratch_used_outside_workspace": True,
        "scratch_deleted_or_not_committed": True,
        "git_status_checked_before_submission": True,
        "git_diff_check_run_before_submission": True,
        "git_diff_check_first_failed_then_fixed": True,
        "final_inspection_before_submission": True,
        "final_inspection_returncode": 0,
        "changed_files_reconstructable": True,
        "boundary_check_observed": True,
        "self_collision_prevention_observed": True,
        "opponent_collision_prevention_observed": True,
        "implementation_excludes_tails": True,
        "semantic_case_count": 12,
        "semantic_cases_passed": 12,
        "semantic_cases_failed": 0,
        "boundary_cases_passed": True,
        "self_collision_cases_passed": True,
        "opponent_collision_cases_passed": True,
        "remote_redaction_placeholder_json_repaired": True,
        "cloud_vm_deleted": True,
        "raw_binary_round_archive_committed": False,
        "project_identifier_committed": False,
        "credential_material_committed": False,
        "provider_private_fields_redacted": True,
        "production_or_live_domain_changed": False,
        "leaderboard_or_swebench_claimed": False,
        "game_score_used_as_model_capability_evidence": False,
        "clean_pass": True,
        "next_gate": ITER22.as_posix(),
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {data.get(key)!r}")
    if data.get("p1_modified_files") != ["README_agent.md", "main.py"]:
        failures.append("summary p1_modified_files must be README_agent.md and main.py")
    if data.get("p2_modified_files") != []:
        failures.append("summary p2_modified_files must be empty")
    if data.get("helper_residue_files") != []:
        failures.append("summary helper_residue_files must be empty")
    if data.get("final_inspection_output") != [" M main.py", "?? README_agent.md"]:
        failures.append("summary final inspection output mismatch")

    hashes = data.get("artifact_hashes", {})
    if not isinstance(hashes, dict) or not hashes:
        failures.append("summary artifact_hashes must be non-empty")
        return
    for rel_path, expected_hash in hashes.items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"hashed artifact missing: {rel_path}")
            continue
        actual_hash = sha256(path)
        if actual_hash != expected_hash:
            failures.append(f"hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}")


def audit_preflight_and_raw(failures: list[str]) -> None:
    preflight = load_json(PREFLIGHT)
    expected_preflight = {
        "schema_version": "telos.iter21.preflight.v1",
        "status": "pass",
        "http_status": "200",
        "selected_model": "gemini-3.1-pro-preview-customtools",
        "candidate_count": 1,
        "usage_metadata_present": True,
        "credential_material_logged": False,
        "project_identifier_logged": False,
        "account_identifier_logged": False,
    }
    for key, value in expected_preflight.items():
        if preflight.get(key) != value:
            failures.append(f"preflight {key} expected {value!r}, got {preflight.get(key)!r}")

    raw = load_json(RAW_SUMMARY)
    if raw.get("schema_version") != "telos.iter21.raw_summary.v1":
        failures.append("raw summary schema mismatch")
    if raw.get("run_exit_code") != 0 or raw.get("p1_exit_status") != "Submitted":
        failures.append("raw summary must record successful p1 submission")
    if raw.get("p1_model_stats", {}).get("api_calls") != 5:
        failures.append("raw summary p1 api call count mismatch")
    if raw.get("p1_modified_files") != ["README_agent.md", "main.py"]:
        failures.append("raw summary p1 modified files mismatch")
    if raw.get("p2_modified_files") != []:
        failures.append("raw summary p2 modified files must be empty")


def audit_diff_and_trajectory(failures: list[str]) -> None:
    changes = load_json(CHANGES)
    modified_files = changes.get("modified_files", {})
    if set(modified_files) != {"README_agent.md", "main.py"}:
        failures.append("changes modified_files set mismatch")
    if RECONSTRUCTED_MAIN.read_text(encoding="utf-8") != modified_files.get("main.py"):
        failures.append("reconstructed main.py mismatch")
    if RECONSTRUCTED_README.read_text(encoding="utf-8") != modified_files.get("README_agent.md"):
        failures.append("reconstructed README_agent.md mismatch")

    diff = changes.get("full_diff", "")
    for required in [
        "possible_moves = {",
        "next_pos in my_body[:-1]",
        "for snake in opponents:",
        "next_pos in snake['body'][:-1]",
    ]:
        if required not in diff:
            failures.append(f"submitted diff missing: {required}")

    trajectory = load_json(TRAJECTORY)
    stats = trajectory.get("info", {}).get("model_stats", {})
    if stats.get("api_calls") != 5:
        failures.append("trajectory api call count mismatch")
    if stats.get("instance_cost") != 0.043329999999999994:
        failures.append("trajectory cost mismatch")
    if trajectory.get("info", {}).get("exit_status") != "Submitted":
        failures.append("trajectory exit status must be Submitted")

    commands = command_sequence(trajectory)
    joined = "\n".join(commands)
    for required in [
        "/tmp/edit.py",
        "git status --short && git diff --check",
        "sed -i",
        "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT",
    ]:
        if required not in joined:
            failures.append(f"trajectory missing command evidence: {required}")
    submit_idx = next((idx for idx, command in enumerate(commands) if "COMPLETE_TASK" in command), -1)
    final_idx = max(
        (idx for idx, command in enumerate(commands) if "git status --short && git diff --check" in command),
        default=-1,
    )
    if not (0 <= final_idx < submit_idx):
        failures.append("final inspection must occur before submission")

    trajectory_text = json.dumps(trajectory, sort_keys=True)
    for required in [
        "main.py:81: trailing whitespace.",
        "<returncode>0</returncode>\\n<output>\\n M main.py\\n?? README_agent.md\\n</output>",
        "<redacted-provider-thought-signature>",
    ]:
        if required not in trajectory_text:
            failures.append(f"trajectory missing evidence: {required}")


def audit_semantics(failures: list[str]) -> None:
    report = load_json(REPORT)
    expected = {
        "schema_version": "telos.opponent_collision_semantic_report.v1",
        "status": "pass",
        "reconstructed_from_modified_files": True,
        "module_imported": True,
        "random_choice_probe_used": True,
        "submitted_logic_mutated": False,
        "provider_api_calls_for_semantic_verification": 0,
        "cloud_or_gpu_used_for_semantic_verification": False,
        "case_count": 12,
        "passed_case_count": 12,
        "failed_case_count": 0,
    }
    for key, value in expected.items():
        if report.get(key) != value:
            failures.append(f"semantic report {key} expected {value!r}, got {report.get(key)!r}")
    cases = report.get("cases")
    if not isinstance(cases, list) or len(cases) != len(EXPECTED_CASES):
        failures.append("semantic report must contain twelve cases")
        return
    seen = set()
    for case in cases:
        case_id = case.get("case_id")
        if case_id not in EXPECTED_CASES:
            failures.append(f"unexpected semantic case: {case_id!r}")
            continue
        seen.add(case_id)
        forbidden, expected_safe = EXPECTED_CASES[case_id]
        if case.get("forbidden_move") != forbidden:
            failures.append(f"{case_id}: forbidden move mismatch")
        if case.get("observed_safe_moves") != expected_safe:
            failures.append(f"{case_id}: observed safe moves mismatch")
        if case.get("selected_move") == forbidden:
            failures.append(f"{case_id}: selected forbidden move")
        if forbidden in case.get("observed_safe_moves", []):
            failures.append(f"{case_id}: forbidden move remained safe")
        if case.get("passed") is not True:
            failures.append(f"{case_id}: case did not pass")
    missing = set(EXPECTED_CASES) - seen
    if missing:
        failures.append(f"missing semantic cases: {sorted(missing)}")


def audit_text_and_receipt(failures: list[str]) -> None:
    output = COMMAND_OUTPUT.read_text(encoding="utf-8")
    for required in [
        "opponent collision semantic verification: pass",
        "cases=12 passed=12 failed=0",
        "opponent-up: pass forbidden=up safe=down,right",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`",
        "All twelve deterministic semantic cases passed",
        "does not claim a CodeClash leaderboard result",
        "does not claim a SWE-bench result",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in ["redaction-placeholder JSON repair", "excludes tails", "All twelve"]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.receipt_id != "iter21-opponent-collision-control-pass":
        failures.append("unexpected receipt id")
    if receipt.status != "pass":
        failures.append("receipt status must be pass")


def audit_no_residue_or_secrets(failures: list[str]) -> None:
    for path in PROOF.rglob("*"):
        if not path.is_file():
            continue
        if path.name.endswith((".tar.gz", ".zip", ".tar", ".pyc")) or "__pycache__" in path.parts:
            failures.append(f"forbidden generated/binary artifact committed: {path}")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"secret-risk pattern found in {path}: {pattern.pattern}")
                break


def main() -> int:
    failures: list[str] = []
    for path in [
        RESULT,
        SUMMARY,
        PREFLIGHT,
        RAW_SUMMARY,
        REPORT,
        COMMAND_OUTPUT,
        REVIEW,
        RECEIPT,
        CHANGES,
        TRAJECTORY,
        RECONSTRUCTED_MAIN,
        RECONSTRUCTED_README,
        ITER22,
    ]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_summary(failures)
        audit_preflight_and_raw(failures)
        audit_diff_and_trajectory(failures)
        audit_semantics(failures)
        audit_text_and_receipt(failures)
        audit_no_residue_or_secrets(failures)

    if failures:
        print("opponent collision control audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("opponent collision control audit: clean semantic pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
