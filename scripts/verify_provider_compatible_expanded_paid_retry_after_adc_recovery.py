#!/usr/bin/env python3
"""Run iter78 bounded paid retry with iter73 recovered receipt prompts."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest


ROOT = Path(__file__).resolve().parents[1]
ITER72_SCRIPT = ROOT / "scripts" / "verify_provider_compatible_expanded_paid_execution_after_slice_refreeze.py"
EXPERIMENT_ID = "iter78_provider_compatible_expanded_paid_retry_after_adc_recovery"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
RAW = PROOF / "raw"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
ITER72_PROOF = (
    ROOT
    / "experiments"
    / "iter72_provider_compatible_expanded_paid_execution_after_slice_refreeze"
    / "proof"
)
ITER72_SUMMARY = ITER72_PROOF / "run_summary.json"
ITER73_PROOF = ROOT / "experiments" / "iter73_expanded_receipt_prompt_recovery_after_paid_block" / "proof"
ITER73_SUMMARY = ITER73_PROOF / "run_summary.json"
ITER74_PROOF = (
    ROOT
    / "experiments"
    / "iter74_provider_compatible_expanded_paid_retry_after_receipt_prompt_recovery"
    / "proof"
)
ITER74_SUMMARY = ITER74_PROOF / "run_summary.json"
ITER77_PROOF = (
    ROOT
    / "experiments"
    / "iter77_runtime_adc_recheck_after_application_default_login"
    / "proof"
)
ITER77_SUMMARY = ITER77_PROOF / "run_summary.json"
RECEIPT_NAME = "receipt_provider_compatible_expanded_paid_retry_after_adc_recovery.json"
OLD_RECEIPT_NAME = "receipt_provider_compatible_expanded_paid_execution_after_slice_refreeze.json"
PAIR_DUMMY = "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml"
PAIR_EDIT = "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml"
RECOVERED_AGENT_BY_PAIR = {
    PAIR_DUMMY: (
        ITER73_PROOF
        / "recovered_overlay"
        / "configs"
        / "mini"
        / "telos_vertex_gemini_dummy_receipt_enforced_agent.yaml"
    ),
    PAIR_EDIT: (
        ITER73_PROOF
        / "recovered_overlay"
        / "configs"
        / "mini"
        / "telos_vertex_gemini_edit_receipt_enforced_agent.yaml"
    ),
}


def load_iter72() -> Any:
    spec = importlib.util.spec_from_file_location("iter72_expanded_paid_runner", ITER72_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load iter72 runner: {ITER72_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


iter72 = load_iter72()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} root must be an object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256_file(path: Path) -> str:
    return iter72.sha256_file(path)


def prerequisite_validation() -> dict[str, Any]:
    iter72_summary = read_json(ITER72_SUMMARY)
    iter73_summary = read_json(ITER73_SUMMARY)
    iter74_summary = read_json(ITER74_SUMMARY)
    iter77_summary = read_json(ITER77_SUMMARY)
    iter72_receipts = run_capture(
        ["python3", "scripts/validate_receipts.py", relative(ITER72_PROOF)]
    )
    iter72_audit = run_capture(
        ["python3", "scripts/audit_provider_compatible_expanded_paid_execution_after_slice_refreeze.py"]
    )
    iter73_receipts = run_capture(
        ["python3", "scripts/validate_receipts.py", relative(ITER73_PROOF)]
    )
    iter73_audit = run_capture(
        ["python3", "scripts/audit_expanded_receipt_prompt_recovery_after_paid_block.py"]
    )
    iter74_receipts = run_capture(
        ["python3", "scripts/validate_receipts.py", relative(ITER74_PROOF)]
    )
    iter74_audit = run_capture(
        [
            "python3",
            "scripts/audit_provider_compatible_expanded_paid_retry_after_receipt_prompt_recovery.py",
        ]
    )
    iter77_receipts = run_capture(
        ["python3", "scripts/validate_receipts.py", relative(ITER77_PROOF)]
    )
    iter77_audit = run_capture(
        ["python3", "scripts/audit_runtime_adc_recheck_after_application_default_login.py"]
    )
    recovered_overlays = []
    for pair_id, path in RECOVERED_AGENT_BY_PAIR.items():
        recovered_overlays.append(
            {
                "pair_id": pair_id,
                "source": relative(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
            }
        )
    clean = (
        iter72_summary.get("status") == "blocked"
        and iter72_summary.get("blocked_result") is True
        and iter72_receipts["returncode"] == 0
        and iter72_audit["returncode"] == 0
        and iter73_summary.get("status") == "pass"
        and iter73_summary.get("clean_pass") is True
        and iter73_receipts["returncode"] == 0
        and iter73_audit["returncode"] == 0
        and iter74_summary.get("status") == "blocked"
        and iter74_summary.get("blocked_result") is True
        and int(iter74_summary.get("executed_pair_count", -1)) == 0
        and iter74_receipts["returncode"] == 0
        and iter74_audit["returncode"] == 0
        and iter77_summary.get("status") == "pass"
        and iter77_summary.get("clean_pass") is True
        and iter77_summary.get("adc_access_token_available") is True
        and iter77_receipts["returncode"] == 0
        and iter77_audit["returncode"] == 0
        and all(item["exists"] for item in recovered_overlays)
    )
    return {
        "schema_version": "telos.provider_compatible_expanded_paid_retry.prerequisite_validation.v1",
        "iter72_status": iter72_summary.get("status"),
        "iter72_blocked_result": iter72_summary.get("blocked_result"),
        "iter72_provider_api_calls": iter72_summary.get("provider_api_calls"),
        "iter72_provider_cost_usd": iter72_summary.get("provider_cost_usd"),
        "iter72_receipt_validation_returncode": iter72_receipts["returncode"],
        "iter72_audit_returncode": iter72_audit["returncode"],
        "iter73_status": iter73_summary.get("status"),
        "iter73_clean_pass": iter73_summary.get("clean_pass"),
        "iter73_recovered_prompt_count": iter73_summary.get("recovered_prompt_count"),
        "iter73_receipt_validation_returncode": iter73_receipts["returncode"],
        "iter73_audit_returncode": iter73_audit["returncode"],
        "iter74_status": iter74_summary.get("status"),
        "iter74_blocked_result": iter74_summary.get("blocked_result"),
        "iter74_executed_pair_count": iter74_summary.get("executed_pair_count"),
        "iter74_provider_api_calls": iter74_summary.get("provider_api_calls"),
        "iter74_provider_cost_usd": iter74_summary.get("provider_cost_usd"),
        "iter74_receipt_validation_returncode": iter74_receipts["returncode"],
        "iter74_audit_returncode": iter74_audit["returncode"],
        "iter77_status": iter77_summary.get("status"),
        "iter77_clean_pass": iter77_summary.get("clean_pass"),
        "iter77_adc_access_token_available": iter77_summary.get("adc_access_token_available"),
        "iter77_provider_model_calls": iter77_summary.get("provider_model_calls"),
        "iter77_provider_spend_usd": iter77_summary.get("provider_spend_usd"),
        "iter77_receipt_validation_returncode": iter77_receipts["returncode"],
        "iter77_audit_returncode": iter77_audit["returncode"],
        "iter73_recovered_prompt_overlays": recovered_overlays,
        "clean_prerequisites": clean,
        "paid_execution_allowed": clean,
    }


def configure_iter72_module() -> None:
    iter72.EXPERIMENT_ID = EXPERIMENT_ID
    iter72.EXPERIMENT = EXPERIMENT
    iter72.PROOF = PROOF
    iter72.RAW = RAW
    iter72.VALID = VALID
    iter72.RESULT = RESULT
    iter72.helper.EXPERIMENT_ID = EXPERIMENT_ID
    iter72.helper.EXPERIMENT = EXPERIMENT
    iter72.helper.PROOF = PROOF
    iter72.helper.RAW = RAW
    iter72.helper.VALID = VALID


def iter78_candidate_rows() -> list[dict[str, Any]]:
    rows = copy.deepcopy(iter72_original_candidate_rows())
    for row in rows:
        pair_id = row.get("pair_id")
        recovered = RECOVERED_AGENT_BY_PAIR.get(str(pair_id))
        if recovered is None:
            continue
        adapter = row.setdefault("adapter_evidence", {})
        adapter["iter70_provider_agent_config_replaced_by_iter73"] = adapter.get(
            "provider_agent_config"
        )
        adapter["provider_agent_config"] = relative(recovered)
        adapter["provider_agent_config_source_iteration"] = (
            "iter73_expanded_receipt_prompt_recovery_after_paid_block"
        )
    return rows


def recovered_binding_from_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    copies = manifest.get("copies", [])
    bindings = []
    for pair_id, source_path in RECOVERED_AGENT_BY_PAIR.items():
        source = relative(source_path)
        copy_entry = next(
            (
                item
                for item in copies
                if item.get("source") == source
                and item.get("destination", "").endswith(source_path.name)
            ),
            {},
        )
        bindings.append(
            {
                "pair_id": pair_id,
                "source": source,
                "source_sha256": sha256_file(source_path) if source_path.exists() else None,
                "destination": copy_entry.get("destination"),
                "destination_sha256": copy_entry.get("destination_sha256"),
                "hash_match": copy_entry.get("hash_match"),
                "copied_or_written": copy_entry.get("copied_or_written", False),
                "materialization": copy_entry.get("materialization"),
            }
        )
    all_materialized = all(
        item["copied_or_written"] is True and item["hash_match"] is True for item in bindings
    )
    return {
        "schema_version": "telos.provider_compatible_expanded_paid_retry.recovered_prompt_overlay_binding.v1",
        "source_iteration": "iter73_expanded_receipt_prompt_recovery_after_paid_block",
        "required_pair_count": len(RECOVERED_AGENT_BY_PAIR),
        "bindings": bindings,
        "all_required_recovered_overlays_materialized": all_materialized,
    }


def unmaterialized_recovered_binding(reason: str) -> dict[str, Any]:
    bindings = []
    for pair_id, source_path in RECOVERED_AGENT_BY_PAIR.items():
        bindings.append(
            {
                "pair_id": pair_id,
                "source": relative(source_path),
                "source_sha256": sha256_file(source_path) if source_path.exists() else None,
                "destination": None,
                "destination_sha256": None,
                "hash_match": False,
                "copied_or_written": False,
                "materialization": "not_materialized",
                "blocked_before_materialization_reason": reason,
            }
        )
    return {
        "schema_version": "telos.provider_compatible_expanded_paid_retry.recovered_prompt_overlay_binding.v1",
        "source_iteration": "iter73_expanded_receipt_prompt_recovery_after_paid_block",
        "required_pair_count": len(RECOVERED_AGENT_BY_PAIR),
        "bindings": bindings,
        "all_required_recovered_overlays_materialized": False,
        "blocked_before_materialization_reason": reason,
    }


def iter78_materialize_runtime_overlay(
    rows: list[dict[str, Any]], *, project_id: str, token: str
) -> dict[str, Any]:
    manifest = iter72_original_materialize_runtime_overlay(
        rows,
        project_id=project_id,
        token=token,
    )
    recovered_sources = {relative(path) for path in RECOVERED_AGENT_BY_PAIR.values()}
    for copy_entry in manifest.get("copies", []):
        if copy_entry.get("source") in recovered_sources:
            copy_entry["materialization"] = "copied_iter73_recovered_receipt_prompt_overlay"
            copy_entry["source_override_reason"] = "iter73_receipt_prompt_recovery_after_paid_block"
    binding = recovered_binding_from_manifest(manifest)
    manifest["schema_version"] = (
        "telos.provider_compatible_expanded_paid_retry.overlay_materialization.v1"
    )
    manifest["iter73_recovered_prompt_overlay_binding_path"] = (
        "recovered_prompt_overlay_binding.json"
    )
    manifest["iter73_recovered_prompt_overlays_all_materialized"] = binding[
        "all_required_recovered_overlays_materialized"
    ]
    write_json(PROOF / "recovered_prompt_overlay_binding.json", binding)
    write_json(PROOF / "overlay_materialization_manifest.json", manifest)
    return manifest


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter78-provider-compatible-expanded-paid-retry-after-adc-recovery-{status}",
        "task_id": "telos:iter78_provider_compatible_expanded_paid_retry_after_adc_recovery@iter77",
        "agent_id": "codex-local-expanded-adapter-row-paid-retry-runner",
        "benchmark_id": "telos_codeclash_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Retry only the four iter71-selected adapter rows after iter73 receipt prompt recovery "
            "and iter77 ADC readiness, using the recovered iter73 prompts for receipt-enforced rows."
        ),
        "acceptance_criteria": [
            "Iter72 validates as a clean blocked packet, iter73 validates as a clean recovery pass, iter74 validates as a clean no-row block, and iter77 validates as a clean ADC pass.",
            "Exactly four adapter-planned rows execute and the two retained BattleSnake rows are not rerun.",
            "The two receipt-enforced rows use the iter73 recovered prompt overlays.",
            "Provider calls stay at or below 32 and provider spend at or below $10.00.",
            "Every receipt-enforced row has a valid Telos receipt before verified completion is accepted.",
            "No GPU, cloud runner, Sentinel mutation, live-domain mutation, or benchmark/model claim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                "notes": "Run summary records row execution, prerequisite validation, provider calls, costs, receipts, and claim boundary.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/recovered_prompt_overlay_binding.json",
                "notes": "Binding proves the receipt-enforced rows used iter73 recovered prompt overlays.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/protocol_effect_report.json",
                "notes": "Report records prerequisite validation, row execution count, provider calls, costs, blockers, and claim boundary.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records the stratified no-benchmark/no-model boundary.",
            },
        ],
        "falsifiers": [
            "The result must block if iter72, iter73, iter74, or iter77 validation fails.",
            "The result must fail if any unselected row executes.",
            "The result must fail if provider calls or spend exceed the frozen ceiling.",
            "The result must block if receipt-required rows lack valid receipts.",
            "The result must fail if the recovered iter73 prompt overlays are not materialized.",
            "The result must fail if unsupported benchmark, model-superiority, production, live-domain, leaderboard, SWE-bench, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def primary_metric_from_rows(row_results: list[dict[str, Any]]) -> dict[str, Any]:
    rows_by_pair = {row["pair_id"]: row for row in row_results}
    metric = {
        "dummy_baseline_verified_completion_evidence": rows_by_pair.get(
            "baseline-agent-completion-evidence__configs-test-dummy-yaml", {}
        ).get("verified_completion_evidence", False),
        "dummy_telos_verified_completion_evidence": rows_by_pair.get(PAIR_DUMMY, {}).get(
            "verified_completion_evidence", False
        ),
        "deterministic_edit_baseline_verified_completion_evidence": rows_by_pair.get(
            "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml", {}
        ).get("verified_completion_evidence", False),
        "deterministic_edit_telos_verified_completion_evidence": rows_by_pair.get(
            PAIR_EDIT, {}
        ).get("verified_completion_evidence", False),
    }
    metric["dummy_delta_telos_minus_baseline"] = int(
        bool(metric["dummy_telos_verified_completion_evidence"])
    ) - int(bool(metric["dummy_baseline_verified_completion_evidence"]))
    metric["deterministic_edit_delta_telos_minus_baseline"] = int(
        bool(metric["deterministic_edit_telos_verified_completion_evidence"])
    ) - int(bool(metric["deterministic_edit_baseline_verified_completion_evidence"]))
    return metric


def rewrite_text_artifacts(
    *,
    status: str,
    row_results: list[dict[str, Any]],
    provider_calls: int,
    provider_cost: float,
    blockers: list[str],
    failures: list[str],
    primary_metric: dict[str, Any],
    prerequisite: dict[str, Any],
    overlay_binding: dict[str, Any],
) -> None:
    if row_results:
        summary_sentence = (
            "The gate retried the four iter71-selected adapter-planned rows after iter73 "
            "receipt prompt recovery."
        )
    else:
        summary_sentence = "The gate blocked before adapter-row execution because preflight failed."
    raw_evidence_line = "- `proof/raw/`\n" if row_results else ""
    RESULT.write_text(
        f"""# Iteration 78 Result - Provider-Compatible Expanded Paid Retry After ADC Recovery

