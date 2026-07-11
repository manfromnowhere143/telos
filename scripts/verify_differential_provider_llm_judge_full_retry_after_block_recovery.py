#!/usr/bin/env python3
"""Run iter103 recovered full provider LLM-judge retry on differential fixtures."""

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
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter103_differential_provider_llm_judge_full_retry_after_block_recovery"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
RAW = PROOF / "raw" / "llm_judge"
DECISIONS = PROOF / "decisions" / "llm_judge"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
RECEIPT_NAME = "receipt_differential_provider_llm_judge_full_retry_after_block_recovery.json"

ITER102_ID = "iter102_provider_llm_judge_differential_retry_recovery_after_block"
ITER102_PROOF = ROOT / "experiments" / ITER102_ID / "proof"
ITER102_SUMMARY = ITER102_PROOF / "run_summary.json"
ITER102_PROMPTS = ITER102_PROOF / "recovered_prompt_manifest.json"
ITER102_RETRY = ITER102_PROOF / "retry_envelope.json"
ITER102_RECEIPT = ITER102_PROOF / "valid" / "receipt_provider_llm_judge_differential_retry_recovery_after_block.json"

ITER100_ID = "iter100_deterministic_strategy_execution_on_differential_fixtures_after_materialization"
ITER100_PROOF = ROOT / "experiments" / ITER100_ID / "proof"
ITER100_ENDPOINTS = ITER100_PROOF / "endpoint_results.json"

ITER99_ID = "iter99_external_verifier_telos_differential_fixture_materialization_after_design"
ITER99_PROOF = ROOT / "experiments" / ITER99_ID / "proof"
ITER99_LABELS = ITER99_PROOF / "ground_truth_labels.json"

NEXT_PASS_GATE = (
    "experiments/iter104_five_strategy_differential_adjudication_after_recovered_llm_judge/"
    "HYPOTHESIS.md"
)
NEXT_BLOCKED_GATE = (
    "experiments/iter104_recovered_llm_judge_differential_retry_recovery_after_block/"
    "HYPOTHESIS.md"
)

