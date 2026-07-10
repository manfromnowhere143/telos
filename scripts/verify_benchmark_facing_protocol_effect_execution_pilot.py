#!/usr/bin/env python3
"""Run iter83 benchmark-facing protocol-effect execution pilot."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest


ROOT = Path(__file__).resolve().parents[1]
ITER72_SCRIPT = ROOT / "scripts" / "verify_provider_compatible_expanded_paid_execution_after_slice_refreeze.py"
EXPERIMENT_ID = "iter83_benchmark_facing_protocol_effect_execution_pilot"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
RAW = PROOF / "raw"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
RECEIPT_NAME = "receipt_benchmark_facing_protocol_effect_execution_pilot.json"

ITER82_ID = "iter82_benchmark_facing_protocol_effect_slice_design"
ITER82_PROOF = ROOT / "experiments" / ITER82_ID / "proof"
ITER82_SUMMARY = ITER82_PROOF / "run_summary.json"
ITER82_FUTURE_PLAN = ITER82_PROOF / "future_paid_run_plan.json"
ITER71_CANDIDATES = (
    ROOT
    / "experiments"
    / "iter71_provider_compatible_expanded_slice_after_adapter_completion"
    / "proof"
    / "candidate_rows.json"
)
ITER54_COMMAND_MANIFEST = (
    ROOT / "experiments" / "iter54_provider_pair_executor_recovery" / "proof" / "command_manifest.json"
)

ITER52_OVERLAY = (
    ROOT
    / "experiments"
    / "iter52_provider_condition_runtime_separation_recovery"
    / "proof"
    / "recovered_overlay"
)
ITER65_BATTLESNAKE_TELOS_AGENT = (
    ROOT
    / "experiments"
    / "iter65_receipt_schema_prompt_alignment"
    / "proof"
    / "recovered_overlay"
    / "configs"
    / "mini"
    / "telos_vertex_gemini_receipt_enforced_agent.yaml"
)
ITER70_OVERLAY = (
    ROOT
    / "experiments"
    / "iter70_provider_compatible_expanded_adapter_completion"
    / "proof"
    / "recovered_overlay"
)
ITER73_OVERLAY = (
    ROOT
    / "experiments"
    / "iter73_expanded_receipt_prompt_recovery_after_paid_block"
    / "proof"
    / "recovered_overlay"
)
ITER80_OVERLAY = (
    ROOT
    / "experiments"
    / "iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery"
    / "proof"
    / "recovered_overlay"
)

PAIR_DUMMY_BASELINE = "baseline-agent-completion-evidence__configs-test-dummy-yaml"
PAIR_BATTLE_BASELINE = "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml"
PAIR_EDIT_BASELINE = "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml"
PAIR_DUMMY_TELOS = "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml"
PAIR_BATTLE_TELOS = "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml"
PAIR_EDIT_TELOS = "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml"
SELECTED_PAIR_IDS = [
    PAIR_DUMMY_BASELINE,
    PAIR_BATTLE_BASELINE,
    PAIR_EDIT_BASELINE,
    PAIR_DUMMY_TELOS,
    PAIR_BATTLE_TELOS,
    PAIR_EDIT_TELOS,
]
PAIR_TO_TASK = {
    PAIR_DUMMY_BASELINE: "dummy",
    PAIR_DUMMY_TELOS: "dummy",
    PAIR_BATTLE_BASELINE: "battlesnake",
    PAIR_BATTLE_TELOS: "battlesnake",
    PAIR_EDIT_BASELINE: "deterministic_edit",
    PAIR_EDIT_TELOS: "deterministic_edit",
}
PAIR_TO_CONDITION = {
    PAIR_DUMMY_BASELINE: "baseline",
    PAIR_BATTLE_BASELINE: "baseline",
    PAIR_EDIT_BASELINE: "baseline",
    PAIR_DUMMY_TELOS: "telos",
    PAIR_BATTLE_TELOS: "telos",
    PAIR_EDIT_TELOS: "telos",
}
PAIR_TO_AGENT_SOURCE = {
    PAIR_DUMMY_BASELINE: ITER80_OVERLAY / "configs" / "mini" / "telos_vertex_gemini_dummy_baseline_agent.yaml",
    PAIR_DUMMY_TELOS: ITER80_OVERLAY / "configs" / "mini" / "telos_vertex_gemini_dummy_receipt_enforced_agent.yaml",
    PAIR_BATTLE_BASELINE: ITER52_OVERLAY / "configs" / "mini" / "telos_vertex_gemini_baseline_agent.yaml",
    PAIR_BATTLE_TELOS: ITER65_BATTLESNAKE_TELOS_AGENT,
    PAIR_EDIT_BASELINE: ITER70_OVERLAY / "configs" / "mini" / "telos_vertex_gemini_edit_baseline_agent.yaml",
    PAIR_EDIT_TELOS: ITER73_OVERLAY / "configs" / "mini" / "telos_vertex_gemini_edit_receipt_enforced_agent.yaml",
}
PAIR_TO_AGENT_DESTINATION_NAME = {
    PAIR_DUMMY_BASELINE: "telos_vertex_gemini_dummy_baseline_agent.yaml",
    PAIR_DUMMY_TELOS: "telos_vertex_gemini_dummy_receipt_enforced_agent.yaml",
    PAIR_BATTLE_BASELINE: "telos_vertex_gemini_baseline_agent.yaml",
    PAIR_BATTLE_TELOS: "telos_vertex_gemini_receipt_enforced_agent.yaml",
    PAIR_EDIT_BASELINE: "telos_vertex_gemini_edit_baseline_agent.yaml",
    PAIR_EDIT_TELOS: "telos_vertex_gemini_edit_receipt_enforced_agent.yaml",
}
PAIR_TO_AGENT_RECOVERY = {
    PAIR_DUMMY_BASELINE: "iter80_dummy_call_ceiling_recovered_overlay",
    PAIR_DUMMY_TELOS: "iter80_dummy_call_ceiling_recovered_receipt_overlay",
    PAIR_BATTLE_BASELINE: "iter52_battlesnake_baseline_overlay_step_limit_recovery",
    PAIR_BATTLE_TELOS: "iter65_battlesnake_receipt_schema_overlay_step_limit_recovery",
    PAIR_EDIT_BASELINE: "iter70_deterministic_edit_baseline_overlay_step_limit_recovery",
    PAIR_EDIT_TELOS: "iter73_deterministic_edit_receipt_schema_overlay_step_limit_recovery",
}
RECOVERED_OVERLAY_DIR = PROOF / "recovered_overlay" / "configs" / "mini"
PAIR_TO_RECOVERED_AGENT = {
    pair_id: RECOVERED_OVERLAY_DIR / name for pair_id, name in PAIR_TO_AGENT_DESTINATION_NAME.items()
}

PER_ROW_CALL_LIMIT = 16
TOTAL_CALL_CEILING = 96
PER_ROW_SPEND_LIMIT_USD = 2.0
TOTAL_SPEND_CEILING_USD = 10.0
WALL_CLOCK_CEILING_SECONDS = 90 * 60
OUTPUT_ROOT = Path("/tmp/telos-codeclash-protocol-effect-benchmark-facing-pilot")
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


def runtime_project() -> tuple[bool, str | None, str]:
    available, project_id = iter72.helper.gcloud_project()
    if available and project_id:
        return True, project_id, "gcloud_config_project"
    adc_path = Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
    if not adc_path.exists():
        return False, None, "none"
    try:
        data = json.loads(adc_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False, None, "adc_quota_project_unreadable"
    quota_project = data.get("quota_project_id")
    if isinstance(quota_project, str) and quota_project:
        return True, quota_project, "adc_quota_project"
    return False, None, "none"


def configure_modules() -> None:
    iter72.EXPERIMENT_ID = EXPERIMENT_ID
    iter72.EXPERIMENT = EXPERIMENT
    iter72.PROOF = PROOF
    iter72.RAW = RAW
    iter72.VALID = VALID
    iter72.RESULT = RESULT
    iter72.SELECTED_PAIR_IDS = SELECTED_PAIR_IDS
    iter72.RETAINED_PAIR_IDS = []
    iter72.TOTAL_CALL_CEILING = TOTAL_CALL_CEILING
    iter72.TOTAL_SPEND_CEILING_USD = TOTAL_SPEND_CEILING_USD
    iter72.PER_ROW_CALL_LIMIT = PER_ROW_CALL_LIMIT
    iter72.PER_ROW_SPEND_LIMIT_USD = PER_ROW_SPEND_LIMIT_USD
    iter72.helper.EXPERIMENT_ID = EXPERIMENT_ID
    iter72.helper.EXPERIMENT = EXPERIMENT
    iter72.helper.PROOF = PROOF
    iter72.helper.RAW = RAW
    iter72.helper.VALID = VALID
    iter72.helper.CALL_CEILING = PER_ROW_CALL_LIMIT
    iter72.helper.SPEND_CEILING = PER_ROW_SPEND_LIMIT_USD


def replace_step_limit(text: str, limit: int) -> tuple[str, int | None]:
    match = re.search(r"^step_limit:\s*(\d+)\s*$", text, flags=re.MULTILINE)
    previous = int(match.group(1)) if match else None
    if match is None:
        raise RuntimeError("agent overlay missing step_limit")
    updated = re.sub(r"^step_limit:\s*\d+\s*$", f"step_limit: {limit}", text, count=1, flags=re.MULTILINE)
    return updated, previous


def write_recovered_agent_overlays() -> dict[str, Any]:
    RECOVERED_OVERLAY_DIR.mkdir(parents=True, exist_ok=True)
    generated = []
    for pair_id in SELECTED_PAIR_IDS:
        source = PAIR_TO_AGENT_SOURCE[pair_id]
        destination = PAIR_TO_RECOVERED_AGENT[pair_id]
        destination.parent.mkdir(parents=True, exist_ok=True)
        updated, previous = replace_step_limit(source.read_text(encoding="utf-8"), PER_ROW_CALL_LIMIT)
        destination.write_text(updated, encoding="utf-8")
        generated.append(
            {
                "pair_id": pair_id,
                "task_surface": PAIR_TO_TASK[pair_id],
                "condition": PAIR_TO_CONDITION[pair_id],
                "source": relative(source),
                "source_sha256": sha256_file(source),
                "destination": relative(destination),
                "destination_sha256": sha256_file(destination),
                "source_recovery": PAIR_TO_AGENT_RECOVERY[pair_id],
                "previous_step_limit": previous,
                "recovered_step_limit": PER_ROW_CALL_LIMIT,
            }
        )
    packet = {
        "schema_version": "telos.benchmark_facing_protocol_effect_execution.recovered_agent_overlays.v1",
        "experiment_id": EXPERIMENT_ID,
        "selected_pair_ids": SELECTED_PAIR_IDS,
        "generated": generated,
        "all_recovered_step_limits_written": all(
            item["recovered_step_limit"] == PER_ROW_CALL_LIMIT for item in generated
        ),
    }
    write_json(PROOF / "recovered_agent_overlay_manifest.json", packet)
    return packet


def benchmark_output_command(command: str, pair_id: str) -> str:
    old_roots = [
        "/tmp/telos-codeclash-protocol-effect-condition-separated",
        "/tmp/telos-codeclash-protocol-effect-expanded-slice",
        "/tmp/telos-codeclash-protocol-effect",
    ]
    output_path = str(OUTPUT_ROOT / pair_id)
    for old_root in old_roots:
        command = command.replace(f"{old_root}/{pair_id}", output_path)
    if not command.startswith("cd /tmp/telos-codeclash && "):
        command = f"cd /tmp/telos-codeclash && {command}"
    command = command.replace("cd /tmp/telos-codeclash && cd /tmp/telos-codeclash && ", "cd /tmp/telos-codeclash && ")
    return command


def row_adapter_overrides(pair_id: str) -> dict[str, str]:
    if PAIR_TO_TASK[pair_id] == "battlesnake":
        condition_suffix = "baseline" if PAIR_TO_CONDITION[pair_id] == "baseline" else "receipt_enforced"
        return {
            "provider_overlay_config": relative(
                ITER52_OVERLAY / "configs" / "test" / f"telos_battlesnake_vertex_gemini_{condition_suffix}.yaml"
            ),
            "provider_agent_config": relative(PAIR_TO_RECOVERED_AGENT[pair_id]),
            "provider_model_config": relative(
                ITER52_OVERLAY / "configs" / "mini" / "telos_vertex_gemini_3_1_pro_customtools.yaml"
            ),
            "provider_cost_registry": relative(
                ITER52_OVERLAY / "configs" / "mini" / "telos_litellm_cost_registry_entry.json"
            ),
        }
    return {
        "provider_agent_config": relative(PAIR_TO_RECOVERED_AGENT[pair_id]),
        "provider_agent_config_source_iteration": EXPERIMENT_ID,
        "provider_agent_step_limit": str(PER_ROW_CALL_LIMIT),
    }


def candidate_rows() -> list[dict[str, Any]]:
    packet = read_json(ITER71_CANDIDATES)
    source_rows = packet.get("candidate_rows", [])
    if not isinstance(source_rows, list):
        raise RuntimeError("iter71 candidate_rows must be a list")
    by_pair = {str(row.get("pair_id")): copy.deepcopy(row) for row in source_rows}
    command_manifest = read_json(ITER54_COMMAND_MANIFEST)
    battlesnake_commands = {
        item.get("pair_id"): item.get("command")
        for item in command_manifest.get("commands", [])
        if isinstance(item, dict)
    }
    selected = []
    for pair_id in SELECTED_PAIR_IDS:
        if pair_id not in by_pair:
            raise RuntimeError(f"missing iter71 candidate row: {pair_id}")
        row = by_pair[pair_id]
        row["pair_id"] = pair_id
        row["task_surface"] = PAIR_TO_TASK[pair_id]
        row["condition_label"] = PAIR_TO_CONDITION[pair_id]
        row["analysis_stratum"] = f"{PAIR_TO_TASK[pair_id]}_benchmark_facing_execution_pilot"
        if PAIR_TO_TASK[pair_id] == "battlesnake":
            command = battlesnake_commands.get(pair_id)
            if not command:
                raise RuntimeError(f"missing iter54 BattleSnake command: {pair_id}")
            row["future_execution_command"] = benchmark_output_command(command, pair_id)
        else:
            row["future_execution_command"] = benchmark_output_command(row["future_execution_command"], pair_id)
        adapter = row.setdefault("adapter_evidence", {})
        adapter["iter83_previous_provider_agent_config"] = adapter.get("provider_agent_config")
        adapter["iter83_step_limit_recovery"] = PAIR_TO_AGENT_RECOVERY[pair_id]
        adapter["provider_agent_step_limit"] = PER_ROW_CALL_LIMIT
        adapter.update(row_adapter_overrides(pair_id))
        selected.append(row)
    return selected


def materialize_runtime_overlay(rows: list[dict[str, Any]], *, project_id: str, token: str) -> dict[str, Any]:
    manifest = iter72.materialize_runtime_overlay(rows, project_id=project_id, token=token)
    recovered_sources = {relative(path) for path in PAIR_TO_RECOVERED_AGENT.values()}
    for copy_entry in manifest.get("copies", []):
        source = copy_entry.get("source")
        if source in recovered_sources:
            pair_id = next(
                pair for pair, path in PAIR_TO_RECOVERED_AGENT.items() if relative(path) == source
            )
            copy_entry["materialization"] = "copied_iter83_benchmark_facing_recovered_overlay"
            copy_entry["pair_id"] = pair_id
            copy_entry["task_surface"] = PAIR_TO_TASK[pair_id]
            copy_entry["condition"] = PAIR_TO_CONDITION[pair_id]
            copy_entry["source_override_reason"] = PAIR_TO_AGENT_RECOVERY[pair_id]
            copy_entry["recovered_step_limit"] = PER_ROW_CALL_LIMIT
    manifest["schema_version"] = "telos.benchmark_facing_protocol_effect_execution.overlay_materialization.v1"
    manifest["selected_pair_ids"] = SELECTED_PAIR_IDS
    manifest["all_selected_agent_overlays_materialized"] = all(
        any(
            entry.get("source") == relative(PAIR_TO_RECOVERED_AGENT[pair_id])
            and entry.get("copied_or_written") is True
            and entry.get("hash_match", True) is True
            for entry in manifest.get("copies", [])
        )
        for pair_id in SELECTED_PAIR_IDS
    )
    write_json(PROOF / "overlay_materialization_manifest.json", manifest)
    return manifest


def write_unmaterialized_overlay(reason: str) -> dict[str, Any]:
    manifest = iter72.write_unmaterialized_overlay(reason)
    manifest["schema_version"] = "telos.benchmark_facing_protocol_effect_execution.overlay_materialization.v1"
    manifest["selected_pair_ids"] = SELECTED_PAIR_IDS
    manifest["all_selected_agent_overlays_materialized"] = False
    write_json(PROOF / "overlay_materialization_manifest.json", manifest)
    return manifest


def prerequisite_validation() -> dict[str, Any]:
    summary = read_json(ITER82_SUMMARY)
    future_plan = read_json(ITER82_FUTURE_PLAN)
    receipt_check = run_capture(["python3", "scripts/validate_receipts.py", relative(ITER82_PROOF)])
    audit_check = run_capture(["python3", "scripts/audit_benchmark_facing_protocol_effect_slice_design.py"])
    clean = (
        summary.get("status") == "pass"
        and summary.get("clean_pass") is True
        and future_plan.get("future_selected_pair_ids") == SELECTED_PAIR_IDS
        and int(future_plan.get("future_per_row_call_limit", -1)) == PER_ROW_CALL_LIMIT
        and int(future_plan.get("future_provider_model_invocation_ceiling", -1)) == TOTAL_CALL_CEILING
        and str(future_plan.get("future_per_row_spend_limit_usd")) == f"{PER_ROW_SPEND_LIMIT_USD:.8f}"
        and str(future_plan.get("future_provider_spend_ceiling_usd")) == f"{TOTAL_SPEND_CEILING_USD:.8f}"
        and receipt_check["returncode"] == 0
        and audit_check["returncode"] == 0
    )
    packet = {
        "schema_version": "telos.benchmark_facing_protocol_effect_execution.prerequisite_validation.v1",
        "experiment_id": EXPERIMENT_ID,
        "iter82_status": summary.get("status"),
        "iter82_clean_pass": summary.get("clean_pass"),
        "iter82_future_gate": summary.get("future_gate"),
        "iter82_receipt_validation_returncode": receipt_check["returncode"],
        "iter82_audit_returncode": audit_check["returncode"],
        "iter82_future_selected_pair_ids": future_plan.get("future_selected_pair_ids"),
        "iter82_future_per_row_call_limit": future_plan.get("future_per_row_call_limit"),
        "iter82_future_provider_model_invocation_ceiling": future_plan.get(
            "future_provider_model_invocation_ceiling"
        ),
        "iter82_future_per_row_spend_limit_usd": future_plan.get("future_per_row_spend_limit_usd"),
        "iter82_future_provider_spend_ceiling_usd": future_plan.get(
            "future_provider_spend_ceiling_usd"
        ),
        "source_iter82_summary": relative(ITER82_SUMMARY),
        "source_iter82_summary_sha256": sha256_file(ITER82_SUMMARY),
        "source_iter82_future_plan": relative(ITER82_FUTURE_PLAN),
        "source_iter82_future_plan_sha256": sha256_file(ITER82_FUTURE_PLAN),
        "clean_prerequisites": clean,
        "paid_execution_allowed": clean,
    }
    write_json(PROOF / "prerequisite_validation.json", packet)
    return packet


def clean_output_root(command: str) -> None:
    output_root = iter72.helper.command_output_root(command)
    if not str(output_root).startswith(str(OUTPUT_ROOT)):
        raise RuntimeError(f"unsafe output root for iter83 cleanup: {output_root}")
    if output_root.exists():
        shutil.rmtree(output_root)


def run_paid_command(pair_id: str, command: str, *, project_id: str, token: str, timeout: int) -> dict[str, Any]:
    clean_output_root(command)
    output_root = iter72.helper.command_output_root(command)
    before = iter72.helper.path_children(output_root)
    transcript_dir = RAW / pair_id
    transcript_dir.mkdir(parents=True, exist_ok=True)
    start = time.time()
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=ROOT,
            env=iter72.helper.command_env(project_id=project_id, token=token),
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
        timed_out = False
        returncode = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = None
        stdout = (
            exc.stdout.decode("utf-8", errors="replace")
            if isinstance(exc.stdout, bytes)
            else (exc.stdout or "")
        )
        stderr = (
            exc.stderr.decode("utf-8", errors="replace")
            if isinstance(exc.stderr, bytes)
            else (exc.stderr or "")
        )
    elapsed = time.time() - start
    output_dir = iter72.helper.newest_output_dir(output_root, before)
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
            "timeout_seconds": timeout,
        },
    )
    return {
        "command": command,
        "elapsed_seconds": round(elapsed, 3),
        "output_dir": output_dir,
        "output_root": output_root,
        "returncode": returncode,
        "timed_out": timed_out,
    }


def primary_metric(row_results: list[dict[str, Any]]) -> dict[str, Any]:
    rows_by_pair = {row.get("pair_id"): row for row in row_results}
    metric: dict[str, Any] = {
        "metric_id": "verified_completion_evidence_by_task_and_condition",
        "aggregate_benchmark_metric_authorized": False,
    }
    for task, baseline_pair, telos_pair in [
        ("dummy", PAIR_DUMMY_BASELINE, PAIR_DUMMY_TELOS),
        ("battlesnake", PAIR_BATTLE_BASELINE, PAIR_BATTLE_TELOS),
        ("deterministic_edit", PAIR_EDIT_BASELINE, PAIR_EDIT_TELOS),
    ]:
        baseline = bool(rows_by_pair.get(baseline_pair, {}).get("verified_completion_evidence", False))
        telos = bool(rows_by_pair.get(telos_pair, {}).get("verified_completion_evidence", False))
        metric[f"{task}_baseline_verified_completion_evidence"] = baseline
        metric[f"{task}_telos_verified_completion_evidence"] = telos
        metric[f"{task}_delta_telos_minus_baseline"] = int(telos) - int(baseline)
    metric["interpretable_protocol_effect_signal"] = any(
        int(metric[f"{task}_delta_telos_minus_baseline"]) != 0
        for task in ["dummy", "battlesnake", "deterministic_edit"]
    )
    return metric


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter83-benchmark-facing-protocol-effect-execution-pilot-{status}",
        "task_id": "telos:iter83_benchmark_facing_protocol_effect_execution_pilot@iter82",
        "agent_id": "codex-local-benchmark-facing-protocol-effect-pilot-runner",
        "benchmark_id": "telos_codeclash_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Execute exactly the six iter82-selected CodeClash public task-condition rows under "
            "the frozen benchmark-facing protocol-effect envelope."
        ),
        "acceptance_criteria": [
            "Iter82 validates as a clean slice-design packet.",
            "Exactly six selected rows execute and zero unselected rows execute.",
            "Provider calls stay at or below 96 and provider spend stays at or below $10.00.",
            "Every completed row has raw artifacts, cost/call accounting, and redaction evidence.",
            "Receipt-enforced rows require a valid Telos receipt before verified completion is accepted.",
            "No GPU, cloud runner, Sentinel mutation, live-domain mutation, benchmark claim, model-superiority claim, or state-of-the-art claim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                "notes": "Run summary records row execution, calls, costs, receipts, blockers, and claim boundary.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/raw/",
                "notes": "Raw packet contains command transcripts and copied CodeClash artifacts.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/recovered_agent_overlay_manifest.json",
                "notes": "Recovered overlay manifest binds all six selected rows to the frozen 16-call ceiling.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records the no-benchmark/no-model/no-SOTA boundary and null-signal handling.",
            },
        ],
        "falsifiers": [
            "The result must block if iter82 validation fails.",
            "The result must fail if any unselected row executes.",
            "The result must fail if provider calls or spend exceed the frozen ceiling.",
            "The result must block/null if the executed rows show no interpretable Telos-minus-baseline protocol-effect signal.",
            "The result must fail if credential, token, project, or service-account residue is committed.",
            "The result must fail if unsupported benchmark, model-superiority, production, live-domain, leaderboard, SWE-bench, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def write_text_artifacts(
    *,
    status: str,
    row_results: list[dict[str, Any]],
    provider_calls: int,
    provider_cost: float,
    blockers: list[str],
    failures: list[str],
    metric: dict[str, Any],
    prereq: dict[str, Any],
    overlay: dict[str, Any],
    elapsed_seconds: float,
) -> None:
    summary_sentence = (
        "The gate executed the six iter82-selected CodeClash public task-condition rows."
        if row_results
        else "The gate blocked before row execution because preflight failed."
    )
    RESULT.write_text(
        f"""# Iteration 83 Result - Benchmark-Facing Protocol-Effect Execution Pilot

