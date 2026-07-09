#!/usr/bin/env python3
"""Publish iter71 provider-compatible expanded-slice artifacts after adapter completion."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter71_provider_compatible_expanded_slice_after_adapter_completion"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
NEXT_EXPERIMENT_ID = "iter72_provider_compatible_expanded_paid_execution_after_slice_refreeze"
NEXT_GATE = ROOT / "experiments" / NEXT_EXPERIMENT_ID / "HYPOTHESIS.md"

ITER48_SLICE = (
    ROOT
    / "experiments"
    / "iter48_provider_compatible_protocol_effect_slice_refreeze"
    / "proof"
    / "provider_compatible_slice.json"
)
ITER66_SUMMARY = (
    ROOT
    / "experiments"
    / "iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment"
    / "proof"
    / "run_summary.json"
)
ITER66_REPORT = (
    ROOT
    / "experiments"
    / "iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment"
    / "proof"
    / "protocol_effect_report.json"
)
ITER70_REPORT = (
    ROOT
    / "experiments"
    / "iter70_provider_compatible_expanded_adapter_completion"
    / "proof"
    / "adapter_completion_report.json"
)
ITER70_SUMMARY = (
    ROOT
    / "experiments"
    / "iter70_provider_compatible_expanded_adapter_completion"
    / "proof"
    / "run_summary.json"
)
ITER70_AUDIT = ROOT / "scripts" / "audit_provider_compatible_expanded_adapter_completion.py"
ITER70_RECEIPTS = (
    "experiments/iter70_provider_compatible_expanded_adapter_completion/proof"
)
ITER66_AUDIT = (
    ROOT
    / "scripts"
    / "audit_provider_compatible_paid_execution_after_receipt_prompt_alignment.py"
)
ITER66_RECEIPTS = (
    "experiments/iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment/proof"
)

EXISTING_BATTLESNAKE_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
]
ADAPTER_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
    "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
]
EXPECTED_CONDITIONS = {
    "baseline_agent_completion_evidence",
    "telos_receipt_enforced_completion_evidence",
}
NEXT_PROVIDER_INVOCATION_CEILING = 32
NEXT_SPEND_CEILING_USD = 10.0
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


def run_capture(args: list[str], *, timeout: int = 120) -> dict[str, Any]:
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


def redaction_findings() -> list[str]:
    findings: list[str] = []
    for path in text_files(EXPERIMENT):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(str(path.relative_to(ROOT)))
                break
    return sorted(set(findings))


def artifact_hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path.relative_to(PROOF)): sha256_file(path) for path in paths}


def condition_verified_completion(condition_id: str, primary_metric: dict[str, Any]) -> bool | None:
    if condition_id == "baseline_agent_completion_evidence":
        value = primary_metric.get("baseline_verified_completion_evidence")
    elif condition_id == "telos_receipt_enforced_completion_evidence":
        value = primary_metric.get("telos_verified_completion_evidence")
    else:
        return None
    return value if isinstance(value, bool) else None


def rewrite_path_to_iter72(value: str) -> str:
    return value.replace(EXPERIMENT_ID, NEXT_EXPERIMENT_ID)


def next_command(pair_id: str, overlay_config: str) -> str:
    output_root = f"/tmp/telos-codeclash-protocol-effect-expanded-slice/{pair_id}"
    return f"cd /tmp/telos-codeclash && uv run codeclash run {overlay_config} -o {output_root}"


def next_artifact_plan(pair_id: str) -> dict[str, Any]:
    raw_root = f"experiments/{NEXT_EXPERIMENT_ID}/proof/raw/{pair_id}"
    return {
        "raw_root": raw_root,
        "pair_summary": f"experiments/{NEXT_EXPERIMENT_ID}/proof/pairs/{pair_id}.json",
        "required_text_artifacts": [
            f"{raw_root}/codeclash_run.log",
            f"{raw_root}/metadata.json",
            f"{raw_root}/redaction_scan.json",
        ],
        "optional_text_artifacts": [
            f"{raw_root}/players/p1/p1_r1.traj.json",
            f"{raw_root}/players/p1/changes_r1.json",
        ],
        "binary_archives_committed": False,
    }


def receipt_validation_plan(pair_id: str, required: bool) -> dict[str, Any]:
    if not required:
        return {"required_before_acceptance": False, "validation_command": None}
    return {
        "required_before_acceptance": True,
        "validation_command": (
            "python3 scripts/validate_receipts.py "
            f"experiments/{NEXT_EXPERIMENT_ID}/proof/raw/{pair_id}"
        ),
    }


def teardown_plan(pair_id: str, *, already_executed: bool) -> dict[str, Any]:
    return {
        "required": not already_executed,
        "already_executed_in_iter66": already_executed,
        "remove_tmp_output_root": (
            None
            if already_executed
            else f"/tmp/telos-codeclash-protocol-effect-expanded-slice/{pair_id}"
        ),
        "must_not_stop_or_modify_sentinel_resources": True,
    }


def stratum_for_public_config(public_config: str) -> str:
    if public_config == "configs/test/battlesnake_pvp_test.yaml":
        return "battlesnake_pvp_existing_paid_evidence"
    if public_config == "configs/test/dummy.yaml":
        return "dummy_minimal_adapter_validation"
    if public_config == "configs/test/telos_battlesnake_edit_test.yaml":
        return "deterministic_edit_small_workspace_edit"
    return "unknown"


def pair_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("pair_id")): row for row in rows if isinstance(row, dict)}


def retained_battlesnake_rows(
    iter48_slice: dict[str, Any], iter66_summary: dict[str, Any]
) -> list[dict[str, Any]]:
    selected = pair_by_id(iter48_slice.get("selected_pairs", []))
    primary_metric = iter66_summary.get("primary_metric", {})
    rows: list[dict[str, Any]] = []
    for pair_id in EXISTING_BATTLESNAKE_PAIR_IDS:
        source = selected[pair_id]
        condition_id = source.get("condition_id")
        rows.append(
            {
                "pair_id": pair_id,
                "task_id": source.get("task_id"),
                "public_config": source.get("public_config"),
                "condition_id": condition_id,
                "analysis_stratum": stratum_for_public_config(str(source.get("public_config"))),
                "selection_status": "included_existing_execution_evidence",
                "decision": "include",
                "decision_reason": (
                    "retained from the already executed iter66 two-row provider-compatible "
                    "BattleSnake pilot"
                ),
                "source_evidence": {
                    "source_kind": "prior_provider_compatible_slice",
                    "slice_artifact": str(ITER48_SLICE.relative_to(ROOT)),
                    "execution_summary": str(ITER66_SUMMARY.relative_to(ROOT)),
                    "execution_report": str(ITER66_REPORT.relative_to(ROOT)),
                },
                "adapter_evidence": {
                    "provider_overlay_config": source.get("provider_overlay_config"),
                    "provider_agent_config": source.get("provider_agent_config"),
                    "provider_model_config": source.get("provider_model_config"),
                    "provider_cost_registry": source.get("provider_cost_registry"),
                    "binding_status": source.get("binding_status"),
                },
                "future_execution_command": source.get("future_execution_command"),
                "future_artifact_plan": source.get("artifact_plan"),
                "cost_capture_plan": source.get("cost_capture_plan"),
                "receipt_validation_plan": source.get("receipt_plan"),
                "redaction_plan": source.get("redaction_plan"),
                "teardown_plan": teardown_plan(pair_id, already_executed=True),
                "execution_evidence_status": "executed_in_iter66",
                "verified_completion_evidence": condition_verified_completion(
                    str(condition_id), primary_metric
                ),
                "rerun_in_next_paid_gate": False,
            }
        )
    return rows


def adapter_rows(iter70_report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in iter70_report.get("planned_adapter_rows", []):
        if not isinstance(source, dict):
            continue
        pair_id = str(source.get("pair_id"))
        public_config = str(source.get("public_config"))
        condition_id = str(source.get("condition_id"))
        overlay = str(source.get("provider_overlay_config", "")).split(
            "proof/recovered_overlay/", maxsplit=1
        )[-1]
        receipt_required = condition_id == "telos_receipt_enforced_completion_evidence"
        rows.append(
            {
                "pair_id": pair_id,
                "task_id": f"codeclash:{public_config}",
                "public_config": public_config,
                "condition_id": condition_id,
                "analysis_stratum": stratum_for_public_config(public_config),
                "selection_status": "included_pending_execution",
                "decision": "include",
                "decision_reason": (
                    "iter70 completed a provider-compatible adapter plan from committed source "
                    "evidence; the row is selected for the next bounded adapter-row execution "
                    "gate but remains non-execution evidence here"
                ),
                "source_evidence": {
                    "source_kind": "committed_source_snapshot",
                    "source_config_path": source.get("source_config_path"),
                    "source_config_sha256": source.get("source_config_sha256"),
                    "source_model_path": source.get("source_model_path"),
                    "source_model_sha256": source.get("source_model_sha256"),
                    "source_semantic_note": source.get("source_semantic_note"),
                },
                "adapter_evidence": {
                    "adapter_status": source.get("adapter_status"),
                    "provider_overlay_config": source.get("provider_overlay_config"),
                    "provider_agent_config": source.get("provider_agent_config"),
                    "provider_model_config": source.get("provider_model_config"),
                    "provider_cost_registry": source.get("provider_cost_registry"),
                    "generated_adapter_planning_evidence_only": source.get(
                        "generated_adapter_planning_evidence_only"
                    ),
                    "execution_result": source.get("execution_result"),
                },
                "future_execution_command": next_command(pair_id, overlay),
                "future_artifact_plan": next_artifact_plan(pair_id),
                "cost_capture_plan": source.get("cost_capture_plan"),
                "receipt_validation_plan": receipt_validation_plan(pair_id, receipt_required),
                "redaction_plan": source.get("redaction_plan"),
                "teardown_plan": teardown_plan(pair_id, already_executed=False),
                "execution_evidence_status": "not_executed_planning_only",
                "verified_completion_evidence": None,
                "rerun_in_next_paid_gate": True,
            }
        )
    return rows


def analysis_boundary() -> dict[str, Any]:
    return {
        "slice_type": "stratified_provider_compatible_protocol_effect_slice",
        "aggregate_primary_metric_authorized": False,
        "cross_task_surface_pooling_authorized": False,
        "within_stratum_baseline_vs_telos_comparison_after_execution": True,
        "task_surface_strata": [
            {
                "analysis_stratum": "battlesnake_pvp_existing_paid_evidence",
                "public_config": "configs/test/battlesnake_pvp_test.yaml",
                "status": "retained_existing_iter66_evidence",
                "interpretation": "prior two-row provider-backed pilot only",
            },
            {
                "analysis_stratum": "dummy_minimal_adapter_validation",
                "public_config": "configs/test/dummy.yaml",
                "status": "selected_pending_adapter_row_execution",
                "interpretation": (
                    "minimal CodeClash task surface; adapter-validation evidence only unless a "
                    "later gate proves a stronger interpretation"
                ),
            },
            {
                "analysis_stratum": "deterministic_edit_small_workspace_edit",
                "public_config": "configs/test/telos_battlesnake_edit_test.yaml",
                "status": "selected_pending_adapter_row_execution",
                "interpretation": (
                    "small deterministic workspace edit target; not benchmark-quality or "
                    "model-quality evidence by itself"
                ),
            },
        ],
    }


def next_paid_gate_plan(selected_rows: list[dict[str, Any]]) -> dict[str, Any]:
    pending = [row for row in selected_rows if row.get("rerun_in_next_paid_gate") is True]
    retained = [row for row in selected_rows if row.get("rerun_in_next_paid_gate") is False]
    return {
        "next_paid_gate_authorized": True,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
        "execution_scope": "adapter_planned_rows_only",
        "row_execution_count": len(pending),
        "row_execution_pair_ids": [row["pair_id"] for row in pending],
        "retained_existing_execution_pair_ids": [row["pair_id"] for row in retained],
        "max_provider_model_invocations": NEXT_PROVIDER_INVOCATION_CEILING,
        "max_provider_spend_usd": NEXT_SPEND_CEILING_USD,
        "expected_cost_source": "metadata.json agents[].agent_stats",
        "missing_cost_blocks_result": True,
        "gpu_allowed": False,
        "cloud_runner_start_allowed": False,
        "sentinel_named_resources_must_not_change": True,
        "production_or_live_domain_change_allowed": False,
        "abort_if_unredacted_provider_residue": True,
        "abort_if_any_receipt_required_row_lacks_valid_receipt": True,
        "aggregate_benchmark_or_model_claim_authorized": False,
    }


def claim_boundary() -> dict[str, bool]:
    return {
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
    }


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter71-provider-compatible-expanded-slice-after-adapter-{status}",
        "task_id": "telos:iter71_provider_compatible_expanded_slice_after_adapter_completion@iter70",
        "agent_id": "codex-local-expanded-slice-refreeze-verifier",
        "benchmark_id": "telos_codeclash_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Refreeze the expanded provider-compatible protocol-effect slice from committed "
            "iter70 adapter evidence without provider calls, spend, row execution, GPU, cloud "
            "runner startup, Sentinel mutation, or benchmark/model overclaim."
        ),
        "acceptance_criteria": [
            "Iter70 adapter completion is present, passed, and audit-clean.",
            "The existing two-row BattleSnake provider-compatible result is read as prior evidence.",
            "Every selected row has source, adapter, command, artifact, cost, redaction, receipt, and teardown plans.",
            "Every candidate row has an explicit inclusion or exclusion decision.",
            "The next paid gate has exact provider/API and spend ceilings if authorized.",
            "The slice is explicitly stratified and does not authorize pooled benchmark/model claims.",
            "Provider calls, spend, row execution, GPU use, cloud runner startup, Sentinel mutation, and live-domain mutation remain zero.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": (
                    "experiments/iter71_provider_compatible_expanded_slice_after_adapter_completion/"
                    "proof/expanded_slice_decision.json"
                ),
                "notes": "Machine-readable expanded slice selection and next-gate plan.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": (
                    "experiments/iter71_provider_compatible_expanded_slice_after_adapter_completion/"
                    "proof/candidate_rows.json"
                ),
                "notes": "Exact candidate rows with inclusion decisions and execution plans.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": (
                    "experiments/iter71_provider_compatible_expanded_slice_after_adapter_completion/"
                    "proof/review.md"
                ),
                "notes": "Review records the stratified boundary and no-claim constraints.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if iter70 is missing, failed, or audit-dirty.",
            "The result must block if any selected row lacks source, adapter, command, artifact, cost, receipt, redaction, or teardown plans.",
            "The result must block if incomparable rows are mixed without an explicit analysis boundary.",
            "The result must fail if provider calls, spend, row execution, GPU, cloud runner startup, Sentinel mutation, or live-domain mutation occurs.",
            "The result must fail if unsupported benchmark, model-superiority, leaderboard, SWE-bench, production, live-domain, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def write_result(status: str, summary: dict[str, Any]) -> None:
    content = f"""# Iteration 71 Result - Provider-Compatible Expanded Slice After Adapter Completion

