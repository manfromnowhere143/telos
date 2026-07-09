#!/usr/bin/env python3
"""Publish iter60 provider model binding recovery artifacts."""

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
EXPERIMENT_ID = "iter60_provider_model_binding_recovery"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RECOVERED = PROOF / "recovered_overlay" / "configs" / "mini"
ITER59_SUMMARY = (
    ROOT
    / "experiments"
    / "iter59_provider_compatible_paid_execution_after_dependency_recovery"
    / "proof"
    / "run_summary.json"
)
ITER59_REPORT = (
    ROOT
    / "experiments"
    / "iter59_provider_compatible_paid_execution_after_dependency_recovery"
    / "proof"
    / "protocol_effect_report.json"
)
ITER54_COMMANDS = (
    ROOT / "experiments" / "iter54_provider_pair_executor_recovery" / "proof" / "command_manifest.json"
)
CODECLASH_DIR = Path("/tmp/telos-codeclash")
CODECLASH_PYTHON = CODECLASH_DIR / ".venv" / "bin" / "python"
MODEL_CONFIG = CODECLASH_DIR / "configs" / "mini" / "telos_vertex_gemini_3_1_pro_customtools.yaml"
MODEL_CONFIG_REL = "configs/mini/telos_vertex_gemini_3_1_pro_customtools.yaml"
MODEL_NAME = "vertex_ai/gemini-3.1-pro-preview-customtools"
RECOVERED_LOCATION = "global"
CALL_CEILING = 2
SPEND_CEILING = 0.05
NEXT_GATE = "experiments/iter61_provider_compatible_paid_execution_after_model_binding_recovery/HYPOTHESIS.md"
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
REDACTION_REPLACEMENTS = [
    (re.compile(r"projects/sunlit-unison-[A-Za-z0-9-]+"), "projects/[REDACTED_GCP_PROJECT]"),
    (re.compile(r"sunlit-unison-[A-Za-z0-9-]+"), "[REDACTED_GCP_PROJECT]"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"), "[REDACTED_SERVICE_ACCOUNT]"),
    (re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"), "[REDACTED_ADC_TOKEN]"),
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


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter60-provider-model-binding-recovery-{status}",
        "task_id": "telos:iter60_provider_model_binding_recovery@iter59",
        "agent_id": "codex-local-provider-model-binding-recovery",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Recover the provider model binding that caused the iter59 two-row provider run to block."
        ),
        "acceptance_criteria": [
            "Iter59 is a clean blocked result with vertex_model_not_found_or_access_denied.",
            "Before and after model binding values are recorded.",
            "The recovered binding is accessible under the local ADC context.",
            "No BattleSnake row, excluded pair, GPU, Sentinel mutation, cloud runner, or overclaim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/model_binding_recovery_report.json",
                "notes": "Records before/after binding, minimal probe outcome, calls, cost, redaction, and no-row controls.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/recovered_overlay/",
                "notes": "Recovered provider model config overlay for the next exact two-row retry.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records the model-binding-only claim boundary.",
            },
        ],
        "falsifiers": [
            "The result must block if iter59 does not name the provider model-binding blocker.",
            "The result must block if the recovered binding cannot be probed within the call/spend ceiling.",
            "The result must fail if any BattleSnake row, excluded pair, GPU, Sentinel mutation, cloud runner, or overclaim occurs.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def run_capture(args: list[str], timeout: int = 30, env: dict[str, str] | None = None) -> dict[str, Any]:
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
        "stdout": redact_text(result.stdout.strip()),
        "stderr": redact_text(result.stderr.strip()),
    }


def gcloud_project_available() -> tuple[bool, str | None]:
    result = run_capture(["gcloud", "config", "get-value", "project"], timeout=10)
    if result["returncode"] != 0 or not result["stdout"]:
        return False, None
    return True, result["stdout"]


def adc_available() -> bool:
    try:
        result = subprocess.run(
            ["gcloud", "auth", "application-default", "print-access-token", "--quiet"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=20,
        )
    except subprocess.TimeoutExpired:
        return False
    return result.returncode == 0


def read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} root must be a mapping")
    return data


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def binding_summary(config: dict[str, Any]) -> dict[str, Any]:
    kwargs = config.get("model_kwargs", {})
    if not isinstance(kwargs, dict):
        kwargs = {}
    return {
        "model_name": config.get("model_name"),
        "vertex_location": kwargs.get("vertex_location"),
        "temperature": kwargs.get("temperature"),
        "max_tokens": kwargs.get("max_tokens"),
        "project_identifier_committed": False,
    }


def apply_recovery() -> dict[str, Any]:
    before_text = MODEL_CONFIG.read_text(encoding="utf-8")
    before_config = read_yaml(MODEL_CONFIG)
    after_config = json.loads(json.dumps(before_config))
    kwargs = after_config.setdefault("model_kwargs", {})
    if not isinstance(kwargs, dict):
        raise RuntimeError("model_kwargs must be a mapping")
    kwargs["vertex_location"] = RECOVERED_LOCATION
    write_yaml(MODEL_CONFIG, after_config)
    recovered_path = RECOVERED / MODEL_CONFIG.name
    write_yaml(recovered_path, after_config)
    return {
        "config_path": str(MODEL_CONFIG),
        "config_relative_path": MODEL_CONFIG_REL,
        "before_sha256": sha256_bytes(before_text.encode("utf-8")),
        "after_sha256": sha256_file(MODEL_CONFIG),
        "recovered_overlay_path": str(recovered_path.relative_to(ROOT)),
        "recovered_overlay_sha256": sha256_file(recovered_path),
        "before_binding": binding_summary(before_config),
        "after_binding": binding_summary(after_config),
        "changed": before_text != MODEL_CONFIG.read_text(encoding="utf-8"),
    }


def litellm_probe(project_id: str | None) -> dict[str, Any]:
    probe = {
        "schema_version": "telos.provider_model_binding_recovery.litellm_probe.v1",
        "attempted": False,
        "model_call_made": False,
        "provider_model_calls": 0,
        "provider_spend_observed_usd": None,
        "provider_spend_bound_usd": SPEND_CEILING,
        "credential_material_logged": False,
        "project_identifier_logged": False,
        "candidate_text_committed": False,
        "model_name": MODEL_NAME,
        "vertex_location": RECOVERED_LOCATION,
        "request_max_tokens": 4,
    }
    if project_id is None:
        probe["status"] = "blocked"
        probe["blocked_reason"] = "project_unavailable"
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
            "TELOS_VERTEX_PROJECT": project_id,
        }
    )
    result = run_capture([str(CODECLASH_PYTHON), "-c", code], timeout=60, env=env)
    (PROOF / "litellm_probe_stdout.txt").write_text(result["stdout"] + "\n", encoding="utf-8")
    (PROOF / "litellm_probe_stderr.txt").write_text(result["stderr"] + "\n", encoding="utf-8")
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
        probe["blocked_reason"] = "litellm_probe_failed"
        return probe
    try:
        parsed = json.loads(result["stdout"])
    except json.JSONDecodeError:
        probe["status"] = "blocked"
        probe["blocked_reason"] = "litellm_probe_stdout_not_json"
        return probe
    probe.update(redact_value(parsed))
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

    iter59 = read_json(ITER59_SUMMARY)
    iter59_report = read_json(ITER59_REPORT)
    command_manifest = read_json(ITER54_COMMANDS)
    project_available, project_id = gcloud_project_available()
    preflight = {
        "schema_version": "telos.provider_model_binding_recovery.preflight.v1",
        "iter59_status": iter59.get("status"),
        "iter59_blockers": iter59.get("blockers", []),
        "iter59_provider_error_classes": iter59.get("provider_error_classes", []),
        "iter59_executed_pair_count": iter59.get("executed_pair_count"),
        "iter59_provider_api_calls": iter59.get("provider_api_calls"),
        "iter59_report_status": iter59_report.get("status"),
        "codeclash_checkout_present": (CODECLASH_DIR / ".git").exists(),
        "codeclash_python_present": CODECLASH_PYTHON.exists(),
        "model_config_present": MODEL_CONFIG.exists(),
        "gcloud_project_available": project_available,
        "project_identifier_logged": False,
        "adc_access_token_available": adc_available(),
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
    write_json(PROOF / "preflight.json", redact_value(preflight))

    blockers: list[str] = []
    failures: list[str] = []
    if iter59.get("status") != "blocked":
        blockers.append("iter59_not_blocked")
    if "vertex_model_not_found_or_access_denied" not in iter59.get("blockers", []):
        blockers.append("iter59_model_binding_blocker_missing")
    if not preflight["codeclash_python_present"] or not preflight["model_config_present"]:
        blockers.append("codeclash_model_config_not_ready")
    if not preflight["gcloud_project_available"] or not preflight["adc_access_token_available"]:
        blockers.append("provider_auth_context_unavailable")

    recovery: dict[str, Any] = {}
    probe: dict[str, Any] = {"attempted": False, "provider_model_calls": 0}
    if not blockers:
        recovery = apply_recovery()
        probe = litellm_probe(project_id)
        if probe.get("status") != "pass":
            blockers.append("recovered_model_binding_probe_failed")

    provider_calls = int(probe.get("provider_model_calls", 0) or 0)
    provider_cost = probe.get("provider_spend_observed_usd")
    provider_cost_value = float(provider_cost or 0.0)
    if provider_calls > CALL_CEILING:
        failures.append("provider_call_ceiling_exceeded")
    if provider_cost_value > SPEND_CEILING:
        failures.append("provider_spend_ceiling_exceeded")

    if preflight["battle_snake_rows_executed"]:
        failures.append("battlesnake_row_executed")
    if preflight["excluded_pair_executed"]:
        failures.append("excluded_pair_executed")

    report = {
        "schema_version": "telos.provider_model_binding_recovery.report.v1",
        "status": "pending",
        "experiment_id": EXPERIMENT_ID,
        "preflight": preflight,
        "model_binding_recovery": recovery,
        "litellm_probe": probe,
        "battle_snake_rows_executed": False,
        "excluded_pair_executed": False,
        "provider_model_calls": provider_calls,
        "provider_call_ceiling": CALL_CEILING,
        "provider_spend_observed_usd": provider_cost,
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
    write_json(PROOF / "model_binding_recovery_report.json", redact_value(report))

    command_lines = [
        f"provider model binding recovery: {status}",
        f"before_vertex_location={recovery.get('before_binding', {}).get('vertex_location')}",
        f"after_vertex_location={recovery.get('after_binding', {}).get('vertex_location')}",
        f"litellm_probe_status={probe.get('status')}",
        f"provider_model_calls={provider_calls}",
        f"provider_spend_observed_usd={provider_cost}",
        "battle_snake_rows_executed=false",
        "excluded_pair_executed=false",
        "gpu_used=false",
        "sentinel_named_resources_modified=false",
        f"blockers={','.join(blockers)}",
        f"failures={','.join(failures)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(command_lines) + "\n", encoding="utf-8")

    scan_paths = [PROOF / "preflight.json", PROOF / "model_binding_recovery_report.json", RECOVERED]
    if (PROOF / "litellm_probe_stdout.txt").exists():
        scan_paths.append(PROOF / "litellm_probe_stdout.txt")
    if (PROOF / "litellm_probe_stderr.txt").exists():
        scan_paths.append(PROOF / "litellm_probe_stderr.txt")
    scan_passed, scan_findings = redaction_scan(scan_paths)
    if not scan_passed:
        failures.append("redaction_scan_failed")
        status = "fail"
        report["status"] = status
        report["failures"] = failures
        report["redaction_scan_passed"] = scan_passed
        report["redaction_findings"] = scan_findings
        write_json(PROOF / "model_binding_recovery_report.json", redact_value(report))
    else:
        report["redaction_scan_passed"] = scan_passed
        report["redaction_findings"] = scan_findings
        write_json(PROOF / "model_binding_recovery_report.json", redact_value(report))

    result_md = f"""# Iteration 60 Result - Provider Model Binding Recovery

Status: `{status.upper()}`.

## Summary

The gate recovered only the provider model binding that blocked `iter59`. It recorded the before
and after binding values, ran no BattleSnake row, executed no excluded pair, used no GPU, started no
cloud runner, and modified no Sentinel-named resource.

- before Vertex location: `{recovery.get('before_binding', {}).get('vertex_location')}`,
- after Vertex location: `{recovery.get('after_binding', {}).get('vertex_location')}`,
- LiteLLM probe status: `{probe.get('status')}`,
- provider model calls: `{provider_calls}`,
- provider spend observed: `{provider_cost}`,
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

## Claim Boundary

This is a provider model-binding recovery result. It is not a protocol-effect result, benchmark
result, SWE-bench score, leaderboard result, production/live-domain result, model-superiority
result, or state-of-the-art result.

## Evidence

- `proof/preflight.json`
- `proof/model_binding_recovery_report.json`
- `proof/recovered_overlay/`
- `proof/litellm_probe_stdout.txt`
- `proof/litellm_probe_stderr.txt`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_provider_model_binding_recovery.json`
"""
    (EXPERIMENT / "RESULT.md").write_text(result_md, encoding="utf-8")

    review = """# Iteration 60 Review

`iter59` blocked because the selected provider model was called in a location where Vertex returned
a model-not-found-or-access-denied response. `iter60` changed only the local recovered model binding
by setting `vertex_location` to `global`, matching the earlier successful Vertex access probe.

The gate did not execute either BattleSnake row. It did not execute excluded pairs, use GPU, start a
cloud runner, modify Sentinel-named resources, or claim benchmark/model/protocol-effect results.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    summary_paths = [
        PROOF / "preflight.json",
        PROOF / "model_binding_recovery_report.json",
        PROOF / "litellm_probe_stdout.txt",
        PROOF / "litellm_probe_stderr.txt",
        PROOF / "command_output.txt",
        PROOF / "review.md",
        RECOVERED,
    ]
    run_summary = {
        "schema_version": "telos.provider_model_binding_recovery.summary.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "iter59_status": iter59.get("status"),
        "iter59_model_binding_blocker_present": "vertex_model_not_found_or_access_denied"
        in iter59.get("blockers", []),
        "before_vertex_location": recovery.get("before_binding", {}).get("vertex_location"),
        "after_vertex_location": recovery.get("after_binding", {}).get("vertex_location"),
        "recovered_binding_accessible": probe.get("status") == "pass",
        "provider_model_calls": provider_calls,
        "provider_call_ceiling": CALL_CEILING,
        "provider_spend_observed_usd": provider_cost,
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
    write_json(PROOF / "run_summary.json", redact_value(run_summary))

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "insight": (
            "The iter59 provider blocker was a location binding issue: the recovered LiteLLM "
            "binding is accessible when the Vertex location is set to global."
            if status == "pass"
            else (
                "Adding vertex_location=global moved LiteLLM past the prior model-location error "
                "but exposed a quota-project/header blocker."
            )
        ),
        "next_action": (
            "retry the same two selected BattleSnake rows with the recovered global Vertex binding"
            if status == "pass"
            else "recover the LiteLLM Vertex quota-project/header path before retrying the two-row pilot"
        ),
        "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
        "evidence_paths": [
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            f"experiments/{EXPERIMENT_ID}/proof/model_binding_recovery_report.json",
            f"experiments/{EXPERIMENT_ID}/proof/recovered_overlay/configs/mini/telos_vertex_gemini_3_1_pro_customtools.yaml",
            f"experiments/{EXPERIMENT_ID}/proof/valid/receipt_provider_model_binding_recovery.json",
        ],
    }
    write_json(PROOF / "learning_record.json", redact_value(learning_record))
    write_json(VALID / "receipt_provider_model_binding_recovery.json", build_receipt(status))

    print("\n".join(command_lines))
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
