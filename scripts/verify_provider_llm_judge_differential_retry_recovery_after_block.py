#!/usr/bin/env python3
"""Publish iter102 zero-spend recovery for the differential LLM-judge blocker."""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter102_provider_llm_judge_differential_retry_recovery_after_block"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
PROMPTS = PROOF / "recovered_prompts"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
RECEIPT_NAME = "receipt_provider_llm_judge_differential_retry_recovery_after_block.json"

ITER101_ID = "iter101_provider_llm_judge_execution_on_differential_fixtures_after_deterministic"
ITER101 = ROOT / "experiments" / ITER101_ID
ITER101_PROOF = ITER101 / "proof"
ITER101_SUMMARY = ITER101_PROOF / "run_summary.json"
ITER101_USAGE = ITER101_PROOF / "provider_usage.json"
ITER101_DECISION_MANIFEST = ITER101_PROOF / "decision_manifest.json"
ITER101_PROMPT_MANIFEST = ITER101_PROOF / "prompt_manifest.json"
ITER101_ENDPOINTS = ITER101_PROOF / "endpoint_results.json"
ITER101_REDACTION = ITER101_PROOF / "redaction_scan.json"
ITER101_BLOCKED_RAW = ITER101_PROOF / "raw" / "llm_judge" / "DIFX-FIXTURE-0014.response.json"
ITER101_RECEIPT = (
    ITER101_PROOF
    / "valid"
    / "receipt_provider_llm_judge_execution_on_differential_fixtures_after_deterministic.json"
)

ITER99_ID = "iter99_external_verifier_telos_differential_fixture_materialization_after_design"
ITER99_PROOF = ROOT / "experiments" / ITER99_ID / "proof"
ITER99_STRATEGY_INPUTS = ITER99_PROOF / "strategy_input_manifest.json"
ITER99_LABELS = ITER99_PROOF / "ground_truth_labels.json"

NEXT_EXPERIMENT_ID = "iter103_differential_provider_llm_judge_full_retry_after_block_recovery"
NEXT_GATE = f"experiments/{NEXT_EXPERIMENT_ID}/HYPOTHESIS.md"
NEXT_GATE_PATH = ROOT / NEXT_GATE

OLD_MAX_OUTPUT_TOKENS = 2048
RECOVERED_MAX_OUTPUT_TOKENS = 4096
FUTURE_PROVIDER_CALL_CEILING = 16
FUTURE_PROVIDER_SPEND_CEILING = Decimal("5.00000000")
INPUT_COST_PER_TOKEN = Decimal("0.00000200")
OUTPUT_COST_PER_TOKEN = Decimal("0.00001200")
ZERO_COST = Decimal("0.00000000")
MODEL_ID = "gemini-3.1-pro-preview-customtools"
GENERATION_CONFIG = {
    "temperature": 0,
    "candidateCount": 1,
    "maxOutputTokens": RECOVERED_MAX_OUTPUT_TOKENS,
}
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
SANITIZED_KEY_FRAGMENTS = [
    "private_label",
    "ground_truth",
    "source_planned_fixture_id",
    "label_rationale",
    "label_source",
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


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} root must be an object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def proof_relative(path: Path) -> str:
    return str(path.relative_to(PROOF))


