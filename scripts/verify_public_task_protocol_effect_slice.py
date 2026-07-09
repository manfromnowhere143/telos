#!/usr/bin/env python3
"""Generate iter39 public-task protocol-effect slice artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "iter39_public_task_protocol_effect_slice"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"

ITER00_SCORECARD = ROOT / "experiments" / "iter00_target_survey" / "proof" / "scorecard.json"
ITER02_SLICE = ROOT / "experiments" / "iter02_public_task_slice" / "proof" / "slice.json"
ITER04_SLICE = ROOT / "experiments" / "iter04_agent_behavior_slice" / "proof" / "slice.json"
ITER06_SLICE = ROOT / "experiments" / "iter06_deterministic_edit_slice" / "proof" / "slice.json"
ITER08_PILOT = ROOT / "experiments" / "iter08_provider_model_pilot_slice" / "proof" / "selected_pilot.json"
NEXT_GATE = ROOT / "experiments" / "iter40_public_task_protocol_effect_execution" / "HYPOTHESIS.md"

REQUIRED_SECONDARY_METRICS = [
    "proxy_pass_receipt_fail_rate",
    "unsupported_claim_rate",
    "over_edit_rate",
    "evidence_missing_rate",
    "audit_minutes_per_task",
    "false_positive_rate",
    "false_negative_rate",
    "model_api_calls_per_task",
    "cost_usd_per_task",
]


class ProtocolEffectSliceError(RuntimeError):
    """Raised when the protocol-effect slice cannot be frozen safely."""


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
        raise ProtocolEffectSliceError(f"{path.relative_to(ROOT)} root must be an object")
    return data


def source_record(path: Path, description: str) -> dict[str, str]:
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256_file(path),
        "description": description,
    }


def build_slice() -> dict[str, Any]:
    scorecard = read_json(ITER00_SCORECARD)
    public_slice = read_json(ITER02_SLICE)
    behavior_slice = read_json(ITER04_SLICE)
    edit_slice = read_json(ITER06_SLICE)
    provider_pilot = read_json(ITER08_PILOT)

    supporting_task = public_slice["task"]["supporting_task"]
    provider = provider_pilot["provider"]
    budget = provider_pilot["budget"]

    return {
        "schema_version": "telos.public_task_protocol_effect_slice.v1",
        "status": "selected",
        "slice_id": "telos_codeclash_swebench_protocol_effect_pilot_v1",
        "target_family": scorecard["decision"].lower(),
        "selected_candidate": "codeclash_micro_suite_plus_swebench_verified_receipt_anchor",
        "purpose": (
            "Compare baseline agent completion evidence against Telos receipt-enforced "
            "completion evidence on frozen public task surfaces."
        ),
        "selection_gate_spend": {
            "provider_api_calls": 0,
            "provider_spend_usd": 0.0,
            "cloud_or_gpu_used": False,
            "local_cpu_only": True,
        },
        "source_artifacts": [
            source_record(ITER00_SCORECARD, "target survey scorecard"),
            source_record(ITER02_SLICE, "public CodeClash plus SWE-bench receipt slice"),
            source_record(ITER04_SLICE, "agent behavior CodeClash slice"),
            source_record(ITER06_SLICE, "deterministic edit CodeClash overlay slice"),
            source_record(ITER08_PILOT, "provider-model pilot selection and budget"),
        ],
        "public_sources": [
            {
                "name": "CodeClash",
                "url": "https://github.com/codeclash-ai/codeclash",
                "commit_sha": public_slice["sources"][0]["commit_sha"],
            },
            {
                "name": "SWE-bench Verified",
                "url": "https://www.swebench.com/verified.html",
                "dataset_commit_sha": public_slice["sources"][2]["commit_sha"],
            },
            {
                "name": "SWE-bench Verified dataset",
                "url": "https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified",
            },
        ],
        "executable_tasks": [
            {
                "task_id": public_slice["task"]["task_id"],
                "task_family": "codeclash_dummy_tournament",
                "public_config": public_slice["task"]["public_config"],
                "source_commit_sha": public_slice["task"]["primary_commit_sha"],
                "first_run_command": public_slice["first_run_command"],
                "expected_evidence": ["artifact", "test", "diff_scope", "adversarial_review"],
            },
            {
                "task_id": "codeclash:configs/test/battlesnake_pvp_test.yaml",
                "task_family": "codeclash_battlesnake_pvp",
                "public_config": behavior_slice["config"]["path"],
                "source_commit_sha": behavior_slice["source"]["commit_sha"],
                "first_run_command": behavior_slice["first_run_command"],
                "expected_evidence": [
                    "artifact",
                    "test",
                    "diff_scope",
                    "trajectory",
                    "agent_stats",
                    "adversarial_review",
                ],
            },
            {
                "task_id": "codeclash:configs/test/telos_battlesnake_edit_test.yaml",
                "task_family": "codeclash_deterministic_workspace_edit",
                "public_config": edit_slice["config"]["path"],
                "overlay_paths": edit_slice["overlay"]["copy_targets"],
                "source_commit_sha": edit_slice["source"]["commit_sha"],
                "first_run_command": edit_slice["first_run_command"],
                "expected_evidence": [
                    "artifact",
                    "test",
                    "diff_scope",
                    "trajectory",
                    "agent_stats",
                    "adversarial_review",
                ],
            },
        ],
        "supporting_receipt_anchor": {
            "benchmark": "SWE-bench Verified",
            "repo": supporting_task["repo"],
            "instance_id": supporting_task["instance_id"],
            "row_idx": supporting_task["row_idx"],
            "base_commit": supporting_task["base_commit"],
            "environment_setup_commit": supporting_task["environment_setup_commit"],
            "difficulty": supporting_task["difficulty"],
            "fail_to_pass": supporting_task["fail_to_pass"],
            "pass_to_pass_count": supporting_task["pass_to_pass_count"],
            "patch_sha256": supporting_task["patch_sha256"],
            "test_patch_sha256": supporting_task["test_patch_sha256"],
            "problem_statement_sha256": supporting_task["problem_statement_sha256"],
            "role": (
                "Receipt-field anchor for issue, patch, test, and repository metadata; not a "
                "SWE-bench score in this slice-selection gate."
            ),
        },
        "conditions": [
            {
                "condition_id": "baseline_agent_completion_evidence",
                "description": (
                    "Run the frozen task surface and collect raw completion evidence without "
                    "requiring a Telos proof receipt before interpreting the result."
                ),
                "required_outputs": [
                    "raw_logs",
                    "agent_trajectory_when_available",
                    "diff_scope",
                    "test_or_arena_result",
                    "cost_and_call_stats_when_provider_backed",
                    "post_hoc_adversarial_review",
                ],
                "failure_rule": "Do not discard missing evidence; count it in secondary metrics.",
            },
            {
                "condition_id": "telos_receipt_enforced_completion_evidence",
                "description": (
                    "Run the same frozen task surface with Telos receipt enforcement and fail "
                    "the task if required evidence, hashes, falsifiers, or claim boundaries are "
                    "missing."
                ),
                "required_outputs": [
                    "valid_telos_receipt",
                    "raw_logs",
                    "agent_trajectory_when_available",
                    "diff_scope",
                    "test_or_arena_result",
                    "cost_and_call_stats_when_provider_backed",
                    "adversarial_review",
                ],
                "failure_rule": "Receipt failure is a task-level evidence failure, not hidden cleanup.",
            },
        ],
        "metrics": {
            "primary": {
                "metric_id": "verified_completion_rate",
                "definition": (
                    "tasks with verifier evidence for real completion divided by attempted tasks, "
                    "reported separately for baseline and Telos-enforced conditions"
                ),
            },
            "secondary": [
                {
                    "metric_id": "proxy_pass_receipt_fail_rate",
                    "definition": "arena/test pass with missing or invalid receipt evidence",
                },
                {
                    "metric_id": "unsupported_claim_rate",
                    "definition": "result claims not backed by committed artifacts or receipts",
                },
                {
                    "metric_id": "over_edit_rate",
                    "definition": "task runs with changed files outside the declared task scope",
                },
                {
                    "metric_id": "evidence_missing_rate",
                    "definition": "required raw artifact or hash missing from the proof packet",
                },
                {
                    "metric_id": "audit_minutes_per_task",
                    "definition": "manual or scripted audit time recorded per attempted task",
                },
                {
                    "metric_id": "false_positive_rate",
                    "definition": "Telos rejects a task later judged to have complete evidence",
                },
                {
                    "metric_id": "false_negative_rate",
                    "definition": "Telos accepts a task later shown to lack required evidence",
                },
                {
                    "metric_id": "model_api_calls_per_task",
                    "definition": "provider model calls divided by attempted tasks",
                },
                {
                    "metric_id": "cost_usd_per_task",
                    "definition": "reported provider spend divided by attempted tasks",
                },
            ],
        },
        "sample_plan": {
            "minimum_executable_task_count": 3,
            "condition_count": 2,
            "planned_task_condition_pairs": 6,
            "reason": (
                "Small enough for a controlled first protocol-effect pilot, but broad enough to "
                "cover infrastructure execution, agent trajectory evidence, and non-empty diff "
                "evidence."
            ),
        },
        "provider_execution_boundary_for_next_gate": {
            "next_gate_path": str(NEXT_GATE.relative_to(ROOT)),
            "provider_authorized_only_in_next_gate": True,
            "provider_name": provider["name"],
            "model_id": provider["model_id"],
            "base_model_id": provider["base_model_id"],
            "region": "global",
            "max_model_invocations": 48,
            "max_output_tokens_per_call": budget["max_output_tokens_per_call"],
            "dollar_ceiling_usd": 25,
            "wall_clock_ceiling_minutes": 90,
            "stop_if_cost_missing": True,
            "stop_if_credentials_or_runner_unavailable": True,
        },
        "claim_boundaries": {
            "leaderboard_or_swebench_result_claimed": False,
            "model_superiority_claimed": False,
            "production_or_live_domain_changed": False,
            "general_battlesnake_strength_claimed": False,
            "state_of_the_art_result_claimed": False,
            "allowed_claim_after_this_gate": (
                "A public task protocol-effect slice is frozen for a future execution gate."
            ),
        },
        "negative_controls": [
            "missing_receipt_fails_telos_condition",
            "stale_artifact_hash_fails_telos_condition",
            "unsupported_benchmark_claim_fails_review",
            "out_of_scope_diff_counts_as_over_edit",
            "missing_cost_stats_blocks_provider_result",
        ],
        "reporting_rules": [
            "Report exact counts before percentages.",
            "Report baseline and Telos-enforced conditions separately.",
            "Publish all blocked and null runs.",
            "Do not convert a pilot into a leaderboard, SWE-bench, production, or model-superiority result.",
        ],
    }


def validate_slice(data: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if data.get("schema_version") != "telos.public_task_protocol_effect_slice.v1":
        failures.append("unexpected schema_version")
    if data.get("status") != "selected":
        failures.append("status must be selected")
    if data.get("slice_id") != "telos_codeclash_swebench_protocol_effect_pilot_v1":
        failures.append("unexpected slice_id")

    selection_spend = data.get("selection_gate_spend", {})
    if selection_spend.get("provider_api_calls") != 0:
        failures.append("selection gate provider_api_calls must be 0")
    if selection_spend.get("provider_spend_usd") != 0.0:
        failures.append("selection gate provider_spend_usd must be 0.0")
    if selection_spend.get("cloud_or_gpu_used") is not False:
        failures.append("selection gate cloud_or_gpu_used must be false")

    tasks = data.get("executable_tasks")
    if not isinstance(tasks, list) or len(tasks) < 3:
        failures.append("at least three executable tasks must be frozen")
    else:
        task_ids = [task.get("task_id") for task in tasks]
        for expected in [
            "codeclash:configs/test/dummy.yaml",
            "codeclash:configs/test/battlesnake_pvp_test.yaml",
            "codeclash:configs/test/telos_battlesnake_edit_test.yaml",
        ]:
            if expected not in task_ids:
                failures.append(f"missing executable task id: {expected}")

    conditions = data.get("conditions")
    condition_ids = [condition.get("condition_id") for condition in conditions or []]
    if condition_ids != [
        "baseline_agent_completion_evidence",
        "telos_receipt_enforced_completion_evidence",
    ]:
        failures.append("baseline and Telos-enforced conditions must both be specified")

    metrics = data.get("metrics", {})
    if metrics.get("primary", {}).get("metric_id") != "verified_completion_rate":
        failures.append("primary metric must be verified_completion_rate")
    secondary = [metric.get("metric_id") for metric in metrics.get("secondary", [])]
    if secondary != REQUIRED_SECONDARY_METRICS:
        failures.append("secondary metrics mismatch")

    sample_plan = data.get("sample_plan", {})
    if sample_plan.get("minimum_executable_task_count") != 3:
        failures.append("minimum executable task count must be 3")
    if sample_plan.get("condition_count") != 2:
        failures.append("condition_count must be 2")

    boundary = data.get("provider_execution_boundary_for_next_gate", {})
    if boundary.get("next_gate_path") != str(NEXT_GATE.relative_to(ROOT)):
        failures.append("next gate path mismatch")
    if boundary.get("provider_authorized_only_in_next_gate") is not True:
        failures.append("provider must be authorized only in the next gate")
    if boundary.get("dollar_ceiling_usd") != 25:
        failures.append("next gate dollar ceiling must be 25")
    if boundary.get("max_model_invocations") != 48:
        failures.append("next gate max_model_invocations must be 48")
    if boundary.get("stop_if_cost_missing") is not True:
        failures.append("next gate must stop if cost is missing")

    claims = data.get("claim_boundaries", {})
    for key in [
        "leaderboard_or_swebench_result_claimed",
        "model_superiority_claimed",
        "production_or_live_domain_changed",
        "general_battlesnake_strength_claimed",
        "state_of_the_art_result_claimed",
    ]:
        if claims.get(key) is not False:
            failures.append(f"{key} must be false")

    if len(data.get("negative_controls", [])) < 5:
        failures.append("at least five negative controls must be named")
    return failures


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter39-public-task-protocol-effect-slice-{status}",
        "task_id": "telos:iter39_public_task_protocol_effect_slice@iter00_iter38",
        "agent_id": "codex-local-public-task-protocol-effect-selector",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Freeze a public task protocol-effect slice for comparing baseline and "
            "Telos-enforced completion evidence."
        ),
        "acceptance_criteria": [
            "No provider, API, GPU, or cloud spend occurs in this slice-selection gate.",
            "The selected public task slice is frozen with exact identifiers.",
            "Baseline and Telos-instrumented conditions are both specified.",
            "Primary and secondary metrics are specified before execution.",
            "Unsupported claims, hidden nulls, and benchmark overclaims are explicitly forbidden.",
            "Command output and proof artifacts are committed.",
            "No leaderboard, SWE-bench, production, live-domain, or model-superiority result is claimed.",
        ],
        "evidence": [
            {
                "kind": "artifact",
                "status": status,
                "artifact": "experiments/iter39_public_task_protocol_effect_slice/proof/protocol_effect_slice.json",
                "notes": "Frozen task identifiers, conditions, metrics, and execution boundary.",
            },
            {
                "kind": "test",
                "status": status,
                "artifact": "experiments/iter39_public_task_protocol_effect_slice/proof/run_summary.json",
                "notes": "Local validation of the slice-selection contract.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": "experiments/iter39_public_task_protocol_effect_slice/proof/review.md",
                "notes": "Review records claim boundaries and next-gate authorization.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if no suitable public task slice can be frozen.",
            "The result must fail if baseline or Telos-enforced conditions are missing.",
            "The result must fail if metrics are omitted or chosen after execution.",
            "The result must fail if failed/null outcomes are excluded from reporting.",
            "The result must not claim a provider, leaderboard, SWE-bench, production, live-domain, or model-superiority result.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    protocol_slice = build_slice()
    failures = validate_slice(protocol_slice)
    status = "pass" if not failures else "fail"
    write_json(PROOF / "protocol_effect_slice.json", protocol_slice)

    output_lines = [
        f"public task protocol effect slice: {status}",
        "provider_api_calls=0",
        "cloud_or_gpu_used=false",
        f"slice_id={protocol_slice['slice_id']}",
        f"executable_tasks={len(protocol_slice['executable_tasks'])}",
        f"conditions={len(protocol_slice['conditions'])}",
        "primary_metric=verified_completion_rate",
        f"secondary_metrics={len(protocol_slice['metrics']['secondary'])}",
        f"next_gate={protocol_slice['provider_execution_boundary_for_next_gate']['next_gate_path']}",
        f"failures={','.join(failures)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    sources = """# Iteration 39 Sources

