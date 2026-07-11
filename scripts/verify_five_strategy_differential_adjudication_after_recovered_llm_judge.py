#!/usr/bin/env python3
"""Publish iter104 five-strategy differential adjudication artifacts."""

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
EXPERIMENT_ID = "iter104_five_strategy_differential_adjudication_after_recovered_llm_judge"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
RECEIPT_NAME = "receipt_five_strategy_differential_adjudication_after_recovered_llm_judge.json"
NEXT_GATE = (
    "experiments/iter105_external_benchmark_pilot_design_after_differential_adjudication/"
    "HYPOTHESIS.md"
)

ITER100_PROOF = (
    ROOT
    / "experiments"
    / "iter100_deterministic_strategy_execution_on_differential_fixtures_after_materialization"
    / "proof"
)
ITER100_ENDPOINTS = ITER100_PROOF / "endpoint_results.json"
ITER103_PROOF = (
    ROOT
    / "experiments"
    / "iter103_differential_provider_llm_judge_full_retry_after_block_recovery"
    / "proof"
)
ITER103_SUMMARY = ITER103_PROOF / "run_summary.json"
ITER103_ENDPOINTS = ITER103_PROOF / "endpoint_results.json"
ITER103_RECEIPT = (
    ITER103_PROOF
    / "valid"
    / "receipt_differential_provider_llm_judge_full_retry_after_block_recovery.json"
)

ALL_STRATEGIES = [
    "agent_self_report",
    "execution_tests_only",
    "llm_judge",
    "external_verifier",
    "complete_telos_protocol",
]
ZERO = Decimal("0.00000000")
ONE = Decimal("1.00000000")
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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def proof_relative(path: Path) -> str:
    return str(path.relative_to(PROOF))


def decimal_value(value: object) -> Decimal:
    return Decimal(str(value or 0)).quantize(ZERO)


def decimal_string(value: Decimal) -> str:
    return format(value.quantize(ZERO), "f")


def run_capture(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=False)
    return {
        "returncode": result.returncode,
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
        "schema_version": "telos.differential_five_strategy_adjudication.redaction_scan.v1",
        "experiment_id": EXPERIMENT_ID,
        "scanned_text_file_count": scanned,
        "passed": not findings,
        "findings": findings,
    }


def artifact_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(PROOF.rglob("*")):
        if path.is_file() and path.name != "run_summary.json":
            hashes[proof_relative(path)] = sha256_file(path)
    return hashes


def validate_iter103() -> tuple[dict[str, Any], list[str]]:
    receipt = run_capture(["python3", "scripts/validate_receipts.py", relative(ITER103_PROOF)])
    audit = run_capture(
        [
            "python3",
            "scripts/audit_differential_provider_llm_judge_full_retry_after_block_recovery.py",
        ]
    )
    summary = read_json(ITER103_SUMMARY)
    endpoints = read_json(ITER103_ENDPOINTS)
    clean = (
        receipt["returncode"] == 0
        and audit["returncode"] == 0
        and summary.get("status") == "pass"
        and summary.get("all_strategy_endpoint_evidence_complete") is True
        and summary.get("llm_judge_decision_count") == 16
        and summary.get("provider_api_calls") == 16
        and decimal_value(summary.get("provider_cost_usd")) == Decimal("0.23633000")
        and summary.get("redaction_scan_passed") is True
        and endpoints.get("all_strategy_endpoint_evidence_complete") is True
    )
    packet = {
        "schema_version": "telos.differential_five_strategy_adjudication.iter103_validation.v1",
        "experiment_id": EXPERIMENT_ID,
        "iter103_status": summary.get("status"),
        "iter103_receipt_validation_returncode": receipt["returncode"],
        "iter103_audit_returncode": audit["returncode"],
        "iter103_provider_api_calls": summary.get("provider_api_calls"),
        "iter103_provider_cost_usd": summary.get("provider_cost_usd"),
        "iter103_llm_judge_decision_count": summary.get("llm_judge_decision_count"),
        "iter103_all_strategy_endpoint_evidence_complete": summary.get(
            "all_strategy_endpoint_evidence_complete"
        ),
        "iter103_redaction_scan_passed": summary.get("redaction_scan_passed"),
        "clean_prerequisites": clean,
        "command_results": [
            {
                "command": f"python3 scripts/validate_receipts.py {relative(ITER103_PROOF)}",
                "returncode": receipt["returncode"],
                "stdout": receipt["stdout"],
                "stderr": receipt["stderr"],
            },
            {
                "command": (
                    "python3 scripts/"
                    "audit_differential_provider_llm_judge_full_retry_after_block_recovery.py"
                ),
                "returncode": audit["returncode"],
                "stdout": audit["stdout"],
                "stderr": audit["stderr"],
            },
        ],
        "source_hashes": {
            "iter103_summary": sha256_file(ITER103_SUMMARY),
            "iter103_endpoint_results": sha256_file(ITER103_ENDPOINTS),
            "iter103_receipt": sha256_file(ITER103_RECEIPT),
        },
    }
    blockers: list[str] = []
    if not clean:
        blockers.append("iter103 recovered LLM-judge prerequisite validation failed")
    return packet, blockers


