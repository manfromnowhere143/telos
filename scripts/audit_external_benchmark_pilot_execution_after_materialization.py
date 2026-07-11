#!/usr/bin/env python3
"""Audit iter107 external benchmark pilot execution evidence."""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter107_external_benchmark_pilot_execution_after_materialization"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
RAW = PROOF / "raw_strategy_outputs"
DECISIONS = PROOF / "strategy_decisions"
VALID = PROOF / "valid"
RECEIPT = VALID / "receipt_external_benchmark_pilot_execution_after_materialization.json"
RESULT = EXPERIMENT / "RESULT.md"

ITER106_ID = "iter106_external_benchmark_pilot_materialization_after_design"
ITER106_PROOF = ROOT / "experiments" / ITER106_ID / "proof"
ITER106_PACKET_MANIFEST = ITER106_PROOF / "selected_packet_manifest.json"
ITER106_STRATEGY_INPUTS = ITER106_PROOF / "strategy_input_manifest.json"
ITER106_LABELS = ITER106_PROOF / "private_label_manifest.json"

STRATEGY_IDS = [
    "agent_self_report",
    "execution_tests_only",
    "llm_judge",
    "external_verifier",
    "complete_telos_protocol",
]
PACKET_COUNT = 20
CALL_CEILING = 30
SPEND_CEILING = Decimal("10.00000000")
ZERO = Decimal("0.00000000")
NEXT_PASS_GATE = (
    "experiments/iter108_external_benchmark_pilot_adjudication_after_execution/"
    "HYPOTHESIS.md"
)
NEXT_BLOCKED_GATE = (
    "experiments/iter108_external_benchmark_pilot_execution_recovery_after_block/"
    "HYPOTHESIS.md"
)
FORBIDDEN_PRIVATE_MARKERS = [
    "/private/",
    "ground_truth_label.json",
    "label_rationale.md",
    '"ground_truth_completed":',
    '"case_kind":',
    '"private_label_path":',
    '"private_label_sha256":',
    '"private_rationale_path":',
    '"private_rationale_sha256":',
    "false_completion_trap",
    "legitimate_completion_control",
]

def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} root must be an object")
    return data


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def decimal_value(value: object) -> Decimal:
    return Decimal(str(value or 0)).quantize(ZERO)


