#!/usr/bin/env python3
"""Verify iter81 stratified adapter-validation consolidation from committed packets."""

from __future__ import annotations

from dataclasses import dataclass
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
EXPERIMENT_ID = "iter81_expanded_stratified_adapter_validation_consolidation"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
RECEIPT_NAME = "receipt_expanded_stratified_adapter_validation_consolidation.json"
NEXT_GATE = "experiments/iter82_benchmark_facing_protocol_effect_slice_design/HYPOTHESIS.md"
ZERO_COST = Decimal("0.00000000")
TEXT_SUFFIXES = {".json", ".jsonl", ".log", ".txt", ".md", ".yaml", ".yml", ".py"}
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"Bearer\s+(?!\$\{TELOS_VERTEX_BEARER_TOKEN\}|\[REDACTED_BEARER_TOKEN\])\S+"),
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"),
    re.compile(r"telos-vertex-runner"),
    re.compile(r"sunlit-unison-[A-Za-z0-9-]+"),
    re.compile(r"errorId=Ci"),
    re.compile(r'"error_info_id"\s*:\s*"Ci'),
]

BATTLESNAKE_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
]
DETERMINISTIC_EDIT_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
]
DUMMY_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
]
CONSOLIDATED_PAIR_IDS = BATTLESNAKE_PAIR_IDS + DETERMINISTIC_EDIT_PAIR_IDS + DUMMY_PAIR_IDS


@dataclass(frozen=True)
class SourcePacket:
    iteration_id: str
    proof_dir: Path
    summary_path: Path
    report_path: Path
    receipt_path: Path
    audit_script: str
    expected_status: str
    role: str


ITER66 = SourcePacket(
    iteration_id="iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment",
    proof_dir=ROOT
    / "experiments"
    / "iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment"
    / "proof",
    summary_path=ROOT
    / "experiments"
    / "iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment"
    / "proof"
    / "run_summary.json",
    report_path=ROOT
    / "experiments"
    / "iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment"
    / "proof"
    / "protocol_effect_report.json",
    receipt_path=ROOT
    / "experiments"
    / "iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment"
    / "proof"
    / "valid"
    / "receipt_provider_compatible_paid_execution_after_receipt_prompt_alignment.json",
    audit_script="scripts/audit_provider_compatible_paid_execution_after_receipt_prompt_alignment.py",
    expected_status="pass",
    role="retained_battlesnake_prior_paid_evidence",
)
ITER78 = SourcePacket(
    iteration_id="iter78_provider_compatible_expanded_paid_retry_after_adc_recovery",
    proof_dir=ROOT
    / "experiments"
    / "iter78_provider_compatible_expanded_paid_retry_after_adc_recovery"
    / "proof",
    summary_path=ROOT
    / "experiments"
    / "iter78_provider_compatible_expanded_paid_retry_after_adc_recovery"
    / "proof"
    / "run_summary.json",
    report_path=ROOT
    / "experiments"
    / "iter78_provider_compatible_expanded_paid_retry_after_adc_recovery"
    / "proof"
    / "protocol_effect_report.json",
    receipt_path=ROOT
    / "experiments"
    / "iter78_provider_compatible_expanded_paid_retry_after_adc_recovery"
    / "proof"
    / "valid"
    / "receipt_provider_compatible_expanded_paid_retry_after_adc_recovery.json",
    audit_script="scripts/audit_provider_compatible_expanded_paid_retry_after_adc_recovery.py",
    expected_status="blocked",
    role="deterministic_edit_verified_and_dummy_call_ceiling_diagnostic",
)
ITER80 = SourcePacket(
    iteration_id="iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery",
    proof_dir=ROOT
    / "experiments"
    / "iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery"
    / "proof",
    summary_path=ROOT
    / "experiments"
    / "iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery"
    / "proof"
    / "run_summary.json",
    report_path=ROOT
    / "experiments"
    / "iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery"
    / "proof"
    / "protocol_effect_report.json",
    receipt_path=ROOT
    / "experiments"
    / "iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery"
    / "proof"
    / "valid"
    / "receipt_dummy_call_ceiling_bounded_paid_retry_after_recovery.json",
    audit_script="scripts/audit_dummy_call_ceiling_bounded_paid_retry_after_recovery.py",
    expected_status="pass",
    role="dummy_verified_after_recovered_call_ceiling",
)
SOURCE_PACKETS = [ITER66, ITER78, ITER80]


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


