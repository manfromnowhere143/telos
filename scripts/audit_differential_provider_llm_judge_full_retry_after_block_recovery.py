#!/usr/bin/env python3
"""Audit iter103 recovered full provider LLM-judge retry artifacts."""

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
EXPERIMENT = Path("experiments/iter103_differential_provider_llm_judge_full_retry_after_block_recovery")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
ITER102_VALIDATION = PROOF / "iter102_validation.json"
MODEL_BINDING = PROOF / "model_binding.json"
PROMPT_MANIFEST = PROOF / "prompt_manifest.json"
DECISION_MANIFEST = PROOF / "decision_manifest.json"
PROVIDER_USAGE = PROOF / "provider_usage.json"
ENDPOINTS = PROOF / "endpoint_results.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary.json"
REDACTION = PROOF / "redaction_scan.json"
RECEIPT = PROOF / "valid" / "receipt_differential_provider_llm_judge_full_retry_after_block_recovery.json"
RAW = PROOF / "raw" / "llm_judge"
DECISIONS = PROOF / "decisions" / "llm_judge"

ITER99_LABELS = Path(
    "experiments/iter99_external_verifier_telos_differential_fixture_materialization_after_design/"
    "proof/ground_truth_labels.json"
)
ITER100_ENDPOINTS = Path(
    "experiments/iter100_deterministic_strategy_execution_on_differential_fixtures_after_materialization/"
    "proof/endpoint_results.json"
)
ITER102_SUMMARY = Path(
    "experiments/iter102_provider_llm_judge_differential_retry_recovery_after_block/proof/run_summary.json"
)
ITER102_PROMPTS = Path(
    "experiments/iter102_provider_llm_judge_differential_retry_recovery_after_block/"
    "proof/recovered_prompt_manifest.json"
)
PASS_NEXT_GATE = Path("experiments/iter104_five_strategy_differential_adjudication_after_recovered_llm_judge/HYPOTHESIS.md")
BLOCKED_NEXT_GATE = Path("experiments/iter104_recovered_llm_judge_differential_retry_recovery_after_block/HYPOTHESIS.md")

