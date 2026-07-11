#!/usr/bin/env python3
"""Audit iter92 empirical validation fixture materialization artifacts."""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter92_empirical_validation_fixture_materialization_for_completion_verification")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
PREREQ = PROOF / "iter91_prerequisite_validation.json"
FIXTURE_MANIFEST = PROOF / "fixture_manifest.json"
GROUND_TRUTH = PROOF / "ground_truth_labels.json"
STRATEGY_INPUTS = PROOF / "strategy_input_manifest.json"
REPORT = PROOF / "materialization_report.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary.json"
REDACTION = PROOF / "redaction_scan.json"
RECEIPT = PROOF / "valid" / "receipt_empirical_validation_fixture_materialization_for_completion_verification.json"
NEXT_GATE = Path("experiments/iter93_deterministic_strategy_execution_on_materialized_fixtures/HYPOTHESIS.md")

ITER91_PROOF = Path("experiments/iter91_empirical_validation_suite_design_for_completion_verification/proof")
ITER91_SUMMARY = ITER91_PROOF / "run_summary.json"
ITER91_CASES = ITER91_PROOF / "case_catalog.json"
ITER91_STRATEGIES = ITER91_PROOF / "strategy_comparison_plan.json"
ITER91_ENDPOINTS = ITER91_PROOF / "endpoint_spec.json"
ITER91_TRUTH = ITER91_PROOF / "ground_truth_policy.json"
ITER91_RECEIPT = ITER91_PROOF / "valid" / "receipt_empirical_validation_suite_design_for_completion_verification.json"

VERIFICATION_STRATEGIES = [
    "agent_self_report",
    "execution_tests_only",
    "llm_judge",
    "external_verifier",
    "complete_telos_protocol",
]
PUBLIC_ARTIFACT_FILES = [
    "case_spec.json",
    "task.md",
    "agent_final_message.md",
    "diff.patch",
    "visible_test_log.txt",
    "receipt_candidate.json",
    "verification_rubric.md",
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
FORBIDDEN_CLAIM_PATTERNS = [
    re.compile(r"benchmark_result_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"model_superiority_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"state_of_the_art_result_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"empirical_superiority_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"comparative_performance_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"benchmark/model/SOTA claim:\s*`true`", re.IGNORECASE),
    re.compile(r"\bSOTA achieved\b", re.IGNORECASE),
    re.compile(r"\bstate-of-the-art achieved\b", re.IGNORECASE),
    re.compile(r"\bmodel superiority achieved\b", re.IGNORECASE),
    re.compile(r"\bempirical superiority achieved\b", re.IGNORECASE),
    re.compile(r"\bcomparative performance achieved\b", re.IGNORECASE),
    re.compile(r"\bleaderboard win\b", re.IGNORECASE),
    re.compile(r"\bSWE-bench win\b", re.IGNORECASE),
]


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be an object")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decimal_value(value: object) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.00000001"))


def text_files(path: Path) -> list[Path]:
    return [
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file() and candidate.suffix in TEXT_SUFFIXES
    ]


def audit_required_files(failures: list[str]) -> None:
    for path in [
        RESULT,
        SUMMARY,
        PREREQ,
        FIXTURE_MANIFEST,
        GROUND_TRUTH,
        STRATEGY_INPUTS,
        REPORT,
        CLAIM_BOUNDARY,
        REDACTION,
        PROOF / "command_output.txt",
        PROOF / "review.md",
        PROOF / "learning_record.json",
        RECEIPT,
        NEXT_GATE,
    ]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")


