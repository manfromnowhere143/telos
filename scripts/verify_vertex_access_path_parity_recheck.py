#!/usr/bin/env python3
"""Publish iter63 Vertex access-path parity recheck artifacts."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import textwrap
from typing import Any
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter63_vertex_access_path_parity_recheck"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
ITER62_SUMMARY = ROOT / "experiments" / "iter62_vertex_bearer_token_path_recovery" / "proof" / "run_summary.json"
ITER62_STDERR = (
    ROOT / "experiments" / "iter62_vertex_bearer_token_path_recovery" / "proof" / "litellm_bearer_probe_stderr.txt"
)
ITER56_PROBE = (
    ROOT / "experiments" / "iter56_provider_auth_recovery_for_paid_protocol_effect" / "proof" / "vertex_access_probe.json"
)
ITER54_COMMANDS = ROOT / "experiments" / "iter54_provider_pair_executor_recovery" / "proof" / "command_manifest.json"
CODECLASH_DIR = Path("/tmp/telos-codeclash")
CODECLASH_PYTHON = CODECLASH_DIR / ".venv" / "bin" / "python"
MODEL_ID = "gemini-3.1-pro-preview-customtools"
MODEL_NAME = f"vertex_ai/{MODEL_ID}"
VERTEX_LOCATION = "global"
TOKEN_ENV = "TELOS_VERTEX_BEARER_TOKEN"
PROJECT_ENV = "TELOS_VERTEX_PROJECT"
QUOTA_ENV = "TELOS_VERTEX_QUOTA_PROJECT"
CALL_CEILING = 2
SPEND_CEILING = 0.05
SPEND_BOUND_PER_CALL = 0.025
CLASSIFICATIONS = {
    "direct_rest_now_blocked",
    "litellm_specific_parity_gap",
    "access_path_recovered",
}
NEXT_BY_CLASSIFICATION = {
    "direct_rest_now_blocked": "experiments/iter64_vertex_project_access_recovery/HYPOTHESIS.md",
    "litellm_specific_parity_gap": "experiments/iter64_litellm_vertex_parity_gap_recovery/HYPOTHESIS.md",
    "access_path_recovered": (
        "experiments/iter64_provider_compatible_paid_execution_after_access_path_recovery/HYPOTHESIS.md"
    ),
}
TEXT_SUFFIXES = {".json", ".jsonl", ".log", ".txt", ".md", ".yaml", ".yml", ".py"}
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
    re.compile(r"ANTHROPIC_API_KEY\s*=\s*\S+"),
    re.compile(r"OPENAI_API_KEY\s*=\s*\S+"),
    re.compile(r"GOOGLE_API_KEY\s*=\s*\S+"),
    re.compile(r"GEMINI_API_KEY\s*=\s*\S+"),
    re.compile(r"GOOGLE_APPLICATION_CREDENTIALS\s*=\s*\S+"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"),
    re.compile(r"telos-vertex-runner"),
    re.compile(r"sunlit-unison-[A-Za-z0-9-]+"),
    re.compile(r"errorId=Ci"),
    re.compile(r'"error_info_id"\s*:\s*"Ci'),
]
STATIC_REDACTIONS = [
    (re.compile(r"projects/sunlit-unison-[A-Za-z0-9-]+"), "projects/[REDACTED_GCP_PROJECT]"),
    (re.compile(r"sunlit-unison-[A-Za-z0-9-]+"), "[REDACTED_GCP_PROJECT]"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"), "[REDACTED_SERVICE_ACCOUNT]"),
    (re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"), "[REDACTED_ADC_TOKEN]"),
    (re.compile(r"Bearer\s+\S+"), "Bearer [REDACTED_BEARER_TOKEN]"),
    (re.compile(r"errorId=Ci[A-Za-z0-9_-]+"), "errorId=[REDACTED_ERROR_ID]"),
    (re.compile(r'"error_info_id"\s*:\s*"Ci[A-Za-z0-9_-]+"'), '"error_info_id": "[REDACTED_ERROR_INFO_ID]"'),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} root must be an object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def redact_text(text: str, *, project_id: str | None = None, token: str | None = None) -> str:
    redacted = text
    if token:
        redacted = redacted.replace(token, "[REDACTED_BEARER_TOKEN]")
    if project_id:
        redacted = redacted.replace(f"projects/{project_id}", "projects/[REDACTED_GCP_PROJECT]")
        redacted = redacted.replace(project_id, "[REDACTED_GCP_PROJECT]")
    for pattern, replacement in STATIC_REDACTIONS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def redact_value(value: Any, *, project_id: str | None = None, token: str | None = None) -> Any:
    if isinstance(value, str):
        return redact_text(value, project_id=project_id, token=token)
    if isinstance(value, list):
        return [redact_value(item, project_id=project_id, token=token) for item in value]
    if isinstance(value, dict):
        return {key: redact_value(item, project_id=project_id, token=token) for key, item in value.items()}
    return value


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter63-vertex-access-path-parity-recheck-{status}",
        "task_id": "telos:iter63_vertex_access_path_parity_recheck@iter62",
        "agent_id": "codex-local-vertex-access-path-parity-recheck",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Classify whether the Vertex blocker is stale direct REST provider access or a "
            "LiteLLM-specific request-path parity gap."
        ),
        "acceptance_criteria": [
            "Iter62 is a clean blocked result with redacted CONSUMER_INVALID evidence.",
            "A current direct REST Vertex probe is attempted with token output suppressed.",
            "At most one matching LiteLLM probe is run only when the direct REST path passes.",
            "At most two provider probes and at most $0.05 bounded spend occur.",
            "No BattleSnake row, excluded pair, GPU, Sentinel mutation, cloud runner, or overclaim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/access_path_parity_report.json",
                "notes": "Records direct REST and LiteLLM parity status, classification, calls, cost, and no-row controls.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/direct_rest_probe.json",
                "notes": "Redacted current direct REST Vertex probe evidence.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records the access-parity-only claim boundary.",
            },
        ],
        "falsifiers": [
            "The result must block if iter62 does not show the named bearer-token path blocker.",
            "The result must block if current direct REST access no longer passes.",
            "The result must block if direct REST passes but LiteLLM still blocks.",
            "The result must fail if any row, excluded pair, GPU, Sentinel mutation, cloud runner, overclaim, or secret leak occurs.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def run_capture(
    args: list[str],
    *,
    timeout: int = 30,
    env: dict[str, str] | None = None,
    project_id: str | None = None,
    token: str | None = None,
) -> dict[str, Any]:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return {"returncode": None, "timed_out": True, "stdout": "", "stderr": ""}
    return {
        "returncode": result.returncode,
        "timed_out": False,
        "stdout": redact_text(result.stdout.strip(), project_id=project_id, token=token),
        "stderr": redact_text(result.stderr.strip(), project_id=project_id, token=token),
    }


def gcloud_project() -> tuple[bool, str | None]:
    try:
        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return False, None
    value = result.stdout.strip()
    if result.returncode != 0 or not value or value == "(unset)":
        return False, None
    return True, value


def access_token() -> str | None:
    try:
        result = subprocess.run(
            ["gcloud", "auth", "application-default", "print-access-token", "--quiet"],
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
    except subprocess.TimeoutExpired:
        return None
    if result.returncode != 0:
        return None
    token = result.stdout.strip()
    return token or None


def direct_rest_probe(project_id: str | None, token: str | None) -> dict[str, Any]:
    probe: dict[str, Any] = {
        "schema_version": "telos.vertex_access_path_parity.direct_rest_probe.v1",
        "attempted": False,
        "model_call_made": False,
        "provider_model_calls": 0,
        "provider_spend_observed_usd": None,
        "provider_spend_bound_usd": 0.0,
        "project_identifier_logged": False,
        "credential_material_logged": False,
        "token_logged": False,
        "selected_model": MODEL_ID,
        "vertex_location": VERTEX_LOCATION,
        "endpoint": (
            "projects/[REDACTED_GCP_PROJECT]/locations/global/publishers/google/models/"
            "gemini-3.1-pro-preview-customtools:generateContent"
        ),
        "request_max_output_tokens": 4,
        "candidate_text_committed": False,
    }
    if project_id is None or token is None:
        probe["status"] = "blocked"
        probe["blocked_reason"] = "project_or_token_unavailable"
        return probe

    url = (
        "https://aiplatform.googleapis.com/v1/"
        f"projects/{project_id}/locations/{VERTEX_LOCATION}/publishers/google/models/"
        f"{MODEL_ID}:generateContent"
    )
    body = {
        "contents": [{"role": "user", "parts": [{"text": "ping"}]}],
        "generationConfig": {"maxOutputTokens": 4, "temperature": 0},
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Goog-User-Project": project_id,
        },
        method="POST",
    )
    probe.update(
        {
            "attempted": True,
            "model_call_made": True,
            "provider_model_calls": 1,
            "provider_spend_bound_usd": SPEND_BOUND_PER_CALL,
        }
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = json.loads(response.read().decode("utf-8"))
            probe["http_status"] = response.status
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        redacted_body = redact_text(error_body, project_id=project_id, token=token)
        (PROOF / "direct_rest_probe_error_body.txt").write_text(redacted_body + "\n", encoding="utf-8")
        probe.update(
            {
                "status": "blocked",
                "http_status": exc.code,
                "error_class": "consumer_invalid_redacted"
                if "CONSUMER_INVALID" in error_body
                else "http_error_redacted",
                "redacted_error_body_path": "direct_rest_probe_error_body.txt",
                "redacted_error_body_sha256": sha256_bytes(redacted_body.encode("utf-8")),
                "redacted_consumer_invalid_present": "CONSUMER_INVALID" in redacted_body,
            }
        )
        return probe
    except (urllib.error.URLError, TimeoutError):
        probe.update(
            {
                "status": "blocked",
                "http_status": None,
                "error_class": "transport_error_redacted",
            }
        )
        return probe

    usage = payload.get("usageMetadata", {})
    candidates = payload.get("candidates", [])
    probe.update(
        {
            "status": "pass",
            "candidate_count": len(candidates),
            "usage_metadata_present": bool(usage),
            "prompt_token_count": usage.get("promptTokenCount"),
            "candidates_token_count": usage.get("candidatesTokenCount"),
            "total_token_count": usage.get("totalTokenCount"),
            "successful_endpoint_access_evidenced": True,
        }
    )
    return probe


def litellm_parity_probe(project_id: str | None, token: str | None) -> dict[str, Any]:
    probe: dict[str, Any] = {
        "schema_version": "telos.vertex_access_path_parity.litellm_probe.v1",
        "attempted": False,
        "model_call_made": False,
        "provider_model_calls": 0,
        "provider_spend_observed_usd": None,
        "provider_spend_bound_usd": 0.0,
        "credential_material_logged": False,
        "project_identifier_logged": False,
        "token_logged": False,
        "candidate_text_committed": False,
        "model_name": MODEL_NAME,
        "vertex_location": VERTEX_LOCATION,
        "request_max_tokens": 4,
    }
    if project_id is None or token is None:
        probe["status"] = "blocked"
        probe["blocked_reason"] = "project_or_token_unavailable"
        return probe
    if not CODECLASH_PYTHON.exists():
        probe["status"] = "blocked"
        probe["blocked_reason"] = "codeclash_python_unavailable"
        return probe

    code = textwrap.dedent(
        """
        import json
        import os
        from litellm import completion, completion_cost

        response = completion(
            model=os.environ["TELOS_MODEL_NAME"],
            messages=[{"role": "user", "content": "ping"}],
            temperature=0,
            max_tokens=4,
            vertex_location=os.environ["TELOS_VERTEX_LOCATION"],
            vertex_project=os.environ["TELOS_VERTEX_PROJECT"],
            extra_headers={
                "Authorization": "Bearer " + os.environ["TELOS_VERTEX_BEARER_TOKEN"],
                "X-Goog-User-Project": os.environ["TELOS_VERTEX_QUOTA_PROJECT"],
            },
        )
        usage = getattr(response, "usage", None)
        if hasattr(usage, "model_dump"):
            usage_data = usage.model_dump()
        elif isinstance(usage, dict):
            usage_data = usage
        else:
            usage_data = {}
        try:
            cost = completion_cost(completion_response=response)
        except Exception:
            cost = None
        print(json.dumps({
            "status": "pass",
            "usage_metadata_present": bool(usage_data),
            "prompt_tokens": usage_data.get("prompt_tokens") or usage_data.get("promptTokenCount"),
            "completion_tokens": usage_data.get("completion_tokens") or usage_data.get("candidatesTokenCount"),
            "total_tokens": usage_data.get("total_tokens") or usage_data.get("totalTokenCount"),
            "provider_spend_observed_usd": cost,
        }, sort_keys=True))
        """
    )
    env = os.environ.copy()
    env.update(
        {
            "TELOS_MODEL_NAME": MODEL_NAME,
            "TELOS_VERTEX_LOCATION": VERTEX_LOCATION,
            PROJECT_ENV: project_id,
            QUOTA_ENV: project_id,
            TOKEN_ENV: token,
        }
    )
    result = run_capture(
        [str(CODECLASH_PYTHON), "-c", code],
        timeout=60,
        env=env,
        project_id=project_id,
        token=token,
    )
    (PROOF / "litellm_parity_probe_stdout.txt").write_text(result["stdout"] + "\n", encoding="utf-8")
    (PROOF / "litellm_parity_probe_stderr.txt").write_text(result["stderr"] + "\n", encoding="utf-8")
    probe.update(
        {
            "attempted": True,
            "model_call_made": True,
            "provider_model_calls": 1,
            "provider_spend_bound_usd": SPEND_BOUND_PER_CALL,
            "returncode": result["returncode"],
            "timed_out": result["timed_out"],
            "stderr_class": "none" if not result["stderr"] else "stderr_redacted",
        }
    )
    if result["returncode"] != 0:
        probe["status"] = "blocked"
        probe["blocked_reason"] = "litellm_parity_probe_failed"
        probe["redacted_consumer_invalid_present"] = "CONSUMER_INVALID" in result["stderr"]
        return probe
    try:
        parsed = json.loads(result["stdout"])
    except json.JSONDecodeError:
        probe["status"] = "blocked"
        probe["blocked_reason"] = "litellm_parity_probe_stdout_not_json"
        return probe
    probe.update(redact_value(parsed, project_id=project_id, token=token))
    return probe


def classify(direct_probe: dict[str, Any], litellm_probe: dict[str, Any]) -> str:
    if direct_probe.get("status") != "pass":
        return "direct_rest_now_blocked"
    if litellm_probe.get("status") != "pass":
        return "litellm_specific_parity_gap"
    return "access_path_recovered"


def text_files_under(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for base in paths:
        candidates = [base] if base.is_file() else [path for path in base.rglob("*") if path.is_file()]
        for path in candidates:
            if path.suffix in TEXT_SUFFIXES:
                files.append(path)
    return files


def redaction_scan(paths: list[Path], *, project_id: str | None, token: str | None) -> tuple[bool, list[str]]:
    findings: list[str] = []
    placeholders = {"[REDACTED_GCP_PROJECT]", "[REDACTED_BEARER_TOKEN]", "[REDACTED_ADC_TOKEN]"}
    dynamic_needles = [
        value for value in [project_id, token] if value and len(value) > 5 and value not in placeholders
    ]
    for path in text_files_under(paths):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(needle in text for needle in dynamic_needles):
            findings.append(str(path.relative_to(ROOT)))
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(str(path.relative_to(ROOT)))
                break
    return not findings, findings


def artifact_hashes(paths: list[Path]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for base in paths:
        if base.is_file() and base.exists():
            hashes[str(base.relative_to(PROOF))] = sha256_file(base)
            continue
        if base.exists():
            for path in sorted(base.rglob("*")):
                if path.is_file():
                    hashes[str(path.relative_to(PROOF))] = sha256_file(path)
    return hashes


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    for stale in [
        PROOF / "direct_rest_probe_error_body.txt",
        PROOF / "litellm_parity_probe_stdout.txt",
        PROOF / "litellm_parity_probe_stderr.txt",
    ]:
        stale.unlink(missing_ok=True)

    iter62 = read_json(ITER62_SUMMARY)
    iter56_probe = read_json(ITER56_PROBE)
    command_manifest = read_json(ITER54_COMMANDS)
    iter62_stderr = ITER62_STDERR.read_text(encoding="utf-8")
    project_available, project_id = gcloud_project()
    token = access_token()
    preflight = {
        "schema_version": "telos.vertex_access_path_parity.preflight.v1",
        "iter62_status": iter62.get("status"),
        "iter62_blockers": iter62.get("blockers", []),
        "iter62_redacted_consumer_invalid_present": "CONSUMER_INVALID" in iter62_stderr
        and "[REDACTED_GCP_PROJECT]" in iter62_stderr,
        "iter62_provider_model_calls": iter62.get("provider_model_calls"),
        "iter62_source_path_header_override_supported": iter62.get("source_path_header_override_supported"),
        "iter56_direct_rest_probe_status": iter56_probe.get("status"),
        "iter56_direct_rest_probe_region": iter56_probe.get("region"),
        "gcloud_project_available": project_available,
        "project_identifier_logged": False,
        "adc_access_token_available": token is not None,
        "adc_token_output_suppressed": True,
        "codeclash_python_present": CODECLASH_PYTHON.exists(),
        "battle_snake_rows_executed": False,
        "excluded_pair_executed": False,
        "excluded_pair_ids": command_manifest.get("excluded_pair_ids", []),
        "provider_call_ceiling": CALL_CEILING,
        "provider_spend_ceiling_usd": SPEND_CEILING,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "cloud_runner_started": False,
    }
    write_json(PROOF / "preflight.json", redact_value(preflight, project_id=project_id, token=token))

    blockers: list[str] = []
    failures: list[str] = []
    if iter62.get("status") != "blocked":
        blockers.append("iter62_not_blocked")
    if "bearer_token_path_probe_failed" not in iter62.get("blockers", []):
        blockers.append("iter62_bearer_token_path_blocker_missing")
    if not preflight["iter62_redacted_consumer_invalid_present"]:
        blockers.append("iter62_consumer_invalid_evidence_missing")
    if iter56_probe.get("status") != "pass" or iter56_probe.get("region") != VERTEX_LOCATION:
        blockers.append("iter56_historical_direct_rest_probe_not_available")
    if not project_available or token is None:
        blockers.append("provider_token_context_unavailable")

    direct_probe = {"attempted": False, "status": "blocked", "provider_model_calls": 0}
    litellm_probe = {"attempted": False, "status": "not_run", "provider_model_calls": 0}
    if not blockers:
        direct_probe = direct_rest_probe(project_id, token)
        write_json(PROOF / "direct_rest_probe.json", redact_value(direct_probe, project_id=project_id, token=token))
        if direct_probe.get("status") != "pass":
            blockers.append("direct_rest_current_probe_failed")
    else:
        write_json(PROOF / "direct_rest_probe.json", redact_value(direct_probe, project_id=project_id, token=token))

    if not blockers and direct_probe.get("status") == "pass":
        litellm_probe = litellm_parity_probe(project_id, token)
        write_json(PROOF / "litellm_parity_probe.json", redact_value(litellm_probe, project_id=project_id, token=token))
        if litellm_probe.get("status") != "pass":
            blockers.append("litellm_parity_probe_failed")
    else:
        write_json(PROOF / "litellm_parity_probe.json", redact_value(litellm_probe, project_id=project_id, token=token))

    classification = classify(direct_probe, litellm_probe)
    provider_calls = int(direct_probe.get("provider_model_calls", 0) or 0) + int(
        litellm_probe.get("provider_model_calls", 0) or 0
    )
    provider_bound = float(direct_probe.get("provider_spend_bound_usd", 0.0) or 0.0) + float(
        litellm_probe.get("provider_spend_bound_usd", 0.0) or 0.0
    )
    observed_values = [
        value
        for value in [
            direct_probe.get("provider_spend_observed_usd"),
            litellm_probe.get("provider_spend_observed_usd"),
        ]
        if value is not None
    ]
    provider_observed = sum(float(value) for value in observed_values) if observed_values else None

    if provider_calls > CALL_CEILING:
        failures.append("provider_call_ceiling_exceeded")
    if provider_bound > SPEND_CEILING:
        failures.append("provider_spend_bound_ceiling_exceeded")
    if classification not in CLASSIFICATIONS:
        failures.append("invalid_blocker_classification")
    for key in ["battle_snake_rows_executed", "excluded_pair_executed", "gpu_used"]:
        if preflight[key]:
            failures.append(f"{key}_forbidden")
    if preflight["sentinel_named_resources_modified"] or preflight["cloud_runner_started"]:
        failures.append("forbidden_resource_or_cloud_runner_used")

    status = "fail" if failures else "blocked" if blockers else "pass"
    report = {
        "schema_version": "telos.vertex_access_path_parity.report.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "blocker_classification": classification,
        "preflight": preflight,
        "direct_rest_probe": direct_probe,
        "litellm_parity_probe": litellm_probe,
        "provider_model_calls": provider_calls,
        "provider_call_ceiling": CALL_CEILING,
        "provider_spend_observed_usd": provider_observed,
        "provider_spend_bound_usd": provider_bound,
        "provider_spend_ceiling_usd": SPEND_CEILING,
        "battle_snake_rows_executed": False,
        "excluded_pair_executed": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "cloud_runner_started": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "blockers": blockers,
        "failures": failures,
    }
    write_json(PROOF / "access_path_parity_report.json", redact_value(report, project_id=project_id, token=token))

    command_lines = [
        f"vertex access path parity recheck: {status}",
        f"iter62_status={iter62.get('status')}",
        f"direct_rest_probe_status={direct_probe.get('status')}",
        f"litellm_parity_probe_status={litellm_probe.get('status')}",
        f"blocker_classification={classification}",
        f"provider_model_calls={provider_calls}",
        f"provider_spend_observed_usd={provider_observed}",
        f"provider_spend_bound_usd={provider_bound}",
        "battle_snake_rows_executed=false",
        "excluded_pair_executed=false",
        "gpu_used=false",
        "sentinel_named_resources_modified=false",
        f"blockers={','.join(blockers)}",
        f"failures={','.join(failures)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(command_lines) + "\n", encoding="utf-8")

    scan_paths = [
        PROOF / "preflight.json",
        PROOF / "direct_rest_probe.json",
        PROOF / "litellm_parity_probe.json",
        PROOF / "access_path_parity_report.json",
        PROOF / "command_output.txt",
    ]
    for optional in [
        PROOF / "direct_rest_probe_error_body.txt",
        PROOF / "litellm_parity_probe_stdout.txt",
        PROOF / "litellm_parity_probe_stderr.txt",
    ]:
        if optional.exists():
            scan_paths.append(optional)
    scan_passed, scan_findings = redaction_scan(scan_paths, project_id=project_id, token=token)
    if not scan_passed:
        failures.append("redaction_scan_failed")
        status = "fail"
        report["status"] = status
        report["failures"] = failures
        report["redaction_scan_passed"] = False
        report["redaction_findings"] = scan_findings
        write_json(PROOF / "access_path_parity_report.json", redact_value(report, project_id=project_id, token=token))
    else:
        report["redaction_scan_passed"] = True
        report["redaction_findings"] = []
        write_json(PROOF / "access_path_parity_report.json", redact_value(report, project_id=project_id, token=token))

    result_md = f"""# Iteration 63 Result - Vertex Access Path Parity Recheck

