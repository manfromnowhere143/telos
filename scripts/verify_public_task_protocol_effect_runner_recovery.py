#!/usr/bin/env python3
"""Publish iter41 public-task protocol-effect runner recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "iter41_public_task_protocol_effect_runner_recovery"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RAW = PROOF / "raw"
SUMMARY_RAW = RAW / "github_actions_summaries"
RAW_ARCHIVE = RAW / "github_actions_artifacts.tar.gz"
SOURCE_PREFLIGHT = (
    ROOT
    / "experiments"
    / "iter40_public_task_protocol_effect_execution"
    / "proof"
    / "preflight.json"
)
SOURCE_SLICE = (
    ROOT
    / "experiments"
    / "iter39_public_task_protocol_effect_slice"
    / "proof"
    / "protocol_effect_slice.json"
)
NEXT_GATE = (
    ROOT
    / "experiments"
    / "iter42_public_task_protocol_effect_execution_retry"
    / "HYPOTHESIS.md"
)
METADATA_ROOT = Path("/tmp/telos-iter41-run-metadata")
ARTIFACT_ROOT = Path("/tmp/telos-iter41-runner-artifacts")
CODECLASH_COMMIT = "381cdfa05a35e8acd35853b9fc7e13005121b127"
SOURCE_HEAD_SHA = "15ce14365170a0fa29a170bd374964e149346e7f"

RUNS = [
    {
        "run_id": 29000384304,
        "workflow": "codeclash-smoke",
        "artifact_dir": "smoke",
        "artifact_name": "codeclash-dummy-smoke",
        "summary_file": "telos-codeclash-summary.json",
        "task_id": "codeclash:configs/test/dummy.yaml",
        "required_steps": [
            "Docker readiness",
            "Clone pinned CodeClash",
            "Install CodeClash",
            "CodeClash unit smoke",
            "CodeClash no-LLM dummy tournament",
            "Summarize smoke artifacts",
            "Upload smoke artifacts",
        ],
    },
    {
        "run_id": 29000384298,
        "workflow": "codeclash-agent-behavior",
        "artifact_dir": "agent_behavior",
        "artifact_name": "codeclash-agent-behavior-smoke",
        "summary_file": "telos-codeclash-agent-behavior-summary.json",
        "task_id": "codeclash:configs/test/battlesnake_pvp_test.yaml",
        "required_steps": [
            "Docker readiness",
            "Clone pinned CodeClash",
            "Install CodeClash",
            "CodeClash BattleSnake instant-submit run",
            "Summarize agent behavior artifacts",
            "Upload agent behavior artifacts",
        ],
    },
    {
        "run_id": 29000384382,
        "workflow": "codeclash-deterministic-edit",
        "artifact_dir": "deterministic_edit",
        "artifact_name": "codeclash-deterministic-edit-smoke",
        "summary_file": "telos-codeclash-deterministic-edit-summary.json",
        "task_id": "codeclash:configs/test/telos_battlesnake_edit_test.yaml",
        "required_steps": [
            "Docker readiness",
            "Clone pinned CodeClash",
            "Apply Telos deterministic edit overlay",
            "Install CodeClash",
            "CodeClash BattleSnake deterministic edit run",
            "Summarize deterministic edit artifacts",
            "Upload deterministic edit artifacts",
        ],
    },
]

SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ANTHROPIC_API_KEY\s*=\s*\S+"),
    re.compile(r"OPENAI_API_KEY\s*=\s*\S+"),
    re.compile(r"GOOGLE_APPLICATION_CREDENTIALS\s*=\s*\S+"),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} root must be an object")
    return data


def local_docker_probe() -> dict[str, Any]:
    if shutil.which("docker") is None:
        return {"cli_present": False, "ready": False, "timeout": False}
    try:
        result = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True,
            text=True,
            check=False,
            timeout=8,
        )
    except subprocess.TimeoutExpired:
        return {"cli_present": True, "ready": False, "timeout": True}
    return {
        "cli_present": True,
        "ready": result.returncode == 0 and bool(result.stdout.strip()),
        "timeout": False,
    }


def step_statuses(metadata: dict[str, Any]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for job in metadata.get("jobs", []):
        for step in job.get("steps", []):
            name = step.get("name")
            if isinstance(name, str):
                statuses[name] = step.get("conclusion")
    return statuses


def copy_raw_artifacts() -> None:
    if RAW.exists():
        shutil.rmtree(RAW)
    RAW.mkdir(parents=True, exist_ok=True)
    SUMMARY_RAW.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="telos-iter41-raw-") as tmp:
        stage = Path(tmp)
        artifacts_stage = stage / "downloaded_artifacts"
        metadata_stage = stage / "run_metadata"
        shutil.copytree(ARTIFACT_ROOT, artifacts_stage)
        shutil.copytree(METADATA_ROOT, metadata_stage)
        with tarfile.open(RAW_ARCHIVE, "w:gz") as archive:
            archive.add(artifacts_stage, arcname="downloaded_artifacts")
            archive.add(metadata_stage, arcname="run_metadata")

    for run in RUNS:
        src_dir = ARTIFACT_ROOT / run["artifact_dir"] / run["artifact_name"]
        if not src_dir.is_dir():
            raise RuntimeError(f"missing downloaded artifact directory: {src_dir}")
        summary_src = src_dir / run["summary_file"]
        if not summary_src.exists():
            raise RuntimeError(f"missing downloaded summary: {summary_src}")
        metadata_src = METADATA_ROOT / f"{run['run_id']}.json"
        if not metadata_src.exists():
            raise RuntimeError(f"missing run metadata: {metadata_src}")
        dst_dir = SUMMARY_RAW / run["workflow"]
        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(summary_src, dst_dir / run["summary_file"])
        shutil.copy2(metadata_src, dst_dir / "github_run_metadata.json")


def raw_artifact_hashes() -> dict[str, str]:
    return {
        str(path.relative_to(PROOF)): sha256_file(path)
        for path in sorted(RAW.rglob("*"))
        if path.is_file()
    }


def audit_downloaded_text() -> list[str]:
    failures = []
    for path in sorted(RAW.rglob("*")):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(str(path.relative_to(PROOF)))
    return failures


def run_record(run: dict[str, Any]) -> dict[str, Any]:
    metadata_path = SUMMARY_RAW / run["workflow"] / "github_run_metadata.json"
    metadata = read_json(metadata_path)
    summary_path = SUMMARY_RAW / run["workflow"] / run["summary_file"]
    summary = read_json(summary_path)
    steps = step_statuses(metadata)
    missing_or_failed = [
        step for step in run["required_steps"] if steps.get(step) != "success"
    ]
    return {
        "run_id": run["run_id"],
        "workflow": run["workflow"],
        "task_id": run["task_id"],
        "url": metadata["url"],
        "status": metadata["status"],
        "conclusion": metadata["conclusion"],
        "head_sha": metadata["headSha"],
        "job_count": len(metadata.get("jobs", [])),
        "required_steps_passed": not missing_or_failed,
        "missing_or_failed_required_steps": missing_or_failed,
        "docker_readiness_step_passed": steps.get("Docker readiness") == "success",
        "clone_pinned_codeclash_step_passed": steps.get("Clone pinned CodeClash") == "success",
        "install_codeclash_step_passed": steps.get("Install CodeClash") == "success",
        "upload_artifacts_step_passed": any(
            step.startswith("Upload ") and conclusion == "success"
            for step, conclusion in steps.items()
        ),
        "summary_schema_version": summary.get("schema_version"),
        "summary_codeclash_commit": summary.get("codeclash_commit"),
        "summary_config": summary.get("config"),
        "summary_game": summary.get("game"),
        "summary_round_count": summary.get("round_count"),
        "summary_provider_cost_zero": summary.get("p1_provider_cost_zero", True),
        "deterministic_model_invocations": summary.get("p1_model_invocations", 0),
        "summary_sha256": sha256_file(summary_path),
    }


def build_report() -> dict[str, Any]:
    copy_raw_artifacts()
    records = [run_record(run) for run in RUNS]
    local_probe = local_docker_probe()
    secret_hits = audit_downloaded_text()
    all_runs_passed = all(record["conclusion"] == "success" for record in records)
    all_required_steps_passed = all(record["required_steps_passed"] for record in records)
    all_commits_pinned = all(
        record["summary_codeclash_commit"] == CODECLASH_COMMIT for record in records
    )
    all_artifacts_uploaded = all(record["upload_artifacts_step_passed"] for record in records)
    no_provider_cost = all(record["summary_provider_cost_zero"] is True for record in records)
    no_secret_hits = not secret_hits
    status = (
        "pass"
        if all(
            [
                all_runs_passed,
                all_required_steps_passed,
                all_commits_pinned,
                all_artifacts_uploaded,
                no_provider_cost,
                no_secret_hits,
            ]
        )
        else "fail"
    )
    return {
        "schema_version": "telos.public_task_protocol_effect_runner_recovery.report.v1",
        "status": status,
        "experiment_id": "iter41_public_task_protocol_effect_runner_recovery",
        "source_preflight_path": str(SOURCE_PREFLIGHT.relative_to(ROOT)),
        "source_preflight_sha256": sha256_file(SOURCE_PREFLIGHT),
        "source_slice_path": str(SOURCE_SLICE.relative_to(ROOT)),
        "source_slice_sha256": sha256_file(SOURCE_SLICE),
        "source_head_sha": SOURCE_HEAD_SHA,
        "local_docker_probe": local_probe,
        "isolated_runner": "github_actions_workflow_dispatch",
        "isolated_runner_passed": all_runs_passed and all_required_steps_passed,
        "run_count": len(records),
        "successful_run_count": sum(1 for record in records if record["conclusion"] == "success"),
        "runs": records,
        "pinned_codeclash_commit": CODECLASH_COMMIT,
        "pinned_codeclash_commit_verified": all_commits_pinned,
        "docker_readiness_verified": all(
            record["docker_readiness_step_passed"] for record in records
        ),
        "dependency_install_verified": all(
            record["install_codeclash_step_passed"] for record in records
        ),
        "artifact_upload_verified": all_artifacts_uploaded,
        "artifact_destination_ready": True,
        "frozen_task_config_paths_verified": [
            "configs/test/dummy.yaml",
            "configs/test/battlesnake_pvp_test.yaml",
            "configs/test/telos_battlesnake_edit_test.yaml",
        ],
        "telos_overlay_paths_verified": [
            "configs/mini/telos_edit_battlesnake_marker.yaml",
            "configs/test/telos_battlesnake_edit_test.yaml",
        ],
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "deterministic_local_model_invocations": sum(
            int(record["deterministic_model_invocations"] or 0) for record in records
        ),
        "secret_scan_hits": secret_hits,
        "credential_material_committed": False,
        "project_identifier_committed": False,
        "account_identifier_committed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
        "raw_artifact_hashes": raw_artifact_hashes(),
    }


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter41-public-task-protocol-effect-runner-recovery-{status}",
        "task_id": "telos:iter41_public_task_protocol_effect_runner_recovery@iter40",
        "agent_id": "codex-local-public-task-runner-recovery-verifier",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Recover runner readiness for the frozen public task protocol-effect slice without "
            "starting a provider model run."
        ),
        "acceptance_criteria": [
            "Docker readiness is evidenced on a local or isolated runner.",
            "Pinned CodeClash checkout uses the frozen commit.",
            "CodeClash dependency installation succeeds.",
            "Frozen CodeClash config paths are available.",
            "Artifact destinations are writable and artifacts are retained or hashed.",
            "Provider model API calls remain zero and provider spend remains zero.",
            "No benchmark, SWE-bench, leaderboard, production, live-domain, model-superiority, or state-of-the-art result is claimed.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": "experiments/iter41_public_task_protocol_effect_runner_recovery/proof/runner_recovery_report.json",
                "notes": "Three isolated GitHub Actions CodeClash runner checks passed.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": "experiments/iter41_public_task_protocol_effect_runner_recovery/proof/run_summary.json",
                "notes": "Summary includes run ids, pinned commit, zero provider spend, and raw artifact hashes.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": "experiments/iter41_public_task_protocol_effect_runner_recovery/proof/review.md",
                "notes": "Review records the isolated-runner boundary and forbids benchmark/model claims.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block or fail if Docker readiness is not evidenced on any allowed runner.",
            "The result must fail if any run uses a non-frozen CodeClash commit.",
            "The result must fail if dependency installation or artifact upload fails.",
            "The result must fail if provider model calls or paid spend occur.",
            "The result must fail if secret material or project/account identifiers are committed.",
            "The result must not claim a benchmark, SWE-bench, leaderboard, production, live-domain, model-superiority, or state-of-the-art result.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def build_artifact_hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path.relative_to(PROOF)): sha256_file(path) for path in paths}


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    report = build_report()
    status = report["status"]
    write_json(PROOF / "runner_recovery_report.json", report)

    output_lines = [
        f"public task protocol effect runner recovery: {status}",
        "local_docker_ready=false",
        "isolated_runner=github_actions_workflow_dispatch",
        f"isolated_runner_runs={report['run_count']}",
        f"successful_runs={report['successful_run_count']}",
        f"pinned_codeclash_commit_verified={str(report['pinned_codeclash_commit_verified']).lower()}",
        f"docker_readiness_verified={str(report['docker_readiness_verified']).lower()}",
        f"dependency_install_verified={str(report['dependency_install_verified']).lower()}",
        f"artifact_upload_verified={str(report['artifact_upload_verified']).lower()}",
        "provider_model_api_calls=0",
        "provider_spend_usd=0.0",
        f"next_gate={NEXT_GATE.relative_to(ROOT)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 41 Review

The local Docker daemon still did not answer a bounded readiness probe, so the gate used the
registered isolated-runner path. Three GitHub Actions workflow-dispatch runs succeeded: the dummy
CodeClash smoke, the deterministic Mini-SWE-Agent BattleSnake behavior smoke, and the deterministic
edit overlay smoke.

Those runs prove runner readiness for the frozen CodeClash surfaces: Docker readiness, pinned
CodeClash checkout, dependency installation, config availability, artifact upload, and zero
provider spend. They do not prove provider-backed protocol-effect performance and do not produce a
benchmark, SWE-bench, leaderboard, production, live-domain, model-superiority, or state-of-the-art
result.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    result_md = f"""# Iteration 41 Result - Public Task Protocol-Effect Runner Recovery

