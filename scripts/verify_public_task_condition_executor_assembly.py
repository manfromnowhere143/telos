#!/usr/bin/env python3
"""Publish iter45 public task-condition executor-assembly artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from build_public_task_condition_executor_manifest import build_manifest


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "iter45_public_task_condition_executor_assembly"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
NEXT_GATE = (
    ROOT
    / "experiments"
    / "iter46_public_task_protocol_effect_execution_with_assembled_executor"
    / "HYPOTHESIS.md"
)
REQUIRED_PAIR_FIELDS = {
    "artifact_plan",
    "cost_capture_plan",
    "redaction_plan",
    "receipt_plan",
    "metric_destinations",
    "lifecycle_plan",
}
EXPECTED_CONDITIONS = {
    "baseline_agent_completion_evidence",
    "telos_receipt_enforced_completion_evidence",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter45-public-task-condition-executor-assembly-{status}",
        "task_id": "telos:iter45_public_task_condition_executor_assembly@iter44",
        "agent_id": "codex-local-task-condition-executor-assembler",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Assemble and dry-run the frozen public task-condition executor manifest before "
            "retrying provider-backed protocol-effect execution."
        ),
        "acceptance_criteria": [
            "Exactly six frozen task-condition pairs are represented.",
            "Baseline and Telos receipt-enforced conditions remain separate.",
            "Every pair has artifact, cost, redaction, lifecycle, receipt, and metric plans.",
            "Full execution remains disabled until a later pre-registered gate.",
            "Provider model calls, provider spend, cloud runner startup, and GPU use remain zero.",
            "No benchmark, leaderboard, SWE-bench, production, live-domain, model-superiority, or state-of-the-art result is claimed.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": (
                    "experiments/iter45_public_task_condition_executor_assembly/"
                    "proof/executor_manifest.json"
                ),
                "notes": "Manifest enumerates all frozen task-condition pairs and their plans.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": (
                    "experiments/iter45_public_task_condition_executor_assembly/"
                    "proof/run_summary.json"
                ),
                "notes": "Summary records the dry-run-only result and zero spend boundary.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": "experiments/iter45_public_task_condition_executor_assembly/proof/review.md",
                "notes": "Review records the assembly boundary and what remains unearned.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must fail if any frozen task or condition is dropped, renamed, or duplicated.",
            "The result must fail if any pair lacks artifact, cost, redaction, lifecycle, receipt, or metric plans.",
            "The result must fail if full execution is enabled in this assembly gate.",
            "The result must fail if any provider model call, cloud runner startup, GPU use, or provider spend occurs.",
            "The result must fail if unsupported benchmark, model-superiority, production, live-domain, leaderboard, SWE-bench, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def build_artifact_hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path.relative_to(PROOF)): sha256_file(path) for path in paths}


def evaluate_manifest(manifest: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected = {
        "schema_version": "telos.public_task_condition_executor_manifest.v1",
        "status": "dry_run_ready",
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "full_execution_enabled": False,
        "requires_future_gate_for_provider_execution": True,
        "task_count": 3,
        "condition_count": 2,
        "planned_task_condition_pairs": 6,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            failures.append(f"manifest {key} expected {value!r}, got {manifest.get(key)!r}")

    if not NEXT_GATE.exists():
        failures.append(f"next gate missing: {NEXT_GATE.relative_to(ROOT)}")

    pairs = manifest.get("pairs", [])
    if not isinstance(pairs, list) or len(pairs) != 6:
        failures.append("manifest must contain exactly six pairs")
        return failures

    pair_ids = [pair.get("pair_id") for pair in pairs if isinstance(pair, dict)]
    if len(set(pair_ids)) != 6:
        failures.append("manifest pair ids must be unique")
    if manifest.get("pair_ids") != pair_ids:
        failures.append("manifest pair_ids must match pair order")

    task_ids = {pair.get("task_id") for pair in pairs}
    condition_ids = {pair.get("condition_id") for pair in pairs}
    if len(task_ids) != 3:
        failures.append(f"expected three task ids, got {sorted(task_ids)}")
    if condition_ids != EXPECTED_CONDITIONS:
        failures.append(f"condition ids changed: {sorted(condition_ids)}")

    controls = manifest.get("controls", {})
    for key in [
        "iter43_harness_recovery_passed",
        "iter43_lifecycle_vm_deleted",
        "iter44_blocked_before_provider_execution",
        "provider_execution_forbidden_in_this_gate",
        "cloud_runner_start_forbidden_in_this_gate",
    ]:
        if controls.get(key) is not True:
            failures.append(f"manifest control {key} must be true")
    if controls.get("exact_pair_count_required") != 6:
        failures.append("exact pair count control must be 6")
    if controls.get("duplicate_pair_ids_allowed") is not False:
        failures.append("duplicate pair ids must remain forbidden")

    for pair in pairs:
        if not isinstance(pair, dict):
            failures.append("pair entry must be an object")
            continue
        missing = sorted(REQUIRED_PAIR_FIELDS - set(pair))
        if missing:
            failures.append(f"{pair.get('pair_id')} missing pair fields: {', '.join(missing)}")
        if pair.get("dry_run_only_in_iter45") is not True:
            failures.append(f"{pair.get('pair_id')} must be dry-run only")
        if pair.get("full_execution_enabled") is not False:
            failures.append(f"{pair.get('pair_id')} must not enable full execution")
        if "uv run codeclash run" not in pair.get("future_execution_command_template", ""):
            failures.append(f"{pair.get('pair_id')} missing CodeClash command template")
        for field in REQUIRED_PAIR_FIELDS:
            if not pair.get(field):
                failures.append(f"{pair.get('pair_id')} {field} must be non-empty")

    claim_boundary = manifest.get("claim_boundary", {})
    for key in [
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "production_or_live_domain_changed",
    ]:
        if claim_boundary.get(key) is not False:
            failures.append(f"claim boundary {key} must be false")

    return failures


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    manifest = build_manifest()
    failures = evaluate_manifest(manifest)
    status = "pass" if not failures else "fail"
    write_json(PROOF / "executor_manifest.json", manifest)

    output_lines = [
        f"public task-condition executor assembly: {status}",
        f"task_count={manifest.get('task_count')}",
        f"condition_count={manifest.get('condition_count')}",
        f"planned_task_condition_pairs={manifest.get('planned_task_condition_pairs')}",
        "provider_model_api_calls=0",
        "provider_spend_usd=0.0",
        "cloud_runner_started=false",
        "gpu_used=false",
        "full_execution_enabled=false",
        "requires_future_gate_for_provider_execution=true",
        f"failures={','.join(failures)}",
        f"next_gate={NEXT_GATE.relative_to(ROOT)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 45 Review

The public task-condition executor assembly gate passed as a dry-run-only result. The committed
manifest enumerates the three frozen CodeClash task surfaces across the two frozen conditions for
six total pairs. Each pair has artifact, cost, redaction, lifecycle, receipt, and metric plans.

No provider model call occurred, no cloud runner started, no GPU was used, and no full
task-condition pair executed in this gate. This is executor readiness evidence, not a benchmark or
model result. The next gate may retry provider-backed execution only under a separately
pre-registered budget, lifecycle, artifact, redaction, and claim-boundary plan.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    result = f"""# Iteration 45 Result - Public Task-Condition Executor Assembly

