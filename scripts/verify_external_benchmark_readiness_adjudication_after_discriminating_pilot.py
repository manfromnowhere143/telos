#!/usr/bin/env python3
"""Verify iter88 external benchmark readiness adjudication."""

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
EXPERIMENT_ID = "iter88_external_benchmark_readiness_adjudication_after_discriminating_pilot"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
RECEIPT_NAME = "receipt_external_benchmark_readiness_adjudication_after_discriminating_pilot.json"
NEXT_GATE = "experiments/iter89_same_slice_discriminating_metric_stability_replication/HYPOTHESIS.md"

ITER86_ID = "iter86_discriminating_metric_backtest_on_committed_artifacts"
ITER86_PROOF = ROOT / "experiments" / ITER86_ID / "proof"
ITER86_SUMMARY = ITER86_PROOF / "run_summary.json"
ITER86_EXTRACTION = ITER86_PROOF / "raw_metric_extraction.json"

ITER87_ID = "iter87_benchmark_facing_discriminating_metric_execution_pilot"
ITER87_PROOF = ROOT / "experiments" / ITER87_ID / "proof"
ITER87_SUMMARY = ITER87_PROOF / "run_summary.json"
ITER87_EXTRACTION = ITER87_PROOF / "fresh_metric_extraction.json"
ITER87_EXECUTION = ITER87_PROOF / "execution_accounting_report.json"
ITER87_RECEIPT = (
    ITER87_PROOF / "valid" / "receipt_benchmark_facing_discriminating_metric_execution_pilot.json"
)

METRIC_ID = "task_native_score_share_delta_with_receipt_gates"
ZERO_COST = Decimal("0.00000000")
ITER87_PROVIDER_COST = Decimal("0.12498400")
ITER87_PROVIDER_CALLS = 21
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