Status: `{status.upper()}`.

## Summary

The gate rechecked the current direct REST Vertex access path and compared LiteLLM only if the
direct path was live. It did not execute any BattleSnake row or excluded pair, did not use GPU,
did not start a cloud runner, did not modify Sentinel-named resources, and did not claim a
benchmark/model result.

- iter62 status: `{iter62.get('status')}`,
- direct REST probe status: `{direct_probe.get('status')}`,
- LiteLLM parity probe status: `{litellm_probe.get('status')}`,
- blocker classification: `{classification}`,
- provider model calls: `{provider_calls}`,
- provider spend observed: `{provider_observed}`,
- provider spend bound: `{provider_bound}`,
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

## Claim Boundary

This is an access-path parity diagnostic. It is not a protocol-effect result, benchmark result,
SWE-bench score, leaderboard result, production/live-domain result, model-superiority result, or
state-of-the-art result.

## Evidence

- `proof/preflight.json`
- `proof/direct_rest_probe.json`
- `proof/litellm_parity_probe.json`
- `proof/access_path_parity_report.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_vertex_access_path_parity_recheck.json`
"""
    (EXPERIMENT / "RESULT.md").write_text(result_md, encoding="utf-8")

    review = f"""# Iteration 63 Review

`iter63` tested the smallest current access-path question after `iter62` blocked on redacted
`CONSUMER_INVALID` evidence: does direct REST still reach the selected Vertex global model, and if
so does the matching LiteLLM path also reach it?

