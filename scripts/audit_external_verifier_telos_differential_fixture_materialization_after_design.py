#!/usr/bin/env python3
"""Audit iter99 external-verifier/Telos differential fixture materialization."""

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


EXPERIMENT = Path("experiments/iter99_external_verifier_telos_differential_fixture_materialization_after_design")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
PREREQ = PROOF / "iter98_prerequisite_validation.json"
FIXTURE_MANIFEST = PROOF / "fixture_manifest.json"
GROUND_TRUTH = PROOF / "ground_truth_labels.json"
STRATEGY_INPUTS = PROOF / "strategy_input_manifest.json"
REPORT = PROOF / "materialization_report.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary.json"
REDACTION = PROOF / "redaction_scan.json"
RECEIPT = (
    PROOF
    / "valid"
    / "receipt_external_verifier_telos_differential_fixture_materialization_after_design.json"
)
NEXT_GATE = Path(
    "experiments/iter100_deterministic_strategy_execution_on_differential_fixtures_after_materialization/"
    "HYPOTHESIS.md"
)

ITER98_PROOF = Path("experiments/iter98_external_verifier_telos_differential_suite_design_after_adjudication/proof")
ITER98_SUMMARY = ITER98_PROOF / "run_summary.json"
ITER98_MATRIX = ITER98_PROOF / "differential_target_matrix.json"
ITER98_RULES = ITER98_PROOF / "fixture_design_rules.json"
ITER98_ENDPOINTS = ITER98_PROOF / "endpoint_sample_size_rationale.json"
ITER98_BOUNDARY = ITER98_PROOF / "claim_boundary.json"
ITER98_RECEIPT = (
    ITER98_PROOF / "valid" / "receipt_external_verifier_telos_differential_suite_design_after_adjudication.json"
)

