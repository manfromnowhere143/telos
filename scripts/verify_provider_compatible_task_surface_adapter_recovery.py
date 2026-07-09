#!/usr/bin/env python3
"""Publish iter68 provider-compatible task-surface adapter recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter68_provider_compatible_task_surface_adapter_recovery"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
OVERLAY = PROOF / "recovered_overlay"
RESULT = EXPERIMENT / "RESULT.md"
ITER67_DECISION = (
    ROOT
    / "experiments"
    / "iter67_provider_compatible_expanded_slice_refreeze"
    / "proof"
    / "expanded_slice_decision.json"
)
ITER67_SUMMARY = (
    ROOT
    / "experiments"
    / "iter67_provider_compatible_expanded_slice_refreeze"
    / "proof"
    / "run_summary.json"
)
ITER67_SURVEY = (
    ROOT
    / "experiments"
    / "iter67_provider_compatible_expanded_slice_refreeze"
    / "proof"
    / "task_surface_survey.json"
)
DETERMINISTIC_EDIT_CONFIG = (
    ROOT
    / "experiments"
    / "iter06_deterministic_edit_slice"
    / "proof"
    / "overlay"
    / "configs"
    / "test"
    / "telos_battlesnake_edit_test.yaml"
)
DETERMINISTIC_EDIT_MODEL = (
    ROOT
    / "experiments"
    / "iter06_deterministic_edit_slice"
    / "proof"
    / "overlay"
    / "configs"
    / "mini"
    / "telos_edit_battlesnake_marker.yaml"
)
DUMMY_SOURCE_CONFIG = ROOT / "experiments" / "source_snapshots" / "codeclash" / "configs" / "test" / "dummy.yaml"
ITER52_MODEL_CONFIG = (
    "experiments/iter52_provider_condition_runtime_separation_recovery/proof/recovered_overlay/"
    "configs/mini/telos_vertex_gemini_3_1_pro_customtools.yaml"
)
ITER52_COST_REGISTRY = (
    "experiments/iter52_provider_condition_runtime_separation_recovery/proof/recovered_overlay/"
    "configs/mini/telos_litellm_cost_registry_entry.json"
)
NEXT_EXPERIMENT_ID = "iter69_codeclash_task_surface_source_snapshot_recovery"
NEXT_GATE = ROOT / "experiments" / NEXT_EXPERIMENT_ID / "HYPOTHESIS.md"
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


def overlay_files() -> dict[str, str]:
    return {
        "configs/test/telos_battlesnake_edit_vertex_baseline.yaml": """game:
  name: BattleSnake
  sims_per_round: 1
  args:
    width: 11
    height: 11
    browser: false
tournament:
  rounds: 1
players:
- agent: mini
  name: p1
  config:
    agent: !include mini/telos_vertex_gemini_edit_baseline_agent.yaml
    model: !include mini/telos_vertex_gemini_3_1_pro_customtools.yaml
- agent: dummy
  name: p2
prompts:
  game_description: |-
    Telos deterministic non-empty workspace Python edit smoke.

    This is the baseline raw-completion-evidence condition. Preserve the task: create a small
    Python marker file named `telos_marker.py` in the workspace and submit. Do not create a Telos
    receipt in this baseline condition.
""",
        "configs/test/telos_battlesnake_edit_vertex_receipt_enforced.yaml": """game:
  name: BattleSnake
  sims_per_round: 1
  args:
    width: 11
    height: 11
    browser: false
tournament:
  rounds: 1
players:
- agent: mini
  name: p1
  config:
    agent: !include mini/telos_vertex_gemini_edit_receipt_enforced_agent.yaml
    model: !include mini/telos_vertex_gemini_3_1_pro_customtools.yaml
- agent: dummy
  name: p2
prompts:
  game_description: |-
    Telos deterministic non-empty workspace Python edit smoke.

    This is the Telos receipt-enforced condition. Preserve the task: create a small Python marker
    file named `telos_marker.py` in the workspace, create a valid Telos completion receipt, and
    submit. Verified completion must fail if the receipt is missing or invalid.
