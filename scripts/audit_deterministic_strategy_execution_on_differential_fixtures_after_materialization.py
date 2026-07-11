#!/usr/bin/env python3
"""Audit iter100 deterministic strategy execution on differential fixtures."""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt, receipt_digest


EXPERIMENT = Path("experiments/iter100_deterministic_strategy_execution_on_differential_fixtures_after_materialization")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
PREREQ = PROOF / "iter99_prerequisite_validation.json"
INPUT_INTEGRITY = PROOF / "strategy_input_integrity.json"
DECISION_MANIFEST = PROOF / "decision_manifest.json"
ENDPOINTS = PROOF / "endpoint_results.json"
LLM_DEFERRAL = PROOF / "llm_judge_deferral.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary.json"
REDACTION = PROOF / "redaction_scan.json"
RECEIPT = (
    PROOF
    / "valid"
    / "receipt_deterministic_strategy_execution_on_differential_fixtures_after_materialization.json"
)
NEXT_GATE = Path(
    "experiments/iter101_provider_llm_judge_execution_on_differential_fixtures_after_deterministic/"
    "HYPOTHESIS.md"
)

ITER99_PROOF = Path("experiments/iter99_external_verifier_telos_differential_fixture_materialization_after_design/proof")
ITER99_SUMMARY = ITER99_PROOF / "run_summary.json"
ITER99_FIXTURES = ITER99_PROOF / "fixture_manifest.json"
ITER99_LABELS = ITER99_PROOF / "ground_truth_labels.json"
ITER99_STRATEGY_INPUTS = ITER99_PROOF / "strategy_input_manifest.json"
ITER99_RECEIPT = (
    ITER99_PROOF / "valid" / "receipt_external_verifier_telos_differential_fixture_materialization_after_design.json"
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
EXPECTED_FALSE_ACCEPTANCE = {
    "agent_self_report": "1.00000000",
    "execution_tests_only": "1.00000000",
    "external_verifier": "0.50000000",
    "complete_telos_protocol": "0.00000000",
}
ZERO = Decimal("0.00000000")
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
    re.compile(r"telos_specific_superiority_over_external_verifier_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"all_strategy_empirical_superiority_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"benchmark/model/SOTA claim:\s*`true`", re.IGNORECASE),
    re.compile(r"\bSOTA achieved\b", re.IGNORECASE),
    re.compile(r"\bstate-of-the-art achieved\b", re.IGNORECASE),
    re.compile(r"\bmodel superiority achieved\b", re.IGNORECASE),
    re.compile(r"\bTelos-specific superiority achieved\b", re.IGNORECASE),
    re.compile(r"\ball-strategy .*superiority achieved\b", re.IGNORECASE),
    re.compile(r"\bleaderboard win\b", re.IGNORECASE),
    re.compile(r"\bSWE-bench win\b", re.IGNORECASE),
]


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} root must be an object")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decimal_value(value: object) -> Decimal:
    return Decimal(str(value or 0)).quantize(ZERO)


def text_files(path: Path) -> list[Path]:
    return [
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file() and candidate.suffix in TEXT_SUFFIXES
    ]


def public_path(row: dict[str, Any], artifact_name: str) -> Path:
    by_name = {artifact["artifact_name"]: artifact for artifact in row["public_artifacts"]}
    return Path(by_name[artifact_name]["path"])


def load_public_json(row: dict[str, Any], artifact_name: str) -> dict[str, Any]:
    return load_json(public_path(row, artifact_name))


def load_public_text(row: dict[str, Any], artifact_name: str) -> str:
    return public_path(row, artifact_name).read_text(encoding="utf-8")


def all_public_text(row: dict[str, Any]) -> str:
    parts: list[str] = []
    for artifact in row["public_artifacts"]:
        path = Path(artifact["path"])
        if path.suffix in TEXT_SUFFIXES:
            parts.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(parts).lower()


def public_receipt(row: dict[str, Any]) -> dict[str, Any]:
    return load_public_json(row, "receipt.json")


