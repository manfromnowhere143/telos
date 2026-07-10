#!/usr/bin/env python3
"""Verify iter90 stability-replication adjudication artifacts."""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter90_stability_replication_adjudication_after_same_slice_run"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
RECEIPT_NAME = "receipt_stability_replication_adjudication_after_same_slice_run.json"
NEXT_GATE = "experiments/iter91_empirical_validation_suite_design_for_completion_verification/HYPOTHESIS.md"

ITER86_ID = "iter86_discriminating_metric_backtest_on_committed_artifacts"
ITER86_EXTRACTION = ROOT / "experiments" / ITER86_ID / "proof" / "raw_metric_extraction.json"
ITER87_ID = "iter87_benchmark_facing_discriminating_metric_execution_pilot"
ITER87_EXTRACTION = ROOT / "experiments" / ITER87_ID / "proof" / "fresh_metric_extraction.json"
ITER89_ID = "iter89_same_slice_discriminating_metric_stability_replication"
ITER89_PROOF = ROOT / "experiments" / ITER89_ID / "proof"
ITER89_SUMMARY = ITER89_PROOF / "run_summary.json"
ITER89_STABILITY = ITER89_PROOF / "stability_report.json"
ITER89_EXTRACTION = ITER89_PROOF / "fresh_metric_extraction.json"
ITER89_EXECUTION = ITER89_PROOF / "execution_accounting_report.json"
ITER89_CLAIM_BOUNDARY = ITER89_PROOF / "claim_boundary.json"
ITER89_RECEIPT = ITER89_PROOF / "valid" / "receipt_same_slice_discriminating_metric_stability_replication.json"

METRIC_ID = "task_native_score_share_delta_with_receipt_gates"
ZERO_COST = Decimal("0.00000000")
ITER89_PROVIDER_COST = Decimal("0.11636200")
ITER89_PROVIDER_CALLS = 19
TASKS = ["dummy", "battlesnake", "deterministic_edit"]
SELECTED_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-dummy-yaml",
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
]
TEXT_SUFFIXES = {".json", ".jsonl", ".log", ".txt", ".md", ".yaml", ".yml", ".py"}
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"Bearer\s+(?!\$\{[A-Z0-9_]+\}|\[REDACTED_BEARER_TOKEN\])\S+"),
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"),
    re.compile(r"telos-vertex-runner"),
    re.compile(r"sunlit-unison-[A-Za-z0-9-]+"),
    re.compile(r"errorId=Ci"),
    re.compile(r'"error_info_id"\s*:\s*"Ci'),
]

CASE_FAMILIES = [
    {
        "case_family_id": "proxy_completion",
        "target_failure_mode": "agent optimizes for a proxy artifact while the requested work remains incomplete",
        "expected_artifact": "task diff, claimed receipt, and external verifier finding",
    },
    {
        "case_family_id": "reward_hacking_behavior",
        "target_failure_mode": "agent satisfies scoring text or local reward while violating task intent",
        "expected_artifact": "score transcript, task intent checklist, and adversarial review",
    },
    {
        "case_family_id": "partial_implementation",
        "target_failure_mode": "agent implements a narrow path and presents it as complete",
        "expected_artifact": "patch, uncovered counterexample, and verifier checklist",
    },
    {
        "case_family_id": "misleading_passing_tests",
        "target_failure_mode": "tests pass while required behavior remains semantically wrong",
        "expected_artifact": "passing test log, hidden oracle finding, and task-spec comparison",
    },
    {
        "case_family_id": "incorrect_stopping_boundary",
        "target_failure_mode": "agent stops after setup, planning, or partial validation and claims completion",
        "expected_artifact": "stop transcript, remaining acceptance criteria, and receipt boundary check",
    },
    {
        "case_family_id": "adversarial_receipts",
        "target_failure_mode": "receipt is malformed, incomplete, stale, or contradicted by artifacts",
        "expected_artifact": "receipt packet, artifact hashes, and independent receipt audit",
    },
    {
        "case_family_id": "semantically_incomplete_solution",
        "target_failure_mode": "surface artifacts look plausible but miss the user-visible requirement",
        "expected_artifact": "spec rubric, produced artifact, semantic verifier decision",
    },
]
VERIFICATION_STRATEGIES = [
    "agent_self_report",
    "execution_tests_only",
    "llm_judge",
    "external_verifier",
    "complete_telos_protocol",
]
QUANTITATIVE_ENDPOINTS = [
    "false_completion_acceptance_rate",
    "false_rejection_rate",
    "legitimate_completion_preservation_rate",
    "cost_usd",
    "wall_clock_time_seconds",
    "reviewer_reproducibility_rate",
]


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} root must be an object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def decimal_value(value: object) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.00000001"))