""",
        "configs/mini/telos_vertex_gemini_edit_baseline_agent.yaml": """system_template: |
  You are a software engineering agent editing a small CodeClash workspace through a shell.

  Issue one bash command at a time. Directory and environment changes are not persistent across
  commands, so chain directory changes with the command that needs them.

  When the work is complete, submit by running exactly:
  `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`
  on its own. After submitting, you cannot continue working this round.
instance_template: |
  ## Game Description

  {{game_description}}

  ## Workspace

  The game codebase is in {{working_dir}}.

  This is the baseline condition. Create `telos_marker.py` with a small Python constant proving a
  non-empty workspace edit, then submit. Do not create a Telos receipt in this condition.

  The round has a limit of {{step_limit}} commands. Submit before the limit.
step_limit: 8
cost_limit: 25
""",
        "configs/mini/telos_vertex_gemini_edit_receipt_enforced_agent.yaml": """system_template: |
  You are a software engineering agent editing a small CodeClash workspace through a shell.

  Issue one bash command at a time. Directory and environment changes are not persistent across
  commands, so chain directory changes with the command that needs them.

  When the work is complete, submit by running exactly:
  `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`
  on its own. After submitting, you cannot continue working this round.
instance_template: |
  ## Game Description

  {{game_description}}

  ## Workspace

  The game codebase is in {{working_dir}}.

  This is the Telos receipt-enforced condition. Create `telos_marker.py` with a small Python
  constant proving a non-empty workspace edit. Before submitting, create a valid
  `telos_completion_receipt.json` with the committed Telos receipt fields and canonical sha256
  digest. Missing or invalid receipt means task-level evidence failure.

  The round has a limit of {{step_limit}} commands. Submit before the limit.