def decimal_string(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.00000001")), "f")


def decimal_value(value: object) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.00000001"))


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
        "schema_version": "telos.external_benchmark_readiness_adjudication.redaction_scan.v1",
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


def validate_iter87() -> tuple[dict[str, Any], list[str]]:
    receipt = run_capture(["python3", "scripts/validate_receipts.py", relative(ITER87_PROOF)])
    audit = run_capture(["python3", "scripts/audit_benchmark_facing_discriminating_metric_execution_pilot.py"])
    summary = read_json(ITER87_SUMMARY)
    extraction = read_json(ITER87_EXTRACTION)
    execution = read_json(ITER87_EXECUTION)
    clean = (
        receipt["returncode"] == 0
        and audit["returncode"] == 0
        and summary.get("status") == "pass"
        and summary.get("clean_pass") is True
        and summary.get("selected_pair_ids") == SELECTED_PAIR_IDS
        and summary.get("executed_pair_ids") == SELECTED_PAIR_IDS
        and summary.get("executed_pair_count") == 6
        and int(summary.get("provider_api_calls", -1)) == ITER87_PROVIDER_CALLS
        and decimal_value(summary.get("provider_cost_usd")) == ITER87_PROVIDER_COST
        and summary.get("metric_id") == METRIC_ID
        and summary.get("fresh_metric_computable") is True
        and summary.get("metric_non_saturated") is True
        and summary.get("fresh_metric_rows_parsed") == 6
        and summary.get("fresh_task_deltas_computed") == 3
        and summary.get("mixed_direction_signal") is True
        and extraction.get("all_rows_parsed") is True
        and execution.get("execution_failures") == []
        and execution.get("execution_blockers_after_metric_redefinition") == []
        and summary.get("benchmark_result_claimed") is False
        and summary.get("model_superiority_claimed") is False
        and summary.get("state_of_the_art_result_claimed") is False
    )
    packet = {
        "schema_version": "telos.external_benchmark_readiness_adjudication.iter87_prerequisite_validation.v1",
        "experiment_id": EXPERIMENT_ID,
        "iter87_status": summary.get("status"),
        "iter87_clean_pass": summary.get("clean_pass"),
        "iter87_selected_pair_ids": summary.get("selected_pair_ids"),
        "iter87_executed_pair_count": summary.get("executed_pair_count"),
        "iter87_provider_api_calls": summary.get("provider_api_calls"),
        "iter87_provider_cost_usd": decimal_string(decimal_value(summary.get("provider_cost_usd"))),
        "iter87_metric_id": summary.get("metric_id"),
        "iter87_metric_non_saturated": summary.get("metric_non_saturated"),
        "iter87_mixed_direction_signal": summary.get("mixed_direction_signal"),
        "iter87_receipt_validation_returncode": receipt["returncode"],
        "iter87_audit_returncode": audit["returncode"],
        "clean_prerequisites": clean,
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
        "command_results": [
            {
                "command": f"python3 scripts/validate_receipts.py {relative(ITER87_PROOF)}",
                "returncode": receipt["returncode"],
                "timed_out": receipt["timed_out"],
                "stdout": receipt["stdout"],
                "stderr": receipt["stderr"],
            },
            {
                "command": "python3 scripts/audit_benchmark_facing_discriminating_metric_execution_pilot.py",
                "returncode": audit["returncode"],
                "timed_out": audit["timed_out"],
                "stdout": audit["stdout"],
                "stderr": audit["stderr"],
            },
        ],
        "source_artifacts": [
            {"path": relative(ITER87_SUMMARY), "sha256": sha256_file(ITER87_SUMMARY)},
            {"path": relative(ITER87_EXTRACTION), "sha256": sha256_file(ITER87_EXTRACTION)},
            {"path": relative(ITER87_EXECUTION), "sha256": sha256_file(ITER87_EXECUTION)},
            {"path": relative(ITER87_RECEIPT), "sha256": sha256_file(ITER87_RECEIPT)},
        ],
    }
    blockers = [] if clean else ["iter87_discriminating_metric_execution_packet_not_clean"]
    return packet, blockers


def locked_iter87_summary() -> dict[str, Any]:
    summary = read_json(ITER87_SUMMARY)
    extraction = read_json(ITER87_EXTRACTION)
    execution = read_json(ITER87_EXECUTION)
    return {
        "schema_version": "telos.external_benchmark_readiness_adjudication.locked_iter87_summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_iteration": ITER87_ID,
        "source_summary": relative(ITER87_SUMMARY),
        "source_summary_sha256": sha256_file(ITER87_SUMMARY),
        "source_extraction": relative(ITER87_EXTRACTION),
        "source_extraction_sha256": sha256_file(ITER87_EXTRACTION),
        "source_execution_accounting": relative(ITER87_EXECUTION),
        "source_execution_accounting_sha256": sha256_file(ITER87_EXECUTION),
        "selected_pair_ids": SELECTED_PAIR_IDS,
        "executed_pair_ids": summary["executed_pair_ids"],
        "executed_pair_count": summary["executed_pair_count"],
        "provider_api_calls": summary["provider_api_calls"],
        "provider_cost_usd": decimal_string(decimal_value(summary["provider_cost_usd"])),
        "provider_call_ceiling": summary["provider_call_ceiling"],
        "provider_spend_ceiling_usd": summary["provider_spend_ceiling_usd"],
        "receipt_required_row_count": sum(
            1 for row in execution.get("row_results", []) if row.get("receipt_required") is True
        ),
        "receipt_required_rows_valid": all(
            row.get("receipt_valid") is True
            for row in execution.get("row_results", [])
            if row.get("receipt_required") is True
        ),
        "metric_id": METRIC_ID,
        "fresh_metric_rows_parsed": extraction["row_count"],
        "fresh_task_deltas_computed": extraction["task_delta_count"],
        "metric_non_saturated": summary["metric_non_saturated"],
        "mixed_direction_signal": summary["mixed_direction_signal"],
        "task_deltas": extraction["task_deltas"],
        "benchmark_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
    }


def direction_by_task(packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["task_surface"]): row for row in packet.get("task_deltas", [])}


