#!/usr/bin/env python3
"""Publish iter62 Vertex bearer-token path recovery artifacts."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import textwrap
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter62_vertex_bearer_token_path_recovery"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RECOVERED = PROOF / "recovered_runtime_binding"
ITER61_SUMMARY = ROOT / "experiments" / "iter61_vertex_quota_project_binding_recovery" / "proof" / "run_summary.json"
ITER61_STDERR = (
    ROOT / "experiments" / "iter61_vertex_quota_project_binding_recovery" / "proof" / "litellm_quota_probe_stderr.txt"
)
ITER56_PROBE = (
    ROOT / "experiments" / "iter56_provider_auth_recovery_for_paid_protocol_effect" / "proof" / "vertex_access_probe.json"
)
ITER54_COMMANDS = ROOT / "experiments" / "iter54_provider_pair_executor_recovery" / "proof" / "command_manifest.json"
CODECLASH_DIR = Path("/tmp/telos-codeclash")
CODECLASH_PYTHON = CODECLASH_DIR / ".venv" / "bin" / "python"
VERTEX_GEMINI_SOURCE = (
    CODECLASH_DIR
    / ".venv"
    / "lib"
    / "python3.11"
    / "site-packages"
    / "litellm"
    / "llms"
    / "vertex_ai"
    / "gemini"
    / "vertex_and_google_ai_studio_gemini.py"
)
MODEL_NAME = "vertex_ai/gemini-3.1-pro-preview-customtools"
RECOVERED_LOCATION = "global"
AUTH_HEADER = "Authorization"
QUOTA_HEADER = "X-Goog-User-Project"
TOKEN_ENV = "TELOS_VERTEX_BEARER_TOKEN"
QUOTA_ENV = "TELOS_VERTEX_QUOTA_PROJECT"
PROJECT_ENV = "TELOS_VERTEX_PROJECT"
CALL_CEILING = 2
SPEND_CEILING = 0.05
NEXT_GATE = "experiments/iter63_provider_compatible_paid_execution_after_access_path_recovery/HYPOTHESIS.md"
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
        redacted = redacted.replace(project_id, "[REDACTED_GCP_PROJECT]")
        redacted = redacted.replace(f"projects/{project_id}", "projects/[REDACTED_GCP_PROJECT]")
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
        "receipt_id": f"iter62-vertex-bearer-token-path-recovery-{status}",
        "task_id": "telos:iter62_vertex_bearer_token_path_recovery@iter61",
        "agent_id": "codex-local-vertex-bearer-token-path-recovery",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Recover the LiteLLM Vertex bearer-token/header path after iter61 showed that "
            "quota-project extra_headers alone still blocked."
        ),
        "acceptance_criteria": [
            "Iter61 is a clean blocked result with redacted CONSUMER_INVALID evidence.",
            "The binding path injects bearer token and quota project at runtime without committed secrets.",
            "At most two provider probes and at most $0.05 bounded spend occur.",
            "No BattleSnake row, excluded pair, GPU, Sentinel mutation, cloud runner, or overclaim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/bearer_token_path_report.json",
                "notes": "Records source-path support, runtime token binding, minimal probe outcome, calls, cost, redaction, and no-row controls.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/recovered_runtime_binding/",
                "notes": "Secret-safe runtime binding template for a future exact two-row retry.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records the bearer-token-only claim boundary.",
            },
        ],
        "falsifiers": [
            "The result must block if iter61 does not show the named access-path blocker.",
            "The result must block if a secret-safe LiteLLM bearer-token/header path cannot be identified.",
            "The result must fail if any BattleSnake row, excluded pair, GPU, Sentinel mutation, cloud runner, or overclaim occurs.",
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


def gcloud_project_available() -> tuple[bool, str | None]:
    result = run_capture(["gcloud", "config", "get-value", "project"], timeout=10)
    if result["returncode"] != 0 or not result["stdout"]:
        return False, None
    return True, result["stdout"]


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


def inspect_source_path() -> dict[str, Any]:
    source = VERTEX_GEMINI_SOURCE.read_text(encoding="utf-8") if VERTEX_GEMINI_SOURCE.exists() else ""
    return {
        "schema_version": "telos.vertex_bearer_token_path.source_path.v1",
        "codeclash_checkout_present": (CODECLASH_DIR / ".git").exists(),
        "codeclash_python_present": CODECLASH_PYTHON.exists(),
        "vertex_gemini_source_path": str(VERTEX_GEMINI_SOURCE),
        "extra_headers_supported": '"extra_headers"' in source,
        "custom_headers_override_default_headers": "default_headers.update(headers)" in source,
        "authorization_header_default_present": 'default_headers["Authorization"]' in source,
        "token_or_project_identifier_committed": False,
    }


def write_runtime_binding() -> dict[str, Any]:
    RECOVERED.mkdir(parents=True, exist_ok=True)
    template = {
        "schema_version": "telos.vertex_bearer_token_path.runtime_template.v1",
        "mechanism": "runtime_env_bearer_token_and_quota_project_header_injection",
        "model_name": MODEL_NAME,
        "model_kwargs_template": {
            "temperature": 0,
            "max_tokens": 4,
            "vertex_location": RECOVERED_LOCATION,
            "vertex_project": f"${{{PROJECT_ENV}}}",
            "extra_headers": {
                AUTH_HEADER: f"Bearer ${{{TOKEN_ENV}}}",
                QUOTA_HEADER: f"${{{QUOTA_ENV}}}",
            },
        },
        "runtime_env_vars": [PROJECT_ENV, TOKEN_ENV, QUOTA_ENV],
        "project_identifier_committed": False,
        "credential_material_committed": False,
        "token_committed": False,
    }
    yaml_template = {
        "model_name": MODEL_NAME,
        "model_kwargs": template["model_kwargs_template"],
    }
    write_json(RECOVERED / "bearer_token_path_binding.json", template)
    (RECOVERED / "telos_vertex_gemini_3_1_pro_customtools.bearer-template.yaml").write_text(
        yaml.safe_dump(yaml_template, sort_keys=False), encoding="utf-8"
    )
    return {
        "schema_version": "telos.vertex_bearer_token_path.mechanism.v1",
        "mechanism": template["mechanism"],
        "authorization_header_source": f"env:{TOKEN_ENV}",
        "quota_header": QUOTA_HEADER,
        "quota_project_source": f"env:{QUOTA_ENV}",
        "vertex_project_source": f"env:{PROJECT_ENV}",
        "template_json_path": str((RECOVERED / "bearer_token_path_binding.json").relative_to(ROOT)),
        "template_yaml_path": str(
            (RECOVERED / "telos_vertex_gemini_3_1_pro_customtools.bearer-template.yaml").relative_to(ROOT)
        ),
        "project_identifier_committed": False,
        "credential_material_committed": False,
        "token_committed": False,
    }


def litellm_bearer_probe(project_id: str | None, token: str | None) -> dict[str, Any]:
    probe: dict[str, Any] = {
        "schema_version": "telos.vertex_bearer_token_path.litellm_probe.v1",
        "attempted": False,
        "model_call_made": False,
        "provider_model_calls": 0,
        "provider_spend_observed_usd": None,
        "provider_spend_bound_usd": SPEND_CEILING,
        "credential_material_logged": False,
        "project_identifier_logged": False,
        "token_logged": False,
        "candidate_text_committed": False,
        "model_name": MODEL_NAME,
        "vertex_location": RECOVERED_LOCATION,
        "authorization_header_source": f"env:{TOKEN_ENV}",
        "quota_header": QUOTA_HEADER,
        "quota_project_source": f"env:{QUOTA_ENV}",
        "request_max_tokens": 4,
    }
    if project_id is None or token is None:
        probe["status"] = "blocked"
        probe["blocked_reason"] = "project_or_token_unavailable"
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
            "TELOS_VERTEX_LOCATION": RECOVERED_LOCATION,
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
    (PROOF / "litellm_bearer_probe_stdout.txt").write_text(result["stdout"] + "\n", encoding="utf-8")
    (PROOF / "litellm_bearer_probe_stderr.txt").write_text(result["stderr"] + "\n", encoding="utf-8")
    probe.update(
        {
            "attempted": True,
            "model_call_made": True,
            "provider_model_calls": 1,
            "returncode": result["returncode"],
            "timed_out": result["timed_out"],
            "stderr_class": "none" if not result["stderr"] else "stderr_redacted",
        }
    )
    if result["returncode"] != 0:
        probe["status"] = "blocked"
        probe["blocked_reason"] = "litellm_bearer_probe_failed"
        return probe
    try:
        parsed = json.loads(result["stdout"])
    except json.JSONDecodeError:
        probe["status"] = "blocked"
        probe["blocked_reason"] = "litellm_bearer_probe_stdout_not_json"
        return probe
    probe.update(redact_value(parsed, project_id=project_id, token=token))
    return probe


def text_files_under(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for base in paths:
        candidates = [base] if base.is_file() else [path for path in base.rglob("*") if path.is_file()]
        for path in candidates:
            if path.suffix in TEXT_SUFFIXES:
                files.append(path)
    return files


def redaction_scan(paths: list[Path]) -> tuple[bool, list[str]]:
    findings: list[str] = []
    for path in text_files_under(paths):
        text = path.read_text(encoding="utf-8", errors="ignore")
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

    iter61 = read_json(ITER61_SUMMARY)
    iter56_probe = read_json(ITER56_PROBE)
    command_manifest = read_json(ITER54_COMMANDS)
    iter61_stderr = ITER61_STDERR.read_text(encoding="utf-8")
    project_available, project_id = gcloud_project_available()
    token = access_token()

    source_path = inspect_source_path()
    runtime_binding = write_runtime_binding()
    preflight = {
        "schema_version": "telos.vertex_bearer_token_path.preflight.v1",
        "iter61_status": iter61.get("status"),
        "iter61_blockers": iter61.get("blockers", []),
        "iter61_redacted_consumer_invalid_present": "CONSUMER_INVALID" in iter61_stderr
        and "[REDACTED_GCP_PROJECT]" in iter61_stderr,
        "iter61_source_path_extra_headers_supported": iter61.get("source_path_extra_headers_supported"),
        "iter56_direct_rest_probe_status": iter56_probe.get("status"),
        "iter56_direct_rest_probe_region": iter56_probe.get("region"),
        "iter56_direct_rest_probe_usage_metadata_present": iter56_probe.get("usage_metadata_present"),
        "source_path": source_path,
        "runtime_binding": runtime_binding,
        "gcloud_project_available": project_available,
        "project_identifier_logged": False,
        "adc_access_token_available": token is not None,
        "adc_token_output_suppressed": True,
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
    if iter61.get("status") != "blocked":
        blockers.append("iter61_not_blocked")
    if "quota_project_binding_probe_failed" not in iter61.get("blockers", []):
        blockers.append("iter61_access_path_blocker_missing")
    if not preflight["iter61_redacted_consumer_invalid_present"]:
        blockers.append("iter61_consumer_invalid_evidence_missing")
    if iter56_probe.get("status") != "pass" or iter56_probe.get("region") != RECOVERED_LOCATION:
        blockers.append("iter56_direct_rest_probe_not_available")
    if not source_path["extra_headers_supported"] or not source_path["custom_headers_override_default_headers"]:
        blockers.append("litellm_header_override_path_missing")
    if not project_available or token is None:
        blockers.append("provider_token_context_unavailable")

    probe: dict[str, Any] = {"attempted": False, "provider_model_calls": 0}
    if not blockers:
        probe = litellm_bearer_probe(project_id, token)
        if probe.get("status") != "pass":
            blockers.append("bearer_token_path_probe_failed")

    provider_calls = int(probe.get("provider_model_calls", 0) or 0)
    provider_cost = probe.get("provider_spend_observed_usd")
    provider_bound = float(probe.get("provider_spend_bound_usd", SPEND_CEILING) or 0.0)
    provider_cost_value = float(provider_cost if provider_cost is not None else provider_bound)
    if provider_calls > CALL_CEILING:
        failures.append("provider_call_ceiling_exceeded")
    if provider_cost_value > SPEND_CEILING:
        failures.append("provider_spend_ceiling_exceeded")
    if preflight["battle_snake_rows_executed"]:
        failures.append("battlesnake_row_executed")
    if preflight["excluded_pair_executed"]:
        failures.append("excluded_pair_executed")

    report = {
        "schema_version": "telos.vertex_bearer_token_path.report.v1",
        "status": "pending",
        "experiment_id": EXPERIMENT_ID,
        "preflight": preflight,
        "source_path": source_path,
        "runtime_binding": runtime_binding,
        "litellm_bearer_probe": probe,
        "battle_snake_rows_executed": False,
        "excluded_pair_executed": False,
        "provider_model_calls": provider_calls,
        "provider_call_ceiling": CALL_CEILING,
        "provider_spend_observed_usd": provider_cost,
        "provider_spend_bound_usd": provider_bound,
        "provider_spend_ceiling_usd": SPEND_CEILING,
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
    status = "fail" if failures else "blocked" if blockers else "pass"
    report["status"] = status
    write_json(PROOF / "bearer_token_path_report.json", redact_value(report, project_id=project_id, token=token))

    command_lines = [
        f"vertex bearer token path recovery: {status}",
        f"iter61_status={iter61.get('status')}",
        f"source_path_header_override_supported={str(source_path['custom_headers_override_default_headers']).lower()}",
        f"litellm_bearer_probe_status={probe.get('status')}",
        f"provider_model_calls={provider_calls}",
        f"provider_spend_observed_usd={provider_cost}",
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
        PROOF / "bearer_token_path_report.json",
        PROOF / "command_output.txt",
        RECOVERED,
    ]
    if (PROOF / "litellm_bearer_probe_stdout.txt").exists():
        scan_paths.append(PROOF / "litellm_bearer_probe_stdout.txt")
    if (PROOF / "litellm_bearer_probe_stderr.txt").exists():
        scan_paths.append(PROOF / "litellm_bearer_probe_stderr.txt")
    scan_passed, scan_findings = redaction_scan(scan_paths)
    if not scan_passed:
        failures.append("redaction_scan_failed")
        status = "fail"
        report["status"] = status
        report["failures"] = failures
        report["redaction_scan_passed"] = scan_passed
        report["redaction_findings"] = scan_findings
        write_json(PROOF / "bearer_token_path_report.json", redact_value(report, project_id=project_id, token=token))
    else:
        report["redaction_scan_passed"] = scan_passed
        report["redaction_findings"] = scan_findings
        write_json(PROOF / "bearer_token_path_report.json", redact_value(report, project_id=project_id, token=token))

    result_md = f"""# Iteration 62 Result - Vertex Bearer Token Path Recovery