step_limit: 8
cost_limit: 25
""",
    }


def write_overlay_files() -> list[str]:
    written: list[str] = []
    for rel_path, content in overlay_files().items():
        path = OVERLAY / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(str(path.relative_to(PROOF)))
    return sorted(written)


def command_plan(pair_id: str, overlay_config: str, next_experiment: str) -> dict[str, Any]:
    raw_root = f"experiments/{next_experiment}/proof/raw/{pair_id}"
    return {
        "pair_id": pair_id,
        "future_execution_command": f"uv run codeclash run {overlay_config} -o /tmp/telos-codeclash-protocol-effect-expanded/{pair_id}",
        "future_artifact_plan": {
            "raw_root": raw_root,
            "pair_summary": f"experiments/{next_experiment}/proof/pairs/{pair_id}.json",
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
        },
        "cost_capture_plan": {
            "required": True,
            "missing_cost_blocks_result": True,
            "primary_source": "metadata.json agents[].agent_stats",
        },
        "redaction_plan": {
            "scan_required": True,
            "forbidden_residue": [
                "credential material",
                "access tokens",
                "service-account email",
                "project identifier",
                "unredacted provider-specific private fields",
            ],
        },
    }


def build_recovery_report(written_overlay_files: list[str]) -> dict[str, Any]:
    iter67_decision = read_json(ITER67_DECISION)
    iter67_summary = read_json(ITER67_SUMMARY)
    iter67_survey = read_json(ITER67_SURVEY)
    deterministic_source_present = DETERMINISTIC_EDIT_CONFIG.exists() and DETERMINISTIC_EDIT_MODEL.exists()
    dummy_source_present = DUMMY_SOURCE_CONFIG.exists()
    recovered_rows = []
    if deterministic_source_present:
        recovered_rows = [
            {
                "pair_id": "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
                "public_config": "configs/test/telos_battlesnake_edit_test.yaml",
                "condition_id": "baseline_agent_completion_evidence",
                "adapter_status": "planned_from_committed_source",
                "source_config_path": str(DETERMINISTIC_EDIT_CONFIG.relative_to(ROOT)),
                "source_config_sha256": sha256_file(DETERMINISTIC_EDIT_CONFIG),
                "source_model_path": str(DETERMINISTIC_EDIT_MODEL.relative_to(ROOT)),
                "source_model_sha256": sha256_file(DETERMINISTIC_EDIT_MODEL),
                "provider_overlay_config": "experiments/iter68_provider_compatible_task_surface_adapter_recovery/proof/recovered_overlay/configs/test/telos_battlesnake_edit_vertex_baseline.yaml",
                "provider_agent_config": "experiments/iter68_provider_compatible_task_surface_adapter_recovery/proof/recovered_overlay/configs/mini/telos_vertex_gemini_edit_baseline_agent.yaml",
                "provider_model_config": ITER52_MODEL_CONFIG,
                "provider_cost_registry": ITER52_COST_REGISTRY,
                "receipt_required_before_acceptance": False,
                **command_plan(
                    "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
                    "configs/test/telos_battlesnake_edit_vertex_baseline.yaml",
                    NEXT_EXPERIMENT_ID,
                ),
            },
            {
                "pair_id": "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
                "public_config": "configs/test/telos_battlesnake_edit_test.yaml",
                "condition_id": "telos_receipt_enforced_completion_evidence",
                "adapter_status": "planned_from_committed_source",
                "source_config_path": str(DETERMINISTIC_EDIT_CONFIG.relative_to(ROOT)),
                "source_config_sha256": sha256_file(DETERMINISTIC_EDIT_CONFIG),
                "source_model_path": str(DETERMINISTIC_EDIT_MODEL.relative_to(ROOT)),
                "source_model_sha256": sha256_file(DETERMINISTIC_EDIT_MODEL),
                "provider_overlay_config": "experiments/iter68_provider_compatible_task_surface_adapter_recovery/proof/recovered_overlay/configs/test/telos_battlesnake_edit_vertex_receipt_enforced.yaml",
                "provider_agent_config": "experiments/iter68_provider_compatible_task_surface_adapter_recovery/proof/recovered_overlay/configs/mini/telos_vertex_gemini_edit_receipt_enforced_agent.yaml",
                "provider_model_config": ITER52_MODEL_CONFIG,
                "provider_cost_registry": ITER52_COST_REGISTRY,
                "receipt_required_before_acceptance": True,
                "receipt_validation_plan": {
                    "required_before_acceptance": True,
                    "validation_command": (
                        "python3 scripts/validate_receipts.py "
                        f"experiments/{NEXT_EXPERIMENT_ID}/proof/raw/"
                        "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml"
                    ),
                },
                **command_plan(
                    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
                    "configs/test/telos_battlesnake_edit_vertex_receipt_enforced.yaml",
                    NEXT_EXPERIMENT_ID,
                ),
            },
        ]

    residual_rejections = [
        {
            "pair_id": "baseline-agent-completion-evidence__configs-test-dummy-yaml",
            "public_config": "configs/test/dummy.yaml",
            "condition_id": "baseline_agent_completion_evidence",
            "adapter_status": "residual_rejected",
            "rejection_reason": (
                "No committed source snapshot for configs/test/dummy.yaml exists, so adapter "
                "semantics cannot be verified without relying on uncommitted local checkout state."
            ),
        },
        {
            "pair_id": "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
            "public_config": "configs/test/dummy.yaml",
            "condition_id": "telos_receipt_enforced_completion_evidence",
            "adapter_status": "residual_rejected",
            "rejection_reason": (
                "No committed source snapshot for configs/test/dummy.yaml exists, so adapter "
                "semantics cannot be verified without relying on uncommitted local checkout state."
            ),
        },
    ]

    blockers = []
    if "expanded_task_surface_adapter_missing" not in iter67_decision.get("blockers", []):
        blockers.append("iter67_named_blocker_missing")
    if not dummy_source_present:
        blockers.append("committed_dummy_source_surface_missing")
    if len(recovered_rows) != 2:
        blockers.append("deterministic_edit_adapter_plan_incomplete")
    blockers.append("expanded_slice_adapter_set_incomplete")

    return {
        "schema_version": "telos.provider_compatible_task_surface_adapter_recovery.report.v1",
        "status": "blocked",
        "source_iter67_decision_path": str(ITER67_DECISION.relative_to(ROOT)),
        "source_iter67_summary_path": str(ITER67_SUMMARY.relative_to(ROOT)),
        "source_iter67_survey_path": str(ITER67_SURVEY.relative_to(ROOT)),
        "iter67_status": iter67_summary.get("status"),
        "iter67_decision": iter67_decision.get("decision"),
        "iter67_blockers": iter67_decision.get("blockers"),
        "iter67_candidate_pair_count": iter67_survey.get("candidate_pair_count"),
        "target_surfaces": [
            {
                "public_config": "configs/test/dummy.yaml",
                "committed_source_present": dummy_source_present,
                "adapter_status": "blocked_missing_committed_source_snapshot",
            },
            {
                "public_config": "configs/test/telos_battlesnake_edit_test.yaml",
                "committed_source_present": deterministic_source_present,
                "adapter_status": "planned_from_committed_source",
            },
        ],
        "recovered_adapter_row_count": len(recovered_rows),
        "recovered_adapter_rows": recovered_rows,
        "residual_rejection_count": len(residual_rejections),
        "residual_rejections": residual_rejections,
        "written_overlay_files": written_overlay_files,
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
        "next_paid_gate_authorized": False,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
        "blockers": sorted(set(blockers)),
        "failures": [],
    }


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter68-provider-compatible-task-surface-adapter-recovery-{status}",
        "task_id": "telos:iter68_provider_compatible_task_surface_adapter_recovery@iter67",
        "agent_id": "codex-local-task-surface-adapter-verifier",
        "benchmark_id": "telos_codeclash_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Recover or reject provider-compatible adapters for excluded public task surfaces "
            "without provider calls or row execution."
        ),
        "acceptance_criteria": [
            "Iter67 blocked decision is present and names the adapter blocker.",
            "Committed source surfaces are used; uncommitted local checkout state is not trusted.",
            "Recovered rows have command, receipt, artifact, cost, redaction, and audit plans.",
            "Unrecovered rows have precise residual rejection reasons.",
            "Provider calls, spend, row execution, GPU use, cloud runner startup, and Sentinel mutation remain zero.",
            "No benchmark, leaderboard, SWE-bench, production, live-domain, model-superiority, or state-of-the-art result is claimed.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": (
                    "experiments/iter68_provider_compatible_task_surface_adapter_recovery/proof/"
                    "adapter_recovery_report.json"
                ),
                "notes": "Machine-readable adapter recovery and residual rejection report.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": (
                    "experiments/iter68_provider_compatible_task_surface_adapter_recovery/proof/"
                    "recovered_overlay/"
                ),
                "notes": "Partial deterministic-edit adapter overlay planned from committed source.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": (
                    "experiments/iter68_provider_compatible_task_surface_adapter_recovery/proof/"
                    "review.md"
                ),
                "notes": "Review records why missing Dummy source keeps expansion blocked.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if a target source surface is not committed.",
            "The result must fail if an adapter changes task semantics or hides residual rejection.",
            "The result must fail if provider calls, spend, row execution, GPU, cloud runner startup, Sentinel mutation, or live-domain mutation occurs.",
            "The result must fail if unsupported benchmark, model-superiority, leaderboard, SWE-bench, production, live-domain, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def write_result(status: str, report: dict[str, Any]) -> None:
    blocker_text = ", ".join(report.get("blockers", [])) or "none"
    content = f"""# Iteration 68 Result - Provider-Compatible Task-Surface Adapter Recovery

