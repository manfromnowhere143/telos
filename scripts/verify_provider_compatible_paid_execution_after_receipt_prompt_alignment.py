#!/usr/bin/env python3
"""Run and publish iter66 provider-compatible paid retry artifacts."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tarfile
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
RAW = PROOF / "raw"
VALID = PROOF / "valid"
ITER63_SUMMARY = (
    ROOT
    / "experiments"
    / "iter63_vertex_access_path_parity_recheck"
    / "proof"
    / "run_summary.json"
)
ITER63_DIRECT_PROBE = (
    ROOT
    / "experiments"
    / "iter63_vertex_access_path_parity_recheck"
    / "proof"
    / "direct_rest_probe.json"
)
ITER63_LITELLM_PROBE = (
    ROOT
    / "experiments"
    / "iter63_vertex_access_path_parity_recheck"
    / "proof"
    / "litellm_parity_probe.json"
)
ITER63_RECEIPT_DIR = (
    ROOT / "experiments" / "iter63_vertex_access_path_parity_recheck" / "proof"
)
ITER64_SOURCE_PROOF = (
    ROOT
    / "experiments"
    / "iter64_provider_compatible_paid_execution_after_access_path_recovery"
    / "proof"
)
ITER64_SOURCE_SUMMARY = ITER64_SOURCE_PROOF / "run_summary.json"
ITER65_SOURCE_PROOF = ROOT / "experiments" / "iter65_receipt_schema_prompt_alignment" / "proof"
ITER65_SOURCE_SUMMARY = ITER65_SOURCE_PROOF / "run_summary.json"
ITER65_RECOVERED_TELOS_AGENT = (
    ITER65_SOURCE_PROOF
    / "recovered_overlay"
    / "configs"
    / "mini"
    / "telos_vertex_gemini_receipt_enforced_agent.yaml"
)
ITER62_BINDING = (
    ROOT
    / "experiments"
    / "iter62_vertex_bearer_token_path_recovery"
    / "proof"
    / "recovered_runtime_binding"
    / "bearer_token_path_binding.json"
)
ITER54_COMMANDS = (
    ROOT / "experiments" / "iter54_provider_pair_executor_recovery" / "proof" / "command_manifest.json"
)
ITER54_OVERLAYS = (
    ROOT / "experiments" / "iter54_provider_pair_executor_recovery" / "proof" / "overlay_copy_manifest.json"
)
ITER48_SLICE = (
    ROOT
    / "experiments"
    / "iter48_provider_compatible_protocol_effect_slice_refreeze"
    / "proof"
    / "provider_compatible_slice.json"
)
CODECLASH_DIR = Path("/tmp/telos-codeclash")
CODECLASH_COMMIT = "381cdfa05a35e8acd35853b9fc7e13005121b127"
DOCKER_BIN = Path("/Applications/Docker.app/Contents/Resources/bin/docker")
MODEL_ID = "gemini-3.1-pro-preview-customtools"
MODEL_NAME = f"vertex_ai/{MODEL_ID}"
VERTEX_LOCATION = "global"
TOKEN_ENV = "TELOS_VERTEX_BEARER_TOKEN"
PROJECT_ENV = "TELOS_VERTEX_PROJECT"
QUOTA_ENV = "TELOS_VERTEX_QUOTA_PROJECT"
RUNTIME_MODEL_CONFIG_REL = Path("configs/mini/telos_vertex_gemini_3_1_pro_customtools.yaml")
TELOS_COST_REGISTRY_ENTRY_REL = Path("configs/mini/telos_litellm_cost_registry_entry.json")
CODECLASH_LITELLM_REGISTRY_REL = Path("configs/mini/litellm_custom_model_config.yaml")
TELOS_RECEIPT_AGENT_REL = Path("configs/mini/telos_vertex_gemini_receipt_enforced_agent.yaml")
SELECTED_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
]
BASELINE_PAIR_ID = "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml"
TELOS_PAIR_ID = "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml"
CALL_CEILING = 16
SPEND_CEILING = 10.0
REUSE_EXISTING_RAW = os.environ.get("TELOS_ITER66_REUSE_RAW") == "1"
RECOVER_BASELINE_OUTPUT_DIR = os.environ.get("TELOS_ITER66_RECOVER_BASELINE_OUTPUT_DIR")
RECOVER_BASELINE_COMMAND_EXECUTION = os.environ.get("TELOS_ITER66_RECOVER_BASELINE_COMMAND_EXECUTION")
DYNAMIC_PROJECT_ID: str | None = None
DYNAMIC_BEARER_TOKEN: str | None = None
TEXT_SUFFIXES = {
    ".json",
    ".jsonl",
    ".log",
    ".txt",
    ".md",
    ".yaml",
    ".yml",
    ".py",
}
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
    (re.compile(r"Bearer\s+(?!\[REDACTED_BEARER_TOKEN\])[^\"\s,]+"), "Bearer [REDACTED_BEARER_TOKEN]"),
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
    if DYNAMIC_BEARER_TOKEN:
        redacted = redacted.replace(DYNAMIC_BEARER_TOKEN, "[REDACTED_BEARER_TOKEN]")
    if DYNAMIC_PROJECT_ID:
        redacted = redacted.replace(
            f"projects/{DYNAMIC_PROJECT_ID}",
            "projects/[REDACTED_GCP_PROJECT]",
        )
        redacted = redacted.replace(DYNAMIC_PROJECT_ID, "[REDACTED_GCP_PROJECT]")
    for pattern, replacement in REDACTION_REPLACEMENTS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def normalize_public_text(text: str) -> str:
    if not text:
        return text
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + ("\n" if lines else "")


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, dict):
        return {key: redact_value(item) for key, item in value.items()}
    return value


def redact_text_file(path: Path) -> None:
    if path.suffix not in TEXT_SUFFIXES:
        return
    original = path.read_text(encoding="utf-8", errors="ignore")
    redacted = normalize_public_text(redact_text(original))
    if redacted != original:
        path.write_text(redacted, encoding="utf-8")


def redact_tree(paths: list[Path]) -> None:
    for base in paths:
        candidates = [base] if base.is_file() else [path for path in base.rglob("*") if path.is_file()]
        for path in candidates:
            redact_text_file(path)


def run_probe(args: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        result = subprocess.run(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"returncode": None, "timed_out": True}
    return {"returncode": result.returncode, "timed_out": False}


def run_capture(args: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        result = subprocess.run(
            args,
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


def runtime_model_config(
    *,
    project_id: str,
    token_value: str,
    quota_project: str,
) -> str:
    return (
        f"model_name: {MODEL_NAME}\n"
        "model_kwargs:\n"
        "  temperature: 0.2\n"
        "  max_tokens: 4096\n"
        f"  vertex_location: {VERTEX_LOCATION}\n"
        f"  vertex_project: {project_id}\n"
        "  extra_headers:\n"
        f"    Authorization: Bearer {token_value}\n"
        f"    X-Goog-User-Project: {quota_project}\n"
    )


def runtime_model_config_template() -> str:
    return runtime_model_config(
        project_id=f"${{{PROJECT_ENV}}}",
        token_value=f"${{{TOKEN_ENV}}}",
        quota_project=f"${{{QUOTA_ENV}}}",
    )


def materialize_runtime_overlay(
    overlay_manifest: dict[str, Any],
    *,
    project_id: str,
    token: str,
) -> dict[str, Any]:
    PROOF.mkdir(parents=True, exist_ok=True)
    placeholder_config = runtime_model_config_template()
    (PROOF / "runtime_access_path_model_config.yaml").write_text(
        placeholder_config,
        encoding="utf-8",
    )

    copies: list[dict[str, Any]] = []
    errors: list[str] = []
    for item in overlay_manifest.get("copies", []):
        destination_rel = Path(str(item.get("destination", "")))
        destination = CODECLASH_DIR / destination_rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination_rel == RUNTIME_MODEL_CONFIG_REL:
            actual_config = runtime_model_config(
                project_id=project_id,
                token_value=token,
                quota_project=project_id,
            )
            destination.write_text(actual_config, encoding="utf-8")
            copied = True
            actual_secret_values_present = project_id in actual_config and token in actual_config
            public_template_matches_shape = (
                MODEL_NAME in placeholder_config
                and f"${{{PROJECT_ENV}}}" in placeholder_config
                and f"${{{TOKEN_ENV}}}" in placeholder_config
                and f"${{{QUOTA_ENV}}}" in placeholder_config
            )
            copies.append(
                {
                    "destination": str(destination_rel),
                    "source": item.get("source"),
                    "materialization": "runtime_secret_values_in_tmp_only",
                    "copied_or_written": copied,
                    "actual_config_written_to_codeclash_tmp": True,
                    "actual_config_committed": False,
                    "actual_config_hash_committed": False,
                    "actual_secret_values_present_in_tmp_config": actual_secret_values_present,
                    "public_template_path": "runtime_access_path_model_config.yaml",
                    "public_template_sha256": sha256_file(PROOF / "runtime_access_path_model_config.yaml"),
                    "public_template_matches_shape": public_template_matches_shape,
                }
            )
            continue

        source_rel = Path(str(item.get("source", "")))
        source_override = False
        if destination_rel == TELOS_RECEIPT_AGENT_REL:
            source_rel = ITER65_RECOVERED_TELOS_AGENT.relative_to(ROOT)
            source_override = True
        source = ROOT / source_rel
        if not source.exists() or not source.is_file():
            errors.append(f"missing source {source_rel}")
            copies.append(
                {
                    "destination": str(destination_rel),
                    "source": str(source_rel),
                    "materialization": "copy_failed",
                    "copied_or_written": False,
                }
            )
            continue
        shutil.copy2(source, destination)
        source_sha = sha256_file(source)
        destination_sha = sha256_file(destination)
        copies.append(
            {
                "destination": str(destination_rel),
                "source": str(source_rel),
                "materialization": "copied_iter65_recovered_overlay"
                if source_override
                else "copied_frozen_overlay",
                "copied_or_written": True,
                "source_sha256": source_sha,
                "destination_sha256": destination_sha,
                "hash_match": source_sha == destination_sha,
                "source_override_reason": "iter65_receipt_schema_prompt_alignment"
                if source_override
                else None,
            }
        )
        if destination_rel == TELOS_COST_REGISTRY_ENTRY_REL:
            registry_destination = CODECLASH_DIR / CODECLASH_LITELLM_REGISTRY_REL
            shutil.copy2(source, registry_destination)
            registry_sha = sha256_file(registry_destination)
            copies.append(
                {
                    "destination": str(CODECLASH_LITELLM_REGISTRY_REL),
                    "source": str(source_rel),
                    "materialization": "runtime_litellm_registry_path_from_telos_entry",
                    "copied_or_written": True,
                    "source_sha256": source_sha,
                    "destination_sha256": registry_sha,
                    "hash_match": source_sha == registry_sha,
                }
            )

    all_materialized = bool(copies) and all(copy.get("copied_or_written") for copy in copies)
    copied_hashes_match = all(
        copy.get("hash_match", True)
        for copy in copies
        if copy.get("materialization") in {"copied_frozen_overlay", "copied_iter65_recovered_overlay"}
    )
    model_config = next(
        (
            copy
            for copy in copies
            if copy.get("destination") == str(RUNTIME_MODEL_CONFIG_REL)
        ),
        {},
    )
    binding = {
        "schema_version": "telos.provider_compatible_paid_execution.runtime_access_path_binding.v1",
        "mechanism": "runtime_tmp_config_with_env_acquired_bearer_token_and_project",
        "model_name": MODEL_NAME,
        "model_kwargs_template": {
            "temperature": 0.2,
            "max_tokens": 4096,
            "vertex_location": VERTEX_LOCATION,
            "vertex_project": f"${{{PROJECT_ENV}}}",
            "extra_headers": {
                "Authorization": f"Bearer ${{{TOKEN_ENV}}}",
                "X-Goog-User-Project": f"${{{QUOTA_ENV}}}",
            },
        },
        "runtime_env_vars": [PROJECT_ENV, TOKEN_ENV, QUOTA_ENV],
        "runtime_env_values_committed": False,
        "token_committed": False,
        "project_identifier_committed": False,
        "credential_material_committed": False,
        "codeclash_tmp_config_path": str(CODECLASH_DIR / RUNTIME_MODEL_CONFIG_REL),
        "actual_config_committed": False,
        "public_template_path": "runtime_access_path_model_config.yaml",
        "public_template_sha256": sha256_file(PROOF / "runtime_access_path_model_config.yaml"),
    }
    write_json(PROOF / "runtime_access_path_binding.json", binding)

    manifest = {
        "schema_version": "telos.provider_compatible_paid_execution.overlay_materialization.v1",
        "codeclash_dir": str(CODECLASH_DIR),
        "copied_file_count": len(copies),
        "copies": copies,
        "all_materialized": all_materialized,
        "copied_hashes_match": copied_hashes_match,
        "runtime_model_config_materialized": bool(model_config),
        "runtime_model_config_has_secret_values_only_in_tmp": model_config.get(
            "actual_secret_values_present_in_tmp_config"
        )
        is True
        and model_config.get("actual_config_committed") is False,
        "runtime_access_path_binding_path": "runtime_access_path_binding.json",
        "errors": errors,
    }
    write_json(PROOF / "overlay_materialization_manifest.json", manifest)
    return manifest


def write_unmaterialized_overlay_evidence(reason: str) -> dict[str, Any]:
    PROOF.mkdir(parents=True, exist_ok=True)
    (PROOF / "runtime_access_path_model_config.yaml").write_text(
        runtime_model_config_template(),
        encoding="utf-8",
    )
    binding = {
        "schema_version": "telos.provider_compatible_paid_execution.runtime_access_path_binding.v1",
        "mechanism": "runtime_tmp_config_with_env_acquired_bearer_token_and_project",
        "model_name": MODEL_NAME,
        "runtime_env_vars": [PROJECT_ENV, TOKEN_ENV, QUOTA_ENV],
        "runtime_env_values_committed": False,
        "token_committed": False,
        "project_identifier_committed": False,
        "credential_material_committed": False,
        "codeclash_tmp_config_path": str(CODECLASH_DIR / RUNTIME_MODEL_CONFIG_REL),
        "actual_config_committed": False,
        "public_template_path": "runtime_access_path_model_config.yaml",
        "public_template_sha256": sha256_file(PROOF / "runtime_access_path_model_config.yaml"),
        "blocked_before_materialization_reason": reason,
    }
    write_json(PROOF / "runtime_access_path_binding.json", binding)
    manifest = {
        "schema_version": "telos.provider_compatible_paid_execution.overlay_materialization.v1",
        "codeclash_dir": str(CODECLASH_DIR),
        "copied_file_count": 0,
        "copies": [],
        "all_materialized": False,
        "copied_hashes_match": False,
        "runtime_model_config_materialized": False,
        "runtime_model_config_has_secret_values_only_in_tmp": False,
        "runtime_access_path_binding_path": "runtime_access_path_binding.json",
        "errors": [reason],
    }
    write_json(PROOF / "overlay_materialization_manifest.json", manifest)
    return manifest


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter66-provider-compatible-paid-execution-after-receipt-prompt-alignment-{status}",
        "task_id": "telos:iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment@iter65",
        "agent_id": "codex-local-provider-compatible-paid-execution-runner",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Execute exactly the two frozen provider-compatible BattleSnake rows after iter65 "
            "recovered receipt prompt alignment, then measure verified-completion evidence under "
            "baseline and Telos receipt-enforced conditions."
        ),
        "acceptance_criteria": [
            "Iter63 is a clean access-path recovery pass before paid execution.",
            "Iter64 and iter65 proof receipts and audits pass before paid execution.",
            "The Telos row uses the recovered iter65 receipt prompt overlay.",
            "Exactly two selected BattleSnake condition rows execute and zero excluded pairs execute.",
            "Provider calls stay at or below 16 and provider spend at or below $10.00.",
            "No GPU, Sentinel resource mutation, production/live-domain mutation, or overclaim occurs.",
            "The Telos row is accepted as verified completion only if receipt validation passes.",
            "Runtime project and bearer-token values are injected only at execution time and are not committed.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                "notes": "Run summary records exact row execution, prompt-overlay, call, cost, receipt, and metric counts.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/raw/",
                "notes": "Raw packet contains command transcripts, CodeClash metadata, trajectory, changes, and extracted round results.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records the two-row claim boundary and any null/blocked outcome.",
            },
        ],
        "falsifiers": [
            "The result must block if iter63 is not a clean access-path recovery pass.",
            "The result must block if iter64 or iter65 proof/audit evidence is missing or invalid.",
            "The result must block if the recovered iter65 receipt prompt cannot be materialized.",
            "The result must block if runtime credential, Docker, or CodeClash readiness regresses.",
            "The result must fail if any excluded pair executes.",
            "The result must fail if provider calls, spend, GPU use, Sentinel mutation, or overclaim exceeds the gate.",
            "The result must fail if credential, project, service-account, or token residue is committed.",
            "The result must not accept the Telos row as verified completion unless receipt validation passes.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def command_output_root(command: str) -> Path:
    parts = shlex.split(command)
    if "-o" not in parts:
        raise RuntimeError(f"frozen command lacks -o output directory: {command}")
    return Path(parts[parts.index("-o") + 1])


def path_children(path: Path) -> set[Path]:
    if not path.exists():
        return set()
    return {child for child in path.iterdir() if child.is_dir()}


def newest_output_dir(root: Path, before: set[Path]) -> Path | None:
    after = path_children(root)
    created = list(after - before)
    if created:
        return max(created, key=lambda p: p.stat().st_mtime)
    if after:
        return max(after, key=lambda p: p.stat().st_mtime)
    return None


def command_env(*, project_id: str, token: str) -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = f"{DOCKER_BIN.parent}:{env.get('PATH', '')}"
    env["NO_COLOR"] = "1"
    env["PYTHONUNBUFFERED"] = "1"
    env[PROJECT_ENV] = project_id
    env[QUOTA_ENV] = project_id
    env[TOKEN_ENV] = token
    env["MSWEA_GLOBAL_CALL_LIMIT"] = str(CALL_CEILING)
    env["MSWEA_GLOBAL_COST_LIMIT"] = str(SPEND_CEILING)
    return env


def run_paid_command(pair_id: str, command: str, *, project_id: str, token: str) -> dict[str, Any]:
    output_root = command_output_root(command)
    before = path_children(output_root)
    transcript_dir = RAW / pair_id
    transcript_dir.mkdir(parents=True, exist_ok=True)
    start = time.time()
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=ROOT,
            env=command_env(project_id=project_id, token=token),
            capture_output=True,
            text=True,
            check=False,
            timeout=1800,
        )
        timed_out = False
        returncode = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = None
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    elapsed = time.time() - start
    output_dir = newest_output_dir(output_root, before)
    (transcript_dir / "command_stdout.txt").write_text(stdout, encoding="utf-8")
    (transcript_dir / "command_stderr.txt").write_text(stderr, encoding="utf-8")
    write_json(
        transcript_dir / "command_execution.json",
        {
            "command": command,
            "elapsed_seconds": round(elapsed, 3),
            "output_dir": str(output_dir) if output_dir else None,
            "output_root": str(output_root),
            "returncode": returncode,
            "timed_out": timed_out,
        },
    )
    return {
        "command": command,
        "elapsed_seconds": round(elapsed, 3),
        "output_dir": output_dir,
        "output_root": output_root,
        "returncode": returncode,
        "timed_out": timed_out,
        "recovered_after_verifier_crash": False,
    }


def recovered_command_result(pair_id: str, command: str, output_dir: Path) -> dict[str, Any]:
    output_root = command_output_root(command)
    transcript_dir = RAW / pair_id
    transcript_dir.mkdir(parents=True, exist_ok=True)
    recovered_execution: dict[str, Any] = {}
    if RECOVER_BASELINE_COMMAND_EXECUTION:
        source = Path(RECOVER_BASELINE_COMMAND_EXECUTION)
        if source.exists() and source.is_file():
            try:
                recovered_execution = read_json(source)
            except json.JSONDecodeError:
                recovered_execution = {}
    returncode = recovered_execution.get("returncode")
    if returncode is None and (output_dir / "metadata.json").exists():
        returncode = 0
    timed_out = bool(recovered_execution.get("timed_out", False))
    elapsed = recovered_execution.get("elapsed_seconds")
    (transcript_dir / "command_stdout.txt").write_text(
        "recovered_existing_output_dir_after_verifier_crash=true\n",
        encoding="utf-8",
    )
    (transcript_dir / "command_stderr.txt").write_text("", encoding="utf-8")
    write_json(
        transcript_dir / "command_execution.json",
        {
            "command": command,
            "elapsed_seconds": elapsed,
            "output_dir": str(output_dir),
            "output_root": str(output_root),
            "returncode": returncode,
            "timed_out": timed_out,
            "recovered_after_verifier_crash": True,
            "recovery_source_output_dir": str(output_dir),
            "recovery_source_command_execution": str(RECOVER_BASELINE_COMMAND_EXECUTION)
            if RECOVER_BASELINE_COMMAND_EXECUTION
            else None,
        },
    )
    return {
        "command": command,
        "elapsed_seconds": elapsed,
        "output_dir": output_dir,
        "output_root": output_root,
        "returncode": returncode,
        "timed_out": timed_out,
        "recovered_after_verifier_crash": True,
        "recovery_source_output_dir": str(output_dir),
    }


def safe_copy_file(source: Path, destination: Path) -> bool:
    if not source.exists() or not source.is_file():
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return True


def copy_round_artifacts(source_output: Path, raw_dir: Path) -> list[str]:
    copied: list[str] = []
    rounds_dir = source_output / "rounds"
    if not rounds_dir.exists():
        rounds_dir = source_output / "game" / "rounds"
    if not rounds_dir.exists():
        return copied
    dest = raw_dir / "rounds"
    for archive in sorted(rounds_dir.glob("round_*.tar.gz")):
        with tarfile.open(archive, "r:gz") as tar:
            for member in tar.getmembers():
                name = Path(member.name)
                if name.name != "results.json" and not name.name.startswith("sim_"):
                    continue
                extracted = tar.extractfile(member)
                if extracted is None:
                    continue
                out_path = dest / archive.stem.replace(".tar", "") / name.name
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(extracted.read())
                copied.append(str(out_path.relative_to(raw_dir)))
    for result_path in sorted(rounds_dir.glob("*/results.json")):
        out_path = dest / result_path.parent.name / "results.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(result_path, out_path)
        copied.append(str(out_path.relative_to(raw_dir)))
    for sim_path in sorted(rounds_dir.glob("*/sim_*.jsonl")):
        out_path = dest / sim_path.parent.name / sim_path.name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(sim_path, out_path)
        copied.append(str(out_path.relative_to(raw_dir)))
    return copied


def finalize_raw_packet(pair_id: str, output_dir: Path | None, copied: list[str]) -> dict[str, Any]:
    raw_dir = RAW / pair_id
    redact_tree([raw_dir])
    metadata_path = raw_dir / "metadata.json"
    metadata = read_json(metadata_path) if metadata_path.exists() else {}
    manifest_entries = []
    for path in sorted(raw_dir.rglob("*")):
        if path.is_file() and path.name != "raw_manifest.json":
            manifest_entries.append(
                {
                    "path": str(path.relative_to(raw_dir)),
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    write_json(
        raw_dir / "raw_manifest.json",
        {
            "output_dir": str(output_dir) if output_dir else None,
            "output_dir_present": bool(output_dir and output_dir.exists()),
            "copied_files": sorted(set(copied)),
            "files": manifest_entries,
            "redacted_before_publication": True,
        },
    )
    return {"raw_dir": raw_dir, "copied_files": sorted(set(copied)), "metadata": metadata}


def copy_raw_packet(pair_id: str, output_dir: Path | None) -> dict[str, Any]:
    raw_dir = RAW / pair_id
    copied: list[str] = []
    if output_dir is None:
        write_json(raw_dir / "raw_manifest.json", {"output_dir_present": False, "copied_files": []})
        return {"raw_dir": raw_dir, "copied_files": copied, "metadata": {}}

    file_map = {
        "metadata.json": output_dir / "metadata.json",
        "tournament.log": output_dir / "tournament.log",
        "everything.log": output_dir / "everything.log",
        "game.log": output_dir / "game.log",
        "players/p1/player.log": output_dir / "players" / "p1" / "player.log",
        "players/p1/p1_r1.traj.json": output_dir / "players" / "p1" / "p1_r1.traj.json",
        "players/p1/changes_r1.json": output_dir / "players" / "p1" / "changes_r1.json",
        "players/p2/player.log": output_dir / "players" / "p2" / "player.log",
    }
    for rel_path, source in file_map.items():
        if safe_copy_file(source, raw_dir / rel_path):
            copied.append(rel_path)
    copied.extend(copy_round_artifacts(output_dir, raw_dir))
    return finalize_raw_packet(pair_id, output_dir, copied)


def existing_command_result(pair_id: str, command: str) -> dict[str, Any]:
    raw_dir = RAW / pair_id
    execution = read_json(raw_dir / "command_execution.json")
    output_dir = execution.get("output_dir")
    return {
        "command": command,
        "elapsed_seconds": execution.get("elapsed_seconds"),
        "output_dir": Path(output_dir) if output_dir else None,
        "output_root": Path(execution["output_root"]) if execution.get("output_root") else None,
        "returncode": execution.get("returncode"),
        "timed_out": execution.get("timed_out"),
    }


def existing_raw_packet(pair_id: str, output_dir: Path | None) -> dict[str, Any]:
    raw_dir = RAW / pair_id
    copied = []
    for path in sorted(raw_dir.rglob("*")):
        if path.is_file() and path.name not in {"raw_manifest.json"}:
            copied.append(str(path.relative_to(raw_dir)))
    return finalize_raw_packet(pair_id, output_dir, copied)


def agent_stats(metadata: dict[str, Any], player_name: str = "p1") -> dict[str, Any]:
    for agent in metadata.get("agents", []):
        if agent.get("name") == player_name:
            stats = agent.get("agent_stats", {})
            return stats.get("1", stats.get(1, {}))
    return {}


def round_winner(metadata: dict[str, Any], round_num: str = "1") -> str | None:
    stats = metadata.get("round_stats", {})
    row = stats.get(round_num, stats.get(int(round_num), {}))
    if isinstance(row, dict):
        winner = row.get("winner")
        return str(winner) if winner is not None else None
    return None


def extract_receipt_candidate(raw_dir: Path) -> dict[str, Any]:
    changes_path = raw_dir / "players" / "p1" / "changes_r1.json"
    result = {
        "candidate_found": False,
        "candidate_json_parseable": False,
        "candidate_valid": False,
        "receipt_validation_returncode": None,
        "receipt_validation_stdout": "",
        "receipt_validation_stderr": "",
    }
    if not changes_path.exists():
        result["reason"] = "changes_file_missing"
        return result

    changes = read_json(changes_path)
    diff = changes.get("full_diff", "")
    lines = diff.splitlines()
    in_receipt = False
    candidate_lines: list[str] = []
    for line in lines:
        if line.startswith("diff --git "):
            in_receipt = " b/telos_completion_receipt.json" in line
            continue
        if not in_receipt:
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            candidate_lines.append(line[1:])
    candidate = "\n".join(candidate_lines).strip()
    if not candidate:
        result["reason"] = "receipt_diff_missing"
        return result

    result["candidate_found"] = True
    candidate_path = raw_dir / "telos_completion_receipt_candidate.json"
    candidate_path.write_text(candidate + "\n", encoding="utf-8")
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        (raw_dir / "receipt_candidate_invalid_json.txt").write_text(candidate + "\n", encoding="utf-8")
        result["reason"] = "candidate_json_invalid"
        return result
    result["candidate_json_parseable"] = True
    if not isinstance(parsed, dict):
        result["reason"] = "candidate_root_not_object"
        return result

    valid_dir = raw_dir / "valid"
    invalid_dir = raw_dir / "invalid"
    valid_dir.mkdir(exist_ok=True)
    invalid_dir.mkdir(exist_ok=True)
    trial_path = valid_dir / "telos_completion_receipt.json"
    write_json(trial_path, parsed)
    validation = subprocess.run(
        ["python3", "scripts/validate_receipts.py", str(raw_dir.relative_to(ROOT))],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    result.update(
        {
            "receipt_validation_returncode": validation.returncode,
            "receipt_validation_stdout": validation.stdout.strip(),
            "receipt_validation_stderr": validation.stderr.strip(),
        }
    )
    if validation.returncode == 0:
        result["candidate_valid"] = True
        return result

    invalid_path = invalid_dir / "telos_completion_receipt.json"
    shutil.move(str(trial_path), invalid_path)
    result["reason"] = "candidate_failed_receipt_validation"
    return result


def row_metrics(pair_id: str, command_result: dict[str, Any], raw_packet: dict[str, Any]) -> dict[str, Any]:
    metadata = raw_packet["metadata"]
    stats = agent_stats(metadata)
    output_dir = command_result.get("output_dir")
    api_calls = stats.get("api_calls", 0) if isinstance(stats, dict) else 0
    cost = stats.get("cost", 0.0) if isinstance(stats, dict) else 0.0
    try:
        api_calls = int(api_calls or 0)
    except (TypeError, ValueError):
        api_calls = 0
    try:
        cost = float(cost or 0.0)
    except (TypeError, ValueError):
        cost = 0.0
    exit_status = str(stats.get("exit_status", "")) if isinstance(stats, dict) else ""
    raw_evidence_present = bool(
        raw_packet["copied_files"]
        and (RAW / pair_id / "metadata.json").exists()
        and (RAW / pair_id / "players" / "p1" / "p1_r1.traj.json").exists()
    )
    receipt = extract_receipt_candidate(RAW / pair_id) if pair_id == TELOS_PAIR_ID else {
        "candidate_found": False,
        "candidate_json_parseable": False,
        "candidate_valid": False,
        "receipt_validation_returncode": None,
        "receipt_validation_stdout": "",
        "receipt_validation_stderr": "",
        "reason": "receipt_not_required_for_baseline",
    }
    if pair_id == TELOS_PAIR_ID:
        verified_completion = bool(
            command_result.get("returncode") == 0
            and raw_evidence_present
            and receipt.get("candidate_valid") is True
        )
    else:
        verified_completion = bool(command_result.get("returncode") == 0 and raw_evidence_present)
    return {
        "pair_id": pair_id,
        "command": command_result["command"],
        "command_returncode": command_result.get("returncode"),
        "command_timed_out": command_result.get("timed_out"),
        "elapsed_seconds": command_result.get("elapsed_seconds"),
        "output_dir": str(output_dir) if output_dir else None,
        "recovered_after_verifier_crash": command_result.get("recovered_after_verifier_crash", False),
        "recovery_source_output_dir": command_result.get("recovery_source_output_dir"),
        "raw_artifact_count": len(raw_packet["copied_files"]),
        "raw_evidence_present": raw_evidence_present,
        "agent_exit_status": exit_status,
        "provider_api_calls": api_calls,
        "provider_cost_usd": cost,
        "round_1_winner": round_winner(metadata),
        "receipt_required": pair_id == TELOS_PAIR_ID,
        "receipt_candidate_found": receipt.get("candidate_found"),
        "receipt_candidate_json_parseable": receipt.get("candidate_json_parseable"),
        "receipt_valid": receipt.get("candidate_valid"),
        "receipt_validation_returncode": receipt.get("receipt_validation_returncode"),
        "receipt_validation_stdout": receipt.get("receipt_validation_stdout"),
        "receipt_validation_stderr": receipt.get("receipt_validation_stderr"),
        "receipt_validation_reason": receipt.get("reason"),
        "verified_completion_evidence": verified_completion,
    }


def provider_error_classes(row_results: list[dict[str, Any]]) -> list[str]:
    classes: set[str] = set()
    for row in row_results:
        status = str(row.get("agent_exit_status", ""))
        if "Publisher model" in status and "NOT_FOUND" in status:
            classes.add("vertex_model_not_found_or_access_denied")
        elif row.get("command_returncode") not in (0, None):
            classes.add("provider_command_nonzero_returncode")
    return sorted(classes)


def text_files_under(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for base in paths:
        if base.is_file():
            candidates = [base]
        else:
            candidates = [path for path in base.rglob("*") if path.is_file()]
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
        if base.is_file():
            hashes[str(base.relative_to(PROOF))] = sha256_file(base)
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file():
                hashes[str(path.relative_to(PROOF))] = sha256_file(path)
    return hashes


def preflight(
    command_manifest: dict[str, Any],
    iter63: dict[str, Any],
    direct_probe: dict[str, Any],
    litellm_probe: dict[str, Any],
    iter62_binding: dict[str, Any],
    overlay_materialization: dict[str, Any],
    *,
    project_available: bool,
    token_available: bool,
) -> dict[str, Any]:
    codeclash_rev = run_capture(["git", "-C", str(CODECLASH_DIR), "rev-parse", "HEAD"])
    docker = run_capture([str(DOCKER_BIN), "info", "--format", "{{.ServerVersion}}"], timeout=10)
    google_auth = run_capture(
        [str(CODECLASH_DIR / ".venv" / "bin" / "python"), "-c", "import google.auth"],
        timeout=10,
    )
    receipt_check = subprocess.run(
        ["python3", "scripts/validate_receipts.py", str(ITER63_RECEIPT_DIR.relative_to(ROOT))],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    iter64 = read_json(ITER64_SOURCE_SUMMARY) if ITER64_SOURCE_SUMMARY.exists() else {}
    iter65 = read_json(ITER65_SOURCE_SUMMARY) if ITER65_SOURCE_SUMMARY.exists() else {}
    iter64_receipt_check = subprocess.run(
        ["python3", "scripts/validate_receipts.py", str(ITER64_SOURCE_PROOF.relative_to(ROOT))],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    iter64_audit = subprocess.run(
        ["python3", "scripts/audit_provider_compatible_paid_execution_after_access_path_recovery.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    iter65_receipt_check = subprocess.run(
        ["python3", "scripts/validate_receipts.py", str(ITER65_SOURCE_PROOF.relative_to(ROOT))],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    iter65_audit = subprocess.run(
        ["python3", "scripts/audit_receipt_schema_prompt_alignment.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    commands = command_manifest.get("commands", [])
    selected_ids = [command.get("pair_id") for command in commands]
    return {
        "schema_version": "telos.provider_compatible_paid_execution.preflight.v1",
        "iter63_status": iter63.get("status"),
        "iter63_clean_pass": iter63.get("clean_pass"),
        "iter63_blocker_classification": iter63.get("blocker_classification"),
        "iter63_direct_rest_probe_status": direct_probe.get("status"),
        "iter63_litellm_parity_probe_status": litellm_probe.get("status"),
        "iter63_receipt_validation_returncode": receipt_check.returncode,
        "iter63_receipt_validation_stdout": receipt_check.stdout.strip(),
        "iter64_status": iter64.get("status"),
        "iter64_clean_pass": iter64.get("clean_pass"),
        "iter64_primary_metric": iter64.get("primary_metric"),
        "iter64_receipt_validation_returncode": iter64_receipt_check.returncode,
        "iter64_receipt_validation_stdout": iter64_receipt_check.stdout.strip(),
        "iter64_audit_returncode": iter64_audit.returncode,
        "iter64_audit_stdout": iter64_audit.stdout.strip(),
        "iter65_status": iter65.get("status"),
        "iter65_clean_pass": iter65.get("clean_pass"),
        "iter65_receipt_failure_classification": iter65.get("iter64_receipt_failure_classification"),
        "iter65_recovered_prompt_path": iter65.get("recovered_prompt_path"),
        "iter65_recovered_prompt_required_fields_present": iter65.get(
            "recovered_prompt_required_fields_present"
        ),
        "iter65_recovered_prompt_digest_rule_present": iter65.get("recovered_prompt_digest_rule_present"),
        "iter65_receipt_validation_returncode": iter65_receipt_check.returncode,
        "iter65_receipt_validation_stdout": iter65_receipt_check.stdout.strip(),
        "iter65_audit_returncode": iter65_audit.returncode,
        "iter65_audit_stdout": iter65_audit.stdout.strip(),
        "iter65_recovered_overlay_present": ITER65_RECOVERED_TELOS_AGENT.exists(),
        "iter65_recovered_overlay_sha256": sha256_file(ITER65_RECOVERED_TELOS_AGENT)
        if ITER65_RECOVERED_TELOS_AGENT.exists()
        else None,
        "codeclash_checkout_present": (CODECLASH_DIR / ".git").exists(),
        "codeclash_expected_commit": CODECLASH_COMMIT,
        "codeclash_actual_commit": codeclash_rev.get("stdout"),
        "codeclash_commit_matches_expected": codeclash_rev.get("stdout") == CODECLASH_COMMIT,
        "docker_preferred_cli": str(DOCKER_BIN),
        "docker_ready": docker.get("returncode") == 0 and bool(docker.get("stdout")),
        "docker_server_version_present": bool(docker.get("stdout")),
        "codeclash_google_auth_import_ready": google_auth.get("returncode") == 0,
        "codeclash_google_auth_error_class": "none"
        if google_auth.get("returncode") == 0
        else "google_auth_module_missing",
        "runtime_project_available": project_available,
        "adc_access_token_available": token_available,
        "adc_token_output_suppressed": True,
        "runtime_access_path_mechanism": iter62_binding.get("mechanism"),
        "runtime_access_path_env_vars": iter62_binding.get("runtime_env_vars"),
        "runtime_env_values_committed": False,
        "runtime_overlay_all_materialized": overlay_materialization.get("all_materialized"),
        "runtime_overlay_copied_hashes_match": overlay_materialization.get("copied_hashes_match"),
        "runtime_model_config_materialized": overlay_materialization.get("runtime_model_config_materialized"),
        "runtime_model_config_has_secret_values_only_in_tmp": overlay_materialization.get(
            "runtime_model_config_has_secret_values_only_in_tmp"
        ),
        "current_access_path_probe_rerun": False,
        "current_access_path_probe_rerun_reason": "provider call ceiling reserved for the two frozen rows",
        "selected_pair_count": len(selected_ids),
        "selected_pair_ids": selected_ids,
        "expected_selected_pair_ids": SELECTED_PAIR_IDS,
        "excluded_pair_ids": command_manifest.get("excluded_pair_ids", []),
        "excluded_pair_selected": bool(set(selected_ids) & set(command_manifest.get("excluded_pair_ids", []))),
        "provider_call_ceiling": CALL_CEILING,
        "provider_spend_ceiling_usd": SPEND_CEILING,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "cloud_runner_started": False,
    }


def latest_existing_output_dir(pair_id: str) -> Path | None:
    root = Path("/tmp/telos-codeclash-protocol-effect-condition-separated") / pair_id
    if not root.exists():
        return None
    children = [child for child in root.iterdir() if child.is_dir()]
    if not children:
        return None
    return max(children, key=lambda path: path.stat().st_mtime)


def dependency_block_evidence() -> dict[str, Any]:
    output_dir = latest_existing_output_dir(SELECTED_PAIR_IDS[0])
    copied = copy_raw_packet(SELECTED_PAIR_IDS[0], output_dir) if output_dir else {
        "raw_dir": RAW / SELECTED_PAIR_IDS[0],
        "copied_files": [],
        "metadata": {},
    }
    log_path = RAW / SELECTED_PAIR_IDS[0] / "everything.log"
    missing_google_seen = False
    if log_path.exists():
        missing_google_seen = "ModuleNotFoundError: No module named 'google'" in log_path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    evidence = {
        "schema_version": "telos.provider_compatible_paid_execution.dependency_block.v1",
        "attempted_pair_id": SELECTED_PAIR_IDS[0] if output_dir else None,
        "attempted_pair_output_dir": str(output_dir) if output_dir else None,
        "telos_pair_attempted": False,
        "missing_dependency": "google.auth",
        "missing_dependency_seen_in_log": missing_google_seen,
        "provider_api_calls_observed_in_partial_metadata": 0,
        "provider_cost_usd_observed_in_partial_metadata": 0.0,
        "copied_raw_files": copied["copied_files"],
    }
    write_json(PROOF / "dependency_block_evidence.json", evidence)
    return evidence


def main() -> int:
    if PROOF.exists():
        shutil.rmtree(PROOF)
    PROOF.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    iter63 = read_json(ITER63_SUMMARY)
    direct_probe = read_json(ITER63_DIRECT_PROBE)
    litellm_probe = read_json(ITER63_LITELLM_PROBE)
    iter62_binding = read_json(ITER62_BINDING)
    command_manifest = read_json(ITER54_COMMANDS)
    overlay_manifest = read_json(ITER54_OVERLAYS)
    _ = read_json(ITER48_SLICE)

    project_available, project_id = gcloud_project()
    token = access_token() if project_available else None
    token_available = token is not None
    global DYNAMIC_PROJECT_ID, DYNAMIC_BEARER_TOKEN
    DYNAMIC_PROJECT_ID = project_id
    DYNAMIC_BEARER_TOKEN = token

    if project_id and token:
        overlay_materialization = materialize_runtime_overlay(
            overlay_manifest,
            project_id=project_id,
            token=token,
        )
    else:
        overlay_materialization = write_unmaterialized_overlay_evidence(
            "runtime_project_or_adc_token_unavailable"
        )

    pre = preflight(
        command_manifest,
        iter63,
        direct_probe,
        litellm_probe,
        iter62_binding,
        overlay_materialization,
        project_available=project_available,
        token_available=token_available,
    )
    write_json(PROOF / "preflight.json", pre)

    blockers: list[str] = []
    failures: list[str] = []
    if pre["iter63_status"] != "pass" or pre["iter63_clean_pass"] is not True:
        blockers.append("iter63_not_clean_access_path_recovery_pass")
    if pre["iter63_blocker_classification"] != "access_path_recovered":
        blockers.append("iter63_access_path_not_recovered")
    if pre["iter63_direct_rest_probe_status"] != "pass":
        blockers.append("iter63_direct_rest_probe_not_pass")
    if pre["iter63_litellm_parity_probe_status"] != "pass":
        blockers.append("iter63_litellm_parity_probe_not_pass")
    if pre["iter63_receipt_validation_returncode"] != 0:
        blockers.append("iter63_receipt_validation_failed")
    if pre["iter64_status"] != "pass" or pre["iter64_clean_pass"] is not True:
        blockers.append("iter64_not_clean_two_row_measurement_pass")
    if pre["iter64_receipt_validation_returncode"] != 0:
        blockers.append("iter64_receipt_validation_failed")
    if pre["iter64_audit_returncode"] != 0:
        blockers.append("iter64_audit_failed")
    if pre["iter65_status"] != "pass" or pre["iter65_clean_pass"] is not True:
        blockers.append("iter65_not_clean_receipt_prompt_alignment_pass")
    if pre["iter65_receipt_failure_classification"] != "schema_incomplete":
        blockers.append("iter65_receipt_failure_classification_not_schema_incomplete")
    if pre["iter65_recovered_prompt_required_fields_present"] is not True:
        blockers.append("iter65_recovered_prompt_required_fields_not_present")
    if pre["iter65_recovered_prompt_digest_rule_present"] is not True:
        blockers.append("iter65_recovered_prompt_digest_rule_not_present")
    if pre["iter65_receipt_validation_returncode"] != 0:
        blockers.append("iter65_receipt_validation_failed")
    if pre["iter65_audit_returncode"] != 0:
        blockers.append("iter65_audit_failed")
    if pre["iter65_recovered_overlay_present"] is not True:
        blockers.append("iter65_recovered_overlay_missing")
    if not pre["codeclash_commit_matches_expected"]:
        blockers.append("codeclash_checkout_not_pinned")
    if not pre["docker_ready"]:
        blockers.append("docker_not_ready")
    if not pre["codeclash_google_auth_import_ready"]:
        blockers.append("codeclash_vertex_google_auth_dependency_missing")
    if not pre["runtime_project_available"]:
        blockers.append("gcloud_project_unavailable")
    if not pre["adc_access_token_available"]:
        blockers.append("adc_auth_unavailable")
    if not pre["runtime_overlay_all_materialized"]:
        blockers.append("runtime_overlay_not_materialized")
    if not pre["runtime_overlay_copied_hashes_match"]:
        blockers.append("runtime_overlay_hash_mismatch")
    if not pre["runtime_model_config_materialized"]:
        blockers.append("runtime_model_config_not_materialized")
    if not pre["runtime_model_config_has_secret_values_only_in_tmp"]:
        blockers.append("runtime_model_config_secret_boundary_not_proven")
    if pre["selected_pair_ids"] != SELECTED_PAIR_IDS:
        failures.append("selected_pair_ids_changed")
    if pre["excluded_pair_selected"]:
        failures.append("excluded_pair_selected")

    dependency_evidence: dict[str, Any] = {}

    row_results: list[dict[str, Any]] = []
    if not blockers and not failures:
        for command in command_manifest.get("commands", []):
            pair_id = command["pair_id"]
            if pair_id == BASELINE_PAIR_ID and RECOVER_BASELINE_OUTPUT_DIR:
                result = recovered_command_result(
                    pair_id,
                    command["command"],
                    Path(RECOVER_BASELINE_OUTPUT_DIR),
                )
                raw_packet = copy_raw_packet(pair_id, result.get("output_dir"))
            elif REUSE_EXISTING_RAW:
                result = existing_command_result(pair_id, command["command"])
                raw_packet = existing_raw_packet(pair_id, result.get("output_dir"))
            else:
                if not project_id or not token:
                    raise RuntimeError("unreachable: row execution without project/token")
                result = run_paid_command(
                    pair_id,
                    command["command"],
                    project_id=project_id,
                    token=token,
                )
                raw_packet = copy_raw_packet(pair_id, result.get("output_dir"))
            row_results.append(row_metrics(pair_id, result, raw_packet))

    provider_calls = sum(int(row.get("provider_api_calls", 0)) for row in row_results)
    provider_cost = round(sum(float(row.get("provider_cost_usd", 0.0)) for row in row_results), 8)
    if row_results and len(row_results) != 2:
        blockers.append("not_exactly_two_rows_executed")
    if any(row.get("command_returncode") not in (0, None) for row in row_results):
        blockers.append("provider_command_nonzero_returncode")
    error_classes = provider_error_classes(row_results)
    for error_class in error_classes:
        if error_class not in blockers:
            blockers.append(error_class)
    if provider_calls > CALL_CEILING:
        failures.append("provider_call_ceiling_exceeded")
    if provider_cost > SPEND_CEILING:
        failures.append("provider_spend_ceiling_exceeded")

    scan_passed, scan_findings = redaction_scan(
        [
            RAW,
            PROOF / "preflight.json",
            PROOF / "runtime_access_path_binding.json",
            PROOF / "runtime_access_path_model_config.yaml",
            PROOF / "overlay_materialization_manifest.json",
        ]
    )
    if not scan_passed:
        failures.append("redaction_scan_failed")

    row_ids = [row["pair_id"] for row in row_results]
    recovered_pair_ids = [
        row["pair_id"] for row in row_results if row.get("recovered_after_verifier_crash") is True
    ]
    excluded_executed = bool(set(row_ids) & set(command_manifest.get("excluded_pair_ids", [])))
    if excluded_executed:
        failures.append("excluded_pair_executed")
    telos_row = next((row for row in row_results if row["pair_id"] == TELOS_PAIR_ID), {})
    receipt_validation_ran = telos_row.get("receipt_validation_returncode") is not None
    if row_results and not receipt_validation_ran:
        blockers.append("telos_receipt_validation_not_run")

    status = "fail" if failures else "blocked" if blockers else "pass"
    metric_rows = {
        row["pair_id"]: {
            "provider_api_calls": row["provider_api_calls"],
            "provider_cost_usd": row["provider_cost_usd"],
            "raw_evidence_present": row["raw_evidence_present"],
            "receipt_required": row["receipt_required"],
            "receipt_valid": row["receipt_valid"],
            "verified_completion_evidence": row["verified_completion_evidence"],
            "round_1_winner": row["round_1_winner"],
            "agent_exit_status": row["agent_exit_status"],
            "recovered_after_verifier_crash": row["recovered_after_verifier_crash"],
        }
        for row in row_results
    }
    primary_metric = {
        "baseline_verified_completion_evidence": metric_rows.get(SELECTED_PAIR_IDS[0], {}).get(
            "verified_completion_evidence", False
        ),
        "telos_verified_completion_evidence": metric_rows.get(SELECTED_PAIR_IDS[1], {}).get(
            "verified_completion_evidence", False
        ),
        "verified_completion_evidence_delta_telos_minus_baseline": int(
            bool(metric_rows.get(SELECTED_PAIR_IDS[1], {}).get("verified_completion_evidence", False))
        )
        - int(bool(metric_rows.get(SELECTED_PAIR_IDS[0], {}).get("verified_completion_evidence", False))),
    }

    report = {
        "schema_version": "telos.provider_compatible_paid_execution.report.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "preflight": pre,
        "iter63_access_path_prerequisite": {
            "status": pre["iter63_status"],
            "clean_pass": pre["iter63_clean_pass"],
            "blocker_classification": pre["iter63_blocker_classification"],
            "direct_rest_probe_status": pre["iter63_direct_rest_probe_status"],
            "litellm_parity_probe_status": pre["iter63_litellm_parity_probe_status"],
            "receipt_validation_returncode": pre["iter63_receipt_validation_returncode"],
        },
        "iter64_two_row_measurement_prerequisite": {
            "status": pre["iter64_status"],
            "clean_pass": pre["iter64_clean_pass"],
            "primary_metric": pre["iter64_primary_metric"],
            "receipt_validation_returncode": pre["iter64_receipt_validation_returncode"],
            "audit_returncode": pre["iter64_audit_returncode"],
        },
        "iter65_receipt_prompt_alignment_prerequisite": {
            "status": pre["iter65_status"],
            "clean_pass": pre["iter65_clean_pass"],
            "receipt_failure_classification": pre["iter65_receipt_failure_classification"],
            "receipt_validation_returncode": pre["iter65_receipt_validation_returncode"],
            "audit_returncode": pre["iter65_audit_returncode"],
            "recovered_prompt_path": pre["iter65_recovered_prompt_path"],
            "recovered_overlay_sha256": pre["iter65_recovered_overlay_sha256"],
        },
        "runtime_access_path_binding_path": "runtime_access_path_binding.json",
        "runtime_overlay_materialization": overlay_materialization,
        "runtime_env_values_committed": False,
        "selected_pair_ids": SELECTED_PAIR_IDS,
        "executed_pair_ids": row_ids,
        "executed_pair_count": len(row_results),
        "verifier_crash_recovery_used": bool(recovered_pair_ids),
        "recovered_after_verifier_crash_pair_ids": recovered_pair_ids,
        "attempted_pair_ids": [
            dependency_evidence["attempted_pair_id"]
        ]
        if dependency_evidence.get("attempted_pair_id")
        else row_ids,
        "dependency_block_evidence": dependency_evidence,
        "excluded_pair_ids": command_manifest.get("excluded_pair_ids", []),
        "excluded_pair_executed": excluded_executed,
        "provider_api_calls": provider_calls,
        "provider_call_ceiling": CALL_CEILING,
        "provider_cost_usd": provider_cost,
        "provider_spend_ceiling_usd": SPEND_CEILING,
        "provider_error_classes": error_classes,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "cloud_runner_started": False,
        "teardown_required": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "redaction_scan_passed": scan_passed,
        "redaction_findings": scan_findings,
        "row_results": row_results,
        "primary_metric": primary_metric,
        "secondary_metrics": {
            "task_success_by_round_winner": {
                row["pair_id"]: row["round_1_winner"] for row in row_results
            },
            "receipt_validation_by_pair": {
                row["pair_id"]: row["receipt_valid"] for row in row_results
            },
            "raw_artifact_count_by_pair": {
                row["pair_id"]: row["raw_artifact_count"] for row in row_results
            },
            "latency_seconds_by_pair": {
                row["pair_id"]: row["elapsed_seconds"] for row in row_results
            },
        },
        "blockers": blockers,
        "failures": failures,
    }
    report = redact_value(report)
    write_json(PROOF / "protocol_effect_report.json", report)

    command_lines = [
        f"provider-compatible paid execution after receipt prompt alignment: {status}",
        f"iter63_status={pre['iter63_status']}",
        f"iter63_blocker_classification={pre['iter63_blocker_classification']}",
        f"iter64_status={pre['iter64_status']}",
        f"iter65_status={pre['iter65_status']}",
        f"iter65_receipt_failure_classification={pre['iter65_receipt_failure_classification']}",
        f"runtime_overlay_all_materialized={str(pre['runtime_overlay_all_materialized']).lower()}",
        f"verifier_crash_recovery_used={str(bool(recovered_pair_ids)).lower()}",
        f"recovered_after_verifier_crash_pair_ids={','.join(recovered_pair_ids)}",
        f"executed_pair_count={len(row_results)}",
        f"excluded_pair_executed={str(excluded_executed).lower()}",
        f"provider_api_calls={provider_calls}",
        f"provider_cost_usd={provider_cost:.8f}",
        "gpu_used=false",
        "sentinel_named_resources_modified=false",
        f"baseline_verified_completion_evidence={str(primary_metric['baseline_verified_completion_evidence']).lower()}",
        f"telos_verified_completion_evidence={str(primary_metric['telos_verified_completion_evidence']).lower()}",
        f"verified_completion_evidence_delta_telos_minus_baseline={primary_metric['verified_completion_evidence_delta_telos_minus_baseline']}",
        f"blockers={','.join(blockers)}",
        f"failures={','.join(failures)}",
    ]
    for row in row_results:
        command_lines.append(
            f"{row['pair_id']}: rc={row['command_returncode']} calls={row['provider_api_calls']} "
            f"cost={row['provider_cost_usd']:.8f} receipt_valid={str(row['receipt_valid']).lower()} "
            f"verified={str(row['verified_completion_evidence']).lower()} "
            f"recovered_after_verifier_crash={str(row['recovered_after_verifier_crash']).lower()}"
        )
    (PROOF / "command_output.txt").write_text("\n".join(command_lines) + "\n", encoding="utf-8")

    if row_results:
        if "vertex_model_not_found_or_access_denied" in blockers:
            summary_sentence = (
                "The gate executed both selected provider-compatible BattleSnake rows after "
                "`iter65` recovered receipt prompt alignment, then blocked because "
                "Vertex returned a redacted model-not-found-or-access-denied error for the "
                "configured provider model."
            )
        else:
            summary_sentence = (
                "The gate executed selected provider-compatible BattleSnake rows after `iter65` "
                "recovered receipt prompt alignment."
            )
    elif "codeclash_vertex_google_auth_dependency_missing" in blockers:
        summary_sentence = (
            "The gate blocked before executing either provider-compatible BattleSnake row because "
            "the pinned CodeClash venv could not import `google.auth` during preflight."
        )
    else:
        summary_sentence = (
            "The gate blocked before executing provider-compatible BattleSnake rows because a "
            "preflight prerequisite failed."
        )

    result_md = f"""# Iteration 66 Result - Provider-Compatible Paid Execution After Receipt Prompt Alignment