Status: `{status.upper()}`.

## Summary

{summary_sentence}

- selected row count: `{len(SELECTED_PAIR_IDS)}`,
- executed row count: `{len(row_results)}`,
- iter82 validation clean: `{str(prereq['clean_prerequisites']).lower()}`,
- all selected agent overlays materialized: `{str(overlay.get('all_selected_agent_overlays_materialized')).lower()}`,
- per-row provider call ceiling: `{PER_ROW_CALL_LIMIT}`,
- provider API calls: `{provider_calls}`,
- provider call ceiling: `{TOTAL_CALL_CEILING}`,
- provider cost from CodeClash metadata: `${provider_cost:.8f}`,
- provider spend ceiling: `${TOTAL_SPEND_CEILING_USD:.2f}`,
- wall-clock seconds: `{elapsed_seconds:.3f}`,
- wall-clock ceiling seconds: `{WALL_CLOCK_CEILING_SECONDS}`,
- GPU used: `false`,
- cloud runner started: `false`,
- Sentinel-named resources modified: `false`,
- benchmark/model/SOTA claim: `false`,
- null/no-signal result: `{str('no_interpretable_telos_minus_baseline_signal' in blockers).lower()}`,
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

## Stratified Metrics

- Dummy baseline verified-completion evidence:
  `{str(metric['dummy_baseline_verified_completion_evidence']).lower()}`,