def audit_schemas(packets: dict[str, dict], failures: list[str]) -> None:
    expected = {
        "summary": "telos.empirical_validation_fixture_materialization.summary.v1",
        "prereq": "telos.empirical_validation_fixture_materialization.iter91_prerequisite_validation.v1",
        "fixtures": "telos.empirical_validation_fixture_materialization.fixture_manifest.v1",
        "truth": "telos.empirical_validation_fixture_materialization.ground_truth_labels.v1",
        "strategy_inputs": "telos.empirical_validation_fixture_materialization.strategy_input_manifest.v1",
        "report": "telos.empirical_validation_fixture_materialization.report.v1",
        "boundary": "telos.empirical_validation_fixture_materialization.claim_boundary.v1",
        "redaction": "telos.empirical_validation_fixture_materialization.redaction_scan.v1",
    }
    for name, schema in expected.items():
        packet = packets[name]
        if packet.get("schema_version") != schema:
            failures.append(f"unexpected {name} schema")
        if packet.get("experiment_id") != EXPERIMENT.name:
            failures.append(f"{name} experiment id mismatch")


def audit_status_and_zero_spend(packets: dict[str, dict], failures: list[str]) -> None:
    summary = packets["summary"]
    redaction = packets["redaction"]
    if summary.get("status") != "pass" or summary.get("clean_pass") is not True:
        failures.append("iter92 summary must be a clean pass")
    if summary.get("blocked_result") is not False or summary.get("quality_failure") is not False:
        failures.append("summary blocked/quality flags must be false")
    if summary.get("blockers") != [] or summary.get("failures") != []:
        failures.append("pass summary must not contain blockers/failures")
    for packet_name in ["summary", "prereq", "fixtures", "truth", "strategy_inputs", "report"]:
        packet = packets[packet_name]
        calls = packet.get("provider_api_calls", packet.get("provider_calls_in_this_gate", 0))
        spend = packet.get(
            "provider_cost_usd",
            packet.get("provider_spend_in_this_gate_usd", "0.00000000"),
        )
        rows = packet.get("row_execution_in_this_gate", 0)
        strategy_execution = packet.get("strategy_execution_in_this_gate", 0)
        if calls != 0:
            failures.append(f"{packet_name} provider calls must be zero")
        if decimal_value(spend) != Decimal("0.00000000"):
            failures.append(f"{packet_name} provider spend must be zero")
        if rows != 0:
            failures.append(f"{packet_name} row execution must be zero")
        if strategy_execution != 0:
            failures.append(f"{packet_name} strategy execution must be zero")
    for key in ["gpu_used", "cloud_runner_started", "sentinel_named_resources_modified"]:
        if summary.get(key) is not False:
            failures.append(f"summary {key} must be false")
    if redaction.get("passed") is not True or redaction.get("findings") != []:
        failures.append("redaction scan must pass with no findings")
    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("summary redaction scan must pass")


def audit_iter91_prerequisite(packets: dict[str, dict], failures: list[str]) -> None:
    prereq = packets["prereq"]
    if prereq.get("clean_prerequisites") is not True:
        failures.append("iter91 prerequisites must be clean")
    if prereq.get("iter91_status") != "pass" or prereq.get("iter91_clean_pass") is not True:
        failures.append("iter91 must remain a clean pass")
    if prereq.get("iter91_receipt_validation_returncode") != 0:
        failures.append("iter91 receipt validation must pass")
    if prereq.get("iter91_audit_returncode") != 0:
        failures.append("iter91 audit must pass")
    by_path = {item.get("path"): item for item in prereq.get("source_artifacts", [])}
    expected_hashes = {
        str(ITER91_SUMMARY): sha256(ITER91_SUMMARY),
        str(ITER91_CASES): sha256(ITER91_CASES),
        str(ITER91_STRATEGIES): sha256(ITER91_STRATEGIES),
        str(ITER91_ENDPOINTS): sha256(ITER91_ENDPOINTS),
        str(ITER91_TRUTH): sha256(ITER91_TRUTH),
        str(ITER91_RECEIPT): sha256(ITER91_RECEIPT),
    }
    for path, expected_hash in expected_hashes.items():
        if by_path.get(path, {}).get("sha256") != expected_hash:
            failures.append(f"iter91 source hash mismatch: {path}")


