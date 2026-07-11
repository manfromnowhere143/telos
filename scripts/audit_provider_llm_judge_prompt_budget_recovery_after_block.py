#!/usr/bin/env python3
"""Audit iter95 provider LLM-judge prompt-budget recovery artifacts."""

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
EXPERIMENT = Path("experiments/iter95_provider_llm_judge_prompt_budget_recovery_after_block")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
ITER94_VALIDATION = PROOF / "iter94_validation.json"
BLOCKER_ANALYSIS = PROOF / "blocker_analysis.json"
PROMPT_MANIFEST = PROOF / "prompt_manifest.json"
LEAKAGE = PROOF / "label_leakage_check.json"
RECOVERY_PLAN = PROOF / "prompt_budget_recovery_plan.json"
RETRY = PROOF / "retry_envelope.json"
BOUNDARY = PROOF / "claim_boundary.json"
REDACTION = PROOF / "redaction_scan.json"
REVIEW = PROOF / "review.md"
COMMAND_OUTPUT = PROOF / "command_output.txt"
RECEIPT = PROOF / "valid" / "receipt_provider_llm_judge_prompt_budget_recovery_after_block.json"
NEXT_GATE = Path("experiments/iter96_provider_llm_judge_bounded_retry_after_prompt_budget_recovery/HYPOTHESIS.md")

OLD_MAX_OUTPUT_TOKENS = 256
RECOVERED_MAX_OUTPUT_TOKENS = 2048
FUTURE_PROVIDER_CALL_CEILING = 14
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
    "source_case_id",
    "private_label_path",
    "private_label_sha256",
    "ground_truth_completed",
    "label_justification",
    "case_kind",
    "false_completion_trap",
    "legitimate_completion_control",
    "ground_truth_label.json",
]
FORBIDDEN_CLAIM_PATTERNS = [
    re.compile(r"benchmark_result_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"model_superiority_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"state_of_the_art_result_claimed[\"`:= ]+true", re.IGNORECASE),
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
        ITER94_VALIDATION,
        BLOCKER_ANALYSIS,
        PROMPT_MANIFEST,
        LEAKAGE,
        RECOVERY_PLAN,
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
        "summary": "telos.provider_llm_judge_prompt_budget_recovery.summary.v1",
        "iter94": "telos.provider_llm_judge_prompt_budget_recovery.iter94_validation.v1",
        "blocker": "telos.provider_llm_judge_prompt_budget_recovery.blocker_analysis.v1",
        "prompt_manifest": "telos.provider_llm_judge_prompt_budget_recovery.prompt_manifest.v1",
        "leakage": "telos.provider_llm_judge_prompt_budget_recovery.label_leakage_check.v1",
        "plan": "telos.provider_llm_judge_prompt_budget_recovery.plan.v1",
        "retry": "telos.provider_llm_judge_prompt_budget_recovery.retry_envelope.v1",
        "boundary": "telos.provider_llm_judge_prompt_budget_recovery.claim_boundary.v1",
        "redaction": "telos.provider_llm_judge_prompt_budget_recovery.redaction_scan.v1",
    }
    for name, schema in expected.items():
        if packets[name].get("schema_version") != schema:
            failures.append(f"{name} schema mismatch: {packets[name].get('schema_version')}")