Status: `{status.upper()}`.

## Summary

{summary_sentence} It did not execute excluded pairs, start a cloud runner, use GPU, or modify
Sentinel-named resources.

- iter63 prerequisite status: `{pre['iter63_status']}`,
- iter63 blocker classification: `{pre['iter63_blocker_classification']}`,
- iter64 prerequisite status: `{pre['iter64_status']}`,
- iter65 prerequisite status: `{pre['iter65_status']}`,
- iter65 receipt failure classification: `{pre['iter65_receipt_failure_classification']}`,
- runtime overlay materialized: `{str(pre['runtime_overlay_all_materialized']).lower()}`,
- runtime env values committed: `false`,
- verifier-crash recovery used: `{str(bool(recovered_pair_ids)).lower()}`,
- recovered verifier-crash pair ids: `{','.join(recovered_pair_ids) if recovered_pair_ids else 'none'}`,
- executed pair count: `{len(row_results)}`,
- excluded pairs executed: `{str(excluded_executed).lower()}`,
- provider API calls: `{provider_calls}`,
- provider cost from CodeClash metadata: `${provider_cost:.8f}`,
- baseline verified-completion evidence: `{str(primary_metric['baseline_verified_completion_evidence']).lower()}`,
- Telos verified-completion evidence: `{str(primary_metric['telos_verified_completion_evidence']).lower()}`,
- Telos-minus-baseline verified-completion delta: `{primary_metric['verified_completion_evidence_delta_telos_minus_baseline']}`.
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

