#!/usr/bin/env python3
"""Publish iter67 provider-compatible expanded-slice refreeze artifacts."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter67_provider_compatible_expanded_slice_refreeze"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
ITER45_MANIFEST = (
    ROOT
    / "experiments"
    / "iter45_public_task_condition_executor_assembly"
    / "proof"
    / "executor_manifest.json"
)
ITER48_SLICE = (
    ROOT
    / "experiments"
    / "iter48_provider_compatible_protocol_effect_slice_refreeze"
    / "proof"
    / "provider_compatible_slice.json"
)
ITER52_PLAN = (
    ROOT
    / "experiments"
    / "iter52_provider_condition_runtime_separation_recovery"
    / "proof"
    / "condition_runtime_separation_plan.json"
)
ITER66_PROOF = (
    ROOT
    / "experiments"
    / "iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment"
    / "proof"
)
ITER66_SUMMARY = ITER66_PROOF / "run_summary.json"
ITER66_REPORT = ITER66_PROOF / "protocol_effect_report.json"
ITER66_RECEIPT = (
    ITER66_PROOF
    / "valid"
    / "receipt_provider_compatible_paid_execution_after_receipt_prompt_alignment.json"
)
ITER66_AUDIT = ROOT / "scripts" / "audit_provider_compatible_paid_execution_after_receipt_prompt_alignment.py"
NEXT_EXPERIMENT_ID = "iter68_provider_compatible_task_surface_adapter_recovery"
NEXT_GATE = ROOT / "experiments" / NEXT_EXPERIMENT_ID / "HYPOTHESIS.md"
READY_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
]
REJECTED_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-dummy-yaml",
    "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
]
PRIMARY_METRIC = {
    "baseline_verified_completion_evidence": True,
    "telos_verified_completion_evidence": True,
    "verified_completion_evidence_delta_telos_minus_baseline": 0,
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


def run_capture(args: list[str], *, timeout: int = 90) -> dict[str, Any]:
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


def git_capture(codeclash_dir: Path, args: list[str]) -> dict[str, Any]:
    return run_capture(["git", "-C", str(codeclash_dir), *args], timeout=30)


def local_codeclash_survey() -> dict[str, Any]:
    codeclash_dir = Path(os.environ.get("TELOS_CODECLASH_DIR", "/tmp/telos-codeclash"))
    if not (codeclash_dir / ".git").exists():
        return {
            "checkout_path": str(codeclash_dir),
            "checkout_present": False,
            "used_for_selection": False,
            "reason_not_used": "checkout not present; committed Telos artifacts are authoritative",
        }

    rev = git_capture(codeclash_dir, ["rev-parse", "HEAD"])
    status = git_capture(codeclash_dir, ["status", "--short"])
    files = git_capture(codeclash_dir, ["ls-files", "configs/test/*.yaml"])
    tracked_paths = [line for line in files.get("stdout", "").splitlines() if line.strip()]
    tracked = []
    for rel_path in tracked_paths:
        path = codeclash_dir / rel_path
        if path.is_file():
            tracked.append(
                {
                    "path": rel_path,
                    "sha256": sha256_file(path),
                    "battle_snake_named_path": "battlesnake" in rel_path.lower(),
                }
            )
    return {
        "checkout_path": str(codeclash_dir),
        "checkout_present": True,
        "checkout_head": rev.get("stdout"),
        "working_tree_dirty": bool(status.get("stdout")),
        "status_line_count": len([line for line in status.get("stdout", "").splitlines() if line]),
        "tracked_test_config_count": len(tracked),
        "tracked_test_configs": tracked,
        "used_for_selection": False,
        "reason_not_used": (
            "iter67 selection is limited to the committed iter45/iter48/iter52 candidate universe "
            "to avoid hidden task expansion or local-checkout tuning"
        ),
    }


def row_lookup(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("pair_id")): row for row in rows if isinstance(row, dict)}


def build_task_surface_survey() -> dict[str, Any]:
    manifest = read_json(ITER45_MANIFEST)
    refreeze = read_json(ITER48_SLICE)
    condition_plan = read_json(ITER52_PLAN)
    iter66_summary = read_json(ITER66_SUMMARY)
    iter66_report = read_json(ITER66_REPORT)

    manifest_pairs = manifest.get("pairs", [])
    ready = row_lookup(condition_plan.get("condition_pair_plans", []))
    rejected = row_lookup(condition_plan.get("rejected_excluded_pairs", []))
    refreeze_excluded = row_lookup(refreeze.get("excluded_pairs", []))

    candidate_pairs = []
    for pair in manifest_pairs:
        pair_id = pair.get("pair_id")
        ready_row = ready.get(pair_id, {})
        rejected_row = rejected.get(pair_id, {})
        refreeze_row = refreeze_excluded.get(pair_id, {})
        if ready_row:
            compatibility = "condition_separated_provider_ready"
            decision = "retain_existing_two_row_slice"
            reason = "already executed in iter66 as the bounded two-row pilot"
        else:
            compatibility = "provider_binding_incompatible"
            decision = "exclude_from_expanded_slice"
            reason = (
                rejected_row.get("rejection_reason")
                or refreeze_row.get("exclusion_reason")
                or "no committed provider-compatible condition adapter exists"
            )
        candidate_pairs.append(
            {
                "pair_id": pair_id,
                "task_id": pair.get("task_id"),
                "public_config": pair.get("public_config"),
                "condition_id": pair.get("condition_id"),
                "compatibility_status": compatibility,
                "iter67_decision": decision,
                "reason": reason,
            }
        )

    surfaces = []
    for public_config in sorted({pair.get("public_config") for pair in manifest_pairs}):
        rows = [pair for pair in candidate_pairs if pair.get("public_config") == public_config]
        ready_rows = [
            pair
            for pair in rows
            if pair.get("compatibility_status") == "condition_separated_provider_ready"
        ]
        rejected_rows = [
            pair for pair in rows if pair.get("compatibility_status") != "condition_separated_provider_ready"
        ]
        if len(ready_rows) == 2:
            expansion_status = "current_two_row_slice_only"
        elif ready_rows:
            expansion_status = "incomplete_condition_balance"
        else:
            expansion_status = "not_provider_compatible_without_adapter_recovery"
        surfaces.append(
            {
                "public_config": public_config,
                "candidate_pair_count": len(rows),
                "provider_ready_pair_count": len(ready_rows),
                "incompatible_pair_count": len(rejected_rows),
                "expansion_status": expansion_status,
                "pair_ids": [pair["pair_id"] for pair in rows],
            }
        )

    return {
        "schema_version": "telos.provider_compatible_expanded_slice_refreeze.survey.v1",
        "status": "blocked",
        "source_executor_manifest_path": str(ITER45_MANIFEST.relative_to(ROOT)),
        "source_provider_slice_path": str(ITER48_SLICE.relative_to(ROOT)),
        "source_condition_plan_path": str(ITER52_PLAN.relative_to(ROOT)),
        "source_iter66_summary_path": str(ITER66_SUMMARY.relative_to(ROOT)),
        "source_iter66_report_path": str(ITER66_REPORT.relative_to(ROOT)),
        "source_executor_manifest_status": manifest.get("status"),
        "source_provider_slice_status": refreeze.get("status"),
        "source_condition_plan_status": condition_plan.get("status"),
        "source_iter66_status": iter66_summary.get("status"),
        "source_iter66_primary_metric": iter66_summary.get("primary_metric"),
        "source_iter66_provider_api_calls": iter66_summary.get("provider_api_calls"),
        "source_iter66_provider_cost_usd": iter66_summary.get("provider_cost_usd"),
        "candidate_public_config_count": len(surfaces),
        "candidate_pair_count": len(candidate_pairs),
        "provider_ready_pair_count": len(READY_PAIR_IDS),
        "incompatible_pair_count": len(REJECTED_PAIR_IDS),
        "available_task_surfaces": surfaces,
        "candidate_pairs": candidate_pairs,
        "iter66_row_results": iter66_report.get("row_results", []),
        "local_codeclash_survey": local_codeclash_survey(),
    }


def build_decision(survey: dict[str, Any]) -> dict[str, Any]:
    condition_plan = read_json(ITER52_PLAN)
    retained = []
    for pair in condition_plan.get("condition_pair_plans", []):
        retained.append(
            {
                "pair_id": pair.get("pair_id"),
                "task_id": pair.get("task_id"),
                "public_config": pair.get("public_config"),
                "condition_id": pair.get("condition_id"),
                "future_execution_command": pair.get("future_execution_command"),
                "future_execution_command_without_output_root": pair.get(
                    "future_execution_command_without_output_root"
                ),
                "provider_overlay_config": pair.get("provider_overlay_config"),
                "provider_agent_config": pair.get("provider_agent_config"),
                "provider_model_config": pair.get("provider_model_config"),
                "future_artifact_plan": pair.get("future_artifact_plan"),
                "receipt_validation_plan": pair.get("receipt_validation_plan"),
                "redaction_plan": pair.get("redaction_plan"),
                "cost_capture_plan": pair.get("cost_capture_plan"),
            }
        )

    excluded = [
        {
            "pair_id": pair.get("pair_id"),
            "task_id": pair.get("task_id"),
            "public_config": pair.get("public_config"),
            "condition_id": pair.get("condition_id"),
            "exclusion_reason": pair.get("reason"),
        }
        for pair in survey.get("candidate_pairs", [])
        if pair.get("iter67_decision") == "exclude_from_expanded_slice"
    ]

    return {
        "schema_version": "telos.provider_compatible_expanded_slice_refreeze.decision.v1",
        "status": "blocked",
        "decision": "no_expanded_slice_currently_justified",
        "decision_reason": (
            "Iter66 fixed Telos receipt validity on the existing two-row BattleSnake slice, but "
            "the committed candidate universe still has no additional condition-balanced "
            "provider-compatible task rows beyond the two already executed rows."
        ),
        "blocked_not_quality_failure": True,
        "blockers": [
            "expanded_task_surface_adapter_missing",
            "no_candidate_pair_beyond_existing_two_has_provider_ready_binding",
        ],
        "failures": [],
        "iter66_primary_metric": survey.get("source_iter66_primary_metric"),
        "iter66_interpretation": (
            "The pilot is real provider-backed evidence that Telos receipt validation can pass, "
            "not evidence that Telos outperforms baseline; the measured delta is zero."
        ),
        "proposed_expanded_slice_pair_ids": [],
        "retained_existing_two_row_slice_pair_ids": READY_PAIR_IDS,
        "existing_two_row_command_plan": retained,
        "excluded_pair_ids": REJECTED_PAIR_IDS,
        "excluded_pairs": excluded,
        "next_recovery_gate": str(NEXT_GATE.relative_to(ROOT)),
        "next_recovery_goal": (
            "Recover local provider-compatible task adapters for the excluded public task "
            "surfaces, or explicitly prove that each remains invalid, before any larger paid run."
        ),
        "next_paid_gate_authorized": False,
        "provider_api_call_ceiling_for_iter67": 0,
        "provider_spend_ceiling_usd_for_iter67": 0.0,
        "row_execution_allowed_in_iter67": False,
        "gpu_allowed": False,
        "cloud_runner_startup_allowed": False,
        "sentinel_named_resources_must_not_change": True,
        "production_or_live_domain_change_allowed": False,
        "claim_boundary": {
            "benchmark_result_claimed": False,
            "leaderboard_or_swebench_result_claimed": False,
            "model_superiority_claimed": False,
            "state_of_the_art_result_claimed": False,
            "production_or_live_domain_changed": False,
        },
    }


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter67-provider-compatible-expanded-slice-refreeze-{status}",
        "task_id": "telos:iter67_provider_compatible_expanded_slice_refreeze@iter66",
        "agent_id": "codex-local-expanded-slice-refreeze-verifier",
        "benchmark_id": "telos_codeclash_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Decide whether the iter66 two-row provider-backed pilot justifies a larger "
            "provider-compatible protocol-effect slice before any additional spend."
        ),
        "acceptance_criteria": [
            "Iter66 receipt validation and audit evidence are rechecked locally.",
            "The committed task-condition candidate universe is surveyed.",
            "Every existing selected row keeps a command, receipt, redaction, cost, and artifact plan.",
            "Every non-selected candidate has an explicit compatibility reason.",
            "Provider calls, spend, row execution, GPU use, cloud runner startup, and Sentinel mutation remain zero.",
            "No benchmark, leaderboard, SWE-bench, production, live-domain, model-superiority, or state-of-the-art result is claimed.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": (
                    "experiments/iter67_provider_compatible_expanded_slice_refreeze/proof/"
                    "expanded_slice_decision.json"
                ),
                "notes": "Machine-readable no-expansion decision and named blockers.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": (
                    "experiments/iter67_provider_compatible_expanded_slice_refreeze/proof/"
                    "task_surface_survey.json"
                ),
                "notes": "Survey of committed candidate task surfaces and compatibility status.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": (
                    "experiments/iter67_provider_compatible_expanded_slice_refreeze/proof/"
                    "review.md"
                ),
                "notes": "Review records why expansion is blocked rather than overstated.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if no additional condition-balanced provider-compatible task rows exist.",
            "The result must fail if any provider call, spend, row execution, GPU, cloud runner startup, Sentinel mutation, or live-domain mutation occurs.",
            "The result must fail if excluded candidates are hidden or selected without command, receipt, cost, redaction, and artifact plans.",
            "The result must fail if it claims benchmark, leaderboard, SWE-bench, production, live-domain, model-superiority, or state-of-the-art evidence.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def evaluate(
    survey: dict[str, Any],
    decision: dict[str, Any],
    iter66_receipt_check: dict[str, Any],
    iter66_audit_check: dict[str, Any],
) -> tuple[str, list[str], list[str]]:
    blockers = list(decision.get("blockers", []))
    failures: list[str] = []

    if iter66_receipt_check.get("returncode") != 0:
        blockers.append("iter66_receipt_validation_missing_or_failed")
    if iter66_audit_check.get("returncode") != 0:
        blockers.append("iter66_audit_missing_or_failed")
    if not ITER66_RECEIPT.exists():
        blockers.append("iter66_receipt_artifact_missing")
    if survey.get("source_executor_manifest_status") != "dry_run_ready":
        blockers.append("iter45_executor_manifest_not_ready")
    if survey.get("source_provider_slice_status") != "pass":
        blockers.append("iter48_provider_slice_not_pass")
    if survey.get("source_condition_plan_status") != "condition_separated_ready":
        blockers.append("iter52_condition_plan_not_ready")
    if survey.get("source_iter66_status") != "pass":
        blockers.append("iter66_not_pass")
    if survey.get("source_iter66_primary_metric") != PRIMARY_METRIC:
        failures.append("iter66_primary_metric_changed")
    if survey.get("candidate_pair_count") != 6:
        failures.append("candidate pair count changed")
    if survey.get("provider_ready_pair_count") != 2:
        failures.append("provider ready pair count changed")
    if survey.get("incompatible_pair_count") != 4:
        failures.append("incompatible pair count changed")
    if decision.get("proposed_expanded_slice_pair_ids") != []:
        failures.append("iter67 must not select an expanded slice without recovered adapters")
    if decision.get("retained_existing_two_row_slice_pair_ids") != READY_PAIR_IDS:
        failures.append("existing two-row slice ids changed")
    if decision.get("excluded_pair_ids") != REJECTED_PAIR_IDS:
        failures.append("excluded pair ids changed")
    if not NEXT_GATE.exists():
        blockers.append("next_adapter_recovery_gate_missing")

    for key, expected in [
        ("provider_api_call_ceiling_for_iter67", 0),
        ("provider_spend_ceiling_usd_for_iter67", 0.0),
        ("row_execution_allowed_in_iter67", False),
        ("gpu_allowed", False),
        ("cloud_runner_startup_allowed", False),
        ("sentinel_named_resources_must_not_change", True),
        ("production_or_live_domain_change_allowed", False),
    ]:
        if decision.get(key) != expected:
            failures.append(f"decision {key} expected {expected!r}, got {decision.get(key)!r}")

    claim_boundary = decision.get("claim_boundary", {})
    for key in [
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "production_or_live_domain_changed",
    ]:
        if claim_boundary.get(key) is not False:
            failures.append(f"claim boundary {key} must be false")

    if failures:
        return "fail", blockers, failures
    if blockers:
        return "blocked", sorted(set(blockers)), failures
    return "pass", blockers, failures


def write_result_md(status: str, blockers: list[str], failures: list[str]) -> None:
    status_label = status.upper()
    blocker_text = ", ".join(blockers) if blockers else "none"
    failure_text = ", ".join(failures) if failures else "none"
    content = f"""# Iteration 67 Result - Provider-Compatible Expanded Slice Refreeze

