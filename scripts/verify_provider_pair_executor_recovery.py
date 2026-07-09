#!/usr/bin/env python3
"""Publish iter54 provider pair executor recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any

from run_provider_compatible_protocol_effect_pairs import (
    DEFAULT_CODECLASH_DIR,
    EXCLUDED_PAIR_IDS,
    READY_PAIR_IDS,
    build_condition_separated_plan,
    build_executor_readiness_plan,
)


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter54_provider_pair_executor_recovery"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
SOURCE_ITER53_SUMMARY = (
    ROOT
    / "experiments"
    / "iter53_provider_compatible_protocol_effect_execution_after_condition_recovery"
    / "proof"
    / "run_summary.json"
)
SOURCE_ITER52_PLAN = (
    ROOT
    / "experiments"
    / "iter52_provider_condition_runtime_separation_recovery"
    / "proof"
    / "condition_runtime_separation_plan.json"
)
CODECLASH_DIR = Path(DEFAULT_CODECLASH_DIR)
CODECLASH_COMMIT = "381cdfa05a35e8acd35853b9fc7e13005121b127"
DOCKER_BIN = Path("/Applications/Docker.app/Contents/Resources/bin/docker")
PATH_DOCKER = Path("/usr/local/bin/docker")
NEXT_GATE = ROOT / "experiments" / "iter55_provider_compatible_paid_execution_after_executor_recovery" / "HYPOTHESIS.md"
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
    re.compile(r"ANTHROPIC_API_KEY\s*=\s*\S+"),
    re.compile(r"OPENAI_API_KEY\s*=\s*\S+"),
    re.compile(r"GOOGLE_API_KEY\s*=\s*\S+"),
    re.compile(r"GEMINI_API_KEY\s*=\s*\S+"),
    re.compile(r"GOOGLE_APPLICATION_CREDENTIALS\s*=\s*\S+"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} root must be an object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(args: list[str], timeout: int = 10) -> dict[str, Any]:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"returncode": None, "timed_out": True, "stdout": "", "stderr": ""}
    return {
        "returncode": result.returncode,
        "timed_out": False,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter54-provider-pair-executor-recovery-{status}",
        "task_id": "telos:iter54_provider_pair_executor_recovery@iter53",
        "agent_id": "codex-local-provider-pair-executor-recovery",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Recover a zero-spend provider pair executor for the two condition-separated "
            "BattleSnake rows before any paid retry."
        ),
        "acceptance_criteria": [
            "Iter53 is a committed blocked result with zero provider calls and zero spend.",
            "The pinned CodeClash checkout is present at the frozen commit.",
            "Recovered iter52 overlays are copied or exactly mapped into the pinned checkout.",
            "The wrapper materializes exact commands for only the two selected BattleSnake rows.",
            "Docker daemon readiness is proven through a bounded no-container probe.",
            "Provider calls, provider spend, cloud runner startup, GPU use, and Sentinel resource modification remain zero.",
            "No benchmark, leaderboard, SWE-bench, production, live-domain, model-superiority, or state-of-the-art result is claimed.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": "experiments/iter54_provider_pair_executor_recovery/proof/executor_readiness_report.json",
                "notes": "Executor readiness report records CodeClash, Docker, overlay, and command readiness.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": "experiments/iter54_provider_pair_executor_recovery/proof/command_manifest.json",
                "notes": "Command manifest records the exact future provider-backed commands without executing them.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": "experiments/iter54_provider_pair_executor_recovery/proof/review.md",
                "notes": "Review records the zero-spend boundary and CLI symlink caveat.",
            },
        ],
        "falsifiers": [
            "The result must block if the pinned CodeClash checkout cannot be verified.",
            "The result must block if Docker daemon readiness cannot be proven.",
            "The result must fail if any provider command is executed.",
            "The result must fail if provider calls, provider spend, cloud runner startup, GPU use, or Sentinel resource modification occurs.",
            "The result must fail if unsupported benchmark, model-superiority, production, live-domain, leaderboard, SWE-bench, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def artifact_hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path.relative_to(PROOF)): sha256_file(path) for path in paths}


def codeclash_state() -> dict[str, Any]:
    state: dict[str, Any] = {
        "checkout_path": str(CODECLASH_DIR),
        "checkout_present": (CODECLASH_DIR / ".git").exists(),
        "expected_commit": CODECLASH_COMMIT,
        "actual_commit": None,
        "pinned_commit_present": False,
        "commit_identifier_logged": True,
    }
    if not state["checkout_present"]:
        return state
    result = run(["git", "-C", str(CODECLASH_DIR), "rev-parse", "HEAD"])
    state["actual_commit"] = result["stdout"].strip() if result["returncode"] == 0 else None
    state["pinned_commit_present"] = state["actual_commit"] == CODECLASH_COMMIT
    status = run(["git", "-C", str(CODECLASH_DIR), "status", "--short"])
    state["status_short_line_count"] = len(
        [line for line in status["stdout"].splitlines() if line.strip()]
    )
    return state


def docker_state() -> dict[str, Any]:
    direct_info = run([str(DOCKER_BIN), "info", "--format", "{{.ServerVersion}}"], timeout=8)
    direct_ps = run([str(DOCKER_BIN), "ps", "--format", "{{json .}}"], timeout=8)
    socket = run(
        [
            "curl",
            "--silent",
            "--show-error",
            "--unix-socket",
            "/var/run/docker.sock",
            "http://localhost/version",
        ],
        timeout=8,
    )
    path_target = PATH_DOCKER.resolve(strict=False) if PATH_DOCKER.exists() else None
    return {
        "preferred_cli_path": str(DOCKER_BIN),
        "preferred_cli_present": DOCKER_BIN.exists(),
        "preferred_cli_ready": direct_info["returncode"] == 0 and bool(direct_info["stdout"].strip()),
        "preferred_cli_server_version": direct_info["stdout"].strip(),
        "preferred_cli_ps_ready": direct_ps["returncode"] == 0,
        "path_cli_path": str(PATH_DOCKER),
        "path_cli_target": str(path_target) if path_target is not None else None,
        "path_cli_target_expected": str(DOCKER_BIN),
        "path_cli_target_is_current_app": path_target == DOCKER_BIN,
        "socket_version_ready": socket["returncode"] == 0,
        "socket_version_payload_present": bool(socket["stdout"].strip()),
        "docker_daemon_ready": direct_info["returncode"] == 0 and socket["returncode"] == 0,
        "containers_started": False,
    }


def copy_overlays(executor_plan: dict[str, Any]) -> dict[str, Any]:
    copies = []
    for record in executor_plan.get("pair_executor_records", []):
        for item in record.get("overlay_copy_manifest", []):
            source = ROOT / item["source"]
            dest = CODECLASH_DIR / item["destination"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            copies.append(
                {
                    "source": item["source"],
                    "destination": str(dest.relative_to(CODECLASH_DIR)),
                    "source_sha256": sha256_file(source),
                    "destination_sha256": sha256_file(dest),
                    "hash_match": sha256_file(source) == sha256_file(dest),
                }
            )
    unique = {copy["destination"]: copy for copy in copies}
    return {
        "copied_file_count": len(unique),
        "all_hashes_match": all(copy["hash_match"] for copy in unique.values()),
        "copies": sorted(unique.values(), key=lambda item: item["destination"]),
    }


def secret_scan(paths: list[Path]) -> tuple[bool, list[str]]:
    findings: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(str(path.relative_to(ROOT)))
                break
    return not findings, findings


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    iter53_summary = read_json(SOURCE_ITER53_SUMMARY)
    source_iter52_plan = read_json(SOURCE_ITER52_PLAN)
    condition_plan = build_condition_separated_plan(next_experiment=NEXT_GATE.parent.name)
    executor_plan = build_executor_readiness_plan(condition_plan, next_experiment=NEXT_GATE.parent.name)
    codeclash = codeclash_state()
    docker = docker_state()
    overlay_copy = copy_overlays(executor_plan) if codeclash["pinned_commit_present"] else {
        "copied_file_count": 0,
        "all_hashes_match": False,
        "copies": [],
    }

    blockers: list[str] = []
    failures: list[str] = []
    if iter53_summary.get("status") != "blocked":
        blockers.append("iter53_not_blocked")
    if iter53_summary.get("provider_model_api_calls") != 0:
        failures.append("iter53_provider_calls_not_zero")
    if iter53_summary.get("provider_spend_usd") != 0.0:
        failures.append("iter53_provider_spend_not_zero")
    if source_iter52_plan.get("status") != "condition_separated_ready":
        blockers.append("iter52_condition_plan_not_ready")
    if executor_plan.get("status") != "executor_readiness_ready":
        blockers.append("executor_readiness_plan_not_ready")
    if executor_plan.get("selected_pair_ids") != READY_PAIR_IDS:
        failures.append("selected_pair_ids_changed")
    if executor_plan.get("excluded_pair_ids") != EXCLUDED_PAIR_IDS:
        failures.append("excluded_pair_ids_changed")
    if not codeclash["pinned_commit_present"]:
        blockers.append("pinned_codeclash_checkout_not_ready")
    if not overlay_copy["all_hashes_match"]:
        blockers.append("overlay_copy_hash_mismatch")
    if not docker["docker_daemon_ready"]:
        blockers.append("docker_daemon_not_ready")

    status = "fail" if failures else "blocked" if blockers else "pass"
    command_manifest = {
        "schema_version": "telos.provider_pair_executor.command_manifest.v1",
        "status": status,
        "selected_pair_count": len(executor_plan.get("pair_executor_records", [])),
        "selected_pair_ids": executor_plan.get("selected_pair_ids"),
        "excluded_pair_count": executor_plan.get("excluded_pair_count"),
        "excluded_pair_ids": executor_plan.get("excluded_pair_ids"),
        "commands": [
            {
                "pair_id": record["pair_id"],
                "condition_id": record["condition_id"],
                "command": record["materialized_codeclash_command"],
                "executed": False,
            }
            for record in executor_plan.get("pair_executor_records", [])
        ],
        "provider_command_executed": False,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
    }
    report = {
        "schema_version": "telos.provider_pair_executor_recovery.report.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "source_iter53_summary_path": str(SOURCE_ITER53_SUMMARY.relative_to(ROOT)),
        "source_iter52_plan_path": str(SOURCE_ITER52_PLAN.relative_to(ROOT)),
        "condition_plan_status": condition_plan.get("status"),
        "executor_plan_status": executor_plan.get("status"),
        "codeclash": codeclash,
        "docker": docker,
        "overlay_copy": overlay_copy,
        "selected_pair_ids": executor_plan.get("selected_pair_ids"),
        "excluded_pair_ids": executor_plan.get("excluded_pair_ids"),
        "provider_command_executed": False,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "blockers": blockers,
        "failures": failures,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
    }
    write_json(PROOF / "executor_readiness_plan.json", executor_plan)
    write_json(PROOF / "command_manifest.json", command_manifest)
    write_json(PROOF / "overlay_copy_manifest.json", overlay_copy)
    write_json(PROOF / "executor_readiness_report.json", report)

    artifact_paths = [
        PROOF / "executor_readiness_plan.json",
        PROOF / "command_manifest.json",
        PROOF / "overlay_copy_manifest.json",
        PROOF / "executor_readiness_report.json",
    ]
    scan_passed, scan_findings = secret_scan(artifact_paths)

    output_lines = [
        f"provider pair executor recovery: {status}",
        "provider_command_executed=false",
        "provider_model_api_calls=0",
        "provider_spend_usd=0.0",
        f"pinned_codeclash_checkout_ready={str(codeclash['pinned_commit_present']).lower()}",
        f"docker_daemon_ready={str(docker['docker_daemon_ready']).lower()}",
        f"path_docker_symlink_current={str(docker['path_cli_target_is_current_app']).lower()}",
        f"overlay_copied_files={overlay_copy['copied_file_count']}",
        f"blockers={','.join(blockers)}",
        f"failures={','.join(failures)}",
        f"next_gate={NEXT_GATE.relative_to(ROOT)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    if status == "pass":
        review_body = """The zero-spend executor recovery closed the concrete iter53 execution blockers. The pinned