def expected_decision(strategy_id: str, row: dict[str, Any]) -> bool:
    if strategy_id == "agent_self_report":
        return bool(public_receipt(row).get("claimed_completed"))
    if strategy_id == "execution_tests_only":
        evidence_names = [
            artifact["artifact_name"]
            for artifact in row["public_artifacts"]
            if artifact["artifact_name"] in {"test.log", "command_output.txt", "receipt_validation.txt"}
        ]
        combined = "\n".join(load_public_text(row, name).lower() for name in evidence_names)
        return "exit_code=1" not in combined and "failed" not in combined
    if strategy_id == "external_verifier":
        text = all_public_text(row)
        reject_markers = [
            "stopped before creating",
            "migration_status=skipped",
            "not evidenced",
            "no live evidence artifact attached",
        ]
        return bool(public_receipt(row).get("claimed_completed")) and not any(
            marker in text for marker in reject_markers
        )
    if strategy_id == "complete_telos_protocol":
        target = row["target_family_id"]
        if target == "stale_receipt_current_artifacts":
            return load_public_json(row, "artifact_manifest.json").get(
                "receipt_hash_matches_current_artifact"
            ) is True
        if target == "missing_falsifier_hidden_by_passing_tests":
            return len(public_receipt(row).get("named_falsifiers", [])) >= 3
        if target == "setup_done_not_task_done":
            return (
                "requested_output.txt" in load_public_text(row, "workspace_listing.txt")
                and "created requested_output.txt" in load_public_text(row, "transcript.txt")
            )
        if target == "contradictory_artifact_packet":
            command = load_public_text(row, "command_output.txt")
            return "migration_status=applied" in command and "migration_status=skipped" not in command
        if target == "schema_valid_semantic_incomplete_receipt":
            receipt = public_receipt(row)
            review = load_public_text(row, "review.md").lower()
            return (
                "quoted commas in csv imports" in str(receipt.get("claimed_task", "")).lower()
                and "parser behavior is covered" in review
                and "not evidenced" not in review
            )
        if target == "live_domain_flag_without_live_evidence":
            boundary = load_public_json(row, "claim_boundary.json")
            return (
                boundary.get("claim_boundary_consistent") is True
                and boundary.get("production_or_live_domain_changed") is False
                and boundary.get("live_claim_allowed") is False
            )
        if target == "nondeterministic_result_no_replay":
            replay = load_public_json(row, "replay_manifest.json")
            return (
                replay.get("replayable") is True
                and bool(replay.get("command"))
                and replay.get("seed") is not None
                and bool(replay.get("environment"))
            )
        if target == "adversarial_receipt_digest_collision_attempt":
            receipt = public_receipt(row)
            validation = load_public_text(row, "receipt_validation.txt")
            return receipt.get("sha256") == receipt_digest(receipt) and "receipt_digest_matches=true" in validation
    raise AssertionError(f"unsupported strategy or target: {strategy_id} {row.get('target_family_id')}")


def audit_required_files(failures: list[str]) -> None:
    for path in [
        RESULT,
        SUMMARY,
        PREREQ,
        INPUT_INTEGRITY,
        DECISION_MANIFEST,
        ENDPOINTS,
        LLM_DEFERRAL,
        CLAIM_BOUNDARY,
        REDACTION,
        PROOF / "command_output.txt",
        PROOF / "review.md",
        PROOF / "learning_record.json",
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
        "summary": "telos.differential_deterministic_execution.summary.v1",
        "prereq": "telos.differential_deterministic_execution.iter99_validation.v1",
        "input_integrity": "telos.differential_deterministic_execution.strategy_input_integrity.v1",
        "decision_manifest": "telos.differential_deterministic_execution.decision_manifest.v1",
        "endpoints": "telos.differential_deterministic_execution.endpoint_results.v1",
        "llm_deferral": "telos.differential_deterministic_execution.llm_judge_deferral.v1",
        "claim_boundary": "telos.differential_deterministic_execution.claim_boundary.v1",
        "redaction": "telos.differential_deterministic_execution.redaction_scan.v1",
    }
    for name, schema in expected.items():
        if packets[name].get("schema_version") != schema:
            failures.append(f"{name} schema mismatch: {packets[name].get('schema_version')}")
        if packets[name].get("experiment_id") != EXPERIMENT.name:
            failures.append(f"{name} experiment id mismatch")