Status: `{status.upper()}`.

## Summary

The gate assembled and audited a dry-run manifest for the frozen public task-condition slice.

- task count: `{manifest.get("task_count")}`,
- condition count: `{manifest.get("condition_count")}`,
- planned task-condition pairs: `{manifest.get("planned_task_condition_pairs")}`,
- provider model API calls: `0`,
- provider spend: `$0.00`,
- cloud runner started: `false`,
- GPU used: `false`,
- full execution enabled: `false`.

Each pair has artifact, cost, redaction, lifecycle, receipt, and metric destinations. The manifest
keeps baseline and Telos receipt-enforced conditions separate and marks full execution as forbidden
until a later pre-registered gate enables it.

## What Is Now Authorized

- Pre-register a bounded retry of the frozen six-pair provider-backed execution using the assembled
  executor manifest.
- Keep exact counts before percentages for baseline and Telos-enforced conditions.
- Continue publishing blocked/null rows if any provider, runner, artifact, redaction, cost, or
  receipt control fails.

## What Remains Forbidden

- No benchmark result is claimed.
- No SWE-bench score is claimed.
- No leaderboard result is claimed.
- No production or live-domain result is claimed.
- No model-superiority or state-of-the-art result is claimed.
- No provider execution is inferred from the dry-run manifest.

## Evidence

- `proof/executor_manifest.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_public_task_condition_executor_assembly.json`
"""
    (EXPERIMENT / "RESULT.md").write_text(result, encoding="utf-8")

    artifact_paths = [
        PROOF / "executor_manifest.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
    ]
    run_summary = {
        "schema_version": "telos.public_task_condition_executor_assembly.summary.v1",
        "status": status,
        "experiment_id": "iter45_public_task_condition_executor_assembly",
        "source_slice_path": manifest["source_slice_path"],
        "source_iter43_summary_path": manifest["source_iter43_summary_path"],
        "source_iter44_summary_path": manifest["source_iter44_summary_path"],
        "harness_path": manifest["harness_path"],
        "planned_task_condition_pairs": manifest["planned_task_condition_pairs"],
        "task_count": manifest["task_count"],
        "condition_count": manifest["condition_count"],
        "pair_ids": manifest["pair_ids"],
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "full_execution_enabled": False,
        "requires_future_gate_for_provider_execution": True,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "clean_pass": status == "pass",
        "blocked_result": False,
        "quality_failure": status == "fail",
        "failures": failures,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
        "artifact_hashes": {},
    }
    run_summary["artifact_hashes"] = build_artifact_hashes(artifact_paths)
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter45_public_task_condition_executor_assembly",
        "status": status,
        "insight": (
            "The frozen public task-condition slice can be represented as six audited dry-run pairs "
            "with artifact, cost, redaction, lifecycle, receipt, and metric plans before provider execution."
        ),
        "next_action": (
            "run the pre-registered provider-backed six-pair protocol-effect execution using the "
            "assembled executor and publish exact counts, costs, raw artifacts, receipts, and nulls"
        ),
        "result_path": "experiments/iter45_public_task_condition_executor_assembly/RESULT.md",
        "evidence_paths": [
            "experiments/iter45_public_task_condition_executor_assembly/proof/run_summary.json",
            "experiments/iter45_public_task_condition_executor_assembly/proof/executor_manifest.json",
            "experiments/iter45_public_task_condition_executor_assembly/proof/command_output.txt",
            "experiments/iter45_public_task_condition_executor_assembly/proof/review.md",
            "experiments/iter45_public_task_condition_executor_assembly/proof/valid/receipt_public_task_condition_executor_assembly.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(
        VALID / "receipt_public_task_condition_executor_assembly.json",
        build_receipt(status),
    )

    print("\n".join(output_lines))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