def audit_fixture_materialization(packets: dict[str, dict], failures: list[str]) -> None:
    summary = packets["summary"]
    fixtures = packets["fixtures"]
    truth = packets["truth"]
    strategy_inputs = packets["strategy_inputs"]
    report = packets["report"]
    if fixtures.get("fixture_count") != 14 or summary.get("materialized_fixture_count") != 14:
        failures.append("fixture count must be 14")
    if fixtures.get("public_artifact_count") != 98:
        failures.append("public artifact count must be 98")
    if truth.get("label_count") != 14 or summary.get("ground_truth_label_count") != 14:
        failures.append("ground-truth label count must be 14")
    if truth.get("false_completion_label_count") != 7:
        failures.append("false label count must be 7")
    if truth.get("legitimate_completion_label_count") != 7:
        failures.append("true label count must be 7")
    if truth.get("labels_visible_to_strategy_inputs") is not False:
        failures.append("labels must not be visible to strategy inputs")
    if truth.get("labels_independent_of_telos_outputs") is not True:
        failures.append("labels must be independent of Telos outputs")
    if strategy_inputs.get("strategy_ids") != VERIFICATION_STRATEGIES:
        failures.append("strategy id list changed")
    if strategy_inputs.get("strategy_count") != 5:
        failures.append("strategy manifest count must be five")
    if strategy_inputs.get("all_strategies_receive_identical_public_artifacts") is not True:
        failures.append("strategy inputs must be identical")
    if strategy_inputs.get("ground_truth_labels_excluded_from_all_strategy_inputs") is not True:
        failures.append("labels must be excluded from all strategy inputs")
    if report.get("fixture_materialization_complete") is not True:
        failures.append("materialization report must be complete")
    if summary.get("next_gate") != str(NEXT_GATE):
        failures.append("summary next gate changed")
    if summary.get("next_gate_pre_registered") is not True or not NEXT_GATE.exists():
        failures.append("next gate must be pre-registered")

    label_by_blind = {row.get("blinded_case_id"): row for row in truth.get("labels", [])}
    fixture_ids = fixtures.get("blinded_case_ids", [])
    if len(fixture_ids) != len(set(fixture_ids)):
        failures.append("blinded fixture ids must be unique")
    for blind in fixture_ids:
        if "TRUE" in str(blind) or "FALSE" in str(blind):
            failures.append(f"blinded id leaks label: {blind}")
    public_artifact_sets: dict[str, tuple[str, ...]] = {}
    public_hash_sets: dict[str, dict[str, str]] = {}
    for row in fixtures.get("fixtures", []):
        blind = row.get("blinded_case_id")
        label = label_by_blind.get(blind)
        if label is None:
            failures.append(f"missing ground truth label for {blind}")
            continue
        public_artifacts = row.get("public_artifacts", [])
        artifact_names = sorted(artifact.get("artifact_name") for artifact in public_artifacts)
        if artifact_names != sorted(PUBLIC_ARTIFACT_FILES):
            failures.append(f"{blind} public artifact names changed")
        for artifact in public_artifacts:
            path = Path(str(artifact.get("path")))
            if not path.exists():
                failures.append(f"{blind} missing public artifact {path}")
                continue
            if sha256(path) != artifact.get("sha256"):
                failures.append(f"{blind} public artifact hash mismatch: {path}")
            if row.get("private_label_path") == str(path):
                failures.append(f"{blind} private label leaked into public artifacts")
        private_path = Path(str(row.get("private_label_path")))
        if not private_path.exists():
            failures.append(f"{blind} missing private label path")
        elif sha256(private_path) != row.get("private_label_sha256"):
            failures.append(f"{blind} private label hash mismatch")
        public_artifact_sets[str(blind)] = tuple(artifact.get("path") for artifact in public_artifacts)
        public_hash_sets[str(blind)] = {
            str(artifact.get("path")): str(artifact.get("sha256")) for artifact in public_artifacts
        }

    for strategy in strategy_inputs.get("strategy_manifests", []):
        if strategy.get("case_count") != 14:
            failures.append(f"{strategy.get('strategy_id')} must have 14 case inputs")
        if strategy.get("identical_public_artifact_packets") is not True:
            failures.append(f"{strategy.get('strategy_id')} must use identical packets")
        if strategy.get("ground_truth_labels_excluded") is not True:
            failures.append(f"{strategy.get('strategy_id')} must exclude labels")
        if strategy.get("strategy_execution_in_this_gate") != 0:
            failures.append(f"{strategy.get('strategy_id')} must not execute in iter92")
        for case_input in strategy.get("case_inputs", []):
            blind = str(case_input.get("blinded_case_id"))
            expected_paths = public_artifact_sets.get(blind)
            expected_hashes = public_hash_sets.get(blind)
            if expected_paths is None or expected_hashes is None:
                failures.append(f"{strategy.get('strategy_id')} unknown blind id {blind}")
                continue
            if tuple(case_input.get("public_artifact_paths", [])) != expected_paths:
                failures.append(f"{strategy.get('strategy_id')} artifact paths changed for {blind}")
            if case_input.get("public_artifact_hashes") != expected_hashes:
                failures.append(f"{strategy.get('strategy_id')} artifact hashes changed for {blind}")
            if case_input.get("excluded_private_label_path") in case_input.get("public_artifact_paths", []):
                failures.append(f"{strategy.get('strategy_id')} leaks label path for {blind}")