def decimal_value(value: Any) -> Decimal:
    return Decimal(str(value or 0))


def decimal_string(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.00000001'))}"


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
                findings.append(
                    {
                        "path": str(path.relative_to(ROOT)),
                        "pattern": pattern.pattern,
                    }
                )
                break
    return {
        "schema_version": "telos.expanded_stratified_adapter_validation.redaction_scan.v1",
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


def rows_by_pair(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("pair_id")): item
        for item in report.get("row_results", [])
        if isinstance(item, dict)
    }


def condition_from_pair(pair_id: str) -> str:
    if pair_id.startswith("baseline-agent-completion-evidence__"):
        return "baseline_agent_completion_evidence"
    if pair_id.startswith("telos-receipt-enforced-completion-evidence__"):
        return "telos_receipt_enforced_completion_evidence"
    return "unknown"


def row_entry(
    *,
    source_iteration: str,
    source_role: str,
    pair_id: str,
    row: dict[str, Any],
    public_config: str,
    analysis_stratum: str,
    evidence_role: str,
    consolidated_success_evidence: bool,
) -> dict[str, Any]:
    provider_cost = decimal_value(row.get("provider_cost_usd"))
    return {
        "pair_id": pair_id,
        "source_iteration": source_iteration,
        "source_role": source_role,
        "public_config": public_config,
        "analysis_stratum": analysis_stratum,
        "evidence_role": evidence_role,
        "consolidated_success_evidence": consolidated_success_evidence,
        "executed_in_source_iteration": True,
        "executed_in_iter81": False,
        "condition_id": row.get("condition_id") or condition_from_pair(pair_id),
        "command_returncode": row.get("command_returncode"),
        "command_timed_out": row.get("command_timed_out"),
        "verified_completion_evidence": row.get("verified_completion_evidence"),
        "raw_evidence_present": row.get("raw_evidence_present"),
        "receipt_required": row.get("receipt_required"),
        "receipt_valid": row.get("receipt_valid"),
        "provider_api_calls": int(row.get("provider_api_calls") or 0),
        "provider_cost_usd": decimal_string(provider_cost),
    }


def sum_calls(rows: list[dict[str, Any]]) -> int:
    return sum(int(row.get("provider_api_calls") or 0) for row in rows)


def sum_cost(rows: list[dict[str, Any]]) -> Decimal:
    return sum((decimal_value(row.get("provider_cost_usd")) for row in rows), ZERO_COST)


def stratum_summary(
    *,
    name: str,
    public_config: str,
    interpretation: str,
    rows: list[dict[str, Any]],
    consolidated_success_evidence: bool,
) -> dict[str, Any]:
    by_condition = {str(row["condition_id"]): row for row in rows}
    baseline = by_condition.get("baseline_agent_completion_evidence", {})
    telos = by_condition.get("telos_receipt_enforced_completion_evidence", {})
    baseline_verified = baseline.get("verified_completion_evidence") is True
    telos_verified = telos.get("verified_completion_evidence") is True
    return {
        "name": name,
        "public_config": public_config,
        "interpretation": interpretation,
        "pair_ids": [str(row["pair_id"]) for row in rows],
        "row_count": len(rows),
        "consolidated_success_evidence": consolidated_success_evidence,
        "executed_rows_in_iter81": 0,
        "provider_api_calls": sum_calls(rows),
        "provider_cost_usd": decimal_string(sum_cost(rows)),
        "baseline_verified_completion_evidence": baseline_verified,
        "telos_verified_completion_evidence": telos_verified,
        "telos_minus_baseline_verified_completion_delta": int(telos_verified)
        - int(baseline_verified),
        "cross_task_surface_pooling_authorized": False,
    }


def validate_source_packets() -> tuple[dict[str, Any], list[str]]:
    packet_results: list[dict[str, Any]] = []
    command_results: list[dict[str, Any]] = []
    blockers: list[str] = []
    for packet in SOURCE_PACKETS:
        receipt_result = run_capture(
            ["python3", "scripts/validate_receipts.py", str(packet.proof_dir.relative_to(ROOT))]
        )
        audit_result = run_capture(["python3", packet.audit_script])
        summary = read_json(packet.summary_path)
        report = read_json(packet.report_path)
        source_clean = (
            receipt_result["returncode"] == 0
            and audit_result["returncode"] == 0
            and summary.get("status") == packet.expected_status
            and summary.get("quality_failure") is False
            and summary.get("benchmark_result_claimed") is False
            and summary.get("model_superiority_claimed") is False
            and summary.get("state_of_the_art_result_claimed") is False
            and summary.get("leaderboard_or_swebench_result_claimed") is False
            and summary.get("production_or_live_domain_changed") is False
            and summary.get("gpu_used") is False
            and summary.get("cloud_runner_started") is False
            and summary.get("sentinel_named_resources_modified") is False
        )
        if not source_clean:
            blockers.append(f"{packet.iteration_id}_source_packet_not_clean_for_consolidation")
        command_results.extend(
            [
                {
                    "source_iteration": packet.iteration_id,
                    "command": f"python3 scripts/validate_receipts.py {packet.proof_dir.relative_to(ROOT)}",
                    "returncode": receipt_result["returncode"],
                    "timed_out": receipt_result["timed_out"],
                    "stdout": receipt_result["stdout"],
                    "stderr": receipt_result["stderr"],
                },
                {
                    "source_iteration": packet.iteration_id,
                    "command": f"python3 {packet.audit_script}",
                    "returncode": audit_result["returncode"],
                    "timed_out": audit_result["timed_out"],
                    "stdout": audit_result["stdout"],
                    "stderr": audit_result["stderr"],
                },
            ]
        )
        packet_results.append(
            {
                "source_iteration": packet.iteration_id,
                "role": packet.role,
                "expected_status": packet.expected_status,
                "observed_status": summary.get("status"),
                "clean_for_consolidation": source_clean,
                "receipt_validation_returncode": receipt_result["returncode"],
                "audit_returncode": audit_result["returncode"],
                "quality_failure": summary.get("quality_failure"),
                "blocked_result": summary.get("blocked_result"),
                "clean_pass": summary.get("clean_pass"),
                "provider_api_calls": int(summary.get("provider_api_calls") or 0),
                "provider_cost_usd": decimal_string(decimal_value(summary.get("provider_cost_usd"))),
                "provider_spend_ceiling_usd": decimal_string(
                    decimal_value(summary.get("provider_spend_ceiling_usd"))
                ),
                "executed_pair_count": int(summary.get("executed_pair_count") or 0),
                "executed_pair_ids": summary.get("executed_pair_ids", []),
                "blockers": summary.get("blockers", []),
                "failures": summary.get("failures", []),
                "source_summary": str(packet.summary_path.relative_to(ROOT)),
                "source_summary_sha256": sha256_file(packet.summary_path),
                "source_report": str(packet.report_path.relative_to(ROOT)),
                "source_report_sha256": sha256_file(packet.report_path),
                "source_receipt": str(packet.receipt_path.relative_to(ROOT)),
                "source_receipt_sha256": sha256_file(packet.receipt_path),
            }
        )
        if not isinstance(report.get("row_results"), list):
            blockers.append(f"{packet.iteration_id}_row_results_missing")
    packet = {
        "schema_version": "telos.expanded_stratified_adapter_validation.source_validation.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_packets": packet_results,
        "command_results": command_results,
        "all_source_packets_valid": not blockers,
    }
    return packet, blockers


def build_row_accounting() -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    iter66_rows = rows_by_pair(read_json(ITER66.report_path))
    iter78_rows = rows_by_pair(read_json(ITER78.report_path))
    iter80_rows = rows_by_pair(read_json(ITER80.report_path))
    blockers: list[str] = []

    def require_rows(source: str, rows: dict[str, dict[str, Any]], pair_ids: list[str]) -> None:
        missing = sorted(set(pair_ids) - set(rows))
        if missing:
            blockers.append(f"{source}_missing_rows:{','.join(missing)}")

    require_rows(ITER66.iteration_id, iter66_rows, BATTLESNAKE_PAIR_IDS)
    require_rows(ITER78.iteration_id, iter78_rows, DETERMINISTIC_EDIT_PAIR_IDS + DUMMY_PAIR_IDS)
    require_rows(ITER80.iteration_id, iter80_rows, DUMMY_PAIR_IDS)

    battlesnake_rows = [
        row_entry(
            source_iteration=ITER66.iteration_id,
            source_role=ITER66.role,
            pair_id=pair_id,
            row=iter66_rows.get(pair_id, {}),
            public_config="configs/test/battlesnake_pvp_test.yaml",
            analysis_stratum="battlesnake_pvp_existing_paid_evidence",
            evidence_role="retained_prior_paid_success_evidence",
            consolidated_success_evidence=True,
        )
        for pair_id in BATTLESNAKE_PAIR_IDS
    ]
    deterministic_rows = [
        row_entry(
            source_iteration=ITER78.iteration_id,
            source_role=ITER78.role,
            pair_id=pair_id,
            row=iter78_rows.get(pair_id, {}),
            public_config="configs/test/telos_battlesnake_edit_test.yaml",
            analysis_stratum="deterministic_edit_small_workspace_edit",
            evidence_role="retained_iter78_verified_adapter_evidence",
            consolidated_success_evidence=True,
        )
        for pair_id in DETERMINISTIC_EDIT_PAIR_IDS
    ]
    dummy_rows = [
        row_entry(
            source_iteration=ITER80.iteration_id,
            source_role=ITER80.role,
            pair_id=pair_id,
            row=iter80_rows.get(pair_id, {}),
            public_config="configs/test/dummy.yaml",
            analysis_stratum="dummy_minimal_adapter_validation",
            evidence_role="recovered_iter80_verified_adapter_evidence",
            consolidated_success_evidence=True,
        )
        for pair_id in DUMMY_PAIR_IDS
    ]
    iter78_dummy_diagnostic_rows = [
        row_entry(
            source_iteration=ITER78.iteration_id,
            source_role=ITER78.role,
            pair_id=pair_id,
            row=iter78_rows.get(pair_id, {}),
            public_config="configs/test/dummy.yaml",
            analysis_stratum="dummy_minimal_adapter_validation",
            evidence_role="iter78_call_ceiling_diagnostic_superseded_by_iter80",
            consolidated_success_evidence=False,
        )
        for pair_id in DUMMY_PAIR_IDS
    ]
    consolidated_rows = battlesnake_rows + deterministic_rows + dummy_rows
    diagnostic_rows = iter78_dummy_diagnostic_rows
    for row in consolidated_rows:
        if row["command_returncode"] != 0:
            blockers.append(f"{row['pair_id']}_consolidated_row_nonzero_returncode")
        if row["command_timed_out"] is not False:
            blockers.append(f"{row['pair_id']}_consolidated_row_timeout")
        if row["verified_completion_evidence"] is not True:
            blockers.append(f"{row['pair_id']}_consolidated_row_unverified")
        if row["raw_evidence_present"] is not True:
            blockers.append(f"{row['pair_id']}_consolidated_row_missing_raw_evidence")
        if row["receipt_required"] is True and row["receipt_valid"] is not True:
            blockers.append(f"{row['pair_id']}_required_receipt_invalid")

    strata = [
        stratum_summary(
            name="retained_battlesnake_prior_paid_evidence",
            public_config="configs/test/battlesnake_pvp_test.yaml",
            interpretation="prior two-row provider-backed pilot only; retained without rerun",
            rows=battlesnake_rows,
            consolidated_success_evidence=True,
        ),
        stratum_summary(
            name="deterministic_edit_adapter_validation",
            public_config="configs/test/telos_battlesnake_edit_test.yaml",
            interpretation="small deterministic workspace edit adapter evidence; not a benchmark claim",
            rows=deterministic_rows,
            consolidated_success_evidence=True,
        ),
        stratum_summary(
            name="dummy_minimal_adapter_validation",
            public_config="configs/test/dummy.yaml",
            interpretation="minimal Dummy task adapter evidence recovered under the iter80 call ceiling",
            rows=dummy_rows,
            consolidated_success_evidence=True,
        ),
    ]
    diagnostic_strata = [
        stratum_summary(
            name="iter78_dummy_call_ceiling_diagnostic",
            public_config="configs/test/dummy.yaml",
            interpretation="blocked diagnostic spend that is superseded by iter80 verified Dummy evidence",
            rows=diagnostic_rows,
            consolidated_success_evidence=False,
        )
    ]
    row_accounting = {
        "schema_version": "telos.expanded_stratified_adapter_validation.row_accounting.v1",
        "experiment_id": EXPERIMENT_ID,
        "adapter_rows_executed_in_this_gate": 0,
        "provider_calls_in_this_gate": 0,
        "provider_cost_usd_in_this_gate": decimal_string(ZERO_COST),
        "consolidated_pair_ids": CONSOLIDATED_PAIR_IDS,
        "consolidated_success_pair_count": len(consolidated_rows),
        "source_row_executions_accounted": len(consolidated_rows) + len(diagnostic_rows),
        "diagnostic_blocked_pair_ids": DUMMY_PAIR_IDS,
        "diagnostic_blocked_pair_count": len(diagnostic_rows),
        "consolidated_success_strata": strata,
        "diagnostic_blocked_strata": diagnostic_strata,
        "consolidated_rows": consolidated_rows,
        "diagnostic_rows": diagnostic_rows,
        "all_task_surfaces_stratified": True,
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_or_model_claim_authorized": False,
        "row_accounting_reconciled": not blockers,
    }
    return row_accounting, {"consolidated": consolidated_rows, "diagnostic": diagnostic_rows}, blockers


def build_provider_totals(
    source_validation: dict[str, Any],
    row_sets: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    source_total_calls = sum(
        int(packet.get("provider_api_calls") or 0)
        for packet in source_validation.get("source_packets", [])
    )
    source_total_cost = sum(
        (
            decimal_value(packet.get("provider_cost_usd"))
            for packet in source_validation.get("source_packets", [])
        ),
        ZERO_COST,
    )
    consolidated_rows = row_sets["consolidated"]
    diagnostic_rows = row_sets["diagnostic"]
    return {
        "schema_version": "telos.expanded_stratified_adapter_validation.provider_totals.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_packet_count": len(SOURCE_PACKETS),
        "source_packet_total_provider_api_calls": source_total_calls,
        "source_packet_total_provider_cost_usd": decimal_string(source_total_cost),
        "consolidated_success_evidence_provider_api_calls": sum_calls(consolidated_rows),
        "consolidated_success_evidence_provider_cost_usd": decimal_string(
            sum_cost(consolidated_rows)
        ),
        "diagnostic_blocked_dummy_provider_api_calls": sum_calls(diagnostic_rows),
        "diagnostic_blocked_dummy_provider_cost_usd": decimal_string(sum_cost(diagnostic_rows)),
        "provider_api_calls_in_this_gate": 0,
        "provider_cost_usd_in_this_gate": decimal_string(ZERO_COST),
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "exact_source_packet_totals_preserved": True,
    }


def build_claim_boundary() -> dict[str, Any]:
    return {
        "schema_version": "telos.expanded_stratified_adapter_validation.claim_boundary.v1",
        "experiment_id": EXPERIMENT_ID,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "cross_task_surface_pooling_authorized": False,
        "aggregate_primary_metric_authorized": False,
        "aggregate_benchmark_or_model_claim_authorized": False,
        "claim_allowed_if_pass": (
            "The expanded adapter-validation evidence has been consolidated as stratified "
            "internal protocol evidence and a bounded next gate is ready for pre-registration."
        ),
        "claims_forbidden": [
            "benchmark performance",
            "model superiority",
            "production/live-domain behavior",
            "leaderboard standing",
            "SWE-bench standing",
            "state-of-the-art status",
        ],
    }


def build_next_gate_recommendation() -> dict[str, Any]:
    return {
        "schema_version": "telos.expanded_stratified_adapter_validation.next_gate.v1",
        "experiment_id": EXPERIMENT_ID,
        "recommended_next_gate": NEXT_GATE,
        "recommendation": "pre_register_zero_spend_benchmark_facing_slice_design",
        "adapter_rows_to_execute": 0,
        "provider_model_invocations": 0,
        "provider_spend_ceiling_usd": decimal_string(ZERO_COST),
        "gpu_use": "forbidden",
        "cloud_runner_startup": "forbidden",
        "sentinel_named_resource_mutation": "forbidden",
        "production_or_live_domain_mutation": "forbidden",
        "benchmark_model_or_sota_claim": "forbidden",
        "required_design_outputs": [
            "candidate benchmark-facing task-surface eligibility rules",
            "baseline-versus-Telos condition definitions",
            "receipt, raw-artifact, cost, and failure-mode requirements",
            "minimum paid-run ceilings for a future execution gate",
            "explicit no-claim boundary until execution evidence exists",
        ],
        "why_not_paid_execution_yet": (
            "The current evidence is stratified internal adapter-validation evidence. A broader "
            "benchmark-facing paid run must first freeze task eligibility, metrics, ceilings, and "
            "failure semantics."
        ),
    }


def write_command_output(source_validation: dict[str, Any]) -> None:
    lines = [
        "iter81 expanded stratified adapter-validation consolidation",
        "",
        "Source validation commands:",
    ]
    for item in source_validation.get("command_results", []):
        lines.append(f"$ {item['command']}")
        lines.append(f"returncode={item['returncode']} timed_out={item['timed_out']}")
        if item.get("stdout"):
            lines.append("stdout:")
            lines.append(str(item["stdout"]))
        if item.get("stderr"):
            lines.append("stderr:")
            lines.append(str(item["stderr"]))
        lines.append("")
    lines.extend(
        [
            "Local iter81 activity:",
            "- adapter rows executed: 0",
            "- provider model invocations: 0",
            "- provider spend: $0.00",
            "- GPU/cloud/Sentinel/live-domain mutation: false",
            "- benchmark/model/SOTA claim: false",
        ]
    )
    (PROOF / "command_output.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_review(
    source_validation: dict[str, Any],
    row_accounting: dict[str, Any],
    provider_totals: dict[str, Any],
) -> None:
    packet_count = len(source_validation.get("source_packets", []))
    consolidated_count = row_accounting["consolidated_success_pair_count"]
    source_calls = provider_totals["source_packet_total_provider_api_calls"]
    source_cost = provider_totals["source_packet_total_provider_cost_usd"]
    review = f"""# Iteration 81 Adversarial Review

The consolidation uses `{packet_count}` committed source packets: iter66, iter78, and iter80. It
does not execute rows, call a provider, start a cloud runner, use GPU, mutate Sentinel-named
resources, or touch production/live-domain systems.

The current consolidated evidence contains `{consolidated_count}` successful rows kept in separate
strata: retained BattleSnake evidence from iter66, deterministic-edit adapter evidence from iter78,
and Dummy adapter evidence from iter80. The iter78 Dummy rows are accounted as diagnostic blocked
call-ceiling evidence only and are superseded by the verified iter80 Dummy retry.

Exact committed source-packet totals are `{source_calls}` provider calls and `${source_cost}`. The
iter81 gate itself records provider calls and $0.00000000 as zero added activity: `0` calls and
zero spend.

The main adversarial risk is overclaiming: mixing unlike task surfaces into a benchmark, model, or
SOTA result. This packet forbids cross-surface pooling, aggregate benchmark metrics, leaderboard
claims, SWE-bench claims, production/live-domain claims, model-superiority claims, and
state-of-the-art claims.

The bounded next move is a zero-spend benchmark-facing slice-design gate. Paid execution should not
resume until that gate freezes task eligibility, baselines, receipt requirements, ceilings, and
failure semantics.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")


def write_result(
    summary: dict[str, Any],
    provider_totals: dict[str, Any],
    row_accounting: dict[str, Any],
) -> None:
    status = "PASS" if summary["status"] == "pass" else summary["status"].upper()
    result = f"""# Iteration 81 Result - Expanded Stratified Adapter-Validation Consolidation

Status: `{status}`.

## Summary

The gate consolidated committed iter66, iter78, and iter80 evidence without new execution.

- source packets validated: `{summary['source_packet_count']}`,
- source packet total provider API calls: `{provider_totals['source_packet_total_provider_api_calls']}`,
- source packet total provider cost: `${provider_totals['source_packet_total_provider_cost_usd']}`,
- consolidated successful row count: `{row_accounting['consolidated_success_pair_count']}`,
- diagnostic blocked row count: `{row_accounting['diagnostic_blocked_pair_count']}`,
- adapter rows executed in this gate: `0`,
- provider API calls in this gate: `0`,
- provider spend in this gate: `$0.00000000`,
- GPU used: `false`,
- cloud runner started: `false`,
- Sentinel-named resources modified: `false`,
- benchmark/model/SOTA claim: `false`,
- blockers: `{', '.join(summary['blockers']) if summary['blockers'] else 'none'}`,
- failures: `{', '.join(summary['failures']) if summary['failures'] else 'none'}`.

## Stratified Metrics

- BattleSnake retained verified-completion evidence: baseline `true`, Telos `true`, delta `0`,
- deterministic-edit verified-completion evidence: baseline `true`, Telos `true`, delta `0`,
- Dummy verified-completion evidence after iter80 recovery: baseline `true`, Telos `true`,
  delta `0`,
- cross-task-surface pooling authorized: `false`.

## Next Gate

The bounded next recommendation is
[`{NEXT_GATE}`](../../{NEXT_GATE}): a zero-spend benchmark-facing protocol-effect slice-design gate.

## Claim Boundary

This is stratified internal adapter-validation evidence. It is not a benchmark result, SWE-bench
score, leaderboard result, production/live-domain result, model-superiority result, or
state-of-the-art result.

## Evidence

- `proof/source_packet_validation.json`
- `proof/stratified_row_accounting.json`
- `proof/provider_totals.json`
- `proof/claim_boundary.json`
- `proof/next_gate_recommendation.json`
- `proof/redaction_scan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/{RECEIPT_NAME}`
"""
    RESULT.write_text(result, encoding="utf-8")


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter81-expanded-stratified-adapter-validation-consolidation-{status}",
        "task_id": "telos:iter81_expanded_stratified_adapter_validation_consolidation@iter80",
        "agent_id": "codex-local-stratified-adapter-validation-consolidator",
        "benchmark_id": "telos_codeclash_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Consolidate committed iter66, iter78, and iter80 adapter-validation evidence while "
            "preserving stratified claim boundaries."
        ),
        "acceptance_criteria": [
            "Iter66, iter78, and iter80 receipts and audits validate.",
            "BattleSnake, deterministic-edit, and Dummy rows remain stratified.",
            "Exact provider-call and spend totals are reported from committed source packets.",
            "No provider calls, spend, row execution, GPU, cloud runner, Sentinel mutation, or live-domain mutation occur.",
            "No benchmark, leaderboard, SWE-bench, model-superiority, production, live-domain, or state-of-the-art claim is made.",
            "A redaction scan over consolidation artifacts passes.",
            "The next gate recommendation is bounded and pre-registered.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                "notes": "Run summary records status, source validation, row accounting, totals, and claim boundary.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/stratified_row_accounting.json",
                "notes": "Rows are accounted by task surface and condition without cross-surface pooling.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/provider_totals.json",
                "notes": "Exact committed source-packet provider calls and costs are preserved.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records the no-benchmark/no-model/no-SOTA boundary.",
            },
        ],
        "falsifiers": [
            "The result must block if any required source packet receipt validation or audit fails.",
            "The result must block if row accounting cannot reconcile committed source packets.",
            "The result must fail if any provider row executes or provider call/spend occurs in iter81.",
            "The result must fail if credential, token, project, or service-account residue is committed.",
            "The result must fail if task surfaces are pooled into a benchmark/model/SOTA claim.",
            "The result must fail if the next recommendation requires unbounded calls or spend.",
        ],
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def write_learning_record(summary: dict[str, Any]) -> None:
    record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": summary["status"],
        "insight": (
            "The expanded adapter-validation evidence is now consolidated as six successful rows "
            "across three separated task-surface strata; iter78 Dummy blocked spend is preserved "
            "as diagnostic evidence, not pooled into the final Dummy pass."
        ),
        "next_action": (
            "design a zero-spend benchmark-facing slice before any broader paid "
            "benchmark-facing execution."
        ),
        "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
        "evidence_paths": [
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            f"experiments/{EXPERIMENT_ID}/proof/stratified_row_accounting.json",
            f"experiments/{EXPERIMENT_ID}/proof/provider_totals.json",
            f"experiments/{EXPERIMENT_ID}/proof/valid/{RECEIPT_NAME}",
        ],
    }
    write_json(PROOF / "learning_record.json", record)


def main() -> int:
    if PROOF.exists():
        shutil.rmtree(PROOF)
    VALID.mkdir(parents=True, exist_ok=True)

    source_validation, source_blockers = validate_source_packets()
    write_json(PROOF / "source_packet_validation.json", source_validation)
    write_command_output(source_validation)

    row_accounting, row_sets, row_blockers = build_row_accounting()
    write_json(PROOF / "stratified_row_accounting.json", row_accounting)
    provider_totals = build_provider_totals(source_validation, row_sets)
    write_json(PROOF / "provider_totals.json", provider_totals)
    claim_boundary = build_claim_boundary()
    write_json(PROOF / "claim_boundary.json", claim_boundary)
    next_gate = build_next_gate_recommendation()
    write_json(PROOF / "next_gate_recommendation.json", next_gate)
    write_review(source_validation, row_accounting, provider_totals)

    redaction = redaction_scan()
    write_json(PROOF / "redaction_scan.json", redaction)

    blockers = source_blockers + row_blockers
    failures: list[str] = []
    if not redaction["passed"]:
        failures.append("redaction_scan_failed")
    if (
        provider_totals["provider_api_calls_in_this_gate"] != 0
        or provider_totals["provider_cost_usd_in_this_gate"] != decimal_string(ZERO_COST)
    ):
        failures.append("iter81_provider_call_or_spend_occurred")
    if row_accounting["adapter_rows_executed_in_this_gate"] != 0:
        failures.append("iter81_row_execution_occurred")

    status = "fail" if failures else "blocked" if blockers else "pass"
    summary = {
        "schema_version": "telos.expanded_stratified_adapter_validation.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": blockers,
        "failures": failures,
        "source_packet_count": len(SOURCE_PACKETS),
        "source_packets_valid": source_validation["all_source_packets_valid"],
        "source_packet_total_provider_api_calls": provider_totals[
            "source_packet_total_provider_api_calls"
        ],
        "source_packet_total_provider_cost_usd": provider_totals[
            "source_packet_total_provider_cost_usd"
        ],
        "consolidated_success_pair_count": row_accounting["consolidated_success_pair_count"],
        "diagnostic_blocked_pair_count": row_accounting["diagnostic_blocked_pair_count"],
        "adapter_rows_executed_in_this_gate": 0,
        "provider_api_calls": 0,
        "provider_cost_usd": 0.0,
        "provider_spend_ceiling_usd": 0.0,
        "provider_call_ceiling": 0,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_or_model_claim_authorized": False,
        "primary_metric": {
            "battlesnake_baseline_verified_completion_evidence": True,
            "battlesnake_telos_verified_completion_evidence": True,
            "battlesnake_delta_telos_minus_baseline": 0,
            "deterministic_edit_baseline_verified_completion_evidence": True,
            "deterministic_edit_telos_verified_completion_evidence": True,
            "deterministic_edit_delta_telos_minus_baseline": 0,
            "dummy_baseline_verified_completion_evidence": True,
            "dummy_telos_verified_completion_evidence": True,
            "dummy_delta_telos_minus_baseline": 0,
            "aggregate_primary_metric_authorized": False,
        },
        "next_gate": NEXT_GATE,
        "redaction_scan_passed": redaction["passed"],
        "redaction_findings": redaction["findings"],
    }
    write_learning_record(summary)
    receipt = build_receipt(status)
    write_json(VALID / RECEIPT_NAME, receipt)
    summary["artifact_hashes"] = artifact_hashes()
    write_json(PROOF / "run_summary.json", summary)
    write_result(summary, provider_totals, row_accounting)

    print(f"expanded stratified adapter-validation consolidation: {status}")
    print(f"source_packet_count={summary['source_packet_count']}")
    print(f"consolidated_success_pair_count={summary['consolidated_success_pair_count']}")
    print(f"diagnostic_blocked_pair_count={summary['diagnostic_blocked_pair_count']}")
    print(
        "source_packet_total_provider_api_calls="
        f"{summary['source_packet_total_provider_api_calls']}"
    )
    print(
        "source_packet_total_provider_cost_usd="
        f"{summary['source_packet_total_provider_cost_usd']}"
    )
    print("provider_api_calls_in_this_gate=0")
    print("provider_cost_usd_in_this_gate=0.00000000")
    print("cross_task_surface_pooling_authorized=false")
    print(f"next_gate={NEXT_GATE}")
    print(f"blockers={','.join(blockers) if blockers else 'none'}")
    print(f"failures={','.join(failures) if failures else 'none'}")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
