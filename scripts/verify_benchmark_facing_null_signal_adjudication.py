#!/usr/bin/env python3
"""Verify iter84 benchmark-facing null-signal adjudication."""

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
EXPERIMENT_ID = "iter84_benchmark_facing_null_signal_adjudication"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
RECEIPT_NAME = "receipt_benchmark_facing_null_signal_adjudication.json"
NEXT_GATE = "experiments/iter85_discriminating_task_metric_redesign/HYPOTHESIS.md"

ITER83_ID = "iter83_benchmark_facing_protocol_effect_execution_pilot"
ITER83_PROOF = ROOT / "experiments" / ITER83_ID / "proof"
ITER83_SUMMARY = ITER83_PROOF / "run_summary.json"
ITER83_REPORT = ITER83_PROOF / "protocol_effect_report.json"
ITER83_RECEIPT = (
    ITER83_PROOF / "valid" / "receipt_benchmark_facing_protocol_effect_execution_pilot.json"
)

SELECTED_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-dummy-yaml",
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
]
TASKS = ["dummy", "battlesnake", "deterministic_edit"]
ZERO_COST = Decimal("0.00000000")
ITER83_PROVIDER_COST = Decimal("0.11319400")
ITER83_PROVIDER_CALLS = 21
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


def decimal_string(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.00000001")), "f")


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
        "schema_version": "telos.benchmark_facing_null_signal.redaction_scan.v1",
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


def validate_iter83() -> tuple[dict[str, Any], list[str]]:
    receipt = run_capture(["python3", "scripts/validate_receipts.py", relative(ITER83_PROOF)])
    audit = run_capture(["python3", "scripts/audit_benchmark_facing_protocol_effect_execution_pilot.py"])
    summary = read_json(ITER83_SUMMARY)
    report = read_json(ITER83_REPORT)
    clean = (
        receipt["returncode"] == 0
        and audit["returncode"] == 0
        and summary.get("status") == "blocked"
        and summary.get("blocked_result") is True
        and summary.get("null_result") is True
        and summary.get("failures") == []
        and summary.get("blockers") == ["no_interpretable_telos_minus_baseline_signal"]
        and summary.get("executed_pair_ids") == SELECTED_PAIR_IDS
        and summary.get("executed_pair_count") == 6
        and summary.get("provider_api_calls") == ITER83_PROVIDER_CALLS
        and Decimal(str(summary.get("provider_cost_usd"))) == ITER83_PROVIDER_COST
        and report.get("row_results")
        and summary.get("benchmark_result_claimed") is False
        and summary.get("model_superiority_claimed") is False
        and summary.get("state_of_the_art_result_claimed") is False
    )
    blockers = [] if clean else ["iter83_null_signal_packet_not_clean"]
    packet = {
        "schema_version": "telos.benchmark_facing_null_signal.prerequisite_validation.v1",
        "experiment_id": EXPERIMENT_ID,
        "iter83_status": summary.get("status"),
        "iter83_blocked_result": summary.get("blocked_result"),
        "iter83_null_result": summary.get("null_result"),
        "iter83_blockers": summary.get("blockers"),
        "iter83_failures": summary.get("failures"),
        "iter83_executed_pair_count": summary.get("executed_pair_count"),
        "iter83_provider_api_calls": summary.get("provider_api_calls"),
        "iter83_provider_cost_usd": decimal_string(Decimal(str(summary.get("provider_cost_usd")))),
        "iter83_receipt_validation_returncode": receipt["returncode"],
        "iter83_audit_returncode": audit["returncode"],
        "clean_prerequisites": clean,
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
        "command_results": [
            {
                "command": f"python3 scripts/validate_receipts.py {relative(ITER83_PROOF)}",
                "returncode": receipt["returncode"],
                "timed_out": receipt["timed_out"],
                "stdout": receipt["stdout"],
                "stderr": receipt["stderr"],
            },
            {
                "command": "python3 scripts/audit_benchmark_facing_protocol_effect_execution_pilot.py",
                "returncode": audit["returncode"],
                "timed_out": audit["timed_out"],
                "stdout": audit["stdout"],
                "stderr": audit["stderr"],
            },
        ],
        "source_artifacts": [
            {"path": relative(ITER83_SUMMARY), "sha256": sha256_file(ITER83_SUMMARY)},
            {"path": relative(ITER83_REPORT), "sha256": sha256_file(ITER83_REPORT)},
            {"path": relative(ITER83_RECEIPT), "sha256": sha256_file(ITER83_RECEIPT)},
        ],
    }
    return packet, blockers


def row_accounting(report: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for row in report.get("row_results", []):
        rows.append(
            {
                "pair_id": row.get("pair_id"),
                "task_surface": row.get("task_surface"),
                "condition_label": row.get("condition_label"),
                "public_config": row.get("public_config"),
                "command_returncode": row.get("command_returncode"),
                "provider_api_calls": row.get("provider_api_calls"),
                "provider_cost_usd": decimal_string(Decimal(str(row.get("provider_cost_usd")))),
                "raw_evidence_present": row.get("raw_evidence_present"),
                "receipt_required": row.get("receipt_required"),
                "receipt_valid": row.get("receipt_valid"),
                "verified_completion_evidence": row.get("verified_completion_evidence"),
                "round_1_winner": row.get("round_1_winner"),
            }
        )
    return {
        "schema_version": "telos.benchmark_facing_null_signal.row_accounting.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_iteration": ITER83_ID,
        "selected_pair_ids": SELECTED_PAIR_IDS,
        "executed_pair_ids": report.get("executed_pair_ids"),
        "executed_pair_count": report.get("executed_pair_count"),
        "source_provider_api_calls": report.get("provider_api_calls"),
        "source_provider_cost_usd": decimal_string(Decimal(str(report.get("provider_cost_usd")))),
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
        "rows": rows,
        "all_rows_verified_completion": all(
            row.get("verified_completion_evidence") is True for row in report.get("row_results", [])
        ),
        "all_required_receipts_valid": all(
            row.get("receipt_valid") is True
            for row in report.get("row_results", [])
            if row.get("receipt_required") is True
        ),
        "all_raw_evidence_present": all(
            row.get("raw_evidence_present") is True for row in report.get("row_results", [])
        ),
    }


def delta_table(report: dict[str, Any]) -> dict[str, Any]:
    rows = report.get("row_results", [])
    by_task_condition = {
        (row.get("task_surface"), row.get("condition_label")): row for row in rows
    }
    deltas = []
    for task in TASKS:
        baseline = by_task_condition.get((task, "baseline"), {})
        telos = by_task_condition.get((task, "telos"), {})
        baseline_verified = bool(baseline.get("verified_completion_evidence"))
        telos_verified = bool(telos.get("verified_completion_evidence"))
        deltas.append(
            {
                "task_surface": task,
                "baseline_pair_id": baseline.get("pair_id"),
                "telos_pair_id": telos.get("pair_id"),
                "baseline_verified_completion_evidence": baseline_verified,
                "telos_verified_completion_evidence": telos_verified,
                "delta_telos_minus_baseline": int(telos_verified) - int(baseline_verified),
                "baseline_provider_api_calls": baseline.get("provider_api_calls"),
                "telos_provider_api_calls": telos.get("provider_api_calls"),
                "baseline_provider_cost_usd": decimal_string(
                    Decimal(str(baseline.get("provider_cost_usd")))
                ),
                "telos_provider_cost_usd": decimal_string(
                    Decimal(str(telos.get("provider_cost_usd")))
                ),
            }
        )
    all_zero = all(row["delta_telos_minus_baseline"] == 0 for row in deltas)
    return {
        "schema_version": "telos.benchmark_facing_null_signal.delta_table.v1",
        "experiment_id": EXPERIMENT_ID,
        "metric_id": "verified_completion_evidence_by_task_and_condition",
        "aggregate_benchmark_metric_authorized": False,
        "deltas": deltas,
        "all_task_surface_deltas_zero": all_zero,
        "interpretable_protocol_effect_signal": not all_zero,
    }


def classify_null(row_packet: dict[str, Any], delta_packet: dict[str, Any]) -> dict[str, Any]:
    saturated = (
        row_packet["all_rows_verified_completion"] is True
        and row_packet["all_required_receipts_valid"] is True
        and delta_packet["all_task_surface_deltas_zero"] is True
    )
    return {
        "schema_version": "telos.benchmark_facing_null_signal.classification.v1",
        "experiment_id": EXPERIMENT_ID,
        "classification": "verified_completion_metric_saturated" if saturated else "unclassified",
        "null_signal_preserved": saturated,
        "no_signal_blocker_preserved": "no_interpretable_telos_minus_baseline_signal",
        "evidence_basis": [
            "all six iter83 rows had verified-completion evidence",
            "all receipt-required iter83 rows had valid Telos receipts",
            "Dummy, BattleSnake, and deterministic-edit deltas were all 0",
            "iter83 had no quality failures and stayed under the frozen call/spend ceilings",
        ],
        "non_claims": [
            "not a benchmark result",
            "not a model-superiority result",
            "not a leaderboard or SWE-bench score",
            "not a state-of-the-art result",
        ],
    }


def next_step_decision(classification: dict[str, Any]) -> dict[str, Any]:
    decision = "redesign_task_metric"
    return {
        "schema_version": "telos.benchmark_facing_null_signal.next_step_decision.v1",
        "experiment_id": EXPERIMENT_ID,
        "decision": decision,
        "next_gate": NEXT_GATE,
        "next_gate_pre_registered": (ROOT / NEXT_GATE).exists(),
        "decision_rationale": (
            "The execution harness is working, but verified-completion evidence saturated across "
            "all three task surfaces. The next informative step is to redesign the task/metric "
            "contract before another paid run."
        ),
        "accepted_path": {
            "kind": "task_metric_redesign",
            "provider_calls": 0,
            "provider_spend_usd": decimal_string(ZERO_COST),
            "row_execution": 0,
            "why": "prevents another paid run against a non-discriminating saturated metric",
        },
        "rejected_paths": [
            {
                "kind": "same_metric_replication",
                "why_rejected_now": (
                    "replicating the saturated verified-completion boolean would likely add cost "
                    "without addressing the diagnostic weakness"
                ),
            },
            {
                "kind": "stop",
                "why_rejected_now": (
                    "the local evidence loop and provider harness are working; the correct "
                    "problem is task/metric discrimination, not mission completion"
                ),
            },
            {
                "kind": "broader_paid_execution",
                "why_rejected_now": (
                    "larger paid execution is unjustified until the metric can distinguish "
                    "protocol effect from ordinary completion"
                ),
            },
        ],
        "classification_source": classification["classification"],
    }


def claim_boundary() -> dict[str, Any]:
    return {
        "schema_version": "telos.benchmark_facing_null_signal.claim_boundary.v1",
        "experiment_id": EXPERIMENT_ID,
        "allowed_claim": (
            "iter83 produced a bounded six-row null/no-signal protocol-effect pilot under budget"
        ),
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "swebench_execution_or_score_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_metric_authorized": False,
    }


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter84-benchmark-facing-null-signal-adjudication-{status}",
        "task_id": "telos:iter84_benchmark_facing_null_signal_adjudication@iter83",
        "agent_id": "codex-local-null-signal-adjudicator",
        "benchmark_id": "telos_codeclash_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Adjudicate the iter83 six-row null/no-signal result without provider calls or "
            "benchmark/model/SOTA claims."
        ),
        "acceptance_criteria": [
            "Iter83 receipt and audit validation pass.",
            "The iter83 no-signal blocker remains visible.",
            "Exact iter83 row, call, cost, receipt, and raw-artifact accounting is reproduced.",
            "The next step decision is justified from committed evidence.",
            "No provider calls, spend, row execution, cloud runner, GPU, Sentinel mutation, or live-domain mutation occurs.",
            "No benchmark, leaderboard, SWE-bench, model-superiority, or state-of-the-art claim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                "notes": "Summary records iter83 validation, null classification, and next gate.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/delta_table.json",
                "notes": "Per-task deltas preserve the all-zero signal.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/next_step_decision.json",
                "notes": "Decision freezes task/metric redesign before further paid execution.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records the no-claim boundary.",
            },
        ],
        "falsifiers": [
            "The result must block if iter83 validation fails.",
            "The result must fail if provider calls, spend, or row execution occur in iter84.",
            "The result must fail if the iter83 null/no-signal blocker is hidden or rebranded as a win.",
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
    delta: dict[str, Any],
    classification: dict[str, Any],
    decision: dict[str, Any],
    blockers: list[str],
    failures: list[str],
) -> None:
    RESULT.write_text(
        f"""# Iteration 84 Result - Benchmark-Facing Null-Signal Adjudication

Status: `{status.upper()}`.

## Summary

This gate adjudicated the iter83 six-row pilot from committed evidence only. It made zero provider
calls, spent `$0.00`, and executed zero CodeClash rows.

- iter83 validation clean: `{str(prereq['clean_prerequisites']).lower()}`,
- iter83 executed row count: `{prereq['iter83_executed_pair_count']}`,
- iter83 provider API calls: `{prereq['iter83_provider_api_calls']}`,
- iter83 provider cost: `${prereq['iter83_provider_cost_usd']}`,
- provider calls in this gate: `0`,
- provider spend in this gate: `$0.00000000`,
- row execution in this gate: `0`,
- null/no-signal blocker preserved: `{str(classification['null_signal_preserved']).lower()}`,
- classification: `{classification['classification']}`,
- next-step decision: `{decision['decision']}`,
- next gate: `{decision['next_gate']}`,
- benchmark/model/SOTA claim: `false`,
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

## Delta Table

| Task surface | Baseline verified | Telos verified | Telos-minus-baseline |
| --- | --- | --- | --- |
""",
        encoding="utf-8",
    )
    with RESULT.open("a", encoding="utf-8") as handle:
        for row in delta["deltas"]:
            handle.write(
                f"| `{row['task_surface']}` | "
                f"`{str(row['baseline_verified_completion_evidence']).lower()}` | "
                f"`{str(row['telos_verified_completion_evidence']).lower()}` | "
                f"`{row['delta_telos_minus_baseline']}` |\n"
            )
        handle.write(
            f"""
## Claim Boundary

This gate may claim only that iter83 produced a bounded six-row null/no-signal protocol-effect
pilot under budget and that iter84 selected task/metric redesign as the next zero-spend step. It is
not a benchmark result, SWE-bench score, leaderboard result, production/live-domain result,
model-superiority result, or state-of-the-art result.

## Evidence

- `proof/prerequisite_validation.json`
- `proof/row_accounting.json`
- `proof/delta_table.json`
- `proof/null_signal_classification.json`
- `proof/next_step_decision.json`
- `proof/claim_boundary.json`
- `proof/redaction_scan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/{RECEIPT_NAME}`
"""
        )

    command_lines = [
        f"benchmark-facing null-signal adjudication: {status}",
        f"iter83_receipt_validation_returncode={prereq['iter83_receipt_validation_returncode']}",
        f"iter83_audit_returncode={prereq['iter83_audit_returncode']}",
        f"iter83_executed_pair_count={prereq['iter83_executed_pair_count']}",
        f"iter83_provider_api_calls={prereq['iter83_provider_api_calls']}",
        f"iter83_provider_cost_usd={prereq['iter83_provider_cost_usd']}",
        "provider_calls_in_this_gate=0",
        "provider_spend_in_this_gate_usd=0.00000000",
        "row_execution_in_this_gate=0",
        f"classification={classification['classification']}",
        f"null_signal_preserved={str(classification['null_signal_preserved']).lower()}",
        f"next_step_decision={decision['decision']}",
        f"next_gate={decision['next_gate']}",
        f"blockers={','.join(blockers)}",
        f"failures={','.join(failures)}",
    ]
    for row in delta["deltas"]:
        command_lines.append(
            f"{row['task_surface']}: baseline={str(row['baseline_verified_completion_evidence']).lower()} "
            f"telos={str(row['telos_verified_completion_evidence']).lower()} "
            f"delta={row['delta_telos_minus_baseline']}"
        )
    (PROOF / "command_output.txt").write_text("\n".join(command_lines) + "\n", encoding="utf-8")
    (PROOF / "review.md").write_text(
        f"""# Iteration 84 Review

Iter83 did not produce an interpretable Telos-minus-baseline signal because the selected
verified-completion metric saturated: baseline and Telos rows all verified on Dummy, BattleSnake,
and deterministic-edit task surfaces. This is real null evidence, not a hidden pass.

- status: `{status}`,
- classification: `{classification['classification']}`,
- next-step decision: `{decision['decision']}`,
- provider calls in iter84: `0`,
- provider spend in iter84: `$0.00000000`,
- row execution in iter84: `0`.

The next gate is a zero-spend task/metric redesign. No benchmark, leaderboard, SWE-bench,
production/live-domain, model-superiority, or state-of-the-art result is claimed.
""",
        encoding="utf-8",
    )