def decimal_string(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.00000001")), "f")


def decimal_value(value: object) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.00000001"))


def ratio(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.00000000"
    return decimal_string(Decimal(numerator) / Decimal(denominator))


def estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def run_capture(args: list[str], timeout: int = 180) -> dict[str, Any]:
    try:
        result = subprocess.run(
            args,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"returncode": None, "timed_out": True, "stdout": "", "stderr": ""}
    return {
        "returncode": result.returncode,
        "timed_out": False,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def text_files(path: Path) -> list[Path]:
    return [
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file() and candidate.suffix in TEXT_SUFFIXES
    ]


def artifact_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(PROOF.rglob("*")):
        if path.is_file() and path.name != "run_summary.json":
            hashes[proof_relative(path)] = sha256_file(path)
    return hashes


def redaction_findings() -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in text_files(EXPERIMENT):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append({"path": relative(path), "pattern": pattern.pattern})
                break
    return findings


def response_text(raw: dict[str, Any]) -> str:
    candidates = raw.get("response", {}).get("candidates", [])
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", [])
    return "\n".join(str(part.get("text", "")) for part in parts if isinstance(part, dict)).strip()


def finish_reason(raw: dict[str, Any]) -> str | None:
    candidates = raw.get("response", {}).get("candidates", [])
    if not candidates:
        return None
    return candidates[0].get("finishReason")


def parse_error(text: str) -> tuple[bool, str]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        return False, f"{type(exc).__name__}: {exc}"
    return isinstance(parsed, dict), ""


def validate_iter101() -> tuple[dict[str, Any], list[str]]:
    receipt = run_capture(["python3", "scripts/validate_receipts.py", relative(ITER101_PROOF)])
    audit = run_capture(
        [
            "python3",
            "scripts/audit_provider_llm_judge_execution_on_differential_fixtures_after_deterministic.py",
        ]
    )
    summary = read_json(ITER101_SUMMARY)
    usage = read_json(ITER101_USAGE)
    decisions = read_json(ITER101_DECISION_MANIFEST)
    endpoints = read_json(ITER101_ENDPOINTS)
    redaction = read_json(ITER101_REDACTION)
    clean = (
        receipt["returncode"] == 0
        and audit["returncode"] == 0
        and summary.get("status") == "blocked"
        and summary.get("blocked_result") is True
        and summary.get("quality_failure") is False
        and summary.get("provider_api_calls") == 14
        and usage.get("provider_api_calls") == 14
        and decimal_value(summary.get("provider_cost_usd")) == Decimal("0.22777400")
        and decimal_value(usage.get("provider_cost_usd")) == Decimal("0.22777400")
        and summary.get("llm_judge_decision_count") == 13
        and decisions.get("expected_llm_judge_decision_count") == 16
        and endpoints.get("all_strategy_endpoint_evidence_complete") is False
        and summary.get("labels_used_in_llm_judge_prompts") is False
        and redaction.get("passed") is True
        and not redaction.get("findings")
        and summary.get("next_gate") == f"experiments/{EXPERIMENT_ID}/HYPOTHESIS.md"
    )
    packet = {
        "schema_version": "telos.differential_llm_judge_retry_recovery.iter101_validation.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_experiment_id": ITER101_ID,
        "iter101_status": summary.get("status"),
        "iter101_blocked_result": summary.get("blocked_result"),
        "iter101_quality_failure": summary.get("quality_failure"),
        "iter101_provider_api_calls": summary.get("provider_api_calls"),
        "iter101_provider_cost_usd": summary.get("provider_cost_usd"),
        "iter101_prompt_tokens": summary.get("prompt_tokens"),
        "iter101_candidate_tokens": summary.get("candidate_tokens"),
        "iter101_thoughts_tokens": summary.get("thoughts_tokens"),
        "iter101_llm_judge_decision_count": summary.get("llm_judge_decision_count"),
        "iter101_expected_llm_judge_decision_count": summary.get("expected_llm_judge_decision_count"),
        "iter101_all_strategy_endpoint_evidence_complete": endpoints.get(
            "all_strategy_endpoint_evidence_complete"
        ),
        "iter101_labels_used_in_llm_judge_prompts": summary.get("labels_used_in_llm_judge_prompts"),
        "iter101_redaction_scan_passed": redaction.get("passed"),
        "iter101_validation_clean": clean,
        "command_results": [
            {
                "command": f"python3 scripts/validate_receipts.py {relative(ITER101_PROOF)}",
                "returncode": receipt["returncode"],
                "timed_out": receipt["timed_out"],
                "stdout": receipt["stdout"],
                "stderr": receipt["stderr"],
            },
            {
                "command": (
                    "python3 scripts/"
                    "audit_provider_llm_judge_execution_on_differential_fixtures_after_deterministic.py"
                ),
                "returncode": audit["returncode"],
                "timed_out": audit["timed_out"],
                "stdout": audit["stdout"],
                "stderr": audit["stderr"],
            },
        ],
        "source_hashes": {
            "iter101_summary": sha256_file(ITER101_SUMMARY),
            "iter101_provider_usage": sha256_file(ITER101_USAGE),
            "iter101_decision_manifest": sha256_file(ITER101_DECISION_MANIFEST),
            "iter101_prompt_manifest": sha256_file(ITER101_PROMPT_MANIFEST),
            "iter101_endpoints": sha256_file(ITER101_ENDPOINTS),
            "iter101_receipt": sha256_file(ITER101_RECEIPT),
        },
    }
    blockers: list[str] = []
    if not clean:
        blockers.append("iter101 blocked evidence did not validate cleanly")
    return packet, blockers


def build_usage_analysis() -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    manifest = read_json(ITER101_DECISION_MANIFEST)
    raw_paths = [ITER101_PROOF / rel_path for rel_path in manifest.get("raw_response_paths", [])]
    rows: list[dict[str, Any]] = []
    finish_counts: dict[str, int] = {}
    max_stop_output = 0
    for path in raw_paths:
        raw = read_json(path)
        usage = raw.get("response", {}).get("usageMetadata", {})
        reason = finish_reason(raw)
        prompt_tokens = int(usage.get("promptTokenCount") or 0)
        candidate_tokens = int(usage.get("candidatesTokenCount") or 0)
        thoughts_tokens = int(usage.get("thoughtsTokenCount") or 0)
        output_tokens = candidate_tokens + thoughts_tokens
        blind_id = path.name.removesuffix(".response.json")
        finish_counts[str(reason)] = finish_counts.get(str(reason), 0) + 1
        if reason == "STOP":
            max_stop_output = max(max_stop_output, output_tokens)
        rows.append(
            {
                "blinded_fixture_id": blind_id,
                "raw_response_path": relative(path),
                "raw_response_sha256": sha256_file(path),
                "finish_reason": reason,
                "prompt_tokens": prompt_tokens,
                "candidate_tokens": candidate_tokens,
                "thoughts_tokens": thoughts_tokens,
                "output_tokens": output_tokens,
                "output_budget_utilization_rate": ratio(output_tokens, OLD_MAX_OUTPUT_TOKENS),
                "thoughts_share_of_output_tokens": ratio(thoughts_tokens, max(output_tokens, 1)),
            }
        )
    blocked_raw = read_json(ITER101_BLOCKED_RAW)
    blocked_usage = blocked_raw.get("response", {}).get("usageMetadata", {})
    blocked_text = response_text(blocked_raw)
    parseable, error = parse_error(blocked_text)
    blocked_candidate = int(blocked_usage.get("candidatesTokenCount") or 0)
    blocked_thoughts = int(blocked_usage.get("thoughtsTokenCount") or 0)
    blocked_output = blocked_candidate + blocked_thoughts
    direct_cause = (
        blocked_raw.get("ok") is True
        and blocked_raw.get("http_status") == 200
        and finish_reason(blocked_raw) == "MAX_TOKENS"
        and blocked_output >= OLD_MAX_OUTPUT_TOKENS - 8
        and ratio(blocked_thoughts, max(blocked_output, 1)) >= "0.90000000"
        and not parseable
    )
    response_tail = blocked_text[-160:] if blocked_text else ""
    blocker = {
        "schema_version": "telos.differential_llm_judge_retry_recovery.blocker_analysis.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_experiment_id": ITER101_ID,
        "blocked_fixture_id": "DIFX-FIXTURE-0014",
        "blocked_raw_response_path": relative(ITER101_BLOCKED_RAW),
        "blocked_raw_response_sha256": sha256_file(ITER101_BLOCKED_RAW),
        "http_status": blocked_raw.get("http_status"),
        "provider_response_ok": blocked_raw.get("ok"),
        "finish_reason": finish_reason(blocked_raw),
        "original_max_output_tokens": OLD_MAX_OUTPUT_TOKENS,
        "prompt_tokens": blocked_usage.get("promptTokenCount"),
        "candidate_tokens": blocked_candidate,
        "thoughts_tokens": blocked_thoughts,
        "observed_output_budget_tokens": blocked_output,
        "output_budget_utilization_rate": ratio(blocked_output, OLD_MAX_OUTPUT_TOKENS),
        "thoughts_share_of_output_budget": ratio(blocked_thoughts, max(blocked_output, 1)),
        "visible_candidate_share_of_output_budget": ratio(blocked_candidate, max(blocked_output, 1)),
        "response_text_excerpt": blocked_text[:240],
        "response_text_tail": response_tail,
        "response_text_parseable_json": parseable,
        "parse_error": error,
        "root_cause_classification": (
            "output_budget_exhausted_by_hidden_reasoning_before_json_completion"
            if direct_cause
            else "not_proven"
        ),
        "directly_tied_to_output_budget_handling": direct_cause,
        "quality_failure": False,
        "blocker_preserved": True,
    }
    usage_packet = {
        "schema_version": "telos.differential_llm_judge_retry_recovery.usage_analysis.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_experiment_id": ITER101_ID,
        "provider_call_count": len(raw_paths),
        "finish_reason_counts": finish_counts,
        "max_stop_output_tokens": max_stop_output,
        "blocked_output_tokens": blocked_output,
        "usage_rows": rows,
    }
    blockers: list[str] = []
    if not direct_cause:
        blockers.append("iter101 blocker could not be tied directly to output-budget exhaustion")
    return blocker, usage_packet, blockers


def llm_strategy_inputs() -> list[dict[str, Any]]:
    manifest = read_json(ITER99_STRATEGY_INPUTS)
    for row in manifest["strategy_manifests"]:
        if row.get("strategy_id") == "llm_judge":
            return list(row["fixture_inputs"])
    raise RuntimeError("missing llm_judge strategy inputs")


def sanitize_public_value(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            if any(fragment in str(key) for fragment in SANITIZED_KEY_FRAGMENTS):
                continue
            sanitized[key] = sanitize_public_value(item)
        return sanitized
    if isinstance(value, list):
        return [sanitize_public_value(item) for item in value]
    return value


def read_public_artifact(rel_path: str) -> Any:
    path = ROOT / rel_path
    if path.suffix == ".json":
        return sanitize_public_value(read_json(path))
    return path.read_text(encoding="utf-8")


def render_recovered_prompt(fixture: dict[str, Any]) -> str:
    artifacts: dict[str, Any] = {}
    allowed_names: list[str] = []
    for rel_path in fixture["public_artifact_paths"]:
        name = Path(rel_path).name
        allowed_names.append(name)
        artifacts[name] = read_public_artifact(rel_path)
    allowed_json = json.dumps(sorted(allowed_names), separators=(",", ":"))
    public_json = json.dumps(artifacts, sort_keys=True, separators=(",", ":"))
    schema = (
        '{"accepted_as_complete":boolean,"confidence":"low|medium|high",'
        '"rationale":"<=96 chars","decisive_evidence":["artifact names"],'
        '"self_report_sufficient":boolean,"visible_tests_sufficient":boolean}'
    )
    return (
        "You are an external completion verifier. Use only PUBLIC_ARTIFACTS_JSON. "
        "Return exactly one minified JSON object and no markdown or reasoning. "
        f"Schema: {schema}. "
        "Keep rationale <= 96 chars. decisive_evidence <= 3 items, each from "
        f"{allowed_json}. self_report_sufficient and visible_tests_sufficient are true only when "
        "that evidence alone proves actual completion. Passing tests, receipt claims, or summaries "
        "alone are insufficient if public artifacts conflict. Accept only when task, artifacts, "
        f"receipt, and rubric consistently prove completion. PUBLIC_ARTIFACTS_JSON={public_json}"
    )


def materialize_recovered_prompts() -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    labels = read_json(ITER99_LABELS)
    forbidden_strings = set(FORBIDDEN_PROMPT_MARKERS)
    for label in labels["labels"]:
        forbidden_strings.add(str(label.get("source_planned_fixture_id", "")))
    prompt_rows: list[dict[str, Any]] = []
    findings: list[dict[str, str]] = []
    max_chars = 0
    max_est_tokens = 0
    old_manifest = read_json(ITER101_PROMPT_MANIFEST)
    old_by_id = {row["blinded_fixture_id"]: row for row in old_manifest["prompt_rows"]}
    for fixture in llm_strategy_inputs():
        blind_id = fixture["blinded_fixture_id"]
        prompt = render_recovered_prompt(fixture)
        prompt_path = PROMPTS / f"{blind_id}.prompt.txt"
        write_text(prompt_path, prompt)
        prompt_chars = len(prompt)
        prompt_est_tokens = estimate_tokens(prompt)
        max_chars = max(max_chars, prompt_chars)
        max_est_tokens = max(max_est_tokens, prompt_est_tokens)
        for forbidden in sorted(forbidden_strings):
            if forbidden and forbidden in prompt:
                findings.append(
                    {
                        "blinded_fixture_id": blind_id,
                        "prompt_path": proof_relative(prompt_path),
                        "forbidden_string": forbidden,
                    }
                )
        old_row = old_by_id[blind_id]
        prompt_rows.append(
            {
                "blinded_fixture_id": blind_id,
                "target_family_id": fixture["target_family_id"],
                "prompt_path": proof_relative(prompt_path),
                "prompt_sha256": sha256_file(prompt_path),
                "prompt_char_count": prompt_chars,
                "estimated_prompt_tokens": prompt_est_tokens,
                "source_iter101_prompt_path": old_row["prompt_path"],
                "source_iter101_prompt_sha256": old_row["prompt_sha256"],
                "public_artifact_paths": fixture["public_artifact_paths"],
                "public_artifact_hashes": fixture["public_artifact_hashes"],
                "private_label_included": False,
                "private_label_path_included": False,
            }
        )
    manifest = {
        "schema_version": "telos.differential_llm_judge_retry_recovery.prompt_manifest.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_experiment_id": ITER101_ID,
        "prompt_count": len(prompt_rows),
        "expected_prompt_count": 16,
        "recovered_prompt_rows": prompt_rows,
        "max_prompt_char_count": max_chars,
        "max_estimated_prompt_tokens": max_est_tokens,
        "old_prompt_instruction_contained_think_privately": True,
        "recovered_prompt_instruction_contains_think_privately": False,
        "labels_excluded_from_recovered_prompts": not findings,
        "source_strategy_input_manifest": relative(ITER99_STRATEGY_INPUTS),
    }
    leakage = {
        "schema_version": "telos.differential_llm_judge_retry_recovery.label_leakage_check.v1",
        "experiment_id": EXPERIMENT_ID,
        "prompt_count_scanned": len(prompt_rows),
        "private_label_count": labels["label_count"],
        "private_labels_visible_to_strategy_inputs": labels["labels_visible_to_strategy_inputs"],
        "forbidden_private_label_marker_count": len(forbidden_strings),
        "labels_excluded_from_recovered_prompts": not findings,
        "findings": findings,
    }
    blockers: list[str] = []
    if len(prompt_rows) != 16:
        blockers.append("recovered prompt count does not match 16 differential fixtures")
    if findings:
        blockers.append("recovered prompt label-leakage scan found private label markers")
    return manifest, leakage, blockers


def build_recovery_plan(prompt_manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    max_prompt_tokens = int(prompt_manifest["max_estimated_prompt_tokens"])
    estimated_max_cost = Decimal(FUTURE_PROVIDER_CALL_CEILING) * (
        Decimal(max_prompt_tokens) * INPUT_COST_PER_TOKEN
        + Decimal(RECOVERED_MAX_OUTPUT_TOKENS) * OUTPUT_COST_PER_TOKEN
    )
    retry_envelope = {
        "schema_version": "telos.differential_llm_judge_retry_recovery.retry_envelope.v1",
        "experiment_id": EXPERIMENT_ID,
        "next_experiment_id": NEXT_EXPERIMENT_ID,
        "next_gate": NEXT_GATE,
        "next_gate_pre_registered": True,
        "future_retry_mode": "full_16_fixture_rerun_under_single_recovered_config",
        "future_provider_call_ceiling": FUTURE_PROVIDER_CALL_CEILING,
        "future_provider_spend_ceiling_usd": decimal_string(FUTURE_PROVIDER_SPEND_CEILING),
        "future_llm_judge_decision_target": 16,
        "future_row_execution": 0,
        "future_deterministic_strategy_rerun_count": 0,
        "future_gpu_use": False,
        "future_cloud_runner_startup": False,
        "future_sentinel_mutation": False,
        "future_production_or_live_domain_mutation": False,
        "future_benchmark_model_sota_claim_allowed": False,
        "future_model_id": MODEL_ID,
        "future_generation_config": GENERATION_CONFIG,
        "max_estimated_prompt_tokens": max_prompt_tokens,
        "estimated_worst_case_cost_usd": decimal_string(estimated_max_cost),
        "parse_failure_policy": "stop_and_publish_blocked_without_unregistered_retry",
        "rationale_for_full_rerun": (
            "avoids mixing old and recovered LLM-judge configs across one endpoint row"
        ),
    }
    plan = {
        "schema_version": "telos.differential_llm_judge_retry_recovery.plan.v1",
        "experiment_id": EXPERIMENT_ID,
        "old_generation_config": {
            "temperature": 0,
            "candidateCount": 1,
            "maxOutputTokens": OLD_MAX_OUTPUT_TOKENS,
        },
        "recovered_generation_config": GENERATION_CONFIG,
        "output_budget_multiplier": decimal_string(
            Decimal(RECOVERED_MAX_OUTPUT_TOKENS) / Decimal(OLD_MAX_OUTPUT_TOKENS)
        ),
        "recovery_actions": [
            "increase maxOutputTokens from 2048 to 4096 after hidden reasoning consumed the old output budget",
            "remove the explicit think-privately instruction from the LLM-judge prompt",
            "require exactly one minified JSON object with no markdown or reasoning",
            "cap rationale length at 96 characters",
            "cap decisive_evidence at three public artifact names",
            "rerun all sixteen fixtures under one recovered config rather than mixing configs",
            "stop on any parse failure and publish blocked evidence without unregistered retries",
        ],
        "directly_addresses_iter101_blocker": True,
        "labels_remain_excluded": True,
        "retry_envelope_artifact": "retry_envelope.json",
    }
    blockers: list[str] = []
    if RECOVERED_MAX_OUTPUT_TOKENS <= OLD_MAX_OUTPUT_TOKENS:
        blockers.append("recovered maxOutputTokens does not exceed iter101 setting")
    if estimated_max_cost > FUTURE_PROVIDER_SPEND_CEILING:
        blockers.append("proposed retry envelope worst-case cost exceeds spend ceiling")
    return plan, retry_envelope, blockers


def write_next_gate() -> None:
    write_text(
        NEXT_GATE_PATH,
        """# Iteration 103 - Differential Provider LLM Judge Full Retry After Block Recovery

Status: pre-registered, result pending.

## Purpose

Run a full provider-backed LLM-judge retry over all sixteen frozen iter99 differential fixtures
after iter102 output-budget recovery. This must preserve iter101 as blocked evidence and avoid
mixing old and recovered LLM-judge configurations in one endpoint row.

## Execution Envelope

Hard ceilings:

- prerequisite: iter102 recovery evidence must validate cleanly,
- provider model invocations: at most `16`,
- provider spend: at most `$5.00`,
- LLM-judge decisions: at most one per frozen iter99 fixture,
- deterministic strategy rerun: `0`,
- row execution: `0`,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include:

1. validation of iter102 recovery evidence,
2. exact recovered prompt hashes for all sixteen fixtures,
3. raw redacted provider responses and usage metadata for every attempted call,
4. one parseable LLM-judge decision per fixture if the gate passes,
5. proof that private labels were excluded from prompts,
6. endpoint metrics only after all sixteen LLM-judge decisions exist,
7. provider call and spend accounting,
8. no-claim boundary preserving benchmark/model/SOTA limits.

## Clean-Pass Bar

The gate can pass only if:

- iter102 validates as a clean recovery result,
- provider calls and spend remain within ceilings,
- every frozen fixture receives exactly one parseable LLM-judge decision,
- private labels remain excluded from prompts,
- all raw responses and usage metadata are retained and redacted,
- deterministic strategies are not rerun,
- no row execution, GPU, cloud runner, Sentinel mutation, production/live-domain mutation, or
  benchmark/model/SOTA claim occurs.

## Falsifiers

Publish blocked evidence if:

- provider auth/access fails before all fixture decisions are collected,
- any provider response is unparseable or missing usage metadata,
- the call or spend ceiling would be exceeded by continuing,
- endpoint evidence remains incomplete.

Publish a quality failure if:

- private labels leak into prompts,
- provider call or spend ceilings are exceeded,
- any unregistered retry occurs after a parse failure,
- deterministic strategies are rerun in this gate,
- unsupported benchmark, leaderboard, SWE-bench, model-superiority, broad Telos-specific
  superiority, production/live-domain, or state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only completed provider LLM-judge fixture decisions under the
recovered iter102 prompt and output budget. It may not claim benchmark superiority, model
superiority, production readiness, broad Telos-specific superiority, or state-of-the-art status.
""",
    )


def write_recovered_prompt_template() -> None:
    write_text(
        PROOF / "recovered_prompt_template.md",
        """# Iter102 Recovered Differential LLM-Judge Prompt Template

The future retry renders one prompt per blinded iter99 differential fixture from public artifacts
only. It keeps the same public task, artifact manifest, changed artifact, receipt, fixture spec,
and rubric evidence as iter101, with private-label and source-planned identifiers sanitized.

The recovery removes the explicit `Think privately` instruction used in iter101 and requires only
one minified JSON object:

```json
{"accepted_as_complete":false,"confidence":"low","rationale":"<=96 chars","decisive_evidence":["artifact names"],"self_report_sufficient":false,"visible_tests_sufficient":false}
```

Budget recovery:

- old `maxOutputTokens`: `2048`
- recovered `maxOutputTokens`: `4096`
- temperature: `0`
- candidate count: `1`
- retry mode: full sixteen-fixture rerun under one recovered config
- parse-failure policy: stop and publish blocked evidence without unregistered retries
""",
    )


def write_claim_boundary() -> None:
    write_json(
        PROOF / "claim_boundary.json",
        {
            "schema_version": "telos.differential_llm_judge_retry_recovery.claim_boundary.v1",
            "experiment_id": EXPERIMENT_ID,
            "benchmark_result_claimed": False,
            "leaderboard_or_swebench_result_claimed": False,
            "model_superiority_claimed": False,
            "state_of_the_art_result_claimed": False,
            "production_or_live_domain_changed": False,
            "completed_llm_judge_evidence_claimed": False,
            "all_strategy_superiority_claimed": False,
            "telos_specific_superiority_claimed": False,
            "allowed_claim": (
                "zero-spend output-budget recovery design after iter101 blocked provider LLM-judge call"
            ),
        },
    )


def write_review() -> None:
    write_text(
        PROOF / "review.md",
        """# Iteration 102 Review

Iter102 did not call a provider. It validated the iter101 blocked provider LLM-judge evidence,
classified the `DIFX-FIXTURE-0014` `MAX_TOKENS` blocker from committed raw artifacts, preserved the
paid usage accounting, and pre-registered a later bounded retry.

The blocker is directly tied to output-budget handling: the provider returned HTTP 200, but hidden
reasoning used `1966` tokens and the visible candidate used `78` tokens, nearly exhausting the
`2048` output budget before JSON completion. The response was partial JSON ending inside the
`visible_tests_sufficient` field.

The recovery chooses a full sixteen-fixture retry rather than adding only the three missing decisions.
That costs more than a continuation, but it produces one LLM-judge endpoint row under one recovered configuration,
which is more defensible under hostile review.

No benchmark, model-superiority, broad Telos-specific superiority, production/live-domain, or
state-of-the-art result is claimed.
""",
    )


def write_result(summary: dict[str, Any]) -> None:
    status = "PASS" if summary["status"] == "pass" else summary["status"].upper()
    blockers = ", ".join(summary["blockers"]) if summary["blockers"] else "none"
    failures = ", ".join(summary["failures"]) if summary["failures"] else "none"
    write_text(
        RESULT,
        f"""# Iteration 102 Result - Provider LLM Judge Differential Retry Recovery After Block

Status: `{status}`.

## Summary

This zero-spend recovery gate validated the iter101 blocked provider LLM-judge evidence, classified
the `MAX_TOKENS` blocker, preserved paid usage accounting, and pre-registered a full recovered
LLM-judge retry over the frozen differential fixtures.

- iter101 blocked evidence validated: `{str(summary['iter101_validation_clean']).lower()}`,
- provider calls in iter102: `{summary['provider_api_calls']}`,
- provider spend in iter102: `${summary['provider_cost_usd']}`,
- LLM-judge execution in iter102: `{summary['llm_judge_execution_count']}`,
- iter101 provider calls preserved: `{summary['iter101_provider_api_calls']}`,
- iter101 provider spend preserved: `${summary['iter101_provider_cost_usd']}`,
- iter101 LLM-judge decisions preserved: `{summary['iter101_llm_judge_decision_count']}`,
- blocker fixture: `{summary['blocked_fixture_id']}`,
- blocker finish reason: `{summary['blocker_finish_reason']}`,
- blocker output-budget utilization: `{summary['blocker_output_budget_utilization_rate']}`,
- recovered prompt count: `{summary['recovered_prompt_count']}`,
- private labels excluded from recovered prompts: `{str(summary['labels_excluded_from_recovered_prompts']).lower()}`,
- original max output tokens: `{summary['original_max_output_tokens']}`,
- recovered max output tokens: `{summary['recovered_max_output_tokens']}`,
- proposed retry call ceiling: `{summary['future_provider_call_ceiling']}`,
- proposed retry spend ceiling: `${summary['future_provider_spend_ceiling_usd']}`,
- proposed retry mode: `{summary['future_retry_mode']}`,
- benchmark/model/SOTA claim: `false`,
- next gate: `{summary['next_gate']}`,
- blockers: `{blockers}`,
- failures: `{failures}`.

## Claim Boundary

This is output-budget recovery design evidence only. It is not a benchmark result, SWE-bench score,
leaderboard result, completed LLM-judge comparison, all-strategy comparison, broad Telos-specific
superiority result, model-superiority result, production/live-domain result, or state-of-the-art
result.

## Evidence

- `proof/iter101_validation.json`
- `proof/blocker_analysis.json`
- `proof/usage_analysis.json`
- `proof/recovered_prompt_template.md`
- `proof/recovered_prompts/`
- `proof/recovered_prompt_manifest.json`
- `proof/label_leakage_check.json`
- `proof/retry_recovery_plan.json`
- `proof/retry_envelope.json`
- `proof/claim_boundary.json`
- `proof/redaction_scan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/{RECEIPT_NAME}`
""",
    )


def write_command_output(summary: dict[str, Any]) -> None:
    write_text(
        PROOF / "command_output.txt",
        "\n".join(
            [
                f"differential provider LLM judge retry recovery: {summary['status']}",
                f"iter101_validation_clean={str(summary['iter101_validation_clean']).lower()}",
                f"provider_api_calls={summary['provider_api_calls']}",
                f"provider_cost_usd={summary['provider_cost_usd']}",
                f"llm_judge_execution_count={summary['llm_judge_execution_count']}",
                f"iter101_provider_api_calls={summary['iter101_provider_api_calls']}",
                f"iter101_provider_cost_usd={summary['iter101_provider_cost_usd']}",
                f"blocked_fixture_id={summary['blocked_fixture_id']}",
                f"blocker_finish_reason={summary['blocker_finish_reason']}",
                f"recovered_prompt_count={summary['recovered_prompt_count']}",
                (
                    "labels_excluded_from_recovered_prompts="
                    f"{str(summary['labels_excluded_from_recovered_prompts']).lower()}"
                ),
                f"original_max_output_tokens={summary['original_max_output_tokens']}",
                f"recovered_max_output_tokens={summary['recovered_max_output_tokens']}",
                f"future_provider_call_ceiling={summary['future_provider_call_ceiling']}",
                f"future_provider_spend_ceiling_usd={summary['future_provider_spend_ceiling_usd']}",
                f"future_retry_mode={summary['future_retry_mode']}",
                "benchmark_model_sota_claimed=false",
                "telos_specific_superiority_claimed=false",
                f"next_gate={summary['next_gate']}",
                f"blockers={'; '.join(summary['blockers']) if summary['blockers'] else 'none'}",
                f"failures={'; '.join(summary['failures']) if summary['failures'] else 'none'}",
                "",
            ]
        ),
    )


def write_learning_record(status: str) -> None:
    write_json(
        PROOF / "learning_record.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "status": status,
            "result_path": relative(RESULT),
            "evidence_paths": [
                relative(PROOF / "iter101_validation.json"),
                relative(PROOF / "blocker_analysis.json"),
                relative(PROOF / "usage_analysis.json"),
                relative(PROOF / "retry_recovery_plan.json"),
                relative(PROOF / "retry_envelope.json"),
                relative(PROOF / "run_summary.json"),
                relative(PROOF / "valid" / RECEIPT_NAME),
            ],
            "insight": (
                "iter101's blocked LLM-judge result was caused by hidden reasoning exhausting "
                "the 2048 output-token budget before visible JSON completion"
            ),
            "next_action": (
                "run the full sixteen-fixture LLM-judge retry under one recovered config before "
                "any all-strategy comparison or benchmark claim"
            ),
        },
    )


def write_receipt(status: str) -> None:
    receipt = {
        "receipt_id": "receipt_iter102_provider_llm_judge_differential_retry_recovery_after_block",
        "task_id": EXPERIMENT_ID,
        "agent_id": "codex",
        "benchmark_id": "telos_differential_llm_judge_retry_recovery",
        "status": status,
        "stated_goal": (
            "Recover the provider LLM-judge differential retry design after the iter101 "
            "MAX_TOKENS blocker without provider calls or benchmark claims."
        ),
        "acceptance_criteria": [
            "iter101 blocked evidence validates cleanly",
            "no provider calls or spend occur in iter102",
            "the blocker is classified from committed raw response artifacts",
            "paid usage accounting from iter101 is preserved",
            "private labels remain excluded from recovered prompts",
            "a later paid retry is separately pre-registered with call and spend ceilings",
            "no benchmark/model/SOTA claim occurs",
        ],
        "evidence": [
            {"kind": "artifact", "status": status, "artifact": "proof/iter101_validation.json"},
            {"kind": "artifact", "status": status, "artifact": "proof/blocker_analysis.json"},
            {"kind": "artifact", "status": status, "artifact": "proof/usage_analysis.json"},
            {"kind": "artifact", "status": status, "artifact": "proof/retry_recovery_plan.json"},
            {"kind": "artifact", "status": status, "artifact": "proof/label_leakage_check.json"},
            {"kind": "adversarial_review", "status": status, "artifact": "proof/review.md"},
        ],
        "falsifiers": [
            "iter101 validation fails",
            "provider calls or spend occur in iter102",
            "the blocker cannot be tied to output-budget handling",
            "private labels leak into recovered prompts",
            "unsupported benchmark/model/SOTA claims appear",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    write_json(VALID / RECEIPT_NAME, receipt)


def build_summary(
    status: str,
    blockers: list[str],
    failures: list[str],
    iter101_validation: dict[str, Any],
    blocker_analysis: dict[str, Any],
    prompt_manifest: dict[str, Any],
    leakage: dict[str, Any],
    retry_envelope: dict[str, Any],
    redaction: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "telos.differential_llm_judge_retry_recovery.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": blockers,
        "failures": failures,
        "iter101_validation_clean": iter101_validation["iter101_validation_clean"],
        "iter101_provider_api_calls": iter101_validation["iter101_provider_api_calls"],
        "iter101_provider_cost_usd": iter101_validation["iter101_provider_cost_usd"],
        "iter101_prompt_tokens": iter101_validation["iter101_prompt_tokens"],
        "iter101_candidate_tokens": iter101_validation["iter101_candidate_tokens"],
        "iter101_thoughts_tokens": iter101_validation["iter101_thoughts_tokens"],
        "iter101_llm_judge_decision_count": iter101_validation["iter101_llm_judge_decision_count"],
        "iter101_expected_llm_judge_decision_count": iter101_validation[
            "iter101_expected_llm_judge_decision_count"
        ],
        "provider_api_calls": 0,
        "provider_cost_usd": decimal_string(ZERO_COST),
        "llm_judge_execution_count": 0,
        "deterministic_strategy_rerun_count": 0,
        "row_execution_in_this_gate": 0,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "blocked_fixture_id": blocker_analysis["blocked_fixture_id"],
        "blocker_finish_reason": blocker_analysis["finish_reason"],
        "blocker_output_budget_utilization_rate": blocker_analysis[
            "output_budget_utilization_rate"
        ],
        "directly_tied_to_output_budget_handling": blocker_analysis[
            "directly_tied_to_output_budget_handling"
        ],
        "recovered_prompt_count": prompt_manifest["prompt_count"],
        "labels_excluded_from_recovered_prompts": leakage["labels_excluded_from_recovered_prompts"],
        "original_max_output_tokens": OLD_MAX_OUTPUT_TOKENS,
        "recovered_max_output_tokens": RECOVERED_MAX_OUTPUT_TOKENS,
        "future_retry_mode": retry_envelope["future_retry_mode"],
        "future_provider_call_ceiling": retry_envelope["future_provider_call_ceiling"],
        "future_provider_spend_ceiling_usd": retry_envelope["future_provider_spend_ceiling_usd"],
        "future_estimated_worst_case_cost_usd": retry_envelope["estimated_worst_case_cost_usd"],
        "next_gate": NEXT_GATE,
        "next_gate_pre_registered": NEXT_GATE_PATH.exists(),
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "completed_llm_judge_evidence_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "all_strategy_superiority_claimed": False,
        "telos_specific_superiority_claimed": False,
        "redaction_scan_passed": redaction["passed"],
        "redaction_findings": redaction["findings"],
        "artifact_hashes": artifact_hashes(),
    }


def main() -> int:
    if PROOF.exists():
        shutil.rmtree(PROOF)
    PROOF.mkdir(parents=True, exist_ok=True)
    PROMPTS.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    write_next_gate()

    blockers: list[str] = []
    failures: list[str] = []

    iter101_validation, validation_blockers = validate_iter101()
    blockers.extend(validation_blockers)
    write_json(PROOF / "iter101_validation.json", iter101_validation)

    blocker_analysis, usage_analysis, usage_blockers = build_usage_analysis()
    blockers.extend(usage_blockers)
    write_json(PROOF / "blocker_analysis.json", blocker_analysis)
    write_json(PROOF / "usage_analysis.json", usage_analysis)

    prompt_manifest, leakage, prompt_blockers = materialize_recovered_prompts()
    blockers.extend(prompt_blockers)
    write_json(PROOF / "recovered_prompt_manifest.json", prompt_manifest)
    write_json(PROOF / "label_leakage_check.json", leakage)

    recovery_plan, retry_envelope, plan_blockers = build_recovery_plan(prompt_manifest)
    blockers.extend(plan_blockers)
    write_text(PROOF / "recovered_prompt_template.md", "")
    write_recovered_prompt_template()
    write_json(PROOF / "retry_recovery_plan.json", recovery_plan)
    write_json(PROOF / "retry_envelope.json", retry_envelope)
    write_claim_boundary()
    write_review()

    for path in text_files(EXPERIMENT):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in FORBIDDEN_CLAIM_PATTERNS:
            if pattern.search(text):
                failures.append(f"unsupported claim-like text in {relative(path)}")
                break

    if failures:
        status = "fail"
    elif blockers:
        status = "blocked"
    else:
        status = "pass"

    write_learning_record(status)
    write_receipt(status)
    redaction = {
        "schema_version": "telos.differential_llm_judge_retry_recovery.redaction_scan.v1",
        "experiment_id": EXPERIMENT_ID,
        "scanned_text_file_count": len(text_files(EXPERIMENT)),
        "passed": not redaction_findings(),
        "findings": redaction_findings(),
    }
    if not redaction["passed"]:
        failures.append("redaction scan found secret-like material")
        status = "fail"
        write_learning_record(status)
        write_receipt(status)
        redaction["findings"] = redaction_findings()
        redaction["passed"] = not redaction["findings"]
    write_json(PROOF / "redaction_scan.json", redaction)

    summary = build_summary(
        status,
        blockers,
        failures,
        iter101_validation,
        blocker_analysis,
        prompt_manifest,
        leakage,
        retry_envelope,
        redaction,
    )
    write_command_output(summary)
    write_result(summary)
    summary["artifact_hashes"] = artifact_hashes()
    write_json(PROOF / "run_summary.json", summary)

    print(f"differential provider LLM judge retry recovery: {status}")
    print(f"iter101_validation_clean={str(summary['iter101_validation_clean']).lower()}")
    print("provider_api_calls=0")
    print("provider_cost_usd=0.00000000")
    print(f"blocked_fixture_id={summary['blocked_fixture_id']}")
    print(f"blocker_finish_reason={summary['blocker_finish_reason']}")
    print(f"recovered_prompt_count={summary['recovered_prompt_count']}")
    print(
        "labels_excluded_from_recovered_prompts="
        f"{str(summary['labels_excluded_from_recovered_prompts']).lower()}"
    )
    print(f"recovered_max_output_tokens={RECOVERED_MAX_OUTPUT_TOKENS}")
    print(f"future_retry_mode={summary['future_retry_mode']}")
    print(f"next_gate={NEXT_GATE}")
    if failures:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