def audit_claim_boundary(packets: dict[str, dict], failures: list[str]) -> None:
    summary = packets["summary"]
    boundary = packets["boundary"]
    false_keys = [
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "swebench_execution_or_score_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "empirical_superiority_claimed",
        "comparative_performance_claimed",
        "production_or_live_domain_changed",
    ]
    for key in false_keys:
        if summary.get(key) is not False:
            failures.append(f"summary {key} must be false")
        if boundary.get(key) is not False:
            failures.append(f"claim boundary {key} must be false")
    if boundary.get("strategy_execution_completed") is not False:
        failures.append("strategy execution must not be claimed")
    if boundary.get("provider_execution_completed") is not False:
        failures.append("provider execution must not be claimed")
    if boundary.get("future_paid_execution_authorized_by_iter92") is not False:
        failures.append("iter92 must not authorize paid execution")


def audit_receipt_text_hashes_and_secrets(summary: dict, failures: list[str]) -> None:
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
        "materialized fixture count: `14`",
        "materialized public artifact count: `98`",
        "ground-truth label count: `14`",
        "all strategy inputs identical: `true`",
        "labels excluded from strategy inputs: `true`",
        "strategy execution in this gate: `0`",
        "comparative-performance claim: `false`",
        "It is not a benchmark result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "No strategy executed.",
        "labels are committed for scoring but excluded from every",
        "comparative-performance, or state-of-the-art result is",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "empirical validation fixture materialization: pass",
        "materialized_fixture_count=14",
        "materialized_public_artifact_count=98",
        "ground_truth_label_count=14",
        "strategy_input_manifest_count=5",
        "all_strategy_inputs_identical=true",
        "labels_excluded_from_strategy_inputs=true",
        "strategy_execution_in_this_gate=0",
        "comparative_performance_claimed=false",
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
            "fixtures": load_json(FIXTURE_MANIFEST),
            "truth": load_json(GROUND_TRUTH),
            "strategy_inputs": load_json(STRATEGY_INPUTS),
            "report": load_json(REPORT),
            "boundary": load_json(CLAIM_BOUNDARY),
            "redaction": load_json(REDACTION),
        }
        audit_schemas(packets, failures)
        audit_status_and_zero_spend(packets, failures)
        audit_iter91_prerequisite(packets, failures)
        audit_fixture_materialization(packets, failures)
        audit_claim_boundary(packets, failures)
        audit_receipt_text_hashes_and_secrets(packets["summary"], failures)
    if failures:
        print("iter92 empirical validation fixture materialization audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter92 empirical validation fixture materialization audit: pass")
    print("fixture_count=14")
    print("public_artifact_count=98")
    print("strategy_execution_in_iter92=0")
    print("provider_spend_in_iter92_usd=0.00000000")
    print(f"next_gate={NEXT_GATE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