def mixed_direction_adjudication() -> dict[str, Any]:
    iter86 = read_json(ITER86_SUMMARY)
    iter86_extraction = read_json(ITER86_EXTRACTION)
    iter87 = read_json(ITER87_SUMMARY)
    iter87_extraction = read_json(ITER87_EXTRACTION)
    iter86_by_task = direction_by_task(iter86_extraction)
    iter87_by_task = direction_by_task(iter87_extraction)
    rows = []
    sign_flip_count = 0
    same_direction_count = 0
    for task in TASKS:
        old = iter86_by_task[task]
        new = iter87_by_task[task]
        old_direction = old["direction"]
        new_direction = new["direction"]
        sign_flip = old_direction != new_direction
        sign_flip_count += int(sign_flip)
        same_direction_count += int(not sign_flip)
        rows.append(
            {
                "task_surface": task,
                "iter86_delta_telos_minus_baseline": old["delta_telos_minus_baseline"],
                "iter86_direction": old_direction,
                "iter87_delta_telos_minus_baseline": new["delta_telos_minus_baseline"],
                "iter87_direction": new_direction,
                "direction_stable": not sign_flip,
                "absolute_delta_change": str(
                    abs(
                        Decimal(str(new["delta_telos_minus_baseline"]))
                        - Decimal(str(old["delta_telos_minus_baseline"]))
                    ).quantize(Decimal("0.00000001"))
                ),
            }
        )
    mixed = iter87.get("mixed_direction_signal") is True
    unstable = sign_flip_count >= 2
    return {
        "schema_version": "telos.external_benchmark_readiness_adjudication.mixed_direction_adjudication.v1",
        "experiment_id": EXPERIMENT_ID,
        "metric_id": METRIC_ID,
        "source_backtest_iteration": ITER86_ID,
        "source_fresh_execution_iteration": ITER87_ID,
        "iter86_source_rows_parsed": iter86["source_rows_parsed"],
        "iter86_metric_non_saturated": iter86["metric_non_saturated"],
        "iter86_mixed_direction_signal": iter86["mixed_direction_signal"],
        "iter87_fresh_metric_rows_parsed": iter87["fresh_metric_rows_parsed"],
        "iter87_metric_non_saturated": iter87["metric_non_saturated"],
        "iter87_mixed_direction_signal": iter87["mixed_direction_signal"],
        "task_comparisons": rows,
        "task_count": len(rows),
        "same_direction_count": same_direction_count,
        "sign_flip_count": sign_flip_count,
        "mixed_direction_signal": mixed,
        "direction_stability_classification": "unstable_mixed_direction_single_pilot" if unstable else "partially_stable",
        "scale_to_external_benchmark_now_supported": False,
        "same_slice_replication_supported": unstable and mixed,
        "stop_for_null_or_negative_signal_supported": False,
        "recover_metric_or_task_surface_supported": False,
        "adjudication": (
            "The metric is computable and non-saturated, but task directions flip between the "
            "committed iter86 backtest and the fresh iter87 execution. This supports same-slice "
            "stability replication, not larger benchmark design yet."
        ),
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
    }


def next_step_decision(adjudication: dict[str, Any]) -> dict[str, Any]:
    decision = "replicate_same_slice"
    return {
        "schema_version": "telos.external_benchmark_readiness_adjudication.next_step_decision.v1",
        "experiment_id": EXPERIMENT_ID,
        "decision": decision,
        "decision_options": [
            "scale_to_external_benchmark_design",
            "replicate_same_slice",
            "recover_metric_or_task_surface",
            "stop_for_null_or_negative_signal",
        ],
        "next_gate": NEXT_GATE,
        "next_gate_pre_registered": (ROOT / NEXT_GATE).exists(),
        "decision_rationale": (
            "Iter87 is valid pilot evidence, but mixed-direction task deltas and direction flips "
            "against iter86 make external benchmark design premature. One same-slice replication "
            "is the smallest useful next spend."
        ),
        "accepted_path": {
            "kind": "same_slice_stability_replication",
            "selected_row_count": 6,
            "future_provider_call_ceiling": 96,
            "future_provider_spend_ceiling_usd": "10.00000000",
            "future_per_row_call_limit": 16,
            "future_per_row_spend_limit_usd": "2.00000000",
            "why": "tests whether task-level directions are stable before larger benchmark design",
        },
        "rejected_paths": [
            {
                "kind": "scale_to_external_benchmark_design",
                "why_rejected_now": (
                    "mixed-direction single-pilot evidence with three task-direction flips is not "
                    "stable enough for larger benchmark design"
                ),
            },
            {
                "kind": "recover_metric_or_task_surface",
                "why_rejected_now": (
                    "the metric is computable, non-saturated, and receipt/accounting evidence is clean"
                ),
            },
            {
                "kind": "stop_for_null_or_negative_signal",
                "why_rejected_now": (
                    "the signal is nonzero and diagnostically useful, even though it is not yet stable"
                ),
            },
        ],
        "source_sign_flip_count": adjudication["sign_flip_count"],
        "source_direction_stability_classification": adjudication[
            "direction_stability_classification"
        ],
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
    }