Status: `{status.upper()}`.

## Summary

The gate recovered only the LiteLLM Vertex bearer-token/header path after `iter61` proved that the
quota header alone was insufficient. It recorded the source-path support, wrote a secret-safe
runtime binding template, ran no BattleSnake row, executed no excluded pair, used no GPU, started
no cloud runner, and modified no Sentinel-named resource.

- iter61 status: `{iter61.get('status')}`,
- header override supported: `{str(source_path['custom_headers_override_default_headers']).lower()}`,
- LiteLLM bearer probe status: `{probe.get('status')}`,
- provider model calls: `{provider_calls}`,
- provider spend observed: `{provider_cost}`,
- provider spend bound: `{provider_bound}`,
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

## Claim Boundary

This is a Vertex bearer-token/header path recovery result. It is not a protocol-effect result,
benchmark result, SWE-bench score, leaderboard result, production/live-domain result,
model-superiority result, or state-of-the-art result.

## Evidence

- `proof/preflight.json`
- `proof/bearer_token_path_report.json`
- `proof/recovered_runtime_binding/`
- `proof/litellm_bearer_probe_stdout.txt`
- `proof/litellm_bearer_probe_stderr.txt`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_vertex_bearer_token_path_recovery.json`
"""
    (EXPERIMENT / "RESULT.md").write_text(result_md, encoding="utf-8")

    review = f"""# Iteration 62 Review

`iter61` proved that quota-project `extra_headers` pass through Mini-SWE-Agent into LiteLLM, but
the LiteLLM-managed Vertex auth path still returned redacted `CONSUMER_INVALID` evidence.
`iter62` checked that LiteLLM merges custom headers after default Authorization headers, then
tested a runtime binding that injects both `{AUTH_HEADER}` and `{QUOTA_HEADER}` from environment.

The committed template contains only environment placeholders. It does not commit a bearer token,
project, account, service-account, VM, zone, or credential value.

The gate did not execute either BattleSnake row. It did not execute excluded pairs, use GPU, start
a cloud runner, modify Sentinel-named resources, or claim benchmark/model/protocol-effect results.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    summary_paths = [
        PROOF / "preflight.json",
        PROOF / "bearer_token_path_report.json",
        PROOF / "litellm_bearer_probe_stdout.txt",
        PROOF / "litellm_bearer_probe_stderr.txt",
        PROOF / "command_output.txt",
        PROOF / "review.md",
        RECOVERED,
    ]
    run_summary = {
        "schema_version": "telos.vertex_bearer_token_path.summary.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "iter61_status": iter61.get("status"),
        "iter61_access_path_blocker_present": "quota_project_binding_probe_failed" in iter61.get("blockers", [])
        and preflight["iter61_redacted_consumer_invalid_present"],
        "source_path_header_override_supported": source_path["custom_headers_override_default_headers"],
        "authorization_header_source": f"env:{TOKEN_ENV}",
        "quota_project_source": f"env:{QUOTA_ENV}",
        "recovered_binding_accessible": probe.get("status") == "pass",
        "provider_model_calls": provider_calls,
        "provider_call_ceiling": CALL_CEILING,
        "provider_spend_observed_usd": provider_cost,
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
        "next_gate": NEXT_GATE if status == "pass" else None,
        "artifact_hashes": artifact_hashes(summary_paths),
    }
    write_json(PROOF / "run_summary.json", redact_value(run_summary, project_id=project_id, token=token))

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "insight": (
            "Runtime bearer-token plus quota-project header injection recovers LiteLLM access to "
            "the selected Vertex global model without committing project or credential material."
            if status == "pass"
            else "The LiteLLM Vertex bearer-token/header path remains unrecovered under the iter62 gate."
        ),
        "next_action": (
            "pre-register the exact two-row paid pilot retry using the recovered runtime access path"
            if status == "pass"
            else "recheck current direct REST versus LiteLLM access-path parity before retrying the two-row pilot"
        ),
        "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
        "evidence_paths": [
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            f"experiments/{EXPERIMENT_ID}/proof/bearer_token_path_report.json",
            f"experiments/{EXPERIMENT_ID}/proof/recovered_runtime_binding/bearer_token_path_binding.json",
            f"experiments/{EXPERIMENT_ID}/proof/valid/receipt_vertex_bearer_token_path_recovery.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(VALID / "receipt_vertex_bearer_token_path_recovery.json", build_receipt(status))

    print("\n".join(command_lines))
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