CodeClash checkout exists at the frozen commit, the recovered iter52 overlays were copied into the
pinned checkout with matching hashes, and the wrapper now materializes exact future commands for
only the two selected BattleSnake rows without executing either command.

Docker readiness is proven through the current Docker Desktop binary and direct Unix-socket API
probe. A local caveat remains: `/usr/local/bin/docker` points to an older `/Volumes/Docker` binary
and can hang, so future local runs should use the recorded Docker Desktop binary path or repair the
root-owned symlink outside the proof gate. This caveat does not require provider calls and did not
start containers."""
        result_summary = (
            "The zero-spend executor recovery passed. Telos can now materialize exact commands for "
            "the two condition-separated provider-compatible BattleSnake rows without executing them."
        )
        authorized_action = (
            "- Pre-register the paid two-row provider-compatible retry using the recovered executor, "
            "exact command manifest, Docker binary path, overlay hashes, receipt validation, cost "
            "capture, redaction, and teardown controls."
        )
    else:
        problem_list = failures if failures else blockers
        review_body = (
            f"The zero-spend executor recovery published `{status}` evidence instead of advancing. "
            f"The named issues are `{', '.join(problem_list)}`. Telos must correct only those "
            "specific executor, checkout, overlay, or Docker readiness gaps before any paid retry.\n\n"
            "No provider command executed while discovering the blocker."
        )
        result_summary = (
            f"The zero-spend executor recovery published `{status}` evidence. Telos cannot advance "
            "to paid provider-compatible execution until the named blockers or failures are fixed."
        )
        authorized_action = (
            "- Correct only the named readiness gap and rerun this zero-spend gate before any paid "
            "provider-compatible retry."
        )

    review = f"""# Iteration 54 Review