The classification is `{classification}`. This classification is diagnostic only. It does not
prove task completion, protocol effect, model quality, leaderboard standing, production behavior,
or state-of-the-art performance.

The gate committed no bearer token, project identifier, account, service-account, VM, zone, or
credential file path. It executed no BattleSnake row, no excluded historical pair, no GPU work, no
Sentinel-named resource mutation, and no cloud-runner action.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    summary_paths = [
        PROOF / "preflight.json",
        PROOF / "direct_rest_probe.json",
        PROOF / "litellm_parity_probe.json",
        PROOF / "access_path_parity_report.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
    ]
    for optional in [
        PROOF / "direct_rest_probe_error_body.txt",
        PROOF / "litellm_parity_probe_stdout.txt",
        PROOF / "litellm_parity_probe_stderr.txt",
    ]:
        if optional.exists():
            summary_paths.append(optional)
    next_gate = NEXT_BY_CLASSIFICATION[classification]
    run_summary = {
        "schema_version": "telos.vertex_access_path_parity.summary.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "iter62_status": iter62.get("status"),
        "iter62_bearer_token_path_blocker_present": "bearer_token_path_probe_failed"
        in iter62.get("blockers", [])
        and preflight["iter62_redacted_consumer_invalid_present"],
        "iter56_historical_direct_rest_probe_status": iter56_probe.get("status"),
        "direct_rest_probe_status": direct_probe.get("status"),
        "litellm_parity_probe_status": litellm_probe.get("status"),
        "blocker_classification": classification,
        "provider_model_calls": provider_calls,
        "provider_call_ceiling": CALL_CEILING,
        "provider_spend_observed_usd": provider_observed,
        "provider_spend_bound_usd": provider_bound,
        "provider_spend_ceiling_usd": SPEND_CEILING,
        "battle_snake_rows_executed": False,
        "excluded_pair_executed": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "cloud_runner_started": False,
        "redaction_scan_passed": scan_passed,
        "redaction_findings": scan_findings,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "blockers": blockers,
        "failures": failures,
        "next_gate": next_gate,
        "artifact_hashes": artifact_hashes(summary_paths),
    }
    write_json(PROOF / "run_summary.json", redact_value(run_summary, project_id=project_id, token=token))

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": "null" if status == "fail" else status,
        "insight": (
            "Current direct REST and LiteLLM access paths both reach the selected Vertex global model."
            if status == "pass"
            else f"The current access-path blocker is classified as {classification}."
        ),
        "next_action": (
            "pre-register the exact two-row paid pilot retry using the recovered access path"
            if classification == "access_path_recovered"
            else f"pre-register {next_gate} and fix only the named access-path blocker"
        ),
        "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
        "evidence_paths": [
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            f"experiments/{EXPERIMENT_ID}/proof/access_path_parity_report.json",
            f"experiments/{EXPERIMENT_ID}/proof/direct_rest_probe.json",
            f"experiments/{EXPERIMENT_ID}/proof/valid/receipt_vertex_access_path_parity_recheck.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(VALID / "receipt_vertex_access_path_parity_recheck.json", build_receipt(status))

    print("\n".join(command_lines))
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
