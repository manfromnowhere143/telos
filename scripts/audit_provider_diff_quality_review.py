#!/usr/bin/env python3
"""Audit the iter14 offline provider-diff quality review proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


PROOF = Path("experiments/iter14_provider_diff_quality_review/proof")
RESULT = Path("experiments/iter14_provider_diff_quality_review/RESULT.md")
SUMMARY = PROOF / "run_summary.json"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_provider_diff_quality_review.json"
ITER13_CHANGES = Path(
    "experiments/iter13_provider_model_pilot_retry_after_access_recovery/proof/raw/codeclash/"
    "PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708155545/players/p1/changes_r1.json"
)
ITER13_P2_CHANGES = Path(
    "experiments/iter13_provider_model_pilot_retry_after_access_recovery/proof/raw/codeclash/"
    "PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708155545/players/p2/changes_r1.json"
)
ITER13_TRAJECTORY = Path(
    "experiments/iter13_provider_model_pilot_retry_after_access_recovery/proof/raw/codeclash/"
    "PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708155545/players/p1/p1_r1.traj.json"
)
ITER09_CONFIG = Path(
    "experiments/iter09_provider_model_pilot_smoke/proof/overlay/configs/test/"
    "telos_battlesnake_vertex_gemini_pilot.yaml"
)
ROOT_CONFIG = Path("configs/test/telos_battlesnake_vertex_gemini_pilot.yaml")
ITER15 = Path("experiments/iter15_provider_strict_diff_rerun/HYPOTHESIS.md")
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
        "schema_version": "telos.provider_diff_quality_review.summary.v1",
        "status": "pass",
        "source_experiment": "iter13_provider_model_pilot_retry_after_access_recovery",
        "spend_usd": 0,
        "model_api_calls_made": 0,
        "provider_model_called": False,
        "gpu_used": False,
        "cloud_resources_created": False,
        "production_or_live_domain_changed": False,
        "diff_quality_status": "quality_fail_for_future_clean_pass",
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {data.get(key)!r}")

    reconstruction = data.get("reconstruction", {})
    if set(reconstruction.get("p1_modified_files", [])) != {
        "README_agent.md",
        "main.py",
        "patch.py",
    }:
        failures.append("summary must record exact p1 modified-file set")
    if reconstruction.get("p2_modified_files") != []:
        failures.append("summary must record p2 empty diff")
    for key in [
        "full_diff_contains_is_move_safe",
        "full_diff_contains_main_py",
        "full_diff_contains_patch_py",
    ]:
        if reconstruction.get(key) is not True:
            failures.append(f"summary reconstruction missing {key}")

    judgments = data.get("judgments", {})
    if judgments.get("main_py_boundary_edit_satisfies_local_step1_intent") is not True:
        failures.append("summary must judge main.py boundary edit as satisfying local Step 1 intent")
    if judgments.get("patch_helper_file_should_fail_future_clean_pass") is not True:
        failures.append("summary must make patch.py a future clean-pass failure")
    if judgments.get("readme_agent_allowed_by_prompt") is not True:
        failures.append("summary must distinguish README_agent.md from helper residue")

    prompt = data.get("task_prompt_resolution", {})
    if prompt.get("root_relative_path_exists") is not False:
        failures.append("summary must record root-relative task config as absent")
    if prompt.get("committed_overlay_path_exists") is not True:
        failures.append("summary must record committed overlay task config as present")
    if prompt.get("trajectory_prompt_present") is not True:
        failures.append("summary must record trajectory prompt as present")

    next_bar = data.get("next_bar_decision", {})
    if next_bar.get("future_provider_smoke_requires_diff_quality_status") is not True:
        failures.append("summary must require future diff-quality status")
    if next_bar.get("future_provider_smoke_unjustified_helper_files_fail_clean_pass") is not True:
        failures.append("summary must make unjustified helper files fail clean pass")

    hashes = data.get("artifact_hashes", {})
    expected_hash_paths = {
        "iter09_overlay_task_config": ITER09_CONFIG,
        "iter13_p1_changes": ITER13_CHANGES,
        "iter13_p1_trajectory": ITER13_TRAJECTORY,
        "iter13_run_summary": Path(
            "experiments/iter13_provider_model_pilot_retry_after_access_recovery/proof/run_summary.json"
        ),
    }
    for key, path in expected_hash_paths.items():
        if hashes.get(key) != sha256(path):
            failures.append(f"hash mismatch for {key}")


def audit_source_artifacts(failures: list[str]) -> None:
    for path in [ITER13_CHANGES, ITER13_P2_CHANGES, ITER13_TRAJECTORY, ITER09_CONFIG]:
        if not path.exists():
            failures.append(f"missing source artifact: {path}")
    if ROOT_CONFIG.exists():
        failures.append("root config unexpectedly exists; update iter14 summary if layout changed")

    changes = load_json(ITER13_CHANGES)
    modified_files = set(changes.get("modified_files", {}))
    if modified_files != {"README_agent.md", "main.py", "patch.py"}:
        failures.append(f"reconstructed modified files mismatch: {sorted(modified_files)}")
    diff = changes.get("full_diff", "")
    for required in [
        "diff --git a/main.py",
        "board_width = game_state['board']['width']",
        "is_move_safe[\"left\"] = False",
        "is_move_safe[\"right\"] = False",
        "is_move_safe[\"down\"] = False",
        "is_move_safe[\"up\"] = False",
        "diff --git a/patch.py",
    ]:
        if required not in diff:
            failures.append(f"p1 diff missing required hunk text: {required}")
    if load_json(ITER13_P2_CHANGES).get("full_diff") != "":
        failures.append("p2 diff must remain empty")

    trajectory_text = ITER13_TRAJECTORY.read_text(encoding="utf-8")
    for required in [
        "This is a one-round provider-model smoke test.",
        "The goal is not a leaderboard",
        "README_agent.md",
    ]:
        if required not in trajectory_text:
            failures.append(f"trajectory prompt missing: {required}")

    config_text = ITER09_CONFIG.read_text(encoding="utf-8")
    for required in ["width: 11", "height: 11", "sims_per_round: 1", "rounds: 1"]:
        if required not in config_text:
            failures.append(f"overlay config missing: {required}")


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


def audit_language(failures: list[str]) -> None:
    result = " ".join(RESULT.read_text(encoding="utf-8").split())
    review = " ".join(REVIEW.read_text(encoding="utf-8").split())
    for phrase in [
        "No provider/model/API/GPU spend occurred.",
        "This is an evidence-quality result.",
        "not a leaderboard result",
        "not a SWE-bench result",
        "not a production/live-domain verification",
        "The retained `patch.py` helper should fail future provider-smoke quality gates.",
        "Future provider-smoke receipts need an explicit diff-quality status:",
    ]:
        if phrase not in result and phrase not in review:
            failures.append(f"missing boundary/decision language: {phrase}")
    forbidden_claims = [
        "leaderboard result is claimed",
        "swe-bench result is claimed",
        "production verified",
        "model superiority",
    ]
    lowered = f"{result} {review}".lower()
    for phrase in forbidden_claims:
        if phrase in lowered:
            failures.append(f"forbidden claim phrase present: {phrase}")

    if not ITER15.exists():
        failures.append("next pre-registered gate is missing")
    elif "unjustified helper" not in ITER15.read_text(encoding="utf-8"):
        failures.append("iter15 hypothesis must carry forward the helper-file quality bar")


def audit_secrets(failures: list[str]) -> None:
    checked = 0
    for path in PROOF.rglob("*"):
        if not path.is_file():
            continue
        checked += 1
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"possible secret pattern in {path}")
    if checked == 0:
        failures.append("secret audit checked zero files")


def main() -> int:
    failures: list[str] = []
    audit_summary(failures)
    audit_source_artifacts(failures)
    audit_receipt(failures)
    audit_language(failures)
    audit_secrets(failures)

    if failures:
        print("provider diff quality review audit failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("provider diff quality review audit: clean pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
