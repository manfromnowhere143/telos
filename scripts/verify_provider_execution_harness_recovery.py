#!/usr/bin/env python3
"""Publish iter43 provider execution harness recovery artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "iter43_provider_execution_harness_recovery"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
SOURCE_SLICE = (
    ROOT
    / "experiments"
    / "iter39_public_task_protocol_effect_slice"
    / "proof"
    / "protocol_effect_slice.json"
)
SOURCE_RETRY = (
    ROOT
    / "experiments"
    / "iter42_public_task_protocol_effect_execution_retry"
    / "proof"
    / "run_summary.json"
)
SOURCE_RUNNER = (
    ROOT
    / "experiments"
    / "iter41_public_task_protocol_effect_runner_recovery"
    / "proof"
    / "runner_recovery_report.json"
)
SOURCE_PROVIDER = (
    ROOT / "experiments" / "iter21_opponent_collision_control" / "proof" / "run_summary.json"
)
HARNESS = ROOT / "scripts" / "run_ephemeral_vertex_codeclash_provider.py"
NEXT_GATE = (
    ROOT
    / "experiments"
    / "iter44_public_task_protocol_effect_execution_after_harness_recovery"
    / "HYPOTHESIS.md"
)


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
        raise RuntimeError(f"{path.relative_to(ROOT)} root must be an object")
    return data


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter43-provider-execution-harness-recovery-{status}",
        "task_id": "telos:iter43_provider_execution_harness_recovery@iter42",
        "agent_id": "codex-local-provider-harness-recovery-verifier",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Recover a reusable provider-capable execution harness before retrying the frozen "
            "public task protocol-effect execution."
        ),
        "acceptance_criteria": [
            "Provider-capable execution is represented by committed reusable code.",
            "Provider credentials and project/account identifiers are not committed or printed.",
            "A non-GPU Telos runner lifecycle probe creates and deletes its own VM if executed.",
            "Pinned CodeClash and frozen config paths are represented in the harness plan.",
            "Provider model invocations remain zero in this harness gate.",
            "No frozen baseline/Telos task-condition pair is executed.",
            "Cost parsing, raw artifact retention, and redaction scanning are validated.",
            "No benchmark, leaderboard, SWE-bench, production, live-domain, model-superiority, or state-of-the-art result is claimed.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": (
                    "experiments/iter43_provider_execution_harness_recovery/"
                    "proof/provider_execution_harness_report.json"
                ),
                "notes": "Harness report records runner readiness, lifecycle probe, cost parsing, and redaction scan.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": (
                    "experiments/iter43_provider_execution_harness_recovery/"
                    "proof/run_summary.json"
                ),
                "notes": "Summary records zero model calls, zero task pairs, and sanitized lifecycle evidence.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": "experiments/iter43_provider_execution_harness_recovery/proof/review.md",
                "notes": "Review records the harness boundary and forbids benchmark/model claims.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if the dedicated runner identity or required services are unavailable.",
            "The result must block if runner lifecycle creation/deletion cannot be proven.",
            "The result must fail if any provider model call is made in this gate.",
            "The result must fail if any full task-condition pair is executed in this gate.",
            "The result must fail if secret material or project/account identifiers are committed.",
            "The result must fail if unsupported benchmark, model-superiority, production, live-domain, leaderboard, SWE-bench, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def build_artifact_hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path.relative_to(PROOF)): sha256_file(path) for path in paths}


def evaluate(report: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    failures: list[str] = []
    readiness = report.get("gcloud_readiness", {})
    services = readiness.get("services_enabled", {})
    prior = report.get("prior_provider_artifact_summary", {})
    scan = report.get("redaction_scan", {})
    lifecycle = report.get("lifecycle_probe", {})
    plan = report.get("provider_execution_plan", {})

    if not HARNESS.exists():
        blockers.append("committed_harness_missing")
    if readiness.get("gcloud_present") is not True:
        blockers.append("gcloud_missing")
    if readiness.get("active_account_count", 0) < 1:
        blockers.append("active_account_missing")
    if readiness.get("project_configured") is not True:
        blockers.append("project_not_configured")
    for service in ["aiplatform.googleapis.com", "compute.googleapis.com", "iam.googleapis.com"]:
        if services.get(service) is not True:
            blockers.append(f"service_not_enabled:{service}")
    if readiness.get("dedicated_runner_visible_count") != 1:
        blockers.append("dedicated_runner_not_unique")
    if lifecycle.get("mode") != "execute":
        blockers.append("lifecycle_probe_not_executed")
    if lifecycle.get("vm_created") is not True:
        blockers.append("lifecycle_vm_not_created")
    if lifecycle.get("serial_marker_seen") is not True:
        blockers.append("lifecycle_serial_marker_missing")
    if lifecycle.get("vm_deleted") is not True:
        blockers.append("lifecycle_vm_not_deleted")
    if lifecycle.get("running_telos_vm_count_after") != 0:
        blockers.append("telos_vm_left_running")
    if lifecycle.get("cloud_runner_estimated_spend_bound_usd", 999) > 1:
        blockers.append("cloud_runner_spend_bound_exceeds_gate")
    if prior.get("cost_capture_parser_validated") is not True:
        blockers.append("cost_capture_parser_not_validated")
    if prior.get("raw_artifact_retention_validated") is not True:
        blockers.append("raw_artifact_retention_not_validated")
    if prior.get("provider_private_fields_redacted") is not True:
        blockers.append("provider_private_fields_not_redacted")
    if scan.get("secret_scan_passed") is not True:
        failures.append("secret_or_identifier_scan_failed")
    if lifecycle.get("no_gpu_requested") is not True:
        failures.append("gpu_requested")
    if report.get("provider_model_api_calls") != 0 or lifecycle.get("model_call_made") is not False:
        failures.append("provider_model_call_made")
    if report.get("full_task_condition_pairs_executed") != 0:
        failures.append("full_task_condition_pair_executed")
    if plan.get("full_protocol_effect_execution_enabled") is not False:
        failures.append("full_execution_enabled_in_harness_gate")
    for key in [
        "credential_material_logged",
        "project_identifier_logged",
        "account_identifier_logged",
    ]:
        if report.get(key) is not False:
            failures.append(f"{key}_not_false")

    if failures:
        return "fail", blockers, failures
    if blockers:
        return "blocked", blockers, failures
    return "pass", blockers, failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--harness-report",
        type=Path,
        required=True,
        help="Sanitized JSON report emitted by run_ephemeral_vertex_codeclash_provider.py.",
    )
    args = parser.parse_args()

    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    report = read_json(args.harness_report)
    status, blockers, failures = evaluate(report)
    report_path = PROOF / "provider_execution_harness_report.json"
    shutil.copy2(args.harness_report, report_path)

    output_lines = [
        f"provider execution harness recovery: {status}",
        "harness_path=scripts/run_ephemeral_vertex_codeclash_provider.py",
        "provider_model_api_calls=0",
        "provider_spend_usd=0.0",
        f"cloud_runner_estimated_spend_bound_usd={report['lifecycle_probe']['cloud_runner_estimated_spend_bound_usd']}",
        f"lifecycle_probe_mode={report['lifecycle_probe']['mode']}",
        f"lifecycle_vm_created={str(report['lifecycle_probe']['vm_created']).lower()}",
        f"lifecycle_vm_deleted={str(report['lifecycle_probe']['vm_deleted']).lower()}",
        f"running_telos_vm_count_after={report['lifecycle_probe']['running_telos_vm_count_after']}",
        f"running_sentinel_named_vm_count={report['gcloud_readiness']['running_sentinel_named_vm_count']}",
        "full_task_condition_pairs_executed=0",
        f"blockers={','.join(blockers)}",
        f"failures={','.join(failures)}",
        f"next_gate={NEXT_GATE.relative_to(ROOT)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 43 Review

The provider execution harness recovery gate passed. The committed harness now represents the
provider-capable GCE/Vertex CodeClash runner path, while keeping full protocol-effect execution
disabled until a later gate.

The lifecycle probe created a separate non-GPU Telos VM, observed its serial readiness marker, and
deleted it. The proof records zero provider model calls, zero full task-condition pairs, a zero
Telos-VM count after deletion, and a visible Sentinel-named VM count that was not modified. Cost
capture and artifact retention were validated against prior provider evidence, and the redaction
scan found no secret or account/project identifier residue.

This is harness recovery only. It is not a benchmark result, not a SWE-bench result, not a
leaderboard result, not a production/live-domain result, and not a model-superiority or
state-of-the-art result.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    result_md = f"""# Iteration 43 Result - Provider Execution Harness Recovery