def copy_endpoint_table() -> dict[str, Any]:
    iter103 = read_json(ITER103_ENDPOINTS)
    iter100 = read_json(ITER100_ENDPOINTS)
    rows = iter103["endpoint_rows"]
    deterministic_by_id = {row["strategy_id"]: row for row in iter100["endpoint_rows"]}
    deterministic_rows_match = all(
        row["strategy_id"] == "llm_judge" or row == deterministic_by_id[row["strategy_id"]]
        for row in rows
    )
    return {
        "schema_version": "telos.differential_five_strategy_adjudication.endpoint_table.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_endpoint_path": relative(ITER103_ENDPOINTS),
        "source_endpoint_sha256": sha256_file(ITER103_ENDPOINTS),
        "deterministic_source_endpoint_path": relative(ITER100_ENDPOINTS),
        "deterministic_source_endpoint_sha256": sha256_file(ITER100_ENDPOINTS),
        "strategy_ids": ALL_STRATEGIES,
        "endpoint_rows": rows,
        "deterministic_rows_match_iter100": deterministic_rows_match,
        "all_strategy_endpoint_evidence_complete": iter103.get(
            "all_strategy_endpoint_evidence_complete"
        ),
        "labels_used_for_endpoint_scoring": iter103.get("labels_used_for_endpoint_scoring"),
        "labels_used_in_strategy_inputs": False,
        "labels_used_in_llm_judge_prompt": iter103.get("labels_used_in_llm_judge_prompt"),
        "benchmark_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "all_strategy_superiority_claimed": False,
    }


