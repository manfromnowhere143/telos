#!/usr/bin/env python3
"""Audit iter102 differential LLM-judge retry recovery artifacts."""

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
EXPERIMENT = Path("experiments/iter102_provider_llm_judge_differential_retry_recovery_after_block")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
ITER101_VALIDATION = PROOF / "iter101_validation.json"
BLOCKER_ANALYSIS = PROOF / "blocker_analysis.json"
USAGE_ANALYSIS = PROOF / "usage_analysis.json"
PROMPT_MANIFEST = PROOF / "recovered_prompt_manifest.json"
LEAKAGE = PROOF / "label_leakage_check.json"
PLAN = PROOF / "retry_recovery_plan.json"
RETRY = PROOF / "retry_envelope.json"
BOUNDARY = PROOF / "claim_boundary.json"
REDACTION = PROOF / "redaction_scan.json"
REVIEW = PROOF / "review.md"
COMMAND_OUTPUT = PROOF / "command_output.txt"
RECEIPT = (
    PROOF
    / "valid"
    / "receipt_provider_llm_judge_differential_retry_recovery_after_block.json"
)
NEXT_GATE = Path("experiments/iter103_differential_provider_llm_judge_full_retry_after_block_recovery/HYPOTHESIS.md")

ITER101_SUMMARY = Path(
    "experiments/iter101_provider_llm_judge_execution_on_differential_fixtures_after_deterministic/"
    "proof/run_summary.json"
)
ITER101_USAGE = Path(
    "experiments/iter101_provider_llm_judge_execution_on_differential_fixtures_after_deterministic/"
    "proof/provider_usage.json"
)
ITER101_DECISION_MANIFEST = Path(
    "experiments/iter101_provider_llm_judge_execution_on_differential_fixtures_after_deterministic/"
    "proof/decision_manifest.json"
)
ITER101_BLOCKED_RAW = Path(
    "experiments/iter101_provider_llm_judge_execution_on_differential_fixtures_after_deterministic/"
    "proof/raw/llm_judge/DIFX-FIXTURE-0014.response.json"
)

OLD_MAX_OUTPUT_TOKENS = 2048
RECOVERED_MAX_OUTPUT_TOKENS = 4096
FUTURE_PROVIDER_CALL_CEILING = 16
FUTURE_PROVIDER_SPEND_CEILING = Decimal("5.00000000")
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
        ITER101_VALIDATION,
        BLOCKER_ANALYSIS,
        USAGE_ANALYSIS,
        PROMPT_MANIFEST,
        LEAKAGE,
        PLAN,
        RETRY,
        BOUNDARY,
        REDACTION,
        REVIEW,
        COMMAND_OUTPUT,
        RECEIPT,
        NEXT_GATE,
        PROOF / "recovered_prompt_template.md",
    ]:
        if not path.exists():
            failures.append(f"missing required file: {path}")