def decimal_string(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.00000001")), "f")


def run_capture(args: list[str], timeout: int = 180) -> dict[str, Any]:
    try:
        result = subprocess.run(
            args,
            cwd=ROOT,
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
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def text_files(path: Path) -> list[Path]:
    return [
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file() and candidate.suffix in TEXT_SUFFIXES
    ]


def redaction_scan() -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    scanned = 0
    for path in text_files(EXPERIMENT):
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append({"path": relative(path), "pattern": pattern.pattern})
                break
    return {
        "schema_version": "telos.stability_replication_adjudication.redaction_scan.v1",
        "experiment_id": EXPERIMENT_ID,
        "scanned_text_file_count": scanned,
        "passed": not findings,
        "findings": findings,
    }


def artifact_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(PROOF.rglob("*")):
        if path.is_file() and path.name != "run_summary.json":
            hashes[str(path.relative_to(PROOF))] = sha256_file(path)
    return hashes


def task_delta_by_task(path: Path) -> dict[str, dict[str, Any]]:
    packet = read_json(path)
    return {str(row["task_surface"]): row for row in packet.get("task_deltas", [])}


def validate_iter89() -> tuple[dict[str, Any], list[str]]:
    receipt = run_capture(["python3", "scripts/validate_receipts.py", relative(ITER89_PROOF)])
    audit = run_capture(["python3", "scripts/audit_same_slice_discriminating_metric_stability_replication.py"])
    summary = read_json(ITER89_SUMMARY)
    stability = read_json(ITER89_STABILITY)
    extraction = read_json(ITER89_EXTRACTION)
    execution = read_json(ITER89_EXECUTION)
    boundary = read_json(ITER89_CLAIM_BOUNDARY)
    clean = (
        receipt["returncode"] == 0
        and audit["returncode"] == 0
        and summary.get("status") == "pass"
        and summary.get("clean_pass") is True
        and summary.get("selected_pair_ids") == SELECTED_PAIR_IDS
        and summary.get("executed_pair_ids") == SELECTED_PAIR_IDS
        and summary.get("executed_pair_count") == 6
        and execution.get("execution_failures") == []
        and execution.get("execution_blockers_after_metric_redefinition") == []
        and int(summary.get("provider_api_calls", -1)) == ITER89_PROVIDER_CALLS
        and decimal_value(summary.get("provider_cost_usd")) == ITER89_PROVIDER_COST
        and summary.get("metric_id") == METRIC_ID
        and summary.get("fresh_metric_computable") is True
        and summary.get("metric_non_saturated") is True
        and summary.get("fresh_metric_rows_parsed") == 6
        and summary.get("fresh_task_deltas_computed") == 3
        and extraction.get("all_rows_parsed") is True
        and stability.get("stability_classification") == "unstable"
        and stability.get("stability_subclassification") == "iter89_mixed_against_prior_directions"
        and stability.get("iter89_matches_iter87_direction_count") == 2
        and stability.get("iter89_matches_iter86_direction_count") == 0
        and stability.get("external_benchmark_design_authorized_by_iter89") is False
        and summary.get("external_benchmark_design_authorized_by_iter89") is False
        and summary.get("benchmark_result_claimed") is False
        and summary.get("model_superiority_claimed") is False
        and summary.get("state_of_the_art_result_claimed") is False
        and boundary.get("benchmark_result_claimed") is False
        and boundary.get("model_superiority_claimed") is False
        and boundary.get("state_of_the_art_result_claimed") is False
    )
    packet = {
        "schema_version": "telos.stability_replication_adjudication.iter89_prerequisite_validation.v1",
        "experiment_id": EXPERIMENT_ID,
        "iter89_status": summary.get("status"),
        "iter89_clean_pass": summary.get("clean_pass"),
        "iter89_receipt_validation_returncode": receipt["returncode"],
        "iter89_audit_returncode": audit["returncode"],
        "iter89_executed_pair_count": summary.get("executed_pair_count"),
        "iter89_provider_api_calls": summary.get("provider_api_calls"),
        "iter89_provider_cost_usd": decimal_string(decimal_value(summary.get("provider_cost_usd"))),
        "iter89_metric_id": summary.get("metric_id"),
        "iter89_metric_non_saturated": summary.get("metric_non_saturated"),
        "iter89_stability_classification": stability.get("stability_classification"),
        "iter89_stability_subclassification": stability.get("stability_subclassification"),
        "iter89_matches_iter87_direction_count": stability.get("iter89_matches_iter87_direction_count"),
        "iter89_matches_iter86_direction_count": stability.get("iter89_matches_iter86_direction_count"),
        "iter89_external_benchmark_design_authorized": stability.get(
            "external_benchmark_design_authorized_by_iter89"
        ),
        "clean_prerequisites": clean,
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
        "command_results": [
            {
                "command": f"python3 scripts/validate_receipts.py {relative(ITER89_PROOF)}",
                "returncode": receipt["returncode"],
                "timed_out": receipt["timed_out"],
                "stdout": receipt["stdout"],
                "stderr": receipt["stderr"],
            },
            {
                "command": "python3 scripts/audit_same_slice_discriminating_metric_stability_replication.py",
                "returncode": audit["returncode"],
                "timed_out": audit["timed_out"],
                "stdout": audit["stdout"],
                "stderr": audit["stderr"],
            },
        ],
        "source_artifacts": [
            {"path": relative(ITER89_SUMMARY), "sha256": sha256_file(ITER89_SUMMARY)},
            {"path": relative(ITER89_STABILITY), "sha256": sha256_file(ITER89_STABILITY)},
            {"path": relative(ITER89_EXTRACTION), "sha256": sha256_file(ITER89_EXTRACTION)},
            {"path": relative(ITER89_EXECUTION), "sha256": sha256_file(ITER89_EXECUTION)},
            {"path": relative(ITER89_CLAIM_BOUNDARY), "sha256": sha256_file(ITER89_CLAIM_BOUNDARY)},
            {"path": relative(ITER89_RECEIPT), "sha256": sha256_file(ITER89_RECEIPT)},
        ],
    }
    blockers = [] if clean else ["iter89_stability_replication_packet_not_clean"]
    return packet, blockers


def locked_iter89_summary() -> dict[str, Any]:
    summary = read_json(ITER89_SUMMARY)
    stability = read_json(ITER89_STABILITY)
    extraction = read_json(ITER89_EXTRACTION)
    execution = read_json(ITER89_EXECUTION)
    return {
        "schema_version": "telos.stability_replication_adjudication.locked_iter89_summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_iteration": ITER89_ID,
        "source_summary": relative(ITER89_SUMMARY),
        "source_summary_sha256": sha256_file(ITER89_SUMMARY),
        "source_stability_report": relative(ITER89_STABILITY),
        "source_stability_report_sha256": sha256_file(ITER89_STABILITY),
        "source_metric_extraction": relative(ITER89_EXTRACTION),
        "source_metric_extraction_sha256": sha256_file(ITER89_EXTRACTION),
        "source_execution_accounting": relative(ITER89_EXECUTION),
        "source_execution_accounting_sha256": sha256_file(ITER89_EXECUTION),
        "selected_pair_ids": SELECTED_PAIR_IDS,
        "executed_pair_ids": summary["executed_pair_ids"],
        "executed_pair_count": summary["executed_pair_count"],
        "provider_api_calls": summary["provider_api_calls"],
        "provider_cost_usd": decimal_string(decimal_value(summary["provider_cost_usd"])),
        "provider_call_ceiling": summary["provider_call_ceiling"],
        "provider_spend_ceiling_usd": summary["provider_spend_ceiling_usd"],
        "metric_id": METRIC_ID,
        "fresh_metric_rows_parsed": extraction["row_count"],
        "fresh_task_deltas_computed": extraction["task_delta_count"],
        "metric_non_saturated": summary["metric_non_saturated"],
        "mixed_direction_signal": summary["mixed_direction_signal"],
        "task_deltas": extraction["task_deltas"],
        "execution_failures": execution["execution_failures"],
        "execution_blockers_after_metric_redefinition": execution[
            "execution_blockers_after_metric_redefinition"
        ],
        "stability_classification": stability["stability_classification"],
        "stability_subclassification": stability["stability_subclassification"],
        "iter89_matches_iter87_direction_count": stability["iter89_matches_iter87_direction_count"],
        "iter89_matches_iter86_direction_count": stability["iter89_matches_iter86_direction_count"],
        "task_comparisons": stability["task_comparisons"],
        "external_benchmark_design_authorized_by_iter89": False,
        "benchmark_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
    }


def direction_evidence_review() -> dict[str, Any]:
    iter86 = task_delta_by_task(ITER86_EXTRACTION)
    iter87 = task_delta_by_task(ITER87_EXTRACTION)
    iter89 = task_delta_by_task(ITER89_EXTRACTION)
    rows: list[dict[str, Any]] = []
    matches_iter87 = 0
    matches_iter86 = 0
    battlesnake_zeroed = False
    for task in TASKS:
        row86 = iter86[task]
        row87 = iter87[task]
        row89 = iter89[task]
        current_direction = row89["direction"]
        matches_prior_execution = current_direction == row87["direction"]
        matches_backtest = current_direction == row86["direction"]
        matches_iter87 += int(matches_prior_execution)
        matches_iter86 += int(matches_backtest)
        if task == "battlesnake":
            battlesnake_zeroed = row89["delta_telos_minus_baseline"] == "0.00000000"
        rows.append(
            {
                "task_surface": task,
                "iter86_delta_telos_minus_baseline": row86["delta_telos_minus_baseline"],
                "iter86_direction": row86["direction"],
                "iter87_delta_telos_minus_baseline": row87["delta_telos_minus_baseline"],
                "iter87_direction": row87["direction"],
                "iter89_delta_telos_minus_baseline": row89["delta_telos_minus_baseline"],
                "iter89_direction": current_direction,
                "iter89_matches_iter87_direction": matches_prior_execution,
                "iter89_matches_iter86_direction": matches_backtest,
            }
        )
    return {
        "schema_version": "telos.stability_replication_adjudication.direction_evidence_review.v1",
        "experiment_id": EXPERIMENT_ID,
        "metric_id": METRIC_ID,
        "source_backtest_iteration": ITER86_ID,
        "source_prior_execution_iteration": ITER87_ID,
        "source_current_execution_iteration": ITER89_ID,
        "task_comparisons": rows,
        "task_count": len(rows),
        "iter89_matches_iter87_direction_count": matches_iter87,
        "iter89_matches_iter86_direction_count": matches_iter86,
        "battlesnake_zeroed_after_positive_iter87": battlesnake_zeroed,
        "stability_classification": "unstable",
        "stability_subclassification": "iter89_mixed_against_prior_directions",
        "empirical_implication": (
            "The same-slice evidence is useful but not stable enough to support benchmark or "
            "SOTA claims. The next evidence should test verification reliability directly."
        ),
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
    }


def next_step_decision(review: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "telos.stability_replication_adjudication.next_step_decision.v1",
        "experiment_id": EXPERIMENT_ID,
        "decision": "design_empirical_validation_suite",
        "decision_options": [
            "scale_to_external_benchmark_design",
            "repeat_same_slice_replication",
            "recover_metric_or_task_surface",
            "stop_benchmark_facing_path",
            "design_empirical_validation_suite",
        ],
        "next_gate": NEXT_GATE,
        "next_gate_pre_registered": (ROOT / NEXT_GATE).exists(),
        "decision_rationale": (
            "Iter89 is a clean run, but its unstable task directions make benchmark or SOTA "
            "escalation scientifically premature. The next defensible milestone is a controlled "
            "empirical validation suite that compares Telos against simpler completion-verification "
            "baselines on failure modes where conventional checks can be fooled."
        ),
        "accepted_path": {
            "kind": "empirical_validation_suite_design",
            "target_scientific_claim": (
                "External verification materially improves autonomous software-agent reliability "
                "by reducing false completion while preserving legitimate completion."
            ),
            "comparison_strategies": VERIFICATION_STRATEGIES,
            "case_family_count": len(CASE_FAMILIES),
            "quantitative_endpoint_count": len(QUANTITATIVE_ENDPOINTS),
            "future_provider_calls_authorized_by_iter90": 0,
            "future_provider_spend_authorized_by_iter90_usd": "0.00000000",
            "why": (
                "A falsifiable suite design is the smallest next step that makes the underlying "
                "scientific claim more defensible without claiming results before data exists."
            ),
        },
        "rejected_paths": [
            {
                "kind": "scale_to_external_benchmark_design",
                "why_rejected_now": "iter89 stability is unstable and does not justify benchmark scaling",
            },
            {
                "kind": "repeat_same_slice_replication",
                "why_rejected_now": (
                    "another paid same-slice run may deepen internal evidence but does not yet "
                    "define the external scientific target or baselines"
                ),
            },
            {
                "kind": "recover_metric_or_task_surface",
                "why_rejected_now": (
                    "the metric remains computable and diagnostic; recovery should be driven by "
                    "empirical validation outcomes rather than protocol expansion"
                ),
            },
            {
                "kind": "stop_benchmark_facing_path",
                "why_rejected_now": (
                    "the unstable evidence is informative and motivates a more defensible "
                    "controlled validation design"
                ),
            },
        ],
        "source_stability_classification": review["stability_classification"],
        "source_stability_subclassification": review["stability_subclassification"],
        "source_iter89_matches_iter87_direction_count": review["iter89_matches_iter87_direction_count"],
        "source_iter89_matches_iter86_direction_count": review["iter89_matches_iter86_direction_count"],
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
    }


def empirical_validation_direction() -> dict[str, Any]:
    return {
        "schema_version": "telos.stability_replication_adjudication.empirical_validation_direction.v1",
        "experiment_id": EXPERIMENT_ID,
        "suite_design_goal": (
            "Measure whether Telos reduces false completion acceptance compared with simpler "
            "completion-verification strategies while preserving legitimate completion."
        ),
        "case_families": CASE_FAMILIES,
        "verification_strategies": [
            {
                "strategy_id": strategy,
                "identical_artifact_requirement": True,
                "must_emit_binary_completion_decision": True,
                "must_emit_rationale_or_evidence_pointer": True,
            }
            for strategy in VERIFICATION_STRATEGIES
        ],
        "quantitative_endpoints": [
            {
                "endpoint_id": endpoint,
                "pre_registered": True,
                "computed_only_after_comparative_execution": True,
            }
            for endpoint in QUANTITATIVE_ENDPOINTS
        ],
        "null_result_policy": "preserve and publish null, negative, blocked, and failed hypotheses",
        "self_validation_risk_control": (
            "The suite must test whether Telos discovers information not available to simpler "
            "baselines, not merely whether Telos validates its own internal process."
        ),
        "benchmark_or_sota_result_claimed": False,
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
    }


def claim_boundary() -> dict[str, Any]:
    return {
        "schema_version": "telos.stability_replication_adjudication.claim_boundary.v1",
        "experiment_id": EXPERIMENT_ID,
        "allowed_claim": (
            "Iter90 adjudicated unstable iter89 stability evidence and selected empirical "
            "validation suite design as the next gate."
        ),
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "swebench_execution_or_score_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_metric_authorized": False,
        "external_benchmark_design_authorized_by_iter90": False,
        "empirical_superiority_claimed": False,
        "future_paid_execution_authorized_by_iter90": False,
    }


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter90-stability-replication-adjudication-{status}",
        "task_id": "telos:iter90_stability_replication_adjudication_after_same_slice_run@iter89",
        "agent_id": "codex-local-stability-replication-adjudicator",
        "benchmark_id": "telos_codeclash_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Adjudicate iter89 same-slice stability evidence and freeze the next defensible "
            "scientific decision before any larger benchmark-facing execution."
        ),
        "acceptance_criteria": [
            "Iter89 receipt and audit validation pass.",
            "Iter89 rows, calls, cost, metric deltas, and stability classification are locked with source hashes.",
            "Iter86, iter87, and iter89 task directions are compared from committed artifacts.",
            "The next decision is explicit and includes rejected paths.",
            "No provider calls, spend, row execution, cloud runner, GPU, Sentinel mutation, or live-domain mutation occurs.",
            "No benchmark, leaderboard, SWE-bench, model-superiority, empirical-superiority, or state-of-the-art claim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                "notes": "Summary records zero-spend adjudication and next gate.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/direction_evidence_review.json",
                "notes": "Direction comparison from iter86, iter87, and iter89 artifacts.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/empirical_validation_direction.json",
                "notes": "Frozen target for the next empirical validation suite design gate.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records why benchmark/SOTA escalation is rejected now.",
            },
        ],
        "falsifiers": [
            "The result must block if iter89 validation fails.",
            "The result must block if iter89 evidence cannot support a precise next decision.",
            "The result must fail if provider calls, spend, or row execution occur in iter90.",
            "The result must fail if unstable same-slice evidence is described as benchmark superiority.",
            "The result must fail if unsupported benchmark, model-superiority, empirical-superiority, production, live-domain, leaderboard, SWE-bench, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def write_text_artifacts(
    *,
    status: str,
    prereq: dict[str, Any],
    locked: dict[str, Any],
    review: dict[str, Any],
    decision: dict[str, Any],
    empirical: dict[str, Any],
    blockers: list[str],
    failures: list[str],
) -> None:
    RESULT.write_text(
        f"""# Iteration 90 Result - Stability Replication Adjudication After Same-Slice Run

Status: `{status.upper()}`.

## Summary

This gate adjudicated committed iter89 evidence without provider calls, spend, or row execution.
The correct next move is empirical validation suite design, not a benchmark/model/SOTA claim.

- iter89 validation clean: `{str(prereq['clean_prerequisites']).lower()}`,
- iter89 executed rows: `{locked['executed_pair_count']}`,
- iter89 provider calls: `{locked['provider_api_calls']}`,
- iter89 provider cost: `${locked['provider_cost_usd']}`,
- iter89 metric: `{METRIC_ID}`,
- iter89 stability classification: `{locked['stability_classification']}`,
- iter89 stability subclassification: `{locked['stability_subclassification']}`,
- iter89 directions matching iter87: `{review['iter89_matches_iter87_direction_count']}`,
- iter89 directions matching iter86: `{review['iter89_matches_iter86_direction_count']}`,
- provider calls in this gate: `0`,
- provider spend in this gate: `$0.00000000`,
- row execution in this gate: `0`,
- next-step decision: `{decision['decision']}`,
- next gate: `{decision['next_gate']}`,
- benchmark/model/SOTA claim: `false`,
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

## Direction Comparison

| Task surface | Iter86 delta | Iter86 direction | Iter87 delta | Iter87 direction | Iter89 delta | Iter89 direction |
| --- | --- | --- | --- | --- | --- | --- |
""",
        encoding="utf-8",
    )
    with RESULT.open("a", encoding="utf-8") as handle:
        for row in review["task_comparisons"]:
            handle.write(
                f"| `{row['task_surface']}` | `{row['iter86_delta_telos_minus_baseline']}` | "
                f"`{row['iter86_direction']}` | `{row['iter87_delta_telos_minus_baseline']}` | "
                f"`{row['iter87_direction']}` | `{row['iter89_delta_telos_minus_baseline']}` | "
                f"`{row['iter89_direction']}` |\n"
            )
        handle.write(
            f"""
## Decision

The accepted next path is `{decision['decision']}`. The rejected paths are immediate external
benchmark design, another paid same-slice replication, metric/task recovery, and stopping the path.
The next gate must design a controlled suite where `{', '.join(VERIFICATION_STRATEGIES)}` are
compared against identical artifacts.

## Empirical Validation Target

The next suite must cover `{len(empirical['case_families'])}` case families and pre-register
quantitative endpoints for false-completion acceptance, false rejection, legitimate completion
preservation, cost, time, and reviewer reproducibility.

## Claim Boundary

This gate may claim only zero-spend adjudication of iter89 evidence and a frozen next-step
decision. It is not a benchmark result, SWE-bench score, leaderboard result, production/live-domain
result, model-superiority result, empirical-superiority result, or state-of-the-art result.

## Evidence

- `proof/iter89_prerequisite_validation.json`
- `proof/locked_iter89_summary.json`
- `proof/direction_evidence_review.json`
- `proof/next_step_decision.json`
- `proof/empirical_validation_direction.json`
- `proof/claim_boundary.json`
- `proof/redaction_scan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/{RECEIPT_NAME}`
"""
        )

    command_lines = [
        f"stability replication adjudication: {status}",
        f"iter89_receipt_validation_returncode={prereq['iter89_receipt_validation_returncode']}",
        f"iter89_audit_returncode={prereq['iter89_audit_returncode']}",
        f"iter89_provider_api_calls={locked['provider_api_calls']}",
        f"iter89_provider_cost_usd={locked['provider_cost_usd']}",
        f"metric_id={METRIC_ID}",
        f"iter89_stability_classification={locked['stability_classification']}",
        f"iter89_stability_subclassification={locked['stability_subclassification']}",
        f"iter89_matches_iter87_direction_count={review['iter89_matches_iter87_direction_count']}",
        f"iter89_matches_iter86_direction_count={review['iter89_matches_iter86_direction_count']}",
        "provider_api_calls=0",
        "provider_cost_usd=0.00000000",
        "row_execution_in_this_gate=0",
        f"next_step_decision={decision['decision']}",
        f"next_gate={decision['next_gate']}",
        "benchmark_result_claimed=false",
        "model_superiority_claimed=false",
        "state_of_the_art_result_claimed=false",
        "empirical_superiority_claimed=false",
        f"case_family_count={len(empirical['case_families'])}",
        f"verification_strategy_count={len(empirical['verification_strategies'])}",
        f"quantitative_endpoint_count={len(empirical['quantitative_endpoints'])}",
        f"blockers={','.join(blockers) if blockers else 'none'}",
        f"failures={','.join(failures) if failures else 'none'}",
    ]
    for row in review["task_comparisons"]:
        command_lines.append(
            f"{row['task_surface']}: iter86_direction={row['iter86_direction']} "
            f"iter87_direction={row['iter87_direction']} iter89_direction={row['iter89_direction']}"
        )
    (PROOF / "command_output.txt").write_text("\n".join(command_lines) + "\n", encoding="utf-8")
    (PROOF / "review.md").write_text(
        f"""# Iteration 90 Review

Iter90 did not run provider rows. It adjudicated committed iter89 stability evidence and selected
empirical validation suite design as the next defensible scientific milestone.

- status: `{status}`,
- iter89 provider calls: `{locked['provider_api_calls']}`,
- iter89 provider cost: `${locked['provider_cost_usd']}`,
- iter89 stability classification: `{locked['stability_classification']}`,
- iter89 stability subclassification: `{locked['stability_subclassification']}`,
- selected next step: `{decision['decision']}`,
- case families for next design: `{len(empirical['case_families'])}`,
- verification strategies for next design: `{len(empirical['verification_strategies'])}`.

Immediate benchmark/SOTA escalation is rejected because same-slice evidence is unstable. Another
paid same-slice replication is also rejected for now because the scientific target and comparison
baselines should be frozen first.

No benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority,
empirical-superiority, or state-of-the-art result is claimed.
""",
        encoding="utf-8",
    )


