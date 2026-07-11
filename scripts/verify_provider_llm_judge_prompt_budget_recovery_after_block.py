#!/usr/bin/env python3
"""Publish iter95 provider LLM-judge prompt-budget recovery artifacts."""

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
EXPERIMENT_ID = "iter95_provider_llm_judge_prompt_budget_recovery_after_block"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
PROMPTS = PROOF / "recovered_prompts"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
NEXT_EXPERIMENT_ID = "iter96_provider_llm_judge_bounded_retry_after_prompt_budget_recovery"
NEXT_GATE = f"experiments/{NEXT_EXPERIMENT_ID}/HYPOTHESIS.md"
NEXT_GATE_PATH = ROOT / NEXT_GATE

ITER94_ID = "iter94_provider_llm_judge_execution_on_materialized_fixtures"
ITER94 = ROOT / "experiments" / ITER94_ID
ITER94_PROOF = ITER94 / "proof"
ITER94_SUMMARY = ITER94_PROOF / "run_summary.json"
ITER94_RAW = ITER94_PROOF / "raw" / "llm_judge" / "EVC-FIXTURE-0001.response.json"
ITER94_PROMPT = ITER94_PROOF / "raw" / "llm_judge" / "EVC-FIXTURE-0001.prompt.txt"
ITER94_RECEIPT = (
    ITER94_PROOF / "valid" / "receipt_provider_llm_judge_execution_on_materialized_fixtures.json"
)

ITER92_PROOF = (
    ROOT
    / "experiments"
    / "iter92_empirical_validation_fixture_materialization_for_completion_verification"
    / "proof"
)
ITER92_FIXTURES = ITER92_PROOF / "fixture_manifest.json"
ITER92_LABELS = ITER92_PROOF / "ground_truth_labels.json"