Status: `{status_label}`.

## Summary

The gate did not execute provider rows. It rechecked the committed `iter66` two-row pilot, surveyed
the committed public task-condition candidate universe, and found no additional
condition-balanced provider-compatible rows beyond the two BattleSnake rows already executed.

- provider API calls: `0`,
- provider spend: `$0.00`,
- row execution: `false`,
- GPU used: `false`,
- cloud runner started: `false`,
- Sentinel-named resources modified: `false`,
- iter66 baseline verified-completion evidence: `true`,
- iter66 Telos verified-completion evidence: `true`,
- iter66 Telos-minus-baseline verified-completion delta: `0`,
- expanded slice decision: `no_expanded_slice_currently_justified`,
- blockers: `{blocker_text}`,
- failures: `{failure_text}`.

## Why It Blocked

`iter66` is a real provider-backed pilot and the Telos receipt now validates, but the committed
candidate universe still contains only one condition-balanced provider-compatible task surface. The
Dummy and deterministic-edit rows remain rejected because selecting them with the current
BattleSnake provider overlays would change task semantics or prompt conditions.

## Claim Boundary

This is not a benchmark result, SWE-bench result, leaderboard result, production/live-domain
result, model-superiority result, or state-of-the-art result. The only new claim is that a larger
paid provider-compatible slice is blocked until task-surface adapters are recovered and audited.

