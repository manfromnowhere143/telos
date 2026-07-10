#!/usr/bin/env python3
"""Audit iter88 external benchmark readiness adjudication artifacts."""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path(
    "experiments/iter88_external_benchmark_readiness_adjudication_after_discriminating_pilot"
)
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
PREREQ = PROOF / "iter87_prerequisite_validation.json"
LOCKED = PROOF / "locked_iter87_summary.json"
ADJUDICATION = PROOF / "mixed_direction_adjudication.json"
DECISION = PROOF / "next_step_decision.json"
REPLICATION = PROOF / "replication_design.json"
SCALE_REJECTION = PROOF / "scale_rejection.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary.json"
REDACTION = PROOF / "redaction_scan.json"
RECEIPT = (
    PROOF / "valid" / "receipt_external_benchmark_readiness_adjudication_after_discriminating_pilot.json"
)
NEXT_GATE = Path("experiments/iter89_same_slice_discriminating_metric_stability_replication/HYPOTHESIS.md")

ITER87_PROOF = Path("experiments/iter87_benchmark_facing_discriminating_metric_execution_pilot/proof")
ITER87_SUMMARY = ITER87_PROOF / "run_summary.json"
ITER87_EXTRACTION = ITER87_PROOF / "fresh_metric_extraction.json"
ITER87_EXECUTION = ITER87_PROOF / "execution_accounting_report.json"
ITER87_RECEIPT = (
    ITER87_PROOF / "valid" / "receipt_benchmark_facing_discriminating_metric_execution_pilot.json"
)
METRIC_ID = "task_native_score_share_delta_with_receipt_gates"
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
FORBIDDEN_CLAIM_PATTERNS = [
    re.compile(r"benchmark_result_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"model_superiority_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"state_of_the_art_result_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"benchmark/model/SOTA claim:\s*`true`", re.IGNORECASE),
    re.compile(r"\bSOTA achieved\b", re.IGNORECASE),
    re.compile(r"\bstate-of-the-art achieved\b", re.IGNORECASE),
    re.compile(r"\bmodel superiority achieved\b", re.IGNORECASE),
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
        LOCKED,
        ADJUDICATION,
        DECISION,
        REPLICATION,
        SCALE_REJECTION,
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
        "summary": "telos.external_benchmark_readiness_adjudication.summary.v1",
        "prereq": "telos.external_benchmark_readiness_adjudication.iter87_prerequisite_validation.v1",
        "locked": "telos.external_benchmark_readiness_adjudication.locked_iter87_summary.v1",
        "adjudication": "telos.external_benchmark_readiness_adjudication.mixed_direction_adjudication.v1",
        "decision": "telos.external_benchmark_readiness_adjudication.next_step_decision.v1",
        "replication": "telos.external_benchmark_readiness_adjudication.replication_design.v1",
        "scale": "telos.external_benchmark_readiness_adjudication.scale_rejection.v1",
        "boundary": "telos.external_benchmark_readiness_adjudication.claim_boundary.v1",
        "redaction": "telos.external_benchmark_readiness_adjudication.redaction_scan.v1",
    }
    for name, schema in expected.items():
        packet = packets[name]
        if packet.get("schema_version") != schema:
            failures.append(f"unexpected {name} schema")
        if packet.get("experiment_id") != EXPERIMENT.name:
            failures.append(f"{name} experiment id mismatch")


def audit_status_and_zero_spend(packets: dict[str, dict], failures: list[str]) -> None:
    summary = packets["summary"]
    prereq = packets["prereq"]
    adjudication = packets["adjudication"]
    decision = packets["decision"]
    replication = packets["replication"]
    scale = packets["scale"]
    redaction = packets["redaction"]
    if summary.get("status") != "pass":
        failures.append("iter88 summary must pass")
    if summary.get("clean_pass") is not True:
        failures.append("summary clean_pass must be true")
    if summary.get("blocked_result") is not False or summary.get("quality_failure") is not False:
        failures.append("summary blocked/quality flags must be false")
    if summary.get("blockers") != [] or summary.get("failures") != []:
        failures.append("pass summary must not contain blockers/failures")
    for packet_name, packet in [
        ("summary", summary),
        ("prereq", prereq),
        ("adjudication", adjudication),
        ("decision", decision),
        ("replication", replication),
        ("scale", scale),
    ]:
        call_value = packet.get("provider_api_calls", packet.get("provider_calls_in_this_gate", 0))
        spend_value = packet.get(
            "provider_cost_usd",
            packet.get(
                "provider_spend_in_this_gate_usd",
                packet.get("provider_spend_in_iter88_usd", 0),
            ),
        )
        row_value = packet.get("row_execution_in_this_gate", packet.get("row_execution_in_iter88", 0))
        if call_value != 0:
            failures.append(f"{packet_name} provider calls must be zero")
        if decimal_value(spend_value) != Decimal("0.00000000"):
            failures.append(f"{packet_name} provider spend must be zero")
        if row_value != 0:
            failures.append(f"{packet_name} row execution must be zero")
    for key in ["gpu_used", "cloud_runner_started", "sentinel_named_resources_modified"]:
        if summary.get(key) is not False:
            failures.append(f"summary {key} must be false")
    if redaction.get("passed") is not True or redaction.get("findings") != []:
        failures.append("redaction scan must pass with no findings")
    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("summary redaction scan must pass")


def audit_iter87_lock(packets: dict[str, dict], failures: list[str]) -> None:
    prereq = packets["prereq"]
    locked = packets["locked"]
    summary = packets["summary"]
    if prereq.get("clean_prerequisites") is not True:
        failures.append("iter87 prerequisites must be clean")
    if prereq.get("iter87_status") != "pass" or prereq.get("iter87_clean_pass") is not True:
        failures.append("iter87 must remain a clean pass")
    if prereq.get("iter87_receipt_validation_returncode") != 0:
        failures.append("iter87 receipt validation must pass")
    if prereq.get("iter87_audit_returncode") != 0:
        failures.append("iter87 audit must pass")
    if prereq.get("iter87_selected_pair_ids") != SELECTED_PAIR_IDS:
        failures.append("iter87 prerequisite selected pair ids changed")
    if locked.get("selected_pair_ids") != SELECTED_PAIR_IDS:
        failures.append("locked selected pair ids changed")
    if locked.get("executed_pair_ids") != SELECTED_PAIR_IDS:
        failures.append("locked executed pair ids changed")
    if locked.get("executed_pair_count") != 6 or summary.get("iter87_executed_pair_count") != 6:
        failures.append("iter87 executed row count must be six")
    if locked.get("provider_api_calls") != 21 or summary.get("iter87_provider_api_calls") != 21:
        failures.append("iter87 provider call count changed")
    if decimal_value(locked.get("provider_cost_usd")) != Decimal("0.12498400"):
        failures.append("iter87 provider cost changed")
    if locked.get("metric_id") != METRIC_ID or summary.get("metric_id") != METRIC_ID:
        failures.append("metric id changed")
    if (
        locked.get("metric_non_saturated") is not True
        or summary.get("iter87_metric_non_saturated") is not True
    ):
        failures.append("iter87 metric must remain non-saturated")
    if (
        locked.get("mixed_direction_signal") is not True
        or summary.get("iter87_mixed_direction_signal") is not True
    ):
        failures.append("iter87 mixed-direction signal must remain true")
    if locked.get("receipt_required_rows_valid") is not True:
        failures.append("iter87 receipt-required rows must remain valid")

    by_path = {item.get("path"): item for item in prereq.get("source_artifacts", [])}
    expected_hashes = {
        str(ITER87_SUMMARY): sha256(ITER87_SUMMARY),
        str(ITER87_EXTRACTION): sha256(ITER87_EXTRACTION),
        str(ITER87_EXECUTION): sha256(ITER87_EXECUTION),
        str(ITER87_RECEIPT): sha256(ITER87_RECEIPT),
    }
    for path, expected_hash in expected_hashes.items():
        if by_path.get(path, {}).get("sha256") != expected_hash:
            failures.append(f"iter87 source hash mismatch: {path}")
    for field, path in [
        ("source_summary_sha256", ITER87_SUMMARY),
        ("source_extraction_sha256", ITER87_EXTRACTION),
        ("source_execution_accounting_sha256", ITER87_EXECUTION),
    ]:
        if locked.get(field) != sha256(path):
            failures.append(f"locked iter87 hash mismatch: {field}")


def audit_adjudication_and_decision(packets: dict[str, dict], failures: list[str]) -> None:
    summary = packets["summary"]
    adjudication = packets["adjudication"]
    decision = packets["decision"]
    replication = packets["replication"]
    scale = packets["scale"]
    rows = adjudication.get("task_comparisons", [])
    if len(rows) != 3 or adjudication.get("task_count") != 3:
        failures.append("adjudication must compare three task surfaces")
    if adjudication.get("sign_flip_count") != 3 or summary.get("sign_flip_count") != 3:
        failures.append("iter86/iter87 sign flip count must be three")
    if adjudication.get("same_direction_count") != 0 or summary.get("same_direction_count") != 0:
        failures.append("same-direction count must be zero")
    if any(row.get("direction_stable") is not False for row in rows):
        failures.append("all three task directions must be unstable")
    if adjudication.get("direction_stability_classification") != "unstable_mixed_direction_single_pilot":
        failures.append("direction stability classification changed")
    if summary.get("direction_stability_classification") != "unstable_mixed_direction_single_pilot":
        failures.append("summary direction stability classification changed")
    if adjudication.get("scale_to_external_benchmark_now_supported") is not False:
        failures.append("adjudication must reject scale-to-benchmark now")
    if summary.get("scale_to_external_benchmark_now_supported") is not False:
        failures.append("summary must reject scale-to-benchmark now")
    if adjudication.get("same_slice_replication_supported") is not True:
        failures.append("adjudication must support same-slice replication")
    if summary.get("same_slice_replication_supported") is not True:
        failures.append("summary must support same-slice replication")

    if decision.get("decision") != "replicate_same_slice":
        failures.append("next decision must be replicate_same_slice")
    if summary.get("next_step_decision") != "replicate_same_slice":
        failures.append("summary next decision changed")
    if decision.get("next_gate") != str(NEXT_GATE) or summary.get("next_gate") != str(NEXT_GATE):
        failures.append("next gate changed")
    if (
        decision.get("next_gate_pre_registered") is not True
        or summary.get("next_gate_pre_registered") is not True
    ):
        failures.append("next gate must be pre-registered")
    if not NEXT_GATE.exists():
        failures.append("next gate hypothesis missing")
    accepted = decision.get("accepted_path", {})
    if accepted.get("selected_row_count") != 6:
        failures.append("accepted replication row count must be six")
    if accepted.get("future_provider_call_ceiling") != 96:
        failures.append("accepted replication call ceiling changed")
    if decimal_value(accepted.get("future_provider_spend_ceiling_usd")) != Decimal("10.00000000"):
        failures.append("accepted replication spend ceiling changed")
    if accepted.get("future_per_row_call_limit") != 16:
        failures.append("accepted per-row call limit changed")
    if decimal_value(accepted.get("future_per_row_spend_limit_usd")) != Decimal("2.00000000"):
        failures.append("accepted per-row spend limit changed")
    rejected_kinds = {row.get("kind") for row in decision.get("rejected_paths", [])}
    if "scale_to_external_benchmark_design" not in rejected_kinds:
        failures.append("decision must explicitly reject external benchmark design now")

    if replication.get("selected_pair_ids") != SELECTED_PAIR_IDS:
        failures.append("replication design selected rows changed")
    if replication.get("provider_call_ceiling") != 96 or summary.get("future_provider_call_ceiling") != 96:
        failures.append("replication call ceiling changed")
    if decimal_value(replication.get("provider_spend_ceiling_usd")) != Decimal("10.00000000"):
        failures.append("replication spend ceiling changed")
    if replication.get("per_row_call_limit") != 16:
        failures.append("replication per-row call limit changed")
    if decimal_value(replication.get("per_row_spend_limit_usd")) != Decimal("2.00000000"):
        failures.append("replication per-row spend limit changed")
    if replication.get("benchmark_execution_authorized_by_iter88") is not False:
        failures.append("iter88 must not authorize benchmark execution")
    if scale.get("precise_blocker") != "task_direction_instability_across_iter86_iter87":
        failures.append("scale rejection blocker changed")
    if scale.get("scale_to_external_benchmark_design_now") is not False:
        failures.append("scale rejection must defer benchmark design now")


def audit_claim_boundary(packets: dict[str, dict], failures: list[str]) -> None:
    summary = packets["summary"]
    boundary = packets["boundary"]
    false_keys = [
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "swebench_execution_or_score_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "production_or_live_domain_changed",
    ]
    for key in false_keys:
        if boundary.get(key) is not False:
            failures.append(f"claim boundary {key} must be false")
        if summary.get(key) is not False:
            failures.append(f"summary {key} must be false")
    for key in [
        "cross_task_surface_pooling_authorized",
        "aggregate_benchmark_metric_authorized",
        "fresh_paid_execution_claimed",
    ]:
        if boundary.get(key) is not False:
            failures.append(f"claim boundary {key} must be false")


def audit_receipt_text_hashes_and_secrets(packets: dict[str, dict], failures: list[str]) -> None:
    summary = packets["summary"]
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
        "provider calls in this gate: `0`",
        "provider spend in this gate: `$0.00000000`",
        "row execution in this gate: `0`",
        "iter86/iter87 sign flips: `3`",
        "direction stability classification: `unstable_mixed_direction_single_pilot`",
        "next-step decision: `replicate_same_slice`",
        "benchmark/model/SOTA claim: `false`",
        "It is not a benchmark result",
        "state-of-the-art result",
    ]:
        if required not in result:
            failures.append(f"result missing required text: {required}")
    for required in [
        "No benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or",
        "state-of-the-art result is claimed.",
        "next_step_decision=replicate_same_slice",
        "provider_calls_in_this_gate=0",
    ]:
        haystack = review if required.startswith("No benchmark") or "claimed" in required else command_output
        if required not in haystack:
            failures.append(f"text artifact missing required text: {required}")
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