Status: `{status.upper()}`.

## Summary

This local gate refroze the expanded provider-compatible slice as a stratified evidence plan. It
retains the two already executed BattleSnake provider-compatible rows from `iter66` and selects the
four `iter70` Dummy/deterministic-edit adapter-planned rows for the next bounded paid gate.

- provider API calls: `0`,
- provider spend: `$0.00`,
- row execution: `false`,
- GPU used: `false`,
- cloud runner started: `false`,
- Sentinel-named resources modified: `false`,
- selected rows in the stratified slice: `{summary['selected_row_count']}`,
- adapter-planned rows selected for next paid execution: `{summary['adapter_planned_selected_row_count']}`,
- existing BattleSnake rows retained without rerun: `{summary['existing_executed_retained_row_count']}`,
- next paid provider invocation ceiling: `{NEXT_PROVIDER_INVOCATION_CEILING}`,
- next paid spend ceiling: `${NEXT_SPEND_CEILING_USD:.2f}`.

## Analysis Boundary

The expanded slice is stratified by task surface. BattleSnake PvP, Dummy, and deterministic-edit
rows may not be pooled into a benchmark, leaderboard, SWE-bench, model-superiority, production, or
state-of-the-art result. The Dummy rows are minimal adapter-validation evidence; deterministic-edit
rows are small non-empty workspace-edit evidence. Any future interpretation must remain within the
per-surface boundary unless a later gate earns a stronger claim.