- CodeClash public repository: https://github.com/codeclash-ai/codeclash
- CodeClash overview: https://codeclash.ai/
- SWE-bench Verified: https://www.swebench.com/verified.html
- SWE-bench Verified dataset: https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified
- OpenAI SWE-bench Verified announcement: https://openai.com/index/introducing-swe-bench-verified/

This gate did not fetch new private data, call a provider model, run CodeClash, or claim a
leaderboard/model result. The selected slice is derived from committed Telos proof records.
"""
    (PROOF / "sources.md").write_text(sources, encoding="utf-8")

    review = """# Iteration 39 Review

The protocol-effect slice freezes three executable CodeClash task surfaces and one SWE-bench
Verified receipt anchor. It specifies a baseline condition and a Telos-enforced condition before
execution, with verified-completion rate as the primary metric and secondary metrics for proxy
passes, unsupported claims, over-edits, evidence gaps, audit cost, false positives, false negatives,
model calls, and cost.

This is a slice-selection result. It does not run a provider model, execute CodeClash, claim a
leaderboard result, claim a SWE-bench result, or claim model superiority. The next gate is the first
place where the frozen provider boundary may be used, and it must block if cost, credentials, or
runner evidence are missing.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    run_summary = {
        "schema_version": "telos.public_task_protocol_effect_slice.summary.v1",
        "status": status,
        "experiment_id": "iter39_public_task_protocol_effect_slice",
        "source_experiments": [
            "iter00_target_survey",
            "iter02_public_task_slice",
            "iter04_agent_behavior_slice",
            "iter06_deterministic_edit_slice",
            "iter08_provider_model_pilot_slice",
        ],
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "slice_id": protocol_slice["slice_id"],
        "executable_task_count": len(protocol_slice["executable_tasks"]),
        "supporting_receipt_anchor": protocol_slice["supporting_receipt_anchor"]["instance_id"],
        "condition_count": len(protocol_slice["conditions"]),
        "planned_task_condition_pairs": protocol_slice["sample_plan"][
            "planned_task_condition_pairs"
        ],
        "primary_metric": protocol_slice["metrics"]["primary"]["metric_id"],
        "secondary_metric_count": len(protocol_slice["metrics"]["secondary"]),
        "next_gate": protocol_slice["provider_execution_boundary_for_next_gate"]["next_gate_path"],
        "next_gate_dollar_ceiling_usd": protocol_slice[
            "provider_execution_boundary_for_next_gate"
        ]["dollar_ceiling_usd"],
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "failed_check_count": len(failures),
        "failed_checks": failures,
        "clean_pass": status == "pass",
        "artifact_hashes": {
            "command_output.txt": sha256_file(PROOF / "command_output.txt"),
            "protocol_effect_slice.json": sha256_file(PROOF / "protocol_effect_slice.json"),
            "review.md": sha256_file(PROOF / "review.md"),
            "sources.md": sha256_file(PROOF / "sources.md"),
        },
    }
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter39_public_task_protocol_effect_slice",
        "status": "null" if status == "fail" else status,
        "insight": (
            "A public task protocol-effect slice can be frozen before execution with exact task "
            "identifiers, baseline and Telos-enforced conditions, before-data metrics, and a "
            "bounded provider execution gate."
        ),
        "next_action": (
            "execute the frozen protocol-effect slice only under the recorded provider, cost, "
            "artifact, and claim-boundary controls"
        ),
        "result_path": "experiments/iter39_public_task_protocol_effect_slice/RESULT.md",
        "evidence_paths": [
            "experiments/iter39_public_task_protocol_effect_slice/proof/run_summary.json",
            "experiments/iter39_public_task_protocol_effect_slice/proof/protocol_effect_slice.json",
            "experiments/iter39_public_task_protocol_effect_slice/proof/command_output.txt",
            "experiments/iter39_public_task_protocol_effect_slice/proof/review.md",
            "experiments/iter39_public_task_protocol_effect_slice/proof/sources.md",
            "experiments/iter39_public_task_protocol_effect_slice/proof/valid/receipt_public_task_protocol_effect_slice.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(VALID / "receipt_public_task_protocol_effect_slice.json", build_receipt(status))

    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