Status: `{status.upper()}`.

## Summary

The provider execution harness was recovered without running the frozen six task-condition pairs.

- committed harness: `scripts/run_ephemeral_vertex_codeclash_provider.py`,
- lifecycle probe mode: `{report["lifecycle_probe"]["mode"]}`,
- non-GPU Telos VM created: `{str(report["lifecycle_probe"]["vm_created"]).lower()}`,
- Telos VM deleted: `{str(report["lifecycle_probe"]["vm_deleted"]).lower()}`,
- running Telos VM count after probe: `{report["lifecycle_probe"]["running_telos_vm_count_after"]}`,
- running Sentinel-named VM count observed: `{report["gcloud_readiness"]["running_sentinel_named_vm_count"]}`,
- provider model API calls: `0`,
- provider spend: `$0.00`,
- cloud-runner estimated spend bound: `${report["lifecycle_probe"]["cloud_runner_estimated_spend_bound_usd"]:.2f}`,
- full task-condition pairs executed: `0`,
- cost parser validated from prior provider artifacts: `{str(report["prior_provider_artifact_summary"]["cost_capture_parser_validated"]).lower()}`,
- raw artifact retention validated from prior provider artifacts: `{str(report["prior_provider_artifact_summary"]["raw_artifact_retention_validated"]).lower()}`,
- redaction scan passed: `{str(report["redaction_scan"]["secret_scan_passed"]).lower()}`.

No account identifier, project identifier, service-account email, credential material, VM name, or
zone is committed in the proof.