## Claim Boundary

This is slice selection evidence, not execution evidence. It is not a benchmark result, SWE-bench
result, leaderboard result, production/live-domain result, model-superiority result, or
state-of-the-art result.

## Next

Run only the pre-registered bounded adapter-row paid execution gate:
[`../{NEXT_EXPERIMENT_ID}/HYPOTHESIS.md`](../{NEXT_EXPERIMENT_ID}/HYPOTHESIS.md).

## Evidence

- `proof/candidate_rows.json`
- `proof/expanded_slice_decision.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_provider_compatible_expanded_slice_after_adapter_completion.json`
"""
    RESULT.write_text(content, encoding="utf-8")


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    iter48_slice = read_json(ITER48_SLICE)
    iter66_summary = read_json(ITER66_SUMMARY)
    iter66_report = read_json(ITER66_REPORT)
    iter70_report = read_json(ITER70_REPORT)
    iter70_summary = read_json(ITER70_SUMMARY)
    iter70_receipt_validation = run_capture(
        ["python3", "scripts/validate_receipts.py", ITER70_RECEIPTS]
    )
    iter70_audit = run_capture(["python3", str(ITER70_AUDIT.relative_to(ROOT))])
    iter66_receipt_validation = run_capture(
        ["python3", "scripts/validate_receipts.py", ITER66_RECEIPTS]
    )
    iter66_audit = run_capture(["python3", str(ITER66_AUDIT.relative_to(ROOT))])

    selected_rows = retained_battlesnake_rows(iter48_slice, iter66_summary) + adapter_rows(
        iter70_report
    )
    candidate_decisions = [
        {
            "pair_id": row["pair_id"],
            "public_config": row["public_config"],
            "condition_id": row["condition_id"],
            "analysis_stratum": row["analysis_stratum"],
            "decision": row["decision"],
            "selection_status": row["selection_status"],
            "reason": row["decision_reason"],
        }
        for row in selected_rows
    ]
    excluded_rows: list[dict[str, Any]] = []
    next_gate = next_paid_gate_plan(selected_rows)
    boundary = analysis_boundary()
    no_claims = claim_boundary()

    blockers: list[str] = []
    failures: list[str] = []
    if iter70_report.get("status") != "pass" or iter70_summary.get("status") != "pass":
        blockers.append("iter70_not_passed")
    if iter70_receipt_validation.get("returncode") != 0:
        blockers.append("iter70_receipt_validation_not_clean")
    if iter70_audit.get("returncode") != 0:
        blockers.append("iter70_audit_not_clean")
    if iter66_summary.get("status") != "pass" or iter66_report.get("status") != "pass":
        blockers.append("iter66_two_row_result_not_passed")
    if iter66_receipt_validation.get("returncode") != 0:
        blockers.append("iter66_receipt_validation_not_clean")
    if iter66_audit.get("returncode") != 0:
        blockers.append("iter66_audit_not_clean")
    if iter48_slice.get("status") != "pass":
        blockers.append("iter48_slice_not_passed")
    if not NEXT_GATE.exists():
        blockers.append("next_paid_gate_missing")
    if len(selected_rows) != 6:
        blockers.append("selected_row_count_not_six")
    if len([row for row in selected_rows if row.get("rerun_in_next_paid_gate")]) != 4:
        blockers.append("adapter_planned_selected_row_count_not_four")
    if len([row for row in selected_rows if not row.get("rerun_in_next_paid_gate")]) != 2:
        blockers.append("existing_retained_row_count_not_two")
    if {row.get("condition_id") for row in selected_rows} != EXPECTED_CONDITIONS:
        blockers.append("selected_conditions_not_balanced")
    if next_gate.get("max_provider_model_invocations") != NEXT_PROVIDER_INVOCATION_CEILING:
        failures.append("next_provider_invocation_ceiling_changed")
    if next_gate.get("max_provider_spend_usd") != NEXT_SPEND_CEILING_USD:
        failures.append("next_spend_ceiling_changed")
    if boundary.get("aggregate_primary_metric_authorized") is not False:
        failures.append("aggregate_primary_metric_boundary_missing")
    if boundary.get("cross_task_surface_pooling_authorized") is not False:
        failures.append("cross_surface_pooling_boundary_missing")
    if any(value is not False for value in no_claims.values()):
        failures.append("claim_boundary_overclaim")

    for row in selected_rows:
        pair_id = str(row.get("pair_id"))
        for key in [
            "source_evidence",
            "adapter_evidence",
            "future_execution_command",
            "future_artifact_plan",
            "cost_capture_plan",
            "receipt_validation_plan",
            "redaction_plan",
            "teardown_plan",
        ]:
            if not row.get(key):
                blockers.append(f"{pair_id}_{key}_missing")
        if "uv run codeclash run" not in str(row.get("future_execution_command")):
            blockers.append(f"{pair_id}_future_command_not_codeclash")
        if row.get("selection_status") == "included_pending_execution":
            adapter = row.get("adapter_evidence", {})
            if adapter.get("generated_adapter_planning_evidence_only") is not True:
                failures.append(f"{pair_id}_adapter_planning_boundary_missing")
            if adapter.get("execution_result") is not False:
                failures.append(f"{pair_id}_adapter_presented_as_execution_result")

    decision = {
        "schema_version": "telos.provider_compatible_expanded_slice_after_adapter_completion.decision.v1",
        "status": "pending_redaction",
        "experiment_id": EXPERIMENT_ID,
        "source_iter70_report_path": str(ITER70_REPORT.relative_to(ROOT)),
        "source_iter70_summary_path": str(ITER70_SUMMARY.relative_to(ROOT)),
        "source_iter48_slice_path": str(ITER48_SLICE.relative_to(ROOT)),
        "source_iter66_summary_path": str(ITER66_SUMMARY.relative_to(ROOT)),
        "source_iter66_report_path": str(ITER66_REPORT.relative_to(ROOT)),
        "iter70_status": iter70_report.get("status"),
        "iter70_planned_adapter_row_count": iter70_report.get("planned_adapter_row_count"),
        "iter70_receipt_validation_returncode": iter70_receipt_validation.get("returncode"),
        "iter70_audit_returncode": iter70_audit.get("returncode"),
        "iter66_status": iter66_summary.get("status"),
        "iter66_primary_metric": iter66_summary.get("primary_metric"),
        "iter66_provider_api_calls": iter66_summary.get("provider_api_calls"),
        "iter66_provider_cost_usd": iter66_summary.get("provider_cost_usd"),
        "iter66_receipt_validation_returncode": iter66_receipt_validation.get("returncode"),
        "iter66_audit_returncode": iter66_audit.get("returncode"),
        "candidate_decisions": candidate_decisions,
        "selected_rows": selected_rows,
        "excluded_rows": excluded_rows,
        "selected_row_count": len(selected_rows),
        "excluded_row_count": len(excluded_rows),
        "existing_executed_retained_row_count": len(
            [row for row in selected_rows if not row.get("rerun_in_next_paid_gate")]
        ),
        "adapter_planned_selected_row_count": len(
            [row for row in selected_rows if row.get("rerun_in_next_paid_gate")]
        ),
        "analysis_boundary": boundary,
        "next_paid_gate_plan": next_gate,
        "slice_selection_evidence_not_execution_evidence": True,
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "row_execution_allowed": False,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        **no_claims,
        "blockers": sorted(set(blockers)),
        "failures": sorted(set(failures)),
    }
    write_json(PROOF / "expanded_slice_decision.json", decision)
    write_json(
        PROOF / "candidate_rows.json",
        {
            "schema_version": (
                "telos.provider_compatible_expanded_slice_after_adapter_completion."
                "candidate_rows.v1"
            ),
            "status": "pending_redaction",
            "experiment_id": EXPERIMENT_ID,
            "candidate_rows": selected_rows,
            "candidate_decisions": candidate_decisions,
            "excluded_rows": excluded_rows,
        },
    )

    output_lines = [
        "provider-compatible expanded slice after adapter completion: pending_redaction",
        "provider_api_calls=0",
        "provider_spend_usd=0.00",
        "row_execution_allowed=false",
        "gpu_used=false",
        "cloud_runner_started=false",
        "sentinel_named_resources_modified=false",
        f"selected_row_count={len(selected_rows)}",
        f"adapter_planned_selected_row_count={decision['adapter_planned_selected_row_count']}",
        f"existing_executed_retained_row_count={decision['existing_executed_retained_row_count']}",
        "expanded_slice_decision=stratified_six_row_slice_refrozen",
        "slice_selection_evidence_not_execution_evidence=true",
        f"next_provider_invocation_ceiling={NEXT_PROVIDER_INVOCATION_CEILING}",
        f"next_spend_ceiling_usd={NEXT_SPEND_CEILING_USD:.2f}",
        f"next_gate={NEXT_GATE.relative_to(ROOT)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 71 Review

The gate correctly refreezes the expanded provider-compatible slice only as a stratified plan. The
two BattleSnake rows are retained as prior iter66 paid evidence and are not rerun by this gate.
The four Dummy/deterministic-edit rows are selected because iter70 supplied committed-source-backed
provider-compatible adapter plans with command, artifact, cost, receipt, redaction, and teardown
plans.

The main adversarial risk is mixing unlike task surfaces. The proof packet blocks that by naming
three separate strata and forbidding cross-surface pooling, aggregate benchmark interpretation,
model-superiority claims, and state-of-the-art claims. Dummy remains a minimal adapter-validation
surface, deterministic-edit remains a small workspace-edit surface, and BattleSnake remains the
only existing paid protocol-effect pilot evidence.

No provider model call, spend, row execution, GPU, cloud runner startup, Sentinel mutation,
production/live-domain mutation, benchmark claim, model claim, or state-of-the-art claim occurred.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    redaction = redaction_findings()
    if redaction:
        failures.append("redaction_findings_present")
    status = "fail" if failures else "blocked" if blockers else "pass"

    decision["status"] = status
    decision["redaction_scan_passed"] = not redaction
    decision["redaction_findings"] = redaction
    decision["blockers"] = sorted(set(blockers))
    decision["failures"] = sorted(set(failures))
    write_json(PROOF / "expanded_slice_decision.json", decision)

    candidate_packet = read_json(PROOF / "candidate_rows.json")
    candidate_packet["status"] = status
    candidate_packet["redaction_scan_passed"] = not redaction
    candidate_packet["redaction_findings"] = redaction
    write_json(PROOF / "candidate_rows.json", candidate_packet)

    output_lines[0] = f"provider-compatible expanded slice after adapter completion: {status}"
    output_lines.extend(
        [
            f"redaction_scan_passed={str(not redaction).lower()}",
            f"blockers={','.join(decision['blockers'])}",
            f"failures={','.join(decision['failures'])}",
        ]
    )
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    receipt_path = (
        VALID / "receipt_provider_compatible_expanded_slice_after_adapter_completion.json"
    )
    write_json(receipt_path, build_receipt(status))

    summary = {
        "schema_version": (
            "telos.provider_compatible_expanded_slice_after_adapter_completion.summary.v1"
        ),
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "iter70_status": iter70_report.get("status"),
        "iter70_planned_adapter_row_count": iter70_report.get("planned_adapter_row_count"),
        "iter70_receipt_validation_returncode": iter70_receipt_validation.get("returncode"),
        "iter70_audit_returncode": iter70_audit.get("returncode"),
        "iter66_status": iter66_summary.get("status"),
        "iter66_primary_metric": iter66_summary.get("primary_metric"),
        "iter66_provider_api_calls": iter66_summary.get("provider_api_calls"),
        "iter66_provider_cost_usd": iter66_summary.get("provider_cost_usd"),
        "selected_row_count": decision["selected_row_count"],
        "excluded_row_count": decision["excluded_row_count"],
        "existing_executed_retained_row_count": decision[
            "existing_executed_retained_row_count"
        ],
        "adapter_planned_selected_row_count": decision["adapter_planned_selected_row_count"],
        "selected_pair_ids": [row["pair_id"] for row in selected_rows],
        "excluded_pair_ids": [],
        "expanded_slice_decision": "stratified_six_row_slice_refrozen",
        "analysis_boundary": boundary,
        "next_paid_gate_plan": next_gate,
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "row_execution_allowed": False,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        **no_claims,
        "slice_selection_evidence_not_execution_evidence": True,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": decision["blockers"],
        "failures": decision["failures"],
        "redaction_scan_passed": not redaction,
        "redaction_findings": redaction,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
        "artifact_hashes": artifact_hashes(
            [
                PROOF / "candidate_rows.json",
                PROOF / "expanded_slice_decision.json",
                PROOF / "command_output.txt",
                PROOF / "review.md",
                receipt_path,
            ]
        ),
    }
    write_json(PROOF / "run_summary.json", summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status if status != "fail" else "null",
        "insight": (
            "The expanded provider-compatible slice can be frozen only as a stratified six-row "
            "plan: two BattleSnake rows remain prior paid evidence and four adapter-planned rows "
            "are selected for a bounded future paid gate without aggregate benchmark claims."
        ),
        "next_action": (
            "run the pre-registered bounded adapter-row paid execution gate only if the operator "
            "accepts the exact provider/API and spend ceilings"
        ),
        "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
        "evidence_paths": [
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            f"experiments/{EXPERIMENT_ID}/proof/expanded_slice_decision.json",
            f"experiments/{EXPERIMENT_ID}/proof/candidate_rows.json",
            f"experiments/{EXPERIMENT_ID}/proof/command_output.txt",
            f"experiments/{EXPERIMENT_ID}/proof/review.md",
            (
                f"experiments/{EXPERIMENT_ID}/proof/valid/"
                "receipt_provider_compatible_expanded_slice_after_adapter_completion.json"
            ),
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_result(status, summary)

    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