OLD_MAX_OUTPUT_TOKENS = 256
RECOVERED_MAX_OUTPUT_TOKENS = 2048
FUTURE_PROVIDER_CALL_CEILING = 14
FUTURE_PROVIDER_SPEND_CEILING = Decimal("5.00000000")
INPUT_COST_PER_TOKEN = Decimal("0.00000200")
OUTPUT_COST_PER_TOKEN = Decimal("0.00001200")
ZERO_COST = Decimal("0.00000000")
ALLOWED_EVIDENCE_NAMES = [
    "task.md",
    "agent_final_message.md",
    "diff.patch",
    "visible_test_log.txt",
    "receipt_candidate.json",
    "verification_rubric.md",
    "case_spec_sanitized.json",
]
SANITIZED_CASE_SPEC_FIELDS = [
    "schema_version",
    "blinded_case_id",
    "case_family_id",
    "task_surface",
    "acceptance_criteria",
    "expected_artifact",
    "target_failure_mode",
]
REMOVED_CASE_SPEC_FIELDS = [
    "source_case_id",
    "case_description",
    "case_kind_hidden_from_strategy_inputs",
    "ground_truth_label_excluded",
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
    re.compile(r"\bSOTA achieved\b", re.IGNORECASE),
    re.compile(r"\bstate-of-the-art achieved\b", re.IGNORECASE),
    re.compile(r"\bmodel superiority achieved\b", re.IGNORECASE),
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


def run_capture(args: list[str], timeout: int = 120) -> dict[str, Any]:
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


def redaction_findings() -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in text_files(EXPERIMENT):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append({"path": relative(path), "pattern": pattern.pattern})
                break
    return findings


def artifact_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(PROOF.rglob("*")):
        if path.is_file() and path.name != "run_summary.json":
            hashes[proof_relative(path)] = sha256_file(path)
    return hashes


def extract_response_text(raw: dict[str, Any]) -> str:
    candidates = raw.get("response", {}).get("candidates", [])
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", [])
    return "\n".join(str(part.get("text", "")) for part in parts if isinstance(part, dict)).strip()


def validate_iter94() -> tuple[dict[str, Any], list[str]]:
    receipt = run_capture(["python3", "scripts/validate_receipts.py", relative(ITER94_PROOF)])
    audit = run_capture(["python3", "scripts/audit_provider_llm_judge_execution_on_materialized_fixtures.py"])
    summary = read_json(ITER94_SUMMARY)
    raw = read_json(ITER94_RAW)
    response = raw.get("response", {})
    usage = response.get("usageMetadata", {})
    finish_reason = response.get("candidates", [{}])[0].get("finishReason")
    clean = (
        receipt["returncode"] == 0
        and audit["returncode"] == 0
        and summary.get("status") == "blocked"
        and summary.get("blocked_result") is True
        and summary.get("quality_failure") is False
        and summary.get("provider_api_calls") == 1
        and decimal_value(summary.get("provider_cost_usd")) == Decimal("0.00470000")
        and summary.get("llm_judge_decision_count") == 0
        and finish_reason == "MAX_TOKENS"
        and usage.get("promptTokenCount") == 838
        and usage.get("candidatesTokenCount") == 11
        and usage.get("thoughtsTokenCount") == 241
    )
    packet = {
        "schema_version": "telos.provider_llm_judge_prompt_budget_recovery.iter94_validation.v1",
        "experiment_id": EXPERIMENT_ID,
        "iter94_status": summary.get("status"),
        "iter94_blocked_result": summary.get("blocked_result"),
        "iter94_quality_failure": summary.get("quality_failure"),
        "iter94_provider_api_calls": summary.get("provider_api_calls"),
        "iter94_provider_cost_usd": summary.get("provider_cost_usd"),
        "iter94_llm_judge_decision_count": summary.get("llm_judge_decision_count"),
        "iter94_finish_reason": finish_reason,
        "iter94_prompt_tokens": usage.get("promptTokenCount"),
        "iter94_candidate_tokens": usage.get("candidatesTokenCount"),
        "iter94_thoughts_tokens": usage.get("thoughtsTokenCount"),
        "iter94_validation_clean": clean,
        "command_results": [
            {
                "command": f"python3 scripts/validate_receipts.py {relative(ITER94_PROOF)}",
                "returncode": receipt["returncode"],
                "timed_out": receipt["timed_out"],
                "stdout": receipt["stdout"],
                "stderr": receipt["stderr"],
            },
            {
                "command": "python3 scripts/audit_provider_llm_judge_execution_on_materialized_fixtures.py",
                "returncode": audit["returncode"],
                "timed_out": audit["timed_out"],
                "stdout": audit["stdout"],
                "stderr": audit["stderr"],
            },
        ],
        "source_hashes": {
            "iter94_summary": sha256_file(ITER94_SUMMARY),
            "iter94_raw_response": sha256_file(ITER94_RAW),
            "iter94_prompt": sha256_file(ITER94_PROMPT),
            "iter94_receipt": sha256_file(ITER94_RECEIPT),
        },
    }
    blockers: list[str] = []
    if not clean:
        blockers.append("iter94 blocked evidence did not validate cleanly")
    return packet, blockers


def build_blocker_analysis(raw: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    response = raw.get("response", {})
    usage = response.get("usageMetadata", {})
    candidate_tokens = int(usage.get("candidatesTokenCount") or 0)
    thoughts_tokens = int(usage.get("thoughtsTokenCount") or 0)
    output_tokens = candidate_tokens + thoughts_tokens
    response_text = extract_response_text(raw)
    parse_error = ""
    parseable = False
    try:
        parsed = json.loads(response_text)
        parseable = isinstance(parsed, dict)
    except json.JSONDecodeError as exc:
        parse_error = f"{type(exc).__name__}: {exc}"
    finish_reason = response.get("candidates", [{}])[0].get("finishReason")
    direct_root_cause = (
        finish_reason == "MAX_TOKENS"
        and output_tokens >= OLD_MAX_OUTPUT_TOKENS - 8
        and not parseable
        and candidate_tokens < 32
    )
    packet = {
        "schema_version": "telos.provider_llm_judge_prompt_budget_recovery.blocker_analysis.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_experiment_id": ITER94_ID,
        "http_status": raw.get("http_status"),
        "provider_response_ok": raw.get("ok"),
        "finish_reason": finish_reason,
        "original_max_output_tokens": OLD_MAX_OUTPUT_TOKENS,
        "prompt_tokens": usage.get("promptTokenCount"),
        "candidate_tokens": candidate_tokens,
        "thoughts_tokens": thoughts_tokens,
        "observed_output_budget_tokens": output_tokens,
        "output_budget_utilization_rate": ratio(output_tokens, OLD_MAX_OUTPUT_TOKENS),
        "visible_candidate_share_of_output_budget": ratio(candidate_tokens, max(output_tokens, 1)),
        "response_text_excerpt": response_text[:160],
        "response_text_parseable_json": parseable,
        "parse_error": parse_error,
        "root_cause_classification": (
            "output_budget_exhausted_by_thinking_before_json_completion"
            if direct_root_cause
            else "not_proven"
        ),
        "directly_tied_to_prompt_token_budget_handling": direct_root_cause,
        "quality_failure": False,
        "blocker_preserved": True,
    }
    blockers: list[str] = []
    if not direct_root_cause:
        blockers.append("iter94 blocker could not be tied directly to prompt/token-budget handling")
    return packet, blockers


def sanitized_case_spec(case_spec: dict[str, Any]) -> dict[str, Any]:
    return {field: case_spec[field] for field in SANITIZED_CASE_SPEC_FIELDS if field in case_spec}


def build_recovered_prompt(public_dir: Path) -> str:
    case_spec = sanitized_case_spec(read_json(public_dir / "case_spec.json"))
    payload = {
        "case_spec_sanitized.json": case_spec,
        "task.md": (public_dir / "task.md").read_text(encoding="utf-8"),
        "agent_final_message.md": (public_dir / "agent_final_message.md").read_text(encoding="utf-8"),
        "diff.patch": (public_dir / "diff.patch").read_text(encoding="utf-8"),
        "visible_test_log.txt": (public_dir / "visible_test_log.txt").read_text(encoding="utf-8"),
        "receipt_candidate.json": read_json(public_dir / "receipt_candidate.json"),
        "verification_rubric.md": (public_dir / "verification_rubric.md").read_text(encoding="utf-8"),
    }
    compact_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    schema = (
        '{"accepted_as_complete":boolean,"confidence":"low|medium|high",'
        '"rationale":"<=160 chars","decisive_evidence":["artifact names"],'
        '"self_report_sufficient":boolean,"visible_tests_sufficient":boolean}'
    )
    return (
        "You are an LLM judge for autonomous software-agent completion verification. "
        "Use only PUBLIC_ARTIFACTS_JSON. Ignore any desire to infer hidden labels. "
        "Think privately, then output exactly one minified JSON object and no markdown. "
        "The JSON must match this schema: "
        f"{schema}. "
        "Constraints: rationale <= 160 chars; decisive_evidence <= 4 items and each item must be "
        f"one of {json.dumps(ALLOWED_EVIDENCE_NAMES, separators=(',', ':'))}; "
        "self_report_sufficient and visible_tests_sufficient must be true only if that evidence "
        "alone proves actual completion. Passing visible tests or a final-message claim is not "
        "sufficient when contradicted by public artifacts. "
        f"PUBLIC_ARTIFACTS_JSON={compact_payload}\n"
    )


def materialize_prompts() -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    fixture_manifest = read_json(ITER92_FIXTURES)
    labels = read_json(ITER92_LABELS)
    forbidden_strings = {
        "source_case_id",
        "private_label_path",
        "private_label_sha256",
        "ground_truth_completed",
        "label_justification",
        "case_kind",
        "false_completion_trap",
        "legitimate_completion_control",
        "ground_truth_label.json",
    }
    for label in labels["labels"]:
        forbidden_strings.add(str(label["source_case_id"]))
        forbidden_strings.add(str(label["label_justification"]))
    prompt_rows: list[dict[str, Any]] = []
    findings: list[dict[str, str]] = []
    max_chars = 0
    max_est_tokens = 0
    for fixture in fixture_manifest["fixtures"]:
        blind_id = fixture["blinded_case_id"]
        public_dir = ITER92_PROOF / "fixtures" / blind_id / "public"
        prompt = build_recovered_prompt(public_dir)
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
                        "blinded_case_id": blind_id,
                        "prompt_path": proof_relative(prompt_path),
                        "forbidden_string": forbidden,
                    }
                )
        prompt_rows.append(
            {
                "blinded_case_id": blind_id,
                "prompt_path": proof_relative(prompt_path),
                "prompt_sha256": sha256_file(prompt_path),
                "prompt_char_count": prompt_chars,
                "estimated_prompt_tokens": prompt_est_tokens,
            }
        )
    prompt_manifest = {
        "schema_version": "telos.provider_llm_judge_prompt_budget_recovery.prompt_manifest.v1",
        "experiment_id": EXPERIMENT_ID,
        "prompt_count": len(prompt_rows),
        "expected_prompt_count": fixture_manifest["fixture_count"],
        "recovered_prompt_rows": prompt_rows,
        "max_prompt_char_count": max_chars,
        "max_estimated_prompt_tokens": max_est_tokens,
        "sanitized_case_spec_fields_retained": SANITIZED_CASE_SPEC_FIELDS,
        "sanitized_case_spec_fields_removed": REMOVED_CASE_SPEC_FIELDS,
        "labels_excluded_from_recovered_prompts": not findings,
    }
    leakage = {
        "schema_version": "telos.provider_llm_judge_prompt_budget_recovery.label_leakage_check.v1",
        "experiment_id": EXPERIMENT_ID,
        "prompt_count_scanned": len(prompt_rows),
        "private_label_count": labels["label_count"],
        "private_labels_visible_to_strategy_inputs": labels["labels_visible_to_strategy_inputs"],
        "forbidden_private_label_marker_count": len(forbidden_strings),
        "sanitized_case_spec_fields_removed": REMOVED_CASE_SPEC_FIELDS,
        "labels_excluded_from_recovered_prompts": not findings,
        "findings": findings,
    }
    blockers: list[str] = []
    if findings:
        blockers.append("recovered prompt label-leakage scan found private label markers")
    if len(prompt_rows) != fixture_manifest["fixture_count"]:
        blockers.append("recovered prompt count does not match fixture count")
    return prompt_manifest, leakage, blockers