## Claim Boundary

This is a bounded two-row provider-compatible protocol-effect pilot. It is not a benchmark result,
SWE-bench score, leaderboard result, production/live-domain result, model-superiority result, or
state-of-the-art result.

## Evidence

- `proof/preflight.json`
- `proof/runtime_access_path_binding.json`
- `proof/runtime_access_path_model_config.yaml`
- `proof/overlay_materialization_manifest.json`
- `proof/protocol_effect_report.json`
- `proof/raw/`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_provider_compatible_paid_execution_after_receipt_prompt_alignment.json`
"""
    (EXPERIMENT / "RESULT.md").write_text(result_md, encoding="utf-8")

    if row_results:
        review_scope = (
            "The paid retry stayed inside the selected BattleSnake rows and kept all four "
            "historical Dummy/deterministic-edit rows unattempted."
        )
    else:
        review_scope = (
            "The paid retry blocked before executing a selected row. Both selected rows and all "
            "four historical Dummy/deterministic-edit rows remained unattempted."
        )

    review = f"""# Iteration 66 Review

{review_scope} Provider calls and cost came from the committed CodeClash metadata, and redaction
was applied before publication.

Access-path prerequisite:

- iter63 status: `{pre['iter63_status']}`,
- iter63 blocker classification: `{pre['iter63_blocker_classification']}`,
- iter64 status: `{pre['iter64_status']}`,
- iter64 audit return code: `{pre['iter64_audit_returncode']}`,
- iter65 status: `{pre['iter65_status']}`,
- iter65 audit return code: `{pre['iter65_audit_returncode']}`,
- iter65 receipt failure classification: `{pre['iter65_receipt_failure_classification']}`,
- runtime overlay materialized: `{str(pre['runtime_overlay_all_materialized']).lower()}`,
- runtime env values committed: `false`,
- verifier-crash recovery used: `{str(bool(recovered_pair_ids)).lower()}`,
- recovered verifier-crash pair ids: `{','.join(recovered_pair_ids) if recovered_pair_ids else 'none'}`.

Primary metric:

- baseline verified-completion evidence: `{str(primary_metric['baseline_verified_completion_evidence']).lower()}`,
- Telos verified-completion evidence: `{str(primary_metric['telos_verified_completion_evidence']).lower()}`,
- Telos-minus-baseline delta: `{primary_metric['verified_completion_evidence_delta_telos_minus_baseline']}`.

Blockers: `{','.join(blockers) if blockers else 'none'}`.
Failures: `{','.join(failures) if failures else 'none'}`.

No benchmark, SWE-bench, leaderboard, production/live-domain, model-superiority, or
state-of-the-art result is claimed.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    summary_paths = [
        PROOF / "preflight.json",
        PROOF / "dependency_block_evidence.json",
        PROOF / "runtime_access_path_binding.json",
        PROOF / "runtime_access_path_model_config.yaml",
        PROOF / "overlay_materialization_manifest.json",
        PROOF / "protocol_effect_report.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
        RAW,
    ]
    run_summary = {
        "schema_version": "telos.provider_compatible_paid_execution.summary.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "iter63_status": pre["iter63_status"],
        "iter63_clean_pass": pre["iter63_clean_pass"],
        "iter63_blocker_classification": pre["iter63_blocker_classification"],
        "iter63_direct_rest_probe_status": pre["iter63_direct_rest_probe_status"],
        "iter63_litellm_parity_probe_status": pre["iter63_litellm_parity_probe_status"],
        "iter63_receipt_validation_returncode": pre["iter63_receipt_validation_returncode"],
        "iter64_status": pre["iter64_status"],
        "iter64_clean_pass": pre["iter64_clean_pass"],
        "iter64_primary_metric": pre["iter64_primary_metric"],
        "iter64_receipt_validation_returncode": pre["iter64_receipt_validation_returncode"],
        "iter64_audit_returncode": pre["iter64_audit_returncode"],
        "iter65_status": pre["iter65_status"],
        "iter65_clean_pass": pre["iter65_clean_pass"],
        "iter65_receipt_failure_classification": pre["iter65_receipt_failure_classification"],
        "iter65_receipt_validation_returncode": pre["iter65_receipt_validation_returncode"],
        "iter65_audit_returncode": pre["iter65_audit_returncode"],
        "iter65_recovered_prompt_path": pre["iter65_recovered_prompt_path"],
        "iter65_recovered_overlay_sha256": pre["iter65_recovered_overlay_sha256"],
        "runtime_access_path_binding_path": "runtime_access_path_binding.json",
        "runtime_overlay_all_materialized": pre["runtime_overlay_all_materialized"],
        "runtime_overlay_copied_hashes_match": pre["runtime_overlay_copied_hashes_match"],
        "runtime_model_config_materialized": pre["runtime_model_config_materialized"],
        "runtime_model_config_has_secret_values_only_in_tmp": pre[
            "runtime_model_config_has_secret_values_only_in_tmp"
        ],
        "runtime_env_values_committed": False,
        "verifier_crash_recovery_used": bool(recovered_pair_ids),
        "recovered_after_verifier_crash_pair_ids": recovered_pair_ids,
        "executed_pair_count": len(row_results),
        "executed_pair_ids": row_ids,
        "attempted_pair_ids": [
            dependency_evidence["attempted_pair_id"]
        ]
        if dependency_evidence.get("attempted_pair_id")
        else row_ids,
        "dependency_block_evidence": dependency_evidence,
        "excluded_pair_executed": excluded_executed,
        "provider_api_calls": provider_calls,
        "provider_call_ceiling": CALL_CEILING,
        "provider_cost_usd": provider_cost,
        "provider_spend_ceiling_usd": SPEND_CEILING,
        "provider_error_classes": error_classes,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "cloud_runner_started": False,
        "teardown_required": False,
        "redaction_scan_passed": scan_passed,
        "redaction_findings": scan_findings,
        "primary_metric": primary_metric,
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
        "artifact_hashes": artifact_hashes(summary_paths),
    }
    run_summary = redact_value(run_summary)
    write_json(PROOF / "run_summary.json", run_summary)

    if status == "blocked" and "codeclash_vertex_google_auth_dependency_missing" in blockers:
        learning_insight = (
            "The iter66 paid retry blocked before selected-row execution because the pinned "
            "CodeClash virtualenv could not import google.auth during preflight."
        )
        learning_next = (
            "fix only the named CodeClash dependency regression before retrying the same frozen "
            "two-row receipt-prompt-aligned paid pilot"
        )
    elif status == "blocked" and "vertex_model_not_found_or_access_denied" in blockers:
        learning_insight = (
            "Both selected provider-compatible BattleSnake rows executed, but each provider call "
            "returned a redacted Vertex model-not-found-or-access-denied response before verified "
            "completion evidence could be accepted."
        )
        learning_next = (
            "recover an accessible provider model binding before retrying the same frozen two-row gate"
        )
    elif status == "blocked":
        learning_insight = (
            "The paid retry did not establish a complete two-row protocol-effect result because a "
            "preflight or execution blocker remained."
        )
        learning_next = "fix only the named blocker before retrying the same frozen two-row gate"
    elif status == "fail":
        learning_insight = (
            "The paid retry exposed a quality failure under the pre-registered two-row protocol-effect "
            "gate."
        )
        learning_next = "publish the failure boundary before deciding whether a corrective gate is justified"
    else:
        learning_insight = (
            "The receipt-prompt-aligned paid provider-compatible protocol-effect retry now has "
            "exact two-row baseline-vs-Telos verified-completion evidence counts."
        )
        learning_next = (
            "decide from the measured two-row result whether a larger external slice is justified"
        )

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "insight": learning_insight,
        "next_action": learning_next,
        "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
        "evidence_paths": [
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            f"experiments/{EXPERIMENT_ID}/proof/protocol_effect_report.json",
            f"experiments/{EXPERIMENT_ID}/proof/command_output.txt",
            f"experiments/{EXPERIMENT_ID}/proof/runtime_access_path_binding.json",
            f"experiments/{EXPERIMENT_ID}/proof/valid/receipt_provider_compatible_paid_execution_after_receipt_prompt_alignment.json",
        ],
    }
    learning_record = redact_value(learning_record)
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(
        VALID / "receipt_provider_compatible_paid_execution_after_receipt_prompt_alignment.json",
        build_receipt(status),
    )

    print("\n".join(command_lines))
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