def replication_design(decision: dict[str, Any]) -> dict[str, Any]:
    accepted = decision["accepted_path"]
    return {
        "schema_version": "telos.external_benchmark_readiness_adjudication.replication_design.v1",
        "experiment_id": EXPERIMENT_ID,
        "design_kind": accepted["kind"],
        "target_gate": NEXT_GATE,
        "target_gate_pre_registered": decision["next_gate_pre_registered"],
        "selected_pair_ids": SELECTED_PAIR_IDS,
        "selected_row_count": accepted["selected_row_count"],
        "provider_call_ceiling": accepted["future_provider_call_ceiling"],
        "provider_spend_ceiling_usd": accepted["future_provider_spend_ceiling_usd"],
        "per_row_call_limit": accepted["future_per_row_call_limit"],
        "per_row_spend_limit_usd": accepted["future_per_row_spend_limit_usd"],
        "stability_outputs_required": [
            "fresh score-share deltas",
            "direction comparison against iter86 and iter87",
            "stable/unstable/blocked/fail classification",
            "no benchmark/model/SOTA claim",
        ],
        "external_benchmark_design_deferred": True,
        "benchmark_execution_authorized_by_iter88": False,
        "provider_calls_in_iter88": 0,
        "provider_spend_in_iter88_usd": decimal_string(ZERO_COST),
        "row_execution_in_iter88": 0,
    }


def scale_rejection(adjudication: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "telos.external_benchmark_readiness_adjudication.scale_rejection.v1",
        "experiment_id": EXPERIMENT_ID,
        "scale_to_external_benchmark_design_now": False,
        "precise_blocker": "task_direction_instability_across_iter86_iter87",
        "evidence": {
            "sign_flip_count": adjudication["sign_flip_count"],
            "mixed_direction_signal": adjudication["mixed_direction_signal"],
            "direction_stability_classification": adjudication[
                "direction_stability_classification"
            ],
        },
        "recovery_target": (
            "one same-slice stability replication before any larger external benchmark design"
        ),
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
    }


