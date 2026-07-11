#!/usr/bin/env python3
"""Audit iter106 external benchmark pilot materialization artifacts."""

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


EXPERIMENT = Path("experiments/iter106_external_benchmark_pilot_materialization_after_design")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
PREREQ = PROOF / "iter105_prerequisite_validation.json"
SELECTED = PROOF / "selected_packet_manifest.json"
PUBLIC_HASHES = PROOF / "public_artifact_hash_manifest.json"
PRIVATE_LABELS = PROOF / "private_label_manifest.json"
STRATEGY_INPUTS = PROOF / "strategy_input_manifest.json"
REPORT = PROOF / "materialization_report.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary.json"
REDACTION = PROOF / "redaction_scan.json"
RECEIPT = PROOF / "valid" / "receipt_external_benchmark_pilot_materialization_after_design.json"
NEXT_GATE = Path("experiments/iter107_external_benchmark_pilot_execution_after_materialization/HYPOTHESIS.md")

ITER105_PROOF = Path("experiments/iter105_external_benchmark_pilot_design_after_differential_adjudication/proof")
ITER105_SUMMARY = ITER105_PROOF / "run_summary.json"
ITER105_TASK_SOURCE = ITER105_PROOF / "pilot_task_source_selection.json"
ITER105_COMPARISON = ITER105_PROOF / "baseline_telos_comparison_design.json"
ITER105_BUDGET = ITER105_PROOF / "sample_size_budget_rationale.json"
ITER105_STOPPING = ITER105_PROOF / "stopping_null_result_rules.json"
ITER105_ARTIFACTS = ITER105_PROOF / "artifact_receipt_requirements.json"
ITER105_BOUNDARY = ITER105_PROOF / "claim_boundary.json"
ITER105_RECEIPT = (
    ITER105_PROOF
    / "valid"
    / "receipt_external_benchmark_pilot_design_after_differential_adjudication.json"
)
SOURCE_SNAPSHOT = Path("experiments/source_snapshots/codeclash/configs/test/dummy.yaml")