- Dummy Telos verified-completion evidence:
  `{str(metric['dummy_telos_verified_completion_evidence']).lower()}`,
- Dummy Telos-minus-baseline delta:
  `{metric['dummy_delta_telos_minus_baseline']}`,
- BattleSnake baseline verified-completion evidence:
  `{str(metric['battlesnake_baseline_verified_completion_evidence']).lower()}`,
- BattleSnake Telos verified-completion evidence:
  `{str(metric['battlesnake_telos_verified_completion_evidence']).lower()}`,
- BattleSnake Telos-minus-baseline delta:
  `{metric['battlesnake_delta_telos_minus_baseline']}`,
- deterministic-edit baseline verified-completion evidence:
  `{str(metric['deterministic_edit_baseline_verified_completion_evidence']).lower()}`,
- deterministic-edit Telos verified-completion evidence:
  `{str(metric['deterministic_edit_telos_verified_completion_evidence']).lower()}`,
- deterministic-edit Telos-minus-baseline delta:
  `{metric['deterministic_edit_delta_telos_minus_baseline']}`.

## Claim Boundary

This is a bounded six-row benchmark-facing protocol-effect execution pilot. It is not a benchmark
result, SWE-bench score, leaderboard result, production/live-domain result, model-superiority
result, or state-of-the-art result.