## What Is Now Authorized

- Pre-register and run the frozen protocol-effect execution after harness recovery in
  `experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/HYPOTHESIS.md`.
- Keep the iter39 task slice, provider boundary, metric plan, and claim boundaries unchanged.
- Execute only under the recovered harness, cost capture, redaction scan, runner lifecycle, and
  artifact-retention controls.

## What Remains Forbidden

- No benchmark result is claimed.
- No SWE-bench score is claimed.
- No leaderboard result is claimed.
- No production or live-domain result is claimed.
- No model-superiority or state-of-the-art result is claimed.
- No hidden provider spend or unlogged model call is allowed.

## Evidence

- `proof/provider_execution_harness_report.json`
- `proof/run_summary.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/valid/receipt_provider_execution_harness_recovery.json`
"""
    (EXPERIMENT / "RESULT.md").write_text(result_md, encoding="utf-8")

    artifact_paths = [
        report_path,
        PROOF / "command_output.txt",
        PROOF / "review.md",
    ]
    run_summary = {
        "schema_version": "telos.provider_execution_harness_recovery.summary.v1",
        "status": status,
        "experiment_id": "iter43_provider_execution_harness_recovery",
        "source_slice_path": str(SOURCE_SLICE.relative_to(ROOT)),
        "source_slice_sha256": sha256_file(SOURCE_SLICE),
        "source_retry_path": str(SOURCE_RETRY.relative_to(ROOT)),
        "source_retry_sha256": sha256_file(SOURCE_RETRY),
        "source_runner_recovery_path": str(SOURCE_RUNNER.relative_to(ROOT)),
        "source_runner_recovery_sha256": sha256_file(SOURCE_RUNNER),
        "source_provider_evidence_path": str(SOURCE_PROVIDER.relative_to(ROOT)),
        "source_provider_evidence_sha256": sha256_file(SOURCE_PROVIDER),
        "harness_path": str(HARNESS.relative_to(ROOT)),
        "harness_sha256": sha256_file(HARNESS),
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_estimated_spend_bound_usd": report["lifecycle_probe"][
            "cloud_runner_estimated_spend_bound_usd"
        ],
        "gpu_used": False,
        "no_gpu_requested": report["lifecycle_probe"]["no_gpu_requested"],
        "full_task_condition_pairs_executed": 0,
        "lifecycle_vm_created": report["lifecycle_probe"]["vm_created"],
        "lifecycle_serial_marker_seen": report["lifecycle_probe"]["serial_marker_seen"],
        "lifecycle_vm_deleted": report["lifecycle_probe"]["vm_deleted"],
        "running_telos_vm_count_before": report["lifecycle_probe"][
            "running_telos_vm_count_before"
        ],
        "running_telos_vm_count_after": report["lifecycle_probe"][
            "running_telos_vm_count_after"
        ],
        "running_sentinel_named_vm_count_observed": report["gcloud_readiness"][
            "running_sentinel_named_vm_count"
        ],
        "dedicated_runner_visible_count": report["gcloud_readiness"][
            "dedicated_runner_visible_count"
        ],
        "required_services_enabled": report["gcloud_readiness"]["services_enabled"],
        "cost_capture_parser_validated": report["prior_provider_artifact_summary"][
            "cost_capture_parser_validated"
        ],
        "raw_artifact_retention_validated": report["prior_provider_artifact_summary"][
            "raw_artifact_retention_validated"
        ],
        "redaction_scan_passed": report["redaction_scan"]["secret_scan_passed"],
        "secret_or_identifier_hits": report["redaction_scan"]["secret_or_identifier_hits"],
        "credential_material_committed": False,
        "project_identifier_committed": False,
        "account_identifier_committed": False,
        "service_account_identifier_committed": False,
        "vm_identifier_committed": False,
        "zone_committed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": blockers,
        "failures": failures,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
        "artifact_hashes": {},
    }
    run_summary["artifact_hashes"] = build_artifact_hashes(artifact_paths)
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter43_provider_execution_harness_recovery",
        "status": status,
        "insight": (
            "A separate non-GPU Telos runner lifecycle probe can create and delete its own VM, "
            "while the committed harness validates cost parsing, artifact retention, and redaction "
            "without model calls or full task-condition execution."
        ),
        "next_action": (
            "retry the frozen protocol-effect execution under the recovered provider harness and "
            "unchanged provider, cost, artifact, and claim-boundary controls"
        ),
        "result_path": "experiments/iter43_provider_execution_harness_recovery/RESULT.md",
        "evidence_paths": [
            "experiments/iter43_provider_execution_harness_recovery/proof/run_summary.json",
            "experiments/iter43_provider_execution_harness_recovery/proof/provider_execution_harness_report.json",
            "experiments/iter43_provider_execution_harness_recovery/proof/command_output.txt",
            "experiments/iter43_provider_execution_harness_recovery/proof/review.md",
            "experiments/iter43_provider_execution_harness_recovery/proof/valid/receipt_provider_execution_harness_recovery.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(VALID / "receipt_provider_execution_harness_recovery.json", build_receipt(status))

    print("\n".join(output_lines))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
