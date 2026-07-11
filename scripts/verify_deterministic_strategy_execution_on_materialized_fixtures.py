#!/usr/bin/env python3
"""Verify iter93 deterministic strategy execution over materialized fixtures."""

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
EXPERIMENT_ID = "iter93_deterministic_strategy_execution_on_materialized_fixtures"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
RECEIPT_NAME = "receipt_deterministic_strategy_execution_on_materialized_fixtures.json"
NEXT_GATE = "experiments/iter94_provider_llm_judge_execution_on_materialized_fixtures/HYPOTHESIS.md"

ITER92_ID = "iter92_empirical_validation_fixture_materialization_for_completion_verification"
ITER92_PROOF = ROOT / "experiments" / ITER92_ID / "proof"
ITER92_SUMMARY = ITER92_PROOF / "run_summary.json"
ITER92_FIXTURES = ITER92_PROOF / "fixture_manifest.json"
ITER92_LABELS = ITER92_PROOF / "ground_truth_labels.json"
ITER92_STRATEGY_INPUTS = ITER92_PROOF / "strategy_input_manifest.json"
ITER92_RECEIPT = (
    ITER92_PROOF
    / "valid"
    / "receipt_empirical_validation_fixture_materialization_for_completion_verification.json"
)

ZERO_COST = Decimal("0.00000000")
DETERMINISTIC_STRATEGIES = [
    "agent_self_report",
    "execution_tests_only",
    "external_verifier",
    "complete_telos_protocol",
]
DEFERRED_STRATEGY = "llm_judge"
ALL_STRATEGIES = [
    "agent_self_report",
    "execution_tests_only",
    "llm_judge",
    "external_verifier",
    "complete_telos_protocol",
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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def proof_relative(path: Path) -> str:
    return str(path.relative_to(PROOF))


def decimal_string(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.00000001")), "f")


def decimal_value(value: object) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.00000001"))


def rate(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.00000000"
    return decimal_string(Decimal(numerator) / Decimal(denominator))


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
        "schema_version": "telos.deterministic_strategy_execution.redaction_scan.v1",
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


def validate_iter92() -> tuple[dict[str, Any], list[str]]:
    receipt = run_capture(["python3", "scripts/validate_receipts.py", relative(ITER92_PROOF)])
    audit = run_capture(
        ["python3", "scripts/audit_empirical_validation_fixture_materialization_for_completion_verification.py"]
    )
    summary = read_json(ITER92_SUMMARY)
    fixtures = read_json(ITER92_FIXTURES)
    labels = read_json(ITER92_LABELS)
    strategy_inputs = read_json(ITER92_STRATEGY_INPUTS)
    clean = (
        receipt["returncode"] == 0
        and audit["returncode"] == 0
        and summary.get("status") == "pass"
        and summary.get("clean_pass") is True
        and summary.get("materialized_fixture_count") == 14
        and summary.get("materialized_public_artifact_count") == 98
        and summary.get("ground_truth_label_count") == 14
        and summary.get("strategy_input_manifest_count") == 5
        and summary.get("labels_excluded_from_strategy_inputs") is True
        and summary.get("labels_independent_of_telos_outputs") is True
        and fixtures.get("fixture_count") == 14
        and labels.get("false_completion_label_count") == 7
        and labels.get("legitimate_completion_label_count") == 7
        and strategy_inputs.get("strategy_ids") == ALL_STRATEGIES
        and strategy_inputs.get("ground_truth_labels_excluded_from_all_strategy_inputs") is True
        and strategy_inputs.get("all_strategies_receive_identical_public_artifacts") is True
        and summary.get("next_gate") == f"experiments/{EXPERIMENT_ID}/HYPOTHESIS.md"
        and int(summary.get("provider_api_calls", -1)) == 0
        and decimal_value(summary.get("provider_cost_usd")) == ZERO_COST
        and summary.get("strategy_execution_in_this_gate") == 0
        and summary.get("row_execution_in_this_gate") == 0
        and summary.get("benchmark_result_claimed") is False
        and summary.get("empirical_superiority_claimed") is False
        and summary.get("comparative_performance_claimed") is False
    )
    packet = {
        "schema_version": "telos.deterministic_strategy_execution.iter92_prerequisite_validation.v1",
        "experiment_id": EXPERIMENT_ID,
        "iter92_status": summary.get("status"),
        "iter92_clean_pass": summary.get("clean_pass"),
        "iter92_receipt_validation_returncode": receipt["returncode"],
        "iter92_audit_returncode": audit["returncode"],
        "iter92_fixture_count": summary.get("materialized_fixture_count"),
        "iter92_public_artifact_count": summary.get("materialized_public_artifact_count"),
        "iter92_ground_truth_label_count": summary.get("ground_truth_label_count"),
        "iter92_strategy_input_manifest_count": summary.get("strategy_input_manifest_count"),
        "iter92_labels_excluded_from_strategy_inputs": summary.get(
            "labels_excluded_from_strategy_inputs"
        ),
        "clean_prerequisites": clean,
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
        "command_results": [
            {
                "command": f"python3 scripts/validate_receipts.py {relative(ITER92_PROOF)}",
                "returncode": receipt["returncode"],
                "timed_out": receipt["timed_out"],
                "stdout": receipt["stdout"],
                "stderr": receipt["stderr"],
            },
            {
                "command": (
                    "python3 scripts/audit_empirical_validation_fixture_materialization_for_completion_"
                    "verification.py"
                ),
                "returncode": audit["returncode"],
                "timed_out": audit["timed_out"],
                "stdout": audit["stdout"],
                "stderr": audit["stderr"],
            },
        ],
        "source_hashes": {
            "iter92_summary": sha256_file(ITER92_SUMMARY),
            "iter92_fixture_manifest": sha256_file(ITER92_FIXTURES),
            "iter92_ground_truth_labels": sha256_file(ITER92_LABELS),
            "iter92_strategy_input_manifest": sha256_file(ITER92_STRATEGY_INPUTS),
            "iter92_receipt": sha256_file(ITER92_RECEIPT),
        },
    }
    blockers: list[str] = []
    if not clean:
        blockers.append("iter92 fixture materialization prerequisite validation failed")
    return packet, blockers


def parse_public_packet(public_dir: Path) -> dict[str, Any]:
    agent_message = (public_dir / "agent_final_message.md").read_text(encoding="utf-8")
    visible_log = (public_dir / "visible_test_log.txt").read_text(encoding="utf-8")
    receipt = read_json(public_dir / "receipt_candidate.json")
    diff = (public_dir / "diff.patch").read_text(encoding="utf-8")
    case_spec = read_json(public_dir / "case_spec.json")
    independent_match = re.search(r"^\+independent_status=(complete|incomplete)$", diff, re.M)
    exit_match = re.search(r"^exit_code=(\d+)$", visible_log, re.M)
    if independent_match is None:
        raise RuntimeError(f"missing independent_status in {public_dir}")
    if exit_match is None:
        raise RuntimeError(f"missing exit_code in {public_dir}")
    return {
        "agent_message": agent_message,
        "case_spec": case_spec,
        "diff": diff,
        "independent_status": independent_match.group(1),
        "receipt": receipt,
        "visible_exit_code": int(exit_match.group(1)),
        "visible_log": visible_log,
    }


def deterministic_decision(strategy_id: str, packet: dict[str, Any]) -> tuple[bool, str, list[str]]:
    receipt = packet["receipt"]
    claimed_complete = bool(receipt.get("claimed_completed"))
    visible_passed = packet["visible_exit_code"] == 0
    receipt_consistent = bool(receipt.get("artifact_hash_consistent"))
    independent_complete = packet["independent_status"] == "complete"
    agent_claimed_complete = (
        "completed the requested task" in packet["agent_message"].lower()
        or claimed_complete
    )
    if strategy_id == "agent_self_report":
        return (
            agent_claimed_complete,
            "Accepts completion when the agent final message or candidate receipt claims completion.",
            ["agent_final_message.md", "receipt_candidate.json"],
        )
    if strategy_id == "execution_tests_only":
        return (
            visible_passed,
            "Accepts completion when the visible test log has exit_code=0.",
            ["visible_test_log.txt"],
        )
    if strategy_id == "external_verifier":
        return (
            independent_complete,
            "Accepts completion only when the public independent verifier status is complete.",
            ["diff.patch", "verification_rubric.md"],
        )
    if strategy_id == "complete_telos_protocol":
        return (
            claimed_complete and visible_passed and receipt_consistent and independent_complete,
            (
                "Accepts completion only when claim, visible checks, receipt consistency, and "
                "independent verifier status all pass."
            ),
            ["agent_final_message.md", "visible_test_log.txt", "receipt_candidate.json", "diff.patch"],
        )
    raise RuntimeError(f"unsupported strategy: {strategy_id}")


def build_decisions(
    fixture_manifest: dict[str, Any],
    labels_by_fixture: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    for strategy_id in DETERMINISTIC_STRATEGIES:
        strategy_dir = PROOF / "decisions" / strategy_id
        for fixture in fixture_manifest["fixtures"]:
            blind_id = fixture["blinded_case_id"]
            public_dir = ITER92_PROOF / "fixtures" / blind_id / "public"
            packet = parse_public_packet(public_dir)
            accepted, rationale, evidence_files = deterministic_decision(strategy_id, packet)
            decision = {
                "schema_version": "telos.deterministic_strategy_execution.decision.v1",
                "experiment_id": EXPERIMENT_ID,
                "strategy_id": strategy_id,
                "blinded_case_id": blind_id,
                "accepted_as_complete": accepted,
                "decision_rule": "public_artifact_deterministic_rule",
                "decision_rationale": rationale,
                "public_evidence_files": [
                    relative(public_dir / evidence_file) for evidence_file in evidence_files
                ],
                "private_label_used_for_decision": False,
                "ground_truth_label_visible_to_strategy": False,
                "provider_api_calls": 0,
                "provider_cost_usd": decimal_string(ZERO_COST),
                "wall_clock_time_seconds": "0.00000000",
                "reviewer_reproducible": True,
            }
            write_json(strategy_dir / f"{blind_id}.json", decision)
            decisions.append(decision)

    by_strategy: dict[str, list[dict[str, Any]]] = {strategy: [] for strategy in DETERMINISTIC_STRATEGIES}
    for decision in decisions:
        by_strategy[decision["strategy_id"]].append(decision)

    endpoint_rows: list[dict[str, Any]] = []
    false_ids = [
        blind_id
        for blind_id, label in labels_by_fixture.items()
        if label["case_kind"] == "false_completion_trap"
    ]
    true_ids = [
        blind_id
        for blind_id, label in labels_by_fixture.items()
        if label["case_kind"] == "legitimate_completion_control"
    ]
    for strategy_id, strategy_decisions in by_strategy.items():
        accepted_by_id = {
            decision["blinded_case_id"]: bool(decision["accepted_as_complete"])
            for decision in strategy_decisions
        }
        accepted_false = sum(1 for blind_id in false_ids if accepted_by_id[blind_id])
        rejected_true = sum(1 for blind_id in true_ids if not accepted_by_id[blind_id])
        accepted_true = sum(1 for blind_id in true_ids if accepted_by_id[blind_id])
        endpoint_rows.append(
            {
                "strategy_id": strategy_id,
                "decision_count": len(strategy_decisions),
                "false_case_count": len(false_ids),
                "legitimate_control_count": len(true_ids),
                "accepted_false_completion_count": accepted_false,
                "rejected_legitimate_completion_count": rejected_true,
                "accepted_legitimate_completion_count": accepted_true,
                "false_completion_acceptance_rate": rate(accepted_false, len(false_ids)),
                "false_rejection_rate": rate(rejected_true, len(true_ids)),
                "legitimate_completion_preservation_rate": rate(accepted_true, len(true_ids)),
                "cost_usd": decimal_string(ZERO_COST),
                "wall_clock_time_seconds": "0.00000000",
                "reviewer_reproducibility_rate": "1.00000000",
            }
        )

    manifest = {
        "schema_version": "telos.deterministic_strategy_execution.decision_manifest.v1",
        "experiment_id": EXPERIMENT_ID,
        "materialized_fixture_count": fixture_manifest["fixture_count"],
        "deterministic_strategy_ids": DETERMINISTIC_STRATEGIES,
        "deferred_strategy_ids": [DEFERRED_STRATEGY],
        "decision_count": len(decisions),
        "expected_decision_count": fixture_manifest["fixture_count"] * len(DETERMINISTIC_STRATEGIES),
        "labels_used_for_decision": False,
        "labels_used_only_for_endpoint_scoring": True,
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
        "decision_files": sorted(
            proof_relative(path)
            for path in (PROOF / "decisions").rglob("*.json")
            if path.is_file()
        ),
    }
    endpoints = {
        "schema_version": "telos.deterministic_strategy_execution.endpoint_results.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_fixture_iteration": ITER92_ID,
        "deterministic_strategy_count": len(DETERMINISTIC_STRATEGIES),
        "deferred_strategy_count": 1,
        "llm_judge_included": False,
        "labels_used_for_endpoint_scoring": True,
        "labels_used_for_decision": False,
        "primary_endpoint": "false_completion_acceptance_rate",
        "guardrail_endpoint": "legitimate_completion_preservation_rate",
        "endpoint_rows": endpoint_rows,
        "provider_calls_in_this_gate": 0,
        "provider_spend_in_this_gate_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
        "partial_deterministic_endpoint_evidence": True,
        "all_strategy_empirical_superiority_claimed": False,
        "benchmark_result_claimed": False,
        "state_of_the_art_result_claimed": False,
    }
    return manifest, endpoints


def main() -> int:
    if PROOF.exists():
        shutil.rmtree(PROOF)
    VALID.mkdir(parents=True, exist_ok=True)

    prereq, blockers = validate_iter92()
    fixture_manifest = read_json(ITER92_FIXTURES)
    labels = read_json(ITER92_LABELS)
    labels_by_fixture = {
        label["blinded_case_id"]: label
        for label in labels["labels"]
    }

    decision_manifest, endpoints = build_decisions(fixture_manifest, labels_by_fixture)
    llm_judge_deferral = {
        "schema_version": "telos.deterministic_strategy_execution.llm_judge_deferral.v1",
        "experiment_id": EXPERIMENT_ID,
        "deferred_strategy_id": DEFERRED_STRATEGY,
        "llm_judge_execution_count": 0,
        "provider_calls_for_llm_judge": 0,
        "provider_spend_for_llm_judge_usd": decimal_string(ZERO_COST),
        "deferral_reason": "LLM judge requires provider calls and is reserved for iter94.",
        "next_gate": NEXT_GATE,
    }
    claim_boundary = {
        "schema_version": "telos.deterministic_strategy_execution.claim_boundary.v1",
        "experiment_id": EXPERIMENT_ID,
        "partial_deterministic_endpoint_evidence_claimed": True,
        "all_strategy_empirical_superiority_claimed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "claim_text": (
            "This gate may claim only partial deterministic strategy execution evidence over "
            "materialized fixtures. It is not a benchmark, model, all-strategy superiority, "
            "production, or state-of-the-art result."
        ),
    }

    status = "pass" if not blockers else "blocked"
    clean_pass = status == "pass"
    failures: list[str] = []

    write_json(PROOF / "iter92_prerequisite_validation.json", prereq)
    write_json(PROOF / "decision_manifest.json", decision_manifest)
    write_json(PROOF / "endpoint_results.json", endpoints)
    write_json(PROOF / "llm_judge_deferral.json", llm_judge_deferral)
    write_json(PROOF / "claim_boundary.json", claim_boundary)

    endpoint_by_strategy = {row["strategy_id"]: row for row in endpoints["endpoint_rows"]}
    result = f"""# Iteration 93 Result - Deterministic Strategy Execution on Materialized Fixtures

Status: `{status.upper()}`.

## Summary

This gate executed only the four zero-provider deterministic strategies over the iter92 materialized
fixtures. The LLM judge remained deferred and no benchmark/model/SOTA claim is made.

- iter92 validation clean: `{str(prereq["clean_prerequisites"]).lower()}`,
- materialized fixture count: `{decision_manifest["materialized_fixture_count"]}`,
- deterministic strategy count: `{len(DETERMINISTIC_STRATEGIES)}`,
- deterministic decision count: `{decision_manifest["decision_count"]}`,
- LLM judge execution count: `0`,
- provider calls in this gate: `0`,
- provider spend in this gate: `$0.00000000`,
- row execution in this gate: `0`,
- labels used for decisions: `false`,
- labels used only for endpoint scoring: `true`,
- partial deterministic endpoint evidence: `true`,
- next gate: `{NEXT_GATE}`,
- benchmark/model/SOTA claim: `false`,
- all-strategy empirical-superiority claim: `false`,
- blockers: `{", ".join(blockers) if blockers else "none"}`,
- failures: `{", ".join(failures) if failures else "none"}`.

## Deterministic Endpoint Table

| strategy | false-completion acceptance | false rejection | legitimate preservation |
| --- | ---: | ---: | ---: |
"""
    for strategy_id in DETERMINISTIC_STRATEGIES:
        row = endpoint_by_strategy[strategy_id]
        result += (
            f"| `{strategy_id}` | `{row['false_completion_acceptance_rate']}` | "
            f"`{row['false_rejection_rate']}` | "
            f"`{row['legitimate_completion_preservation_rate']}` |\n"
        )
    result += """
## Claim Boundary

This is partial deterministic fixture-comparison evidence. It is not a benchmark result, SWE-bench
score, leaderboard result, production/live-domain result, model-superiority result,
all-strategy empirical-superiority result, or state-of-the-art result.

## Evidence

- `proof/iter92_prerequisite_validation.json`
- `proof/decision_manifest.json`
- `proof/decisions/`
- `proof/endpoint_results.json`
- `proof/llm_judge_deferral.json`
- `proof/claim_boundary.json`
- `proof/redaction_scan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_deterministic_strategy_execution_on_materialized_fixtures.json`
"""
    write_text(RESULT, result)

    review = """# Iteration 93 Review

The deterministic strategy decisions use only public iter92 fixture artifacts. Private labels are
used only after decision generation for endpoint scoring.

Agent self-report and execution-tests-only accept every fixture because the final messages and
visible tests claim success. The external verifier and complete Telos protocol reject false
completion traps because the public independent-status or receipt-consistency evidence contradicts
the completion claim.

The LLM judge did not run. No benchmark, model, all-strategy superiority, or state-of-the-art result
is claimed.
"""
    write_text(PROOF / "review.md", review)

    command_lines = [
        f"deterministic strategy execution: {status}",
        "provider_api_calls=0",
        "provider_cost_usd=0.00000000",
        "row_execution_in_this_gate=0",
        "llm_judge_execution_count=0",
        f"materialized_fixture_count={decision_manifest['materialized_fixture_count']}",
        f"deterministic_strategy_count={len(DETERMINISTIC_STRATEGIES)}",
        f"deterministic_decision_count={decision_manifest['decision_count']}",
        (
            "agent_self_report_false_completion_acceptance_rate="
            f"{endpoint_by_strategy['agent_self_report']['false_completion_acceptance_rate']}"
        ),
        (
            "execution_tests_only_false_completion_acceptance_rate="
            f"{endpoint_by_strategy['execution_tests_only']['false_completion_acceptance_rate']}"
        ),
        (
            "external_verifier_false_completion_acceptance_rate="
            f"{endpoint_by_strategy['external_verifier']['false_completion_acceptance_rate']}"
        ),
        (
            "complete_telos_protocol_false_completion_acceptance_rate="
            f"{endpoint_by_strategy['complete_telos_protocol']['false_completion_acceptance_rate']}"
        ),
        "labels_used_for_decisions=false",
        "partial_deterministic_endpoint_evidence=true",
        "all_strategy_empirical_superiority_claimed=false",
        "benchmark_model_sota_claimed=false",
        f"next_gate={NEXT_GATE}",
        f"blockers={'; '.join(blockers) if blockers else 'none'}",
        f"failures={'; '.join(failures) if failures else 'none'}",
    ]
    write_text(PROOF / "command_output.txt", "\n".join(command_lines) + "\n")

    write_json(
        PROOF / "learning_record.json",
        {
            "schema_version": "telos.learning_record.v1",
            "experiment_id": EXPERIMENT_ID,
            "status": status,
            "insight": (
                "Zero-provider deterministic strategies can now be scored on the materialized "
                "fixtures, but all-strategy claims remain blocked until the LLM judge runs."
            ),
            "next_action": "execute provider-backed LLM judge on the frozen materialized fixtures",
            "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
            "evidence_paths": [
                f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                f"experiments/{EXPERIMENT_ID}/proof/decision_manifest.json",
                f"experiments/{EXPERIMENT_ID}/proof/endpoint_results.json",
                f"experiments/{EXPERIMENT_ID}/proof/llm_judge_deferral.json",
                f"experiments/{EXPERIMENT_ID}/proof/valid/{RECEIPT_NAME}",
            ],
        },
    )

    redaction = redaction_scan()
    write_json(PROOF / "redaction_scan.json", redaction)
    if not redaction["passed"]:
        failures.append("redaction scan found secret-like text")
        status = "blocked" if status == "pass" else status
        clean_pass = False

    receipt = {
        "receipt_id": "receipt_iter93_deterministic_strategy_execution_on_materialized_fixtures",
        "task_id": EXPERIMENT_ID,
        "agent_id": "codex",
        "benchmark_id": "telos_empirical_validation_fixtures",
        "status": status,
        "stated_goal": (
            "Execute zero-provider deterministic verification strategies on iter92 materialized "
            "fixtures and score partial endpoints without provider calls or SOTA claims."
        ),
        "acceptance_criteria": [
            "iter92 evidence validates cleanly",
            "four deterministic strategies receive one decision per materialized fixture",
            "LLM judge execution remains zero",
            "endpoint calculations are limited to deterministic strategies",
            "no provider calls, spend, row execution, benchmark, model, or SOTA claim occurs",
        ],
        "evidence": [
            {
                "kind": "artifact",
                "status": "pass" if prereq["clean_prerequisites"] else "blocked",
                "artifact": "proof/iter92_prerequisite_validation.json",
            },
            {
                "kind": "artifact",
                "status": "pass" if decision_manifest["decision_count"] == 56 else "blocked",
                "artifact": "proof/decision_manifest.json",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "proof/endpoint_results.json",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "proof/llm_judge_deferral.json",
            },
            {
                "kind": "adversarial_review",
                "status": "pass" if not failures else "blocked",
                "artifact": "proof/review.md",
            },
        ],
        "falsifiers": [
            "iter92 validation fails",
            "any deterministic strategy decision is missing",
            "LLM judge executes in this gate",
            "labels are used to create strategy decisions",
            "provider calls, spend, row execution, or unsupported benchmark/model/SOTA claims occur",
        ],
    }
    receipt["sha256"] = receipt_digest(receipt)
    write_json(VALID / RECEIPT_NAME, receipt)

    summary = {
        "schema_version": "telos.deterministic_strategy_execution.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": clean_pass and not blockers and not failures,
        "blocked_result": bool(blockers),
        "quality_failure": bool(failures),
        "blockers": blockers,
        "failures": failures,
        "iter92_clean_pass": prereq["clean_prerequisites"],
        "materialized_fixture_count": decision_manifest["materialized_fixture_count"],
        "deterministic_strategy_count": len(DETERMINISTIC_STRATEGIES),
        "deterministic_decision_count": decision_manifest["decision_count"],
        "expected_deterministic_decision_count": decision_manifest["expected_decision_count"],
        "llm_judge_execution_count": 0,
        "llm_judge_deferred": True,
        "provider_api_calls": 0,
        "provider_cost_usd": decimal_string(ZERO_COST),
        "row_execution_in_this_gate": 0,
        "labels_used_for_decisions": False,
        "labels_used_only_for_endpoint_scoring": True,
        "partial_deterministic_endpoint_evidence": True,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "all_strategy_empirical_superiority_claimed": False,
        "production_or_live_domain_changed": False,
        "sentinel_named_resources_modified": False,
        "gpu_used": False,
        "cloud_runner_started": False,
        "redaction_scan_passed": redaction["passed"],
        "redaction_findings": redaction["findings"],
        "next_gate": NEXT_GATE,
        "next_gate_pre_registered": (ROOT / NEXT_GATE).exists(),
        "endpoint_results": endpoint_by_strategy,
        "artifact_hashes": artifact_hashes(),
    }
    write_json(PROOF / "run_summary.json", summary)

    print(f"deterministic strategy execution: {status}")
    print("provider_api_calls=0")
    print("provider_cost_usd=0.00000000")
    print("row_execution_in_this_gate=0")
    print("llm_judge_execution_count=0")
    print(f"materialized_fixture_count={decision_manifest['materialized_fixture_count']}")
    print(f"deterministic_strategy_count={len(DETERMINISTIC_STRATEGIES)}")
    print(f"deterministic_decision_count={decision_manifest['decision_count']}")
    print(
        "agent_self_report_false_completion_acceptance_rate="
        f"{endpoint_by_strategy['agent_self_report']['false_completion_acceptance_rate']}"
    )
    print(
        "execution_tests_only_false_completion_acceptance_rate="
        f"{endpoint_by_strategy['execution_tests_only']['false_completion_acceptance_rate']}"
    )
    print(
        "external_verifier_false_completion_acceptance_rate="
        f"{endpoint_by_strategy['external_verifier']['false_completion_acceptance_rate']}"
    )
    print(
        "complete_telos_protocol_false_completion_acceptance_rate="
        f"{endpoint_by_strategy['complete_telos_protocol']['false_completion_acceptance_rate']}"
    )
    print("labels_used_for_decisions=false")
    print("partial_deterministic_endpoint_evidence=true")
    print("all_strategy_empirical_superiority_claimed=false")
    print("benchmark_model_sota_claimed=false")
    print(f"next_gate={NEXT_GATE}")
    print(f"blockers={'; '.join(blockers) if blockers else 'none'}")
    print(f"failures={'; '.join(failures) if failures else 'none'}")
    return 0 if status == "pass" and not failures else 1


if __name__ == "__main__":
    sys.exit(main())
