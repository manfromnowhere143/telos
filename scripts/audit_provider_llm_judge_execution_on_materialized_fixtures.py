#!/usr/bin/env python3
"""Audit iter94 provider LLM-judge execution artifacts."""

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
EXPERIMENT = Path("experiments/iter94_provider_llm_judge_execution_on_materialized_fixtures")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
PREREQ = PROOF / "iter93_prerequisite_validation.json"
MODEL_BINDING = PROOF / "model_binding.json"
PROMPT_TEMPLATE = PROOF / "judge_prompt_template.md"
DECISION_MANIFEST = PROOF / "decision_manifest.json"
PROVIDER_USAGE = PROOF / "provider_usage.json"
ENDPOINTS = PROOF / "endpoint_results.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary.json"
REDACTION = PROOF / "redaction_scan.json"
RECEIPT = PROOF / "valid" / "receipt_provider_llm_judge_execution_on_materialized_fixtures.json"
RAW = PROOF / "raw" / "llm_judge"
NEXT_GATE = Path("experiments/iter95_provider_llm_judge_prompt_budget_recovery_after_block/HYPOTHESIS.md")

ITER93_PROOF = Path("experiments/iter93_deterministic_strategy_execution_on_materialized_fixtures/proof")
ITER93_SUMMARY = ITER93_PROOF / "run_summary.json"
ITER93_ENDPOINTS = ITER93_PROOF / "endpoint_results.json"
ITER93_RECEIPT = ITER93_PROOF / "valid" / "receipt_deterministic_strategy_execution_on_materialized_fixtures.json"
ITER92_LABELS = Path("experiments/iter92_empirical_validation_fixture_materialization_for_completion_verification/proof/ground_truth_labels.json")

CALL_CEILING = 14
SPEND_CEILING = Decimal("10.00000000")
RECORDED_BLOCKED_COST = Decimal("0.00470000")
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
        MODEL_BINDING,
        PROMPT_TEMPLATE,
        DECISION_MANIFEST,
        PROVIDER_USAGE,
        ENDPOINTS,
        CLAIM_BOUNDARY,
        REDACTION,
        RECEIPT,
        NEXT_GATE,
        RAW / "EVC-FIXTURE-0001.prompt.txt",
        RAW / "EVC-FIXTURE-0001.response.json",
    ]:
        if not path.exists():
            failures.append(f"missing required file: {path}")