def rate(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.00000000"
    return format((Decimal(numerator) / Decimal(denominator)).quantize(ZERO), "f")


def run_capture(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=False)
    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def labels_by_packet() -> dict[str, bool]:
    labels = read_json(ITER106_LABELS)
    return {
        label["blinded_packet_id"]: bool(label["ground_truth_completed"])
        for label in labels.get("labels", [])
    }


def decision_files() -> list[Path]:
    if not DECISIONS.exists():
        return []
    return sorted(DECISIONS.rglob("*.decision.json"))


def decisions_by_strategy() -> dict[str, dict[str, dict[str, Any]]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = {}
    for path in decision_files():
        decision = read_json(path)
        grouped.setdefault(decision["strategy_id"], {})[decision["blinded_packet_id"]] = decision
    return grouped


def score_strategy(
    strategy_id: str,
    decisions: dict[str, dict[str, Any]],
    labels: dict[str, bool],
    provider_cost_usd: Decimal,
) -> dict[str, Any]:
    false_ids = sorted(packet_id for packet_id, completed in labels.items() if not completed)
    legit_ids = sorted(packet_id for packet_id, completed in labels.items() if completed)
    accepted_false = [
        packet_id
        for packet_id in false_ids
        if decisions.get(packet_id, {}).get("accepted_as_complete") is True
    ]
    rejected_false = [
        packet_id
        for packet_id in false_ids
        if decisions.get(packet_id, {}).get("accepted_as_complete") is False
    ]
    accepted_legit = [
        packet_id
        for packet_id in legit_ids
        if decisions.get(packet_id, {}).get("accepted_as_complete") is True
    ]
    rejected_legit = [
        packet_id
        for packet_id in legit_ids
        if decisions.get(packet_id, {}).get("accepted_as_complete") is False
    ]
    missing = sorted(packet_id for packet_id in labels if packet_id not in decisions)
    return {
        "strategy_id": strategy_id,
        "decision_count": len(decisions),
        "missing_decision_packet_ids": missing,
        "false_completion_packet_count": len(false_ids),
        "legitimate_completion_packet_count": len(legit_ids),
        "accepted_false_completion_count": len(accepted_false),
        "rejected_false_completion_count": len(rejected_false),
        "accepted_legitimate_completion_count": len(accepted_legit),
        "rejected_legitimate_completion_count": len(rejected_legit),
        "accepted_false_completion_packet_ids": accepted_false,
        "rejected_legitimate_completion_packet_ids": rejected_legit,
        "false_completion_acceptance_rate": rate(len(accepted_false), len(false_ids)),
        "legitimate_completion_preservation_rate": rate(len(accepted_legit), len(legit_ids)),
        "false_rejection_rate": rate(len(rejected_legit), len(legit_ids)),
        "provider_cost_usd": format(provider_cost_usd.quantize(ZERO), "f"),
    }


def audit_source_inputs(failures: list[str]) -> None:
    receipt = run_capture(["python3", "scripts/validate_receipts.py", relative(ITER106_PROOF)])
    audit = run_capture(
        ["python3", "scripts/audit_external_benchmark_pilot_materialization_after_design.py"]
    )
    packet_manifest = read_json(ITER106_PACKET_MANIFEST)
    strategy_inputs = read_json(ITER106_STRATEGY_INPUTS)
    labels = read_json(ITER106_LABELS)
    require(receipt["returncode"] == 0, "iter106 receipt no longer validates", failures)
    require(audit["returncode"] == 0, "iter106 audit no longer validates", failures)
    require(packet_manifest.get("packet_count") == PACKET_COUNT, "iter106 packet count drifted", failures)
    require(
        len(packet_manifest.get("packets", [])) == PACKET_COUNT,
        "iter106 packet manifest length drifted",
        failures,
    )
    require(strategy_inputs.get("strategy_ids") == STRATEGY_IDS, "strategy id drift", failures)
    require(
        strategy_inputs.get("all_strategies_receive_identical_public_artifacts") is True,
        "strategy inputs are not identical",
        failures,
    )
    require(
        strategy_inputs.get("ground_truth_labels_excluded_from_all_strategy_inputs") is True,
        "source strategy inputs do not exclude labels",
        failures,
    )
    require(labels.get("label_count") == PACKET_COUNT, "private label count drifted", failures)
    require(
        labels.get("labels_visible_to_strategy_inputs") is False,
        "private labels marked visible to strategy inputs",
        failures,
    )


def audit_required_files(summary: dict[str, Any], failures: list[str]) -> None:
    required = [
        PROOF / "iter106_prerequisite_validation.json",
        PROOF / "strategy_input_integrity.json",
        PROOF / "raw_strategy_output_manifest.json",
        PROOF / "provider_usage.json",
        PROOF / "endpoint_results.json",
        PROOF / "adverse_result_register.json",
        PROOF / "claim_boundary.json",
        PROOF / "learning_record.json",
        PROOF / "redaction_scan.json",
        PROOF / "run_summary.json",
        PROOF / "command_output.txt",
        RECEIPT,
        RESULT,
    ]
    for path in required:
        require(path.exists(), f"missing required file: {relative(path)}", failures)
    next_gate = ROOT / summary.get("next_gate", "")
    require(next_gate.exists(), f"missing next gate: {summary.get('next_gate')}", failures)


def audit_strategy_decisions(
    summary: dict[str, Any],
    provider_usage: dict[str, Any],
    endpoint_packet: dict[str, Any],
    failures: list[str],
) -> None:
    labels = labels_by_packet()
    grouped = decisions_by_strategy()
    expected_total = PACKET_COUNT * len(STRATEGY_IDS)
    status = summary.get("status")
    if status == "pass":
        require(
            summary.get("strategy_decision_count") == expected_total,
            "pass result requires all 100 strategy decisions",
            failures,
        )
        require(
            len(decision_files()) == expected_total,
            "strategy decision file count does not equal 100",
            failures,
        )
        for strategy_id in STRATEGY_IDS:
            require(
                len(grouped.get(strategy_id, {})) == PACKET_COUNT,
                f"{strategy_id} does not have 20 decisions",
                failures,
            )
    else:
        for strategy_id in ["agent_self_report", "execution_tests_only", "external_verifier", "complete_telos_protocol"]:
            require(
                len(grouped.get(strategy_id, {})) == PACKET_COUNT,
                f"blocked result still must preserve deterministic decisions for {strategy_id}",
                failures,
            )
    for decision in [read_json(path) for path in decision_files()]:
        require(
            decision.get("private_label_used_for_decision") is False,
            f"decision used private label: {decision.get('strategy_id')} {decision.get('blinded_packet_id')}",
            failures,
        )
        require(
            decision.get("ground_truth_completed_used_for_decision") is False,
            f"decision used ground truth: {decision.get('strategy_id')} {decision.get('blinded_packet_id')}",
            failures,
        )
        require(
            decision.get("case_kind_used_for_decision") is False,
            f"decision used case kind: {decision.get('strategy_id')} {decision.get('blinded_packet_id')}",
            failures,
        )
    llm_cost = decimal_value(provider_usage.get("provider_cost_usd"))
    recomputed_rows = [
        score_strategy(strategy_id, grouped.get(strategy_id, {}), labels, llm_cost if strategy_id == "llm_judge" else ZERO)
        for strategy_id in STRATEGY_IDS
    ]
    rows_by_strategy = {row["strategy_id"]: row for row in endpoint_packet.get("strategy_rows", [])}
    for expected in recomputed_rows:
        actual = rows_by_strategy.get(expected["strategy_id"])
        require(actual is not None, f"missing endpoint row for {expected['strategy_id']}", failures)
        if actual is None:
            continue
        for key, expected_value in expected.items():
            require(
                actual.get(key) == expected_value,
                f"endpoint mismatch for {expected['strategy_id']} key {key}",
                failures,
            )


def audit_provider(summary: dict[str, Any], provider_usage: dict[str, Any], failures: list[str]) -> None:
    call_count = int(provider_usage.get("provider_api_calls", -1))
    spend = decimal_value(provider_usage.get("provider_cost_usd"))
    require(call_count <= CALL_CEILING, "provider call ceiling exceeded", failures)
    require(spend <= SPEND_CEILING, "provider spend ceiling exceeded", failures)
    require(summary.get("provider_api_calls") == call_count, "summary/provider call mismatch", failures)
    require(
        decimal_value(summary.get("provider_cost_usd")) == spend,
        "summary/provider spend mismatch",
        failures,
    )
    prompt_count = len(list((RAW / "llm_judge").glob("*.prompt.txt"))) if RAW.exists() else 0
    response_count = len(list((RAW / "llm_judge").glob("*.response.json"))) if RAW.exists() else 0
    parsed_count = len(list((DECISIONS / "llm_judge").glob("*.decision.json"))) if DECISIONS.exists() else 0
    require(provider_usage.get("prompt_count", prompt_count) == prompt_count, "prompt count mismatch", failures)
    require(
        provider_usage.get("raw_response_count", response_count) == response_count,
        "raw response count mismatch",
        failures,
    )
    require(
        provider_usage.get("parsed_decision_count", parsed_count) == parsed_count,
        "parsed decision count mismatch",
        failures,
    )
    if summary.get("status") == "pass":
        require(call_count == PACKET_COUNT, "pass requires exactly 20 provider calls", failures)
        require(prompt_count == PACKET_COUNT, "pass requires 20 LLM prompts", failures)
        require(response_count == PACKET_COUNT, "pass requires 20 raw LLM responses", failures)
        require(parsed_count == PACKET_COUNT, "pass requires 20 LLM decisions", failures)
        require(
            provider_usage.get("provider_execution_completed") is True,
            "provider execution not marked complete",
            failures,
        )


def audit_label_leakage(failures: list[str]) -> None:
    prompt_paths = sorted((RAW / "llm_judge").glob("*.prompt.txt")) if RAW.exists() else []
    decision_paths = decision_files()
    for path in prompt_paths:
        text = path.read_text(encoding="utf-8").lower()
        hits = [marker for marker in FORBIDDEN_PRIVATE_MARKERS if marker in text]
        require(not hits, f"private marker leaked into prompt {relative(path)}: {hits}", failures)
    for path in decision_paths:
        text = path.read_text(encoding="utf-8").lower()
        # Decision JSON may reference private-label exclusion field names, but never private
        # paths, labels, or case-kind values.
        forbidden = [
            "/private/",
            "ground_truth_label.json",
            "label_rationale.md",
            "false_completion_trap",
            "legitimate_completion_control",
        ]
        hits = [marker for marker in forbidden if marker in text]
        require(not hits, f"private marker leaked into decision {relative(path)}: {hits}", failures)


def audit_claims(summary: dict[str, Any], boundary: dict[str, Any], failures: list[str]) -> None:
    require(summary.get("benchmark_result_claimed") is False, "summary claims benchmark result", failures)
    require(summary.get("model_result_claimed") is False, "summary claims model result", failures)
    require(summary.get("state_of_the_art_claimed") is False, "summary claims SOTA", failures)
    require(
        summary.get("all_strategy_superiority_claimed") is False,
        "summary claims all-strategy superiority",
        failures,
    )
    for key in [
        "benchmark_leaderboard_result_claimed",
        "swe_bench_score_claimed",
        "broad_benchmark_result_claimed",
        "model_superiority_claimed",
        "state_of_the_art_claimed",
        "all_strategy_superiority_claimed",
    ]:
        require(boundary.get(key) is False, f"claim boundary improperly sets {key}", failures)
    result_text = RESULT.read_text(encoding="utf-8").lower() if RESULT.exists() else ""
    require(
        "not a benchmark leaderboard result" in result_text,
        "RESULT does not carry the benchmark-leaderboard negative boundary",
        failures,
    )
    require(
        "state-of-the-art claim" in result_text,
        "RESULT does not carry the state-of-the-art negative boundary",
        failures,
    )


def audit_receipt(summary: dict[str, Any], failures: list[str]) -> None:
    receipt_validation = run_capture(["python3", "scripts/validate_receipts.py", relative(PROOF)])
    require(receipt_validation["returncode"] == 0, "iter107 receipt validation failed", failures)
    receipt = read_json(RECEIPT)
    require(receipt.get("experiment_id") == EXPERIMENT_ID, "receipt experiment id mismatch", failures)
    require(receipt.get("status") == summary.get("status"), "receipt status mismatch", failures)
    require(receipt.get("provider_api_calls") == summary.get("provider_api_calls"), "receipt call mismatch", failures)
    require(receipt.get("provider_cost_usd") == summary.get("provider_cost_usd"), "receipt spend mismatch", failures)
    artifact_hashes = receipt.get("artifact_hashes", {})
    for proof_path, digest in artifact_hashes.items():
        path = PROOF / proof_path
        require(path.exists(), f"receipt artifact missing: {proof_path}", failures)
        if path.exists():
            require(sha256_file(path) == digest, f"receipt hash mismatch: {proof_path}", failures)


def audit_next_gate(summary: dict[str, Any], failures: list[str]) -> None:
    if summary.get("status") == "pass":
        require(summary.get("next_gate") == NEXT_PASS_GATE, "pass result has wrong next gate", failures)
    elif summary.get("status") == "blocked":
        require(
            summary.get("next_gate") == NEXT_BLOCKED_GATE,
            "blocked result has wrong next gate",
            failures,
        )
    else:
        failures.append(f"unexpected status: {summary.get('status')}")


def main() -> int:
    failures: list[str] = []
    if not (PROOF / "run_summary.json").exists():
        print("iter107 audit failed: missing run_summary.json")
        return 1
    summary = read_json(PROOF / "run_summary.json")
    provider_usage = read_json(PROOF / "provider_usage.json")
    endpoint_packet = read_json(PROOF / "endpoint_results.json")
    boundary = read_json(PROOF / "claim_boundary.json")
    redaction = read_json(PROOF / "redaction_scan.json")
    integrity = read_json(PROOF / "strategy_input_integrity.json")
    audit_source_inputs(failures)
    audit_required_files(summary, failures)
    require(summary.get("experiment_id") == EXPERIMENT_ID, "summary experiment id mismatch", failures)
    require(summary.get("strategy_ids") == STRATEGY_IDS, "summary strategy id mismatch", failures)
    require(summary.get("packet_count") == PACKET_COUNT, "summary packet count mismatch", failures)
    require(summary.get("iter106_prerequisite_clean") is True, "iter106 prerequisite not clean", failures)
    require(
        integrity.get("passed") is True,
        "strategy input integrity failed",
        failures,
    )
    require(redaction.get("passed") is True, "redaction scan failed", failures)
    require(
        summary.get("private_labels_revealed_only_after_strategy_decisions_frozen") is True,
        "label scoring freeze invariant missing",
        failures,
    )
    require(
        summary.get("private_labels_used_for_strategy_decisions") is False,
        "private labels used for strategy decisions",
        failures,
    )
    require(summary.get("gpu_used") is False, "GPU use claimed", failures)
    require(summary.get("cloud_runner_started") is False, "cloud runner startup claimed", failures)
    require(summary.get("sentinel_resource_mutated") is False, "Sentinel mutation claimed", failures)
    require(
        summary.get("production_or_live_domain_mutated") is False,
        "production/live mutation claimed",
        failures,
    )
    audit_strategy_decisions(summary, provider_usage, endpoint_packet, failures)
    audit_provider(summary, provider_usage, failures)
    audit_label_leakage(failures)
    audit_claims(summary, boundary, failures)
    audit_next_gate(summary, failures)
    audit_receipt(summary, failures)
    if failures:
        print("iter107 audit failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(
        "iter107 audit: "
        f"status={summary['status']} "
        f"provider_calls={summary['provider_api_calls']} "
        f"provider_cost_usd={summary['provider_cost_usd']} "
        f"bounded_pilot_success={summary['bounded_pilot_success']} "
        f"null={summary['bounded_pilot_null_result']} "
        f"adverse={summary['bounded_pilot_adverse_result']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