STRATEGY_IDS = [
    "agent_self_report",
    "execution_tests_only",
    "llm_judge",
    "external_verifier",
    "complete_telos_protocol",
]
COMMON_PUBLIC_FILES = [
    "fixture_spec.json",
    "task.md",
    "verification_rubric.md",
]
TARGET_PUBLIC_FILES = {
    "stale_receipt_current_artifacts": [
        "artifact_manifest.json",
        "changed_artifact.txt",
        "receipt.json",
    ],
    "missing_falsifier_hidden_by_passing_tests": [
        "acceptance_criteria.md",
        "receipt.json",
        "test.log",
    ],
    "setup_done_not_task_done": [
        "receipt.json",
        "transcript.txt",
        "workspace_listing.txt",
    ],
    "contradictory_artifact_packet": [
        "command_output.txt",
        "receipt.json",
        "summary.md",
    ],
    "schema_valid_semantic_incomplete_receipt": [
        "receipt.json",
        "review.md",
        "task_spec.md",
    ],
    "live_domain_flag_without_live_evidence": [
        "claim_boundary.json",
        "deployment_note.md",
        "receipt.json",
    ],
    "nondeterministic_result_no_replay": [
        "receipt.json",
        "replay_manifest.json",
        "result_summary.md",
    ],
    "adversarial_receipt_digest_collision_attempt": [
        "artifact_manifest.json",
        "receipt.json",
        "receipt_validation.txt",
    ],
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
    re.compile(r"external_verifier_telos_differential_result_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"comparative_performance_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"benchmark/model/SOTA claim:\s*`true`", re.IGNORECASE),
    re.compile(r"\bSOTA achieved\b", re.IGNORECASE),
    re.compile(r"\bstate-of-the-art achieved\b", re.IGNORECASE),
    re.compile(r"\bmodel superiority achieved\b", re.IGNORECASE),
    re.compile(r"\bTelos-specific superiority achieved\b", re.IGNORECASE),
    re.compile(r"\bcomparative performance achieved\b", re.IGNORECASE),
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


def audit_schemas(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    expected = {
        "summary": "telos.differential_fixture_materialization.summary.v1",
        "prereq": "telos.differential_fixture_materialization.iter98_validation.v1",
        "fixtures": "telos.differential_fixture_materialization.fixture_manifest.v1",
        "truth": "telos.differential_fixture_materialization.ground_truth_labels.v1",
        "strategy_inputs": "telos.differential_fixture_materialization.strategy_input_manifest.v1",
        "report": "telos.differential_fixture_materialization.report.v1",
        "boundary": "telos.differential_fixture_materialization.claim_boundary.v1",
        "redaction": "telos.differential_fixture_materialization.redaction_scan.v1",
    }
    for name, schema in expected.items():
        packet = packets[name]
        if packet.get("schema_version") != schema:
            failures.append(f"unexpected {name} schema: {packet.get('schema_version')}")
        if packet.get("experiment_id") != EXPERIMENT.name:
            failures.append(f"{name} experiment id mismatch")


def audit_status_and_zero_spend(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = packets["summary"]
    redaction = packets["redaction"]
    if summary.get("status") != "pass" or summary.get("clean_pass") is not True:
        failures.append("iter99 summary must be a clean pass")
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
        if decimal_value(spend) != ZERO:
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


def audit_iter98_prerequisite(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    prereq = packets["prereq"]
    if prereq.get("clean_prerequisites") is not True:
        failures.append("iter98 prerequisites must be clean")
    if prereq.get("iter98_status") != "pass" or prereq.get("iter98_clean_pass") is not True:
        failures.append("iter98 must remain a clean pass")
    if prereq.get("iter98_receipt_validation_returncode") != 0:
        failures.append("iter98 receipt validation must pass")
    if prereq.get("iter98_audit_returncode") != 0:
        failures.append("iter98 audit must pass")
    if prereq.get("iter98_target_family_count") != 8:
        failures.append("iter98 target family count must be eight")
    if prereq.get("iter98_planned_fixture_count") != 16:
        failures.append("iter98 planned fixture count must be sixteen")
    if prereq.get("iter98_expected_divergence_claimed_as_result") is not False:
        failures.append("iter98 must not claim expected divergence as a result")
    by_path = {item.get("path"): item for item in prereq.get("source_artifacts", [])}
    expected_hashes = {
        str(ITER98_SUMMARY): sha256(ITER98_SUMMARY),
        str(ITER98_MATRIX): sha256(ITER98_MATRIX),
        str(ITER98_RULES): sha256(ITER98_RULES),
        str(ITER98_ENDPOINTS): sha256(ITER98_ENDPOINTS),
        str(ITER98_BOUNDARY): sha256(ITER98_BOUNDARY),
        str(ITER98_RECEIPT): sha256(ITER98_RECEIPT),
    }
    for path, expected_hash in expected_hashes.items():
        if by_path.get(path, {}).get("sha256") != expected_hash:
            failures.append(f"iter98 source hash mismatch: {path}")


def audit_fixture_materialization(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = packets["summary"]
    fixtures = packets["fixtures"]
    truth = packets["truth"]
    strategy_inputs = packets["strategy_inputs"]
    report = packets["report"]
    matrix = load_json(ITER98_MATRIX)
    target_ids = [row["target_family_id"] for row in matrix["differential_target_rows"]]
    if fixtures.get("fixture_count") != 16 or summary.get("materialized_fixture_count") != 16:
        failures.append("fixture count must be 16")
    if fixtures.get("target_family_count") != 8 or summary.get("target_family_count") != 8:
        failures.append("target family count must be 8")
    if fixtures.get("public_artifact_count") != 96:
        failures.append("public artifact count must be 96")
    if truth.get("label_count") != 16 or summary.get("ground_truth_label_count") != 16:
        failures.append("ground-truth label count must be 16")
    if truth.get("false_completion_label_count") != 8:
        failures.append("false label count must be 8")
    if truth.get("legitimate_completion_label_count") != 8:
        failures.append("true label count must be 8")
    if truth.get("labels_visible_to_strategy_inputs") is not False:
        failures.append("labels must not be visible to strategy inputs")
    if truth.get("labels_independent_of_telos_outputs") is not True:
        failures.append("labels must be independent of Telos outputs")
    if strategy_inputs.get("strategy_ids") != STRATEGY_IDS:
        failures.append("strategy id list changed")
    if strategy_inputs.get("strategy_count") != 5:
        failures.append("strategy manifest count must be five")
    if strategy_inputs.get("all_strategies_receive_identical_public_artifacts") is not True:
        failures.append("strategy inputs must be identical")
    if strategy_inputs.get("ground_truth_labels_excluded_from_all_strategy_inputs") is not True:
        failures.append("labels must be excluded from all strategy inputs")
    if strategy_inputs.get("source_planned_fixture_ids_excluded_from_all_strategy_inputs") is not True:
        failures.append("planned fixture ids must be excluded from all strategy inputs")
    if report.get("fixture_materialization_complete") is not True:
        failures.append("materialization report must be complete")
    if summary.get("next_gate") != str(NEXT_GATE):
        failures.append("summary next gate changed")
    if summary.get("next_gate_pre_registered") is not True or not NEXT_GATE.exists():
        failures.append("next gate must be pre-registered")

    label_by_blind = {row.get("blinded_fixture_id"): row for row in truth.get("labels", [])}
    fixture_ids = fixtures.get("blinded_fixture_ids", [])
    if len(fixture_ids) != 16 or len(fixture_ids) != len(set(fixture_ids)):
        failures.append("blinded fixture ids must be 16 unique ids")
    for blind in fixture_ids:
        upper = str(blind).upper()
        if "TRUE" in upper or "FALSE" in upper or "TRAP" in upper or "LEGITIMATE" in upper:
            failures.append(f"blinded id leaks label: {blind}")
    target_counts = {target_id: 0 for target_id in target_ids}
    public_artifact_sets: dict[str, tuple[str, ...]] = {}
    public_hash_sets: dict[str, dict[str, str]] = {}
    for row in fixtures.get("fixtures", []):
        blind = str(row.get("blinded_fixture_id"))
        target_id = str(row.get("target_family_id"))
        if target_id not in target_counts:
            failures.append(f"unknown target family: {target_id}")
        else:
            target_counts[target_id] += 1
        label = label_by_blind.get(blind)
        if label is None:
            failures.append(f"missing ground truth label for {blind}")
            continue
        if label.get("label_visible_to_strategy_inputs") is not False:
            failures.append(f"{blind} label visibility must be false")
        if label.get("label_independent_of_telos_outputs") is not True:
            failures.append(f"{blind} label must be independent of Telos outputs")
        public_artifacts = row.get("public_artifacts", [])
        artifact_names = sorted(artifact.get("artifact_name") for artifact in public_artifacts)
        expected_names = sorted(COMMON_PUBLIC_FILES + TARGET_PUBLIC_FILES.get(target_id, []))
        if artifact_names != expected_names:
            failures.append(f"{blind} public artifact names changed: {artifact_names}")
        if row.get("public_artifact_count") != 6:
            failures.append(f"{blind} must have six public artifacts")
        for artifact in public_artifacts:
            path = Path(str(artifact.get("path")))
            if not path.exists():
                failures.append(f"{blind} missing public artifact {path}")
                continue
            if "/private/" in str(path):
                failures.append(f"{blind} private artifact leaked into public manifest")
            if sha256(path) != artifact.get("sha256"):
                failures.append(f"{blind} public artifact hash mismatch: {path}")
            if row.get("private_label_path") == str(path):
                failures.append(f"{blind} private label leaked into public artifacts")
        private_path = Path(str(row.get("private_label_path")))
        if not private_path.exists():
            failures.append(f"{blind} missing private label path")
        elif sha256(private_path) != row.get("private_label_sha256"):
            failures.append(f"{blind} private label hash mismatch")
        public_artifact_sets[blind] = tuple(artifact.get("path") for artifact in public_artifacts)
        public_hash_sets[blind] = {
            str(artifact.get("path")): str(artifact.get("sha256")) for artifact in public_artifacts
        }
    for target_id, count in target_counts.items():
        if count != 2:
            failures.append(f"{target_id} must have two fixtures")

    for strategy in strategy_inputs.get("strategy_manifests", []):
        strategy_id = strategy.get("strategy_id")
        if strategy.get("fixture_count") != 16:
            failures.append(f"{strategy_id} must have 16 fixture inputs")
        if strategy.get("identical_public_artifact_packets") is not True:
            failures.append(f"{strategy_id} must use identical packets")
        if strategy.get("ground_truth_labels_excluded") is not True:
            failures.append(f"{strategy_id} must exclude labels")
        if strategy.get("strategy_execution_in_this_gate") != 0:
            failures.append(f"{strategy_id} must not execute in iter99")
        for fixture_input in strategy.get("fixture_inputs", []):
            blind = str(fixture_input.get("blinded_fixture_id"))
            expected_paths = public_artifact_sets.get(blind)
            expected_hashes = public_hash_sets.get(blind)
            if expected_paths is None or expected_hashes is None:
                failures.append(f"{strategy_id} unknown blind id {blind}")
                continue
            if tuple(fixture_input.get("public_artifact_paths", [])) != expected_paths:
                failures.append(f"{strategy_id} artifact paths changed for {blind}")
            if fixture_input.get("public_artifact_hashes") != expected_hashes:
                failures.append(f"{strategy_id} artifact hashes changed for {blind}")
            if fixture_input.get("private_label_included") is not False:
                failures.append(f"{strategy_id} includes a private label for {blind}")
            if fixture_input.get("private_label_path_included") is not False:
                failures.append(f"{strategy_id} includes a private label path for {blind}")
            if fixture_input.get("source_planned_fixture_id_included") is not False:
                failures.append(f"{strategy_id} includes a label-bearing planned fixture id for {blind}")
            for path in fixture_input.get("public_artifact_paths", []):
                if "/private/" in str(path) or "ground_truth_label" in str(path):
                    failures.append(f"{strategy_id} public input leaks private label path for {blind}")


def audit_claim_boundary(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = packets["summary"]
    boundary = packets["boundary"]
    false_keys = [
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "swebench_execution_or_score_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "telos_specific_superiority_over_external_verifier_claimed",
        "external_verifier_telos_differential_result_claimed",
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
    if boundary.get("future_paid_execution_authorized_by_iter99") is not False:
        failures.append("iter99 must not authorize paid execution")


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
        "target families: `8`",
        "materialized fixture count: `16`",
        "materialized public artifact count: `96`",
        "ground-truth label count: `16`",
        "all strategy inputs identical: `true`",
        "labels excluded from strategy inputs: `true`",
        "strategy execution in this gate: `0`",
        "Telos-specific superiority claim: `false`",
        "It is not a benchmark result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "No strategy executed.",
        "labels are committed for later scoring but excluded from every",
        "differential-result, comparative-performance, or",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "differential fixture materialization: pass",
        "target_family_count=8",
        "materialized_fixture_count=16",
        "materialized_public_artifact_count=96",
        "ground_truth_label_count=16",
        "strategy_input_manifest_count=5",
        "all_strategy_inputs_identical=true",
        "labels_excluded_from_strategy_inputs=true",
        "strategy_execution_in_this_gate=0",
        "external_verifier_telos_differential_result_claimed=false",
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
        audit_iter98_prerequisite(packets, failures)
        audit_fixture_materialization(packets, failures)
        audit_claim_boundary(packets, failures)
        audit_receipt_text_hashes_and_secrets(packets["summary"], failures)
    if failures:
        print("iter99 differential fixture materialization audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter99 differential fixture materialization audit: pass")
    print("target_family_count=8")
    print("fixture_count=16")
    print("public_artifact_count=96")
    print("strategy_execution_in_iter99=0")
    print("provider_spend_in_iter99_usd=0.00000000")
    print(f"next_gate={NEXT_GATE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