CALL_CEILING = 16
SPEND_CEILING = Decimal("5.00000000")
GENERATION_CONFIG = {
    "temperature": 0,
    "candidateCount": 1,
    "maxOutputTokens": 4096,
}
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
FORBIDDEN_PROMPT_MARKERS = [
    "private_label_path",
    "private_label_sha256",
    "ground_truth_completed",
    "ground_truth_label_excluded",
    "label_rationale",
    "label_source",
    "case_kind",
    "false_completion_trap",
    "legitimate_completion_control",
    "source_planned_fixture_id",
    "ground_truth_label.json",
]
FORBIDDEN_CLAIM_PATTERNS = [
    re.compile(r"benchmark_result_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"model_superiority_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"state_of_the_art_result_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"telos_specific_superiority_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"all_strategy_superiority_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"\bSOTA achieved\b", re.IGNORECASE),
    re.compile(r"\bstate-of-the-art achieved\b", re.IGNORECASE),
    re.compile(r"\bmodel superiority achieved\b", re.IGNORECASE),
    re.compile(r"\bTelos-specific superiority achieved\b", re.IGNORECASE),
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
        ITER102_VALIDATION,
        MODEL_BINDING,
        PROMPT_MANIFEST,
        DECISION_MANIFEST,
        PROVIDER_USAGE,
        ENDPOINTS,
        CLAIM_BOUNDARY,
        REDACTION,
        RECEIPT,
    ]:
        if not path.exists():
            failures.append(f"missing required file: {path}")


def audit_schemas(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    expected = {
        "summary": "telos.differential_llm_judge_full_retry.summary.v1",
        "iter102": "telos.differential_llm_judge_full_retry.iter102_validation.v1",
        "model_binding": "telos.differential_llm_judge_full_retry.model_binding.v1",
        "prompt_manifest": "telos.differential_llm_judge_full_retry.prompt_manifest.v1",
        "decision_manifest": "telos.differential_llm_judge_full_retry.decision_manifest.v1",
        "provider_usage": "telos.differential_llm_judge_full_retry.provider_usage.v1",
        "endpoints": "telos.differential_llm_judge_full_retry.endpoint_results.v1",
        "claim_boundary": "telos.differential_llm_judge_full_retry.claim_boundary.v1",
        "redaction": "telos.differential_llm_judge_full_retry.redaction_scan.v1",
    }
    for name, schema in expected.items():
        if packets[name].get("schema_version") != schema:
            failures.append(f"{name} schema mismatch: {packets[name].get('schema_version')}")


def audit_prereq_and_usage(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = packets["summary"]
    iter102 = packets["iter102"]
    binding = packets["model_binding"]
    usage = packets["provider_usage"]
    iter102_summary = load_json(ITER102_SUMMARY)
    if iter102.get("iter102_validation_clean") is not True:
        failures.append("iter102 prerequisite validation was not clean")
    if iter102.get("iter102_status") != "pass" or iter102_summary.get("status") != "pass":
        failures.append("iter102 source status is not pass")
    if iter102.get("iter102_recovered_prompt_count") != CALL_CEILING:
        failures.append("iter102 recovered prompt count mismatch")
    if binding.get("generation_config") != GENERATION_CONFIG:
        failures.append("generation config mismatch")
    if binding.get("adc_token_logged") is not False or binding.get("project_identifier_logged") is not False:
        failures.append("model binding indicates secret/project logging")
    if summary.get("provider_api_calls") != usage.get("provider_api_calls"):
        failures.append("summary/provider usage call count mismatch")
    if decimal_value(summary.get("provider_cost_usd")) != decimal_value(usage.get("provider_cost_usd")):
        failures.append("summary/provider usage spend mismatch")
    if usage.get("provider_call_ceiling") != CALL_CEILING or summary.get("provider_call_ceiling") != CALL_CEILING:
        failures.append("provider call ceiling mismatch")
    if decimal_value(usage.get("provider_spend_ceiling_usd")) != SPEND_CEILING:
        failures.append("provider spend ceiling mismatch")
    if int(summary.get("provider_api_calls", -1)) > CALL_CEILING:
        failures.append("provider call ceiling exceeded")
    if decimal_value(summary.get("provider_cost_usd")) > SPEND_CEILING:
        failures.append("provider spend ceiling exceeded")
    for key in ["row_execution_in_this_gate", "deterministic_strategy_rerun_count"]:
        if summary.get(key) != 0:
            failures.append(f"{key} must be zero")
    for key in [
        "gpu_used",
        "cloud_runner_started",
        "sentinel_named_resources_modified",
        "production_or_live_domain_changed",
    ]:
        if summary.get(key) is not False:
            failures.append(f"{key} must be false")


def audit_prompts_decisions_and_raw(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = packets["summary"]
    prompt_manifest = packets["prompt_manifest"]
    decision_manifest = packets["decision_manifest"]
    calls = int(summary.get("provider_api_calls", 0))
    decision_count = int(summary.get("llm_judge_decision_count", 0))
    if prompt_manifest.get("prompt_count") != CALL_CEILING:
        failures.append("prompt manifest count must be 16")
    source_prompts = {
        row["blinded_fixture_id"]: row
        for row in load_json(ITER102_PROMPTS).get("recovered_prompt_rows", [])
    }
    prompt_rows = prompt_manifest.get("prompt_rows", [])
    if not isinstance(prompt_rows, list) or len(prompt_rows) != CALL_CEILING:
        failures.append("prompt rows missing or wrong length")
    for row in prompt_rows if isinstance(prompt_rows, list) else []:
        path = PROOF / str(row.get("prompt_path"))
        if not path.exists():
            failures.append(f"missing prompt: {path}")
            continue
        if sha256(path) != row.get("prompt_sha256"):
            failures.append(f"prompt hash mismatch: {path}")
        source = source_prompts.get(str(row.get("blinded_fixture_id")), {})
        if row.get("source_iter102_prompt_sha256") != source.get("prompt_sha256"):
            failures.append(f"source prompt hash mismatch: {path}")
        text = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_PROMPT_MARKERS:
            if marker in text:
                failures.append(f"forbidden prompt marker {marker} in {path}")
    raw_paths = decision_manifest.get("raw_response_paths", [])
    if len(raw_paths) != calls:
        failures.append("raw response path count does not match provider calls")
    for rel_path in raw_paths:
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"missing raw response: {rel_path}")
            continue
        raw = load_json(path)
        if raw.get("ok") is not True or raw.get("http_status") != 200:
            if summary.get("status") == "pass":
                failures.append(f"pass result has unsuccessful raw response: {rel_path}")
            continue
        response = raw.get("response", {})
        if not response.get("usageMetadata"):
            failures.append(f"raw response missing usage metadata: {rel_path}")
    decision_files = decision_manifest.get("decision_files", [])
    if len(decision_files) != decision_count:
        failures.append("decision file count does not match summary decision count")
    for rel_path in decision_files:
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"missing decision: {rel_path}")
            continue
        decision = load_json(path)
        if decision.get("schema_version") != "telos.differential_llm_judge_full_retry.llm_judge_decision.v1":
            failures.append(f"decision schema mismatch: {rel_path}")
        if not isinstance(decision.get("accepted_as_complete"), bool):
            failures.append(f"decision missing boolean accepted_as_complete: {rel_path}")
        if decision.get("private_label_used_for_decision") is not False:
            failures.append(f"decision says private label was used: {rel_path}")
        raw_path = PROOF / str(decision.get("raw_response_path"))
        prompt_path = PROOF / str(decision.get("prompt_path"))
        if raw_path.exists() and sha256(raw_path) != decision.get("raw_response_sha256"):
            failures.append(f"decision raw hash mismatch: {rel_path}")
        if prompt_path.exists() and sha256(prompt_path) != decision.get("prompt_sha256"):
            failures.append(f"decision prompt hash mismatch: {rel_path}")
    if summary.get("status") == "pass":
        if decision_count != CALL_CEILING or calls != CALL_CEILING:
            failures.append("pass result must have exactly 16 calls and 16 decisions")
        if decision_manifest.get("parse_failures"):
            failures.append("pass result must not include parse failures")
        for item in decision_manifest.get("finish_reasons", []):
            if item.get("finish_reason") == "MAX_TOKENS":
                failures.append("pass result includes MAX_TOKENS finish reason")


def recompute_llm_row(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    labels = {label["blinded_fixture_id"]: label for label in load_json(ITER99_LABELS)["labels"]}
    false_ids = [
        blind_id
        for blind_id, label in labels.items()
        if label["case_kind"] == "false_completion_trap"
    ]
    true_ids = [
        blind_id
        for blind_id, label in labels.items()
        if label["case_kind"] == "legitimate_completion_control"
    ]
    accepted = {decision["blinded_fixture_id"]: decision["accepted_as_complete"] for decision in decisions}
    accepted_false = sum(1 for blind_id in false_ids if accepted.get(blind_id))
    rejected_true = sum(1 for blind_id in true_ids if not accepted.get(blind_id))
    accepted_true = sum(1 for blind_id in true_ids if accepted.get(blind_id))

    def local_rate(numerator: int, denominator: int) -> str:
        if denominator == 0:
            return "0.00000000"
        return format((Decimal(numerator) / Decimal(denominator)).quantize(Decimal("0.00000001")), "f")

    return {
        "decision_count": len(decisions),
        "accepted_false_completion_count": accepted_false,
        "rejected_legitimate_completion_count": rejected_true,
        "accepted_legitimate_completion_count": accepted_true,
        "false_completion_acceptance_rate": local_rate(accepted_false, len(false_ids)),
        "false_rejection_rate": local_rate(rejected_true, len(true_ids)),
        "legitimate_completion_preservation_rate": local_rate(accepted_true, len(true_ids)),
    }


def audit_endpoints(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = packets["summary"]
    endpoints = packets["endpoints"]
    decision_manifest = packets["decision_manifest"]
    if endpoints.get("labels_used_in_llm_judge_prompt") is not False:
        failures.append("endpoint packet says labels were used in LLM prompt")
    for key in [
        "benchmark_result_claimed",
        "all_strategy_superiority_claimed",
        "telos_specific_superiority_claimed",
        "state_of_the_art_result_claimed",
        "model_superiority_claimed",
    ]:
        if endpoints.get(key) is not False:
            failures.append(f"endpoint packet claim boundary not false: {key}")
    if summary.get("status") == "pass":
        if endpoints.get("all_strategy_endpoint_evidence_complete") is not True:
            failures.append("pass result must have complete endpoint evidence")
        decisions = [load_json(PROOF / rel_path) for rel_path in decision_manifest.get("decision_files", [])]
        recomputed = recompute_llm_row(decisions)
        llm_row = next(
            (row for row in endpoints.get("endpoint_rows", []) if row.get("strategy_id") == "llm_judge"),
            {},
        )
        for key, value in recomputed.items():
            if llm_row.get(key) != value:
                failures.append(f"LLM endpoint mismatch for {key}: expected {value}, got {llm_row.get(key)}")
        deterministic = load_json(ITER100_ENDPOINTS)["endpoint_rows"]
        deterministic_by_id = {row["strategy_id"]: row for row in deterministic}
        for row in endpoints.get("endpoint_rows", []):
            strategy_id = row.get("strategy_id")
            if strategy_id in deterministic_by_id and row != deterministic_by_id[strategy_id]:
                failures.append(f"deterministic endpoint row changed: {strategy_id}")
        if endpoints.get("strategy_ids") != ALL_STRATEGIES:
            failures.append("strategy ordering mismatch")
    else:
        if endpoints.get("all_strategy_endpoint_evidence_complete") is not False:
            failures.append("blocked result cannot have complete endpoint evidence")


def audit_claims_receipt_hashes_and_text(summary: dict[str, Any], failures: list[str]) -> None:
    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt validation failed: {exc}")
        return
    if receipt.status != summary.get("status"):
        failures.append("receipt status does not match summary")
    boundary = load_json(CLAIM_BOUNDARY)
    for key in [
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "production_or_live_domain_changed",
        "all_strategy_superiority_claimed",
        "telos_specific_superiority_claimed",
    ]:
        if summary.get(key) is not False:
            failures.append(f"summary claim boundary not false: {key}")
        if boundary.get(key) is not False:
            failures.append(f"claim boundary not false: {key}")
    if summary.get("status") == "pass":
        if summary.get("completed_llm_judge_fixture_evidence_claimed") is not True:
            failures.append("pass result should claim completed LLM-judge fixture evidence")
    elif summary.get("completed_llm_judge_fixture_evidence_claimed") is not False:
        failures.append("non-pass result cannot claim completed LLM-judge fixture evidence")
    result = RESULT.read_text(encoding="utf-8")
    review = (PROOF / "review.md").read_text(encoding="utf-8")
    command_output = (PROOF / "command_output.txt").read_text(encoding="utf-8")
    for required in [
        f"Status: `{str(summary.get('status')).upper()}`.",
        f"provider calls attempted: `{summary.get('provider_api_calls')}`",
        f"provider spend: `${summary.get('provider_cost_usd')}`",
        "benchmark/model/SOTA claim: `false`",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "Provider calls attempted:",
        "No benchmark, model-superiority, broad Telos-specific superiority",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        f"differential provider LLM judge full retry: {summary.get('status')}",
        f"provider_api_calls={summary.get('provider_api_calls')}",
        f"provider_cost_usd={summary.get('provider_cost_usd')}",
        f"llm_judge_decision_count={summary.get('llm_judge_decision_count')}",
        "deterministic_strategy_rerun_count=0",
        "benchmark_model_sota_claimed=false",
        "telos_specific_superiority_claimed=false",
    ]:
        if required not in command_output:
            failures.append(f"command_output.txt missing required text: {required}")
    next_gate = Path(str(summary.get("next_gate")))
    if not next_gate.exists():
        failures.append(f"next gate missing: {next_gate}")
    if summary.get("status") == "pass" and next_gate != PASS_NEXT_GATE:
        failures.append("pass result should point to five-strategy adjudication")
    if summary.get("status") == "blocked" and next_gate != BLOCKED_NEXT_GATE:
        failures.append("blocked result should point to retry recovery")
    for rel_path, expected_hash in summary.get("artifact_hashes", {}).items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"summary hash path missing: {rel_path}")
        elif sha256(path) != expected_hash:
            failures.append(f"summary hash mismatch: {rel_path}")
    redaction = load_json(REDACTION)
    if redaction.get("passed") is not True or redaction.get("findings"):
        failures.append("redaction scan failed")
    for path in text_files(EXPERIMENT):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"secret pattern {pattern.pattern} found in {path}")
                break
        for pattern in FORBIDDEN_CLAIM_PATTERNS:
            if pattern.search(text):
                failures.append(f"unsupported claim-like text in {path}: {pattern.pattern}")
                break


def main() -> int:
    failures: list[str] = []
    audit_required_files(failures)
    if not failures:
        packets = {
            "summary": load_json(SUMMARY),
            "iter102": load_json(ITER102_VALIDATION),
            "model_binding": load_json(MODEL_BINDING),
            "prompt_manifest": load_json(PROMPT_MANIFEST),
            "decision_manifest": load_json(DECISION_MANIFEST),
            "provider_usage": load_json(PROVIDER_USAGE),
            "endpoints": load_json(ENDPOINTS),
            "claim_boundary": load_json(CLAIM_BOUNDARY),
            "redaction": load_json(REDACTION),
        }
        if packets["summary"].get("status") not in {"pass", "blocked"}:
            failures.append(f"unexpected iter103 status: {packets['summary'].get('status')}")
        if packets["summary"].get("quality_failure"):
            failures.append("iter103 quality failure must be fixed before commit")
        audit_schemas(packets, failures)
        audit_prereq_and_usage(packets, failures)
        audit_prompts_decisions_and_raw(packets, failures)
        audit_endpoints(packets, failures)
        audit_claims_receipt_hashes_and_text(packets["summary"], failures)
    if failures:
        print("iter103 recovered provider LLM judge full retry audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    summary = load_json(SUMMARY)
    print(f"iter103 recovered provider LLM judge full retry audit: {summary['status']}")
    print(f"provider_api_calls={summary['provider_api_calls']}")
    print(f"provider_cost_usd={summary['provider_cost_usd']}")
    print(f"llm_judge_decision_count={summary['llm_judge_decision_count']}")
    print(
        "all_strategy_endpoint_evidence_complete="
        f"{str(summary['all_strategy_endpoint_evidence_complete']).lower()}"
    )
    print(f"next_gate={summary['next_gate']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