def main() -> int:
    failures: list[str] = []
    audit_required_files(failures)
    if failures:
        for failure in failures:
            print(f"iter88 external benchmark readiness audit failure: {failure}")
        return 1
    packets = {
        "summary": load_json(SUMMARY),
        "prereq": load_json(PREREQ),
        "locked": load_json(LOCKED),
        "adjudication": load_json(ADJUDICATION),
        "decision": load_json(DECISION),
        "replication": load_json(REPLICATION),
        "scale": load_json(SCALE_REJECTION),
        "boundary": load_json(CLAIM_BOUNDARY),
        "redaction": load_json(REDACTION),
    }
    audit_schemas(packets, failures)
    audit_status_and_zero_spend(packets, failures)
    audit_iter87_lock(packets, failures)
    audit_adjudication_and_decision(packets, failures)
    audit_claim_boundary(packets, failures)
    audit_receipt_text_hashes_and_secrets(packets, failures)
    if failures:
        for failure in failures:
            print(f"iter88 external benchmark readiness audit failure: {failure}")
        return 1
    print("iter88 external benchmark readiness audit: pass")
    print("decision=replicate_same_slice")
    print("sign_flip_count=3")
    print("provider_calls_in_iter88=0")
    print("provider_spend_in_iter88_usd=0.00000000")
    print(f"next_gate={NEXT_GATE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