def claim_boundary() -> dict[str, Any]:
    return {
        "schema_version": "telos.external_benchmark_readiness_adjudication.claim_boundary.v1",
        "experiment_id": EXPERIMENT_ID,
        "allowed_claim": (
            "Iter88 adjudicated iter87 evidence and selected same-slice stability replication as "
            "the next step with zero new spend."
        ),
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "swebench_execution_or_score_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_metric_authorized": False,
        "fresh_paid_execution_claimed": False,
    }


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter88-external-benchmark-readiness-adjudication-{status}",
        "task_id": "telos:iter88_external_benchmark_readiness_adjudication_after_discriminating_pilot@iter87",
        "agent_id": "codex-local-external-benchmark-readiness-adjudicator",
        "benchmark_id": "telos_codeclash_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Adjudicate whether iter87 discriminating-metric pilot evidence justifies larger "
            "external benchmark design, same-slice replication, recovery, or stop."
        ),
        "acceptance_criteria": [
            "Iter87 receipt and audit validation pass.",
            "Iter87 calls, spend, row count, receipts, and task deltas are locked with source hashes.",
            "Mixed-direction and direction-stability evidence is adjudicated from committed artifacts.",
            "The next decision is explicit and falsifiable.",
            "No provider calls, spend, row execution, cloud runner, GPU, Sentinel mutation, or live-domain mutation occurs.",
            "No benchmark, leaderboard, SWE-bench, model-superiority, or state-of-the-art claim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                "notes": "Summary records zero-spend adjudication and selected next gate.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/mixed_direction_adjudication.json",
                "notes": "Direction stability comparison from iter86 and iter87 artifacts.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/next_step_decision.json",
                "notes": "Decision selects same-slice replication and rejects benchmark scaling now.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records the no-benchmark/no-model/no-SOTA boundary.",
            },
        ],
        "falsifiers": [
            "The result must block if iter87 validation fails.",
            "The result must block if iter87 evidence cannot support a precise next decision.",
            "The result must fail if provider calls, spend, or row execution occur in iter88.",
            "The result must fail if mixed-direction pilot evidence is described as an aggregate benchmark win.",
            "The result must fail if unsupported benchmark, model-superiority, production, live-domain, leaderboard, SWE-bench, or state-of-the-art claims appear.",
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
    adjudication: dict[str, Any],
    decision: dict[str, Any],
    blockers: list[str],
    failures: list[str],
) -> None:
    RESULT.write_text(
        f"""# Iteration 88 Result - External Benchmark Readiness Adjudication After Discriminating Pilot

Status: `{status.upper()}`.

## Summary

This gate adjudicated committed iter87 evidence without provider calls, spend, or row execution.
The iter87 pilot is valid bounded protocol-effect evidence, but it is not ready to scale into a
larger external benchmark design because task directions are mixed and unstable.

- iter87 validation clean: `{str(prereq['clean_prerequisites']).lower()}`,
- iter87 executed rows: `{locked['executed_pair_count']}`,
- iter87 provider calls: `{locked['provider_api_calls']}`,
- iter87 provider cost: `${locked['provider_cost_usd']}`,
- iter87 metric: `{METRIC_ID}`,
- iter87 mixed-direction signal: `{str(locked['mixed_direction_signal']).lower()}`,
- iter86/iter87 sign flips: `{adjudication['sign_flip_count']}`,
- direction stability classification: `{adjudication['direction_stability_classification']}`,
- provider calls in this gate: `0`,
- provider spend in this gate: `$0.00000000`,
- row execution in this gate: `0`,
- next-step decision: `{decision['decision']}`,
- next gate: `{decision['next_gate']}`,
- benchmark/model/SOTA claim: `false`,
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

## Direction Comparison

| Task surface | Iter86 delta | Iter86 direction | Iter87 delta | Iter87 direction | Stable direction |
| --- | --- | --- | --- | --- | --- |
""",
        encoding="utf-8",
    )
    with RESULT.open("a", encoding="utf-8") as handle:
        for row in adjudication["task_comparisons"]:
            handle.write(
                f"| `{row['task_surface']}` | `{row['iter86_delta_telos_minus_baseline']}` | "
                f"`{row['iter86_direction']}` | `{row['iter87_delta_telos_minus_baseline']}` | "
                f"`{row['iter87_direction']}` | `{str(row['direction_stable']).lower()}` |\n"
            )
        handle.write(
            f"""
## Decision

The accepted next path is `{decision['decision']}`: one bounded same-slice stability replication.
External benchmark design is deferred because the current evidence is mixed-direction and unstable.

## Claim Boundary

This gate may claim only zero-spend adjudication of iter87 evidence and a frozen next-step decision.
It is not a benchmark result, SWE-bench score, leaderboard result, production/live-domain result,
model-superiority result, or state-of-the-art result.

## Evidence

- `proof/iter87_prerequisite_validation.json`
- `proof/locked_iter87_summary.json`
- `proof/mixed_direction_adjudication.json`
- `proof/next_step_decision.json`
- `proof/replication_design.json`
- `proof/scale_rejection.json`
- `proof/claim_boundary.json`
- `proof/redaction_scan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/{RECEIPT_NAME}`
"""
        )

    command_lines = [
        f"external benchmark readiness adjudication: {status}",
        f"iter87_receipt_validation_returncode={prereq['iter87_receipt_validation_returncode']}",
        f"iter87_audit_returncode={prereq['iter87_audit_returncode']}",
        f"iter87_provider_api_calls={locked['provider_api_calls']}",
        f"iter87_provider_cost_usd={locked['provider_cost_usd']}",
        f"metric_id={METRIC_ID}",
        f"mixed_direction_signal={str(locked['mixed_direction_signal']).lower()}",
        f"sign_flip_count={adjudication['sign_flip_count']}",
        f"direction_stability_classification={adjudication['direction_stability_classification']}",
        "provider_calls_in_this_gate=0",
        "provider_spend_in_this_gate_usd=0.00000000",
        "row_execution_in_this_gate=0",
        f"next_step_decision={decision['decision']}",
        f"next_gate={decision['next_gate']}",
        "benchmark_result_claimed=false",
        "model_superiority_claimed=false",
        "state_of_the_art_result_claimed=false",
        f"blockers={','.join(blockers) if blockers else 'none'}",
        f"failures={','.join(failures) if failures else 'none'}",
    ]
    for row in adjudication["task_comparisons"]:
        command_lines.append(
            f"{row['task_surface']}: iter86_delta={row['iter86_delta_telos_minus_baseline']} "
            f"iter87_delta={row['iter87_delta_telos_minus_baseline']} "
            f"direction_stable={str(row['direction_stable']).lower()}"
        )
    (PROOF / "command_output.txt").write_text("\n".join(command_lines) + "\n", encoding="utf-8")
    (PROOF / "review.md").write_text(
        f"""# Iteration 88 Review

Iter88 did not run provider rows. It adjudicated committed iter87 pilot evidence and compared
iter86 backtest directions against iter87 fresh-execution directions.

- status: `{status}`,
- iter87 provider calls: `{locked['provider_api_calls']}`,
- iter87 provider cost: `${locked['provider_cost_usd']}`,
- sign flips across iter86 and iter87: `{adjudication['sign_flip_count']}`,
- direction stability classification: `{adjudication['direction_stability_classification']}`,
- selected next step: `{decision['decision']}`.

The result rejects larger external benchmark design for now because mixed-direction single-pilot
evidence is not stable enough. The next gate is one bounded same-slice stability replication.
No benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
state-of-the-art result is claimed.
""",
        encoding="utf-8",
    )