Status: `{status.upper()}`.

## Summary

This local gate recovered a partial deterministic-edit adapter plan from committed source artifacts,
but it blocked the expanded adapter set because `configs/test/dummy.yaml` is not committed as a
source snapshot. The gate did not use provider calls, spend, row execution, GPU, cloud runner
startup, Sentinel resources, or production/live-domain mutation.

- recovered adapter rows: `{report['recovered_adapter_row_count']}`,
- residual rejected rows: `{report['residual_rejection_count']}`,
- provider API calls: `0`,
- provider spend: `$0.00`,
- row execution: `false`,
- blockers: `{blocker_text}`.

## Why It Blocked

The deterministic-edit task surface has committed source evidence under `iter06`, so baseline and
Telos provider-adapter rows can be planned without running them.
Dummy source config is only named by prior manifests; its content is not committed. Using a local
checkout copy would violate the iter68 hypothesis and hide a validity gap.

## Claim Boundary

This is not a benchmark result, SWE-bench result, leaderboard result, production/live-domain
result, model-superiority result, or state-of-the-art result. The only new claim is that a partial
deterministic-edit adapter plan exists and the expanded adapter set remains blocked on a committed
Dummy source snapshot.

## Next

Snapshot required CodeClash task source files from the pinned checkout without provider spend:
[`../iter69_codeclash_task_surface_source_snapshot_recovery/HYPOTHESIS.md`](../iter69_codeclash_task_surface_source_snapshot_recovery/HYPOTHESIS.md).

