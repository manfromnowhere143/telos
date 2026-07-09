#!/usr/bin/env python3
"""Run iter72 bounded provider-compatible adapter-row execution."""

from __future__ import annotations

import hashlib
import importlib.util
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
EXPERIMENT_ID = "iter72_provider_compatible_expanded_paid_execution_after_slice_refreeze"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
RAW = PROOF / "raw"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
ITER71_PROOF = (
    ROOT / "experiments" / "iter71_provider_compatible_expanded_slice_after_adapter_completion" / "proof"
)
ITER71_SUMMARY = ITER71_PROOF / "run_summary.json"
ITER71_DECISION = ITER71_PROOF / "expanded_slice_decision.json"
ITER71_CANDIDATES = ITER71_PROOF / "candidate_rows.json"
ITER66_SUMMARY = (
    ROOT
    / "experiments"
    / "iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment"
    / "proof"
    / "run_summary.json"
)
HELPER_PATH = ROOT / "scripts" / "verify_provider_compatible_paid_execution_after_receipt_prompt_alignment.py"
CODECLASH_DIR = Path("/tmp/telos-codeclash")
CODECLASH_COMMIT = "381cdfa05a35e8acd35853b9fc7e13005121b127"
RUNTIME_MODEL_CONFIG_REL = Path("configs/mini/telos_vertex_gemini_3_1_pro_customtools.yaml")
CODECLASH_LITELLM_REGISTRY_REL = Path("configs/mini/litellm_custom_model_config.yaml")
TOTAL_CALL_CEILING = 32
TOTAL_SPEND_CEILING_USD = 10.0
PER_ROW_CALL_LIMIT = 8
PER_ROW_SPEND_LIMIT_USD = 2.5
SELECTED_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
    "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
]
RETAINED_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
]
TEXT_SUFFIXES = {".json", ".jsonl", ".log", ".txt", ".md", ".yaml", ".yml", ".py"}
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"Bearer\s+(?!\$\{TELOS_VERTEX_BEARER_TOKEN\}|\[REDACTED_BEARER_TOKEN\])\S+"),
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"),
    re.compile(r"telos-vertex-runner"),
    re.compile(r"sunlit-unison-[A-Za-z0-9-]+"),
    re.compile(r"errorId=Ci"),
    re.compile(r'"error_info_id"\s*:\s*"Ci'),
]