def main() -> int:
    if PROOF.exists():
        shutil.rmtree(PROOF)
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    prereq, blockers = validate_iter87()
    locked = locked_iter87_summary()
    adjudication = mixed_direction_adjudication()
    decision = next_step_decision(adjudication)
    replication = replication_design(decision)
    rejection = scale_rejection(adjudication)
    boundary = claim_boundary()

    failures: list[str] = []
    if not prereq["clean_prerequisites"]:
        blockers.append("iter87_prerequisite_validation_failed")
    if locked["executed_pair_ids"] != SELECTED_PAIR_IDS:
        failures.append("iter87_executed_pair_ids_changed")
    if locked["receipt_required_rows_valid"] is not True:
        blockers.append("iter87_receipt_required_rows_not_valid")
    if adjudication["same_slice_replication_supported"] is not True:
        blockers.append("same_slice_replication_not_supported_by_adjudication")
    if decision["next_gate_pre_registered"] is not True:
        blockers.append("next_gate_not_pre_registered")
    if boundary["aggregate_benchmark_metric_authorized"] is not False:
        failures.append("aggregate_benchmark_metric_incorrectly_authorized")

    write_json(PROOF / "iter87_prerequisite_validation.json", prereq)
    write_json(PROOF / "locked_iter87_summary.json", locked)
    write_json(PROOF / "mixed_direction_adjudication.json", adjudication)
    write_json(PROOF / "next_step_decision.json", decision)
    write_json(PROOF / "replication_design.json", replication)
    write_json(PROOF / "scale_rejection.json", rejection)
    write_json(PROOF / "claim_boundary.json", boundary)

    scan = redaction_scan()
    if not scan["passed"]:
        failures.append("redaction_scan_failed")
    write_json(PROOF / "redaction_scan.json", scan)

    blockers = sorted(set(blockers))
    failures = sorted(set(failures))
    status = "fail" if failures else "blocked" if blockers else "pass"
    write_json(VALID / RECEIPT_NAME, build_receipt(status))
    write_text_artifacts(
        status=status,
        prereq=prereq,
        locked=locked,
        adjudication=adjudication,
        decision=decision,
        blockers=blockers,
        failures=failures,
    )
    write_json(
        PROOF / "learning_record.json",
        {
            "schema_version": "telos.learning_record.v1",
            "experiment_id": EXPERIMENT_ID,
            "status": status if status != "fail" else "null",
            "insight": (
                "Iter87 is valid bounded pilot evidence, but task directions are unstable across "
                "iter86 and iter87, so external benchmark design is premature."
            ),
            "next_action": "run one bounded same-slice stability replication before larger benchmark design",
            "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
            "evidence_paths": [
                f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                f"experiments/{EXPERIMENT_ID}/proof/mixed_direction_adjudication.json",
                f"experiments/{EXPERIMENT_ID}/proof/next_step_decision.json",
                f"experiments/{EXPERIMENT_ID}/proof/replication_design.json",
                f"experiments/{EXPERIMENT_ID}/proof/valid/{RECEIPT_NAME}",
            ],
        },
    )
    summary = {
        "schema_version": "telos.external_benchmark_readiness_adjudication.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": blockers,
        "failures": failures,
        "iter87_status": prereq["iter87_status"],
        "iter87_clean_pass": prereq["iter87_clean_pass"],
        "iter87_receipt_validation_returncode": prereq["iter87_receipt_validation_returncode"],
        "iter87_audit_returncode": prereq["iter87_audit_returncode"],
        "iter87_executed_pair_count": locked["executed_pair_count"],
        "iter87_provider_api_calls": locked["provider_api_calls"],
        "iter87_provider_cost_usd": locked["provider_cost_usd"],
        "metric_id": METRIC_ID,
        "iter87_metric_non_saturated": locked["metric_non_saturated"],
        "iter87_mixed_direction_signal": locked["mixed_direction_signal"],
        "sign_flip_count": adjudication["sign_flip_count"],
        "same_direction_count": adjudication["same_direction_count"],
        "direction_stability_classification": adjudication["direction_stability_classification"],
        "scale_to_external_benchmark_now_supported": adjudication[
            "scale_to_external_benchmark_now_supported"
        ],
        "same_slice_replication_supported": adjudication["same_slice_replication_supported"],
        "next_step_decision": decision["decision"],
        "next_gate": decision["next_gate"],
        "next_gate_pre_registered": decision["next_gate_pre_registered"],
        "future_provider_call_ceiling": replication["provider_call_ceiling"],
        "future_provider_spend_ceiling_usd": replication["provider_spend_ceiling_usd"],
        "provider_api_calls": 0,
        "provider_cost_usd": 0.0,
        "row_execution_in_this_gate": 0,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "swebench_execution_or_score_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "redaction_scan_passed": scan["passed"],
        "redaction_findings": scan["findings"],
        "artifact_hashes": artifact_hashes(),
    }
    write_json(PROOF / "run_summary.json", summary)

    print(f"external benchmark readiness adjudication: {status}")
    print("provider_api_calls=0")
    print("provider_cost_usd=0.00000000")
    print("row_execution_in_this_gate=0")
    print(f"iter87_provider_api_calls={locked['provider_api_calls']}")
    print(f"iter87_provider_cost_usd={locked['provider_cost_usd']}")
    print(f"metric_id={METRIC_ID}")
    print(f"sign_flip_count={adjudication['sign_flip_count']}")
    print(f"direction_stability_classification={adjudication['direction_stability_classification']}")
    print(f"next_step_decision={decision['decision']}")
    print(f"next_gate={decision['next_gate']}")
    print(f"blockers={','.join(blockers) if blockers else 'none'}")
    print(f"failures={','.join(failures) if failures else 'none'}")
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    sys.exit(main())