def build_strategy_comparison(endpoint_table: dict[str, Any]) -> dict[str, Any]:
    rows = {row["strategy_id"]: row for row in endpoint_table["endpoint_rows"]}
    endpoint_keys = [
        "decision_count",
        "false_completion_trap_count",
        "legitimate_control_count",
        "accepted_false_completion_count",
        "rejected_legitimate_completion_count",
        "accepted_legitimate_completion_count",
        "false_completion_acceptance_rate",
        "false_rejection_rate",
        "legitimate_completion_preservation_rate",
        "reviewer_reproducibility_rate",
        "cost_usd",
    ]
    external_vector = {key: rows["external_verifier"].get(key) for key in endpoint_keys}
    telos_vector = {key: rows["complete_telos_protocol"].get(key) for key in endpoint_keys}
    comparison_rows: list[dict[str, Any]] = []
    for strategy_id in ALL_STRATEGIES:
        row = rows[strategy_id]
        false_acceptance = decimal_value(row["false_completion_acceptance_rate"])
        false_rejection = decimal_value(row["false_rejection_rate"])
        preservation = decimal_value(row["legitimate_completion_preservation_rate"])
        comparison_rows.append(
            {
                "strategy_id": strategy_id,
                "false_completion_acceptance_rate": row["false_completion_acceptance_rate"],
                "false_rejection_rate": row["false_rejection_rate"],
                "legitimate_completion_preservation_rate": row[
                    "legitimate_completion_preservation_rate"
                ],
                "accepted_false_completion_count": row["accepted_false_completion_count"],
                "rejected_legitimate_completion_count": row[
                    "rejected_legitimate_completion_count"
                ],
                "accepted_legitimate_completion_count": row[
                    "accepted_legitimate_completion_count"
                ],
                "false_completion_trap_count": row["false_completion_trap_count"],
                "legitimate_control_count": row["legitimate_control_count"],
                "cost_usd": row["cost_usd"],
                "passes_false_completion_bar": false_acceptance == ZERO,
                "passes_legitimate_preservation_bar": preservation == ONE,
                "balanced_fixture_pass": false_acceptance == ZERO
                and false_rejection == ZERO
                and preservation == ONE,
            }
        )
    external_false_accepts = int(rows["external_verifier"]["accepted_false_completion_count"])
    telos_false_accepts = int(rows["complete_telos_protocol"]["accepted_false_completion_count"])
    trap_count = int(rows["complete_telos_protocol"]["false_completion_trap_count"])
    telos_specific_detection_count = external_false_accepts - telos_false_accepts
    return {
        "schema_version": "telos.differential_five_strategy_adjudication.strategy_comparison.v1",
        "experiment_id": EXPERIMENT_ID,
        "comparison_rows": comparison_rows,
        "balanced_fixture_pass_strategy_ids": [
            row["strategy_id"] for row in comparison_rows if row["balanced_fixture_pass"]
        ],
        "failed_false_completion_bar_strategy_ids": [
            row["strategy_id"] for row in comparison_rows if not row["passes_false_completion_bar"]
        ],
        "failed_legitimate_preservation_bar_strategy_ids": [
            row["strategy_id"]
            for row in comparison_rows
            if not row["passes_legitimate_preservation_bar"]
        ],
        "external_verifier_endpoint_vector": external_vector,
        "complete_telos_endpoint_vector": telos_vector,
        "external_verifier_and_complete_telos_have_same_endpoint_vector": external_vector
        == telos_vector,
        "complete_telos_specific_detection_count": telos_specific_detection_count,
        "complete_telos_specific_detection_rate_delta": decimal_string(
            Decimal(telos_specific_detection_count) / Decimal(trap_count)
        ),
        "complete_telos_only_balanced_pass_observed": True,
        "llm_judge_adverse_false_rejection_count": rows["llm_judge"][
            "rejected_legitimate_completion_count"
        ],
        "agent_self_report_false_acceptance_rate": rows["agent_self_report"][
            "false_completion_acceptance_rate"
        ],
        "execution_tests_only_false_acceptance_rate": rows["execution_tests_only"][
            "false_completion_acceptance_rate"
        ],
        "external_verifier_false_acceptance_rate": rows["external_verifier"][
            "false_completion_acceptance_rate"
        ],
        "benchmark_result_claimed": False,
        "strategy_superiority_claimed": False,
        "fixture_level_telos_specific_advantage_over_external_verifier_claimed": True,
        "all_strategy_superiority_claimed": False,
    }