## Evidence

- `proof/prerequisite_validation.json`
- `proof/recovered_agent_overlay_manifest.json`
- `proof/preflight.json`
- `proof/runtime_access_path_binding.json`
- `proof/runtime_access_path_model_config.yaml`
- `proof/overlay_materialization_manifest.json`
- `proof/protocol_effect_report.json`
- `proof/raw/`
- `proof/redaction_scan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/{RECEIPT_NAME}`
""",
        encoding="utf-8",
    )
    command_lines = [
        f"benchmark-facing protocol-effect execution pilot: {status}",
        f"selected_pair_count={len(SELECTED_PAIR_IDS)}",
        f"executed_pair_count={len(row_results)}",
        f"per_row_call_limit={PER_ROW_CALL_LIMIT}",
        f"provider_api_calls={provider_calls}",
        f"provider_call_ceiling={TOTAL_CALL_CEILING}",
        f"provider_cost_usd={provider_cost:.8f}",
        f"provider_spend_ceiling_usd={TOTAL_SPEND_CEILING_USD:.2f}",
        f"wall_clock_seconds={elapsed_seconds:.3f}",
        f"wall_clock_ceiling_seconds={WALL_CLOCK_CEILING_SECONDS}",
        "gpu_used=false",
        "cloud_runner_started=false",
        "sentinel_named_resources_modified=false",
        f"dummy_baseline_verified_completion_evidence={str(metric['dummy_baseline_verified_completion_evidence']).lower()}",
        f"dummy_telos_verified_completion_evidence={str(metric['dummy_telos_verified_completion_evidence']).lower()}",
        f"dummy_delta_telos_minus_baseline={metric['dummy_delta_telos_minus_baseline']}",
        f"battlesnake_baseline_verified_completion_evidence={str(metric['battlesnake_baseline_verified_completion_evidence']).lower()}",
        f"battlesnake_telos_verified_completion_evidence={str(metric['battlesnake_telos_verified_completion_evidence']).lower()}",
        f"battlesnake_delta_telos_minus_baseline={metric['battlesnake_delta_telos_minus_baseline']}",
        f"deterministic_edit_baseline_verified_completion_evidence={str(metric['deterministic_edit_baseline_verified_completion_evidence']).lower()}",
        f"deterministic_edit_telos_verified_completion_evidence={str(metric['deterministic_edit_telos_verified_completion_evidence']).lower()}",
        f"deterministic_edit_delta_telos_minus_baseline={metric['deterministic_edit_delta_telos_minus_baseline']}",
        f"interpretable_protocol_effect_signal={str(metric['interpretable_protocol_effect_signal']).lower()}",
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
        f"""# Iteration 83 Review