def audit_schemas(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    expected = {
        "summary": "telos.provider_llm_judge_execution.summary.v1",
        "prereq": "telos.provider_llm_judge_execution.iter93_prerequisite_validation.v1",
        "model_binding": "telos.provider_llm_judge_execution.model_binding.v1",
        "decision_manifest": "telos.provider_llm_judge_execution.decision_manifest.v1",
        "provider_usage": "telos.provider_llm_judge_execution.provider_usage.v1",
        "endpoints": "telos.provider_llm_judge_execution.endpoint_results.v1",
        "claim_boundary": "telos.provider_llm_judge_execution.claim_boundary.v1",
        "redaction": "telos.provider_llm_judge_execution.redaction_scan.v1",
    }
    for name, schema in expected.items():
        if packets[name].get("schema_version") != schema:
            failures.append(f"{name} schema mismatch: {packets[name].get('schema_version')}")


def audit_iter93_prerequisite(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    prereq = packets["prereq"]
    iter93 = load_json(ITER93_SUMMARY)
    if prereq.get("clean_prerequisites") is not True:
        failures.append("iter93 prerequisite not clean")
    if prereq.get("iter93_receipt_validation_returncode") != 0:
        failures.append("iter93 receipt validation failed")
    if prereq.get("iter93_audit_returncode") != 0:
        failures.append("iter93 audit failed")
    if prereq.get("iter93_deterministic_decision_count") != 56:
        failures.append("iter93 deterministic decision count mismatch")
    if prereq.get("iter93_llm_judge_execution_count") != 0:
        failures.append("iter93 already had LLM judge execution")
    for label, path in [
        ("iter93_summary", ITER93_SUMMARY),
        ("iter93_endpoint_results", ITER93_ENDPOINTS),
        ("iter93_receipt", ITER93_RECEIPT),
    ]:
        if prereq.get("source_hashes", {}).get(label) != sha256(path):
            failures.append(f"iter93 prerequisite hash mismatch: {label}")
    if iter93.get("next_gate") != "experiments/iter94_provider_llm_judge_execution_on_materialized_fixtures/HYPOTHESIS.md":
        failures.append("iter93 next gate mismatch")


def audit_blocked_provider_run(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = packets["summary"]
    manifest = packets["decision_manifest"]
    usage = packets["provider_usage"]
    endpoints = packets["endpoints"]
    binding = packets["model_binding"]
    boundary = packets["claim_boundary"]
    redaction = packets["redaction"]

    if summary.get("status") != "blocked":
        failures.append("iter94 should be a blocked result")
    if summary.get("blocked_result") is not True:
        failures.append("blocked_result must be true")
    if summary.get("quality_failure") is not False:
        failures.append("blocked parse issue must not be classified as quality failure")
    if summary.get("clean_pass") is not False:
        failures.append("blocked run cannot be clean_pass")
    if not summary.get("blockers"):
        failures.append("blocked run must list blocker")
    if summary.get("failures"):
        failures.append("blocked run must not list quality failures")
    if summary.get("llm_judge_decision_count") != 0 or manifest.get("llm_judge_decision_count") != 0:
        failures.append("LLM judge decision count should be zero after parse blocker")
    if summary.get("expected_llm_judge_decision_count") != 14:
        failures.append("expected LLM judge decision count mismatch")
    if summary.get("provider_api_calls") != 1 or usage.get("provider_api_calls") != 1:
        failures.append("provider call count should record exactly one attempted call")
    if summary.get("provider_call_ceiling") != CALL_CEILING or usage.get("provider_call_ceiling") != CALL_CEILING:
        failures.append("provider call ceiling mismatch")
    if decimal_value(summary.get("provider_cost_usd")) != RECORDED_BLOCKED_COST:
        failures.append("provider cost should match recorded blocked call")
    if decimal_value(usage.get("provider_cost_usd")) != RECORDED_BLOCKED_COST:
        failures.append("provider usage cost mismatch")
    if decimal_value(summary.get("provider_spend_ceiling_usd")) != SPEND_CEILING:
        failures.append("provider spend ceiling mismatch")
    if decimal_value(summary.get("provider_cost_usd")) > SPEND_CEILING:
        failures.append("provider spend exceeded ceiling")
    if summary.get("labels_used_in_llm_judge_prompts") is not False:
        failures.append("summary says labels were used in prompts")
    if manifest.get("labels_used_in_llm_judge_prompt") is not False:
        failures.append("manifest says labels were used in prompt")
    if endpoints.get("labels_used_in_llm_judge_prompt") is not False:
        failures.append("endpoints say labels were used in prompt")
    if endpoints.get("all_strategy_endpoint_evidence_complete") is not False:
        failures.append("blocked run should not have complete all-strategy endpoints")
    if binding.get("adc_token_logged") is not False or binding.get("project_identifier_logged") is not False:
        failures.append("model binding indicates secret/project logging")
    if redaction.get("passed") is not True or redaction.get("findings"):
        failures.append("redaction scan failed")
    for key in [
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "production_or_live_domain_changed",
    ]:
        if summary.get(key) is not False:
            failures.append(f"summary claim boundary not false: {key}")
        if key in boundary and boundary.get(key) is not False:
            failures.append(f"claim boundary not false: {key}")
    raw = load_json(RAW / "EVC-FIXTURE-0001.response.json")
    if raw.get("ok") is not True or raw.get("http_status") != 200:
        failures.append("raw response should record a successful provider HTTP response")
    response = raw.get("response", {})
    usage_meta = response.get("usageMetadata", {})
    if usage_meta.get("promptTokenCount") != 838:
        failures.append("raw prompt token count mismatch")
    if usage_meta.get("candidatesTokenCount") != 11:
        failures.append("raw candidate token count mismatch")
    if usage_meta.get("thoughtsTokenCount") != 241:
        failures.append("raw thoughts token count mismatch")
    finish_reason = response.get("candidates", [{}])[0].get("finishReason")
    if finish_reason != "MAX_TOKENS":
        failures.append(f"expected MAX_TOKENS blocker, got {finish_reason}")
    prompt_text = (RAW / "EVC-FIXTURE-0001.prompt.txt").read_text(encoding="utf-8")
    for forbidden in ["ground_truth_completed", "label_justification", "ground_truth_label.json"]:
        if forbidden in prompt_text:
            failures.append(f"prompt contains label-like text: {forbidden}")
    if "ground_truth_labels.json" in prompt_text:
        failures.append("prompt references ground-truth labels file")
    if "EVC-PROXY-FALSE-001" not in prompt_text:
        failures.append("prompt no longer matches committed first fixture")
    labels = load_json(ITER92_LABELS)
    if labels.get("label_count") != 14:
        failures.append("iter92 labels unavailable for future scoring")


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
        "Status: `BLOCKED`.",
        "provider calls attempted: `1`",
        "provider spend: `$0.00470000`",
        "LLM judge decision count: `0`",
        "all-strategy endpoint evidence complete: `false`",
        "benchmark/model/SOTA claim: `false`",
        "LLM judge response could not be parsed",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "Provider calls attempted: `1`.",
        "Provider spend: `$0.00470000`.",
        "Status: `blocked`.",
        "No benchmark, model-superiority, production/live-domain, or state-of-the-art result",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "provider LLM judge execution: blocked",
        "provider_api_calls=1",
        "provider_cost_usd=0.00470000",
        "llm_judge_decision_count=0",
        "all_strategy_endpoint_evidence_complete=false",
        "llm_judge_false_completion_acceptance_rate=not_available",
        "benchmark_model_sota_claimed=false",
        "failures=none",
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
            "model_binding": load_json(MODEL_BINDING),
            "decision_manifest": load_json(DECISION_MANIFEST),
            "provider_usage": load_json(PROVIDER_USAGE),
            "endpoints": load_json(ENDPOINTS),
            "claim_boundary": load_json(CLAIM_BOUNDARY),
            "redaction": load_json(REDACTION),
        }
        audit_schemas(packets, failures)
        audit_iter93_prerequisite(packets, failures)
        audit_blocked_provider_run(packets, failures)
        audit_receipt_text_hashes_and_secrets(packets["summary"], failures)
    if failures:
        print("iter94 provider LLM judge execution audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter94 provider LLM judge execution audit: blocked pass")
    print("provider_api_calls=1")
    print("provider_cost_usd=0.00470000")
    print("llm_judge_decision_count=0")
    print("blocker=llm_judge_response_parse_failure_after_max_tokens")
    print(f"next_gate={NEXT_GATE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