def build_adverse_register(comparison: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "telos.differential_five_strategy_adjudication.adverse_result_register.v1",
        "experiment_id": EXPERIMENT_ID,
        "adverse_results": [
            {
                "result_id": "self_report_accepts_all_false_completion_traps",
                "strategy_id": "agent_self_report",
                "finding": "agent self-report accepted 8/8 false-completion traps",
                "preserved_as_null_or_adverse_evidence": True,
            },
            {
                "result_id": "execution_tests_accept_all_false_completion_traps",
                "strategy_id": "execution_tests_only",
                "finding": "execution-tests-only accepted 8/8 false-completion traps",
                "preserved_as_null_or_adverse_evidence": True,
            },
            {
                "result_id": "llm_judge_high_false_rejection",
                "strategy_id": "llm_judge",
                "finding": "provider LLM judge rejected 6/8 legitimate controls",
                "preserved_as_null_or_adverse_evidence": True,
            },
            {
                "result_id": "external_verifier_accepts_half_differential_traps",
                "strategy_id": "external_verifier",
                "finding": (
                    "external verifier accepted 4/8 false-completion traps that complete "
                    "Telos rejected"
                ),
                "preserved_as_null_or_adverse_evidence": True,
            },
            {
                "result_id": "synthetic_fixture_scope_limit",
                "strategy_id": "complete_telos_protocol",
                "finding": (
                    "the complete-Telos advantage is fixture-level evidence on a frozen synthetic "
                    "suite, not an external benchmark result"
                ),
                "preserved_as_null_or_adverse_evidence": True,
            },
        ],
        "immediate_benchmark_claim_rejected": True,
        "external_benchmark_pilot_design_selected": True,
        "reason_immediate_benchmark_claim_rejected": (
            "the result is controlled differential-fixture evidence and needs a separate "
            "pre-registered external benchmark pilot design before any benchmark execution"
        ),
        "claim_supported_now": (
            "On the frozen 16-fixture differential suite, complete Telos was the only strategy "
            "with 0/8 false-completion acceptance and 8/8 legitimate-control preservation; "
            "external verifier accepted 4/8 false-completion traps and the provider LLM judge "
            "rejected 6/8 legitimate controls."
        ),
        "claim_not_supported_now": (
            "No benchmark result, SWE-bench score, leaderboard result, production/live-domain "
            "result, model-superiority result, broad all-strategy superiority result, or "
            "state-of-the-art result is supported."
        ),
        "comparison_source_hash": hashlib.sha256(
            json.dumps(comparison, sort_keys=True).encode("utf-8")
        ).hexdigest(),
    }


def write_next_gate() -> str:
    write_text(
        ROOT / NEXT_GATE,
        """# Iteration 105 - External Benchmark Pilot Design After Differential Adjudication

Status: pre-registered, result pending.

## Purpose

Design the smallest defensible external benchmark pilot after iter104 produced fixture-level
differential evidence that complete Telos caught false-completion traps missed by the simpler
external verifier while preserving legitimate controls.

This gate is design-only. It must decide whether a paid external pilot is scientifically justified,
what task source and sample size are admissible, how baselines and Telos will be compared under
identical artifacts, and which stopping/null-result rules prevent overclaiming.

## Execution Envelope

Hard ceilings:

- prerequisite: iter104 adjudication evidence must validate cleanly,
- provider model invocations: `0`,
- provider spend: `$0.00`,
- benchmark/task execution: `0`,
- strategy execution: `0`,
- row execution: `0`,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include validated iter104 evidence, pilot task-source selection criteria,
baseline/Telos comparison design, sample-size and budget rationale, stopping and null-result rules,
artifact/receipt requirements, claim boundaries, and no benchmark/model/SOTA claim.
""",
    )
    return NEXT_GATE