def audit_summary_and_iter94(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = packets["summary"]
    iter94 = packets["iter94"]
    blocker = packets["blocker"]
    if summary.get("status") != "pass" or summary.get("clean_pass") is not True:
        failures.append("iter95 must be a clean pass")
    if summary.get("provider_api_calls") != 0:
        failures.append("iter95 provider calls must be zero")
    if decimal_value(summary.get("provider_cost_usd")) != ZERO:
        failures.append("iter95 provider spend must be zero")
    for key in [
        "llm_judge_execution_count",
        "deterministic_strategy_rerun_count",
        "row_execution_in_this_gate",
    ]:
        if summary.get(key) != 0:
            failures.append(f"{key} must be zero")
    for key in ["gpu_used", "cloud_runner_started", "sentinel_named_resources_modified", "production_or_live_domain_changed"]:
        if summary.get(key) is not False:
            failures.append(f"{key} must be false")
    if iter94.get("iter94_validation_clean") is not True:
        failures.append("iter94 validation was not clean")
    if iter94.get("iter94_status") != "blocked":
        failures.append("iter94 status should be blocked")
    if iter94.get("iter94_quality_failure") is not False:
        failures.append("iter94 quality failure should be false")
    if iter94.get("iter94_provider_api_calls") != 1:
        failures.append("iter94 provider call count mismatch")
    if decimal_value(iter94.get("iter94_provider_cost_usd")) != Decimal("0.00470000"):
        failures.append("iter94 provider cost mismatch")
    if iter94.get("iter94_llm_judge_decision_count") != 0:
        failures.append("iter94 should have zero LLM-judge decisions")
    if iter94.get("iter94_finish_reason") != "MAX_TOKENS":
        failures.append("iter94 finish reason should be MAX_TOKENS")
    if blocker.get("directly_tied_to_prompt_token_budget_handling") is not True:
        failures.append("blocker is not tied to prompt/token-budget handling")
    if blocker.get("root_cause_classification") != "output_budget_exhausted_by_thinking_before_json_completion":
        failures.append("unexpected blocker root-cause classification")
    if blocker.get("original_max_output_tokens") != OLD_MAX_OUTPUT_TOKENS:
        failures.append("old max output token mismatch")
    if blocker.get("thoughts_tokens") != 241 or blocker.get("candidate_tokens") != 11:
        failures.append("iter94 usage analysis mismatch")
    if blocker.get("response_text_parseable_json") is not False:
        failures.append("iter94 raw response should be unparseable JSON")


def audit_prompt_recovery(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = packets["summary"]
    prompt_manifest = packets["prompt_manifest"]
    leakage = packets["leakage"]
    plan = packets["plan"]
    retry = packets["retry"]
    if prompt_manifest.get("prompt_count") != 14:
        failures.append("recovered prompt count must be 14")
    if prompt_manifest.get("labels_excluded_from_recovered_prompts") is not True:
        failures.append("prompt manifest says labels were not excluded")
    if leakage.get("labels_excluded_from_recovered_prompts") is not True or leakage.get("findings"):
        failures.append("label leakage check failed")
    if summary.get("labels_excluded_from_recovered_prompts") is not True:
        failures.append("summary label exclusion mismatch")
    if plan.get("recovered_generation_config", {}).get("maxOutputTokens") != RECOVERED_MAX_OUTPUT_TOKENS:
        failures.append("recovered maxOutputTokens mismatch")
    if plan.get("old_generation_config", {}).get("maxOutputTokens") != OLD_MAX_OUTPUT_TOKENS:
        failures.append("old maxOutputTokens mismatch in recovery plan")
    if plan.get("directly_addresses_iter94_blocker") is not True:
        failures.append("recovery plan does not directly address blocker")
    if "stop on any parse failure and publish blocked evidence without unregistered retries" not in plan.get(
        "prompt_recovery_actions", []
    ):
        failures.append("recovery plan missing stop-on-parse-failure action")
    if retry.get("next_gate") != str(NEXT_GATE):
        failures.append("retry envelope next gate mismatch")
    if retry.get("next_gate_pre_registered") is not True:
        failures.append("retry next gate is not pre-registered")
    if retry.get("future_provider_call_ceiling") != FUTURE_PROVIDER_CALL_CEILING:
        failures.append("future provider call ceiling mismatch")
    if decimal_value(retry.get("future_provider_spend_ceiling_usd")) != FUTURE_PROVIDER_SPEND_CEILING:
        failures.append("future provider spend ceiling mismatch")
    if retry.get("future_generation_config", {}).get("maxOutputTokens") != RECOVERED_MAX_OUTPUT_TOKENS:
        failures.append("retry generation config maxOutputTokens mismatch")
    if decimal_value(retry.get("estimated_worst_case_cost_usd")) > FUTURE_PROVIDER_SPEND_CEILING:
        failures.append("estimated worst-case retry cost exceeds ceiling")
    prompt_rows = prompt_manifest.get("recovered_prompt_rows", [])
    if not isinstance(prompt_rows, list) or len(prompt_rows) != 14:
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
            "output exactly one minified JSON object",
            "rationale <= 160 chars",
            "decisive_evidence <= 4 items",
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
        "provider calls in iter95: `0`",
        "provider spend in iter95: `$0.00000000`",
        "private labels excluded from recovered prompts: `true`",
        "benchmark/model/SOTA claim: `false`",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "Iter95 did not call a provider.",
        "old `256` output-token ceiling",
        "recovered design raises the output ceiling to `2048`",
        "No benchmark, model-superiority, production/live-domain, or state-of-the-art result",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "provider LLM judge prompt-budget recovery: pass",
        "iter94_validation_clean=true",
        "provider_api_calls=0",
        "provider_cost_usd=0.00000000",
        "recovered_prompt_count=14",
        "labels_excluded_from_recovered_prompts=true",
        "recovered_max_output_tokens=2048",
        "benchmark_model_sota_claimed=false",
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
            "iter94": load_json(ITER94_VALIDATION),
            "blocker": load_json(BLOCKER_ANALYSIS),
            "prompt_manifest": load_json(PROMPT_MANIFEST),
            "leakage": load_json(LEAKAGE),
            "plan": load_json(RECOVERY_PLAN),
            "retry": load_json(RETRY),
            "boundary": load_json(BOUNDARY),
            "redaction": load_json(REDACTION),
        }
        audit_schemas(packets, failures)
        audit_summary_and_iter94(packets, failures)
        audit_prompt_recovery(packets, failures)
        audit_claims_receipt_hashes_and_text(packets["summary"], failures)
    if failures:
        print("iter95 provider LLM judge prompt-budget recovery audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter95 provider LLM judge prompt-budget recovery audit: pass")
    print("provider_api_calls=0")
    print("provider_cost_usd=0.00000000")
    print("recovered_prompt_count=14")
    print("recovered_max_output_tokens=2048")
    print(f"next_gate={NEXT_GATE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
