#!/usr/bin/env python3
"""Publish iter70 provider-compatible expanded adapter completion artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter70_provider_compatible_expanded_adapter_completion"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
OVERLAY = PROOF / "recovered_overlay"
RESULT = EXPERIMENT / "RESULT.md"
ITER68_REPORT = (
    ROOT
    / "experiments"
    / "iter68_provider_compatible_task_surface_adapter_recovery"
    / "proof"
    / "adapter_recovery_report.json"
)
ITER69_SUMMARY = (
    ROOT
    / "experiments"
    / "iter69_codeclash_task_surface_source_snapshot_recovery"
    / "proof"
    / "run_summary.json"
)
ITER69_REPORT = (
    ROOT
    / "experiments"
    / "iter69_codeclash_task_surface_source_snapshot_recovery"
    / "proof"
    / "source_snapshot_report.json"
)
DUMMY_SOURCE_CONFIG = ROOT / "experiments" / "source_snapshots" / "codeclash" / "configs" / "test" / "dummy.yaml"
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
ITER68_OVERLAY = (
    ROOT
    / "experiments"
    / "iter68_provider_compatible_task_surface_adapter_recovery"
    / "proof"
    / "recovered_overlay"
)
ITER52_MODEL_CONFIG = (
    "experiments/iter52_provider_condition_runtime_separation_recovery/proof/recovered_overlay/"
    "configs/mini/telos_vertex_gemini_3_1_pro_customtools.yaml"
)
ITER52_COST_REGISTRY = (
    "experiments/iter52_provider_condition_runtime_separation_recovery/proof/recovered_overlay/"
    "configs/mini/telos_litellm_cost_registry_entry.json"
)
NEXT_EXPERIMENT_ID = "iter71_provider_compatible_expanded_slice_after_adapter_completion"
NEXT_GATE = ROOT / "experiments" / NEXT_EXPERIMENT_ID / "HYPOTHESIS.md"
EXPECTED_DUMMY_SHA256 = "b8e856447fc71c79bb5e042dc530127480d670d84fd51c03e2c2e7f58c630e97"
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


def dummy_overlay_files() -> dict[str, str]:
    return {
        "configs/test/telos_dummy_vertex_baseline.yaml": """tournament:
  rounds: 3
game:
  name: Dummy
  sims_per_round: 1000
players:
- agent: mini
  name: p1
  config:
    agent: !include mini/telos_vertex_gemini_dummy_baseline_agent.yaml
    model: !include mini/telos_vertex_gemini_3_1_pro_customtools.yaml
- agent: dummy
  name: p2
prompts:
  game_description: |-
    You are a software developer ({{player_id}}) competing in a coding game.

    The game is played in {{rounds}} rounds. For every round, you (and your competitor) edit
    program code that controls your bot. This is round {{round}}. After you and your competitor
    finish editing your codebases, the game is run automatically.

    This is the baseline raw-completion-evidence condition. Complete the task and submit without
    creating a Telos receipt.
""",
        "configs/test/telos_dummy_vertex_receipt_enforced.yaml": """tournament:
  rounds: 3
game:
  name: Dummy
  sims_per_round: 1000
players:
- agent: mini
  name: p1
  config:
    agent: !include mini/telos_vertex_gemini_dummy_receipt_enforced_agent.yaml
    model: !include mini/telos_vertex_gemini_3_1_pro_customtools.yaml
- agent: dummy
  name: p2
prompts:
  game_description: |-
    You are a software developer ({{player_id}}) competing in a coding game.

    The game is played in {{rounds}} rounds. For every round, you (and your competitor) edit
    program code that controls your bot. This is round {{round}}. After you and your competitor
    finish editing your codebases, the game is run automatically.

    This is the Telos receipt-enforced condition. Complete the task, create a valid Telos
    completion receipt, and submit. Verified completion must fail if the receipt is missing or
    invalid.