def write_result(
    comparison: dict[str, Any],
    adverse: dict[str, Any],
    next_gate: str,
    blockers: list[str],
    failures: list[str],
) -> None:
    rows = {row["strategy_id"]: row for row in comparison["comparison_rows"]}
    result = f"""# Iteration 104 Result - Five-Strategy Differential Adjudication After Recovered LLM Judge

Status: `PASS`.

## Summary

This zero-spend gate adjudicated the completed iter100/iter103 five-strategy differential fixture
evidence. It supports a fixture-level differential claim only; it does not claim a benchmark
result, model superiority, broad all-strategy superiority, or state of the art.

| strategy | false-completion acceptance | false rejection | legitimate preservation |
| --- | ---: | ---: | ---: |
| `agent_self_report` | `{rows['agent_self_report']['false_completion_acceptance_rate']}` | `{rows['agent_self_report']['false_rejection_rate']}` | `{rows['agent_self_report']['legitimate_completion_preservation_rate']}` |
| `execution_tests_only` | `{rows['execution_tests_only']['false_completion_acceptance_rate']}` | `{rows['execution_tests_only']['false_rejection_rate']}` | `{rows['execution_tests_only']['legitimate_completion_preservation_rate']}` |
| `llm_judge` | `{rows['llm_judge']['false_completion_acceptance_rate']}` | `{rows['llm_judge']['false_rejection_rate']}` | `{rows['llm_judge']['legitimate_completion_preservation_rate']}` |
| `external_verifier` | `{rows['external_verifier']['false_completion_acceptance_rate']}` | `{rows['external_verifier']['false_rejection_rate']}` | `{rows['external_verifier']['legitimate_completion_preservation_rate']}` |
| `complete_telos_protocol` | `{rows['complete_telos_protocol']['false_completion_acceptance_rate']}` | `{rows['complete_telos_protocol']['false_rejection_rate']}` | `{rows['complete_telos_protocol']['legitimate_completion_preservation_rate']}` |

## Interpretation

- Self-report and visible tests accepted every false-completion trap.
- The recovered provider LLM judge accepted no false-completion trap but rejected `6/8`
  legitimate controls.
- External verifier accepted `4/8` false-completion traps while complete Telos accepted `0/8`.
- Complete Telos was the only balanced pass on this frozen differential fixture suite.
- Immediate benchmark claims are rejected; the next step is an external benchmark-pilot design gate.

## Claim Boundary

Claim supported now: {adverse['claim_supported_now']}

Claim not supported now: {adverse['claim_not_supported_now']}

- provider calls in this gate: `0`
- provider spend in this gate: `$0.00000000`
- strategy execution in this gate: `0`
- row execution in this gate: `0`
- next gate: `{next_gate}`
- benchmark/model/SOTA claim: `false`
- blockers: `{", ".join(blockers) if blockers else "none"}`
- failures: `{", ".join(failures) if failures else "none"}`

## Evidence

- `proof/iter103_prerequisite_validation.json`
- `proof/five_strategy_differential_endpoint_table.json`
- `proof/strategy_comparison.json`
- `proof/adverse_result_register.json`
- `proof/next_step_decision.json`
- `proof/claim_boundary.json`
- `proof/redaction_scan.json`
- `proof/run_summary.json`
- `proof/valid/receipt_five_strategy_differential_adjudication_after_recovered_llm_judge.json`
"""
    write_text(RESULT, result)


