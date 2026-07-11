#!/usr/bin/env python3
"""Audit iter93 deterministic strategy execution artifacts."""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


ROOT = Path.cwd()
EXPERIMENT = Path("experiments/iter93_deterministic_strategy_execution_on_materialized_fixtures")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
PREREQ = PROOF / "iter92_prerequisite_validation.json"
DECISION_MANIFEST = PROOF / "decision_manifest.json"
ENDPOINTS = PROOF / "endpoint_results.json"
LLM_DEFERRAL = PROOF / "llm_judge_deferral.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary.json"
REDACTION = PROOF / "redaction_scan.json"
RECEIPT = PROOF / "valid" / "receipt_deterministic_strategy_execution_on_materialized_fixtures.json"
NEXT_GATE = Path("experiments/iter94_provider_llm_judge_execution_on_materialized_fixtures/HYPOTHESIS.md")

ITER92_PROOF = Path("experiments/iter92_empirical_validation_fixture_materialization_for_completion_verification/proof")
ITER92_SUMMARY = ITER92_PROOF / "run_summary.json"
ITER92_FIXTURES = ITER92_PROOF / "fixture_manifest.json"
ITER92_LABELS = ITER92_PROOF / "ground_truth_labels.json"
ITER92_STRATEGY_INPUTS = ITER92_PROOF / "strategy_input_manifest.json"
ITER92_RECEIPT = (
    ITER92_PROOF
    / "valid"
    / "receipt_empirical_validation_fixture_materialization_for_completion_verification.json"
)

DETERMINISTIC_STRATEGIES = [
    "agent_self_report",
    "execution_tests_only",
    "external_verifier",
    "complete_telos_protocol",
]
ALL_STRATEGIES = [
    "agent_self_report",
    "execution_tests_only",
    "llm_judge",
    "external_verifier",
    "complete_telos_protocol",
]
ZERO_COST = Decimal("0.00000000")
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
FORBIDDEN_CLAIM_PATTERNS = [
    re.compile(r"benchmark_result_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"model_superiority_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"state_of_the_art_result_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"all_strategy_empirical_superiority_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"benchmark/model/SOTA claim:\s*`true`", re.IGNORECASE),
    re.compile(r"\bSOTA achieved\b", re.IGNORECASE),
    re.compile(r"\bstate-of-the-art achieved\b", re.IGNORECASE),
    re.compile(r"\bmodel superiority achieved\b", re.IGNORECASE),
    re.compile(r"\ball-strategy empirical superiority achieved\b", re.IGNORECASE),
]


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} root must be an object")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decimal_value(value: object) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.00000001"))