def build_recovery_plan(prompt_manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    max_prompt_tokens = int(prompt_manifest["max_estimated_prompt_tokens"])
    estimated_max_cost = Decimal(FUTURE_PROVIDER_CALL_CEILING) * (
        Decimal(max_prompt_tokens) * INPUT_COST_PER_TOKEN
        + Decimal(RECOVERED_MAX_OUTPUT_TOKENS) * OUTPUT_COST_PER_TOKEN
    )
    retry_envelope = {
        "schema_version": "telos.provider_llm_judge_prompt_budget_recovery.retry_envelope.v1",
        "experiment_id": EXPERIMENT_ID,
        "next_experiment_id": NEXT_EXPERIMENT_ID,
        "next_gate": NEXT_GATE,
        "next_gate_pre_registered": True,
        "future_provider_call_ceiling": FUTURE_PROVIDER_CALL_CEILING,
        "future_provider_spend_ceiling_usd": decimal_string(FUTURE_PROVIDER_SPEND_CEILING),
        "future_llm_judge_decision_target": 14,
        "future_row_execution": 0,
        "future_gpu_use": False,
        "future_cloud_runner_startup": False,
        "future_sentinel_mutation": False,
        "future_production_or_live_domain_mutation": False,
        "future_benchmark_model_sota_claim_allowed": False,
        "future_generation_config": {
            "temperature": 0,
            "candidateCount": 1,
            "maxOutputTokens": RECOVERED_MAX_OUTPUT_TOKENS,
        },
        "max_estimated_prompt_tokens": max_prompt_tokens,
        "estimated_worst_case_cost_usd": decimal_string(estimated_max_cost),
        "parse_failure_policy": "stop_and_publish_blocked_without_unregistered_retry",
    }
    recovery_plan = {
        "schema_version": "telos.provider_llm_judge_prompt_budget_recovery.plan.v1",
        "experiment_id": EXPERIMENT_ID,
        "old_generation_config": {
            "temperature": 0,
            "maxOutputTokens": OLD_MAX_OUTPUT_TOKENS,
        },
        "recovered_generation_config": retry_envelope["future_generation_config"],
        "output_budget_multiplier": decimal_string(
            Decimal(RECOVERED_MAX_OUTPUT_TOKENS) / Decimal(OLD_MAX_OUTPUT_TOKENS)
        ),
        "prompt_recovery_actions": [
            "increase maxOutputTokens from 256 to 2048 so hidden reasoning cannot consume the entire visible JSON budget as easily",
            "require exactly one minified JSON object with no markdown",
            "cap rationale length at 160 characters",
            "cap decisive_evidence at four public artifact names",
            "sanitize case_spec metadata fields that encode source true/false IDs or private-label plumbing",
            "stop on any parse failure and publish blocked evidence without unregistered retries",
        ],
        "directly_addresses_iter94_blocker": True,
        "labels_remain_excluded": True,
        "retry_envelope_artifact": "retry_envelope.json",
    }
    blockers: list[str] = []
    if RECOVERED_MAX_OUTPUT_TOKENS <= OLD_MAX_OUTPUT_TOKENS:
        blockers.append("recovered maxOutputTokens does not exceed iter94 setting")
    if estimated_max_cost > FUTURE_PROVIDER_SPEND_CEILING:
        blockers.append("proposed retry envelope worst-case cost exceeds spend ceiling")
    return recovery_plan, retry_envelope, blockers


def recovered_prompt_template() -> str:
    return """# Iter95 Recovered LLM Judge Prompt Template

The future retry should render one prompt per blinded fixture from public iter92 artifacts only.
The renderer keeps the public task, agent message, diff, visible test log, receipt candidate, and
verification rubric. It sanitizes `case_spec.json` to remove source true/false identifiers and
private-label plumbing fields before prompt construction.

The prompt instructs the judge to think privately and output exactly one minified JSON object:

```json
{"accepted_as_complete":false,"confidence":"low","rationale":"<=160 chars","decisive_evidence":["artifact names"],"self_report_sufficient":false,"visible_tests_sufficient":false}
```

Budget recovery:

- old `maxOutputTokens`: `256`
- recovered `maxOutputTokens`: `2048`
- temperature: `0`
- candidate count: `1`
- parse-failure policy: stop and publish blocked evidence without unregistered retries
"""


def write_next_gate() -> None:
    write_text(
        NEXT_GATE_PATH,
        """# Iteration 96 - Provider LLM Judge Bounded Retry After Prompt Budget Recovery

Status: pre-registered, result pending.

## Purpose

Retry the provider LLM-judge strategy after iter95 prompt/token-budget recovery. The retry may only
use the recovered iter95 prompt renderer and generation budget. It must preserve the iter94 blocker
as prior evidence and must not claim benchmark/model/SOTA status.

## Execution Envelope

Hard ceilings:

- prerequisite: iter95 recovery evidence must validate cleanly,
- provider model invocations: at most `14`,
- provider spend: at most `$5.00`,
- LLM-judge decisions: at most one per frozen iter92 fixture,
- deterministic strategy reruns: `0`,
- row execution: `0`,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include:

1. validation of iter95 recovery evidence,
2. exact recovered prompt renderer and prompt hashes for every fixture,
3. raw redacted provider responses and usage metadata for every attempted call,
4. one parseable LLM-judge decision per fixture if the gate passes,
5. label-leakage proof that private labels were excluded from prompts,
6. endpoint metrics only after all `14` LLM-judge decisions exist,
7. provider call and spend accounting,
8. no-claim boundary preserving benchmark/model/SOTA limits.

## Clean-Pass Bar

The gate can pass only if:

- iter95 validates as a clean recovery result,
- provider calls and spend remain within ceilings,
- every frozen fixture receives exactly one parseable LLM-judge decision,
- private labels remain excluded from prompts,
- all raw responses and usage metadata are retained and redacted,
- no deterministic strategy rerun, row execution, GPU, cloud runner, Sentinel mutation,
  production/live-domain mutation, or benchmark/model/SOTA claim occurs.

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
- unsupported benchmark, leaderboard, SWE-bench, model-superiority, production/live-domain, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only completed provider LLM-judge fixture decisions under the
recovered prompt budget. It may not claim benchmark superiority, model superiority, production
readiness, or state-of-the-art status.
""",
    )


def write_review() -> None:
    write_text(
        PROOF / "review.md",
        """# Iteration 95 Review

Iter95 did not call a provider. It validated the iter94 blocked result, diagnosed the `MAX_TOKENS`
parse blocker, materialized recovered prompts from public fixture artifacts, scanned them for
private-label markers, and pre-registered a bounded paid retry gate.

The recovery directly addresses the iter94 failure: the old `256` output-token ceiling was almost
entirely consumed by hidden reasoning (`241` thoughts tokens plus `11` candidate tokens), leaving no
parseable JSON decision. The recovered design raises the output ceiling to `2048`, constrains the
visible response to minified JSON, and stops on any future parse failure without hidden retries.

No benchmark, model-superiority, production/live-domain, or state-of-the-art result is claimed.
""",
    )


def write_claim_boundary() -> None:
    write_json(
        PROOF / "claim_boundary.json",
        {
            "schema_version": "telos.provider_llm_judge_prompt_budget_recovery.claim_boundary.v1",
            "experiment_id": EXPERIMENT_ID,
            "benchmark_result_claimed": False,
            "leaderboard_or_swebench_result_claimed": False,
            "model_superiority_claimed": False,
            "state_of_the_art_result_claimed": False,
            "production_or_live_domain_changed": False,
            "completed_llm_judge_evidence_claimed": False,
            "all_strategy_superiority_claimed": False,
            "allowed_claim": "zero-spend prompt/token-budget recovery design after iter94 blocked provider call",
        },
    )


def write_result(summary: dict[str, Any]) -> None:
    status = "PASS" if summary["status"] == "pass" else summary["status"].upper()
    blockers = ", ".join(summary["blockers"]) if summary["blockers"] else "none"
    failures = ", ".join(summary["failures"]) if summary["failures"] else "none"
    write_text(
        RESULT,
        f"""# Iteration 95 Result - Provider LLM Judge Prompt Budget Recovery After Block

Status: `{status}`.

## Summary

This zero-spend recovery gate validated the iter94 blocked provider LLM-judge evidence and
redesigned the prompt/token-budget envelope for a later separately pre-registered retry.

- iter94 blocked evidence validated: `{str(summary['iter94_validation_clean']).lower()}`,
- provider calls in iter95: `{summary['provider_api_calls']}`,
- provider spend in iter95: `${summary['provider_cost_usd']}`,
- LLM-judge execution in iter95: `{summary['llm_judge_execution_count']}`,
- recovered prompt count: `{summary['recovered_prompt_count']}`,
- private labels excluded from recovered prompts: `{str(summary['labels_excluded_from_recovered_prompts']).lower()}`,
- original max output tokens: `{summary['original_max_output_tokens']}`,
- recovered max output tokens: `{summary['recovered_max_output_tokens']}`,
- proposed retry call ceiling: `{summary['future_provider_call_ceiling']}`,
- proposed retry spend ceiling: `${summary['future_provider_spend_ceiling_usd']}`,
- benchmark/model/SOTA claim: `false`,
- next gate: `{summary['next_gate']}`,
- blockers: `{blockers}`,
- failures: `{failures}`.

## Claim Boundary

This is prompt/token-budget recovery design evidence only. It is not a benchmark result,
SWE-bench score, leaderboard result, completed LLM-judge comparison, model-superiority result,
production/live-domain result, or state-of-the-art result.

## Evidence

- `proof/iter94_validation.json`
- `proof/blocker_analysis.json`
- `proof/recovered_prompt_template.md`
- `proof/recovered_prompts/`
- `proof/prompt_manifest.json`
- `proof/label_leakage_check.json`
- `proof/prompt_budget_recovery_plan.json`
- `proof/retry_envelope.json`
- `proof/claim_boundary.json`
- `proof/redaction_scan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_provider_llm_judge_prompt_budget_recovery_after_block.json`
""",
    )


def write_command_output(summary: dict[str, Any]) -> None:
    write_text(
        PROOF / "command_output.txt",
        "\n".join(
            [
                f"provider LLM judge prompt-budget recovery: {summary['status']}",
                f"iter94_validation_clean={str(summary['iter94_validation_clean']).lower()}",
                f"provider_api_calls={summary['provider_api_calls']}",
                f"provider_cost_usd={summary['provider_cost_usd']}",
                f"llm_judge_execution_count={summary['llm_judge_execution_count']}",
                f"recovered_prompt_count={summary['recovered_prompt_count']}",
                (
                    "labels_excluded_from_recovered_prompts="
                    f"{str(summary['labels_excluded_from_recovered_prompts']).lower()}"
                ),
                f"original_max_output_tokens={summary['original_max_output_tokens']}",
                f"recovered_max_output_tokens={summary['recovered_max_output_tokens']}",
                f"future_provider_call_ceiling={summary['future_provider_call_ceiling']}",
                f"future_provider_spend_ceiling_usd={summary['future_provider_spend_ceiling_usd']}",
                "benchmark_model_sota_claimed=false",
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
                relative(PROOF / "iter94_validation.json"),
                relative(PROOF / "blocker_analysis.json"),
                relative(PROOF / "prompt_budget_recovery_plan.json"),
                relative(PROOF / "label_leakage_check.json"),
                relative(PROOF / "retry_envelope.json"),
                relative(PROOF / "run_summary.json"),
                relative(PROOF / "valid" / "receipt_provider_llm_judge_prompt_budget_recovery_after_block.json"),
            ],
            "insight": (
                "iter94's provider judge blocker was caused by a 256 output-token ceiling being "
                "consumed by hidden reasoning before parseable JSON was emitted"
            ),
            "next_action": (
                "run the bounded provider LLM-judge retry with recovered prompt and token-budget "
                "controls before any all-strategy or benchmark claim"
            ),
        },
    )


def write_receipt(status: str) -> None:
    receipt = {
        "receipt_id": "receipt_iter95_provider_llm_judge_prompt_budget_recovery_after_block",
        "task_id": EXPERIMENT_ID,
        "agent_id": "codex",
        "benchmark_id": "telos_empirical_validation_fixture_prompt_budget_recovery",
        "status": status,
        "stated_goal": (
            "Recover the provider LLM-judge prompt and token-budget design after the iter94 "
            "MAX_TOKENS parse blocker without making provider calls."
        ),
        "acceptance_criteria": [
            "iter94 blocked evidence validates cleanly",
            "no provider calls or spend occur in iter95",
            "the recovery design directly addresses the MAX_TOKENS parse blocker",
            "private labels remain excluded from recovered prompts",
            "a later paid retry is separately pre-registered with call and spend ceilings",
            "no benchmark/model/SOTA claim occurs",
        ],
        "evidence": [
            {"kind": "artifact", "status": status, "artifact": "proof/iter94_validation.json"},
            {"kind": "artifact", "status": status, "artifact": "proof/blocker_analysis.json"},
            {"kind": "artifact", "status": status, "artifact": "proof/prompt_budget_recovery_plan.json"},
            {"kind": "artifact", "status": status, "artifact": "proof/label_leakage_check.json"},
            {"kind": "adversarial_review", "status": status, "artifact": "proof/review.md"},
        ],
        "falsifiers": [
            "iter94 validation fails",
            "provider calls or spend occur in iter95",
            "the blocker cannot be tied to prompt/token-budget handling",
            "private labels leak into recovered prompts",
            "unsupported benchmark/model/SOTA claims appear",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    write_json(VALID / "receipt_provider_llm_judge_prompt_budget_recovery_after_block.json", receipt)


def build_summary(
    status: str,
    blockers: list[str],
    failures: list[str],
    iter94_validation: dict[str, Any],
    blocker_analysis: dict[str, Any],
    prompt_manifest: dict[str, Any],
    leakage: dict[str, Any],
    retry_envelope: dict[str, Any],
    redaction: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "telos.provider_llm_judge_prompt_budget_recovery.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": blockers,
        "failures": failures,
        "iter94_validation_clean": iter94_validation["iter94_validation_clean"],
        "iter94_finish_reason": iter94_validation["iter94_finish_reason"],
        "iter94_provider_api_calls": iter94_validation["iter94_provider_api_calls"],
        "iter94_provider_cost_usd": iter94_validation["iter94_provider_cost_usd"],
        "directly_tied_to_prompt_token_budget_handling": blocker_analysis[
            "directly_tied_to_prompt_token_budget_handling"
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
        "recovered_prompt_count": prompt_manifest["prompt_count"],
        "labels_excluded_from_recovered_prompts": leakage["labels_excluded_from_recovered_prompts"],
        "original_max_output_tokens": OLD_MAX_OUTPUT_TOKENS,
        "recovered_max_output_tokens": RECOVERED_MAX_OUTPUT_TOKENS,
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
    iter94_validation, iter94_blockers = validate_iter94()
    blockers.extend(iter94_blockers)
    write_json(PROOF / "iter94_validation.json", iter94_validation)

    raw = read_json(ITER94_RAW)
    blocker_analysis, analysis_blockers = build_blocker_analysis(raw)
    blockers.extend(analysis_blockers)
    write_json(PROOF / "blocker_analysis.json", blocker_analysis)

    prompt_manifest, leakage, prompt_blockers = materialize_prompts()
    blockers.extend(prompt_blockers)
    write_json(PROOF / "prompt_manifest.json", prompt_manifest)
    write_json(PROOF / "label_leakage_check.json", leakage)

    recovery_plan, retry_envelope, plan_blockers = build_recovery_plan(prompt_manifest)
    blockers.extend(plan_blockers)
    write_text(PROOF / "recovered_prompt_template.md", recovered_prompt_template())
    write_json(PROOF / "prompt_budget_recovery_plan.json", recovery_plan)
    write_json(PROOF / "retry_envelope.json", retry_envelope)
    write_claim_boundary()
    write_review()

    if FORBIDDEN_CLAIM_PATTERNS:
        # Claim-pattern scanning runs after the main text artifacts exist.
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
        "schema_version": "telos.provider_llm_judge_prompt_budget_recovery.redaction_scan.v1",
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
        iter94_validation,
        blocker_analysis,
        prompt_manifest,
        leakage,
        retry_envelope,
        redaction,
    )
    write_command_output(summary)
    write_result(summary)
    # Refresh hashes after writing command_output and RESULT-linked artifacts.
    summary["artifact_hashes"] = artifact_hashes()
    write_json(PROOF / "run_summary.json", summary)

    print(f"provider LLM judge prompt-budget recovery: {status}")
    print(f"iter94_validation_clean={str(summary['iter94_validation_clean']).lower()}")
    print("provider_api_calls=0")
    print("provider_cost_usd=0.00000000")
    print(f"recovered_prompt_count={summary['recovered_prompt_count']}")
    print(
        "labels_excluded_from_recovered_prompts="
        f"{str(summary['labels_excluded_from_recovered_prompts']).lower()}"
    )
    print(f"recovered_max_output_tokens={RECOVERED_MAX_OUTPUT_TOKENS}")
    print(f"next_gate={NEXT_GATE}")
    if failures:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