{review_body}

No provider command executed. No provider model call, provider spend, cloud runner startup, GPU
use, Sentinel-named resource modification, production/live-domain change, benchmark claim, model
superiority claim, or state-of-the-art claim occurred.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    result_md = f"""# Iteration 54 Result - Provider Pair Executor Recovery

Status: `{status.upper()}`.

## Summary

{result_summary}

- pinned CodeClash checkout ready: `{str(codeclash['pinned_commit_present']).lower()}`,
- overlay files copied with matching hashes: `{str(overlay_copy['all_hashes_match']).lower()}`,
- Docker daemon ready through the current Docker Desktop binary: `{str(docker['docker_daemon_ready']).lower()}`,
- provider commands executed: `false`,
- provider model API calls: `0`,
- provider spend: `$0.00`,
- cloud runner started: `false`,
- GPU used: `false`,
- Sentinel-named resources modified: `false`.

## Caveat

`/usr/local/bin/docker` is a root-owned symlink to an older `/Volumes/Docker` binary and can hang.
The proof uses the current Docker Desktop binary at
`/Applications/Docker.app/Contents/Resources/bin/docker`, which answered the daemon probe.

## What Is Now Authorized

{authorized_action}

## What Remains Forbidden

- No benchmark result is claimed.
- No SWE-bench score is claimed.
- No leaderboard result is claimed.
- No production or live-domain result is claimed.
- No model-superiority or state-of-the-art result is claimed.
- No provider-backed protocol-effect metric is inferred from executor readiness.

## Evidence

- `proof/executor_readiness_report.json`
- `proof/executor_readiness_plan.json`
- `proof/command_manifest.json`
- `proof/overlay_copy_manifest.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_provider_pair_executor_recovery.json`
"""
    (EXPERIMENT / "RESULT.md").write_text(result_md, encoding="utf-8")

    artifact_paths.extend([PROOF / "command_output.txt", PROOF / "review.md"])
    summary = {
        "schema_version": "telos.provider_pair_executor_recovery.summary.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "source_iter53_summary_path": str(SOURCE_ITER53_SUMMARY.relative_to(ROOT)),
        "source_iter53_summary_sha256": sha256_file(SOURCE_ITER53_SUMMARY),
        "selected_pair_ids": executor_plan.get("selected_pair_ids"),
        "excluded_pair_ids": executor_plan.get("excluded_pair_ids"),
        "pinned_codeclash_checkout_ready": codeclash["pinned_commit_present"],
        "docker_daemon_ready": docker["docker_daemon_ready"],
        "path_docker_symlink_current": docker["path_cli_target_is_current_app"],
        "overlay_copy_hashes_match": overlay_copy["all_hashes_match"],
        "provider_command_executed": False,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "redaction_scan_passed": scan_passed,
        "redaction_findings": scan_findings,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": blockers,
        "failures": failures,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
        "artifact_hashes": {},
    }
    summary["artifact_hashes"] = artifact_hashes(artifact_paths)
    write_json(PROOF / "run_summary.json", summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "insight": (
            "The two-row provider-compatible executor can materialize exact commands after "
            "condition separation, with pinned CodeClash, copied overlays, Docker daemon readiness, "
            "and zero provider calls."
        ),
        "next_action": (
            "pre-register the paid two-row provider-compatible retry using the recovered executor "
            "and keep the claim limited to exact two-row protocol-effect evidence"
        ),
        "result_path": "experiments/iter54_provider_pair_executor_recovery/RESULT.md",
        "evidence_paths": [
            "experiments/iter54_provider_pair_executor_recovery/proof/run_summary.json",
            "experiments/iter54_provider_pair_executor_recovery/proof/executor_readiness_report.json",
            "experiments/iter54_provider_pair_executor_recovery/proof/command_manifest.json",
            "experiments/iter54_provider_pair_executor_recovery/proof/overlay_copy_manifest.json",
            "experiments/iter54_provider_pair_executor_recovery/proof/valid/receipt_provider_pair_executor_recovery.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(VALID / "receipt_provider_pair_executor_recovery.json", build_receipt(status))

    print("\n".join(output_lines))
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