def load_helper() -> Any:
    spec = importlib.util.spec_from_file_location("iter66_paid_helper", HELPER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load helper: {HELPER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


helper = load_helper()


def configure_helper() -> None:
    helper.EXPERIMENT_ID = EXPERIMENT_ID
    helper.EXPERIMENT = EXPERIMENT
    helper.PROOF = PROOF
    helper.RAW = RAW
    helper.VALID = VALID
    helper.CALL_CEILING = PER_ROW_CALL_LIMIT
    helper.SPEND_CEILING = PER_ROW_SPEND_LIMIT_USD


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


def run_capture(args: list[str], timeout: int = 30) -> dict[str, Any]:
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


def candidate_rows() -> list[dict[str, Any]]:
    packet = read_json(ITER71_CANDIDATES)
    rows = packet.get("candidate_rows", [])
    if not isinstance(rows, list):
        raise RuntimeError("iter71 candidate_rows must be a list")
    return [row for row in rows if row.get("pair_id") in SELECTED_PAIR_IDS]


def overlay_destination(source_path: str) -> Path:
    marker = "proof/recovered_overlay/"
    if marker in source_path:
        return Path(source_path.split(marker, maxsplit=1)[1])
    return Path(source_path).relative_to(Path(source_path).parents[3])


def materialize_runtime_overlay(rows: list[dict[str, Any]], *, project_id: str, token: str) -> dict[str, Any]:
    PROOF.mkdir(parents=True, exist_ok=True)
    placeholder_config = helper.runtime_model_config(
        project_id="${TELOS_VERTEX_PROJECT}",
        token_value="${TELOS_VERTEX_BEARER_TOKEN}",
        quota_project="${TELOS_VERTEX_QUOTA_PROJECT}",
    )
    (PROOF / "runtime_access_path_model_config.yaml").write_text(
        placeholder_config,
        encoding="utf-8",
    )

    source_to_destination: dict[str, Path] = {}
    for row in rows:
        adapter = row.get("adapter_evidence", {})
        for key in ["provider_overlay_config", "provider_agent_config", "provider_cost_registry"]:
            source = str(adapter.get(key, ""))
            if source:
                source_to_destination[source] = overlay_destination(source)
        source_to_destination[str(adapter.get("provider_model_config"))] = RUNTIME_MODEL_CONFIG_REL

    copies: list[dict[str, Any]] = []
    errors: list[str] = []
    for source_text, destination_rel in sorted(source_to_destination.items()):
        if not source_text or source_text == "None":
            continue
        destination = CODECLASH_DIR / destination_rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination_rel == RUNTIME_MODEL_CONFIG_REL:
            actual_config = helper.runtime_model_config(
                project_id=project_id,
                token_value=token,
                quota_project=project_id,
            )
            destination.write_text(actual_config, encoding="utf-8")
            copies.append(
                {
                    "destination": str(destination_rel),
                    "source": source_text,
                    "materialization": "runtime_secret_values_in_tmp_only",
                    "copied_or_written": True,
                    "actual_config_written_to_codeclash_tmp": True,
                    "actual_config_committed": False,
                    "actual_secret_values_present_in_tmp_config": (
                        project_id in actual_config and token in actual_config
                    ),
                    "public_template_path": "runtime_access_path_model_config.yaml",
                    "public_template_sha256": sha256_file(PROOF / "runtime_access_path_model_config.yaml"),
                }
            )
            continue

        source = ROOT / source_text
        if not source.exists():
            errors.append(f"missing source {source_text}")
            copies.append(
                {
                    "destination": str(destination_rel),
                    "source": source_text,
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
                "source": source_text,
                "materialization": "copied_iter71_adapter_overlay",
                "copied_or_written": True,
                "source_sha256": source_sha,
                "destination_sha256": destination_sha,
                "hash_match": source_sha == destination_sha,
            }
        )
        if destination_rel.name == "telos_litellm_cost_registry_entry.json":
            registry_destination = CODECLASH_DIR / CODECLASH_LITELLM_REGISTRY_REL
            shutil.copy2(source, registry_destination)
            registry_sha = sha256_file(registry_destination)
            copies.append(
                {
                    "destination": str(CODECLASH_LITELLM_REGISTRY_REL),
                    "source": source_text,
                    "materialization": "runtime_litellm_registry_path_from_telos_entry",
                    "copied_or_written": True,
                    "source_sha256": source_sha,
                    "destination_sha256": registry_sha,
                    "hash_match": source_sha == registry_sha,
                }
            )

    all_materialized = bool(copies) and all(copy.get("copied_or_written") for copy in copies)
    copied_hashes_match = all(copy.get("hash_match", True) for copy in copies)
    runtime_copy = next(
        (copy for copy in copies if copy.get("destination") == str(RUNTIME_MODEL_CONFIG_REL)),
        {},
    )
    binding = {
        "schema_version": "telos.provider_compatible_expanded_paid_execution.runtime_access_path_binding.v1",
        "mechanism": "runtime_tmp_config_with_env_acquired_bearer_token_and_project",
        "model_name": helper.MODEL_NAME,
        "runtime_env_vars": [helper.PROJECT_ENV, helper.TOKEN_ENV, helper.QUOTA_ENV],
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
        "schema_version": "telos.provider_compatible_expanded_paid_execution.overlay_materialization.v1",
        "codeclash_dir": str(CODECLASH_DIR),
        "copied_file_count": len(copies),
        "copies": copies,
        "all_materialized": all_materialized,
        "copied_hashes_match": copied_hashes_match,
        "runtime_model_config_materialized": bool(runtime_copy),
        "runtime_model_config_has_secret_values_only_in_tmp": (
            runtime_copy.get("actual_secret_values_present_in_tmp_config") is True
            and runtime_copy.get("actual_config_committed") is False
        ),
        "runtime_access_path_binding_path": "runtime_access_path_binding.json",
        "errors": errors,
    }
    write_json(PROOF / "overlay_materialization_manifest.json", manifest)
    return manifest


def write_unmaterialized_overlay(reason: str) -> dict[str, Any]:
    PROOF.mkdir(parents=True, exist_ok=True)
    (PROOF / "runtime_access_path_model_config.yaml").write_text(
        helper.runtime_model_config(
            project_id="${TELOS_VERTEX_PROJECT}",
            token_value="${TELOS_VERTEX_BEARER_TOKEN}",
            quota_project="${TELOS_VERTEX_QUOTA_PROJECT}",
        ),
        encoding="utf-8",
    )
    write_json(
        PROOF / "runtime_access_path_binding.json",
        {
            "schema_version": "telos.provider_compatible_expanded_paid_execution.runtime_access_path_binding.v1",
            "mechanism": "runtime_tmp_config_with_env_acquired_bearer_token_and_project",
            "runtime_env_values_committed": False,
            "blocked_before_materialization_reason": reason,
        },
    )
    manifest = {
        "schema_version": "telos.provider_compatible_expanded_paid_execution.overlay_materialization.v1",
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


def receipt_required(row: dict[str, Any]) -> bool:
    return row.get("condition_id") == "telos_receipt_enforced_completion_evidence"


def agent_stats(metadata: dict[str, Any], player_name: str = "p1") -> dict[str, Any]:
    return helper.agent_stats(metadata, player_name)


def row_metrics(
    row: dict[str, Any], command_result: dict[str, Any], raw_packet: dict[str, Any]
) -> dict[str, Any]:
    pair_id = str(row["pair_id"])
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
    raw_dir = RAW / pair_id
    raw_evidence_present = bool(
        raw_packet["copied_files"]
        and (raw_dir / "metadata.json").exists()
        and (raw_dir / "raw_manifest.json").exists()
    )
    if receipt_required(row):
        receipt = helper.extract_receipt_candidate(raw_dir)
    else:
        receipt = {
            "candidate_found": False,
            "candidate_json_parseable": False,
            "candidate_valid": False,
            "receipt_validation_returncode": None,
            "receipt_validation_stdout": "",
            "receipt_validation_stderr": "",
            "reason": "receipt_not_required_for_baseline",
        }
    verified_completion = bool(
        command_result.get("returncode") == 0
        and raw_evidence_present
        and (receipt.get("candidate_valid") is True if receipt_required(row) else True)
    )
    return {
        "pair_id": pair_id,
        "public_config": row.get("public_config"),
        "analysis_stratum": row.get("analysis_stratum"),
        "condition_id": row.get("condition_id"),
        "command": command_result["command"],
        "command_returncode": command_result.get("returncode"),
        "command_timed_out": command_result.get("timed_out"),
        "elapsed_seconds": command_result.get("elapsed_seconds"),
        "output_dir": str(output_dir) if output_dir else None,
        "raw_artifact_count": len(raw_packet["copied_files"]),
        "raw_evidence_present": raw_evidence_present,
        "agent_exit_status": exit_status,
        "provider_api_calls": api_calls,
        "provider_cost_usd": cost,
        "round_1_winner": helper.round_winner(metadata),
        "receipt_required": receipt_required(row),
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
    classes = set(helper.provider_error_classes(row_results))
    for row in row_results:
        if row.get("command_timed_out"):
            classes.add("provider_command_timed_out")
    return sorted(classes)


def text_files(path: Path) -> list[Path]:
    return [
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file() and candidate.suffix in TEXT_SUFFIXES
    ]


def redaction_scan() -> tuple[bool, list[str]]:
    findings: list[str] = []
    for path in text_files(EXPERIMENT):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(str(path.relative_to(ROOT)))
                break
    return not findings, sorted(set(findings))


def artifact_hashes(paths: list[Path]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for base in paths:
        if not base.exists():
            continue
        if base.is_file():
            hashes[str(base.relative_to(PROOF))] = sha256_file(base)
        else:
            for path in sorted(base.rglob("*")):
                if path.is_file():
                    hashes[str(path.relative_to(PROOF))] = sha256_file(path)
    return hashes


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter72-provider-compatible-expanded-paid-execution-{status}",
        "task_id": "telos:iter72_provider_compatible_expanded_paid_execution_after_slice_refreeze@iter71",
        "agent_id": "codex-local-expanded-adapter-row-paid-runner",
        "benchmark_id": "telos_codeclash_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Execute only the four iter71-selected adapter-planned rows under the frozen "
            "provider-compatible expanded-slice boundary."
        ),
        "acceptance_criteria": [
            "Iter71 passed and selected exactly four adapter-planned rows.",
            "Only those four rows execute; the two BattleSnake rows are retained as prior evidence.",
            "Provider calls stay at or below 32 and provider spend at or below $10.00.",
            "Every receipt-enforced row has a valid Telos receipt before verified completion is accepted.",
            "Raw artifacts, metadata, costs, receipts, redaction scans, and teardown evidence are committed.",
            "No GPU, cloud runner, Sentinel mutation, live-domain mutation, or benchmark/model claim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                "notes": "Run summary records exact row execution, provider calls, costs, receipts, and claim boundary.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/raw/",
                "notes": "Raw packet contains command transcripts and copied CodeClash artifacts.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records the stratified no-benchmark/no-model boundary.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if iter71 proof or selected-row hashes are invalid.",
            "The result must fail if any unselected row executes.",
            "The result must fail if provider calls or spend exceed the frozen ceiling.",
            "The result must block if receipt-required rows lack valid receipts.",
            "The result must fail if credential, token, project, or service-account residue is committed.",
            "The result must fail if unsupported benchmark, model-superiority, production, live-domain, leaderboard, SWE-bench, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def write_result(
    status: str,
    *,
    row_results: list[dict[str, Any]],
    provider_calls: int,
    provider_cost: float,
    blockers: list[str],
    failures: list[str],
    primary_metric: dict[str, Any],
) -> None:
    if row_results:
        summary_sentence = (
            "The gate executed the four iter71-selected adapter-planned rows under the stratified "
            "provider-compatible boundary."
        )
    else:
        summary_sentence = "The gate blocked before adapter-row execution because preflight failed."
    content = f"""# Iteration 72 Result - Provider-Compatible Expanded Paid Execution After Slice Refreeze

Status: `{status.upper()}`.

## Summary

{summary_sentence}

- executed adapter row count: `{len(row_results)}`,
- retained BattleSnake rows rerun: `false`,
- provider API calls: `{provider_calls}`,
- provider call ceiling: `{TOTAL_CALL_CEILING}`,
- provider cost from CodeClash metadata: `${provider_cost:.8f}`,
- provider spend ceiling: `${TOTAL_SPEND_CEILING_USD:.2f}`,
- GPU used: `false`,
- cloud runner started: `false`,
- Sentinel-named resources modified: `false`,
- benchmark/model/SOTA claim: `false`,
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

## Stratified Metrics

- Dummy baseline verified-completion evidence:
  `{str(primary_metric['dummy_baseline_verified_completion_evidence']).lower()}`,
- Dummy Telos verified-completion evidence:
  `{str(primary_metric['dummy_telos_verified_completion_evidence']).lower()}`,
- deterministic-edit baseline verified-completion evidence:
  `{str(primary_metric['deterministic_edit_baseline_verified_completion_evidence']).lower()}`,
- deterministic-edit Telos verified-completion evidence:
  `{str(primary_metric['deterministic_edit_telos_verified_completion_evidence']).lower()}`.

## Claim Boundary

This is a bounded four-row adapter-validation extension under a stratified Telos protocol-effect
boundary. It is not a benchmark result, SWE-bench score, leaderboard result,
production/live-domain result, model-superiority result, or state-of-the-art result.

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
- `proof/valid/receipt_provider_compatible_expanded_paid_execution_after_slice_refreeze.json`
"""
    RESULT.write_text(content, encoding="utf-8")


def main() -> int:
    configure_helper()
    if PROOF.exists():
        shutil.rmtree(PROOF)
    PROOF.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    iter71_summary = read_json(ITER71_SUMMARY)
    iter71_decision = read_json(ITER71_DECISION)
    iter66_summary = read_json(ITER66_SUMMARY)
    rows = candidate_rows()
    selected_ids = [row["pair_id"] for row in rows]
    project_available, project_id = helper.gcloud_project()
    token = helper.access_token() if project_available else None
    token_available = token is not None
    helper.DYNAMIC_PROJECT_ID = project_id
    helper.DYNAMIC_BEARER_TOKEN = token

    if project_id and token:
        overlay = materialize_runtime_overlay(rows, project_id=project_id, token=token)
    else:
        overlay = write_unmaterialized_overlay("runtime_project_or_adc_token_unavailable")

    codeclash_rev = run_capture(["git", "-C", str(CODECLASH_DIR), "rev-parse", "HEAD"])
    docker = run_capture(
        [str(helper.DOCKER_BIN), "info", "--format", "{{.ServerVersion}}"],
        timeout=10,
    )
    google_auth = run_capture(
        [str(CODECLASH_DIR / ".venv" / "bin" / "python"), "-c", "import google.auth"],
        timeout=10,
    )
    iter71_receipt = run_capture(
        ["python3", "scripts/validate_receipts.py", str(ITER71_PROOF.relative_to(ROOT))]
    )
    iter71_audit = run_capture(
        ["python3", "scripts/audit_provider_compatible_expanded_slice_after_adapter_completion.py"]
    )
    preflight = {
        "schema_version": "telos.provider_compatible_expanded_paid_execution.preflight.v1",
        "iter71_status": iter71_summary.get("status"),
        "iter71_clean_pass": iter71_summary.get("clean_pass"),
        "iter71_selected_pair_ids": iter71_summary.get("selected_pair_ids"),
        "iter71_next_paid_gate_plan": iter71_summary.get("next_paid_gate_plan"),
        "iter71_receipt_validation_returncode": iter71_receipt["returncode"],
        "iter71_audit_returncode": iter71_audit["returncode"],
        "iter66_status": iter66_summary.get("status"),
        "iter66_primary_metric": iter66_summary.get("primary_metric"),
        "codeclash_expected_commit": CODECLASH_COMMIT,
        "codeclash_actual_commit": codeclash_rev.get("stdout"),
        "codeclash_commit_matches_expected": codeclash_rev.get("stdout") == CODECLASH_COMMIT,
        "docker_ready": docker.get("returncode") == 0 and bool(docker.get("stdout")),
        "docker_server_version_present": bool(docker.get("stdout")),
        "codeclash_google_auth_import_ready": google_auth.get("returncode") == 0,
        "runtime_project_available": project_available,
        "adc_access_token_available": token_available,
        "adc_token_output_suppressed": True,
        "runtime_env_values_committed": False,
        "runtime_overlay_all_materialized": overlay.get("all_materialized"),
        "runtime_overlay_copied_hashes_match": overlay.get("copied_hashes_match"),
        "runtime_model_config_materialized": overlay.get("runtime_model_config_materialized"),
        "runtime_model_config_has_secret_values_only_in_tmp": overlay.get(
            "runtime_model_config_has_secret_values_only_in_tmp"
        ),
        "selected_pair_ids": selected_ids,
        "expected_selected_pair_ids": SELECTED_PAIR_IDS,
        "retained_existing_pair_ids": RETAINED_PAIR_IDS,
        "provider_call_ceiling": TOTAL_CALL_CEILING,
        "provider_spend_ceiling_usd": TOTAL_SPEND_CEILING_USD,
        "per_row_call_limit": PER_ROW_CALL_LIMIT,
        "per_row_spend_limit_usd": PER_ROW_SPEND_LIMIT_USD,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
    }
    write_json(PROOF / "preflight.json", preflight)

    blockers: list[str] = []
    failures: list[str] = []
    if preflight["iter71_status"] != "pass" or preflight["iter71_clean_pass"] is not True:
        blockers.append("iter71_not_clean_pass")
    if preflight["iter71_receipt_validation_returncode"] != 0:
        blockers.append("iter71_receipt_validation_failed")
    if preflight["iter71_audit_returncode"] != 0:
        blockers.append("iter71_audit_failed")
    if selected_ids != SELECTED_PAIR_IDS:
        failures.append("selected_pair_ids_changed")
    if preflight["codeclash_commit_matches_expected"] is not True:
        blockers.append("codeclash_checkout_not_pinned")
    if preflight["docker_ready"] is not True:
        blockers.append("docker_not_ready")
    if preflight["codeclash_google_auth_import_ready"] is not True:
        blockers.append("codeclash_google_auth_import_failed")
    if preflight["runtime_project_available"] is not True:
        blockers.append("gcloud_project_unavailable")
    if preflight["adc_access_token_available"] is not True:
        blockers.append("adc_auth_unavailable")
    if preflight["runtime_overlay_all_materialized"] is not True:
        blockers.append("runtime_overlay_not_materialized")
    if preflight["runtime_overlay_copied_hashes_match"] is not True:
        blockers.append("runtime_overlay_hash_mismatch")
    if preflight["runtime_model_config_has_secret_values_only_in_tmp"] is not True:
        blockers.append("runtime_model_config_secret_boundary_not_proven")

    row_results: list[dict[str, Any]] = []
    if not blockers and not failures:
        for row in rows:
            pair_id = row["pair_id"]
            command = row["future_execution_command"]
            result = helper.run_paid_command(pair_id, command, project_id=project_id, token=token)
            raw_packet = helper.copy_raw_packet(pair_id, result.get("output_dir"))
            row_result = row_metrics(row, result, raw_packet)
            row_results.append(row_result)
            calls_so_far = sum(int(item.get("provider_api_calls", 0)) for item in row_results)
            cost_so_far = sum(float(item.get("provider_cost_usd", 0.0)) for item in row_results)
            if calls_so_far > TOTAL_CALL_CEILING or cost_so_far > TOTAL_SPEND_CEILING_USD:
                failures.append("provider_ceiling_exceeded_during_execution")
                break

    provider_calls = sum(int(row.get("provider_api_calls", 0)) for row in row_results)
    provider_cost = round(sum(float(row.get("provider_cost_usd", 0.0)) for row in row_results), 8)
    if row_results and len(row_results) != 4:
        blockers.append("not_exactly_four_rows_executed")
    if provider_calls > TOTAL_CALL_CEILING:
        failures.append("provider_call_ceiling_exceeded")
    if provider_cost > TOTAL_SPEND_CEILING_USD:
        failures.append("provider_spend_ceiling_exceeded")
    if any(row.get("command_returncode") not in (0, None) for row in row_results):
        blockers.append("provider_command_nonzero_returncode")
    for error_class in provider_error_classes(row_results):
        if error_class not in blockers:
            blockers.append(error_class)
    for row in row_results:
        if row.get("receipt_required") is True and row.get("receipt_valid") is not True:
            blockers.append(f"{row['pair_id']}_receipt_not_valid")

    scan_passed, scan_findings = redaction_scan()
    if not scan_passed:
        failures.append("redaction_scan_failed")

    rows_by_pair = {row["pair_id"]: row for row in row_results}
    primary_metric = {
        "dummy_baseline_verified_completion_evidence": rows_by_pair.get(
            "baseline-agent-completion-evidence__configs-test-dummy-yaml", {}
        ).get("verified_completion_evidence", False),
        "dummy_telos_verified_completion_evidence": rows_by_pair.get(
            "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml", {}
        ).get("verified_completion_evidence", False),
        "deterministic_edit_baseline_verified_completion_evidence": rows_by_pair.get(
            "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml", {}
        ).get("verified_completion_evidence", False),
        "deterministic_edit_telos_verified_completion_evidence": rows_by_pair.get(
            "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml", {}
        ).get("verified_completion_evidence", False),
    }
    primary_metric["dummy_delta_telos_minus_baseline"] = int(
        bool(primary_metric["dummy_telos_verified_completion_evidence"])
    ) - int(bool(primary_metric["dummy_baseline_verified_completion_evidence"]))
    primary_metric["deterministic_edit_delta_telos_minus_baseline"] = int(
        bool(primary_metric["deterministic_edit_telos_verified_completion_evidence"])
    ) - int(bool(primary_metric["deterministic_edit_baseline_verified_completion_evidence"]))

    blockers = sorted(set(blockers))
    failures = sorted(set(failures))
    status = "fail" if failures else "blocked" if blockers else "pass"

    report = {
        "schema_version": "telos.provider_compatible_expanded_paid_execution.report.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "preflight": preflight,
        "iter71_decision": iter71_decision,
        "selected_pair_ids": SELECTED_PAIR_IDS,
        "retained_existing_pair_ids": RETAINED_PAIR_IDS,
        "executed_pair_ids": [row["pair_id"] for row in row_results],
        "executed_pair_count": len(row_results),
        "row_results": row_results,
        "provider_api_calls": provider_calls,
        "provider_call_ceiling": TOTAL_CALL_CEILING,
        "provider_cost_usd": provider_cost,
        "provider_spend_ceiling_usd": TOTAL_SPEND_CEILING_USD,
        "per_row_call_limit": PER_ROW_CALL_LIMIT,
        "per_row_spend_limit_usd": PER_ROW_SPEND_LIMIT_USD,
        "primary_metric": primary_metric,
        "analysis_boundary": iter71_summary.get("analysis_boundary"),
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_or_model_claim_authorized": False,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "redaction_scan_passed": scan_passed,
        "redaction_findings": scan_findings,
        "blockers": blockers,
        "failures": failures,
    }
    report = helper.redact_value(report)
    write_json(PROOF / "protocol_effect_report.json", report)

    command_lines = [
        f"provider-compatible expanded paid execution after slice refreeze: {status}",
        f"selected_pair_count={len(SELECTED_PAIR_IDS)}",
        f"executed_pair_count={len(row_results)}",
        "retained_battlesnake_rows_rerun=false",
        f"provider_api_calls={provider_calls}",
        f"provider_call_ceiling={TOTAL_CALL_CEILING}",
        f"provider_cost_usd={provider_cost:.8f}",
        f"provider_spend_ceiling_usd={TOTAL_SPEND_CEILING_USD:.2f}",
        "gpu_used=false",
        "cloud_runner_started=false",
        "sentinel_named_resources_modified=false",
        f"dummy_baseline_verified_completion_evidence={str(primary_metric['dummy_baseline_verified_completion_evidence']).lower()}",
        f"dummy_telos_verified_completion_evidence={str(primary_metric['dummy_telos_verified_completion_evidence']).lower()}",
        f"deterministic_edit_baseline_verified_completion_evidence={str(primary_metric['deterministic_edit_baseline_verified_completion_evidence']).lower()}",
        f"deterministic_edit_telos_verified_completion_evidence={str(primary_metric['deterministic_edit_telos_verified_completion_evidence']).lower()}",
        f"blockers={','.join(blockers)}",
        f"failures={','.join(failures)}",
    ]
    for row in row_results:
        command_lines.append(
            f"{row['pair_id']}: rc={row['command_returncode']} calls={row['provider_api_calls']} "
            f"cost={row['provider_cost_usd']:.8f} receipt_required={str(row['receipt_required']).lower()} "
            f"receipt_valid={str(row['receipt_valid']).lower()} verified={str(row['verified_completion_evidence']).lower()}"
        )
    (PROOF / "command_output.txt").write_text("\n".join(command_lines) + "\n", encoding="utf-8")

    review = f"""# Iteration 72 Review

The gate attempted only the four adapter-planned rows selected by iter71. The two BattleSnake rows
were retained as prior iter66 evidence and were not rerun. The result remains stratified by task
surface; Dummy and deterministic-edit evidence may not be pooled into a benchmark/model claim.

Provider calls and costs were read from committed CodeClash metadata after redaction. Receipt
validation was required before accepting verified completion for the two Telos receipt-enforced
rows.

- status: `{status}`,
- executed row count: `{len(row_results)}`,
- provider API calls: `{provider_calls}`,
- provider cost: `${provider_cost:.8f}`,
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

No benchmark, SWE-bench, leaderboard, production/live-domain, model-superiority, or
state-of-the-art result is claimed.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    summary_paths = [
        PROOF / "preflight.json",
        PROOF / "runtime_access_path_binding.json",
        PROOF / "runtime_access_path_model_config.yaml",
        PROOF / "overlay_materialization_manifest.json",
        PROOF / "protocol_effect_report.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
        RAW,
    ]
    run_summary = {
        "schema_version": "telos.provider_compatible_expanded_paid_execution.summary.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "iter71_status": preflight["iter71_status"],
        "iter71_clean_pass": preflight["iter71_clean_pass"],
        "iter71_receipt_validation_returncode": preflight["iter71_receipt_validation_returncode"],
        "iter71_audit_returncode": preflight["iter71_audit_returncode"],
        "selected_pair_ids": SELECTED_PAIR_IDS,
        "retained_existing_pair_ids": RETAINED_PAIR_IDS,
        "executed_pair_count": len(row_results),
        "executed_pair_ids": [row["pair_id"] for row in row_results],
        "provider_api_calls": provider_calls,
        "provider_call_ceiling": TOTAL_CALL_CEILING,
        "provider_cost_usd": provider_cost,
        "provider_spend_ceiling_usd": TOTAL_SPEND_CEILING_USD,
        "per_row_call_limit": PER_ROW_CALL_LIMIT,
        "per_row_spend_limit_usd": PER_ROW_SPEND_LIMIT_USD,
        "runtime_overlay_all_materialized": preflight["runtime_overlay_all_materialized"],
        "runtime_overlay_copied_hashes_match": preflight["runtime_overlay_copied_hashes_match"],
        "runtime_model_config_materialized": preflight["runtime_model_config_materialized"],
        "runtime_model_config_has_secret_values_only_in_tmp": preflight[
            "runtime_model_config_has_secret_values_only_in_tmp"
        ],
        "runtime_env_values_committed": False,
        "primary_metric": primary_metric,
        "analysis_boundary": iter71_summary.get("analysis_boundary"),
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_or_model_claim_authorized": False,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "redaction_scan_passed": scan_passed,
        "redaction_findings": scan_findings,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": blockers,
        "failures": failures,
        "artifact_hashes": artifact_hashes(summary_paths),
    }
    run_summary = helper.redact_value(run_summary)
    write_json(PROOF / "run_summary.json", run_summary)

    if status == "pass":
        learning_next = "analyze the stratified four-row result before any broader benchmark claim"
        learning_insight = (
            "The four adapter-planned rows executed under the iter72 ceiling with stratified "
            "verified-completion evidence."
        )
    elif status == "blocked":
        learning_next = "fix only the named iter72 blocker before retrying the same four-row gate"
        learning_insight = "The iter72 paid adapter-row gate produced blocked/null evidence."
    else:
        learning_next = "publish the quality-failure boundary before deciding on corrective work"
        learning_insight = "The iter72 paid adapter-row gate hit a quality failure."
    write_json(
        PROOF / "learning_record.json",
        {
            "schema_version": "telos.learning_record.v1",
            "experiment_id": EXPERIMENT_ID,
            "status": status if status != "fail" else "null",
            "insight": learning_insight,
            "next_action": learning_next,
            "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
            "evidence_paths": [
                f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                f"experiments/{EXPERIMENT_ID}/proof/protocol_effect_report.json",
                f"experiments/{EXPERIMENT_ID}/proof/command_output.txt",
                f"experiments/{EXPERIMENT_ID}/proof/review.md",
                f"experiments/{EXPERIMENT_ID}/proof/valid/receipt_provider_compatible_expanded_paid_execution_after_slice_refreeze.json",
            ],
        },
    )
    write_json(
        VALID / "receipt_provider_compatible_expanded_paid_execution_after_slice_refreeze.json",
        build_receipt(status),
    )
    write_result(
        status,
        row_results=row_results,
        provider_calls=provider_calls,
        provider_cost=provider_cost,
        blockers=blockers,
        failures=failures,
        primary_metric=primary_metric,
    )

    print("\n".join(command_lines))
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