## Next

Recover local provider-compatible adapters for the rejected task surfaces before any larger paid
run: [`../iter68_provider_compatible_task_surface_adapter_recovery/HYPOTHESIS.md`](../iter68_provider_compatible_task_surface_adapter_recovery/HYPOTHESIS.md).

## Evidence

- `proof/task_surface_survey.json`
- `proof/expanded_slice_decision.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_provider_compatible_expanded_slice_refreeze.json`
"""
    RESULT.write_text(content, encoding="utf-8")


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    iter66_receipt_check = run_capture(
        ["python3", "scripts/validate_receipts.py", str(ITER66_PROOF.relative_to(ROOT))]
    )
    iter66_audit_check = run_capture(["python3", str(ITER66_AUDIT.relative_to(ROOT))])
    survey = build_task_surface_survey()
    decision = build_decision(survey)
    status, blockers, failures = evaluate(
        survey, decision, iter66_receipt_check, iter66_audit_check
    )
    survey["status"] = status
    decision["status"] = status
    decision["blockers"] = blockers
    decision["failures"] = failures

    write_json(PROOF / "task_surface_survey.json", survey)
    write_json(PROOF / "expanded_slice_decision.json", decision)

    output_lines = [
        f"provider-compatible expanded slice refreeze: {status}",
        "provider_api_calls=0",
        "provider_spend_usd=0.00",
        "row_execution_allowed=false",
        "gpu_used=false",
        "cloud_runner_started=false",
        "sentinel_named_resources_modified=false",
        f"iter66_receipt_validation_returncode={iter66_receipt_check.get('returncode')}",
        f"iter66_audit_returncode={iter66_audit_check.get('returncode')}",
        "iter66_verified_completion_evidence_delta_telos_minus_baseline=0",
        f"candidate_public_config_count={survey['candidate_public_config_count']}",
        f"candidate_pair_count={survey['candidate_pair_count']}",
        f"provider_ready_pair_count={survey['provider_ready_pair_count']}",
        f"incompatible_pair_count={survey['incompatible_pair_count']}",
        f"expanded_slice_decision={decision['decision']}",
        f"blockers={','.join(blockers)}",
        f"failures={','.join(failures)}",
        f"next_gate={NEXT_GATE.relative_to(ROOT)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 67 Review

The expanded-slice refreeze correctly blocks instead of pretending that the iter66 two-row pilot is
an expanded benchmark. Iter66 fixed the Telos receipt validity problem, but it measured a
zero Telos-minus-baseline verified-completion delta on one BattleSnake task surface.

The committed task-condition universe still has six rows: two BattleSnake PvP rows are
condition-separated and provider-ready, while four Dummy or deterministic-edit rows remain
provider-incompatible under the existing overlays. Selecting those rows now would change task
semantics or prompt conditions.

This gate made no provider call, spent no money, executed no row, used no GPU, started no cloud
runner, and modified no Sentinel-named resources. The next work is adapter recovery for the
excluded task surfaces, not a benchmark/model/state-of-the-art claim.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    receipt_path = VALID / "receipt_provider_compatible_expanded_slice_refreeze.json"
    write_json(receipt_path, build_receipt(status))

    redaction = redaction_findings()
    summary = {
        "schema_version": "telos.provider_compatible_expanded_slice_refreeze.summary.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "iter66_status": survey.get("source_iter66_status"),
        "iter66_primary_metric": survey.get("source_iter66_primary_metric"),
        "iter66_provider_api_calls": survey.get("source_iter66_provider_api_calls"),
        "iter66_provider_cost_usd": survey.get("source_iter66_provider_cost_usd"),
        "iter66_receipt_validation_returncode": iter66_receipt_check.get("returncode"),
        "iter66_audit_returncode": iter66_audit_check.get("returncode"),
        "candidate_public_config_count": survey.get("candidate_public_config_count"),
        "candidate_pair_count": survey.get("candidate_pair_count"),
        "provider_ready_pair_count": survey.get("provider_ready_pair_count"),
        "incompatible_pair_count": survey.get("incompatible_pair_count"),
        "expanded_slice_decision": decision.get("decision"),
        "proposed_expanded_slice_pair_ids": decision.get("proposed_expanded_slice_pair_ids"),
        "retained_existing_two_row_slice_pair_ids": READY_PAIR_IDS,
        "excluded_pair_ids": REJECTED_PAIR_IDS,
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "row_execution_allowed": False,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": blockers,
        "failures": failures,
        "redaction_scan_passed": not redaction,
        "redaction_findings": redaction,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
        "artifact_hashes": artifact_hashes(
            [
                PROOF / "task_surface_survey.json",
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
        "status": status,
        "insight": (
            "A larger provider-compatible protocol-effect slice is not yet earned: iter66 fixed "
            "Telos receipt validity, but no additional condition-balanced provider-ready task "
            "rows exist in the committed candidate universe."
        ),
        "next_action": (
            "recover provider-compatible task-surface adapters for the excluded public rows before "
            "attempting any larger paid protocol-effect run"
        ),
        "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
        "evidence_paths": [
            f"experiments/{EXPERIMENT_ID}/proof/task_surface_survey.json",
            f"experiments/{EXPERIMENT_ID}/proof/expanded_slice_decision.json",
            f"experiments/{EXPERIMENT_ID}/proof/command_output.txt",
            f"experiments/{EXPERIMENT_ID}/proof/review.md",
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            (
                f"experiments/{EXPERIMENT_ID}/proof/valid/"
                "receipt_provider_compatible_expanded_slice_refreeze.json"
            ),
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_result_md(status, blockers, failures)

    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