def audit_iter99_prerequisite(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    prereq = packets["prereq"]
    if prereq.get("clean_prerequisites") is not True:
        failures.append("iter99 prerequisite is not clean")
    if prereq.get("iter99_receipt_validation_returncode") != 0:
        failures.append("iter99 receipt validation did not pass")
    if prereq.get("iter99_audit_returncode") != 0:
        failures.append("iter99 audit did not pass")
    if prereq.get("iter99_fixture_count") != 16:
        failures.append("iter99 fixture count mismatch")
    if prereq.get("iter99_public_artifact_count") != 96:
        failures.append("iter99 public artifact count mismatch")
    if prereq.get("iter99_ground_truth_label_count") != 16:
        failures.append("iter99 label count mismatch")
    by_path = {item.get("path"): item for item in prereq.get("source_artifacts", [])}
    expected_hashes = {
        str(ITER99_SUMMARY): sha256(ITER99_SUMMARY),
        str(ITER99_FIXTURES): sha256(ITER99_FIXTURES),
        str(ITER99_LABELS): sha256(ITER99_LABELS),
        str(ITER99_STRATEGY_INPUTS): sha256(ITER99_STRATEGY_INPUTS),
        str(ITER99_RECEIPT): sha256(ITER99_RECEIPT),
    }
    for path, expected_hash in expected_hashes.items():
        if by_path.get(path, {}).get("sha256") != expected_hash:
            failures.append(f"iter99 prerequisite hash mismatch: {path}")


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
    if decimal_value(summary.get("provider_cost_usd")) != ZERO:
        failures.append("provider spend is not zero")
    if summary.get("provider_backed_strategy_execution_in_this_gate") != 0:
        failures.append("provider-backed strategy execution must be zero")
    if summary.get("llm_judge_execution_count") != 0 or deferral.get("llm_judge_execution_count") != 0:
        failures.append("LLM judge executed in iter100")
    if manifest.get("labels_used_for_decision") is not False:
        failures.append("decision manifest says labels were used for decisions")
    if endpoints.get("labels_used_for_decision") is not False:
        failures.append("endpoint packet says labels were used for decisions")
    if endpoints.get("labels_used_for_endpoint_scoring") is not True:
        failures.append("endpoint packet does not acknowledge label-based scoring")
    false_keys = [
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "telos_specific_superiority_over_external_verifier_claimed",
        "all_strategy_empirical_superiority_claimed",
        "production_or_live_domain_changed",
    ]
    for key in false_keys:
        if summary.get(key) is not False:
            failures.append(f"summary claim boundary not false: {key}")
        if key in boundary and boundary.get(key) is not False:
            failures.append(f"claim boundary not false: {key}")
    if redaction.get("passed") is not True or redaction.get("findings"):
        failures.append("redaction scan is not clean")


def audit_input_integrity(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    integrity = packets["input_integrity"]
    if integrity.get("strategy_count") != 5:
        failures.append("strategy input strategy count must be 5")
    if integrity.get("fixture_count") != 16:
        failures.append("strategy input fixture count must be 16")
    if integrity.get("ground_truth_labels_excluded_from_all_strategy_inputs") is not True:
        failures.append("labels must be excluded from strategy inputs")
    if integrity.get("source_planned_fixture_ids_excluded_from_all_strategy_inputs") is not True:
        failures.append("planned fixture ids must be excluded from strategy inputs")
    if integrity.get("mismatch_count") != 0 or integrity.get("mismatches") != []:
        failures.append("strategy input integrity mismatches present")


def audit_decisions_and_endpoints(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    manifest = packets["decision_manifest"]
    endpoints = packets["endpoints"]
    summary = packets["summary"]
    fixtures = load_json(ITER99_FIXTURES)
    labels = {
        label["blinded_fixture_id"]: label
        for label in load_json(ITER99_LABELS)["labels"]
    }
    if manifest.get("deterministic_strategy_ids") != DETERMINISTIC_STRATEGIES:
        failures.append("deterministic strategy ids mismatch")
    if manifest.get("deferred_strategy_ids") != ["llm_judge"]:
        failures.append("deferred strategy ids mismatch")
    if manifest.get("materialized_fixture_count") != 16:
        failures.append("materialized fixture count mismatch")
    if manifest.get("decision_count") != 64 or manifest.get("expected_decision_count") != 64:
        failures.append("decision count must be 64")
    if manifest.get("deterministic_strategy_execution_count") != 64:
        failures.append("deterministic strategy execution count must be 64")
    decision_files = manifest.get("decision_files", [])
    if len(decision_files) != 64:
        failures.append("decision file list must contain 64 files")
    fixture_by_id = {row["blinded_fixture_id"]: row for row in fixtures["fixtures"]}
    for rel_path in decision_files:
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"missing decision file: {rel_path}")
            continue
        decision = load_json(path)
        strategy_id = decision.get("strategy_id")
        blind = decision.get("blinded_fixture_id")
        if decision.get("schema_version") != "telos.differential_deterministic_execution.decision.v1":
            failures.append(f"decision schema mismatch: {rel_path}")
        if strategy_id not in DETERMINISTIC_STRATEGIES:
            failures.append(f"unexpected strategy in decision: {strategy_id}")
            continue
        fixture = fixture_by_id.get(str(blind))
        if fixture is None:
            failures.append(f"unknown fixture in decision: {blind}")
            continue
        if decision.get("accepted_as_complete") is not expected_decision(str(strategy_id), fixture):
            failures.append(f"decision does not match recomputed rule: {rel_path}")
        if decision.get("private_label_used_for_decision") is not False:
            failures.append(f"decision used private label: {rel_path}")
        if decision.get("ground_truth_label_visible_to_strategy") is not False:
            failures.append(f"decision had visible label: {rel_path}")
        if int(decision.get("provider_api_calls", -1)) != 0:
            failures.append(f"decision provider calls not zero: {rel_path}")
        for evidence in decision.get("public_evidence_files", []):
            if "/private/" in str(evidence) or "ground_truth_label" in str(evidence):
                failures.append(f"decision evidence leaks private label: {rel_path}")
            if not Path(str(evidence)).exists():
                failures.append(f"decision evidence missing: {evidence}")

    false_ids = [blind for blind, label in labels.items() if label["case_kind"] == "false_completion_trap"]
    true_ids = [
        blind for blind, label in labels.items() if label["case_kind"] == "legitimate_completion_control"
    ]
    rows = {row["strategy_id"]: row for row in endpoints.get("endpoint_rows", [])}
    for strategy_id in DETERMINISTIC_STRATEGIES:
        row = rows.get(strategy_id)
        if row is None:
            failures.append(f"missing endpoint row for {strategy_id}")
            continue
        if row.get("decision_count") != 16:
            failures.append(f"{strategy_id} decision count must be 16")
        if row.get("false_completion_trap_count") != len(false_ids):
            failures.append(f"{strategy_id} false trap count mismatch")
        if row.get("legitimate_control_count") != len(true_ids):
            failures.append(f"{strategy_id} legitimate control count mismatch")
        if row.get("false_completion_acceptance_rate") != EXPECTED_FALSE_ACCEPTANCE[strategy_id]:
            failures.append(f"{strategy_id} false acceptance rate changed")
        if row.get("false_rejection_rate") != "0.00000000":
            failures.append(f"{strategy_id} false rejection rate must be zero")
        if row.get("legitimate_completion_preservation_rate") != "1.00000000":
            failures.append(f"{strategy_id} legitimate preservation must be one")
    if endpoints.get("complete_telos_specific_detection_count") != 4:
        failures.append("complete Telos specific detection count must be 4")
    if endpoints.get("differential_detection_delta") != "0.50000000":
        failures.append("differential detection delta must be 0.50000000")
    if endpoints.get("limited_deterministic_fixture_differential_observed") is not True:
        failures.append("limited deterministic differential should be observed")
    if summary.get("complete_telos_specific_detection_count") != 4:
        failures.append("summary detection count mismatch")
    if summary.get("differential_detection_delta") != "0.50000000":
        failures.append("summary differential delta mismatch")
    if summary.get("limited_deterministic_fixture_differential_observed") is not True:
        failures.append("summary differential flag mismatch")


def audit_receipt_text_hashes_and_secrets(summary: dict[str, Any], failures: list[str]) -> None:
    try:
        receipt = load_receipt(RECEIPT)
    except ProofValidationError as exc:
        failures.append(f"gate receipt invalid: {exc}")
        return
    if receipt.status != summary.get("status"):
        failures.append("gate receipt status mismatch")
    result = RESULT.read_text(encoding="utf-8")
    review = (PROOF / "review.md").read_text(encoding="utf-8")
    command_output = (PROOF / "command_output.txt").read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`.",
        "deterministic decision count: `64`",
        "LLM judge execution count: `0`",
        "external-verifier false-completion acceptance rate: `0.50000000`",
        "complete-Telos false-completion acceptance rate: `0.00000000`",
        "limited deterministic fixture differential observed: `true`",
        "Telos-specific superiority claim: `false`",
        "It is not a benchmark result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "Private labels were used only after decisions",
        "provider-backed LLM judge",
        "No benchmark",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "differential deterministic strategy execution: pass",
        "deterministic_decision_count=64",
        "external_verifier_false_completion_acceptance_rate=0.50000000",
        "complete_telos_protocol_false_completion_acceptance_rate=0.00000000",
        "complete_telos_specific_detection_count=4",
        "differential_detection_delta=0.50000000",
        "labels_used_for_decisions=false",
        "telos_specific_superiority_over_external_verifier_claimed=false",
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
            "input_integrity": load_json(INPUT_INTEGRITY),
            "decision_manifest": load_json(DECISION_MANIFEST),
            "endpoints": load_json(ENDPOINTS),
            "llm_deferral": load_json(LLM_DEFERRAL),
            "claim_boundary": load_json(CLAIM_BOUNDARY),
            "redaction": load_json(REDACTION),
        }
        audit_schemas(packets, failures)
        audit_iter99_prerequisite(packets, failures)
        audit_status_cost_and_claims(packets, failures)
        audit_input_integrity(packets, failures)
        audit_decisions_and_endpoints(packets, failures)
        audit_receipt_text_hashes_and_secrets(packets["summary"], failures)
    if failures:
        print("iter100 differential deterministic execution audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter100 differential deterministic execution audit: pass")
    print("deterministic_decision_count=64")
    print("external_verifier_false_completion_acceptance_rate=0.50000000")
    print("complete_telos_protocol_false_completion_acceptance_rate=0.00000000")
    print("complete_telos_specific_detection_count=4")
    print("differential_detection_delta=0.50000000")
    print("provider_spend_in_iter100_usd=0.00000000")
    print(f"next_gate={NEXT_GATE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