Status: `{status.upper()}`.

## Summary

{summary_sentence}

- executed adapter row count: `{len(row_results)}`,
- retained BattleSnake rows rerun: `false`,
- iter72 prerequisite validation clean: `{str(prerequisite['iter72_audit_returncode'] == 0).lower()}`,
- iter73 recovery validation clean: `{str(prerequisite['iter73_audit_returncode'] == 0).lower()}`,
- iter74 blocked retry validation clean: `{str(prerequisite['iter74_audit_returncode'] == 0).lower()}`,
- iter77 ADC readiness validation clean: `{str(prerequisite['iter77_audit_returncode'] == 0).lower()}`,
- recovered iter73 prompt overlays materialized: `{str(overlay_binding['all_required_recovered_overlays_materialized']).lower()}`,
- provider API calls: `{provider_calls}`,
- provider call ceiling: `{iter72.TOTAL_CALL_CEILING}`,
- provider cost from CodeClash metadata: `${provider_cost:.8f}`,
- provider spend ceiling: `${iter72.TOTAL_SPEND_CEILING_USD:.2f}`,
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

This is a bounded four-row adapter-validation retry under a stratified Telos protocol-effect
boundary. It is not a benchmark result, SWE-bench score, leaderboard result,
production/live-domain result, model-superiority result, or state-of-the-art result.