""",
        "configs/mini/telos_vertex_gemini_dummy_baseline_agent.yaml": """system_template: |
  You are a software engineering agent editing a CodeClash workspace through a shell.

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

  This is the baseline condition. Make the smallest task-appropriate edit available in the
  workspace, then submit. Do not create a Telos receipt in this condition.

  The round has a limit of {{step_limit}} commands. Submit before the limit.
step_limit: 8
cost_limit: 25
""",
        "configs/mini/telos_vertex_gemini_dummy_receipt_enforced_agent.yaml": """system_template: |
  You are a software engineering agent editing a CodeClash workspace through a shell.

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

  This is the Telos receipt-enforced condition. Make the smallest task-appropriate edit available
  in the workspace. Before submitting, create a valid `telos_completion_receipt.json` with the
  committed Telos receipt fields and canonical sha256 digest. Missing or invalid receipt means
  task-level evidence failure.

  The round has a limit of {{step_limit}} commands. Submit before the limit.
step_limit: 8
cost_limit: 25
""",
    }


def copy_deterministic_overlay_files() -> list[str]:
    rel_paths = [
        "configs/test/telos_battlesnake_edit_vertex_baseline.yaml",
        "configs/test/telos_battlesnake_edit_vertex_receipt_enforced.yaml",
        "configs/mini/telos_vertex_gemini_edit_baseline_agent.yaml",
        "configs/mini/telos_vertex_gemini_edit_receipt_enforced_agent.yaml",
    ]
    copied: list[str] = []
    for rel_path in rel_paths:
        source = ITER68_OVERLAY / rel_path
        destination = OVERLAY / rel_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied.append(str(destination.relative_to(PROOF)))
    return copied


def write_dummy_overlay_files() -> list[str]:
    written: list[str] = []
    for rel_path, content in dummy_overlay_files().items():
        path = OVERLAY / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(str(path.relative_to(PROOF)))
    return sorted(written)


def command_plan(pair_id: str, overlay_config: str) -> dict[str, Any]:
    raw_root = f"experiments/{NEXT_EXPERIMENT_ID}/proof/raw/{pair_id}"
    return {
        "pair_id": pair_id,
        "future_execution_command": (
            f"cd /tmp/telos-codeclash && uv run codeclash run {overlay_config} "
            f"-o /tmp/telos-codeclash-protocol-effect-expanded-adapter/{pair_id}"
        ),
        "future_artifact_plan": {
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
        "teardown_plan": {
            "required": True,
            "remove_tmp_output_root": f"/tmp/telos-codeclash-protocol-effect-expanded-adapter/{pair_id}",
            "must_not_stop_or_modify_sentinel_resources": True,
        },
    }


def row(
    *,
    pair_id: str,
    public_config: str,
    condition_id: str,
    source_config_path: Path,
    provider_overlay_config: str,
    provider_agent_config: str,
    receipt_required: bool,
    source_model_path: Path | None = None,
    source_semantic_note: str,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "pair_id": pair_id,
        "public_config": public_config,
        "condition_id": condition_id,
        "adapter_status": "planned_from_committed_source",
        "source_config_path": str(source_config_path.relative_to(ROOT)),
        "source_config_sha256": sha256_file(source_config_path),
        "source_semantic_note": source_semantic_note,
        "provider_overlay_config": f"experiments/{EXPERIMENT_ID}/proof/recovered_overlay/{provider_overlay_config}",
        "provider_agent_config": f"experiments/{EXPERIMENT_ID}/proof/recovered_overlay/{provider_agent_config}",
        "provider_model_config": ITER52_MODEL_CONFIG,
        "provider_cost_registry": ITER52_COST_REGISTRY,
        "receipt_required_before_acceptance": receipt_required,
        "generated_adapter_planning_evidence_only": True,
        "execution_result": False,
        **command_plan(pair_id, provider_overlay_config),
    }
    if source_model_path is not None:
        data["source_model_path"] = str(source_model_path.relative_to(ROOT))
        data["source_model_sha256"] = sha256_file(source_model_path)
    if receipt_required:
        data["receipt_validation_plan"] = {
            "required_before_acceptance": True,
            "validation_command": (
                "python3 scripts/validate_receipts.py "
                f"experiments/{NEXT_EXPERIMENT_ID}/proof/raw/{pair_id}"
            ),
        }
    else:
        data["receipt_validation_plan"] = {
            "required_before_acceptance": False,
            "validation_command": None,
        }
    return data


def build_adapter_rows() -> list[dict[str, Any]]:
    return [
        row(
            pair_id="baseline-agent-completion-evidence__configs-test-dummy-yaml",
            public_config="configs/test/dummy.yaml",
            condition_id="baseline_agent_completion_evidence",
            source_config_path=DUMMY_SOURCE_CONFIG,
            provider_overlay_config="configs/test/telos_dummy_vertex_baseline.yaml",
            provider_agent_config="configs/mini/telos_vertex_gemini_dummy_baseline_agent.yaml",
            receipt_required=False,
            source_semantic_note=(
                "Dummy is a minimal CodeClash task surface. The adapter preserves the Dummy game "
                "and source prompt while making p1 provider-compatible; future execution must not "
                "treat this as a benchmark-quality task without a separate slice decision."
            ),
        ),
        row(
            pair_id="telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
            public_config="configs/test/dummy.yaml",
            condition_id="telos_receipt_enforced_completion_evidence",
            source_config_path=DUMMY_SOURCE_CONFIG,
            provider_overlay_config="configs/test/telos_dummy_vertex_receipt_enforced.yaml",
            provider_agent_config="configs/mini/telos_vertex_gemini_dummy_receipt_enforced_agent.yaml",
            receipt_required=True,
            source_semantic_note=(
                "Dummy is a minimal CodeClash task surface. The adapter preserves the Dummy game "
                "and source prompt while adding only the Telos receipt condition; future execution "
                "must keep this separated from benchmark or model-quality claims."
            ),
        ),
        row(
            pair_id="baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
            public_config="configs/test/telos_battlesnake_edit_test.yaml",
            condition_id="baseline_agent_completion_evidence",
            source_config_path=DETERMINISTIC_EDIT_CONFIG,
            source_model_path=DETERMINISTIC_EDIT_MODEL,
            provider_overlay_config="configs/test/telos_battlesnake_edit_vertex_baseline.yaml",
            provider_agent_config="configs/mini/telos_vertex_gemini_edit_baseline_agent.yaml",
            receipt_required=False,
            source_semantic_note=(
                "Deterministic-edit source already encodes a small non-empty workspace edit target "
                "and was planned from committed iter06 evidence in iter68."
            ),
        ),
        row(
            pair_id="telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
            public_config="configs/test/telos_battlesnake_edit_test.yaml",
            condition_id="telos_receipt_enforced_completion_evidence",
            source_config_path=DETERMINISTIC_EDIT_CONFIG,
            source_model_path=DETERMINISTIC_EDIT_MODEL,
            provider_overlay_config="configs/test/telos_battlesnake_edit_vertex_receipt_enforced.yaml",
            provider_agent_config="configs/mini/telos_vertex_gemini_edit_receipt_enforced_agent.yaml",
            receipt_required=True,
            source_semantic_note=(
                "Deterministic-edit source already encodes a small non-empty workspace edit target; "
                "the adapter adds the Telos receipt condition before acceptance."
            ),
        ),
    ]


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter70-provider-compatible-expanded-adapter-completion-{status}",
        "task_id": "telos:iter70_provider_compatible_expanded_adapter_completion@iter69",
        "agent_id": "codex-local-expanded-adapter-completion-verifier",
        "benchmark_id": "telos_codeclash_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Complete provider-compatible adapter planning for the committed Dummy and "
            "deterministic-edit task surfaces without provider calls or row execution."
        ),
        "acceptance_criteria": [
            "Iter69 passed with a matching committed Dummy source snapshot hash.",
            "Iter68 residual Dummy adapter rejection is present and corrected by committed source evidence.",
            "Dummy and deterministic-edit baseline/Telos rows have command, artifact, cost, receipt, redaction, and teardown plans.",
            "Generated adapters are labeled as planning evidence, not execution results.",
            "Provider calls, spend, row execution, GPU use, cloud runner startup, Sentinel mutation, and live-domain mutation remain zero.",
            "No benchmark, leaderboard, SWE-bench, production, live-domain, model-superiority, or state-of-the-art result is claimed.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": (
                    "experiments/iter70_provider_compatible_expanded_adapter_completion/proof/"
                    "adapter_completion_report.json"
                ),
                "notes": "Machine-readable expanded adapter completion report.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": (
                    "experiments/iter70_provider_compatible_expanded_adapter_completion/proof/"
                    "recovered_overlay/"
                ),
                "notes": "Provider-compatible Dummy and deterministic-edit adapter overlays.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": (
                    "experiments/iter70_provider_compatible_expanded_adapter_completion/proof/"
                    "review.md"
                ),
                "notes": "Review records the planning-only boundary and Dummy semantic caveat.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if iter69 is missing, failed, or hash-mismatched.",
            "The result must block if any planned row lacks committed source evidence or exact future command/artifact/cost plans.",
            "The result must fail if generated adapters are presented as execution evidence.",
            "The result must fail if provider calls, spend, row execution, GPU, cloud runner startup, Sentinel mutation, or live-domain mutation occurs.",
            "The result must fail if unsupported benchmark, model-superiority, leaderboard, SWE-bench, production, live-domain, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def write_result(status: str, report: dict[str, Any]) -> None:
    content = f"""# Iteration 70 Result - Provider-Compatible Expanded Adapter Completion