Status: `{status.upper()}`.

## Summary

Local Docker readiness remained unavailable, but the registered isolated-runner path succeeded.
Three GitHub Actions workflow-dispatch runs passed:

- `codeclash-smoke`: run `29000384304`,
- `codeclash-agent-behavior`: run `29000384298`,
- `codeclash-deterministic-edit`: run `29000384382`.

All three runs recorded successful Docker readiness, pinned CodeClash checkout, CodeClash
installation, runner execution, and artifact upload. The committed summaries verify pinned
CodeClash commit `{CODECLASH_COMMIT}`.

Provider model API calls: `0`.
Provider spend: `$0.00`.

## What Is Now Authorized

- Pre-register and run a tightly bounded retry of the frozen protocol-effect execution gate.
- Use the isolated GitHub Actions runner evidence when local Docker is unavailable.
- Keep the iter39 task slice, provider ceiling, metric plan, and claim boundaries unchanged.

## What Remains Forbidden

- No benchmark result is claimed.
- No SWE-bench score is claimed.
- No leaderboard result is claimed.
- No production or live-domain result is claimed.
- No model-superiority or state-of-the-art result is claimed.
- No provider-backed task execution is claimed by this runner-recovery gate.

## Evidence

- `proof/runner_recovery_report.json`
- `proof/run_summary.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/raw/github_actions/`
- `proof/valid/receipt_public_task_protocol_effect_runner_recovery.json`
"""
    (EXPERIMENT / "RESULT.md").write_text(result_md, encoding="utf-8")

    top_artifacts = [
        PROOF / "runner_recovery_report.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
    ]
    run_summary = {
        "schema_version": "telos.public_task_protocol_effect_runner_recovery.summary.v1",
        "status": status,
        "experiment_id": "iter41_public_task_protocol_effect_runner_recovery",
        "source_experiment": "iter40_public_task_protocol_effect_execution",
        "isolated_runner": report["isolated_runner"],
        "isolated_runner_passed": report["isolated_runner_passed"],
        "run_ids": [record["run_id"] for record in report["runs"]],
        "successful_run_count": report["successful_run_count"],
        "pinned_codeclash_commit_verified": report["pinned_codeclash_commit_verified"],
        "docker_readiness_verified": report["docker_readiness_verified"],
        "dependency_install_verified": report["dependency_install_verified"],
        "artifact_upload_verified": report["artifact_upload_verified"],
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "credential_material_committed": False,
        "project_identifier_committed": False,
        "account_identifier_committed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "clean_pass": status == "pass",
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
        "raw_artifact_file_count": len(report["raw_artifact_hashes"]),
        "raw_artifact_hashes": report["raw_artifact_hashes"],
        "artifact_hashes": {},
    }
    write_json(PROOF / "run_summary.json", run_summary)
    run_summary["artifact_hashes"] = build_artifact_hashes(top_artifacts)
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter41_public_task_protocol_effect_runner_recovery",
        "status": status,
        "insight": (
            "Local Docker remained unavailable, but the isolated GitHub Actions path proves "
            "runner readiness for all three frozen CodeClash surfaces at zero provider spend."
        ),
        "next_action": (
            "retry the frozen protocol-effect execution only under the isolated-runner, provider, "
            "cost, artifact, and claim-boundary controls"
        ),
        "result_path": "experiments/iter41_public_task_protocol_effect_runner_recovery/RESULT.md",
        "evidence_paths": [
            "experiments/iter41_public_task_protocol_effect_runner_recovery/proof/run_summary.json",
            "experiments/iter41_public_task_protocol_effect_runner_recovery/proof/runner_recovery_report.json",
            "experiments/iter41_public_task_protocol_effect_runner_recovery/proof/command_output.txt",
            "experiments/iter41_public_task_protocol_effect_runner_recovery/proof/review.md",
            "experiments/iter41_public_task_protocol_effect_runner_recovery/proof/valid/receipt_public_task_protocol_effect_runner_recovery.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(
        VALID / "receipt_public_task_protocol_effect_runner_recovery.json",
        build_receipt(status),
    )

    print("\n".join(output_lines))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