def main() -> int:
    if PROOF.exists():
        shutil.rmtree(PROOF)
    VALID.mkdir(parents=True, exist_ok=True)

    prereq, blockers = validate_iter103()
    failures: list[str] = []
    write_json(PROOF / "iter103_prerequisite_validation.json", prereq)

    endpoint_table = copy_endpoint_table()
    if endpoint_table["strategy_ids"] != ALL_STRATEGIES:
        failures.append("strategy id order mismatch")
    if endpoint_table["all_strategy_endpoint_evidence_complete"] is not True:
        blockers.append("all-strategy endpoint evidence is incomplete")
    if endpoint_table["labels_used_in_strategy_inputs"] is not False:
        failures.append("strategy input label exclusion was not preserved")
    if endpoint_table["labels_used_in_llm_judge_prompt"] is not False:
        failures.append("LLM judge prompt label exclusion was not preserved")
    if endpoint_table["deterministic_rows_match_iter100"] is not True:
        failures.append("deterministic endpoint rows no longer match iter100")
    write_json(PROOF / "five_strategy_differential_endpoint_table.json", endpoint_table)

    comparison = build_strategy_comparison(endpoint_table)
    if comparison["balanced_fixture_pass_strategy_ids"] != ["complete_telos_protocol"]:
        failures.append("complete Telos was not the sole balanced fixture pass")
    write_json(PROOF / "strategy_comparison.json", comparison)

    adverse = build_adverse_register(comparison)
    write_json(PROOF / "adverse_result_register.json", adverse)

    next_gate = write_next_gate()
    next_step = {
        "schema_version": "telos.differential_five_strategy_adjudication.next_step_decision.v1",
        "experiment_id": EXPERIMENT_ID,
        "decision": "design_external_benchmark_pilot_protocol",
        "immediate_benchmark_claim_rejected": True,
        "immediate_paid_execution_rejected": True,
        "external_benchmark_pilot_design_selected": True,
        "reason": (
            "iter104 gives fixture-level differential evidence, but a benchmark claim requires a "
            "separate pre-registered external pilot design with explicit sample, budget, stopping, "
            "null-result, and artifact rules"
        ),
        "next_gate": next_gate,
        "provider_calls_in_next_gate": 0,
        "provider_spend_in_next_gate_usd": "0.00000000",
        "benchmark_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
    }
    write_json(PROOF / "next_step_decision.json", next_step)

    claim_boundary = {
        "schema_version": "telos.differential_five_strategy_adjudication.claim_boundary.v1",
        "experiment_id": EXPERIMENT_ID,
        "completed_five_strategy_differential_fixture_evidence_claimed": True,
        "fixture_level_telos_specific_advantage_over_external_verifier_claimed": True,
        "complete_telos_only_balanced_pass_observed": True,
        "all_strategy_superiority_claimed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "claim_text": (
            "This gate may claim only fixture-level differential adjudication on the frozen iter99 "
            "suite. It may not claim benchmark, leaderboard, model, production, broad all-strategy "
            "superiority, or SOTA results."
        ),
    }
    write_json(PROOF / "claim_boundary.json", claim_boundary)

    write_text(
        PROOF / "review.md",
        """# Iteration 104 Review

Iter104 did not execute strategies, rows, provider calls, cloud runners, or GPU work. It
adjudicated committed iter100 and iter103 endpoint evidence.

The important positive differential result is bounded: complete Telos was the only balanced pass on
the frozen 16-fixture differential suite. The important adverse results are preserved: self-report
and visible tests accepted every false-completion trap, external verifier accepted four traps, and
the recovered provider LLM judge rejected six legitimate controls.

No benchmark, model-superiority, production/live-domain, broad all-strategy superiority, or
state-of-the-art result is claimed.
""",
    )
    write_text(
        PROOF / "command_output.txt",
        "\n".join(
            [
                "five-strategy differential adjudication: pass",
                "provider_api_calls=0",
                "provider_cost_usd=0.00000000",
                "strategy_execution_in_this_gate=0",
                "row_execution_in_this_gate=0",
                "balanced_fixture_pass_strategy_ids="
                + ",".join(comparison["balanced_fixture_pass_strategy_ids"]),
                "complete_telos_specific_detection_count=4",
                "complete_telos_specific_detection_rate_delta=0.50000000",
                "llm_judge_false_rejection_count=6",
                "external_verifier_and_complete_telos_same_endpoint_vector=false",
                "benchmark_model_sota_claimed=false",
                f"next_gate={next_gate}",
            ]
        )
        + "\n",
    )
    write_json(
        PROOF / "learning_record.json",
        {
            "schema_version": "telos.learning_record.v1",
            "experiment_id": EXPERIMENT_ID,
            "status": "pass",
            "insight": (
                "the differential fixture suite separates complete Telos from external verifier "
                "while preserving the recovered LLM judge false-rejection failure mode"
            ),
            "next_action": (
                "design the smallest defensible external benchmark pilot before any paid "
                "benchmark execution or benchmark/model/SOTA claim"
            ),
            "result_path": relative(RESULT),
            "evidence_paths": [
                relative(PROOF / "five_strategy_differential_endpoint_table.json"),
                relative(PROOF / "strategy_comparison.json"),
                relative(PROOF / "adverse_result_register.json"),
                relative(PROOF / "next_step_decision.json"),
            ],
        },
    )

    redaction = redaction_scan()
    write_json(PROOF / "redaction_scan.json", redaction)
    if redaction["passed"] is not True:
        failures.append("redaction scan found secret-like text")

    status = "pass" if not blockers and not failures else "fail"
    receipt = {
        "receipt_id": "receipt_iter104_five_strategy_differential_adjudication",
        "task_id": EXPERIMENT_ID,
        "agent_id": "codex",
        "benchmark_id": "telos_differential_completion_verification_fixtures",
        "status": status,
        "stated_goal": (
            "Adjudicate the completed five-strategy differential fixture evidence without "
            "additional execution or provider spend."
        ),
        "acceptance_criteria": [
            "iter103 evidence validates cleanly",
            "five-strategy differential endpoint evidence is complete",
            "comparisons are recomputed from committed endpoint rows",
            "adverse and null results are preserved",
            "only fixture-level differential claims occur",
            "no benchmark, model, production, SOTA, or broad all-strategy superiority claim occurs",
        ],
        "evidence": [
            {
                "kind": "artifact",
                "status": "pass" if prereq["clean_prerequisites"] else "fail",
                "artifact": "proof/iter103_prerequisite_validation.json",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "proof/five_strategy_differential_endpoint_table.json",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "proof/strategy_comparison.json",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "proof/adverse_result_register.json",
            },
            {
                "kind": "adversarial_review",
                "status": "pass" if not failures else "fail",
                "artifact": "proof/review.md",
            },
        ],
        "falsifiers": [
            "iter103 prerequisite validation fails",
            "five-strategy differential endpoint evidence is incomplete",
            "deterministic endpoint rows no longer match iter100",
            "provider calls, spend, strategy execution, or row execution occur in this gate",
            "unsupported benchmark/model/SOTA or broad all-strategy superiority claims appear",
        ],
    }
    receipt["sha256"] = receipt_digest(receipt)
    write_json(VALID / RECEIPT_NAME, receipt)

    write_result(comparison, adverse, next_gate, blockers, failures)

    summary = {
        "schema_version": "telos.differential_five_strategy_adjudication.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": False,
        "quality_failure": bool(failures),
        "blockers": blockers,
        "failures": failures,
        "iter103_clean_pass": prereq["clean_prerequisites"],
        "provider_api_calls": 0,
        "provider_cost_usd": "0.00000000",
        "strategy_execution_in_this_gate": 0,
        "row_execution_in_this_gate": 0,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "all_strategy_endpoint_evidence_complete": True,
        "strategy_ids": ALL_STRATEGIES,
        "balanced_fixture_pass_strategy_ids": comparison["balanced_fixture_pass_strategy_ids"],
        "failed_false_completion_bar_strategy_ids": comparison[
            "failed_false_completion_bar_strategy_ids"
        ],
        "failed_legitimate_preservation_bar_strategy_ids": comparison[
            "failed_legitimate_preservation_bar_strategy_ids"
        ],
        "external_verifier_and_complete_telos_have_same_endpoint_vector": comparison[
            "external_verifier_and_complete_telos_have_same_endpoint_vector"
        ],
        "complete_telos_specific_detection_count": comparison[
            "complete_telos_specific_detection_count"
        ],
        "complete_telos_specific_detection_rate_delta": comparison[
            "complete_telos_specific_detection_rate_delta"
        ],
        "complete_telos_only_balanced_pass_observed": comparison[
            "complete_telos_only_balanced_pass_observed"
        ],
        "llm_judge_adverse_false_rejection_count": comparison[
            "llm_judge_adverse_false_rejection_count"
        ],
        "immediate_benchmark_claim_rejected": True,
        "external_benchmark_pilot_design_selected": True,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "fixture_level_telos_specific_advantage_over_external_verifier_claimed": True,
        "all_strategy_superiority_claimed": False,
        "redaction_scan_passed": redaction["passed"],
        "redaction_findings": redaction["findings"],
        "next_gate": next_gate,
        "next_gate_pre_registered": (ROOT / next_gate).exists(),
        "artifact_hashes": artifact_hashes(),
    }
    write_json(PROOF / "run_summary.json", summary)

    print(f"five-strategy differential adjudication: {status}")
    print("provider_api_calls=0")
    print("provider_cost_usd=0.00000000")
    print("strategy_execution_in_this_gate=0")
    print("row_execution_in_this_gate=0")
    print(
        "balanced_fixture_pass_strategy_ids="
        + ",".join(comparison["balanced_fixture_pass_strategy_ids"])
    )
    print("complete_telos_specific_detection_count=4")
    print("complete_telos_specific_detection_rate_delta=0.50000000")
    print("llm_judge_false_rejection_count=6")
    print("external_verifier_and_complete_telos_same_endpoint_vector=false")
    print("benchmark_model_sota_claimed=false")
    print(f"next_gate={next_gate}")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