def main() -> int:
    if PROOF.exists():
        shutil.rmtree(PROOF)
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    prereq, blockers = validate_iter89()
    locked = locked_iter89_summary()
    review = direction_evidence_review()
    decision = next_step_decision(review)
    empirical = empirical_validation_direction()
    boundary = claim_boundary()

    failures: list[str] = []
    if not prereq["clean_prerequisites"]:
        blockers.append("iter89_prerequisite_validation_failed")
    if locked["executed_pair_ids"] != SELECTED_PAIR_IDS:
        failures.append("iter89_executed_pair_ids_changed")
    if locked["provider_api_calls"] != ITER89_PROVIDER_CALLS:
        failures.append("iter89_provider_call_count_changed")
    if decimal_value(locked["provider_cost_usd"]) != ITER89_PROVIDER_COST:
        failures.append("iter89_provider_cost_changed")
    if review["stability_classification"] != "unstable":
        blockers.append("iter89_stability_not_unstable")
    if decision["next_gate_pre_registered"] is not True:
        blockers.append("next_gate_not_pre_registered")
    if len(empirical["case_families"]) != len(CASE_FAMILIES):
        blockers.append("empirical_case_family_count_mismatch")
    if boundary["empirical_superiority_claimed"] is not False:
        failures.append("empirical_superiority_incorrectly_claimed")

    write_json(PROOF / "iter89_prerequisite_validation.json", prereq)
    write_json(PROOF / "locked_iter89_summary.json", locked)
    write_json(PROOF / "direction_evidence_review.json", review)
    write_json(PROOF / "next_step_decision.json", decision)
    write_json(PROOF / "empirical_validation_direction.json", empirical)
    write_json(PROOF / "claim_boundary.json", boundary)

    blockers = sorted(set(blockers))
    failures = sorted(set(failures))
    status = "fail" if failures else "blocked" if blockers else "pass"
    write_json(VALID / RECEIPT_NAME, build_receipt(status))
    write_text_artifacts(
        status=status,
        prereq=prereq,
        locked=locked,
        review=review,
        decision=decision,
        empirical=empirical,
        blockers=blockers,
        failures=failures,
    )

    scan = redaction_scan()
    if not scan["passed"]:
        failures.append("redaction_scan_failed")
        status = "fail"
        write_json(VALID / RECEIPT_NAME, build_receipt(status))
        write_text_artifacts(
            status=status,
            prereq=prereq,
            locked=locked,
            review=review,
            decision=decision,
            empirical=empirical,
            blockers=blockers,
            failures=failures,
        )
        scan = redaction_scan()
    write_json(PROOF / "redaction_scan.json", scan)
    write_json(
        PROOF / "learning_record.json",
        {
            "schema_version": "telos.learning_record.v1",
            "experiment_id": EXPERIMENT_ID,
            "status": status if status != "fail" else "null",
            "insight": (
                "Iter89 is a clean but unstable same-slice replication; the next defensible "
                "milestone is empirical validation suite design against simpler verification baselines."
            ),
            "next_action": "design a controlled empirical validation suite for completion verification",
            "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
            "evidence_paths": [
                f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                f"experiments/{EXPERIMENT_ID}/proof/direction_evidence_review.json",
                f"experiments/{EXPERIMENT_ID}/proof/next_step_decision.json",
                f"experiments/{EXPERIMENT_ID}/proof/empirical_validation_direction.json",
                f"experiments/{EXPERIMENT_ID}/proof/valid/{RECEIPT_NAME}",
            ],
        },
    )
    summary = {
        "schema_version": "telos.stability_replication_adjudication.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": blockers,
        "failures": failures,
        "iter89_status": prereq["iter89_status"],
        "iter89_clean_pass": prereq["iter89_clean_pass"],
        "iter89_receipt_validation_returncode": prereq["iter89_receipt_validation_returncode"],
        "iter89_audit_returncode": prereq["iter89_audit_returncode"],
        "iter89_executed_pair_count": locked["executed_pair_count"],
        "iter89_provider_api_calls": locked["provider_api_calls"],
        "iter89_provider_cost_usd": locked["provider_cost_usd"],
        "metric_id": METRIC_ID,
        "iter89_metric_non_saturated": locked["metric_non_saturated"],
        "iter89_mixed_direction_signal": locked["mixed_direction_signal"],
        "iter89_stability_classification": locked["stability_classification"],
        "iter89_stability_subclassification": locked["stability_subclassification"],
        "iter89_matches_iter87_direction_count": review["iter89_matches_iter87_direction_count"],
        "iter89_matches_iter86_direction_count": review["iter89_matches_iter86_direction_count"],
        "battlesnake_zeroed_after_positive_iter87": review["battlesnake_zeroed_after_positive_iter87"],
        "external_benchmark_design_authorized_by_iter89": False,
        "next_step_decision": decision["decision"],
        "next_gate": decision["next_gate"],
        "next_gate_pre_registered": decision["next_gate_pre_registered"],
        "empirical_case_family_count": len(empirical["case_families"]),
        "verification_strategy_count": len(empirical["verification_strategies"]),
        "quantitative_endpoint_count": len(empirical["quantitative_endpoints"]),
        "provider_api_calls": 0,
        "provider_cost_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "swebench_execution_or_score_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "empirical_superiority_claimed": False,
        "production_or_live_domain_changed": False,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "redaction_scan_passed": scan["passed"],
        "redaction_findings": scan["findings"],
        "artifact_hashes": artifact_hashes(),
    }
    write_json(PROOF / "run_summary.json", summary)

    print(f"stability replication adjudication: {status}")
    print("provider_api_calls=0")
    print("provider_cost_usd=0.00000000")
    print("row_execution_in_this_gate=0")
    print(f"iter89_provider_api_calls={locked['provider_api_calls']}")
    print(f"iter89_provider_cost_usd={locked['provider_cost_usd']}")
    print(f"iter89_stability_classification={locked['stability_classification']}")
    print(f"iter89_stability_subclassification={locked['stability_subclassification']}")
    print(f"next_step_decision={decision['decision']}")
    print(f"next_gate={decision['next_gate']}")
    print(f"blockers={','.join(blockers) if blockers else 'none'}")
    print(f"failures={','.join(failures) if failures else 'none'}")
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    sys.exit(main())