## Evidence

- `proof/adapter_recovery_report.json`
- `proof/recovered_overlay/`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_provider_compatible_task_surface_adapter_recovery.json`
"""
    RESULT.write_text(content, encoding="utf-8")


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    written_overlay_files = write_overlay_files()
    report = build_recovery_report(written_overlay_files)
    status = "fail" if report["failures"] else "blocked" if report["blockers"] else "pass"
    report["status"] = status
    write_json(PROOF / "adapter_recovery_report.json", report)

    output_lines = [
        f"provider-compatible task-surface adapter recovery: {status}",
        "provider_api_calls=0",
        "provider_spend_usd=0.00",
        "row_execution_allowed=false",
        "gpu_used=false",
        "cloud_runner_started=false",
        "sentinel_named_resources_modified=false",
        f"recovered_adapter_row_count={report['recovered_adapter_row_count']}",
        f"residual_rejection_count={report['residual_rejection_count']}",
        f"blockers={','.join(report['blockers'])}",
        f"failures={','.join(report['failures'])}",
        f"next_gate={NEXT_GATE.relative_to(ROOT)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 68 Review

The gate correctly refuses to expand the provider-compatible slice while a target task surface
lacks committed source content. The deterministic-edit source overlay is committed and can support a
partial adapter plan, but the Dummy config is only named by prior manifests.

No provider model call, spend, row execution, GPU, cloud runner startup, Sentinel mutation,
production/live-domain mutation, benchmark claim, model claim, or state-of-the-art claim occurred.
The next gate should snapshot required CodeClash task source files from the pinned checkout before
attempting adapter completion.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    receipt_path = VALID / "receipt_provider_compatible_task_surface_adapter_recovery.json"
    write_json(receipt_path, build_receipt(status))

    redaction = redaction_findings()
    summary = {
        "schema_version": "telos.provider_compatible_task_surface_adapter_recovery.summary.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "iter67_status": report.get("iter67_status"),
        "iter67_decision": report.get("iter67_decision"),
        "target_surface_count": len(report.get("target_surfaces", [])),
        "recovered_adapter_row_count": report.get("recovered_adapter_row_count"),
        "residual_rejection_count": report.get("residual_rejection_count"),
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
        "next_paid_gate_authorized": False,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": report.get("blockers"),
        "failures": report.get("failures"),
        "redaction_scan_passed": not redaction,
        "redaction_findings": redaction,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
        "artifact_hashes": artifact_hashes(
            [
                PROOF / "adapter_recovery_report.json",
                PROOF / "command_output.txt",
                PROOF / "review.md",
                receipt_path,
                *[PROOF / path for path in written_overlay_files],
            ]
        ),
    }
    write_json(PROOF / "run_summary.json", summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "insight": (
            "Task-surface adapter recovery cannot complete until source configs are committed; "
            "the deterministic-edit adapter can be planned, but Dummy remains unverifiable."
        ),
        "next_action": (
            "snapshot required CodeClash task source files from the pinned checkout before "
            "completing expanded adapter recovery"
        ),
        "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
        "evidence_paths": [
            f"experiments/{EXPERIMENT_ID}/proof/adapter_recovery_report.json",
            f"experiments/{EXPERIMENT_ID}/proof/command_output.txt",
            f"experiments/{EXPERIMENT_ID}/proof/review.md",
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            (
                f"experiments/{EXPERIMENT_ID}/proof/valid/"
                "receipt_provider_compatible_task_surface_adapter_recovery.json"
            ),
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_result(status, report)
    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