def audit_schemas(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    expected = {
        "summary": "telos.differential_llm_judge_retry_recovery.summary.v1",
        "iter101": "telos.differential_llm_judge_retry_recovery.iter101_validation.v1",
        "blocker": "telos.differential_llm_judge_retry_recovery.blocker_analysis.v1",
        "usage": "telos.differential_llm_judge_retry_recovery.usage_analysis.v1",
        "prompt_manifest": "telos.differential_llm_judge_retry_recovery.prompt_manifest.v1",
        "leakage": "telos.differential_llm_judge_retry_recovery.label_leakage_check.v1",
        "plan": "telos.differential_llm_judge_retry_recovery.plan.v1",
        "retry": "telos.differential_llm_judge_retry_recovery.retry_envelope.v1",
        "boundary": "telos.differential_llm_judge_retry_recovery.claim_boundary.v1",
        "redaction": "telos.differential_llm_judge_retry_recovery.redaction_scan.v1",
    }
    for name, schema in expected.items():
        if packets[name].get("schema_version") != schema:
            failures.append(f"{name} schema mismatch: {packets[name].get('schema_version')}")


def audit_summary_and_iter101(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = packets["summary"]
    iter101 = packets["iter101"]
    iter101_summary = load_json(ITER101_SUMMARY)
    iter101_usage = load_json(ITER101_USAGE)
    if summary.get("status") != "pass" or summary.get("clean_pass") is not True:
        failures.append("iter102 must be a clean pass")
    if summary.get("provider_api_calls") != 0:
        failures.append("iter102 provider calls must be zero")
    if decimal_value(summary.get("provider_cost_usd")) != ZERO:
        failures.append("iter102 provider spend must be zero")
    for key in [
        "llm_judge_execution_count",
        "deterministic_strategy_rerun_count",
        "row_execution_in_this_gate",
    ]:
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
    if iter101.get("iter101_validation_clean") is not True:
        failures.append("iter101 validation was not clean")
    if iter101.get("iter101_status") != "blocked":
        failures.append("iter101 status should be blocked")
    if iter101.get("iter101_quality_failure") is not False:
        failures.append("iter101 quality failure should be false")
    if iter101.get("iter101_provider_api_calls") != 14:
        failures.append("iter101 provider call count mismatch")
    if decimal_value(iter101.get("iter101_provider_cost_usd")) != Decimal("0.22777400"):
        failures.append("iter101 provider cost mismatch")
    if iter101.get("iter101_llm_judge_decision_count") != 13:
        failures.append("iter101 decision count mismatch")
    if iter101.get("iter101_expected_llm_judge_decision_count") != 16:
        failures.append("iter101 expected decision count mismatch")
    if iter101.get("iter101_labels_used_in_llm_judge_prompts") is not False:
        failures.append("iter101 labels should not have been used in prompts")
    if summary.get("iter101_provider_api_calls") != iter101_summary.get("provider_api_calls"):
        failures.append("summary did not preserve iter101 provider call count")
    if decimal_value(summary.get("iter101_provider_cost_usd")) != decimal_value(
        iter101_usage.get("provider_cost_usd")
    ):
        failures.append("summary did not preserve iter101 provider spend")


def audit_blocker_and_usage(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = packets["summary"]
    blocker = packets["blocker"]
    usage = packets["usage"]
    raw = load_json(ITER101_BLOCKED_RAW)
    raw_usage = raw.get("response", {}).get("usageMetadata", {})
    if blocker.get("blocked_fixture_id") != "DIFX-FIXTURE-0014":
        failures.append("unexpected blocked fixture id")
    if blocker.get("finish_reason") != "MAX_TOKENS":
        failures.append("blocker finish reason should be MAX_TOKENS")
    if blocker.get("directly_tied_to_output_budget_handling") is not True:
        failures.append("blocker is not tied to output-budget handling")
    if blocker.get("root_cause_classification") != "output_budget_exhausted_by_hidden_reasoning_before_json_completion":
        failures.append("unexpected blocker root-cause classification")
    if blocker.get("original_max_output_tokens") != OLD_MAX_OUTPUT_TOKENS:
        failures.append("old max output token mismatch")
    if blocker.get("thoughts_tokens") != 1966 or blocker.get("candidate_tokens") != 78:
        failures.append("iter101 blocker usage analysis mismatch")
    if blocker.get("response_text_parseable_json") is not False:
        failures.append("iter101 blocked response should be unparseable JSON")
    if blocker.get("blocked_raw_response_sha256") != sha256(ITER101_BLOCKED_RAW):
        failures.append("blocked raw response hash mismatch")
    if raw_usage.get("thoughtsTokenCount") != blocker.get("thoughts_tokens"):
        failures.append("blocker thoughts token count does not match raw response")
    if summary.get("blocked_fixture_id") != blocker.get("blocked_fixture_id"):
        failures.append("summary/blocker fixture mismatch")
    if usage.get("provider_call_count") != 14:
        failures.append("usage analysis provider call count mismatch")
    if usage.get("finish_reason_counts", {}).get("MAX_TOKENS") != 1:
        failures.append("usage analysis should show one MAX_TOKENS response")
    if usage.get("finish_reason_counts", {}).get("STOP") != 13:
        failures.append("usage analysis should show thirteen STOP responses")
    if usage.get("blocked_output_tokens") != 2044:
        failures.append("usage analysis blocked output token mismatch")
    if len(usage.get("usage_rows", [])) != 14:
        failures.append("usage rows should include fourteen attempted calls")
    decision_manifest = load_json(ITER101_DECISION_MANIFEST)
    raw_paths = [row.get("raw_response_path") for row in usage.get("usage_rows", [])]
    for rel_path in decision_manifest.get("raw_response_paths", []):
        if str(Path("experiments") / "..") in rel_path:
            failures.append("unexpected relative traversal in raw response path")
        full = str(Path("experiments/iter101_provider_llm_judge_execution_on_differential_fixtures_after_deterministic/proof") / rel_path)
        if full not in raw_paths:
            failures.append(f"usage analysis missing raw response path: {rel_path}")


def audit_prompt_recovery(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = packets["summary"]
    prompt_manifest = packets["prompt_manifest"]
    leakage = packets["leakage"]
    plan = packets["plan"]
    retry = packets["retry"]
    if prompt_manifest.get("prompt_count") != 16:
        failures.append("recovered prompt count must be 16")
    if prompt_manifest.get("labels_excluded_from_recovered_prompts") is not True:
        failures.append("prompt manifest says labels were not excluded")
    if prompt_manifest.get("recovered_prompt_instruction_contains_think_privately") is not False:
        failures.append("recovered prompt should not contain the think-privately instruction")
    if leakage.get("labels_excluded_from_recovered_prompts") is not True or leakage.get("findings"):
        failures.append("label leakage check failed")
    if summary.get("labels_excluded_from_recovered_prompts") is not True:
        failures.append("summary label exclusion mismatch")
    if plan.get("recovered_generation_config", {}).get("maxOutputTokens") != RECOVERED_MAX_OUTPUT_TOKENS:
        failures.append("recovered maxOutputTokens mismatch")
    if plan.get("old_generation_config", {}).get("maxOutputTokens") != OLD_MAX_OUTPUT_TOKENS:
        failures.append("old maxOutputTokens mismatch in recovery plan")
    if plan.get("directly_addresses_iter101_blocker") is not True:
        failures.append("recovery plan does not directly address blocker")
    for required in [
        "remove the explicit think-privately instruction from the LLM-judge prompt",
        "rerun all sixteen fixtures under one recovered config rather than mixing configs",
        "stop on any parse failure and publish blocked evidence without unregistered retries",
    ]:
        if required not in plan.get("recovery_actions", []):
            failures.append(f"recovery plan missing action: {required}")
    if retry.get("next_gate") != str(NEXT_GATE):
        failures.append("retry envelope next gate mismatch")
    if retry.get("next_gate_pre_registered") is not True:
        failures.append("retry next gate is not pre-registered")
    if retry.get("future_retry_mode") != "full_16_fixture_rerun_under_single_recovered_config":
        failures.append("retry mode mismatch")
    if retry.get("future_provider_call_ceiling") != FUTURE_PROVIDER_CALL_CEILING:
        failures.append("future provider call ceiling mismatch")
    if decimal_value(retry.get("future_provider_spend_ceiling_usd")) != FUTURE_PROVIDER_SPEND_CEILING:
        failures.append("future provider spend ceiling mismatch")
    if retry.get("future_generation_config", {}).get("maxOutputTokens") != RECOVERED_MAX_OUTPUT_TOKENS:
        failures.append("retry generation config maxOutputTokens mismatch")
    if decimal_value(retry.get("estimated_worst_case_cost_usd")) > FUTURE_PROVIDER_SPEND_CEILING:
        failures.append("estimated worst-case retry cost exceeds ceiling")
    prompt_rows = prompt_manifest.get("recovered_prompt_rows", [])
    if not isinstance(prompt_rows, list) or len(prompt_rows) != 16:
        failures.append("prompt rows missing or wrong length")
        return
    for row in prompt_rows:
        path = PROOF / str(row.get("prompt_path"))
        if not path.exists():
            failures.append(f"missing recovered prompt: {path}")
            continue
        if sha256(path) != row.get("prompt_sha256"):
            failures.append(f"prompt hash mismatch: {path}")
        text = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_PROMPT_MARKERS:
            if marker in text:
                failures.append(f"forbidden prompt marker {marker} in {path}")
        for required in [
            "PUBLIC_ARTIFACTS_JSON=",
            "Return exactly one minified JSON object",
            "Keep rationale <= 96 chars",
            "decisive_evidence <= 3 items",
        ]:
            if required not in text:
                failures.append(f"recovered prompt missing required instruction {required}: {path}")


def audit_claims_receipt_hashes_and_text(summary: dict[str, Any], failures: list[str]) -> None:
    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt validation failed: {exc}")
        return
    if receipt.status != summary.get("status"):
        failures.append("receipt status does not match summary")
    boundary = load_json(BOUNDARY)
    for key in [
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "production_or_live_domain_changed",
        "completed_llm_judge_evidence_claimed",
        "all_strategy_superiority_claimed",
        "telos_specific_superiority_claimed",
    ]:
        if summary.get(key) is not False:
            failures.append(f"summary claim boundary not false: {key}")
        if boundary.get(key) is not False:
            failures.append(f"claim boundary not false: {key}")
    result = RESULT.read_text(encoding="utf-8")
    review = REVIEW.read_text(encoding="utf-8")
    command_output = COMMAND_OUTPUT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`.",
        "provider calls in iter102: `0`",
        "provider spend in iter102: `$0.00000000`",
        "private labels excluded from recovered prompts: `true`",
        "proposed retry mode: `full_16_fixture_rerun_under_single_recovered_config`",
        "benchmark/model/SOTA claim: `false`",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "Iter102 did not call a provider.",
        "full sixteen-fixture retry rather than adding only the three missing decisions",
        "one LLM-judge endpoint row under one recovered configuration",
        "No benchmark, model-superiority, broad Telos-specific superiority",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "differential provider LLM judge retry recovery: pass",
        "iter101_validation_clean=true",
        "provider_api_calls=0",
        "provider_cost_usd=0.00000000",
        "blocked_fixture_id=DIFX-FIXTURE-0014",
        "blocker_finish_reason=MAX_TOKENS",
        "recovered_prompt_count=16",
        "labels_excluded_from_recovered_prompts=true",
        "recovered_max_output_tokens=4096",
        "future_retry_mode=full_16_fixture_rerun_under_single_recovered_config",
        "benchmark_model_sota_claimed=false",
        "telos_specific_superiority_claimed=false",
    ]:
        if required not in command_output:
            failures.append(f"command_output.txt missing required text: {required}")
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
            "iter101": load_json(ITER101_VALIDATION),
            "blocker": load_json(BLOCKER_ANALYSIS),
            "usage": load_json(USAGE_ANALYSIS),
            "prompt_manifest": load_json(PROMPT_MANIFEST),
            "leakage": load_json(LEAKAGE),
            "plan": load_json(PLAN),
            "retry": load_json(RETRY),
            "boundary": load_json(BOUNDARY),
            "redaction": load_json(REDACTION),
        }
        if packets["summary"].get("status") not in {"pass", "blocked"}:
            failures.append(f"unexpected iter102 status: {packets['summary'].get('status')}")
        if packets["summary"].get("quality_failure"):
            failures.append("iter102 quality failure must be fixed before commit")
        audit_schemas(packets, failures)
        audit_summary_and_iter101(packets, failures)
        audit_blocker_and_usage(packets, failures)
        audit_prompt_recovery(packets, failures)
        audit_claims_receipt_hashes_and_text(packets["summary"], failures)
    if failures:
        print("iter102 provider LLM judge retry recovery audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    summary = load_json(SUMMARY)
    print(f"iter102 provider LLM judge retry recovery audit: {summary['status']}")
    print(f"iter101_provider_api_calls={summary['iter101_provider_api_calls']}")
    print(f"iter101_provider_cost_usd={summary['iter101_provider_cost_usd']}")
    print(f"provider_api_calls={summary['provider_api_calls']}")
    print(f"provider_cost_usd={summary['provider_cost_usd']}")
    print(f"blocked_fixture_id={summary['blocked_fixture_id']}")
    print(f"future_retry_mode={summary['future_retry_mode']}")
    print(f"next_gate={summary['next_gate']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