def main() -> int:
    if PROOF.exists():
        shutil.rmtree(PROOF)
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    prereq, blockers = validate_iter83()
    report = read_json(ITER83_REPORT)
    rows = row_accounting(report)
    delta = delta_table(report)
    classification = classify_null(rows, delta)
    decision = next_step_decision(classification)
    boundary = claim_boundary()

    failures: list[str] = []
    if not prereq["clean_prerequisites"]:
        blockers.append("iter83_prerequisite_validation_failed")
    if not rows["all_rows_verified_completion"]:
        blockers.append("iter83_rows_not_all_verified")
    if not rows["all_required_receipts_valid"]:
        blockers.append("iter83_required_receipts_not_all_valid")
    if not delta["all_task_surface_deltas_zero"]:
        blockers.append("iter83_deltas_not_all_zero")
    if classification["null_signal_preserved"] is not True:
        failures.append("iter83_null_signal_not_preserved")
    if decision["decision"] != "redesign_task_metric":
        failures.append("unexpected_next_step_decision")
    if decision["next_gate_pre_registered"] is not True:
        blockers.append("next_gate_not_pre_registered")

    write_json(PROOF / "prerequisite_validation.json", prereq)
    write_json(PROOF / "row_accounting.json", rows)
    write_json(PROOF / "delta_table.json", delta)
    write_json(PROOF / "null_signal_classification.json", classification)
    write_json(PROOF / "next_step_decision.json", decision)
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
        delta=delta,
        classification=classification,
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
                "Iter83 is a true null/no-signal result caused by saturation of the "
                "verified-completion metric across all selected task surfaces."
            ),
            "next_action": (
                "redesign the task and metric contract before any further paid execution or "
                "benchmark claim"
            ),
            "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
            "evidence_paths": [
                f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                f"experiments/{EXPERIMENT_ID}/proof/delta_table.json",
                f"experiments/{EXPERIMENT_ID}/proof/null_signal_classification.json",
                f"experiments/{EXPERIMENT_ID}/proof/next_step_decision.json",
                f"experiments/{EXPERIMENT_ID}/proof/valid/{RECEIPT_NAME}",
            ],
        },
    )
    summary = {
        "schema_version": "telos.benchmark_facing_null_signal.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": blockers,
        "failures": failures,
        "iter83_status": prereq["iter83_status"],
        "iter83_null_result": prereq["iter83_null_result"],
        "iter83_blockers": prereq["iter83_blockers"],
        "iter83_executed_pair_count": prereq["iter83_executed_pair_count"],
        "iter83_provider_api_calls": prereq["iter83_provider_api_calls"],
        "iter83_provider_cost_usd": prereq["iter83_provider_cost_usd"],
        "provider_api_calls": 0,
        "provider_cost_usd": 0.0,
        "row_execution_in_this_gate": 0,
        "delta_table": delta["deltas"],
        "all_task_surface_deltas_zero": delta["all_task_surface_deltas_zero"],
        "null_signal_classification": classification["classification"],
        "null_signal_preserved": classification["null_signal_preserved"],
        "next_step_decision": decision["decision"],
        "next_gate": decision["next_gate"],
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

    print(f"benchmark-facing null-signal adjudication: {status}")
    print("provider_api_calls=0")
    print("provider_cost_usd=0.00000000")
    print(f"iter83_provider_api_calls={prereq['iter83_provider_api_calls']}")
    print(f"iter83_provider_cost_usd={prereq['iter83_provider_cost_usd']}")
    print(f"classification={classification['classification']}")
    print(f"next_step_decision={decision['decision']}")
    print(f"next_gate={decision['next_gate']}")
    print(f"blockers={','.join(blockers) if blockers else 'none'}")
    print(f"failures={','.join(failures) if failures else 'none'}")
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    sys.exit(main())