## Evidence

- `proof/prerequisite_validation.json`
- `proof/preflight.json`
- `proof/runtime_access_path_binding.json`
- `proof/runtime_access_path_model_config.yaml`
- `proof/overlay_materialization_manifest.json`
- `proof/recovered_prompt_overlay_binding.json`
- `proof/protocol_effect_report.json`
{raw_evidence_line}- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/{RECEIPT_NAME}`
""",
        encoding="utf-8",
    )

    command_lines = [
        f"provider-compatible expanded paid retry after ADC recovery: {status}",
        f"iter72_receipt_validation_returncode={prerequisite['iter72_receipt_validation_returncode']}",
        f"iter72_audit_returncode={prerequisite['iter72_audit_returncode']}",
        f"iter73_receipt_validation_returncode={prerequisite['iter73_receipt_validation_returncode']}",
        f"iter73_audit_returncode={prerequisite['iter73_audit_returncode']}",
        f"iter74_receipt_validation_returncode={prerequisite['iter74_receipt_validation_returncode']}",
        f"iter74_audit_returncode={prerequisite['iter74_audit_returncode']}",
        f"iter77_receipt_validation_returncode={prerequisite['iter77_receipt_validation_returncode']}",
        f"iter77_audit_returncode={prerequisite['iter77_audit_returncode']}",
        f"iter77_adc_access_token_available={str(prerequisite['iter77_adc_access_token_available']).lower()}",
        f"recovered_iter73_prompt_overlays_materialized={str(overlay_binding['all_required_recovered_overlays_materialized']).lower()}",
        f"selected_pair_count={len(iter72.SELECTED_PAIR_IDS)}",
        f"executed_pair_count={len(row_results)}",
        "retained_battlesnake_rows_rerun=false",
        f"provider_api_calls={provider_calls}",
        f"provider_call_ceiling={iter72.TOTAL_CALL_CEILING}",
        f"provider_cost_usd={provider_cost:.8f}",
        f"provider_spend_ceiling_usd={iter72.TOTAL_SPEND_CEILING_USD:.2f}",
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

    (PROOF / "review.md").write_text(
        f"""# Iteration 78 Review

The gate retried only the four adapter-planned rows selected by iter71, after validating the
iter72 blocked packet, iter73 recovered-prompt packet, iter74 no-row ADC block, and iter77 ADC
readiness pass. The two BattleSnake rows were retained as prior iter66 evidence and were not rerun.

The receipt-enforced Dummy and deterministic-edit rows used the iter73 recovered prompt overlays.
Receipt validation was required before accepting verified completion for those rows. The result
remains stratified by task surface; Dummy and deterministic-edit evidence may not be pooled into a
benchmark/model claim.

- status: `{status}`,
- executed row count: `{len(row_results)}`,
- provider API calls: `{provider_calls}`,
- provider cost: `${provider_cost:.8f}`,
- recovered iter73 prompt overlays materialized: `{str(overlay_binding['all_required_recovered_overlays_materialized']).lower()}`,
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

No benchmark, SWE-bench, leaderboard, production/live-domain, model-superiority, or
state-of-the-art result is claimed.
""",
        encoding="utf-8",
    )


def postprocess_outputs(prerequisite: dict[str, Any]) -> None:
    write_json(PROOF / "prerequisite_validation.json", prerequisite)
    preflight = read_json(PROOF / "preflight.json")
    report = read_json(PROOF / "protocol_effect_report.json")
    summary = read_json(PROOF / "run_summary.json")
    overlay = read_json(PROOF / "overlay_materialization_manifest.json")
    binding_path = PROOF / "recovered_prompt_overlay_binding.json"
    if not binding_path.exists():
        write_json(
            binding_path,
            unmaterialized_recovered_binding("runtime_project_or_adc_token_unavailable"),
        )
    overlay_binding = read_json(binding_path)

    for packet in [preflight, report, summary]:
        packet["prerequisite_validation_path"] = "prerequisite_validation.json"
        packet["iter72_status"] = prerequisite["iter72_status"]
        packet["iter72_blocked_result"] = prerequisite["iter72_blocked_result"]
        packet["iter72_receipt_validation_returncode"] = prerequisite[
            "iter72_receipt_validation_returncode"
        ]
        packet["iter72_audit_returncode"] = prerequisite["iter72_audit_returncode"]
        packet["iter73_status"] = prerequisite["iter73_status"]
        packet["iter73_clean_pass"] = prerequisite["iter73_clean_pass"]
        packet["iter73_receipt_validation_returncode"] = prerequisite[
            "iter73_receipt_validation_returncode"
        ]
        packet["iter73_audit_returncode"] = prerequisite["iter73_audit_returncode"]
        packet["iter74_status"] = prerequisite["iter74_status"]
        packet["iter74_blocked_result"] = prerequisite["iter74_blocked_result"]
        packet["iter74_executed_pair_count"] = prerequisite["iter74_executed_pair_count"]
        packet["iter74_receipt_validation_returncode"] = prerequisite[
            "iter74_receipt_validation_returncode"
        ]
        packet["iter74_audit_returncode"] = prerequisite["iter74_audit_returncode"]
        packet["iter77_status"] = prerequisite["iter77_status"]
        packet["iter77_clean_pass"] = prerequisite["iter77_clean_pass"]
        packet["iter77_adc_access_token_available"] = prerequisite[
            "iter77_adc_access_token_available"
        ]
        packet["iter77_receipt_validation_returncode"] = prerequisite[
            "iter77_receipt_validation_returncode"
        ]
        packet["iter77_audit_returncode"] = prerequisite["iter77_audit_returncode"]
        packet["iter73_recovered_prompt_overlay_binding_path"] = (
            "recovered_prompt_overlay_binding.json"
        )
        packet["iter73_recovered_prompt_overlays_all_materialized"] = overlay_binding[
            "all_required_recovered_overlays_materialized"
        ]
        packet["receipt_enforced_rows_used_iter73_recovered_overlays"] = overlay_binding[
            "all_required_recovered_overlays_materialized"
        ]

    preflight["schema_version"] = (
        "telos.provider_compatible_expanded_paid_retry_after_adc_recovery.preflight.v1"
    )
    report["schema_version"] = (
        "telos.provider_compatible_expanded_paid_retry_after_adc_recovery.report.v1"
    )
    summary["schema_version"] = (
        "telos.provider_compatible_expanded_paid_retry_after_adc_recovery.summary.v1"
    )
    report["prerequisite_validation"] = prerequisite
    report["recovered_prompt_overlay_binding"] = overlay_binding
    summary["recovered_prompt_overlay_binding"] = overlay_binding
    summary["retained_battlesnake_rows_rerun"] = False
    overlay["schema_version"] = (
        "telos.provider_compatible_expanded_paid_retry.overlay_materialization.v1"
    )
    overlay["iter73_recovered_prompt_overlay_binding_path"] = (
        "recovered_prompt_overlay_binding.json"
    )
    overlay["iter73_recovered_prompt_overlays_all_materialized"] = overlay_binding[
        "all_required_recovered_overlays_materialized"
    ]
    write_json(PROOF / "overlay_materialization_manifest.json", overlay)

    blockers = sorted(set(summary.get("blockers", [])))
    failures = sorted(set(summary.get("failures", [])))
    executed_pair_count = int(summary.get("executed_pair_count", 0))
    if not overlay_binding["all_required_recovered_overlays_materialized"]:
        if executed_pair_count:
            failures.append("iter73_recovered_prompt_overlay_not_materialized")
        else:
            blockers.append("iter73_recovered_prompt_overlay_not_materialized")
    summary["blockers"] = sorted(set(blockers))
    report["blockers"] = sorted(set(blockers))
    summary["failures"] = sorted(set(failures))
    report["failures"] = sorted(set(failures))
    status = "fail" if failures else "blocked" if blockers else "pass"
    for packet in [summary, report]:
        packet["status"] = status
        packet["clean_pass"] = status == "pass"
        packet["blocked_result"] = status == "blocked"
        packet["quality_failure"] = status == "fail"

    row_results = report.get("row_results", [])
    provider_calls = int(summary.get("provider_api_calls", 0))
    provider_cost = float(summary.get("provider_cost_usd", 0.0))
    primary_metric = primary_metric_from_rows(row_results)
    summary["primary_metric"] = primary_metric
    report["primary_metric"] = primary_metric

    write_json(PROOF / "preflight.json", iter72.helper.redact_value(preflight))
    write_json(PROOF / "protocol_effect_report.json", iter72.helper.redact_value(report))
    rewrite_text_artifacts(
        status=status,
        row_results=row_results,
        provider_calls=provider_calls,
        provider_cost=provider_cost,
        blockers=summary["blockers"],
        failures=summary["failures"],
        primary_metric=primary_metric,
        prerequisite=prerequisite,
        overlay_binding=overlay_binding,
    )
    old_receipt = VALID / OLD_RECEIPT_NAME
    if old_receipt.exists():
        old_receipt.unlink()
    write_json(VALID / RECEIPT_NAME, build_receipt(status))
    write_json(
        PROOF / "learning_record.json",
        {
            "schema_version": "telos.learning_record.v1",
            "experiment_id": EXPERIMENT_ID,
            "status": status if status != "fail" else "null",
            "insight": (
                "The iter78 paid retry executed under iter73 recovered receipt prompts and iter77 ADC readiness."
                if row_results
                else "The iter78 paid retry blocked before row execution because runtime ADC refresh was unavailable."
            ),
            "next_action": (
                "analyze the stratified retry evidence before any broader benchmark claim"
                if status == "pass"
                else "recover the named prerequisite before retrying paid rows"
                if status == "blocked"
                else "publish the quality-failure boundary before corrective work"
            ),
            "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
            "evidence_paths": [
                f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                f"experiments/{EXPERIMENT_ID}/proof/protocol_effect_report.json",
                f"experiments/{EXPERIMENT_ID}/proof/prerequisite_validation.json",
                f"experiments/{EXPERIMENT_ID}/proof/recovered_prompt_overlay_binding.json",
                f"experiments/{EXPERIMENT_ID}/proof/valid/{RECEIPT_NAME}",
            ],
        },
    )
    summary_paths = [
        PROOF / "prerequisite_validation.json",
        PROOF / "preflight.json",
        PROOF / "runtime_access_path_binding.json",
        PROOF / "runtime_access_path_model_config.yaml",
        PROOF / "overlay_materialization_manifest.json",
        PROOF / "recovered_prompt_overlay_binding.json",
        PROOF / "protocol_effect_report.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
        PROOF / "learning_record.json",
        VALID,
        RAW,
    ]
    summary["artifact_hashes"] = iter72.artifact_hashes(summary_paths)
    write_json(PROOF / "run_summary.json", iter72.helper.redact_value(summary))


def write_preflight_block(prerequisite: dict[str, Any]) -> int:
    if PROOF.exists():
        shutil.rmtree(PROOF)
    PROOF.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    write_json(PROOF / "prerequisite_validation.json", prerequisite)
    iter72.configure_helper()
    iter72.write_unmaterialized_overlay("iter72_or_iter73_or_iter74_or_iter77_prerequisite_validation_failed")
    overlay = read_json(PROOF / "overlay_materialization_manifest.json")
    write_json(
        PROOF / "recovered_prompt_overlay_binding.json",
        {
            "schema_version": "telos.provider_compatible_expanded_paid_retry.recovered_prompt_overlay_binding.v1",
            "source_iteration": "iter73_expanded_receipt_prompt_recovery_after_paid_block",
            "required_pair_count": len(RECOVERED_AGENT_BY_PAIR),
            "bindings": [],
            "all_required_recovered_overlays_materialized": False,
        },
    )
    preflight = {
        "schema_version": "telos.provider_compatible_expanded_paid_retry_after_adc_recovery.preflight.v1",
        "experiment_id": EXPERIMENT_ID,
        "prerequisite_validation_path": "prerequisite_validation.json",
        "iter72_status": prerequisite["iter72_status"],
        "iter72_blocked_result": prerequisite["iter72_blocked_result"],
        "iter72_receipt_validation_returncode": prerequisite["iter72_receipt_validation_returncode"],
        "iter72_audit_returncode": prerequisite["iter72_audit_returncode"],
        "iter73_status": prerequisite["iter73_status"],
        "iter73_clean_pass": prerequisite["iter73_clean_pass"],
        "iter73_receipt_validation_returncode": prerequisite["iter73_receipt_validation_returncode"],
        "iter73_audit_returncode": prerequisite["iter73_audit_returncode"],
        "iter74_status": prerequisite["iter74_status"],
        "iter74_blocked_result": prerequisite["iter74_blocked_result"],
        "iter74_executed_pair_count": prerequisite["iter74_executed_pair_count"],
        "iter74_receipt_validation_returncode": prerequisite["iter74_receipt_validation_returncode"],
        "iter74_audit_returncode": prerequisite["iter74_audit_returncode"],
        "iter77_status": prerequisite["iter77_status"],
        "iter77_clean_pass": prerequisite["iter77_clean_pass"],
        "iter77_adc_access_token_available": prerequisite["iter77_adc_access_token_available"],
        "iter77_receipt_validation_returncode": prerequisite["iter77_receipt_validation_returncode"],
        "iter77_audit_returncode": prerequisite["iter77_audit_returncode"],
        "selected_pair_ids": iter72.SELECTED_PAIR_IDS,
        "expected_selected_pair_ids": iter72.SELECTED_PAIR_IDS,
        "retained_existing_pair_ids": iter72.RETAINED_PAIR_IDS,
        "provider_call_ceiling": iter72.TOTAL_CALL_CEILING,
        "provider_spend_ceiling_usd": iter72.TOTAL_SPEND_CEILING_USD,
        "runtime_overlay_all_materialized": overlay.get("all_materialized"),
        "runtime_overlay_copied_hashes_match": overlay.get("copied_hashes_match"),
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
    }
    blockers = ["iter72_or_iter73_or_iter74_or_iter77_prerequisite_validation_failed"]
    write_json(PROOF / "preflight.json", preflight)
    report = {
        "schema_version": "telos.provider_compatible_expanded_paid_retry_after_adc_recovery.report.v1",
        "status": "blocked",
        "experiment_id": EXPERIMENT_ID,
        "preflight": preflight,
        "selected_pair_ids": iter72.SELECTED_PAIR_IDS,
        "retained_existing_pair_ids": iter72.RETAINED_PAIR_IDS,
        "executed_pair_ids": [],
        "executed_pair_count": 0,
        "row_results": [],
        "provider_api_calls": 0,
        "provider_call_ceiling": iter72.TOTAL_CALL_CEILING,
        "provider_cost_usd": 0.0,
        "provider_spend_ceiling_usd": iter72.TOTAL_SPEND_CEILING_USD,
        "primary_metric": primary_metric_from_rows([]),
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
        "redaction_scan_passed": True,
        "redaction_findings": [],
        "blockers": blockers,
        "failures": [],
        "prerequisite_validation": prerequisite,
        "iter72_status": prerequisite["iter72_status"],
        "iter72_blocked_result": prerequisite["iter72_blocked_result"],
        "iter72_receipt_validation_returncode": prerequisite["iter72_receipt_validation_returncode"],
        "iter72_audit_returncode": prerequisite["iter72_audit_returncode"],
        "iter73_status": prerequisite["iter73_status"],
        "iter73_clean_pass": prerequisite["iter73_clean_pass"],
        "iter73_receipt_validation_returncode": prerequisite["iter73_receipt_validation_returncode"],
        "iter73_audit_returncode": prerequisite["iter73_audit_returncode"],
        "iter74_status": prerequisite["iter74_status"],
        "iter74_blocked_result": prerequisite["iter74_blocked_result"],
        "iter74_executed_pair_count": prerequisite["iter74_executed_pair_count"],
        "iter74_receipt_validation_returncode": prerequisite["iter74_receipt_validation_returncode"],
        "iter74_audit_returncode": prerequisite["iter74_audit_returncode"],
        "iter77_status": prerequisite["iter77_status"],
        "iter77_clean_pass": prerequisite["iter77_clean_pass"],
        "iter77_adc_access_token_available": prerequisite["iter77_adc_access_token_available"],
        "iter77_receipt_validation_returncode": prerequisite["iter77_receipt_validation_returncode"],
        "iter77_audit_returncode": prerequisite["iter77_audit_returncode"],
    }
    write_json(PROOF / "protocol_effect_report.json", report)
    write_json(VALID / RECEIPT_NAME, build_receipt("blocked"))
    rewrite_text_artifacts(
        status="blocked",
        row_results=[],
        provider_calls=0,
        provider_cost=0.0,
        blockers=blockers,
        failures=[],
        primary_metric=report["primary_metric"],
        prerequisite=prerequisite,
        overlay_binding=read_json(PROOF / "recovered_prompt_overlay_binding.json"),
    )
    summary_paths = [
        PROOF / "prerequisite_validation.json",
        PROOF / "preflight.json",
        PROOF / "runtime_access_path_binding.json",
        PROOF / "runtime_access_path_model_config.yaml",
        PROOF / "overlay_materialization_manifest.json",
        PROOF / "recovered_prompt_overlay_binding.json",
        PROOF / "protocol_effect_report.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
        VALID,
        RAW,
    ]
    write_json(
        PROOF / "run_summary.json",
        {
            "schema_version": "telos.provider_compatible_expanded_paid_retry_after_adc_recovery.summary.v1",
            "status": "blocked",
            "experiment_id": EXPERIMENT_ID,
            "selected_pair_ids": iter72.SELECTED_PAIR_IDS,
            "retained_existing_pair_ids": iter72.RETAINED_PAIR_IDS,
            "executed_pair_count": 0,
            "executed_pair_ids": [],
            "provider_api_calls": 0,
            "provider_call_ceiling": iter72.TOTAL_CALL_CEILING,
            "provider_cost_usd": 0.0,
            "provider_spend_ceiling_usd": iter72.TOTAL_SPEND_CEILING_USD,
            "primary_metric": report["primary_metric"],
            "clean_pass": False,
            "blocked_result": True,
            "quality_failure": False,
            "blockers": blockers,
            "failures": [],
            "gpu_used": False,
            "cloud_runner_started": False,
            "sentinel_named_resources_modified": False,
            "production_or_live_domain_changed": False,
            "benchmark_result_claimed": False,
            "leaderboard_or_swebench_result_claimed": False,
            "model_superiority_claimed": False,
            "state_of_the_art_result_claimed": False,
            "iter72_status": prerequisite["iter72_status"],
            "iter72_blocked_result": prerequisite["iter72_blocked_result"],
            "iter72_receipt_validation_returncode": prerequisite[
                "iter72_receipt_validation_returncode"
            ],
            "iter72_audit_returncode": prerequisite["iter72_audit_returncode"],
            "iter73_status": prerequisite["iter73_status"],
            "iter73_clean_pass": prerequisite["iter73_clean_pass"],
            "iter73_receipt_validation_returncode": prerequisite[
                "iter73_receipt_validation_returncode"
            ],
            "iter73_audit_returncode": prerequisite["iter73_audit_returncode"],
            "iter74_status": prerequisite["iter74_status"],
            "iter74_blocked_result": prerequisite["iter74_blocked_result"],
            "iter74_executed_pair_count": prerequisite["iter74_executed_pair_count"],
            "iter74_receipt_validation_returncode": prerequisite[
                "iter74_receipt_validation_returncode"
            ],
            "iter74_audit_returncode": prerequisite["iter74_audit_returncode"],
            "iter77_status": prerequisite["iter77_status"],
            "iter77_clean_pass": prerequisite["iter77_clean_pass"],
            "iter77_adc_access_token_available": prerequisite[
                "iter77_adc_access_token_available"
            ],
            "iter77_receipt_validation_returncode": prerequisite[
                "iter77_receipt_validation_returncode"
            ],
            "iter77_audit_returncode": prerequisite["iter77_audit_returncode"],
            "artifact_hashes": iter72.artifact_hashes(summary_paths),
        },
    )
    return 0


iter72_original_candidate_rows = iter72.candidate_rows
iter72_original_materialize_runtime_overlay = iter72.materialize_runtime_overlay


def main() -> int:
    configure_iter72_module()
    iter72.candidate_rows = iter78_candidate_rows
    iter72.materialize_runtime_overlay = iter78_materialize_runtime_overlay
    prerequisite = prerequisite_validation()
    if prerequisite["clean_prerequisites"] is not True:
        return write_preflight_block(prerequisite)
    rc = iter72.main()
    postprocess_outputs(prerequisite)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