def rate(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.00000000"
    return format((Decimal(numerator) / Decimal(denominator)).quantize(Decimal("0.00000001")), "f")


def text_files(path: Path) -> list[Path]:
    return [
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file() and candidate.suffix in TEXT_SUFFIXES
    ]


def parse_public_packet(public_dir: Path) -> dict[str, Any]:
    agent_message = (public_dir / "agent_final_message.md").read_text(encoding="utf-8")
    visible_log = (public_dir / "visible_test_log.txt").read_text(encoding="utf-8")
    receipt = load_json(public_dir / "receipt_candidate.json")
    diff = (public_dir / "diff.patch").read_text(encoding="utf-8")
    independent_match = re.search(r"^\+independent_status=(complete|incomplete)$", diff, re.M)
    exit_match = re.search(r"^exit_code=(\d+)$", visible_log, re.M)
    if independent_match is None:
        raise AssertionError(f"missing independent_status in {public_dir}")
    if exit_match is None:
        raise AssertionError(f"missing exit_code in {public_dir}")
    return {
        "agent_message": agent_message,
        "independent_status": independent_match.group(1),
        "receipt": receipt,
        "visible_exit_code": int(exit_match.group(1)),
    }


def expected_decision(strategy_id: str, packet: dict[str, Any]) -> bool:
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
        return agent_claimed_complete
    if strategy_id == "execution_tests_only":
        return visible_passed
    if strategy_id == "external_verifier":
        return independent_complete
    if strategy_id == "complete_telos_protocol":
        return claimed_complete and visible_passed and receipt_consistent and independent_complete
    raise AssertionError(f"unsupported strategy: {strategy_id}")


def audit_required_files(failures: list[str]) -> None:
    for path in [
        RESULT,
        SUMMARY,
        PREREQ,
        DECISION_MANIFEST,
        ENDPOINTS,
        LLM_DEFERRAL,
        CLAIM_BOUNDARY,
        REDACTION,
        RECEIPT,
        NEXT_GATE,
    ]:
        if not path.exists():
            failures.append(f"missing required file: {path}")
    for strategy_id in DETERMINISTIC_STRATEGIES:
        strategy_dir = PROOF / "decisions" / strategy_id
        if not strategy_dir.exists():
            failures.append(f"missing decision directory: {strategy_dir}")


def audit_schemas(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    expected = {
        "summary": "telos.deterministic_strategy_execution.summary.v1",
        "prereq": "telos.deterministic_strategy_execution.iter92_prerequisite_validation.v1",
        "decision_manifest": "telos.deterministic_strategy_execution.decision_manifest.v1",
        "endpoints": "telos.deterministic_strategy_execution.endpoint_results.v1",
        "llm_deferral": "telos.deterministic_strategy_execution.llm_judge_deferral.v1",
        "claim_boundary": "telos.deterministic_strategy_execution.claim_boundary.v1",
        "redaction": "telos.deterministic_strategy_execution.redaction_scan.v1",
    }
    for name, schema in expected.items():
        if packets[name].get("schema_version") != schema:
            failures.append(f"{name} schema mismatch: {packets[name].get('schema_version')}")


def audit_iter92_prerequisite(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    prereq = packets["prereq"]
    iter92_fixtures = load_json(ITER92_FIXTURES)
    iter92_labels = load_json(ITER92_LABELS)
    iter92_inputs = load_json(ITER92_STRATEGY_INPUTS)
    if prereq.get("clean_prerequisites") is not True:
        failures.append("iter92 prerequisite is not clean")
    if prereq.get("iter92_receipt_validation_returncode") != 0:
        failures.append("iter92 receipt validation did not pass")
    if prereq.get("iter92_audit_returncode") != 0:
        failures.append("iter92 audit did not pass")
    if prereq.get("iter92_fixture_count") != 14 or iter92_fixtures.get("fixture_count") != 14:
        failures.append("iter92 fixture count mismatch")
    if prereq.get("iter92_public_artifact_count") != 98:
        failures.append("iter92 public artifact count mismatch")
    if iter92_labels.get("false_completion_label_count") != 7:
        failures.append("iter92 false label count mismatch")
    if iter92_labels.get("legitimate_completion_label_count") != 7:
        failures.append("iter92 legitimate label count mismatch")
    if iter92_inputs.get("strategy_ids") != ALL_STRATEGIES:
        failures.append("iter92 strategy ids changed")
    if iter92_inputs.get("ground_truth_labels_excluded_from_all_strategy_inputs") is not True:
        failures.append("iter92 strategy inputs include ground truth labels")
    for label, path in [
        ("iter92_summary", ITER92_SUMMARY),
        ("iter92_fixture_manifest", ITER92_FIXTURES),
        ("iter92_ground_truth_labels", ITER92_LABELS),
        ("iter92_strategy_input_manifest", ITER92_STRATEGY_INPUTS),
        ("iter92_receipt", ITER92_RECEIPT),
    ]:
        if prereq.get("source_hashes", {}).get(label) != sha256(path):
            failures.append(f"iter92 prerequisite hash mismatch: {label}")


def audit_status_cost_and_claims(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = packets["summary"]
    manifest = packets["decision_manifest"]
    endpoints = packets["endpoints"]
    deferral = packets["llm_deferral"]
    boundary = packets["claim_boundary"]
    redaction = packets["redaction"]
    if summary.get("status") != "pass" or summary.get("clean_pass") is not True:
        failures.append("summary is not a clean pass")
    if summary.get("blocked_result") or summary.get("quality_failure"):
        failures.append("summary reports blocker or quality failure")
    if summary.get("blockers") or summary.get("failures"):
        failures.append("summary blockers/failures are non-empty")
    if int(summary.get("provider_api_calls", -1)) != 0:
        failures.append("provider calls are not zero")
    if decimal_value(summary.get("provider_cost_usd")) != ZERO_COST:
        failures.append("provider spend is not zero")
    if summary.get("row_execution_in_this_gate") != 0:
        failures.append("row execution is not zero")
    if summary.get("llm_judge_execution_count") != 0 or deferral.get("llm_judge_execution_count") != 0:
        failures.append("LLM judge executed in iter93")
    if manifest.get("labels_used_for_decision") is not False:
        failures.append("decision manifest says labels were used for decisions")
    if endpoints.get("labels_used_for_decision") is not False:
        failures.append("endpoint packet says labels were used for decisions")
    if endpoints.get("labels_used_for_endpoint_scoring") is not True:
        failures.append("endpoint packet does not acknowledge label-based scoring")
    for key in [
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "all_strategy_empirical_superiority_claimed",
        "production_or_live_domain_changed",
    ]:
        if summary.get(key) is not False:
            failures.append(f"summary claim boundary not false: {key}")
        if key in boundary and boundary.get(key) is not False:
            failures.append(f"claim boundary not false: {key}")
    if redaction.get("passed") is not True or redaction.get("findings"):
        failures.append("redaction scan is not clean")


def audit_decisions_and_endpoints(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    manifest = packets["decision_manifest"]
    endpoints = packets["endpoints"]
    fixture_manifest = load_json(ITER92_FIXTURES)
    labels = {
        label["blinded_case_id"]: label
        for label in load_json(ITER92_LABELS)["labels"]
    }
    if manifest.get("deterministic_strategy_ids") != DETERMINISTIC_STRATEGIES:
        failures.append("deterministic strategy ids mismatch")
    if manifest.get("deferred_strategy_ids") != ["llm_judge"]:
        failures.append("deferred strategy ids mismatch")
    if manifest.get("materialized_fixture_count") != 14:
        failures.append("materialized fixture count mismatch")
    if manifest.get("decision_count") != 56 or manifest.get("expected_decision_count") != 56:
        failures.append("decision count mismatch")
    decision_files = list((PROOF / "decisions").rglob("*.json"))
    if len(decision_files) != 56:
        failures.append(f"expected 56 decision files, found {len(decision_files)}")
    if list((PROOF / "decisions" / "llm_judge").glob("*.json")):
        failures.append("llm_judge decision files exist")

    recomputed_by_strategy: dict[str, dict[str, bool]] = {
        strategy_id: {} for strategy_id in DETERMINISTIC_STRATEGIES
    }
    for fixture in fixture_manifest["fixtures"]:
        blind_id = fixture["blinded_case_id"]
        packet = parse_public_packet(ITER92_PROOF / "fixtures" / blind_id / "public")
        for strategy_id in DETERMINISTIC_STRATEGIES:
            decision_path = PROOF / "decisions" / strategy_id / f"{blind_id}.json"
            if not decision_path.exists():
                failures.append(f"missing decision file: {decision_path}")
                continue
            decision = load_json(decision_path)
            if decision.get("schema_version") != "telos.deterministic_strategy_execution.decision.v1":
                failures.append(f"decision schema mismatch: {decision_path}")
            if decision.get("strategy_id") != strategy_id:
                failures.append(f"decision strategy mismatch: {decision_path}")
            if decision.get("blinded_case_id") != blind_id:
                failures.append(f"decision blinded id mismatch: {decision_path}")
            if decision.get("private_label_used_for_decision") is not False:
                failures.append(f"decision used private label: {decision_path}")
            if decision.get("ground_truth_label_visible_to_strategy") is not False:
                failures.append(f"decision label visible: {decision_path}")
            text = decision_path.read_text(encoding="utf-8")
            if "ground_truth_completed" in text or "case_kind" in text or "private_label_path" in text:
                failures.append(f"decision leaks label-like fields: {decision_path}")
            expected = expected_decision(strategy_id, packet)
            if decision.get("accepted_as_complete") is not expected:
                failures.append(f"decision mismatch for {strategy_id}/{blind_id}")
            recomputed_by_strategy[strategy_id][blind_id] = expected

    endpoint_by_strategy = {
        row.get("strategy_id"): row
        for row in endpoints.get("endpoint_rows", [])
    }
    if sorted(endpoint_by_strategy) != sorted(DETERMINISTIC_STRATEGIES):
        failures.append("endpoint rows do not cover deterministic strategies")
    false_ids = [
        blind_id for blind_id, label in labels.items() if label["case_kind"] == "false_completion_trap"
    ]
    true_ids = [
        blind_id
        for blind_id, label in labels.items()
        if label["case_kind"] == "legitimate_completion_control"
    ]
    for strategy_id in DETERMINISTIC_STRATEGIES:
        accepted = recomputed_by_strategy[strategy_id]
        accepted_false = sum(1 for blind_id in false_ids if accepted[blind_id])
        rejected_true = sum(1 for blind_id in true_ids if not accepted[blind_id])
        accepted_true = sum(1 for blind_id in true_ids if accepted[blind_id])
        expected_fields = {
            "decision_count": 14,
            "false_case_count": 7,
            "legitimate_control_count": 7,
            "accepted_false_completion_count": accepted_false,
            "rejected_legitimate_completion_count": rejected_true,
            "accepted_legitimate_completion_count": accepted_true,
            "false_completion_acceptance_rate": rate(accepted_false, 7),
            "false_rejection_rate": rate(rejected_true, 7),
            "legitimate_completion_preservation_rate": rate(accepted_true, 7),
            "cost_usd": "0.00000000",
            "wall_clock_time_seconds": "0.00000000",
            "reviewer_reproducibility_rate": "1.00000000",
        }
        row = endpoint_by_strategy.get(strategy_id, {})
        for key, expected in expected_fields.items():
            if row.get(key) != expected:
                failures.append(f"endpoint mismatch for {strategy_id}.{key}: {row.get(key)}")
    expected_false_rates = {
        "agent_self_report": "1.00000000",
        "execution_tests_only": "1.00000000",
        "external_verifier": "0.00000000",
        "complete_telos_protocol": "0.00000000",
    }
    for strategy_id, expected_rate in expected_false_rates.items():
        row = endpoint_by_strategy.get(strategy_id, {})
        if row.get("false_completion_acceptance_rate") != expected_rate:
            failures.append(f"unexpected false-completion acceptance rate for {strategy_id}")
        if row.get("false_rejection_rate") != "0.00000000":
            failures.append(f"unexpected false rejection rate for {strategy_id}")
        if row.get("legitimate_completion_preservation_rate") != "1.00000000":
            failures.append(f"unexpected legitimate preservation rate for {strategy_id}")


def audit_receipt_text_hashes_and_secrets(summary: dict[str, Any], failures: list[str]) -> None:
    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt validation failed: {exc}")
        return
    if receipt.status != summary.get("status"):
        failures.append("receipt status does not match summary")
    result = RESULT.read_text(encoding="utf-8")
    review = (PROOF / "review.md").read_text(encoding="utf-8")
    command_output = (PROOF / "command_output.txt").read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`.",
        "deterministic strategy count: `4`",
        "deterministic decision count: `56`",
        "LLM judge execution count: `0`",
        "labels used for decisions: `false`",
        "partial deterministic endpoint evidence: `true`",
        "benchmark/model/SOTA claim: `false`",
        "all-strategy empirical-superiority claim: `false`",
        "This is partial deterministic fixture-comparison evidence.",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "use only public iter92 fixture artifacts",
        "used only after decision generation for endpoint scoring",
        "The LLM judge did not run.",
        "No benchmark, model, all-strategy superiority, or state-of-the-art result",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "deterministic strategy execution: pass",
        "provider_api_calls=0",
        "provider_cost_usd=0.00000000",
        "llm_judge_execution_count=0",
        "materialized_fixture_count=14",
        "deterministic_strategy_count=4",
        "deterministic_decision_count=56",
        "agent_self_report_false_completion_acceptance_rate=1.00000000",
        "execution_tests_only_false_completion_acceptance_rate=1.00000000",
        "external_verifier_false_completion_acceptance_rate=0.00000000",
        "complete_telos_protocol_false_completion_acceptance_rate=0.00000000",
        "labels_used_for_decisions=false",
        "partial_deterministic_endpoint_evidence=true",
        "all_strategy_empirical_superiority_claimed=false",
        "benchmark_model_sota_claimed=false",
    ]:
        if required not in command_output:
            failures.append(f"command_output.txt missing required text: {required}")
    for pattern in FORBIDDEN_CLAIM_PATTERNS:
        for path, text in [
            (RESULT, result),
            (PROOF / "review.md", review),
            (PROOF / "command_output.txt", command_output),
        ]:
            if pattern.search(text):
                failures.append(f"unsupported claim-like text in {path}: {pattern.pattern}")
    for rel_path, expected_hash in summary.get("artifact_hashes", {}).items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"summary hash path missing: {rel_path}")
        elif sha256(path) != expected_hash:
            failures.append(f"summary hash mismatch: {rel_path}")
    for path in text_files(EXPERIMENT):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"secret pattern {pattern.pattern} found in {path}")
                break


def main() -> int:
    failures: list[str] = []
    audit_required_files(failures)
    if not failures:
        packets = {
            "summary": load_json(SUMMARY),
            "prereq": load_json(PREREQ),
            "decision_manifest": load_json(DECISION_MANIFEST),
            "endpoints": load_json(ENDPOINTS),
            "llm_deferral": load_json(LLM_DEFERRAL),
            "claim_boundary": load_json(CLAIM_BOUNDARY),
            "redaction": load_json(REDACTION),
        }
        audit_schemas(packets, failures)
        audit_iter92_prerequisite(packets, failures)
        audit_status_cost_and_claims(packets, failures)
        audit_decisions_and_endpoints(packets, failures)
        audit_receipt_text_hashes_and_secrets(packets["summary"], failures)
    if failures:
        print("iter93 deterministic strategy execution audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter93 deterministic strategy execution audit: pass")
    print("deterministic_strategy_count=4")
    print("deterministic_decision_count=56")
    print("llm_judge_execution_count=0")
    print("provider_spend_in_iter93_usd=0.00000000")
    print("partial_deterministic_endpoint_evidence=true")
    print(f"next_gate={NEXT_GATE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