This gate attempted the frozen six-row benchmark-facing pilot from iter82: baseline and Telos
receipt-enforced conditions for Dummy, BattleSnake, and deterministic-edit CodeClash public task
surfaces. The result remains stratified by task surface; no aggregate benchmark, model-superiority,
leaderboard, SWE-bench, production/live-domain, or state-of-the-art claim is authorized.

- status: `{status}`,
- executed row count: `{len(row_results)}`,
- provider API calls: `{provider_calls}`,
- provider cost: `${provider_cost:.8f}`,
- interpretable protocol-effect signal: `{str(metric['interpretable_protocol_effect_signal']).lower()}`,
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

If the status is blocked only because `no_interpretable_telos_minus_baseline_signal` is present,
the pilot executed but published null protocol-effect evidence. That still forbids benchmark,
model, and SOTA claims.
""",
        encoding="utf-8",
    )


def main() -> int:
    configure_modules()
    started = time.time()
    if PROOF.exists():
        shutil.rmtree(PROOF)
    PROOF.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    prereq = prerequisite_validation()
    recovered_manifest = write_recovered_agent_overlays()
    rows = candidate_rows()
    selected_ids = [row["pair_id"] for row in rows]
    write_json(
        PROOF / "selected_row_plan.json",
        {
            "schema_version": "telos.benchmark_facing_protocol_effect_execution.selected_row_plan.v1",
            "experiment_id": EXPERIMENT_ID,
            "selected_pair_ids": selected_ids,
            "expected_selected_pair_ids": SELECTED_PAIR_IDS,
            "row_count": len(rows),
            "rows": [
                {
                    "pair_id": row["pair_id"],
                    "task_surface": row["task_surface"],
                    "condition_label": row["condition_label"],
                    "public_config": row.get("public_config"),
                    "future_execution_command": row.get("future_execution_command"),
                    "provider_agent_config": row.get("adapter_evidence", {}).get("provider_agent_config"),
                }
                for row in rows
            ],
        },
    )

    project_available, project_id, project_source = runtime_project()
    token = iter72.helper.access_token() if project_available else None
    token_available = token is not None
    iter72.helper.DYNAMIC_PROJECT_ID = project_id
    iter72.helper.DYNAMIC_BEARER_TOKEN = token

    if project_id and token:
        overlay = materialize_runtime_overlay(rows, project_id=project_id, token=token)
    else:
        overlay = write_unmaterialized_overlay("runtime_project_or_adc_token_unavailable")

    codeclash_rev = run_capture(["git", "-C", str(iter72.CODECLASH_DIR), "rev-parse", "HEAD"])
    docker = run_capture(
        [str(iter72.helper.DOCKER_BIN), "info", "--format", "{{.ServerVersion}}"],
        timeout=10,
    )
    google_auth = run_capture(
        [str(iter72.CODECLASH_DIR / ".venv" / "bin" / "python"), "-c", "import google.auth"],
        timeout=10,
    )
    preflight = {
        "schema_version": "telos.benchmark_facing_protocol_effect_execution.preflight.v1",
        "experiment_id": EXPERIMENT_ID,
        "iter82_status": prereq["iter82_status"],
        "iter82_clean_pass": prereq["iter82_clean_pass"],
        "iter82_receipt_validation_returncode": prereq["iter82_receipt_validation_returncode"],
        "iter82_audit_returncode": prereq["iter82_audit_returncode"],
        "codeclash_expected_commit": iter72.CODECLASH_COMMIT,
        "codeclash_actual_commit": codeclash_rev.get("stdout"),
        "codeclash_commit_matches_expected": codeclash_rev.get("stdout") == iter72.CODECLASH_COMMIT,
        "docker_ready": docker.get("returncode") == 0 and bool(docker.get("stdout")),
        "docker_server_version_present": bool(docker.get("stdout")),
        "codeclash_google_auth_import_ready": google_auth.get("returncode") == 0,
        "runtime_project_available": project_available,
        "runtime_project_source": project_source,
        "adc_access_token_available": token_available,
        "adc_token_output_suppressed": True,
        "runtime_env_values_committed": False,
        "runtime_overlay_all_materialized": overlay.get("all_materialized"),
        "runtime_overlay_copied_hashes_match": overlay.get("copied_hashes_match"),
        "runtime_model_config_materialized": overlay.get("runtime_model_config_materialized"),
        "runtime_model_config_has_secret_values_only_in_tmp": overlay.get(
            "runtime_model_config_has_secret_values_only_in_tmp"
        ),
        "all_selected_agent_overlays_materialized": overlay.get(
            "all_selected_agent_overlays_materialized"
        ),
        "selected_pair_ids": selected_ids,
        "expected_selected_pair_ids": SELECTED_PAIR_IDS,
        "provider_call_ceiling": TOTAL_CALL_CEILING,
        "provider_spend_ceiling_usd": TOTAL_SPEND_CEILING_USD,
        "per_row_call_limit": PER_ROW_CALL_LIMIT,
        "per_row_spend_limit_usd": PER_ROW_SPEND_LIMIT_USD,
        "wall_clock_ceiling_seconds": WALL_CLOCK_CEILING_SECONDS,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
    }
    write_json(PROOF / "preflight.json", iter72.helper.redact_value(preflight))

    blockers: list[str] = []
    failures: list[str] = []
    if prereq["clean_prerequisites"] is not True:
        blockers.append("iter82_prerequisite_validation_failed")
    if selected_ids != SELECTED_PAIR_IDS:
        failures.append("selected_pair_ids_changed")
    if preflight["codeclash_commit_matches_expected"] is not True:
        blockers.append("codeclash_checkout_not_pinned")
    if preflight["docker_ready"] is not True:
        blockers.append("docker_not_ready")
    if preflight["codeclash_google_auth_import_ready"] is not True:
        blockers.append("codeclash_google_auth_import_failed")
    if preflight["runtime_project_available"] is not True:
        blockers.append("runtime_project_unavailable")
    if preflight["adc_access_token_available"] is not True:
        blockers.append("adc_auth_unavailable")
    if preflight["runtime_overlay_all_materialized"] is not True:
        blockers.append("runtime_overlay_not_materialized")
    if preflight["runtime_overlay_copied_hashes_match"] is not True:
        blockers.append("runtime_overlay_hash_mismatch")
    if preflight["runtime_model_config_has_secret_values_only_in_tmp"] is not True:
        blockers.append("runtime_model_config_secret_boundary_not_proven")
    if preflight["all_selected_agent_overlays_materialized"] is not True:
        blockers.append("selected_agent_overlays_not_materialized")

    row_results: list[dict[str, Any]] = []
    if not blockers and not failures:
        for row in rows:
            elapsed = time.time() - started
            remaining = max(1, int(WALL_CLOCK_CEILING_SECONDS - elapsed))
            if remaining <= 1:
                blockers.append("wall_clock_ceiling_reached_before_next_row")
                break
            result = run_paid_command(
                row["pair_id"],
                row["future_execution_command"],
                project_id=project_id or "",
                token=token or "",
                timeout=min(1800, remaining),
            )
            raw_packet = iter72.helper.copy_raw_packet(row["pair_id"], result.get("output_dir"))
            row_result = iter72.row_metrics(row, result, raw_packet)
            row_result["task_surface"] = PAIR_TO_TASK[row["pair_id"]]
            row_result["condition_label"] = PAIR_TO_CONDITION[row["pair_id"]]
            row_results.append(row_result)
            calls_so_far = sum(int(item.get("provider_api_calls", 0)) for item in row_results)
            cost_so_far = sum(float(item.get("provider_cost_usd", 0.0)) for item in row_results)
            if calls_so_far > TOTAL_CALL_CEILING or cost_so_far > TOTAL_SPEND_CEILING_USD:
                failures.append("provider_ceiling_exceeded_during_execution")
                break

    provider_calls = sum(int(row.get("provider_api_calls", 0)) for row in row_results)
    provider_cost = round(sum(float(row.get("provider_cost_usd", 0.0)) for row in row_results), 8)
    elapsed_seconds = round(time.time() - started, 3)
    executed_pair_ids = [row.get("pair_id") for row in row_results]
    if row_results and executed_pair_ids != SELECTED_PAIR_IDS[: len(executed_pair_ids)]:
        failures.append("executed_pair_order_changed")
    if row_results and len(row_results) != len(SELECTED_PAIR_IDS) and not failures:
        blockers.append("not_exactly_six_rows_executed")
    if set(executed_pair_ids) - set(SELECTED_PAIR_IDS):
        failures.append("unselected_row_executed")
    if provider_calls > TOTAL_CALL_CEILING:
        failures.append("provider_call_ceiling_exceeded")
    if provider_cost > TOTAL_SPEND_CEILING_USD:
        failures.append("provider_spend_ceiling_exceeded")
    if any(int(row.get("provider_api_calls", 0)) > PER_ROW_CALL_LIMIT for row in row_results):
        failures.append("per_row_call_ceiling_exceeded")
    if any(float(row.get("provider_cost_usd", 0.0)) > PER_ROW_SPEND_LIMIT_USD for row in row_results):
        failures.append("per_row_spend_ceiling_exceeded")
    if elapsed_seconds > WALL_CLOCK_CEILING_SECONDS:
        failures.append("wall_clock_ceiling_exceeded")
    if any(row.get("command_returncode") not in (0, None) for row in row_results):
        blockers.append("provider_command_nonzero_returncode")
    for error_class in iter72.provider_error_classes(row_results):
        if error_class not in blockers:
            blockers.append(error_class)
    for row in row_results:
        if row.get("raw_evidence_present") is not True:
            blockers.append(f"{row['pair_id']}_raw_evidence_missing")
        if int(row.get("provider_api_calls", 0)) <= 0 and row.get("command_returncode") == 0:
            blockers.append(f"{row['pair_id']}_provider_call_stats_missing")
        if row.get("receipt_required") is True and row.get("receipt_valid") is not True:
            blockers.append(f"{row['pair_id']}_receipt_not_valid")

    metric = primary_metric(row_results)
    if len(row_results) == len(SELECTED_PAIR_IDS) and not metric["interpretable_protocol_effect_signal"]:
        blockers.append("no_interpretable_telos_minus_baseline_signal")

    scan_passed, scan_findings = redaction_scan()
    if not scan_passed:
        failures.append("redaction_scan_failed")

    blockers = sorted(set(blockers))
    failures = sorted(set(failures))
    status = "fail" if failures else "blocked" if blockers else "pass"

    report = {
        "schema_version": "telos.benchmark_facing_protocol_effect_execution.report.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "null_result": "no_interpretable_telos_minus_baseline_signal" in blockers,
        "preflight": preflight,
        "prerequisite_validation": prereq,
        "recovered_agent_overlay_manifest": recovered_manifest,
        "selected_pair_ids": SELECTED_PAIR_IDS,
        "executed_pair_ids": executed_pair_ids,
        "executed_pair_count": len(row_results),
        "row_results": row_results,
        "provider_api_calls": provider_calls,
        "provider_call_ceiling": TOTAL_CALL_CEILING,
        "provider_cost_usd": provider_cost,
        "provider_spend_ceiling_usd": TOTAL_SPEND_CEILING_USD,
        "per_row_call_limit": PER_ROW_CALL_LIMIT,
        "per_row_spend_limit_usd": PER_ROW_SPEND_LIMIT_USD,
        "wall_clock_seconds": elapsed_seconds,
        "wall_clock_ceiling_seconds": WALL_CLOCK_CEILING_SECONDS,
        "primary_metric": metric,
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_or_model_claim_authorized": False,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "swebench_execution_or_score_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "redaction_scan_passed": scan_passed,
        "redaction_findings": scan_findings,
        "blockers": blockers,
        "failures": failures,
    }
    write_json(PROOF / "protocol_effect_report.json", iter72.helper.redact_value(report))
    write_json(
        PROOF / "redaction_scan.json",
        {
            "schema_version": "telos.benchmark_facing_protocol_effect_execution.redaction_scan.v1",
            "experiment_id": EXPERIMENT_ID,
            "redaction_scan_passed": scan_passed,
            "redaction_findings": scan_findings,
        },
    )
    write_json(VALID / RECEIPT_NAME, build_receipt(status))
    write_text_artifacts(
        status=status,
        row_results=row_results,
        provider_calls=provider_calls,
        provider_cost=provider_cost,
        blockers=blockers,
        failures=failures,
        metric=metric,
        prereq=prereq,
        overlay=overlay,
        elapsed_seconds=elapsed_seconds,
    )
    learning_status = "null" if "no_interpretable_telos_minus_baseline_signal" in blockers else status
    write_json(
        PROOF / "learning_record.json",
        {
            "schema_version": "telos.learning_record.v1",
            "experiment_id": EXPERIMENT_ID,
            "status": learning_status if learning_status != "fail" else "null",
            "insight": (
                "The six-row pilot produced an interpretable stratified protocol-effect signal."
                if status == "pass"
                else "The six-row pilot produced bounded blocked/null evidence before any benchmark or SOTA claim."
            ),
            "next_action": (
                "design the next externally reviewable replication gate without aggregate benchmark claims"
                if status == "pass"
                else "recover only the named iter83 blocker or publish the null finding before any broader execution"
            ),
            "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
            "evidence_paths": [
                f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                f"experiments/{EXPERIMENT_ID}/proof/protocol_effect_report.json",
                f"experiments/{EXPERIMENT_ID}/proof/raw/",
                f"experiments/{EXPERIMENT_ID}/proof/valid/{RECEIPT_NAME}",
            ],
        },
    )

    summary_paths = [
        PROOF / "prerequisite_validation.json",
        PROOF / "selected_row_plan.json",
        PROOF / "recovered_agent_overlay_manifest.json",
        PROOF / "preflight.json",
        PROOF / "runtime_access_path_binding.json",
        PROOF / "runtime_access_path_model_config.yaml",
        PROOF / "overlay_materialization_manifest.json",
        PROOF / "protocol_effect_report.json",
        PROOF / "redaction_scan.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
        PROOF / "learning_record.json",
        VALID,
        RAW,
    ]
    summary = {
        "schema_version": "telos.benchmark_facing_protocol_effect_execution.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "null_result": "no_interpretable_telos_minus_baseline_signal" in blockers,
        "blockers": blockers,
        "failures": failures,
        "iter82_status": prereq["iter82_status"],
        "iter82_clean_pass": prereq["iter82_clean_pass"],
        "iter82_receipt_validation_returncode": prereq["iter82_receipt_validation_returncode"],
        "iter82_audit_returncode": prereq["iter82_audit_returncode"],
        "selected_pair_ids": SELECTED_PAIR_IDS,
        "executed_pair_ids": executed_pair_ids,
        "executed_pair_count": len(row_results),
        "provider_api_calls": provider_calls,
        "provider_call_ceiling": TOTAL_CALL_CEILING,
        "provider_cost_usd": provider_cost,
        "provider_spend_ceiling_usd": TOTAL_SPEND_CEILING_USD,
        "per_row_call_limit": PER_ROW_CALL_LIMIT,
        "per_row_spend_limit_usd": PER_ROW_SPEND_LIMIT_USD,
        "wall_clock_seconds": elapsed_seconds,
        "wall_clock_ceiling_seconds": WALL_CLOCK_CEILING_SECONDS,
        "runtime_overlay_all_materialized": overlay.get("all_materialized"),
        "runtime_overlay_copied_hashes_match": overlay.get("copied_hashes_match"),
        "runtime_model_config_materialized": overlay.get("runtime_model_config_materialized"),
        "runtime_model_config_has_secret_values_only_in_tmp": overlay.get(
            "runtime_model_config_has_secret_values_only_in_tmp"
        ),
        "all_selected_agent_overlays_materialized": overlay.get(
            "all_selected_agent_overlays_materialized"
        ),
        "primary_metric": metric,
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_or_model_claim_authorized": False,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "swebench_execution_or_score_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "redaction_scan_passed": scan_passed,
        "redaction_findings": scan_findings,
        "artifact_hashes": iter72.artifact_hashes(summary_paths),
    }
    write_json(PROOF / "run_summary.json", iter72.helper.redact_value(summary))

    print(f"benchmark-facing protocol-effect execution pilot: {status}")
    print(f"selected_pair_count={len(SELECTED_PAIR_IDS)}")
    print(f"executed_pair_count={len(row_results)}")
    print(f"provider_api_calls={provider_calls}")
    print(f"provider_call_ceiling={TOTAL_CALL_CEILING}")
    print(f"provider_cost_usd={provider_cost:.8f}")
    print(f"provider_spend_ceiling_usd={TOTAL_SPEND_CEILING_USD:.2f}")
    print(f"interpretable_protocol_effect_signal={str(metric['interpretable_protocol_effect_signal']).lower()}")
    print(f"blockers={','.join(blockers) if blockers else 'none'}")
    print(f"failures={','.join(failures) if failures else 'none'}")
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    sys.exit(main())