Status: `{status.upper()}`.

## Summary

This local gate completed provider-compatible adapter planning for the committed Dummy and
deterministic-edit task surfaces. It wrote `4` planned rows and `8` overlay files. The adapters are
planning evidence only; they are not execution results and do not authorize paid execution.

- provider API calls: `0`,
- provider spend: `$0.00`,
- row execution: `false`,
- GPU used: `false`,
- cloud runner started: `false`,
- Sentinel-named resources modified: `false`,
- planned adapter rows: `{report['planned_adapter_row_count']}`,
- generated adapter files are execution evidence: `false`.

## Dummy Caveat

`configs/test/dummy.yaml` is a minimal CodeClash task surface. The adapter preserves the Dummy game
and source prompt while making condition-specific provider rows possible. Any future run must keep
Dummy separated from benchmark-quality or model-quality claims unless a later slice gate proves a
stronger interpretation.

## Claim Boundary

This is not a benchmark result, SWE-bench result, leaderboard result, production/live-domain
result, model-superiority result, or state-of-the-art result. The only new claim is that a
provider-compatible expanded adapter plan exists from committed source evidence.

## Next

Refreeze the expanded slice before any paid execution:
[`../iter71_provider_compatible_expanded_slice_after_adapter_completion/HYPOTHESIS.md`](../iter71_provider_compatible_expanded_slice_after_adapter_completion/HYPOTHESIS.md).