ZERO = Decimal("0.00000000")
FUTURE_SPEND_CEILING = Decimal("10.00000000")
PACKET_COUNT = 20
PAIR_COUNT = 10
FALSE_PACKET_COUNT = 10
LEGITIMATE_PACKET_COUNT = 10
PROVIDER_CALL_CEILING = 30
PUBLIC_ARTIFACT_NAMES = [
    "task_statement.md",
    "repository_commit.txt",
    "setup_manifest.json",
    "baseline_visible_test_log.txt",
    "completion_claim.md",
    "artifact_manifest.json",
    "receipt_or_receipt_absence.json",
    "strategy_input_manifest.json",
]
PRIVATE_ARTIFACT_NAMES = ["ground_truth_label.json", "label_rationale.md"]
STRATEGY_IDS = [
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
FORBIDDEN_CLAIM_PATTERNS = [
    re.compile(r"benchmark_result_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"external_benchmark_result_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"leaderboard_or_swebench_result_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"model_superiority_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"state_of_the_art_result_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"all_strategy_superiority_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"comparative_performance_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"benchmark/model/SOTA claim:\s*`true`", re.IGNORECASE),
    re.compile(r"\bSOTA achieved\b", re.IGNORECASE),
    re.compile(r"\bstate-of-the-art achieved\b", re.IGNORECASE),
    re.compile(r"\bmodel superiority achieved\b", re.IGNORECASE),
    re.compile(r"\bbenchmark achieved\b", re.IGNORECASE),
    re.compile(r"\bcomparative performance achieved\b", re.IGNORECASE),
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
        SELECTED,
        PUBLIC_HASHES,
        PRIVATE_LABELS,
        STRATEGY_INPUTS,
        REPORT,
        CLAIM_BOUNDARY,
        REDACTION,
        PROOF / "command_output.txt",
        PROOF / "materialization_review.md",
        PROOF / "review.md",
        PROOF / "learning_record.json",
        RECEIPT,
        NEXT_GATE,
    ]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")


def audit_schemas(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    expected = {
        "summary": "telos.external_benchmark_pilot_materialization.summary.v1",
        "prereq": "telos.external_benchmark_pilot_materialization.iter105_validation.v1",
        "selected": "telos.external_benchmark_pilot_materialization.selected_packet_manifest.v1",
        "public_hashes": "telos.external_benchmark_pilot_materialization.public_hashes.v1",
        "private_labels": "telos.external_benchmark_pilot_materialization.private_labels.v1",
        "strategy_inputs": "telos.external_benchmark_pilot_materialization.strategy_inputs.v1",
        "report": "telos.external_benchmark_pilot_materialization.report.v1",
        "boundary": "telos.external_benchmark_pilot_materialization.claim_boundary.v1",
        "redaction": "telos.external_benchmark_pilot_materialization.redaction_scan.v1",
    }
    for name, schema in expected.items():
        packet = packets[name]
        if packet.get("schema_version") != schema:
            failures.append(f"unexpected {name} schema: {packet.get('schema_version')}")
        if packet.get("experiment_id") != EXPERIMENT.name:
            failures.append(f"{name} experiment id mismatch")


def audit_status_and_zero_execution(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = packets["summary"]
    redaction = packets["redaction"]
    if summary.get("status") != "pass" or summary.get("clean_pass") is not True:
        failures.append("iter106 summary must be a clean pass")
    if summary.get("blocked_result") is not False or summary.get("quality_failure") is not False:
        failures.append("summary blocked/quality flags must be false")
    if summary.get("blockers") != [] or summary.get("failures") != []:
        failures.append("pass summary must not contain blockers/failures")
    for packet_name in ["summary", "prereq", "selected", "public_hashes", "private_labels", "strategy_inputs", "report"]:
        packet = packets[packet_name]
        calls = packet.get("provider_api_calls", packet.get("provider_calls_in_this_gate", 0))
        spend = packet.get("provider_cost_usd", packet.get("provider_spend_in_this_gate_usd", "0.00000000"))
        task_execution = packet.get("benchmark_task_execution_in_this_gate", 0)
        strategy_execution = packet.get("strategy_execution_in_this_gate", 0)
        row_execution = packet.get("row_execution_in_this_gate", 0)
        if calls != 0:
            failures.append(f"{packet_name} provider calls must be zero")
        if decimal_value(spend) != ZERO:
            failures.append(f"{packet_name} provider spend must be zero")
        if task_execution != 0:
            failures.append(f"{packet_name} benchmark task execution must be zero")
        if strategy_execution != 0:
            failures.append(f"{packet_name} strategy execution must be zero")
        if row_execution != 0:
            failures.append(f"{packet_name} row execution must be zero")
    for key in [
        "gpu_used",
        "cloud_runner_started",
        "sentinel_named_resources_modified",
        "production_or_live_domain_changed",
    ]:
        if summary.get(key) is not False:
            failures.append(f"summary {key} must be false")
    if redaction.get("passed") is not True or redaction.get("findings") != []:
        failures.append("redaction scan must pass with no findings")
    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("summary redaction scan must pass")


def audit_iter105_prerequisite(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    prereq = packets["prereq"]
    if prereq.get("clean_prerequisites") is not True:
        failures.append("iter105 prerequisites must be clean")
    if prereq.get("iter105_status") != "pass" or prereq.get("iter105_clean_pass") is not True:
        failures.append("iter105 source status must be pass")
    if prereq.get("iter105_receipt_validation_returncode") != 0:
        failures.append("iter105 receipt validation must pass")
    if prereq.get("iter105_audit_returncode") != 0:
        failures.append("iter105 audit must pass")
    if prereq.get("iter105_planned_packet_count") != PACKET_COUNT:
        failures.append("iter105 planned packet count mismatch")
    if prereq.get("iter105_strategy_ids") != STRATEGY_IDS:
        failures.append("iter105 strategy list mismatch")
    if prereq.get("iter105_private_labels_excluded_from_strategy_inputs") is not True:
        failures.append("iter105 label exclusion must be true")
    if prereq.get("iter105_future_provider_call_ceiling") != PROVIDER_CALL_CEILING:
        failures.append("iter105 provider call ceiling mismatch")
    if decimal_value(prereq.get("iter105_future_spend_ceiling_usd")) != FUTURE_SPEND_CEILING:
        failures.append("iter105 future spend ceiling mismatch")
    if prereq.get("iter105_benchmark_result_claimed") is not False:
        failures.append("iter105 must not claim benchmark result")
    expected_hashes = {
        "iter105_summary": sha256(ITER105_SUMMARY),
        "iter105_task_source": sha256(ITER105_TASK_SOURCE),
        "iter105_comparison": sha256(ITER105_COMPARISON),
        "iter105_budget": sha256(ITER105_BUDGET),
        "iter105_stopping": sha256(ITER105_STOPPING),
        "iter105_artifacts": sha256(ITER105_ARTIFACTS),
        "iter105_boundary": sha256(ITER105_BOUNDARY),
        "iter105_receipt": sha256(ITER105_RECEIPT),
        "codeclash_dummy_source_snapshot": sha256(SOURCE_SNAPSHOT),
    }
    if prereq.get("source_hashes") != expected_hashes:
        failures.append("iter105/source-anchor hashes mismatch")


def audit_packet_materialization(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = packets["summary"]
    selected = packets["selected"]
    public_hashes = packets["public_hashes"]
    private_labels = packets["private_labels"]
    strategy_inputs = packets["strategy_inputs"]
    report = packets["report"]
    if selected.get("packet_count") != PACKET_COUNT or summary.get("materialized_packet_count") != PACKET_COUNT:
        failures.append("packet count must be 20")
    if selected.get("pair_count") != PAIR_COUNT or summary.get("materialized_pair_count") != PAIR_COUNT:
        failures.append("pair count must be 10")
    if private_labels.get("false_completion_label_count") != FALSE_PACKET_COUNT:
        failures.append("false-completion label count must be 10")
    if private_labels.get("legitimate_completion_label_count") != LEGITIMATE_PACKET_COUNT:
        failures.append("legitimate-control label count must be 10")
    if public_hashes.get("public_artifact_count") != PACKET_COUNT * len(PUBLIC_ARTIFACT_NAMES):
        failures.append("public artifact count must be 160")
    if report.get("materialization_complete") is not True:
        failures.append("materialization report must be complete")
    if summary.get("next_gate") != str(NEXT_GATE):
        failures.append("summary next gate changed")
    if summary.get("next_gate_pre_registered") is not True or not NEXT_GATE.exists():
        failures.append("next gate must be pre-registered")
    if selected.get("source_anchor", {}).get("codeclash_snapshot_sha256") != sha256(SOURCE_SNAPSHOT):
        failures.append("source anchor snapshot hash mismatch")

    labels_by_packet = {
        row.get("blinded_packet_id"): row for row in private_labels.get("labels", [])
    }
    selected_by_packet = {row.get("blinded_packet_id"): row for row in selected.get("packets", [])}
    hash_by_packet = {
        row.get("blinded_packet_id"): row.get("public_artifact_hashes", {})
        for row in public_hashes.get("packet_public_artifact_hashes", [])
    }
    if len(selected_by_packet) != PACKET_COUNT or len(labels_by_packet) != PACKET_COUNT:
        failures.append("packet ids must be unique across selected packets and private labels")
    false_count = 0
    true_count = 0
    pair_counts: dict[str, int] = {}
    for blind, row in selected_by_packet.items():
        if not isinstance(blind, str) or not blind.startswith("EBP-PACKET-"):
            failures.append(f"unexpected blinded packet id: {blind}")
            continue
        upper = blind.upper()
        if "FALSE" in upper or "TRUE" in upper or "TRAP" in upper or "LEGITIMATE" in upper:
            failures.append(f"blinded packet id leaks label: {blind}")
        label = labels_by_packet.get(blind)
        if label is None:
            failures.append(f"missing private label for {blind}")
            continue
        pair_counts[label["pair_id"]] = pair_counts.get(label["pair_id"], 0) + 1
        false_count += int(label.get("ground_truth_completed") is False)
        true_count += int(label.get("ground_truth_completed") is True)
        if label.get("label_visible_to_strategy_inputs") is not False:
            failures.append(f"{blind} label must not be visible to strategies")
        if label.get("label_independent_of_telos_outputs") is not True:
            failures.append(f"{blind} label must be independent of Telos outputs")
        public_artifacts = row.get("public_artifacts", [])
        private_artifacts = row.get("private_artifacts", [])
        if sorted(artifact.get("artifact_name") for artifact in public_artifacts) != sorted(PUBLIC_ARTIFACT_NAMES):
            failures.append(f"{blind} public artifact names changed")
        if sorted(artifact.get("artifact_name") for artifact in private_artifacts) != sorted(PRIVATE_ARTIFACT_NAMES):
            failures.append(f"{blind} private artifact names changed")
        if row.get("public_artifact_count") != len(PUBLIC_ARTIFACT_NAMES):
            failures.append(f"{blind} public artifact count mismatch")
        if row.get("private_artifact_count") != len(PRIVATE_ARTIFACT_NAMES):
            failures.append(f"{blind} private artifact count mismatch")
        global_hashes = hash_by_packet.get(blind)
        if not global_hashes:
            failures.append(f"missing global public hashes for {blind}")
        for artifact in public_artifacts:
            path = Path(str(artifact.get("path")))
            if not path.exists():
                failures.append(f"{blind} missing public artifact {path}")
                continue
            if "/private/" in str(path) or "ground_truth_label" in str(path):
                failures.append(f"{blind} private artifact leaked into public manifest")
            if path.name not in PUBLIC_ARTIFACT_NAMES:
                failures.append(f"{blind} unexpected public artifact name {path.name}")
            actual_hash = sha256(path)
            if actual_hash != artifact.get("sha256"):
                failures.append(f"{blind} selected public hash mismatch: {path}")
            if global_hashes and global_hashes.get(str(path)) != actual_hash:
                failures.append(f"{blind} global public hash mismatch: {path}")
        for artifact in private_artifacts:
            path = Path(str(artifact.get("path")))
            if not path.exists():
                failures.append(f"{blind} missing private artifact {path}")
            elif sha256(path) != artifact.get("sha256"):
                failures.append(f"{blind} private artifact hash mismatch: {path}")
    if false_count != FALSE_PACKET_COUNT or true_count != LEGITIMATE_PACKET_COUNT:
        failures.append("private label balance mismatch")
    for pair, count in pair_counts.items():
        if count != 2:
            failures.append(f"{pair} must contain two labels")

    if strategy_inputs.get("strategy_ids") != STRATEGY_IDS or strategy_inputs.get("strategy_count") != 5:
        failures.append("strategy manifest ids/count changed")
    if strategy_inputs.get("all_strategies_receive_identical_public_artifacts") is not True:
        failures.append("strategy inputs must be identical")
    if strategy_inputs.get("ground_truth_labels_excluded_from_all_strategy_inputs") is not True:
        failures.append("ground truth labels must be excluded from all strategy inputs")
    if strategy_inputs.get("private_label_paths_excluded_from_all_strategy_inputs") is not True:
        failures.append("private label paths must be excluded from all strategy inputs")
    expected_public_hashes = {
        blind: {
            artifact["path"]: artifact["sha256"]
            for artifact in selected_by_packet.get(blind, {}).get("public_artifacts", [])
        }
        for blind in selected_by_packet
    }
    for strategy in strategy_inputs.get("strategy_manifests", []):
        strategy_id = strategy.get("strategy_id")
        if strategy.get("packet_count") != PACKET_COUNT:
            failures.append(f"{strategy_id} packet input count mismatch")
        if strategy.get("identical_public_artifact_packets") is not True:
            failures.append(f"{strategy_id} must use identical packets")
        if strategy.get("ground_truth_labels_excluded") is not True:
            failures.append(f"{strategy_id} must exclude labels")
        if strategy.get("strategy_execution_in_this_gate") != 0:
            failures.append(f"{strategy_id} must not execute in iter106")
        for packet_input in strategy.get("packet_inputs", []):
            blind = str(packet_input.get("blinded_packet_id"))
            expected_hashes = expected_public_hashes.get(blind)
            if expected_hashes is None:
                failures.append(f"{strategy_id} unknown packet id {blind}")
                continue
            if packet_input.get("public_artifact_hashes") != expected_hashes:
                failures.append(f"{strategy_id} public hashes changed for {blind}")
            if packet_input.get("public_artifact_paths") != list(expected_hashes):
                failures.append(f"{strategy_id} public paths changed for {blind}")
            for key in [
                "private_label_included",
                "private_label_path_included",
                "private_rationale_included",
                "ground_truth_completed_included",
                "case_kind_included",
            ]:
                if packet_input.get(key) is not False:
                    failures.append(f"{strategy_id} {key} leaked for {blind}")
            for path in packet_input.get("public_artifact_paths", []):
                if "/private/" in str(path) or "ground_truth_label" in str(path):
                    failures.append(f"{strategy_id} private label path leaked for {blind}")


def audit_claim_boundary(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = packets["summary"]
    boundary = packets["boundary"]
    false_keys = [
        "external_benchmark_result_claimed",
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "swebench_execution_or_score_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "all_strategy_superiority_claimed",
        "comparative_performance_claimed",
        "production_or_live_domain_changed",
    ]
    for key in false_keys:
        if summary.get(key) is not False:
            failures.append(f"summary {key} must be false")
        if boundary.get(key) is not False:
            failures.append(f"claim boundary {key} must be false")
    for key in [
        "benchmark_task_execution_completed",
        "strategy_execution_completed",
        "provider_execution_completed",
        "future_paid_execution_authorized_by_iter106",
    ]:
        if boundary.get(key) is not False:
            failures.append(f"claim boundary {key} must be false")
    if boundary.get("external_benchmark_pilot_materialization_claimed") is not True:
        failures.append("materialization claim should be true")


def audit_receipt_text_hashes_and_secrets(summary: dict[str, Any], failures: list[str]) -> None:
    try:
        receipt = load_receipt(RECEIPT)
    except ProofValidationError as exc:
        failures.append(f"gate receipt invalid: {exc}")
        return
    if receipt.status != summary.get("status"):
        failures.append("gate receipt status mismatch")
    result = RESULT.read_text(encoding="utf-8")
    review = (PROOF / "materialization_review.md").read_text(encoding="utf-8")
    command_output = (PROOF / "command_output.txt").read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`.",
        "materialized packet count: `20`",
        "false-completion packet labels: `10`",
        "legitimate-control packet labels: `10`",
        "materialized public artifact count: `160`",
        "labels excluded from strategy inputs: `true`",
        "benchmark/task execution in this gate: `0`",
        "external benchmark result claim: `false`",
        "It is not a benchmark",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "No strategy executed.",
        "No benchmark/task execution occurred.",
        "Private labels and label rationales are committed for later",
        "scoring but excluded from every strategy input.",
        "This is not a benchmark result",
    ]:
        if required not in review:
            failures.append(f"materialization_review.md missing required text: {required}")
    for required in [
        "external benchmark pilot materialization: pass",
        "materialized_packet_count=20",
        "false_completion_packet_count=10",
        "legitimate_control_packet_count=10",
        "materialized_public_artifact_count=160",
        "strategy_input_manifest_count=5",
        "labels_excluded_from_strategy_inputs=true",
        "benchmark_task_execution_in_this_gate=0",
        "external_benchmark_result_claimed=false",
        "comparative_performance_claimed=false",
    ]:
        if required not in command_output:
            failures.append(f"command_output.txt missing required text: {required}")
    for pattern in FORBIDDEN_CLAIM_PATTERNS:
        for path, text in [
            (RESULT, result),
            (PROOF / "materialization_review.md", review),
            (PROOF / "review.md", (PROOF / "review.md").read_text(encoding="utf-8")),
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
            "selected": load_json(SELECTED),
            "public_hashes": load_json(PUBLIC_HASHES),
            "private_labels": load_json(PRIVATE_LABELS),
            "strategy_inputs": load_json(STRATEGY_INPUTS),
            "report": load_json(REPORT),
            "boundary": load_json(CLAIM_BOUNDARY),
            "redaction": load_json(REDACTION),
        }
        audit_schemas(packets, failures)
        audit_status_and_zero_execution(packets, failures)
        audit_iter105_prerequisite(packets, failures)
        audit_packet_materialization(packets, failures)
        audit_claim_boundary(packets, failures)
        audit_receipt_text_hashes_and_secrets(packets["summary"], failures)
    if failures:
        print("iter106 external benchmark pilot materialization audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter106 external benchmark pilot materialization audit: pass")
    print("packet_count=20")
    print("false_completion_packet_count=10")
    print("legitimate_control_packet_count=10")
    print("public_artifact_count=160")
    print("strategy_execution_in_iter106=0")
    print("provider_spend_in_iter106_usd=0.00000000")
    print(f"next_gate={NEXT_GATE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