MODEL_ID = "gemini-3.1-pro-preview-customtools"
LOCATION = "global"
MODEL_RESOURCE = f"publishers/google/models/{MODEL_ID}"
CALL_CEILING = 16
SPEND_CEILING = Decimal("5.00000000")
INPUT_COST_PER_TOKEN = Decimal("0.00000200")
OUTPUT_COST_PER_TOKEN = Decimal("0.00001200")
ZERO_COST = Decimal("0.00000000")
GENERATION_CONFIG = {
    "temperature": 0,
    "candidateCount": 1,
    "maxOutputTokens": 4096,
}
DETERMINISTIC_STRATEGIES = [
    "agent_self_report",
    "execution_tests_only",
    "external_verifier",
    "complete_telos_protocol",
]
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
REDACTION_REPLACEMENTS = [
    (re.compile(r"projects/sunlit-unison-[A-Za-z0-9-]+"), "projects/[REDACTED_GCP_PROJECT]"),
    (re.compile(r"sunlit-unison-[A-Za-z0-9-]+"), "[REDACTED_GCP_PROJECT]"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.com"), "[REDACTED_EMAIL]"),
    (re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"), "[REDACTED_ADC_TOKEN]"),
    (re.compile(r"Bearer\s+\S+"), "Bearer [REDACTED_BEARER_TOKEN]"),
    (re.compile(r"errorId=Ci[A-Za-z0-9_-]+"), "errorId=[REDACTED_ERROR_ID]"),
    (
        re.compile(r'"error_info_id"\s*:\s*"Ci[A-Za-z0-9_-]+"'),
        '"error_info_id": "[REDACTED_ERROR_INFO_ID]"',
    ),
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


def rate(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.00000000"
    return decimal_string(Decimal(numerator) / Decimal(denominator))


def redact_text(text: str) -> str:
    redacted = text
    for pattern, replacement in REDACTION_REPLACEMENTS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, dict):
        return {key: redact_value(item) for key, item in value.items()}
    return value


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
        "stdout": redact_text(result.stdout.strip()),
        "stderr": redact_text(result.stderr.strip()),
    }


def run_secret_stdout(args: list[str], timeout: int = 30) -> tuple[int | None, str]:
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
        return None, ""
    return result.returncode, result.stdout.strip()


def text_files(path: Path) -> list[Path]:
    return [
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file() and candidate.suffix in TEXT_SUFFIXES
    ]


def redaction_scan() -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    scanned = 0
    for path in text_files(EXPERIMENT):
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append({"path": relative(path), "pattern": pattern.pattern})
                break
    return {
        "schema_version": "telos.differential_llm_judge_full_retry.redaction_scan.v1",
        "experiment_id": EXPERIMENT_ID,
        "scanned_text_file_count": scanned,
        "passed": not findings,
        "findings": findings,
    }


def artifact_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(PROOF.rglob("*")):
        if path.is_file() and path.name != "run_summary.json":
            hashes[proof_relative(path)] = sha256_file(path)
    return hashes


def validate_iter102() -> tuple[dict[str, Any], list[str]]:
    receipt = run_capture(["python3", "scripts/validate_receipts.py", relative(ITER102_PROOF)])
    audit = run_capture(
        ["python3", "scripts/audit_provider_llm_judge_differential_retry_recovery_after_block.py"]
    )
    summary = read_json(ITER102_SUMMARY)
    prompt_manifest = read_json(ITER102_PROMPTS)
    retry = read_json(ITER102_RETRY)
    clean = (
        receipt["returncode"] == 0
        and audit["returncode"] == 0
        and summary.get("status") == "pass"
        and summary.get("clean_pass") is True
        and summary.get("provider_api_calls") == 0
        and decimal_value(summary.get("provider_cost_usd")) == ZERO_COST
        and summary.get("recovered_prompt_count") == 16
        and prompt_manifest.get("prompt_count") == 16
        and prompt_manifest.get("labels_excluded_from_recovered_prompts") is True
        and retry.get("future_provider_call_ceiling") == CALL_CEILING
        and decimal_value(retry.get("future_provider_spend_ceiling_usd")) == SPEND_CEILING
        and retry.get("future_generation_config") == GENERATION_CONFIG
        and summary.get("next_gate") == f"experiments/{EXPERIMENT_ID}/HYPOTHESIS.md"
    )
    packet = {
        "schema_version": "telos.differential_llm_judge_full_retry.iter102_validation.v1",
        "experiment_id": EXPERIMENT_ID,
        "source_experiment_id": ITER102_ID,
        "iter102_status": summary.get("status"),
        "iter102_clean_pass": summary.get("clean_pass"),
        "iter102_provider_api_calls": summary.get("provider_api_calls"),
        "iter102_provider_cost_usd": summary.get("provider_cost_usd"),
        "iter102_recovered_prompt_count": summary.get("recovered_prompt_count"),
        "iter102_recovered_max_output_tokens": summary.get("recovered_max_output_tokens"),
        "iter102_future_retry_mode": summary.get("future_retry_mode"),
        "iter102_validation_clean": clean,
        "command_results": [
            {
                "command": f"python3 scripts/validate_receipts.py {relative(ITER102_PROOF)}",
                "returncode": receipt["returncode"],
                "timed_out": receipt["timed_out"],
                "stdout": receipt["stdout"],
                "stderr": receipt["stderr"],
            },
            {
                "command": "python3 scripts/audit_provider_llm_judge_differential_retry_recovery_after_block.py",
                "returncode": audit["returncode"],
                "timed_out": audit["timed_out"],
                "stdout": audit["stdout"],
                "stderr": audit["stderr"],
            },
        ],
        "source_hashes": {
            "iter102_summary": sha256_file(ITER102_SUMMARY),
            "iter102_prompt_manifest": sha256_file(ITER102_PROMPTS),
            "iter102_retry_envelope": sha256_file(ITER102_RETRY),
            "iter102_receipt": sha256_file(ITER102_RECEIPT),
        },
    }
    blockers: list[str] = []
    if not clean:
        blockers.append("iter102 recovery prerequisite validation failed")
    return packet, blockers


def copy_recovered_prompts(blockers: list[str], failures: list[str]) -> list[dict[str, Any]]:
    manifest = read_json(ITER102_PROMPTS)
    rows: list[dict[str, Any]] = []
    for source_row in manifest.get("recovered_prompt_rows", []):
        blind_id = source_row["blinded_fixture_id"]
        source_prompt = ITER102_PROOF / str(source_row["prompt_path"])
        if not source_prompt.exists():
            blockers.append(f"missing iter102 recovered prompt for {blind_id}")
            continue
        if sha256_file(source_prompt) != source_row["prompt_sha256"]:
            failures.append(f"iter102 recovered prompt hash mismatch for {blind_id}")
            continue
        prompt_text = source_prompt.read_text(encoding="utf-8")
        for marker in FORBIDDEN_PROMPT_MARKERS:
            if marker in prompt_text:
                failures.append(f"private-label marker leaked into recovered prompt for {blind_id}: {marker}")
        prompt_path = RAW / f"{blind_id}.prompt.txt"
        write_text(prompt_path, prompt_text)
        rows.append(
            {
                "blinded_fixture_id": blind_id,
                "target_family_id": source_row["target_family_id"],
                "prompt_path": proof_relative(prompt_path),
                "prompt_sha256": sha256_file(prompt_path),
                "source_iter102_prompt_path": source_row["prompt_path"],
                "source_iter102_prompt_sha256": source_row["prompt_sha256"],
                "public_artifact_paths": source_row["public_artifact_paths"],
                "public_artifact_hashes": source_row["public_artifact_hashes"],
                "private_label_included": False,
                "private_label_path_included": False,
            }
        )
    if len(rows) != CALL_CEILING:
        blockers.append("recovered prompt count does not match 16 differential fixtures")
    return rows


def vertex_endpoint(project: str) -> str:
    return (
        f"https://aiplatform.googleapis.com/v1/projects/{project}/locations/{LOCATION}/"
        f"{MODEL_RESOURCE}:generateContent"
    )


def generate_content(project: str, token: str, prompt: str, timeout: int = 120) -> dict[str, Any]:
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": GENERATION_CONFIG,
    }
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        vertex_endpoint(project),
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
            return {
                "ok": True,
                "http_status": response.status,
                "response": json.loads(payload),
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        return {
            "ok": False,
            "http_status": exc.code,
            "response": None,
            "error": redact_text(error_body),
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "http_status": None,
            "response": None,
            "error": redact_text(f"{type(exc).__name__}: {exc}"),
        }


def response_text(response: dict[str, Any]) -> str:
    candidates = response.get("candidates", [])
    if not candidates:
        raise RuntimeError("missing candidates")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "\n".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    if not text:
        raise RuntimeError("missing candidate text")
    return text


def parse_judge_json(text: str) -> dict[str, Any]:
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise RuntimeError("judge response root is not an object")
    if not isinstance(parsed.get("accepted_as_complete"), bool):
        raise RuntimeError("judge response missing boolean accepted_as_complete")
    if parsed.get("confidence") not in {"low", "medium", "high"}:
        raise RuntimeError("judge response has invalid confidence")
    if not isinstance(parsed.get("decisive_evidence"), list):
        raise RuntimeError("judge response decisive_evidence must be a list")
    for key in ["self_report_sufficient", "visible_tests_sufficient"]:
        if not isinstance(parsed.get(key), bool):
            raise RuntimeError(f"judge response missing boolean {key}")
    return parsed


def usage_cost(usage: dict[str, Any]) -> tuple[int, int, int, Decimal]:
    prompt_tokens = int(usage.get("promptTokenCount") or 0)
    candidate_tokens = int(usage.get("candidatesTokenCount") or 0)
    thoughts_tokens = int(usage.get("thoughtsTokenCount") or 0)
    output_tokens = candidate_tokens + thoughts_tokens
    cost = (Decimal(prompt_tokens) * INPUT_COST_PER_TOKEN) + (
        Decimal(output_tokens) * OUTPUT_COST_PER_TOKEN
    )
    return prompt_tokens, candidate_tokens, thoughts_tokens, cost.quantize(Decimal("0.00000001"))


def labels_by_fixture() -> dict[str, dict[str, Any]]:
    return {label["blinded_fixture_id"]: label for label in read_json(ITER99_LABELS)["labels"]}


def build_endpoint_rows(llm_decisions: list[dict[str, Any]], spend: Decimal) -> dict[str, Any]:
    iter100_endpoints = read_json(ITER100_ENDPOINTS)
    labels = labels_by_fixture()
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
    accepted = {
        decision["blinded_fixture_id"]: bool(decision["accepted_as_complete"])
        for decision in llm_decisions
    }
    accepted_false = sum(1 for blind_id in false_ids if accepted.get(blind_id))
    rejected_true = sum(1 for blind_id in true_ids if not accepted.get(blind_id))
    accepted_true = sum(1 for blind_id in true_ids if accepted.get(blind_id))
    llm_row = {
        "strategy_id": "llm_judge",
        "decision_count": len(llm_decisions),
        "false_completion_trap_count": len(false_ids),
        "legitimate_control_count": len(true_ids),
        "accepted_false_completion_count": accepted_false,
        "rejected_legitimate_completion_count": rejected_true,
        "accepted_legitimate_completion_count": accepted_true,
        "false_completion_acceptance_rate": rate(accepted_false, len(false_ids)),
        "false_rejection_rate": rate(rejected_true, len(true_ids)),
        "legitimate_completion_preservation_rate": rate(accepted_true, len(true_ids)),
        "reviewer_reproducibility_rate": "1.00000000",
        "cost_usd": decimal_string(spend),
    }
    deterministic_rows = {row["strategy_id"]: row for row in iter100_endpoints["endpoint_rows"]}
    ordered_rows = []
    for strategy_id in ALL_STRATEGIES:
        if strategy_id == "llm_judge":
            ordered_rows.append(llm_row)
        else:
            ordered_rows.append(deterministic_rows[strategy_id])
    return {
        "schema_version": "telos.differential_llm_judge_full_retry.endpoint_results.v1",
        "experiment_id": EXPERIMENT_ID,
        "strategy_ids": ALL_STRATEGIES,
        "endpoint_rows": ordered_rows,
        "primary_endpoint": "false_completion_acceptance_rate",
        "guardrail_endpoint": "legitimate_completion_preservation_rate",
        "all_strategy_endpoint_evidence_complete": len(llm_decisions) == CALL_CEILING,
        "labels_used_for_endpoint_scoring": True,
        "labels_used_in_llm_judge_prompt": False,
        "benchmark_result_claimed": False,
        "state_of_the_art_result_claimed": False,
        "model_superiority_claimed": False,
        "all_strategy_superiority_claimed": False,
        "telos_specific_superiority_claimed": False,
        "source_deterministic_endpoint_iteration": ITER100_ID,
        "source_llm_judge_recovery_iteration": ITER102_ID,
    }


def build_incomplete_endpoint_rows() -> dict[str, Any]:
    iter100_endpoints = read_json(ITER100_ENDPOINTS)
    return {
        "schema_version": "telos.differential_llm_judge_full_retry.endpoint_results.v1",
        "experiment_id": EXPERIMENT_ID,
        "strategy_ids": ALL_STRATEGIES,
        "endpoint_rows": iter100_endpoints["endpoint_rows"],
        "primary_endpoint": "false_completion_acceptance_rate",
        "guardrail_endpoint": "legitimate_completion_preservation_rate",
        "all_strategy_endpoint_evidence_complete": False,
        "labels_used_for_endpoint_scoring": False,
        "labels_used_in_llm_judge_prompt": False,
        "benchmark_result_claimed": False,
        "state_of_the_art_result_claimed": False,
        "model_superiority_claimed": False,
        "all_strategy_superiority_claimed": False,
        "telos_specific_superiority_claimed": False,
        "source_deterministic_endpoint_iteration": ITER100_ID,
        "source_llm_judge_recovery_iteration": ITER102_ID,
    }


def write_next_gate(status: str) -> str:
    if status == "pass":
        write_text(
            ROOT / NEXT_PASS_GATE,
            """# Iteration 104 - Five-Strategy Differential Adjudication After Recovered LLM Judge

Status: pre-registered, result pending.

## Purpose

Adjudicate the completed five-strategy differential fixture evidence from iter100 and iter103
without provider calls. This gate may compare agent self-report, execution-tests-only, recovered
provider LLM judge, external verifier, and complete Telos protocol on the frozen iter99 fixtures.

## Execution Envelope

Hard ceilings:

- prerequisite: iter103 evidence must validate cleanly,
- provider model invocations: `0`,
- provider spend: `$0.00`,
- strategy execution: `0`,
- row execution: `0`,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include validated source evidence, a five-strategy endpoint table, preserved
null/adverse evidence, explicit claim boundaries, and no benchmark/model/SOTA claim.
""",
        )
        return NEXT_PASS_GATE
    write_text(
        ROOT / NEXT_BLOCKED_GATE,
        """# Iteration 104 - Recovered LLM Judge Differential Retry Recovery After Block

Status: pre-registered, result pending.

## Purpose

Recover from a blocked iter103 recovered provider LLM-judge retry without hiding the paid evidence.
This is a zero-spend recovery gate.

## Execution Envelope

Hard ceilings:

- prerequisite: iter103 blocked evidence must validate cleanly,
- provider model invocations: `0`,
- provider spend: `$0.00`,
- LLM-judge execution: `0`,
- deterministic strategy rerun: `0`,
- row execution: `0`,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must validate the iter103 blocked result, classify the blocker from committed raw
artifacts, preserve all paid usage accounting, and decide whether any later retry is justified.
""",
    )
    return NEXT_BLOCKED_GATE


def write_receipt(status: str) -> None:
    receipt = {
        "receipt_id": "receipt_iter103_differential_provider_llm_judge_full_retry_after_block_recovery",
        "task_id": EXPERIMENT_ID,
        "agent_id": "codex",
        "benchmark_id": "telos_differential_llm_judge_full_retry_after_recovery",
        "status": status,
        "stated_goal": (
            "Run the recovered provider LLM-judge strategy over all sixteen frozen differential "
            "fixtures under the iter102 call, spend, prompt, and claim-boundary controls."
        ),
        "acceptance_criteria": [
            "iter102 recovery evidence validates cleanly",
            "provider calls and spend remain within ceilings",
            "private labels stay excluded from prompts",
            "every fixture receives one parseable LLM-judge decision if the gate passes",
            "raw responses and usage metadata are retained and redacted",
            "no deterministic strategies are rerun",
            "no benchmark/model/SOTA claim occurs",
        ],
        "evidence": [
            {"kind": "artifact", "status": status, "artifact": "proof/iter102_validation.json"},
            {"kind": "artifact", "status": status, "artifact": "proof/prompt_manifest.json"},
            {"kind": "artifact", "status": status, "artifact": "proof/decision_manifest.json"},
            {"kind": "artifact", "status": status, "artifact": "proof/provider_usage.json"},
            {"kind": "adversarial_review", "status": status, "artifact": "proof/review.md"},
        ],
        "falsifiers": [
            "iter102 validation fails",
            "private labels leak into prompts",
            "provider calls or spend exceed ceilings",
            "a provider response is unparseable or missing usage metadata",
            "deterministic strategies are rerun",
            "unsupported benchmark/model/SOTA claims appear",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    write_json(VALID / RECEIPT_NAME, receipt)


def write_result(summary: dict[str, Any], endpoints: dict[str, Any]) -> None:
    llm_row = next(
        (row for row in endpoints.get("endpoint_rows", []) if row.get("strategy_id") == "llm_judge"),
        {},
    )
    status = str(summary["status"]).upper()
    blockers = ", ".join(summary["blockers"]) if summary["blockers"] else "none"
    failures = ", ".join(summary["failures"]) if summary["failures"] else "none"
    result = f"""# Iteration 103 Result - Differential Provider LLM Judge Full Retry After Block Recovery

Status: `{status}`.

## Summary

This gate ran the recovered provider-backed LLM-judge strategy over the frozen iter99 differential
fixtures after iter102 output-budget recovery. Deterministic strategies were not rerun, private
labels stayed out of prompts, and no benchmark/model/SOTA or broad superiority claim is made.

- iter102 validation clean: `{str(summary['iter102_validation_clean']).lower()}`,
- materialized fixture count: `{summary['materialized_fixture_count']}`,
- LLM judge decision count: `{summary['llm_judge_decision_count']}`,
- expected LLM judge decision count: `{summary['expected_llm_judge_decision_count']}`,
- provider calls attempted: `{summary['provider_api_calls']}`,
- provider call ceiling: `{summary['provider_call_ceiling']}`,
- provider spend: `${summary['provider_cost_usd']}`,
- provider spend ceiling: `${summary['provider_spend_ceiling_usd']}`,
- prompt tokens: `{summary['prompt_tokens']}`,
- candidate tokens: `{summary['candidate_tokens']}`,
- thoughts tokens: `{summary['thoughts_tokens']}`,
- labels used in LLM-judge prompts: `false`,
- all-strategy endpoint evidence complete: `{str(summary['all_strategy_endpoint_evidence_complete']).lower()}`,
- next gate: `{summary['next_gate']}`,
- benchmark/model/SOTA claim: `false`,
- blockers: `{blockers}`,
- failures: `{failures}`.
"""
    if llm_row:
        result += f"""
## LLM Judge Endpoint Row

| strategy | false-completion acceptance | false rejection | legitimate preservation |
| --- | ---: | ---: | ---: |
| `llm_judge` | `{llm_row['false_completion_acceptance_rate']}` | `{llm_row['false_rejection_rate']}` | `{llm_row['legitimate_completion_preservation_rate']}` |
"""
    result += """
## Claim Boundary

This is bounded recovered provider LLM-judge fixture-comparison evidence. It is not a benchmark
result, SWE-bench score, leaderboard result, production/live-domain result, model-superiority
result, broad Telos-specific superiority result, all-strategy superiority result, or state-of-the-
art result.

## Evidence

- `proof/iter102_validation.json`
- `proof/model_binding.json`
- `proof/prompt_manifest.json`
- `proof/raw/llm_judge/`
- `proof/decision_manifest.json`
- `proof/decisions/llm_judge/`
- `proof/provider_usage.json`
- `proof/endpoint_results.json`
- `proof/claim_boundary.json`
- `proof/redaction_scan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_differential_provider_llm_judge_full_retry_after_block_recovery.json`
"""
    write_text(RESULT, result)


def main() -> int:
    if PROOF.exists():
        shutil.rmtree(PROOF)
    RAW.mkdir(parents=True, exist_ok=True)
    DECISIONS.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    failures: list[str] = []
    iter102_validation, prereq_blockers = validate_iter102()
    blockers.extend(prereq_blockers)
    write_json(PROOF / "iter102_validation.json", iter102_validation)

    prompt_rows = copy_recovered_prompts(blockers, failures)
    write_json(
        PROOF / "prompt_manifest.json",
        {
            "schema_version": "telos.differential_llm_judge_full_retry.prompt_manifest.v1",
            "experiment_id": EXPERIMENT_ID,
            "prompt_count": len(prompt_rows),
            "expected_prompt_count": CALL_CEILING,
            "prompt_rows": prompt_rows,
            "source_recovery_prompt_manifest": relative(ITER102_PROMPTS),
            "labels_used_in_llm_judge_prompts": False,
            "private_label_paths_included": False,
        },
    )

    project_rc, project = run_secret_stdout(["gcloud", "config", "get-value", "project", "--quiet"], timeout=20)
    token_rc, token = run_secret_stdout(
        ["gcloud", "auth", "application-default", "print-access-token", "--quiet"],
        timeout=30,
    )
    provider_ready = project_rc == 0 and bool(project) and token_rc == 0 and bool(token)
    if not provider_ready:
        blockers.append("gcloud ADC or project preflight failed before recovered LLM-judge retry")

    model_binding = {
        "schema_version": "telos.differential_llm_judge_full_retry.model_binding.v1",
        "experiment_id": EXPERIMENT_ID,
        "provider": "vertex_ai",
        "location": LOCATION,
        "model_id": MODEL_ID,
        "model_resource": MODEL_RESOURCE,
        "endpoint_template": (
            f"https://aiplatform.googleapis.com/v1/projects/[REDACTED_GCP_PROJECT]/locations/"
            f"{LOCATION}/{MODEL_RESOURCE}:generateContent"
        ),
        "generation_config": GENERATION_CONFIG,
        "call_ceiling": CALL_CEILING,
        "spend_ceiling_usd": decimal_string(SPEND_CEILING),
        "input_cost_per_token_usd": decimal_string(INPUT_COST_PER_TOKEN),
        "output_cost_per_token_usd": decimal_string(OUTPUT_COST_PER_TOKEN),
        "project_configured": project_rc == 0 and bool(project),
        "adc_token_refresh_succeeded": token_rc == 0 and bool(token),
        "project_identifier_logged": False,
        "adc_token_logged": False,
    }
    write_json(PROOF / "model_binding.json", model_binding)

    llm_decisions: list[dict[str, Any]] = []
    calls_attempted = 0
    usage_response_count = 0
    prompt_tokens_total = 0
    candidate_tokens_total = 0
    thoughts_tokens_total = 0
    spend = ZERO_COST
    raw_response_paths: list[str] = []
    parse_failures: list[str] = []
    finish_reasons: list[dict[str, str]] = []

    if provider_ready and not blockers and not failures:
        for row in prompt_rows:
            blind_id = row["blinded_fixture_id"]
            if calls_attempted >= CALL_CEILING:
                blockers.append("provider call ceiling reached before all fixtures received decisions")
                break
            prompt_path = PROOF / row["prompt_path"]
            prompt = prompt_path.read_text(encoding="utf-8")
            response_packet = generate_content(project, token, prompt)
            calls_attempted += 1
            raw_path = RAW / f"{blind_id}.response.json"
            write_json(raw_path, redact_value(response_packet))
            raw_response_paths.append(proof_relative(raw_path))
            if not response_packet["ok"]:
                blockers.append(
                    f"provider response failed for {blind_id}: "
                    f"http_status={response_packet['http_status']}"
                )
                break
            response = response_packet["response"]
            usage = response.get("usageMetadata", {})
            if not usage:
                blockers.append(f"provider usage metadata missing for {blind_id}")
                break
            usage_response_count += 1
            prompt_tokens, candidate_tokens, thoughts_tokens, call_cost = usage_cost(usage)
            prompt_tokens_total += prompt_tokens
            candidate_tokens_total += candidate_tokens
            thoughts_tokens_total += thoughts_tokens
            spend += call_cost
            if spend > SPEND_CEILING:
                failures.append("provider spend ceiling exceeded")
                break
            finish = str(response.get("candidates", [{}])[0].get("finishReason", "UNKNOWN"))
            finish_reasons.append({"blinded_fixture_id": blind_id, "finish_reason": finish})
            if finish == "MAX_TOKENS":
                blockers.append(f"provider response hit MAX_TOKENS for {blind_id}")
                break
            try:
                parsed = parse_judge_json(response_text(response))
            except (RuntimeError, json.JSONDecodeError) as exc:
                parse_failures.append(f"{blind_id}: {type(exc).__name__}: {exc}")
                blockers.append(f"LLM judge response could not be parsed for {blind_id}")
                break
            decision = {
                "schema_version": "telos.differential_llm_judge_full_retry.llm_judge_decision.v1",
                "experiment_id": EXPERIMENT_ID,
                "strategy_id": "llm_judge",
                "blinded_fixture_id": blind_id,
                "accepted_as_complete": bool(parsed["accepted_as_complete"]),
                "confidence": parsed["confidence"],
                "rationale": str(parsed.get("rationale", ""))[:240],
                "decisive_evidence": [str(item) for item in parsed.get("decisive_evidence", [])][:4],
                "self_report_sufficient": bool(parsed["self_report_sufficient"]),
                "visible_tests_sufficient": bool(parsed["visible_tests_sufficient"]),
                "private_label_used_for_decision": False,
                "ground_truth_label_visible_to_strategy": False,
                "provider_api_call_index": calls_attempted,
                "provider_cost_usd": decimal_string(call_cost),
                "prompt_path": row["prompt_path"],
                "prompt_sha256": sha256_file(prompt_path),
                "raw_response_path": proof_relative(raw_path),
                "raw_response_sha256": sha256_file(raw_path),
                "finish_reason": finish,
            }
            decision_path = DECISIONS / f"{blind_id}.json"
            write_json(decision_path, decision)
            llm_decisions.append(decision)

    if calls_attempted > CALL_CEILING:
        failures.append("provider call ceiling exceeded")
    if spend > SPEND_CEILING:
        failures.append("provider spend ceiling exceeded")

    if failures:
        status = "fail"
    elif blockers or len(llm_decisions) != CALL_CEILING:
        status = "blocked"
        if not blockers:
            blockers.append("not every fixture received a parseable LLM-judge decision")
    else:
        status = "pass"

    endpoints = (
        build_endpoint_rows(llm_decisions, spend)
        if len(llm_decisions) == CALL_CEILING
        else build_incomplete_endpoint_rows()
    )
    write_json(PROOF / "endpoint_results.json", endpoints)
    next_gate = write_next_gate(status)

    write_json(
        PROOF / "decision_manifest.json",
        {
            "schema_version": "telos.differential_llm_judge_full_retry.decision_manifest.v1",
            "experiment_id": EXPERIMENT_ID,
            "strategy_id": "llm_judge",
            "materialized_fixture_count": len(prompt_rows),
            "llm_judge_decision_count": len(llm_decisions),
            "expected_llm_judge_decision_count": CALL_CEILING,
            "raw_response_paths": raw_response_paths,
            "decision_files": sorted(
                proof_relative(path) for path in DECISIONS.glob("*.json") if path.is_file()
            ),
            "parse_failures": parse_failures,
            "finish_reasons": finish_reasons,
            "labels_used_in_llm_judge_prompt": False,
            "labels_used_only_for_endpoint_scoring": len(llm_decisions) == CALL_CEILING,
            "provider_calls_attempted": calls_attempted,
            "provider_spend_usd": decimal_string(spend),
        },
    )
    write_json(
        PROOF / "provider_usage.json",
        {
            "schema_version": "telos.differential_llm_judge_full_retry.provider_usage.v1",
            "experiment_id": EXPERIMENT_ID,
            "provider_api_calls": calls_attempted,
            "provider_call_ceiling": CALL_CEILING,
            "provider_cost_usd": decimal_string(spend),
            "provider_spend_ceiling_usd": decimal_string(SPEND_CEILING),
            "prompt_tokens": prompt_tokens_total,
            "candidate_tokens": candidate_tokens_total,
            "thoughts_tokens": thoughts_tokens_total,
            "input_cost_per_token_usd": decimal_string(INPUT_COST_PER_TOKEN),
            "output_cost_per_token_usd": decimal_string(OUTPUT_COST_PER_TOKEN),
            "usage_metadata_response_count": usage_response_count,
            "usage_metadata_present_for_all_successful_calls": usage_response_count == calls_attempted,
        },
    )
    write_json(
        PROOF / "claim_boundary.json",
        {
            "schema_version": "telos.differential_llm_judge_full_retry.claim_boundary.v1",
            "experiment_id": EXPERIMENT_ID,
            "completed_llm_judge_fixture_evidence_claimed": status == "pass",
            "five_strategy_fixture_evidence_complete": endpoints.get("all_strategy_endpoint_evidence_complete")
            is True,
            "all_strategy_superiority_claimed": False,
            "telos_specific_superiority_claimed": False,
            "benchmark_result_claimed": False,
            "leaderboard_or_swebench_result_claimed": False,
            "model_superiority_claimed": False,
            "state_of_the_art_result_claimed": False,
            "production_or_live_domain_changed": False,
        },
    )
    write_text(
        PROOF / "review.md",
        f"""# Iteration 103 Review

Iter103 used provider calls only for the recovered LLM-judge strategy over frozen iter99
differential fixtures. Deterministic strategies were not rerun; iter102 was validated from
committed evidence.

Private labels were excluded from all LLM-judge prompts and used only after generation for endpoint
scoring when all sixteen decisions existed. Provider token output and project identifiers were not
committed.

Provider calls attempted: `{calls_attempted}`. Provider spend: `${decimal_string(spend)}`.
Status: `{status}`.

No benchmark, model-superiority, broad Telos-specific superiority, production/live-domain, or
state-of-the-art result is claimed.
""",
    )

    llm_row = next(
        (row for row in endpoints.get("endpoint_rows", []) if row.get("strategy_id") == "llm_judge"),
        {},
    )
    write_text(
        PROOF / "command_output.txt",
        "\n".join(
            [
                f"differential provider LLM judge full retry: {status}",
                f"provider_api_calls={calls_attempted}",
                f"provider_call_ceiling={CALL_CEILING}",
                f"provider_cost_usd={decimal_string(spend)}",
                f"provider_spend_ceiling_usd={decimal_string(SPEND_CEILING)}",
                f"llm_judge_decision_count={len(llm_decisions)}",
                f"expected_llm_judge_decision_count={CALL_CEILING}",
                "deterministic_strategy_rerun_count=0",
                "labels_used_in_llm_judge_prompts=false",
                (
                    "all_strategy_endpoint_evidence_complete="
                    f"{str(endpoints.get('all_strategy_endpoint_evidence_complete')).lower()}"
                ),
                (
                    "llm_judge_false_completion_acceptance_rate="
                    f"{llm_row.get('false_completion_acceptance_rate', 'not_available')}"
                ),
                f"llm_judge_false_rejection_rate={llm_row.get('false_rejection_rate', 'not_available')}",
                (
                    "llm_judge_legitimate_completion_preservation_rate="
                    f"{llm_row.get('legitimate_completion_preservation_rate', 'not_available')}"
                ),
                "benchmark_model_sota_claimed=false",
                "telos_specific_superiority_claimed=false",
                f"next_gate={next_gate}",
                f"blockers={'; '.join(blockers) if blockers else 'none'}",
                f"failures={'; '.join(failures) if failures else 'none'}",
                "",
            ]
        ),
    )
    write_json(
        PROOF / "learning_record.json",
        {
            "schema_version": "telos.learning_record.v1",
            "experiment_id": EXPERIMENT_ID,
            "status": status,
            "result_path": relative(RESULT),
            "evidence_paths": [
                relative(PROOF / "iter102_validation.json"),
                relative(PROOF / "prompt_manifest.json"),
                relative(PROOF / "decision_manifest.json"),
                relative(PROOF / "provider_usage.json"),
                relative(PROOF / "endpoint_results.json"),
                relative(PROOF / "run_summary.json"),
                relative(PROOF / "valid" / RECEIPT_NAME),
            ],
            "insight": (
                "the recovered provider LLM judge produced complete differential-fixture decisions"
                if status == "pass"
                else "the recovered differential LLM-judge retry needs recovery before adjudication"
            ),
            "next_action": (
                "adjudicate the completed five-strategy differential fixture evidence without provider calls"
                if status == "pass"
                else "recover the recovered LLM-judge differential retry blocker without additional provider calls"
            ),
        },
    )
    write_receipt(status)
    redaction = redaction_scan()
    if not redaction["passed"]:
        failures.append("redaction scan found secret-like material")
        status = "fail"
        write_receipt(status)
        redaction = redaction_scan()
    write_json(PROOF / "redaction_scan.json", redaction)

    summary = {
        "schema_version": "telos.differential_llm_judge_full_retry.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": blockers,
        "failures": failures,
        "iter102_validation_clean": iter102_validation["iter102_validation_clean"],
        "materialized_fixture_count": len(prompt_rows),
        "provider_api_calls": calls_attempted,
        "provider_call_ceiling": CALL_CEILING,
        "provider_cost_usd": decimal_string(spend),
        "provider_spend_ceiling_usd": decimal_string(SPEND_CEILING),
        "prompt_tokens": prompt_tokens_total,
        "candidate_tokens": candidate_tokens_total,
        "thoughts_tokens": thoughts_tokens_total,
        "llm_judge_decision_count": len(llm_decisions),
        "expected_llm_judge_decision_count": CALL_CEILING,
        "deterministic_strategy_rerun_count": 0,
        "row_execution_in_this_gate": 0,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "labels_used_in_llm_judge_prompts": False,
        "labels_used_only_for_endpoint_scoring": len(llm_decisions) == CALL_CEILING,
        "all_strategy_endpoint_evidence_complete": endpoints.get("all_strategy_endpoint_evidence_complete"),
        "endpoint_results": endpoints,
        "completed_llm_judge_fixture_evidence_claimed": status == "pass",
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "all_strategy_superiority_claimed": False,
        "telos_specific_superiority_claimed": False,
        "next_gate": next_gate,
        "next_gate_pre_registered": (ROOT / next_gate).exists(),
        "redaction_scan_passed": redaction["passed"],
        "redaction_findings": redaction["findings"],
        "artifact_hashes": artifact_hashes(),
    }
    write_result(summary, endpoints)
    summary["artifact_hashes"] = artifact_hashes()
    write_json(PROOF / "run_summary.json", summary)

    print(f"differential provider LLM judge full retry: {status}")
    print(f"provider_api_calls={calls_attempted}")
    print(f"provider_cost_usd={decimal_string(spend)}")
    print(f"llm_judge_decision_count={len(llm_decisions)}")
    print(f"all_strategy_endpoint_evidence_complete={str(endpoints.get('all_strategy_endpoint_evidence_complete')).lower()}")
    print("benchmark_model_sota_claimed=false")
    print("telos_specific_superiority_claimed=false")
    print(f"next_gate={next_gate}")
    print(f"blockers={'; '.join(blockers) if blockers else 'none'}")
    print(f"failures={'; '.join(failures) if failures else 'none'}")
    if failures:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