## Evidence

- `proof/adapter_completion_report.json`
- `proof/recovered_overlay/`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_provider_compatible_expanded_adapter_completion.json`
"""
    RESULT.write_text(content, encoding="utf-8")


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    copied_files = copy_deterministic_overlay_files()
    written_files = write_dummy_overlay_files()
    overlay_files = sorted(set(copied_files + written_files))

    iter68_report = read_json(ITER68_REPORT)
    iter69_summary = read_json(ITER69_SUMMARY)
    iter69_report = read_json(ITER69_REPORT)
    rows = build_adapter_rows()

    blockers: list[str] = []
    failures: list[str] = []
    if iter69_summary.get("status") != "pass":
        blockers.append("iter69_not_passed")
    if iter69_summary.get("source_snapshot_sha256") != EXPECTED_DUMMY_SHA256:
        blockers.append("iter69_dummy_source_hash_mismatch")
    if sha256_file(DUMMY_SOURCE_CONFIG) != EXPECTED_DUMMY_SHA256:
        blockers.append("committed_dummy_source_hash_mismatch")
    if not any(
        item.get("public_config") == "configs/test/dummy.yaml"
        and item.get("adapter_status") == "residual_rejected"
        for item in iter68_report.get("residual_rejections", [])
    ):
        blockers.append("iter68_dummy_residual_rejection_missing")
    if len(rows) != 4:
        blockers.append("adapter_row_count_mismatch")
    if len(overlay_files) != 8:
        blockers.append("overlay_file_count_mismatch")
    for row_data in rows:
        for key in [
            "future_execution_command",
            "future_artifact_plan",
            "cost_capture_plan",
            "receipt_validation_plan",
            "redaction_plan",
            "teardown_plan",
        ]:
            if not row_data.get(key):
                blockers.append(f"{row_data['pair_id']}_{key}_missing")
        if row_data.get("generated_adapter_planning_evidence_only") is not True:
            failures.append(f"{row_data['pair_id']}_planning_boundary_missing")
        if row_data.get("execution_result") is not False:
            failures.append(f"{row_data['pair_id']}_presented_as_execution_result")

    redaction = redaction_findings()
    if redaction:
        failures.append("redaction_findings_present")

    status = "fail" if failures else "blocked" if blockers else "pass"
    report = {
        "schema_version": "telos.provider_compatible_expanded_adapter_completion.report.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "source_iter68_report_path": str(ITER68_REPORT.relative_to(ROOT)),
        "source_iter69_summary_path": str(ITER69_SUMMARY.relative_to(ROOT)),
        "source_iter69_report_path": str(ITER69_REPORT.relative_to(ROOT)),
        "iter68_status": iter68_report.get("status"),
        "iter68_dummy_residual_rejection_present": "iter68_dummy_residual_rejection_missing" not in blockers,
        "iter69_status": iter69_summary.get("status"),
        "iter69_dummy_source_sha256": iter69_summary.get("source_snapshot_sha256"),
        "iter69_copied_source_files_are_execution_results": iter69_summary.get(
            "copied_source_files_are_execution_results"
        ),
        "iter69_snapshot_report_status": iter69_report.get("status"),
        "target_surfaces": [
            {
                "public_config": "configs/test/dummy.yaml",
                "committed_source_path": str(DUMMY_SOURCE_CONFIG.relative_to(ROOT)),
                "committed_source_sha256": sha256_file(DUMMY_SOURCE_CONFIG),
                "adapter_status": "planned_from_committed_source",
                "semantic_caveat": "minimal Dummy source; future slice gate must bound interpretation",
            },
            {
                "public_config": "configs/test/telos_battlesnake_edit_test.yaml",
                "committed_source_path": str(DETERMINISTIC_EDIT_CONFIG.relative_to(ROOT)),
                "committed_source_sha256": sha256_file(DETERMINISTIC_EDIT_CONFIG),
                "adapter_status": "planned_from_committed_source",
                "source_model_path": str(DETERMINISTIC_EDIT_MODEL.relative_to(ROOT)),
                "source_model_sha256": sha256_file(DETERMINISTIC_EDIT_MODEL),
            },
        ],
        "planned_adapter_row_count": len(rows),
        "dummy_adapter_row_count": len(
            [item for item in rows if item["public_config"] == "configs/test/dummy.yaml"]
        ),
        "deterministic_edit_adapter_row_count": len(
            [
                item
                for item in rows
                if item["public_config"] == "configs/test/telos_battlesnake_edit_test.yaml"
            ]
        ),
        "planned_adapter_rows": rows,
        "written_overlay_file_count": len(overlay_files),
        "written_overlay_files": overlay_files,
        "generated_adapters_are_planning_evidence_only": True,
        "generated_adapters_are_execution_results": False,
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
        "redaction_scan_passed": not redaction,
        "redaction_findings": redaction,
        "blockers": sorted(set(blockers)),
        "failures": sorted(set(failures)),
    }
    write_json(PROOF / "adapter_completion_report.json", report)

    output_lines = [
        f"provider-compatible expanded adapter completion: {status}",
        "provider_api_calls=0",
        "provider_spend_usd=0.00",
        "row_execution_allowed=false",
        "gpu_used=false",
        "cloud_runner_started=false",
        "sentinel_named_resources_modified=false",
        f"planned_adapter_row_count={report['planned_adapter_row_count']}",
        f"dummy_adapter_row_count={report['dummy_adapter_row_count']}",
        f"deterministic_edit_adapter_row_count={report['deterministic_edit_adapter_row_count']}",
        f"written_overlay_file_count={report['written_overlay_file_count']}",
        "generated_adapters_are_planning_evidence_only=true",
        "generated_adapters_are_execution_results=false",
        f"redaction_scan_passed={str(report['redaction_scan_passed']).lower()}",
        f"blockers={','.join(report['blockers'])}",
        f"failures={','.join(report['failures'])}",
        f"next_gate={NEXT_GATE.relative_to(ROOT)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 70 Review

The gate completes adapter planning from committed source evidence only. The Dummy adapters are
valid as planning artifacts because they preserve the Dummy game and source prompt while making p1
provider-compatible for a future controlled slice decision. They are not execution evidence, and
the Dummy task remains a minimal task surface with a strict interpretation boundary.

The deterministic-edit adapters reuse the iter68 recovered overlays and remain backed by committed
iter06 source evidence. No provider model call, spend, row execution, GPU, cloud runner startup,
Sentinel mutation, production/live-domain mutation, benchmark claim, model claim, or
state-of-the-art claim occurred.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    receipt_path = VALID / "receipt_provider_compatible_expanded_adapter_completion.json"
    write_json(receipt_path, build_receipt(status))

    summary = {
        "schema_version": "telos.provider_compatible_expanded_adapter_completion.summary.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "iter69_status": iter69_summary.get("status"),
        "iter69_dummy_source_sha256": iter69_summary.get("source_snapshot_sha256"),
        "planned_adapter_row_count": report["planned_adapter_row_count"],
        "dummy_adapter_row_count": report["dummy_adapter_row_count"],
        "deterministic_edit_adapter_row_count": report["deterministic_edit_adapter_row_count"],
        "written_overlay_file_count": report["written_overlay_file_count"],
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
        "generated_adapters_are_planning_evidence_only": True,
        "generated_adapters_are_execution_results": False,
        "next_paid_gate_authorized": False,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": report["blockers"],
        "failures": report["failures"],
        "redaction_scan_passed": report["redaction_scan_passed"],
        "redaction_findings": redaction,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
        "artifact_hashes": artifact_hashes(
            [
                PROOF / "adapter_completion_report.json",
                PROOF / "command_output.txt",
                PROOF / "review.md",
                receipt_path,
                *[PROOF / path for path in overlay_files],
            ]
        ),
    }
    write_json(PROOF / "run_summary.json", summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status if status != "fail" else "null",
        "insight": (
            "Committed source snapshots are sufficient to plan four provider-compatible adapter "
            "rows, but paid execution still requires a separate expanded-slice refreeze."
        ),
        "next_action": (
            "refreeze or reject the expanded provider-compatible slice before any paid execution "
            "of adapter-planned rows"
        ),
        "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
        "evidence_paths": [
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            f"experiments/{EXPERIMENT_ID}/proof/adapter_completion_report.json",
            f"experiments/{EXPERIMENT_ID}/proof/command_output.txt",
            f"experiments/{EXPERIMENT_ID}/proof/review.md",
            f"experiments/{EXPERIMENT_ID}/proof/recovered_overlay/configs/test/telos_dummy_vertex_baseline.yaml",
            f"experiments/{EXPERIMENT_ID}/proof/recovered_overlay/configs/test/telos_dummy_vertex_receipt_enforced.yaml",
            f"experiments/{EXPERIMENT_ID}/proof/valid/receipt_provider_compatible_expanded_adapter_completion.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_result(status, report)

    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
